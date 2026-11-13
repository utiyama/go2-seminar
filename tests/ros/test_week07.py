"""week07 nodes against a bridge with odometry and LiDAR errors. Skipped outside the pixi (ROS) environment."""
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import numpy as np
import pytest

rclpy = pytest.importorskip("rclpy")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from test_week07 import BLANK1, BLANK2, filled_source  # noqa: E402


@pytest.fixture
def bridge():
    process = subprocess.Popen([sys.executable, "-m", "go2_seminar.ros.sim_bridge", "--seconds", "90",
                                "--odom-linear-scale", "1.1", "--odom-angular-scale", "1.05", "--scan-noise", "0.03"],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(2.0)
    yield process
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def run(script, output, *extra):
    result = subprocess.run([sys.executable, str(script), "--output", str(output), *extra],
                            cwd=ROOT, capture_output=True, text=True, timeout=120)
    return result


def rmse(values, truth):
    return float(np.sqrt(np.mean((values - truth) ** 2)))


def test_localize_baseline_and_filled(bridge, tmp_path):
    # Baseline: the estimate is the odometry, which reads 10 % long.
    output = tmp_path / "base"
    result = run("exercises/week07/localize.py", output, "--stop-distance", "0.8")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "LiDAR --" in result.stdout
    data = np.genfromtxt(output.with_suffix(".csv"), delimiter=",", names=True)
    assert np.allclose(data["estimate_m"], data["odometry_m"], atol=1e-3)
    assert np.all(np.isnan(data["lidar_m"]))
    assert 0.03 < data["odometry_m"][-1] - data["truth_m"][-1] < 0.09
    assert output.with_suffix(".png").stat().st_size > 1000

    # Blanks 1 and 2 filled: closer to the truth than the odometry alone.
    script = tmp_path / "localize_filled.py"
    script.write_text(filled_source((BLANK1, BLANK2)), encoding="utf-8")
    output = tmp_path / "filled"
    result = run(script, output, "--reset", "--stop-distance", "0.8")
    assert result.returncode == 0, result.stdout + result.stderr
    data = np.genfromtxt(output.with_suffix(".csv"), delimiter=",", names=True)
    assert rmse(data["estimate_m"], data["truth_m"]) < rmse(data["odometry_m"], data["truth_m"])
    assert rmse(data["lidar_m"], data["truth_m"]) < 0.06

    # All blanks filled: the gain is computed, and grows from the start.
    script.write_text(filled_source(), encoding="utf-8")
    result = run(script, tmp_path / "kalman", "--reset", "--kalman", "--stop-distance", "0.8")
    assert result.returncode == 0, result.stdout + result.stderr
    match = re.search(r"走行中のゲイン  最初 ([\d.]+)  最後 ([\d.]+)", result.stdout)
    assert match and 0.2 < float(match.group(2)) < 0.6


def test_square_returns_by_odometry_but_not_in_truth(bridge, tmp_path):
    output = tmp_path / "square"
    result = run("exercises/week07/square.py", output, "--side", "0.5")
    assert result.returncode == 0, result.stdout + result.stderr
    odometry = re.search(r"オドメトリでは  出発点まで ([\d.]+) m、向きの差 (\d+) 度", result.stdout)
    truth = re.search(r"実際の位置では  出発点まで ([\d.]+) m、向きの差 (\d+) 度", result.stdout)
    assert odometry and truth, result.stdout
    assert float(odometry.group(1)) < 0.05 and int(odometry.group(2)) <= 2
    assert float(truth.group(1)) > float(odometry.group(1)) and int(truth.group(2)) > 10
    assert output.with_suffix(".png").stat().st_size > 1000


@pytest.mark.skipif(sys.platform == "win32", reason="Ctrl+C cannot be sent to a single child process on Windows")
def test_ctrl_c_pressed_repeatedly_still_saves(bridge, tmp_path):
    # A second Ctrl+C used to interrupt the figure being saved, and the stop command failed after the first.
    output = tmp_path / "interrupted"
    process = subprocess.Popen([sys.executable, "exercises/week07/localize.py", "--output", str(output), "--reset"],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                               env=dict(os.environ, PYTHONUNBUFFERED="1"),
                               preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL))
    lines = []
    while "開始" not in "".join(lines):
        line = process.stdout.readline()
        assert line, "".join(lines)
        lines.append(line)
    time.sleep(1.5)  # driving
    for _ in range(4):
        process.send_signal(signal.SIGINT)
        time.sleep(0.1)
    rest, _ = process.communicate(timeout=30)
    stdout = "".join(lines) + rest
    assert process.returncode == 0 and "Traceback" not in stdout, stdout
    assert "保存先" in stdout and output.with_suffix(".png").stat().st_size > 1000
    assert output.with_suffix(".csv").exists()
