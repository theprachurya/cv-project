from fastapi.testclient import TestClient
from app.main import app


def test_status():
    with TestClient(app) as c:
        r = c.get("/api/status")
        assert r.status_code == 200
        assert r.json()["backend"] == "online"
