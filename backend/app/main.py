import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import system, analysis, sessions
from app.core.config import settings
from app.core.logging import setup_logging
from app.database.session import Base, engine
import app.models  # noqa: F401  (registers tables)

setup_logging()
log = logging.getLogger("road_safety")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.report_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    log.info("Database ready, backend started")
    yield


app = FastAPI(title="Smart Road Safety & Blind Spot Detection", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","),
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(system.router)
app.include_router(analysis.router)
app.include_router(analysis.ws_router)
app.include_router(sessions.router)
