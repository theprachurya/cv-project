import json
from datetime import datetime, timezone
from app.database.session import SessionLocal
from app.models import Alert, AnalysisSession, DetectionEvent, TrackedObject


def create_session(source: str, filename: str | None) -> int:
    with SessionLocal() as db:
        s = AnalysisSession(source=source, filename=filename, status="running")
        db.add(s); db.commit()
        return s.id


def save_alert(session_id: int, a: dict) -> int:
    with SessionLocal() as db:
        row = Alert(session_id=session_id, type=a["type"], severity=a["severity"], track_id=a["track_id"],
                    frame=a["frame"], video_time=a["video_time"], x=a["x"], y=a["y"], reason=a["reason"])
        db.add(row); db.commit()
        return row.id


def save_detection_events(session_id: int, events: list[dict]):
    """Persist a batch of tracked-object observations in one transaction."""
    if not events:
        return
    with SessionLocal() as db:
        db.add_all(DetectionEvent(session_id=session_id, **event) for event in events)
        db.commit()


def ack_alert(alert_id: int) -> bool:
    with SessionLocal() as db:
        row = db.get(Alert, alert_id)
        if not row:
            return False
        row.acknowledged = True; db.commit()
        return True


def finalize_session(session_id: int, status: str, frames: int, summary: dict, tracks: list[dict]):
    with SessionLocal() as db:
        s = db.get(AnalysisSession, session_id)
        s.status, s.frames_processed = status, frames
        s.ended_at = datetime.now(timezone.utc)
        s.summary = json.dumps(summary)
        for t in tracks:
            db.add(TrackedObject(session_id=session_id, **t))
        db.commit()


def alert_dict(a: Alert) -> dict:
    return {"id": a.id, "type": a.type, "severity": a.severity, "track_id": a.track_id, "frame": a.frame,
            "video_time": a.video_time, "x": a.x, "y": a.y, "reason": a.reason,
            "acknowledged": a.acknowledged, "timestamp": a.created_at.isoformat()}


def detection_dict(d: DetectionEvent) -> dict:
    return {"id": d.id, "session_id": d.session_id, "frame": d.frame, "video_time": d.video_time,
            "track_id": d.track_id, "label": d.label, "confidence": d.confidence,
            "box": [d.x1, d.y1, d.x2, d.y2], "motion": d.motion, "speed": d.speed,
            "proximity": d.proximity, "risk_score": d.risk_score, "risk_level": d.risk_level,
            "ttc": d.ttc, "reasons": d.reasons.split(" | ") if d.reasons else []}


def session_dict(s: AnalysisSession) -> dict:
    return {"id": s.id, "source": s.source, "filename": s.filename, "status": s.status,
            "started_at": s.started_at.isoformat(), "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "frames_processed": s.frames_processed}
