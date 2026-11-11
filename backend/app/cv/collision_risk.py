"""Module E: explainable rule-based collision risk (0-100) with optional time-to-collision."""
from dataclasses import dataclass, field

VULNERABLE = {"pedestrian", "bicycle", "motorcycle"}
NON_COLLISION_TARGETS = {"traffic light"}


@dataclass
class Risk:
    score: int
    level: str
    ttc: float | None
    reasons: list[str] = field(default_factory=list)


def estimate_risk(label: str, proximity: float, motion: str, growth: float, cx_frac: float,
                  fps: float, medium: float = 35, high: float = 65) -> Risk:
    """Points: proximity (35) + approach rate (25) + time-to-collision (25) + position in driving path (15).

    TTC ~= 1 / (relative growth per second) assumes a roughly constant closing speed. It is a rough estimate.
    """
    if label in NON_COLLISION_TARGETS:
        return Risk(0, "low", None, ["static road signal excluded from collision scoring"])
    reasons = []
    approaching = motion == "approaching"
    pts = 35 * proximity
    if proximity >= 0.5:
        reasons.append(f"close to camera ({proximity:.0%} nearness)")
    ttc = None
    if approaching and growth > 0.004 and fps > 0:
        t = 1.0 / (growth * fps)
        ttc = round(t, 1) if t <= 30 else None
    if approaching:
        pts += 25 * min(growth / 0.04, 1.0)
        reasons.append(f"growing {growth:.1%} per frame (approaching)")
    if ttc is not None:
        pts += 25 if ttc <= 2 else 15 if ttc <= 4 else 6 if ttc <= 8 else 0
        reasons.append(f"estimated time-to-collision {ttc:.1f}s")
    centrality = 1 - min(abs(cx_frac - 0.5) / 0.5, 1.0)
    pts += 15 * centrality * (1.0 if (approaching or proximity > 0.5) else 0.3)
    if centrality > 0.6 and proximity > 0.4:
        reasons.append("in the driving path")
    if motion == "receding":
        pts *= 0.4
    elif motion == "stationary" and proximity < 0.6:
        pts *= 0.5
    if label in VULNERABLE and proximity > 0.4:
        pts += 5
        reasons.append(f"vulnerable road user ({label})")
    score = int(max(0, min(100, round(pts))))
    level = "high" if score >= high else "medium" if score >= medium else "low"
    return Risk(score, level, ttc, reasons)
