"""Fine-tune the COCO-pretrained nano detector with low-VRAM settings."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[2]
DATA_YAML = ROOT / "datasets" / "road_safety_mixed" / "data.yaml"
RUNS = ROOT / "training" / "runs"
WEIGHTS_DIR = ROOT / "backend" / "models"
FINAL_WEIGHTS = WEIGHTS_DIR / "roadsafety-yolov8n.pt"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--imgsz", type=int, default=416)
    parser.add_argument("--batch", type=int, default=2)
    parser.add_argument("--device", default="0", help="CUDA device index, or 'cpu'")
    parser.add_argument("--weights", default="yolov8n.pt", help="COCO-pretrained Ultralytics checkpoint")
    args = parser.parse_args()
    if not DATA_YAML.is_file():
        raise FileNotFoundError(f"Dataset not found at {DATA_YAML}. Run scripts/prepare_training_data.py first.")

    model = YOLO(args.weights)
    model.train(
        data=str(DATA_YAML), epochs=args.epochs, imgsz=args.imgsz, batch=args.batch, device=args.device,
        workers=0, amp=True, cache=False, patience=3, close_mosaic=2, seed=42, deterministic=True,
        project=str(RUNS), name="roadsafety-yolov8n", exist_ok=True, plots=False, save=True,
    )
    run_dir = Path(model.trainer.save_dir)
    best = run_dir / "weights" / "best.pt"
    if not best.is_file():
        raise FileNotFoundError(f"Training completed without a best checkpoint: {best}")
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, FINAL_WEIGHTS)

    trained = YOLO(str(FINAL_WEIGHTS))
    metrics = trained.val(data=str(DATA_YAML), split="test", imgsz=args.imgsz, batch=args.batch,
                          device=args.device, workers=0, plots=False)
    summary = {
        "model": FINAL_WEIGHTS.name,
        "base_checkpoint": args.weights,
        "dataset": "SobanHM/Road-Objects-Detection-Dataset + LibreYOLO/road-traffic",
        "device": args.device,
        "epochs_requested": args.epochs,
        "epochs_completed": max(0, len((run_dir / "results.csv").read_text(encoding="utf-8").splitlines()) - 1),
        "imgsz": args.imgsz,
        "batch": args.batch,
        "test_split": {key: float(value) for key, value in metrics.results_dict.items()},
    }
    (WEIGHTS_DIR / "training_metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Saved application detector: {FINAL_WEIGHTS}")


if __name__ == "__main__":
    main()
