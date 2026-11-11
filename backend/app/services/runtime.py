"""Live-editable thresholds (changed from the dashboard while analysis runs)."""
import threading
from typing import Literal
from pydantic import BaseModel, Field, model_validator
from app.core.config import settings


class RuntimeSettings(BaseModel):
    conf_threshold: float = Field(settings.conf_threshold, ge=0.05, le=0.95)
    medium_risk: int = Field(35, ge=1, le=99)
    high_risk: int = Field(65, ge=2, le=100)
    cooldown_s: float = Field(5.0, ge=0, le=60)
    side_frac: float = Field(0.3, ge=0.1, le=0.45)
    close_proximity: float = Field(0.8, ge=0.3, le=1.0)
    use_depth: bool = True
    depth_every: int = Field(5, ge=1, le=60)
    view: Literal["detection", "flow", "depth"] = "detection"

    @model_validator(mode="after")
    def _order(self):
        if self.high_risk <= self.medium_risk:
            raise ValueError("high_risk must be greater than medium_risk")
        return self


_lock = threading.Lock()
_current = RuntimeSettings()


def get() -> RuntimeSettings:
    with _lock:
        return _current


def set_(new: RuntimeSettings) -> RuntimeSettings:
    global _current
    with _lock:
        _current = new
        return _current
