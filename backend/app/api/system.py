from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.services.analysis import runner

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/status")
def status():
    return {
        "backend": "online",
        "processing": runner.state()["status"],
        "source": runner.state()["source"],
        "model": settings.yolo_model,
        "conf_threshold": settings.conf_threshold,
        "time": datetime.now(timezone.utc).isoformat(),
    }
