"""week06 planner helpers. No ROS needed: planner.py imports rclpy only inside main()."""
import importlib.util
import math
from pathlib import Path

import numpy as np

from go2_seminar.ros.maps import load_map, room_map

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exercises/week06/planner.py"

# The answers shown in exercises/week06/README.md.
BLANK1 = ("                # priority = new_cost + weight * ???",
          "                priority = new_cost + weight * heuristic(nxt, goal)")
BLANK2 = ("    # cells = round(??? / resolution)",
          "    cells = round(margin / resolution)")
BLANK3 = ("    # error = wrap_angle(direction - ???)\n"
          "    # v = speed if abs(error) < 0.5 else 0.0  # 向きが大きくずれている間は、その場で回る\n"
          "    # return v, max(-1.0, min(1.0, 1.5 * error))",
          "    error = wrap_angle(direction - yaw)\n"
          "    v = speed if abs(error) < 0.5 else 0.0  # 向きが大きくずれている間は、その場で回る\n"
          "    return v, max(-1.0, min(1.0, 1.5 * error))")


def filled_source():
    text = SOURCE.read_text(encoding="utf-8")
    for blank, answer in (BLANK1, BLANK2, BLANK3):
        assert text.count(blank) == 1
        text = text.replace(blank, answer)
    return text


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plan(planner, margin, goal=(2.5, 0.0), weight=1.0):
    grid = room_map()
    occupied = grid["occupancy"] != 0
    blocked = planner.inflate(occupied, margin, grid["resolution"])
    cells, done = planner.search(blocked, planner.to_cell((0.0, 0.0), grid), planner.to_cell(goal, grid), weight)
    return grid, occupied, blocked, cells, done


def test_room_map_matches_the_bridge_room(tmp_path):
    grid = room_map()
    occupancy = grid["occupancy"]
    assert occupancy.shape == (120, 160) and grid["resolution"] == 0.05

    def value(x, y):
        return occupancy[math.floor((y + 3.0) / 0.05), math.floor((x + 3.0) / 0.05)]

    assert value(0.0, 0.0) == 0 and value(2.5, 0.0) == 0
    assert value(1.5, 0.0) == 100 and value(1.5, 0.55) == 100   # the box ahead
    assert value(0.6, 0.9) == 100 and value(2.3, -0.8) == 100   # the two small boxes
    assert value(3.02, 0.0) == 100 and value(0.0, -1.52) == 100  # outer walls
    assert value(-2.0, 0.0) == -1 and value(0.0, 2.5) == -1      # outside the room
    np.savez(tmp_path / "map.npz", **grid)
    loaded = load_map(tmp_path / "map.npz")
    assert np.array_equal(loaded["occupancy"], occupancy) and loaded["x_min"] == -3.0


def test_baseline_is_dijkstra_without_margin_and_does_not_move():
    planner = load(SOURCE)
    grid, occupied, blocked, cells, done = plan(planner, margin=0.25)
    assert np.array_equal(blocked, occupied)  # blank 2 not filled: no margin
    assert cells[0] == planner.to_cell((0.0, 0.0), grid) and cells[-1] == planner.to_cell((2.5, 0.0), grid)
    assert not any(blocked[row, col] for col, row in cells)
    assert len(done) > 3000  # searches in every direction
    assert planner.steer((0.0, 0.0, 0.0), (1.0, 1.0), 0.15) == (0.0, 0.0)


def test_cells_and_targets():
    planner = load(SOURCE)
    grid = room_map()
    assert planner.to_cell((0.0, 0.0), grid) == (60, 60)
    assert np.allclose(planner.to_xy((60, 60), grid), (0.025, 0.025))
    assert planner.heuristic((0, 0), (3, 4)) == 5.0
    path = [(0.0, 0.0), (0.1, 0.0), (0.2, 0.0), (0.5, 0.0), (0.6, 0.0)]
    assert planner.next_target(path, (0.0, 0.0), 0) == ((0.5, 0.0), 3)
    assert planner.next_target(path, (0.55, 0.0), 3) == ((0.6, 0.0), 4)  # the last point is kept
    assert math.isclose(planner.path_length(path), 0.6)


def test_readme_answers(tmp_path):
    path = tmp_path / "planner_filled.py"
    path.write_text(filled_source(), encoding="utf-8")
    planner = load(path)
    baseline = load(SOURCE)

    # Blank 1: A* finds a path of the same cost while expanding far fewer cells.
    def cost(cells):
        return sum(math.dist(a, b) for a, b in zip(cells[:-1], cells[1:]))

    _grid, _occupied, _blocked, dijkstra_cells, dijkstra_done = plan(baseline, margin=0.0)
    _grid, _occupied, _blocked, cells, done = plan(planner, margin=0.0)
    assert math.isclose(cost(cells), cost(dijkstra_cells))
    assert len(done) < len(dijkstra_done) / 3
    _grid, _occupied, _blocked, greedy_cells, greedy_done = plan(planner, margin=0.0, weight=5.0)
    assert len(greedy_done) < len(done) and cost(greedy_cells) >= cost(cells)
    _grid, _occupied, _blocked, _cells, zero_done = plan(planner, margin=0.0, weight=0.0)
    assert len(zero_done) == len(dijkstra_done)

    # Blank 2: the path keeps the margin from every occupied cell.
    grid, occupied, blocked, cells, _done = plan(planner, margin=0.25)
    assert blocked.sum() > occupied.sum()
    rows, cols = np.nonzero(grid["occupancy"] == 100)
    for col, row in cells:
        assert np.hypot(cols - col, rows - row).min() > 5.0  # 0.25 m = 5 cells
    assert plan(planner, margin=0.4)[3] == []                # the gaps beside the box are closed

    # Blank 3: turn toward the target, and move forward once roughly facing it.
    v, w = planner.steer((0.0, 0.0, 0.0), (1.0, 0.0), 0.15)
    assert v == 0.15 and abs(w) < 1e-9
    v, w = planner.steer((0.0, 0.0, 0.0), (0.0, 1.0), 0.15)
    assert v == 0.0 and w == 1.0                             # target on the left: turn left in place
    v, w = planner.steer((0.0, 0.0, math.pi), (1.0, -0.2), 0.15)
    assert v == 0.0 and w > 0                                # facing -x, target behind on the robot's left
    v, w = planner.steer((1.0, 1.0, math.pi / 2), (0.9, 2.0), 0.15)
    assert v == 0.15 and 0 < w < 0.2
