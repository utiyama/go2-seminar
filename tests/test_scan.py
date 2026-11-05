"""sector_min works without ROS (plain objects standing in for LaserScan)."""
import math
from types import SimpleNamespace

import numpy as np

from go2_seminar.ros.scan import sector_min


def make_scan(ranges):
    return SimpleNamespace(ranges=list(ranges), angle_min=0.0, angle_increment=math.radians(1.0), range_min=0.12)


def test_front_sector_wraps_around_zero():
    ranges = np.full(360, 3.0)
    ranges[355] = 1.0          # -5 degrees, inside the front sector
    ranges[20] = 0.5           # outside ±15 degrees
    assert sector_min(make_scan(ranges), 0.0, 15.0) == 1.0


def test_left_right_and_invalid_values():
    ranges = np.full(360, 2.0)
    ranges[90] = 0.8
    ranges[270] = math.inf     # no return
    ranges[271] = 0.05         # below range_min, ignored
    scan = make_scan(ranges)
    assert sector_min(scan, 90.0, 15.0) == 0.8
    assert sector_min(scan, 270.0, 15.0) == 2.0
    assert sector_min(make_scan(np.full(360, math.inf)), 0.0, 15.0) == math.inf
