# Smart Road Safety & Blind Spot Detection (Computer Vision)

A driver-assistance **simulation** built for learning. It is not a certified safety system, and a single
front-facing camera cannot detect real physical blind spots: the left/right zones are a camera-image simulation.

For coding-agent setup and repository conventions, see [AGENTS.md](AGENTS.md).

## Architecture and data flow
```
Webcam / uploaded video
   -> FastAPI runner thread (resize, frame skip)
   -> YOLOv8 detection            cv/detector.py
   -> ByteTrack IDs + history     cv/tracker.py      (IDs survive short detection loss)
   -> Lucas-Kanade flow per object + Farneback dense view   cv/optical_flow.py
   -> Relative depth: MiDaS-small + ground-plane perspective  cv/depth_estimation.py
   -> Rule-based risk 0-100 + time-to-collision   cv/collision_risk.py
   -> Left/right zone simulation  cv/blind_spot.py
   -> Alerts with per-object cooldown  services/alerts.py
   -> SQLite (sessions, tracks, detections, alerts, summary)  +  WebSocket /ws/state  +  MJPEG /api/stream
   -> React dashboard (video, risk, motion table, alerts, analytics, history, PDF report)
```
Video frames go over MJPEG (`/api/stream`), live data over a WebSocket (`/ws/state`), and controls over REST.

## Run locally
Backend (Windows PowerShell, Python 3.12, NVIDIA GPU):
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu130
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
pytest                                                  # 17 tests
```
Frontend (Node 18+), in a second PowerShell terminal:
```powershell
cd frontend
npm install
npm run dev
```
Then open http://localhost:5173.

If you ran an earlier stage, delete `backend/road_safety.db` once: the database tables changed.

## Models (all free, no API keys)
- **Road-adapted YOLOv8n**: `backend/models/roadsafety-yolov8n.pt` is the default application detector. It starts from the pretrained 80-class COCO YOLOv8n model and is fine-tuned on two small public traffic datasets, with labels mapped back to COCO class IDs. The backend keeps pedestrian, bicycle, car, motorcycle, bus, truck, and traffic-light detections.
- **MiDaS-small**: downloaded via `torch.hub` on first run (needs internet once, then cached). If it cannot load,
  the app falls back to perspective-only proximity and says so in the Risk panel ("depth: perspective").

## Download data and retrain the detector

The included training workflow downloads two CC BY 4.0 public datasets from Hugging Face: [Road Objects Detection Dataset](https://huggingface.co/datasets/SobanHM/Road-Objects-Detection-Dataset) and [Roboflow 100 Road Traffic](https://huggingface.co/datasets/LibreYOLO/road-traffic). The first supplies pedestrian, bicycle, car, bus, and truck examples. The second adds motorcycle examples. The workflow keeps the 80-class COCO output head, so the app's class IDs remain compatible.

On Windows with Python 3.12 and an NVIDIA GPU, run from `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu130
python -m pip install -r requirements.txt
python -m scripts.prepare_training_data
python -m scripts.train_detector --epochs 8 --imgsz 416 --batch 2 --device 0
```

Preparation stores source files under `datasets/raw/` and makes the merged YOLO dataset under `datasets/road_safety_mixed/`. Training uses mixed precision, 416-pixel images, batch size 2, and zero data-loader workers to fit a 4 GB RTX 3050. It evaluates the held-out test split and copies the best checkpoint to `backend/models/roadsafety-yolov8n.pt`; metrics go in `backend/models/training_metrics.json`. Dataset copies and training runs are ignored by Git, while the application checkpoint is retained.

Current checkpoint run: 8 epochs; held-out precision 70.5%, recall 37.8%, mAP@0.50 39.9%, and mAP@0.50:0.95 26.4% on 229 test images. A development-only demo clip produced 13 detections across 8 sampled frames in a model-loading smoke check. These are results from a small mixed-source classroom dataset, not a safety benchmark.

See [datasets/README.md](datasets/README.md) for source attribution, licenses, and class mapping. The small fine-tuning corpus supports a classroom adaptation run, not a road-certified detector benchmark.

## Test videos
Use a short forward-facing dashcam clip (MP4). Video files are not included in this repository; add a local MP4 through the upload control. The Hugging Face mixed-traffic dataset contains anonymized clips, but its full archive is about 12 GB, so download only a single clip if you need a ready-made demo video. Keep its attribution when redistributing a clip. A phone video recorded from a parked position can also exercise upload, tracking, and alert history, but it does not establish real-world vehicle safety performance.

## How the key numbers are computed (and their limits)
- **Depth/proximity** is *relative* (0 to 1, near/medium/far), never meters. It averages MiDaS with a flat-road
  perspective estimate (lower object bottom edge = closer; horizon assumed at 42% of frame height).
- **Motion class**: approaching/receding from the object's size growth (box scale + LK feature expansion);
  lateral/stationary from LK translation. Ego-motion of the host vehicle is not compensated.
- **Time-to-collision** = 1 / (growth rate per second), assuming constant closing speed. Treat it as a rough indicator.
- **Risk score** = proximity (35) + approach rate (25) + TTC (25) + position in driving path (15), reduced for
  receding or still objects. Thresholds are editable in the dashboard.

## Configuration (`backend/.env`)
`CONF_THRESHOLD`, `FRAME_WIDTH` (smaller = faster), `FRAME_SKIP` (2 or 3 for slow laptops), `LOST_TRACK_BUFFER`, `TRACK_MIN_HITS`.
Alert thresholds, cooldown, zone width and the video view (detection / optical flow / depth) change live in the UI.

## API summary
`POST /api/videos` · `POST /api/analysis/start|stop|pause|resume` · `GET /api/analysis/state` · `GET /api/stream` ·
`WS /ws/state` · `GET /api/alerts` · `GET /api/detections?session_id=<id>&limit=100&offset=0` · `PATCH /api/alerts/{id}/ack` · `GET /api/analytics` · `GET /api/sessions` ·
`GET /api/sessions/{id}/report.pdf|report.json` · `GET|PUT /api/settings`. Interactive docs at http://localhost:8000/docs.

## Docker
`docker compose up --build` (uploaded videos only; webcam is easier natively).
