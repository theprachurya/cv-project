"""Module C: Lucas-Kanade (sparse, per object) and Farneback (dense) optical flow + motion classification."""
from dataclasses import dataclass
import cv2
import numpy as np

LK = dict(winSize=(15, 15), maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))


@dataclass
class FlowResult:
    dx: float          # median horizontal motion of tracked features (px/frame)
    dy: float          # median vertical motion (px/frame)
    magnitude: float   # hypot(dx, dy)
    expansion: float   # relative outward growth of the feature cloud per frame (>0 = expanding = approaching)
    points: int


def box_flow(prev_gray: np.ndarray, gray: np.ndarray, box) -> FlowResult | None:
    h, w = gray.shape[:2]
    x1, y1, x2, y2 = max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3])
    if x2 - x1 < 12 or y2 - y1 < 12:
        return None
    pts = cv2.goodFeaturesToTrack(prev_gray[y1:y2, x1:x2], maxCorners=40, qualityLevel=0.01, minDistance=4)
    if pts is None or len(pts) < 4:
        return None
    pts = (pts + np.array([[x1, y1]], dtype=np.float32)).astype(np.float32)
    nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, pts, None, **LK)
    ok = st.ravel() == 1
    p0, p1 = pts[ok].reshape(-1, 2), nxt[ok].reshape(-1, 2)
    if len(p0) < 4:
        return None
    flow = p1 - p0
    dx, dy = float(np.median(flow[:, 0])), float(np.median(flow[:, 1]))
    rel = p0 - np.array([(x1 + x2) / 2, (y1 + y2) / 2], dtype=np.float32)
    r2 = (rel ** 2).sum(axis=1) + 1e-6
    # residual flow after removing translation; its radial part / radius is the scale change per frame
    expansion = float(np.mean(((flow - [dx, dy]) * rel).sum(axis=1) / r2))
    return FlowResult(dx, dy, float(np.hypot(dx, dy)), expansion, len(p0))


def classify_motion(dx: float, dy: float, growth: float, still_px: float = 0.6, grow_thr: float = 0.008) -> str:
    """Combine apparent size change (growth) with image-plane translation into a motion class."""
    if growth >= grow_thr:
        return "approaching"
    if growth <= -grow_thr:
        return "receding"
    if abs(dx) > still_px and abs(dx) >= abs(dy):
        return "lateral"
    return "stationary"


def dense_flow_overlay(prev_gray: np.ndarray, gray: np.ndarray, frame: np.ndarray, scale: float = 0.5) -> np.ndarray:
    """Farneback dense flow rendered as HSV (hue = direction, brightness = speed), blended over the frame."""
    a = cv2.resize(prev_gray, None, fx=scale, fy=scale)
    b = cv2.resize(gray, None, fx=scale, fy=scale)
    flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    hsv = np.zeros((*a.shape, 3), np.uint8)
    hsv[..., 0] = ang * 180 / np.pi / 2
    hsv[..., 1] = 255
    hsv[..., 2] = np.clip(mag * 12, 0, 255).astype(np.uint8)
    vis = cv2.resize(cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR), (frame.shape[1], frame.shape[0]))
    return cv2.addWeighted(frame, 0.45, vis, 0.55, 0)
