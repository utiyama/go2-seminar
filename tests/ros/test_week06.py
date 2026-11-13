"""week06 planner node against the bridge. Skipped outside the pixi (ROS) environment."""
from pathlib import Path
import subprocess
import sys
import time

import pytest

rclpy = pytest.importorskip("rclpy")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from test_week06 import filled_source  # noqa: E402


@pytest.fixture
def bridge():
    process = subprocess.Popen([sys.executable, "-m", "go2_seminar.ros.sim_bridge", "--seconds", "60"],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(2.0)
    yield process
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def run_planner(script, output, *extra):
    return subprocess.run([sys.executable, str(script), "--output", str(output), *extra],
                          cwd=ROOT, capture_output=True, text=True, timeout=90)


def test_baseline_plans_with_dijkstra(bridge, tmp_path):
    output = tmp_path / "plan"
    result = run_planner("exercises/week06/planner.py", output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "うち余裕の分 0 個" in result.stdout
    assert "経路の長さ 3.00 m  調べたセル 3965 個" in result.stdout
    assert output.with_suffix(".png").stat().st_size > 1000


def test_filled_node_plans_and_follows(bridge, tmp_path):
    script = tmp_path / "planner_filled.py"
    script.write_text(filled_source(), encoding="utf-8")
    result = run_planner(script, tmp_path / "plan")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "経路の長さ 3.20 m  調べたセル 825 個" in result.stdout

    result = run_planner(script, tmp_path / "blocked", "--margin", "0.4")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "経路が見つかりません" in result.stdout

    output = tmp_path / "follow"
    result = run_planner(script, output, "--follow", "--goal", "0.9", "-0.9", "--seconds", "60")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "到着しました" in result.stdout
    assert "実際の位置では 0.0" in result.stdout  # the bridge odometry is exact: within 0.1 m of the goal
    assert output.with_suffix(".png").stat().st_size > 1000
