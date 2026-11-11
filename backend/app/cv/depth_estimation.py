"""Module D: relative depth. MiDaS-small (monocular) when available + always-on ground-plane perspective proxy.

Both give RELATIVE nearness in [0, 1] (1 = nearest). They are NOT metric distances.
Perspective assumption: a flat road and a camera whose horizon sits at HORIZON * frame height, so the lower the
object's bottom edge, the closer it is.
"""
import logging
import cv2
import numpy as np

log = logging.getLogger("depth")
HORIZON = 0.42


def perspective_proximity(box, frame_h: int, horizon: float = HORIZON) -> float:
    return float(np.clip((box[3] - horizon * frame_h) / ((1 - horizon) * frame_h), 0.0, 1.0))


def proximity_label(p: float) -> str:
    return "near" if p >= 0.66 else "medium" if p >= 0.33 else "far"


def object_depth(depth_norm: np.ndarray, box) -> float:
    """Median normalized nearness inside the central part of a box."""
    h, w = depth_norm.shape[:2]
    x1, y1, x2, y2 = box
    cx, cy, bw, bh = (x1 + x2) // 2, (y1 + y2) // 2, (x2 - x1) // 4, (y2 - y1) // 4
    roi = depth_norm[max(0, cy - bh):min(h, cy + bh + 1), max(0, cx - bw):min(w, cx + bw + 1)]
    return float(np.median(roi)) if roi.size else 0.0


def colorize(depth_norm: np.ndarray) -> np.ndarray:
    return cv2.applyColorMap((depth_norm * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)


class DepthEstimator:
    """Loads MiDaS-small via torch.hub (downloads weights on first use). Raises if torch/weights are unavailable."""

    def __init__(self):
        import torch
        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small", trust_repo=True).to(self.device).eval()
        self.transform = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True).small_transform

    def estimate(self, frame_bgr: np.ndarray) -> np.ndarray:
        t = self.torch
        inp = self.transform(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)).to(self.device)
        with t.no_grad():
            pred = self.model(inp)
            pred = t.nn.functional.interpolate(pred.unsqueeze(1), size=frame_bgr.shape[:2],
                                               mode="bicubic", align_corners=False).squeeze().cpu().numpy()
        return (pred - pred.min()) / (pred.max() - pred.min() + 1e-6)  # MiDaS = inverse depth -> 1 is near
