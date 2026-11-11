"""Module A: YOLO object detection (COCO classes relevant to road safety)."""
from dataclasses import dataclass
import cv2
import numpy as np

CLASS_MAP = {0: "pedestrian", 1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck", 9: "traffic light"}
COLORS = {  # BGR
    "pedestrian": (0, 165, 255), "bicycle": (255, 200, 0), "car": (246, 130, 59),
    "motorcycle": (200, 80, 200), "bus": (80, 200, 120), "truck": (60, 200, 230),
    "traffic light": (40, 220, 255),
}


@dataclass
class Detection:
    label: str
    confidence: float
    box: tuple[int, int, int, int]  # x1, y1, x2, y2


def parse_boxes(cls_ids, confs, xyxy, min_conf: float) -> list[Detection]:
    """Convert raw YOLO arrays into Detections, keeping only road-relevant classes above min_conf."""
    out = []
    for c, p, b in zip(cls_ids, confs, xyxy):
        c = int(c)
        if c in CLASS_MAP and float(p) >= min_conf:
            out.append(Detection(CLASS_MAP[c], float(p), tuple(int(v) for v in b)))
    return out


class Detector:
    def __init__(self, model_name: str, conf: float):
        from ultralytics import YOLO  # imported lazily: heavy, downloads weights on first use
        self.model = YOLO(model_name)
        self.conf = conf

    def detect(self, frame: np.ndarray) -> list[Detection]:
        res = self.model.predict(frame, conf=self.conf, classes=list(CLASS_MAP), verbose=False)[0]
        b = res.boxes
        return parse_boxes(b.cls.cpu().numpy(), b.conf.cpu().numpy(), b.xyxy.cpu().numpy(), self.conf)


def draw_detections(frame: np.ndarray, dets: list[Detection]) -> np.ndarray:
    for d in dets:
        x1, y1, x2, y2 = d.box
        color = COLORS.get(d.label, (255, 255, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        text = f"{d.label} {d.confidence:.0%}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, max(0, y1 - th - 8)), (x1 + tw + 6, y1), color, -1)
        cv2.putText(frame, text, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    return frame
