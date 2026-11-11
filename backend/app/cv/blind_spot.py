"""Module F: camera-based left/right monitoring-zone simulation (NOT a physical blind-spot sensor)."""
VEHICLES = {"car", "truck", "bus", "motorcycle"}
RANK = {"clear": 0, "low": 1, "medium": 2, "high": 3}


def region_of(cx_frac: float, side_frac: float) -> str:
    return "left" if cx_frac < side_frac else "right" if cx_frac > 1 - side_frac else "center"


def blind_spot_status(infos: list[dict], side_frac: float = 0.3) -> dict:
    out = {"left": {"level": "clear", "ids": []}, "right": {"level": "clear", "ids": []}}
    for i in infos:
        side = region_of(i["cx_frac"], side_frac)
        if side == "center" or i["label"] not in VEHICLES:
            continue
        toward_center = i["dx"] > 0.5 if side == "left" else i["dx"] < -0.5
        closing = toward_center or i["motion"] == "approaching"
        p = i["proximity"]
        level = "high" if (p >= 0.6 and closing) else "medium" if ((p >= 0.35 and closing) or p >= 0.6) else "low"
        s = out[side]
        s["ids"].append(i["id"])
        if RANK[level] > RANK[s["level"]]:
            s["level"] = level
    return out
