"""Download small public traffic datasets and merge road labels into COCO IDs.

The pretrained YOLOv8n head stays at 80 COCO classes, so the application keeps
its existing COCO class IDs (including motorcycle) after road-scene fine-tuning.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "datasets"
RAW = DATASETS / "raw"
OUTPUT = DATASETS / "road_safety_mixed"

# COCO 2017 category names in their canonical YOLO class order.
COCO_NAMES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
    "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard",
    "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
    "scissors", "teddy bear", "hair drier", "toothbrush",
]

DATASETS = {
    "soban": {
        "repo": "SobanHM/Road-Objects-Detection-Dataset",
        "mapping": {"bike": 1, "bicycle": 1, "bus": 5, "car": 2, "person": 0,
                    "traffic signal": 9, "traffic light": 9, "truck": 7},
    },
    "libre": {
        "repo": "LibreYOLO/road-traffic",
        "mapping": {"bicycles": 1, "bicycle": 1, "buses": 5, "bus": 5,
                    "motorcycles": 3, "motorcycle": 3, "taxis": 2, "taxi": 2, "vehicles": 2},
    },
}
SPLITS = {"train": "train", "valid": "val", "test": "test"}


def _names(data_yaml: Path) -> dict[int, str]:
    raw = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))["names"]
    return {int(k): str(v).strip().lower() for k, v in raw.items()} if isinstance(raw, dict) else {
        i: str(v).strip().lower() for i, v in enumerate(raw)
    }


def download_sources() -> dict[str, Path]:
    roots = {}
    patterns = ["data.yaml", "README.md", "train/images/**", "train/labels/**",
                "valid/images/**", "valid/labels/**", "test/images/**", "test/labels/**"]
    for slug, spec in DATASETS.items():
        dest = RAW / slug
        snapshot_download(repo_id=spec["repo"], repo_type="dataset", local_dir=str(dest),
                          allow_patterns=patterns, max_workers=4)
        roots[slug] = dest
    return roots


def prepare(download: bool = True) -> Path:
    source_roots = download_sources() if download else {name: RAW / name for name in DATASETS}
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    totals = {split: 0 for split in SPLITS.values()}
    for slug, source_root in source_roots.items():
        class_names = _names(source_root / "data.yaml")
        name_to_coco = DATASETS[slug]["mapping"]
        id_to_coco = {class_id: name_to_coco[name] for class_id, name in class_names.items() if name in name_to_coco}
        for source_split, dest_split in SPLITS.items():
            image_dir = source_root / source_split / "images"
            label_dir = source_root / source_split / "labels"
            if not image_dir.is_dir() or not label_dir.is_dir():
                continue
            for image in sorted(image_dir.iterdir()):
                if image.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                    continue
                label = label_dir / f"{image.stem}.txt"
                if not label.is_file():
                    raise FileNotFoundError(f"Missing annotation file for {image}")
                rows = []
                for line in label.read_text(encoding="utf-8").splitlines():
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    try:
                        source_class = int(parts[0])
                        values = [float(value) for value in parts[1:5]]
                    except ValueError:
                        continue
                    if source_class in id_to_coco and all(0 <= value <= 1 for value in values):
                        rows.append(f"{id_to_coco[source_class]} " + " ".join(f"{v:.7f}" for v in values))
                output_image_dir = OUTPUT / "images" / dest_split
                output_label_dir = OUTPUT / "labels" / dest_split
                output_image_dir.mkdir(parents=True, exist_ok=True)
                output_label_dir.mkdir(parents=True, exist_ok=True)
                target_name = f"{slug}_{image.name}"
                shutil.copy2(image, output_image_dir / target_name)
                (output_label_dir / f"{Path(target_name).stem}.txt").write_text("\n".join(rows), encoding="utf-8")
                totals[dest_split] += 1

    if not totals["train"] or not totals["val"] or not totals["test"]:
        raise RuntimeError(f"Prepared dataset is missing a split: {totals}")
    config = {"path": str(OUTPUT.resolve()), "train": "images/train", "val": "images/val", "test": "images/test",
              "names": COCO_NAMES}
    (OUTPUT / "data.yaml").write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"Prepared {totals['train']} train / {totals['val']} validation / {totals['test']} test images at {OUTPUT}")
    return OUTPUT / "data.yaml"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-download", action="store_true", help="Use datasets already present under datasets/raw")
    args = parser.parse_args()
    prepare(download=not args.no_download)


if __name__ == "__main__":
    main()
