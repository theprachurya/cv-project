from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./road_safety.db"
    upload_dir: Path = Path("../sample_videos")
    report_dir: Path = Path("../reports")
    cors_origins: str = "http://localhost:5173"
    yolo_model: str = "models/roadsafety-yolov8n.pt"
    conf_threshold: float = 0.4
    frame_width: int = 640
    frame_skip: int = 1
    lost_track_buffer: int = 30  # frames a lost track is remembered before its ID is retired
    track_min_hits: int = 3  # detections needed before a track is shown/counted


settings = Settings()
