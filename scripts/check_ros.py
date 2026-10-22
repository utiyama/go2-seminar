"""ROS 2環境（pixi）の確認。pixi環境内で実行します: pixi run check"""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time
import traceback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/ros-environment.json")
    args = parser.parse_args()
    report = {"python": platform.python_version(), "system": platform.system(),
              "machine": platform.machine(), "gui": "not tested", "checks": {}}
    try:
        if sys.version_info[:2] != (3, 11):
            raise RuntimeError("Python 3.11 is required")
        report["ros_distro"] = os.environ.get("ROS_DISTRO")
        report["rmw_env"] = os.environ.get("RMW_IMPLEMENTATION")
        report["ros_domain_id"] = os.environ.get("ROS_DOMAIN_ID")
        report["discovery_range"] = os.environ.get("ROS_AUTOMATIC_DISCOVERY_RANGE")
        if not (report["ros_domain_id"] or "").isdigit():
            raise RuntimeError("ROS_DOMAIN_ID is not set; the activation script did not run")
        report["cyclonedds_uri"] = os.environ.get("CYCLONEDDS_URI")
        uri = (report["cyclonedds_uri"] or "").split(",")[0]  # Windows appends an inline fragment
        if not uri.startswith("file://") or not Path(uri[len("file://"):]).is_file():
            raise RuntimeError("CYCLONEDDS_URI does not point to scripts/cyclonedds*.xml")
        report["robot_mode"] = uri.endswith("-robot.xml")
        if report["ros_distro"] != "jazzy":
            raise RuntimeError("ROS_DISTRO is not 'jazzy'; run inside the pixi environment")
        if report["rmw_env"] != "rmw_cyclonedds_cpp":
            raise RuntimeError("RMW_IMPLEMENTATION must be rmw_cyclonedds_cpp (set by pixi.toml)")
        report["ros2_cli"] = shutil.which("ros2")
        if not report["ros2_cli"]:
            raise RuntimeError("ros2 command not found")
        import mujoco
        import numpy as np
        report["packages"] = {"mujoco": mujoco.__version__, "numpy": np.__version__}
        if mujoco.__version__ != "3.3.7":
            raise RuntimeError("mujoco version differs from classroom pin 3.3.7")
        import rclpy
        from rclpy.utilities import get_rmw_implementation_identifier
        from std_msgs.msg import String
        from sensor_msgs.msg import LaserScan  # noqa: F401  (needed from week03)
        from geometry_msgs.msg import TwistStamped  # noqa: F401
        from nav_msgs.msg import Odometry  # noqa: F401
        report["rmw"] = get_rmw_implementation_identifier()
        if report["rmw"] != "rmw_cyclonedds_cpp":
            raise RuntimeError(f"Unexpected RMW: {report['rmw']}")
        rclpy.init()
        try:
            node = rclpy.create_node("go2_seminar_check")
            received = []
            node.create_subscription(String, "/go2_seminar_check", lambda m: received.append(m.data), 10)
            publisher = node.create_publisher(String, "/go2_seminar_check", 10)
            start = time.monotonic()
            while time.monotonic() - start < 10 and not received:
                publisher.publish(String(data="hello"))
                rclpy.spin_once(node, timeout_sec=0.1)
            if not received:
                raise RuntimeError("Publish/subscribe round trip failed within 10 s")
            report["checks"]["pubsub_roundtrip_s"] = round(time.monotonic() - start, 3)
            node.destroy_node()
        finally:
            rclpy.shutdown()
        from go2_seminar import Go2Sim
        kinematic = Go2Sim("kinematic", obstacles=True)
        if not np.isclose(kinematic.get_range(), 1.4):
            raise RuntimeError("Range geometry mismatch")
        kinematic.set_velocity(0.2)
        kinematic.step(1.0)
        if not np.allclose(kinematic.get_pose().position[:2], [0.2, 0]):
            raise RuntimeError("Ideal motion check failed")
        report["checks"]["kinematic_move_and_range"] = "PASS"
        report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = str(error)
        traceback.print_exc()
        print("ROS環境の確認に失敗しました。対処方法: docs/troubleshooting.md", file=sys.stderr)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
