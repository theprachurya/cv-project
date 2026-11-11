"""Background analysis runner: frame loop -> detect -> track -> flow -> depth -> risk -> blind spots -> alerts."""
import logging
import statistics
import threading
import time
from collections import Counter
from pathlib import Path
import cv2
from app.core.config import settings
from app.cv.blind_spot import VEHICLES, blind_spot_status
from app.cv.collision_risk import estimate_risk
from app.cv.depth_estimation import (DepthEstimator, colorize, object_depth, perspective_proximity,
                                     proximity_label)
from app.cv.detector import Detector
from app.cv.optical_flow import box_flow, classify_motion, dense_flow_overlay
from app.cv.overlay import draw_regions, draw_scene
from app.cv.tracker import Tracker, center
from app.services import persistence, runtime
from app.services.alerts import AlertManager, evaluate_alerts

log = logging.getLogger("analysis")
LEVELS = ("low", "medium", "high")


class AnalysisRunner:
    def __init__(self):
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._paused = threading.Event()
        self._detector = None
        self._depth = None
        self._depth_tried = False
        self._jpeg: bytes | None = None
        self._alerts: list[dict] = []
        self._mgr = AlertManager()
        self._tracker = None
        self._src_fps = 30.0
        self._t0 = time.time()
        self._reset_stats()
        self._state = self._blank()

    # ---- state helpers
    @staticmethod
    def _blank(**kw):
        s = {"status": "idle", "source": None, "filename": None, "session_id": None, "frame": 0, "frame_id": 0,
             "fps": 0.0, "counts": {}, "tracks": [], "unique_objects": 0, "objects_in_frame": 0,
             "overall": {"score": 0, "level": "low"}, "blind_spots": {"left": {"level": "clear", "ids": []},
             "right": {"level": "clear", "ids": []}}, "alerts": [], "alert_count": 0, "summary": {},
             "depth_backend": "perspective", "error": None}
        s.update(kw)
        return s

    def _reset_stats(self):
        self._risk_frames, self._motion_frames, self._timeline = Counter(), Counter(), []
        self._frames = self._raw = 0

    def state(self) -> dict:
        with self._lock:
            return dict(self._state)

    def latest(self):
        with self._lock:
            return self._state["frame_id"], self._jpeg

    def _set(self, **kw):
        with self._lock:
            self._state.update(kw)

    # ---- control
    def start(self, source: str, path: Path | None = None):
        self.stop()
        self._stop.clear(); self._paused.clear()
        self._jpeg = None
        self._alerts = []
        with self._lock:
            self._state = self._blank(status="loading_model", source=source, filename=path.name if path else None)
        self._thread = threading.Thread(target=self._run, args=(source, path), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        if self.state()["status"] in ("running", "paused", "loading_model"):
            self._set(status="stopped")

    def pause(self):
        if self.state()["status"] == "running":
            self._paused.set(); self._set(status="paused")

    def resume(self):
        if self.state()["status"] == "paused":
            self._paused.clear(); self._set(status="running")

    def ack(self, alert_id: int):
        with self._lock:
            for a in self._alerts:
                if a["id"] == alert_id:
                    a["acknowledged"] = True

    # ---- pipeline
    def _init_depth(self, use_depth: bool):
        if use_depth and not self._depth_tried:
            self._depth_tried = True
            try:
                self._depth = DepthEstimator()
            except Exception as e:  # torch missing / offline: fall back to perspective proximity
                log.warning("MiDaS unavailable (%s); using perspective-only proximity", e)
        self._set(depth_backend="midas+perspective" if self._depth else "perspective")

    def _analyze(self, t, prev_gray, gray, depth_map, fps_eff, rt) -> dict:
        h, w = gray.shape[:2]
        flow = box_flow(prev_gray, gray, t.box) if prev_gray is not None else None
        growth = statistics.mean([t.scale_rate] + ([flow.expansion] if flow else []))
        dx, dy = (flow.dx, flow.dy) if flow else t.displacement
        mag = float(flow.magnitude) if flow else float((dx ** 2 + dy ** 2) ** 0.5)
        motion = classify_motion(dx, dy, growth)
        prox = perspective_proximity(t.box, h)
        if depth_map is not None:
            prox = 0.5 * prox + 0.5 * object_depth(depth_map, t.box)
        cx, cy = center(t.box)
        risk = estimate_risk(t.label, prox, motion, growth, cx / w, fps_eff, rt.medium_risk, rt.high_risk)
        return {"id": t.id, "label": t.label, "confidence": round(float(t.confidence), 2), "box": [int(v) for v in t.box],
                "cx": float(cx), "cy": float(cy), "cx_frac": float(cx / w), "dx": round(float(dx), 2), "dy": round(float(dy), 2),
                "magnitude": round(mag, 2), "speed": round(mag * fps_eff, 1), "motion": motion, "growth": round(float(growth), 4),
                "proximity": round(float(prox), 2), "depth_label": proximity_label(prox), "ttc": risk.ttc,
                "risk_score": risk.score, "risk_level": risk.level, "reasons": risk.reasons, "age": int(t.last_frame - t.first_frame)}

    def _run(self, source: str, path: Path | None):
        cap, sid, final, frames = None, None, "stopped", 0
        pending_detections: list[dict] = []
        try:
            rt = runtime.get()
            if self._detector is None:
                self._detector = Detector(settings.yolo_model, rt.conf_threshold)
            self._init_depth(rt.use_depth)
            cap = cv2.VideoCapture(0 if source == "webcam" else str(path))
            if not cap.isOpened():
                raise RuntimeError("Could not open webcam" if source == "webcam" else "Could not open video file")
            self._src_fps = src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            skip = max(1, settings.frame_skip)
            fps_eff = src_fps / skip
            delay = 1.0 / src_fps if source == "video" else 0.0
            self._tracker = tracker = Tracker(fps_eff, settings.lost_track_buffer, settings.track_min_hits)
            self._reset_stats(); self._mgr.reset(); self._t0 = time.time()
            sid = persistence.create_session(source, path.name if path else None)
            self._set(status="running", session_id=sid)
            prev_gray, depth_map, idx, fid, t_last = None, None, 0, 0, time.time()
            while not self._stop.is_set():
                if self._paused.is_set():
                    time.sleep(0.05); continue
                t0 = time.time()
                ok, frame = cap.read()
                if not ok:
                    final = "ended" if source == "video" else "error"
                    if final == "error":
                        self._set(error="Camera stopped delivering frames")
                    break
                idx += 1
                if idx % skip:
                    continue
                if frame.shape[1] > settings.frame_width:
                    s = settings.frame_width / frame.shape[1]
                    frame = cv2.resize(frame, (settings.frame_width, int(frame.shape[0] * s)))
                rt = runtime.get()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                self._detector.conf = rt.conf_threshold
                tracks = tracker.update(self._detector.detect(frame), idx)
                if self._depth and rt.use_depth:
                    if depth_map is None or fid % rt.depth_every == 0:
                        depth_map = self._depth.estimate(frame)
                else:
                    depth_map = None
                infos = [self._analyze(t, prev_gray, gray, depth_map, fps_eff, rt) for t in tracks]
                bs = blind_spot_status(infos, rt.side_frac)
                vtime = idx / src_fps
                new = evaluate_alerts(self._mgr, infos, bs, idx, vtime, rt.cooldown_s * src_fps, rt.close_proximity)
                for a in new:
                    a["id"] = persistence.save_alert(sid, a)
                for i in infos:
                    x1, y1, x2, y2 = i["box"]
                    pending_detections.append({
                        "frame": idx, "video_time": round(vtime, 3), "track_id": i["id"], "label": i["label"],
                        "confidence": i["confidence"], "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                        "motion": i["motion"], "speed": i["speed"], "proximity": i["proximity"],
                        "risk_score": i["risk_score"], "risk_level": i["risk_level"], "ttc": i["ttc"],
                        "reasons": " | ".join(i["reasons"]),
                    })
                if fid % 25 == 0 and pending_detections:
                    persistence.save_detection_events(sid, pending_detections)
                    pending_detections.clear()
                top = max(infos, key=lambda i: i["risk_score"], default=None)
                overall = {"score": top["risk_score"] if top else 0, "level": top["risk_level"] if top else "low"}
                fid += 1
                self._frames, self._raw = fid, idx
                self._risk_frames[overall["level"]] += 1
                self._motion_frames.update(i["motion"] for i in infos)
                if fid % 3 == 0:
                    self._timeline.append({"t": round(vtime, 1), "score": overall["score"]})
                    if len(self._timeline) > 800:
                        self._timeline = self._timeline[::2]
                # ---- render
                if rt.view == "flow" and prev_gray is not None:
                    frame = dense_flow_overlay(prev_gray, gray, frame)
                elif rt.view == "depth" and depth_map is not None:
                    frame = colorize(depth_map)
                draw_regions(frame, bs, rt.side_frac)
                draw_scene(frame, tracks, infos)
                ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                prev_gray = gray
                now = time.time()
                unique = tracker.unique_by_label()
                with self._lock:
                    self._alerts.extend(new)
                    self._jpeg = buf.tobytes()
                    self._state.update(frame=idx, frame_id=fid, objects_in_frame=len(infos), counts=unique,
                                       unique_objects=sum(unique.values()), tracks=infos, overall=overall,
                                       blind_spots=bs, alerts=self._alerts[-40:][::-1], alert_count=len(self._alerts),
                                       fps=round(1.0 / max(now - t_last, 1e-3), 1))
                    if fid % 5 == 0:
                        self._state["summary"] = self.summary()
                t_last = now
                wait = delay - (time.time() - t0)
                if wait > 0:
                    time.sleep(wait)
            frames = fid
        except Exception as e:
            log.exception("Analysis failed")
            final = "error"
            self._set(error=str(e))
        finally:
            if cap is not None:
                cap.release()
            if sid is not None and pending_detections:
                try:
                    persistence.save_detection_events(sid, pending_detections)
                except Exception:
                    log.exception("Could not save the final detection-event batch")
            summary = self.summary()
            if sid is not None:
                tr = self._tracker
                tracks = [{"track_id": t.id, "label": t.label, "first_frame": t.first_frame, "last_frame": t.last_frame,
                           "avg_confidence": t.avg_confidence} for t in (tr.tracks.values() if tr else []) if t.hits >= tr.min_hits]
                try:
                    persistence.finalize_session(sid, final, frames, summary, tracks)
                except Exception:
                    log.exception("Could not save session")
            self._set(status=final, summary=summary)

    def summary(self) -> dict:
        tr = self._tracker
        by_label = tr.unique_by_label() if tr else {}
        confs = [t.avg_confidence for t in tr.tracks.values() if t.hits >= tr.min_hits] if tr else []
        n = max(sum(self._risk_frames.values()), 1)
        types = Counter(a["type"] for a in self._alerts)
        return {
            "filename": self._state.get("filename"), "duration_s": round(time.time() - self._t0, 1),
            "video_seconds": round(self._raw / self._src_fps, 1), "frames_analyzed": self._frames,
            "unique_objects": sum(by_label.values()), "by_label": by_label,
            "vehicles": sum(v for k, v in by_label.items() if k in VEHICLES or k == "bicycle"),
            "pedestrians": by_label.get("pedestrian", 0),
            "avg_confidence": round(statistics.mean(confs), 3) if confs else 0.0,
            "total_alerts": len(self._alerts), "alerts_by_type": dict(types),
            "left_alerts": types.get("Left Blind Spot", 0), "right_alerts": types.get("Right Blind Spot", 0),
            "high_risk_events": sum(1 for a in self._alerts if a["severity"] == "high"),
            "risk_distribution": {k: round(100 * self._risk_frames.get(k, 0) / n, 1) for k in LEVELS},
            "motion_distribution": dict(self._motion_frames), "timeline": self._timeline[-300:],
        }


runner = AnalysisRunner()
