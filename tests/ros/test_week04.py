"""week04 FSM node against the bridge. Skipped outside the pixi (ROS) environment."""
import csv
from pathlib import Path
import subprocess
import sys
import time

import pytest

rclpy = pytest.importorskip("rclpy")

ROOT = Path(__file__).resolve().parents[2]


def test_fsm_stops_before_the_wall(tmp_path):
    bridge = subprocess.Popen([sys.executable, "-m", "go2_seminar.ros.sim_bridge", "--seconds", "40", "--scene", "wall"],
                              cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        time.sleep(2.0)
        output = tmp_path / "fsm"
        result = subprocess.run([sys.executable, "exercises/week04/fsm.py", "--seconds", "12", "--speed", "0.2",
                                 "--stop-distance", "0.6", "--output", str(output)],
                                cwd=ROOT, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "FORWARD → STOP" in result.stdout
        with output.with_suffix(".csv").open() as stream:
            rows = list(csv.DictReader(stream))
        assert rows[-1]["state"] == "STOP"
        front = float(rows[-1]["front_m"])
        assert 0.4 < front < 0.6, front     # stopped shortly after crossing the threshold, not inside the box
        assert abs(float(rows[-1]["odom_x_m"]) - (1.4 - front)) < 0.1
        assert output.with_suffix(".png").stat().st_size > 1000
    finally:
        bridge.terminate()
        try:
            bridge.wait(timeout=10)
        except subprocess.TimeoutExpired:
            bridge.kill()
