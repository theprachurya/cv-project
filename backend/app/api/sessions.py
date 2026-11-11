import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import get_db
from app.models import Alert, AnalysisSession, DetectionEvent
from app.services import persistence, runtime
from app.services.analysis import runner
from app.services.report import build_pdf

router = APIRouter(prefix="/api", tags=["sessions"])


def _get(db: Session, sid: int) -> AnalysisSession:
    s = db.get(AnalysisSession, sid)
    if not s:
        raise HTTPException(404, "Session not found")
    return s


@router.get("/sessions")
def sessions(db: Session = Depends(get_db)):
    rows = db.scalars(select(AnalysisSession).order_by(AnalysisSession.id.desc())).all()
    out = []
    for s in rows:
        d = persistence.session_dict(s)
        sm = json.loads(s.summary) if s.summary else {}
        d.update(total_alerts=sm.get("total_alerts", 0), high_risk_events=sm.get("high_risk_events", 0),
                 unique_objects=sm.get("unique_objects", 0))
        out.append(d)
    return out


@router.get("/sessions/{sid}")
def session_detail(sid: int, db: Session = Depends(get_db)):
    s = _get(db, sid)
    return {**persistence.session_dict(s), "summary": json.loads(s.summary) if s.summary else {}}


@router.get("/alerts")
def alerts(session_id: int | None = None, severity: str | None = None, db: Session = Depends(get_db)):
    sid = session_id or runner.state()["session_id"]
    if sid is None:
        return []
    q = select(Alert).where(Alert.session_id == sid).order_by(Alert.id.desc())
    if severity:
        q = q.where(Alert.severity == severity)
    return [persistence.alert_dict(a) for a in db.scalars(q).all()]


@router.get("/detections")
def detections(session_id: int | None = None, limit: int = Query(100, ge=1, le=500),
               offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    """Return saved tracked-object observations for a session, newest frame first."""
    sid = session_id or runner.state()["session_id"]
    if sid is None:
        return []
    if not db.get(AnalysisSession, sid):
        raise HTTPException(404, "Session not found")
    q = (select(DetectionEvent).where(DetectionEvent.session_id == sid)
         .order_by(DetectionEvent.frame.desc(), DetectionEvent.id.desc()).offset(offset).limit(limit))
    return [persistence.detection_dict(d) for d in db.scalars(q).all()]


@router.patch("/alerts/{alert_id}/ack")
def ack(alert_id: int):
    if not persistence.ack_alert(alert_id):
        raise HTTPException(404, "Alert not found")
    runner.ack(alert_id)
    return {"id": alert_id, "acknowledged": True}


@router.get("/analytics")
def analytics():
    return runner.state()["summary"]


def _report_parts(db, sid):
    s = _get(db, sid)
    if not s.summary:
        raise HTTPException(409, "Session is still running or has no summary yet")
    al = [persistence.alert_dict(a) for a in db.scalars(select(Alert).where(Alert.session_id == sid).order_by(Alert.video_time))]
    return persistence.session_dict(s), json.loads(s.summary), al


@router.get("/sessions/{sid}/report.pdf")
def report_pdf(sid: int, db: Session = Depends(get_db)):
    sess, summary, al = _report_parts(db, sid)
    path = settings.report_dir / f"session_{sid}.pdf"
    build_pdf(path, sess, summary, al)
    return FileResponse(path, media_type="application/pdf", filename=f"road_safety_report_{sid}.pdf")


@router.get("/sessions/{sid}/report.json")
def report_json(sid: int, db: Session = Depends(get_db)):
    sess, summary, al = _report_parts(db, sid)
    return {"session": sess, "summary": summary, "alerts": al}


@router.get("/settings")
def get_settings():
    return runtime.get()


@router.put("/settings")
def put_settings(new: runtime.RuntimeSettings):
    return runtime.set_(new)
