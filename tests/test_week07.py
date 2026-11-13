"""week07 helpers. No ROS needed: localize.py and square.py import rclpy only inside main()."""
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exercises/week07/localize.py"
SQUARE = ROOT / "exercises/week07/square.py"

# The answers shown in exercises/week07/README.md.
BLANK1 = ("    # return wall - ???", "    return wall - front")
BLANK2 = ("    # return predicted + gain * (??? - predicted)", "    return predicted + gain * (measured - predicted)")
BLANK3 = ("    # return p / (p + ???)", "    return p / (p + r)")


def filled_source(blanks=(BLANK1, BLANK2, BLANK3)):
    text = SOURCE.read_text(encoding="utf-8")
    for blank, answer in blanks:
        assert text.count(blank) == 1
        text = text.replace(blank, answer)
    return text


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def simulate(localize, gain, kalman=False, odom_sigma=0.1, scan_sigma=0.03, steps=50):
    """Drive 0.02 m per step toward a wall 1.4 m away; odometry reads 10 % long, the LiDAR is noisy."""
    rng = np.random.default_rng(0)
    estimator = localize.Estimator(gain, odom_sigma, scan_sigma, kalman)
    truth = np.arange(1, steps + 1) * 0.02
    estimates = [estimator.update(0.022, 1.4, 1.4 - x + rng.normal(0, 0.03)) for x in truth]
    return np.array(estimates), truth, estimator


def test_baseline_follows_odometry():
    localize = load(SOURCE)
    assert math.isnan(localize.measure(1.4, 1.0))
    assert localize.correct(0.5, 0.4, 0.2) == 0.5
    assert localize.kalman_gain(1.0, 1.0) == 0.0
    estimates, truth, _estimator = simulate(localize, gain=0.2)
    assert np.allclose(estimates, truth * 1.1)


def test_front_distance():
    localize = load(SOURCE)
    ranges = [1.5] + [2.0] * 359
    scan = SimpleNamespace(ranges=ranges, angle_min=0.0, angle_increment=math.radians(1.0), range_min=0.12)
    assert localize.front_distance(scan) == 1.5
    scan.ranges = [math.inf] + [2.0] * 359
    assert math.isnan(localize.front_distance(scan))
    scan.ranges = [0.05] + [2.0] * 359
    assert math.isnan(localize.front_distance(scan))
    # A scan that starts at -180 degrees has the front ray in the middle.
    scan = SimpleNamespace(ranges=[2.0] * 180 + [0.7] + [2.0] * 179, angle_min=-math.pi,
                           angle_increment=math.radians(1.0), range_min=0.12)
    assert localize.front_distance(scan) == 0.7


def test_readme_answers(tmp_path):
    path = tmp_path / "localize_filled.py"
    path.write_text(filled_source(), encoding="utf-8")
    localize = load(path)
    assert math.isclose(localize.measure(1.4, 1.0), 0.4)
    assert math.isclose(localize.correct(0.5, 0.4, 0.2), 0.48)
    assert localize.correct(0.5, 0.4, 0.0) == 0.5 and localize.correct(0.5, 0.4, 1.0) == 0.4
    assert localize.kalman_gain(1.0, 1.0) == 0.5 and localize.kalman_gain(0.0, 1.0) == 0.0
    assert localize.kalman_gain(9.0, 1.0) == 0.9

    def rmse(values, truth):
        return float(np.sqrt(np.mean((values - truth) ** 2)))

    odometry = rmse(*simulate(localize, gain=0.0)[:2])
    lidar = rmse(*simulate(localize, gain=1.0)[:2])
    fused = rmse(*simulate(localize, gain=0.2)[:2])
    assert fused < lidar < odometry

    estimates, truth, estimator = simulate(localize, gain=0.2, kalman=True)
    assert rmse(estimates, truth) < lidar
    assert 0.2 < estimator.last_gain < 0.6
    # Declaring the LiDAR ten times noisier lowers the gain.
    assert simulate(localize, gain=0.2, kalman=True, scan_sigma=0.3)[2].last_gain < 0.1


def test_only_blank1_filled_still_follows_odometry(tmp_path):
    path = tmp_path / "localize_blank1.py"
    path.write_text(filled_source((BLANK1,)), encoding="utf-8")
    localize = load(path)
    estimates, truth, _estimator = simulate(localize, gain=0.2)
    assert np.allclose(estimates, truth * 1.1)


def test_square_geometry():
    square = load(SQUARE)
    assert square.corners(0.8) == [(0.8, 0.0), (0.8, -0.8), (0.0, -0.8), (0.0, 0.0)]
    assert square.corners(0.5, left=True)[1] == (0.5, 0.5)
    start = (1.0, 2.0, math.pi / 2)
    assert np.allclose(square.to_odom((0.8, 0.0), start), (1.0, 2.8))
    assert np.allclose(square.to_odom((0.8, -0.8), start), (1.8, 2.8))
    assert np.allclose(square.relative((1.8, 2.8, math.pi), start), (0.8, -0.8, math.pi / 2))
    v, w = square.steer((0.0, 0.0, 0.0), (1.0, 0.0), 0.15)
    assert v == 0.15 and abs(w) < 1e-9
    v, w = square.steer((0.0, 0.0, 0.0), (0.0, -1.0), 0.15)
    assert v == 0.0 and w == -1.0
