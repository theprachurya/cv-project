"""Alert generation with per-object cooldowns (no repeated spam for the same tracked object)."""
from datetime import datetime, timezone

RANK = {"low": 0, "medium": 1, "high": 2}
VEHICLES = {"car", "truck", "bus", "motorcycle"}


class AlertManager:
    def __init__(self):
        self.last: dict[tuple, tuple[int, int]] = {}

    def reset(self):
        self.last.clear()

    def raise_alert(self, type_, severity, track_id, frame, video_time, x, y, reason, cooldown_frames):
        key, prev = (type_, track_id), self.last.get((type_, track_id))
        if prev and frame - prev[0] < cooldown_frames and RANK[severity] <= prev[1]:
            return None  # still cooling down and not more severe than the last alert for this object
        self.last[key] = (frame, RANK[severity])
        return {"id": None, "type": type_, "severity": severity, "track_id": track_id, "frame": frame,
                "video_time": round(video_time, 2), "x": float(x), "y": float(y), "reason": reason,
                "acknowledged": False, "timestamp": datetime.now(timezone.utc).isoformat()}


def evaluate_alerts(mgr, infos, bs, frame, video_time, cooldown_frames, close_prox=0.8) -> list[dict]:
    out = []

    def add(type_, sev, i, reason):
        a = mgr.raise_alert(type_, sev, i["id"], frame, video_time, i["cx"], i["cy"], reason, cooldown_frames)
        if a:
            out.append(a)

    for i in infos:
        why = "; ".join(i["reasons"]) or "rule-based risk score"
        if i["risk_level"] in ("medium", "high"):
            add("Collision Risk", i["risk_level"], i, f"{i['label']} #{i['id']} risk {i['risk_score']}/100: {why}")
        elif i["label"] in VEHICLES and i["motion"] == "approaching" and i["ttc"] is not None and i["ttc"] <= 8:
            add("Approaching Vehicle", "medium", i, f"{i['label']} #{i['id']} approaching, TTC {i['ttc']}s")
        if i["label"] == "pedestrian" and i["proximity"] >= 0.4:
            add("Pedestrian Detection", "medium" if i["proximity"] >= 0.6 else "low", i,
                f"pedestrian #{i['id']} at {i['proximity']:.0%} nearness")
        if i["label"] != "traffic light" and i["proximity"] >= close_prox:
            add("Close Obstacle", "high" if i["proximity"] >= 0.9 else "medium", i,
                f"{i['label']} #{i['id']} very close ({i['proximity']:.0%} nearness)")
    by_id = {i["id"]: i for i in infos}
    for side in ("left", "right"):
        s = bs[side]
        if s["level"] in ("medium", "high"):
            i = by_id[s["ids"][0]]
            add(f"{side.capitalize()} Blind Spot", s["level"], i, f"vehicle #{i['id']} in {side} zone, closing in")
    return out
