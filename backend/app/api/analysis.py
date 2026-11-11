import asyncio
import time
import uuid
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.config import settings
from app.services.analysis import runner

router = APIRouter(prefix="/api", tags=["analysis"])
ws_router = APIRouter()
ALLOWED = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MAX_BYTES = 500 * 1024 * 1024


class StartRequest(BaseModel):
    source: Literal["webcam", "video"]
    filename: str | None = None


@router.post("/videos", status_code=201)
async def upload_video(file: UploadFile):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Unsupported file type. Use one of: {', '.join(sorted(ALLOWED))}")
    name = f"{uuid.uuid4().hex[:8]}_{Path(file.filename).name}"
    dest = settings.upload_dir / name
    size = 0
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_BYTES:
                out.close(); dest.unlink(missing_ok=True)
                raise HTTPException(413, "Video exceeds the 500 MB limit")
            out.write(chunk)
    return {"filename": name, "size": size}


@router.post("/analysis/start")
def start(req: StartRequest):
    path = None
    if req.source == "video":
        if not req.filename:
            raise HTTPException(400, "filename is required for video analysis")
        path = settings.upload_dir / Path(req.filename).name
        if not path.is_file():
            raise HTTPException(404, "Video not found. Upload it first.")
    runner.start(req.source, path)
    return runner.state()


@router.post("/analysis/stop")
def stop():
    runner.stop(); return runner.state()


@router.post("/analysis/pause")
def pause():
    runner.pause(); return runner.state()


@router.post("/analysis/resume")
def resume():
    runner.resume(); return runner.state()


@router.get("/analysis/state")
def state():
    return runner.state()


@router.get("/stream")
def stream():
    def gen():
        last = -1
        while True:
            fid, jpeg = runner.latest()
            if jpeg is not None and fid != last:
                last = fid
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            elif runner.state()["status"] in ("idle", "stopped", "ended", "error"):
                return
            time.sleep(0.02)
    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")


@ws_router.websocket("/ws/state")
async def ws_state(ws: WebSocket):
    """Pushes the live analysis state (tracks, risk, alerts, summary) ~4x per second."""
    await ws.accept()
    try:
        while True:
            await ws.send_json(runner.state())
            await asyncio.sleep(0.25)
    except (WebSocketDisconnect, RuntimeError):
        pass
