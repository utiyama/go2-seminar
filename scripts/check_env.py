"""A headless acceptance check; GUI success must be checked separately."""
import argparse
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import sys
import traceback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/environment.json")
    args = parser.parse_args()
    report = {"python": platform.python_version(), "system": platform.system(),
              "machine": platform.machine(), "gui": "not tested", "checks": {}}
    try:
        if sys.version_info[:2] != (3, 11):
            raise RuntimeError("Python 3.11 is required")
        pins = {"mujoco": "3.3.7", "mujoco-menagerie": "2026.9.0", "numpy": "2.2.6", "matplotlib": "3.10.6"}
        report["packages"] = {name: metadata.version(name) for name in pins}
        if report["packages"] != pins:
            raise RuntimeError("Package versions differ from classroom pins; rerun install script")
        import numpy as np
        from go2_seminar import Go2Sim
        physics = Go2Sim()
        report["model_oid"] = physics.robot_info.oid
        report["model_license"] = physics.robot_info.license
        report["dimensions"] = {"nq": physics.model.nq, "nv": physics.model.nv, "nu": physics.model.nu}
        if (physics.model.nq, physics.model.nv, physics.model.nu) != (19, 18, 12):
            raise RuntimeError("Unexpected model dimensions")
        physics.step(5.0)
        pose = physics.get_pose()
        if not (0.15 < pose.position[2] < 0.5 and np.max(np.abs(pose.rpy[:2])) < 0.3):
            raise RuntimeError("Standing acceptance check failed")
        report["checks"]["standing_5s"] = physics.get_state()
        target = physics.get_joint_positions()
        target[1] += 0.05
        before = physics.get_joint_positions()[1]
        physics.set_joint_targets(target)
        physics.step(0.5)
        change = float(physics.get_joint_positions()[1] - before)
        if abs(change) < 0.005:
            raise RuntimeError("Joint command produced no measurable response")
        report["checks"]["joint_response_rad"] = change
        imu = physics.get_imu()
        if not all(np.all(np.isfinite(v)) for v in imu.values()):
            raise RuntimeError("Non-finite IMU")
        kinematic = Go2Sim("kinematic", obstacles=True)
        distance = kinematic.get_range()
        if not np.isclose(distance, 1.4):
            raise RuntimeError("Range geometry mismatch")
        kinematic.set_velocity(0.2)
        kinematic.step(1.0)
        if not np.allclose(kinematic.get_pose().position[:2], [0.2, 0]):
            raise RuntimeError("Ideal motion check failed")
        kinematic.stop()
        kinematic.step(1.0)
        if not np.allclose(kinematic.get_pose().position[:2], [0.2, 0]):
            raise RuntimeError("Stop check failed")
        report["checks"]["kinematic_move_stop_and_range"] = "PASS"
        report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = str(error)
        traceback.print_exc()
        print("セットアップと通信を確認してください。対処方法: docs/troubleshooting.md", file=sys.stderr)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
