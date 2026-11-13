"""week05 mapping node against the bridge. Skipped outside the pixi (ROS) environment."""
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pytest

rclpy = pytest.importorskip("rclpy")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from test_week05 import filled_source  # noqa: E402


@pytest.fixture
def bridge():
    process = subprocess.Popen([sys.executable, "-m", "go2_seminar.ros.sim_bridge", "--seconds", "40"],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(2.0)
    yield process
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def run_mapping(script, output, *extra):
    return subprocess.run([sys.executable, str(script), "--seconds", "6", "--output", str(output), *extra],
                          cwd=ROOT, capture_output=True, text=True, timeout=60)


def test_baseline_runs_and_saves_an_empty_map(bridge, tmp_path):
    output = tmp_path / "map"
    result = run_mapping("exercises/week05/mapping.py", output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "占有セル 0 個" in result.stdout
    assert output.with_suffix(".png").stat().st_size > 1000
    assert np.all(np.load(output.with_suffix(".npz"))["occupancy"] == -1)


@pytest.mark.parametrize("extra", [(), ("--truth",)])
def test_filled_node_maps_the_wall_ahead(bridge, tmp_path, extra):
    script = tmp_path / "mapping_filled.py"
    script.write_text(filled_source(), encoding="utf-8")
    output = tmp_path / "map"
    result = run_mapping(script, output, *extra)
    assert result.returncode == 0, result.stdout + result.stderr
    occupancy = np.load(output.with_suffix(".npz"))["occupancy"]
    # Robot at the origin: the box face is at x = 1.4 m, y = 0 -> row 60, col 87 or 88.
    assert occupancy[60, 87:89].max() == 100
    assert occupancy[60, 70] == 0          # x = 0.5 m: the ray passed through
    assert occupancy[60, 100] == -1        # x = 2.0 m: hidden behind the box
    assert (occupancy == 100).sum() > 100
