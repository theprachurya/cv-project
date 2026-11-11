"""Module B: ByteTrack-based multi-object tracking with per-object motion history."""
from collections import Counter, deque
from dataclasses import dataclass, field
import cv2
import numpy as np
import supervision as sv
from app.cv.detector import CLASS_MAP, COLORS, Detection

CLASS_IDS = {v: k for k, v in CLASS_MAP.items()}
Box = tuple[int, int, int, int]


def center(b: Box) -> tuple[float, float]:
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


@dataclass
class Track:
    id: int
    box: Box
    prev_box: Box | None
    confidence: float
    first_frame: int
    last_frame: int
    hits: int = 0
    conf_sum: float = 0.0
    labels: Counter = field(default_factory=Counter)
    trail: deque = field(default_factory=lambda: deque(maxlen=30))
    areas: deque = field(default_factory=lambda: deque(maxlen=10))

    @property
    def label(self) -> str:
        return self.labels.most_common(1)[0][0]

    @property
    def displacement(self) -> tuple[float, float]:
        """Center displacement (dx, dy) in pixels between the previous and current box."""
        if self.prev_box is None:
            return (0.0, 0.0)
        (x0, y0), (x1, y1) = center(self.prev_box), center(self.box)
        return (x1 - x0, y1 - y0)

    @property
    def scale_rate(self) -> float:
        """Relative growth of the box's linear size per processed frame (>0 = getting bigger/closer)."""
        if len(self.areas) < 5 or self.areas[0] <= 0:
            return 0.0
        return (self.areas[-1] / self.areas[0]) ** (0.5 / (len(self.areas) - 1)) - 1

    @property
    def avg_confidence(self) -> float:
        return self.conf_sum / max(self.hits, 1)


class Tracker:
    def __init__(self, fps: float = 30.0, lost_buffer: int = 30, min_hits: int = 3):
        self.bt = sv.ByteTrack(track_activation_threshold=0.3, lost_track_buffer=lost_buffer,
                               minimum_matching_threshold=0.8, frame_rate=max(1, int(fps)))
        self.min_hits = min_hits
        self.tracks: dict[int, Track] = {}

    def update(self, dets: list[Detection], frame_idx: int) -> list[Track]:
        """Feed one frame of detections; returns confirmed tracks seen in this frame."""
        if dets:
            sv_dets = sv.Detections(
                xyxy=np.array([d.box for d in dets], dtype=float),
                confidence=np.array([d.confidence for d in dets]),
                class_id=np.array([CLASS_IDS[d.label] for d in dets]))
        else:
            sv_dets = sv.Detections.empty()
        out = self.bt.update_with_detections(sv_dets)
        active = []
        for xyxy, conf, cid, tid in zip(out.xyxy, out.confidence, out.class_id, out.tracker_id):
            tid, box = int(tid), tuple(int(v) for v in xyxy)
            t = self.tracks.get(tid)
            if t is None:
                t = self.tracks[tid] = Track(tid, box, None, float(conf), frame_idx, frame_idx)
            else:
                t.prev_box, t.box = t.box, box
            t.confidence, t.last_frame = float(conf), frame_idx
            t.hits += 1
            t.conf_sum += float(conf)
            t.labels[CLASS_MAP[int(cid)]] += 1
            t.trail.append(center(box))
            t.areas.append(max(1, (box[2] - box[0]) * (box[3] - box[1])))
            if t.hits >= self.min_hits:
                active.append(t)
        return active

    def unique_by_label(self) -> dict[str, int]:
        """Unique confirmed objects seen so far, grouped by class (not per-frame detections)."""
        return dict(Counter(t.label for t in self.tracks.values() if t.hits >= self.min_hits))


def draw_tracks(frame: np.ndarray, tracks: list[Track]) -> np.ndarray:
    for t in tracks:
        x1, y1, x2, y2 = t.box
        color = COLORS.get(t.label, (255, 255, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        if len(t.trail) > 1:
            cv2.polylines(frame, [np.array(t.trail, np.int32)], False, color, 1, cv2.LINE_AA)
        text = f"#{t.id} {t.label} {t.confidence:.0%}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, max(0, y1 - th - 8)), (x1 + tw + 6, y1), color, -1)
        cv2.putText(frame, text, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    return frame
