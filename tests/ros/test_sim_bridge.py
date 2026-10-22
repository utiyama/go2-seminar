"""Checks for the ROS 2 bridge. Skipped automatically outside the pixi (ROS) environment."""
import math
import subprocess
import sys
import time

import numpy as np
import pytest

rclpy = pytest.importorskip("rclpy")

from go2_seminar.ros.sim_bridge import OdometryModel  # noqa: E402


def test_odometry_model_exact_without_errors():
    model = OdometryModel()
    for _ in range(100):
        model.integrate(0.2, 0.0, 0.02)
    assert math.isclose(model.x, 0.4, abs_tol=1e-9) and abs(model.y) < 1e-12
    for _ in range(100):
        model.integrate(0.0, math.pi / 4, 0.02)
    assert math.isclose(model.yaw, math.pi / 2, abs_tol=1e-9)


def test_odometry_model_bias_only_while_moving():
    model = OdometryModel(angular_bias=0.1)
    model.integrate(0.0, 0.0, 1.0)
    assert model.yaw == 0.0
    model.integrate(0.1, 0.0, 1.0)
    assert math.isclose(model.yaw, 0.1, abs_tol=1e-9)


def test_bridge_publishes_scan_and_moves_on_cmd_vel():
    from geometry_msgs.msg import TwistStamped
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import LaserScan
    from rclpy.qos import qos_profile_sensor_data

    bridge = subprocess.Popen([sys.executable, "-m", "go2_seminar.ros.sim_bridge", "--seconds", "20",
                               "--scene", "wall"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    rclpy.init()
    try:
        node = rclpy.create_node("bridge_test")
        scans, odoms = [], []
        node.create_subscription(LaserScan, "scan", scans.append, qos_profile_sensor_data)
        node.create_subscription(Odometry, "odom", odoms.append, 10)
        pub = node.create_publisher(TwistStamped, "cmd_vel", 10)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and not (scans and odoms):
            rclpy.spin_once(node, timeout_sec=0.1)
        assert scans and odoms, bridge.stdout.read() if bridge.poll() is not None else "no messages within 30 s"
        scan = scans[-1]
        assert len(scan.ranges) == 360 and scan.header.frame_id == "base_scan"
        assert math.isclose(scan.ranges[0], 1.4, abs_tol=0.02)      # box ahead at x=1.5 (half size 0.1)
        assert all(r >= scan.range_min for r in scan.ranges if math.isfinite(r))
        start_x = odoms[-1].pose.pose.position.x
        t0 = time.monotonic()
        while time.monotonic() - t0 < 2.0:
            msg = TwistStamped()
            msg.header.stamp = node.get_clock().now().to_msg()
            msg.header.frame_id = "base_link"
            msg.twist.linear.x = 0.2
            pub.publish(msg)
            rclpy.spin_once(node, timeout_sec=0.05)
        moved = odoms[-1].pose.pose.position.x - start_x
        assert 0.2 < moved < 0.5, moved
        # Command timeout: without new commands the robot must stop.
        t0 = time.monotonic()
        while time.monotonic() - t0 < 1.5:
            rclpy.spin_once(node, timeout_sec=0.05)
        x_after_stop = odoms[-1].pose.pose.position.x
        while time.monotonic() - t0 < 2.5:
            rclpy.spin_once(node, timeout_sec=0.05)
        assert abs(odoms[-1].pose.pose.position.x - x_after_stop) < 1e-6
        node.destroy_node()
    finally:
        rclpy.shutdown()
        bridge.terminate()
        try:
            bridge.wait(timeout=10)
        except subprocess.TimeoutExpired:
            bridge.kill()
