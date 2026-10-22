"""week03 ROS nodes against the bridge. Skipped outside the pixi (ROS) environment."""
import csv
from pathlib import Path
import subprocess
import sys
import time

import pytest

rclpy = pytest.importorskip("rclpy")

ROOT = Path(__file__).resolve().parents[2]


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


def test_scan_front_saves_csv_and_plot(bridge, tmp_path):
    output = tmp_path / "scan"
    result = subprocess.run([sys.executable, "exercises/week03/scan_front.py", "--seconds", "6",
                             "--output", str(output)], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    with output.with_suffix(".csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) >= 10  # 5 Hz scans for about 6 s
    assert abs(float(rows[-1]["front_min_m"]) - 1.4) < 0.02
    assert output.with_suffix(".png").stat().st_size > 1000


def test_scan_noise_republishes(bridge):
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan

    noise = subprocess.Popen([sys.executable, "exercises/week03/scan_noise.py", "--sigma", "0.05", "--seconds", "20"],
                             cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    rclpy.init()
    try:
        node = rclpy.create_node("noise_test")
        received = []
        node.create_subscription(LaserScan, "scan_noisy", received.append, qos_profile_sensor_data)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and len(received) < 3:
            rclpy.spin_once(node, timeout_sec=0.1)
        assert len(received) >= 3, "no /scan_noisy within 30 s"
        front = [m.ranges[0] for m in received]
        assert len(received[-1].ranges) == 360
        assert all(abs(f - 1.4) < 0.3 for f in front) and len(set(front)) > 1
        node.destroy_node()
    finally:
        rclpy.shutdown()
        noise.terminate()
        try:
            noise.wait(timeout=10)
        except subprocess.TimeoutExpired:
            noise.kill()
