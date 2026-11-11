import numpy as np
from app.cv.detector import parse_boxes, draw_detections


def test_filters_classes_and_confidence():
    dets = parse_boxes([2, 99, 0, 7, 9], [0.9, 0.9, 0.2, 0.6, 0.8],
                       [[1, 2, 30, 40]] * 5, min_conf=0.4)
    assert [d.label for d in dets] == ["car", "truck", "traffic light"]


def test_draw_does_not_change_shape():
    frame = np.zeros((100, 100, 3), np.uint8)
    out = draw_detections(frame, parse_boxes([2], [0.8], [[10, 20, 60, 80]], 0.4))
    assert out.shape == (100, 100, 3) and out.any()
