"""week05 mapping helpers. No ROS needed: mapping.py imports rclpy only inside main()."""
import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exercises/week05/mapping.py"

# The answers shown in exercises/week05/README.md.
BLANK1 = ("    # col = np.floor((x - X_MIN) / ???).astype(int)\n"
          "    # row = np.floor((y - Y_MIN) / ???).astype(int)\n"
          "    # return col, row",
          "    col = np.floor((x - X_MIN) / resolution).astype(int)\n"
          "    row = np.floor((y - Y_MIN) / resolution).astype(int)\n"
          "    return col, row")
BLANK2 = ("    # return body_to_world(local, [???, ???], ???)",
          "    return body_to_world(local, [x, y], yaw)")


def filled_source():
    text = SOURCE.read_text(encoding="utf-8")
    for blank, answer in (BLANK1, BLANK2):
        assert text.count(blank) == 1
        text = text.replace(blank, answer)
    return text


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_baseline_leaves_the_grid_empty():
    mapping = load(SOURCE)
    points = np.array([[1.0, 0.0], [0.0, 2.0]])
    col, row = mapping.to_cells(points, 0.05)
    assert col.size == 0 and row.size == 0
    assert np.array_equal(mapping.to_odom(points, (1.0, 2.0, np.pi / 2)), points)


def test_scan_helpers():
    mapping = load(SOURCE)
    r, a = np.array([1.0, 2.0]), np.array([0.0, np.pi / 2])
    assert np.allclose(mapping.polar_to_xy(r, a), [[1, 0], [0, 2]])
    free = mapping.ray_points(r, a, 0.1)
    assert np.all(np.hypot(free[:, 0], free[:, 1]) < 2.0 - 0.1 + 1e-9)   # stops before the hit
    assert len(free) == 9 + 19


def test_readme_answers(tmp_path):
    path = tmp_path / "mapping_filled.py"
    path.write_text(filled_source(), encoding="utf-8")
    mapping = load(path)
    col, row = mapping.to_cells(np.array([[1.42, 0.01], [-3.0, -3.0], [0.0, 0.0]]), 0.05)
    assert col.tolist() == [88, 0, 60] and row.tolist() == [60, 0, 60]
    # Robot at (1, 2) facing +y: a point 1 m ahead is at (1, 3), 1 m to the left at (0, 2).
    moved = mapping.to_odom(np.array([[1.0, 0.0], [0.0, 1.0]]), (1.0, 2.0, np.pi / 2))
    assert np.allclose(moved, [[1, 3], [0, 2]])
    grid = mapping.Grid(0.05)
    grid.add(grid.passes, np.array([10, 11, 999]), np.array([5, 5, 5]))
    grid.add(grid.hits, np.array([11, 11]), np.array([5, 5]))
    occupancy = grid.occupancy(min_hits=2)
    assert occupancy[5, 10] == 0 and occupancy[5, 11] == 100 and occupancy[0, 0] == -1
