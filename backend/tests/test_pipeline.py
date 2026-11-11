"""End-to-end: synthetic video of a car growing toward the camera, fake detector, real flow/risk/alerts/DB/PDF."""
import cv2
import numpy as np
from fastapi.testclient import TestClient
from app.cv.detector import Detection
from app.main import app
from app.services.analysis import runner


def box(k):
    w = int(50 * 1.04 ** k); y2 = 170 + 4 * k
    return (320 - w // 2, y2 - int(w * 0.7), 320 + w // 2, y2)


class FakeDetector:
    conf = 0.4
    def __init__(self): self.n = 0
    def detect(self, frame):
        k = self.n; self.n += 1
        return [Detection("car", 0.9, box(k))]


def make_video(path, n=40):
    tex = np.random.default_rng(0).integers(0, 255, (80, 80, 3), dtype=np.uint8)
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 30, (640, 360))
    for k in range(n):
        f = np.full((360, 640, 3), 90, np.uint8)
        x1, y1, x2, y2 = box(k)
        f[y1:y2, x1:x2] = cv2.resize(tex, (x2 - x1, y2 - y1))
        vw.write(f)
    vw.release()


def test_full_pipeline(tmp_path):
    vid = tmp_path / "approach.mp4"
    make_video(vid)
    with TestClient(app) as c:
        runner._detector, runner._depth_tried = FakeDetector(), True
        runner.start("video", vid)
        runner._thread.join(timeout=60)
        st = runner.state()
        assert st["status"] == "ended", st["error"]
        sm = st["summary"]
        assert sm["frames_analyzed"] == 40 and sm["unique_objects"] == 1
        assert sm["motion_distribution"].get("approaching", 0) > 10
        assert sm["total_alerts"] >= 1 and sm["risk_distribution"]["high"] + sm["risk_distribution"]["medium"] > 0
        sid = st["session_id"]
        assert any(s["id"] == sid for s in c.get("/api/sessions").json())
        detections = c.get(f"/api/detections?session_id={sid}&limit=10")
        assert detections.status_code == 200 and detections.json()
        assert detections.json()[0]["label"] == "car"
        assert c.get("/api/detections?session_id=999999").status_code == 404
        al = c.get(f"/api/alerts?session_id={sid}").json()
        assert al and c.patch(f"/api/alerts/{al[0]['id']}/ack").json()["acknowledged"]
        pdf = c.get(f"/api/sessions/{sid}/report.pdf")
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
        assert c.get(f"/api/sessions/{sid}/report.json").json()["summary"]["unique_objects"] == 1
        with c.websocket_connect("/ws/state") as ws:
            assert ws.receive_json()["status"] == "ended"
        bad = c.put("/api/settings", json={"medium_risk": 80, "high_risk": 60})
        assert bad.status_code == 422
