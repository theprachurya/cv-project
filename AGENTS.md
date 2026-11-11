# Instructions for coding agents

## Project scope

This repository is a learning project that simulates driver-assistance analysis from a webcam or uploaded road video. It is not a certified safety system. The left/right zones are regions in the camera image, not physical blind-spot sensors; depth and time-to-collision values are relative heuristics, not calibrated measurements.

Before making changes, read `README.md` for architecture, setup, data attribution, model details, and known limitations. Read `datasets/README.md` before changing or redistributing training data or video assets.

## Repository map

- `backend/app/`: FastAPI API, SQLAlchemy persistence, frame analysis, detection, tracking, optical flow, depth, risk, and alerts.
- `backend/scripts/`: download/prepare public training data and train/evaluate the YOLO detector.
- `backend/tests/`: backend unit and API tests.
- `backend/models/`: application YOLO checkpoint and recorded training metrics.
- `frontend/src/`: React/TypeScript dashboard, API clients, hooks, and views.
- `datasets/README.md`: dataset sources, licenses, attribution, and class mapping. Training data itself is downloaded/generated locally.
- `sample_videos/README.md`: optional demo-video attribution. Media files are not committed.
- `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`: containerized setup.

## Local setup

Use Python 3.12 for native development and Node.js 18 or newer for the frontend. Follow the Windows GPU install commands in `README.md` when using CUDA; otherwise install a PyTorch build appropriate for the machine before installing `backend/requirements.txt`.

Backend, from `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu130
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Run the frontend in a second terminal from `frontend/` with `npm ci` and `npm run dev`; open `http://localhost:5173`. The API documentation is at `http://localhost:8000/docs`. For uploaded-video Docker use, run `docker compose up --build` from the repository root.

The default application detector is `backend/models/roadsafety-yolov8n.pt`. MiDaS-small weights download through `torch.hub` on first use and require internet access. Training data is not checked in; see `README.md` and `datasets/README.md` for the reproducible download and training commands.

## Change guidance

- Keep API request/response types aligned between `backend/app/` and `frontend/src/types/index.ts` / `frontend/src/services/api.ts`.
- Preserve dataset and demo-media attribution when adding data.
- Do not commit `.env` files, databases, downloaded/prepared datasets, generated build output, caches, or local videos. The fine-tuned application checkpoint is intentionally included.
- Describe risk, depth, and motion as estimates and preserve the project's simulation and safety limitations in user-facing copy.

