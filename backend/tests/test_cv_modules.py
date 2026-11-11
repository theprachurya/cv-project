import numpy as np
from app.cv.blind_spot import blind_spot_status
from app.cv.collision_risk import estimate_risk
from app.cv.depth_estimation import object_depth, perspective_proximity, proximity_label
from app.cv.optical_flow import box_flow, classify_motion
from app.services.alerts import AlertManager, evaluate_alerts


def test_lk_flow_measures_translation():
    tex = np.random.default_rng(1).integers(0, 255, (240, 320), dtype=np.uint8)
    moved = np.roll(tex, 5, axis=1)
    f = box_flow(tex, moved, (100, 80, 220, 180))
    assert f is not None and abs(f.dx - 5) < 1.0 and abs(f.dy) < 1.0


def test_motion_classes():
    assert classify_motion(0, 0, 0.02) == "approaching"
    assert classify_motion(0, 0, -0.02) == "receding"
    assert classify_motion(3, 0.2, 0.0) == "lateral"
    assert classify_motion(0.1, 0.1, 0.0) == "stationary"


def test_risk_levels_and_ttc():
    hi = estimate_risk("car", 0.9, "approaching", 0.04, 0.5, 30)
    assert hi.level == "high" and abs(hi.ttc - 0.8) < 0.1
    assert estimate_risk("car", 0.2, "lateral", 0.0, 0.1, 30).level == "low"
    assert estimate_risk("car", 0.9, "receding", -0.02, 0.5, 30).level == "low"
    assert estimate_risk("car", 0.9, "approaching", 0.04, 0.5, 30, medium=35, high=99).level == "medium"


def test_traffic_light_is_not_scored_as_a_collision_target():
    r = estimate_risk("traffic light", 1.0, "approaching", 0.04, 0.5, 30)
    assert r.level == "low" and r.score == 0 and r.ttc is None
    alerts = evaluate_alerts(AlertManager(), [{**_info(label="traffic light", proximity=1.0, risk_level="low")}],
                             {"left": {"level": "clear", "ids": []}, "right": {"level": "clear", "ids": []}},
                             1, 0.0, 30)
    assert alerts == []


def test_depth_helpers():
    assert perspective_proximity((0, 0, 10, 360), 360) == 1.0
    assert perspective_proximity((0, 0, 10, 100), 360) == 0.0
    assert proximity_label(0.8) == "near" and proximity_label(0.1) == "far"
    d = np.zeros((100, 100)); d[40:60, 40:60] = 0.9
    assert object_depth(d, (30, 30, 70, 70)) == 0.9


def _info(**kw):
    base = dict(id=1, label="car", cx_frac=0.1, dx=3.0, proximity=0.7, motion="lateral", cx=60.0, cy=200.0, ttc=None,
                risk_level="low", risk_score=10, reasons=[])
    base.update(kw); return base


def test_blind_spot_zones():
    bs = blind_spot_status([_info(), _info(id=2, cx_frac=0.5)])
    assert bs["left"]["level"] == "high" and bs["left"]["ids"] == [1]
    assert bs["right"]["level"] == "clear"


def test_alert_cooldown_and_escalation():
    m = AlertManager()
    a = lambda sev, f: m.raise_alert("Collision Risk", sev, 7, f, 0, 0, 0, "x", 100)
    assert a("medium", 1) is not None
    assert a("medium", 20) is None          # cooldown
    assert a("high", 21) is not None        # escalation passes
    assert a("high", 150) is not None       # cooldown expired


def test_evaluate_alerts_types():
    bs = blind_spot_status([_info()])
    out = evaluate_alerts(AlertManager(), [_info(risk_level="high", risk_score=80, reasons=["r"])], bs, 1, 0.0, 100)
    assert {"Collision Risk", "Left Blind Spot"} <= {a["type"] for a in out}
