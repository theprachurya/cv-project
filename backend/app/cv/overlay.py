import cv2
import numpy as np

COL = {"low": (94, 197, 34), "medium": (8, 179, 234), "high": (68, 68, 239), "clear": (120, 120, 120)}  # BGR


def _label(frame, text, x, y, color):
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv2.rectangle(frame, (x, max(0, y - th - 6)), (x + tw + 6, y), color, -1)
    cv2.putText(frame, text, (x + 3, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)


def draw_scene(frame, tracks, infos):
    for t, i in zip(tracks, infos):
        x1, y1, x2, y2 = i["box"]
        c = COL[i["risk_level"]]
        cv2.rectangle(frame, (x1, y1), (x2, y2), c, 2)
        if len(t.trail) > 1:
            cv2.polylines(frame, [np.array(t.trail, np.int32)], False, c, 1, cv2.LINE_AA)
        _label(frame, f"#{i['id']} {i['label']} {i['confidence']:.0%}", x1, y1, c)
        extra = f" TTC {i['ttc']}s" if i["ttc"] is not None else ""
        _label(frame, f"{i['motion']} | {i['depth_label']}{extra}", x1, y2 + 18, c)
        if i["magnitude"] > 0.5:  # LK motion vector
            cx, cy = int(i["cx"]), int(i["cy"])
            cv2.arrowedLine(frame, (cx, cy), (int(cx + i["dx"] * 8), int(cy + i["dy"] * 8)), (255, 255, 255), 2, tipLength=0.3)
    return frame


def draw_regions(frame, bs, side_frac):
    h, w = frame.shape[:2]
    zones = {"left": (0, int(w * side_frac)), "right": (int(w * (1 - side_frac)), w)}
    layer = frame.copy()
    for side, (x0, x1) in zones.items():
        cv2.rectangle(layer, (x0, 0), (x1, h), COL[bs[side]["level"]], -1)
    cv2.addWeighted(layer, 0.14, frame, 0.86, 0, frame)
    for side, (x0, x1) in zones.items():
        lvl = bs[side]["level"]
        cv2.line(frame, (x1 if side == "left" else x0, 0), (x1 if side == "left" else x0, h), COL[lvl], 1)
        if lvl in ("medium", "high"):
            _label(frame, f"{side.upper()} ALERT", x0 + 6, 26, COL[lvl])
    return frame
