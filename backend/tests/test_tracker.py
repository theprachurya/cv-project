from app.cv.detector import Detection
from app.cv.tracker import Tracker


def car(x, y=100, conf=0.9, label="car"):
    return Detection(label, conf, (x, y, x + 60, y + 40))


def run(frames, **kw):
    tr = Tracker(**kw)
    return tr, [tr.update(f, i + 1) for i, f in enumerate(frames)]


def test_same_id_for_moving_object_and_displacement():
    tr, outs = run([[car(100 + 5 * i)] for i in range(10)], min_hits=2)
    ids = {t.id for o in outs for t in o}
    assert len(ids) == 1
    t = outs[-1][0]
    assert abs(t.displacement[0] - 5) < 1e-6 and t.displacement[1] == 0
    assert t.prev_box != t.box


def test_two_objects_get_distinct_ids():
    tr, outs = run([[car(50 + 3 * i), car(400 - 3 * i, 250, label="truck")] for i in range(8)], min_hits=2)
    assert len({t.id for t in outs[-1]}) == 2
    assert tr.unique_by_label() == {"car": 1, "truck": 1}


def test_id_survives_short_detection_loss():
    frames = [[car(100 + 4 * i)] for i in range(6)] + [[], []] + [[car(100 + 4 * i)] for i in range(8, 14)]
    tr, outs = run(frames, min_hits=2)
    assert len({t.id for o in outs for t in o}) == 1
    assert sum(tr.unique_by_label().values()) == 1
