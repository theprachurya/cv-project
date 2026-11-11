from datetime import datetime, timezone
from sqlalchemy import Float, ForeignKey, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base


def _now():
    return datetime.now(timezone.utc)


class AnalysisSession(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(20))  # "webcam" | "video"
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="created")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    frames_processed: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON report data
    alerts: Mapped[list["Alert"]] = relationship(back_populates="session")
    tracks: Mapped[list["TrackedObject"]] = relationship(back_populates="session")


class TrackedObject(Base):
    __tablename__ = "tracked_objects"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    track_id: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(32))
    first_frame: Mapped[int] = mapped_column(Integer)
    last_frame: Mapped[int] = mapped_column(Integer)
    avg_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    session: Mapped[AnalysisSession] = relationship(back_populates="tracks")


class DetectionEvent(Base):
    """One tracked-object observation on an analyzed frame."""
    __tablename__ = "detection_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    frame: Mapped[int] = mapped_column(Integer, index=True)
    video_time: Mapped[float] = mapped_column(Float, default=0.0)
    track_id: Mapped[int] = mapped_column(Integer, index=True)
    label: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Float)
    x1: Mapped[int] = mapped_column(Integer)
    y1: Mapped[int] = mapped_column(Integer)
    x2: Mapped[int] = mapped_column(Integer)
    y2: Mapped[int] = mapped_column(Integer)
    motion: Mapped[str] = mapped_column(String(24))
    speed: Mapped[float] = mapped_column(Float)
    proximity: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(10))
    ttc: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasons: Mapped[str] = mapped_column(Text, default="")


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    type: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(10))  # low | medium | high
    track_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frame: Mapped[int] = mapped_column(Integer)
    video_time: Mapped[float] = mapped_column(Float, default=0.0)
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    session: Mapped[AnalysisSession] = relationship(back_populates="alerts")
