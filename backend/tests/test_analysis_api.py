from fastapi.testclient import TestClient
from app.main import app


def test_rejects_bad_extension():
    with TestClient(app) as c:
        r = c.post("/api/videos", files={"file": ("x.txt", b"hi")})
        assert r.status_code == 400


def test_start_missing_video_404():
    with TestClient(app) as c:
        assert c.post("/api/analysis/start", json={"source": "video", "filename": "nope.mp4"}).status_code == 404
        assert c.post("/api/analysis/start", json={"source": "video"}).status_code == 400
