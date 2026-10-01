"""Small teaching wrapper; no Unitree SDK, ROS, or locomotion policy.

SI units throughout. World: x/y horizontal, z up. Body: x forward, y left.
Quaternions are w,x,y,z; yaw is positive counter-clockwise about world z.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import math
import os

import mujoco
import mujoco_menagerie as menagerie
import numpy as np


def finite_vector(value, size: int, name: str) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != (size,) or not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain {size} finite numbers")
    return result


@dataclass(frozen=True)
class Pose:
    position: np.ndarray
    quaternion_wxyz: np.ndarray
    rpy: np.ndarray


class Go2Sim:
    """mode='physics': PD joint control + contact dynamics.

    mode='kinematic': ideal SE(2) base motion, fixed legs, NO dynamics or
    collision response. Designed for frames/planning, not quadruped walking.
    Public model/data allow advanced exercises; callers own their validity.
    """

    def __init__(self, mode: Literal["physics", "kinematic"] = "physics",
                 *, obstacles: bool = False, cache_dir: str | Path | None = None):
        if mode not in ("physics", "kinematic"):
            raise ValueError("mode must be 'physics' or 'kinematic'")
        self.mode = mode
        # Local cache makes a pre-warmed repository folder easy to carry to class.
        cache_path = cache_dir or os.environ.get("MENAGERIE_CACHE_DIR", ".cache/menagerie")
        cache = menagerie.Cache(dir=Path(cache_path).resolve())
        self.robot_info = menagerie.get("unitree_go2")
        spec = self.robot_info.spec("scene", cache=cache)
        spec.add_sensor(name="seminar_gyro", type=mujoco.mjtSensor.mjSENS_GYRO,
                        objtype=mujoco.mjtObj.mjOBJ_SITE, objname="imu")
        spec.add_sensor(name="seminar_accel", type=mujoco.mjtSensor.mjSENS_ACCELEROMETER,
                        objtype=mujoco.mjtObj.mjOBJ_SITE, objname="imu")
        if obstacles:
            spec.worldbody.add_geom(name="classroom_wall", type=mujoco.mjtGeom.mjGEOM_BOX,
                                    pos=[1.5, 0, 0.25], size=[0.1, 0.6, 0.25],
                                    rgba=[0.8, 0.25, 0.1, 1], group=0)
        self.model = spec.compile()
        self.data = mujoco.MjData(self.model)
        self.base_id = self.model.body("base").id
        root_joint = self.model.body_jntadr[self.base_id]
        if self.model.jnt_type[root_joint] != mujoco.mjtJoint.mjJNT_FREE:
            raise RuntimeError("Expected a free base joint")
        self._root_q = int(self.model.jnt_qposadr[root_joint])
        self._root_v = int(self.model.jnt_dofadr[root_joint])
        self._jids = self.model.actuator_trnid[:, 0].copy()
        if self.model.nu != 12 or not np.allclose(self.model.actuator_gear[:, 0], 1):
            raise RuntimeError("Expected 12 direct-drive joint motors")
        self._qa = self.model.jnt_qposadr[self._jids]
        self._va = self.model.jnt_dofadr[self._jids]
        self.joint_names = tuple(self.model.joint(int(j)).name for j in self._jids)
        self.kp, self.kd = 45.0, 3.0
        self._command = np.zeros(3)
        self.reset()

    @property
    def time(self) -> float:
        return float(self.data.time)

    def reset(self) -> None:
        mujoco.mj_resetDataKeyframe(self.model, self.data, self.model.key("home").id)
        self.data.ctrl[:] = 0  # The model's home ctrl values are not motor torques.
        self._home = self.data.qpos[self._qa].copy()
        self._target = self._home.copy()
        self._command[:] = 0
        mujoco.mj_forward(self.model, self.data)

    def get_pose(self) -> Pose:
        p = self.data.qpos[self._root_q:self._root_q + 3].copy()
        q = self.data.qpos[self._root_q + 3:self._root_q + 7].copy()
        w, x, y, z = q
        rpy = np.array([
            math.atan2(2 * (w*x + y*z), 1 - 2 * (x*x + y*y)),
            math.asin(float(np.clip(2 * (w*y - z*x), -1, 1))),
            math.atan2(2 * (w*z + x*y), 1 - 2 * (y*y + z*z)),
        ])
        return Pose(p, q, rpy)

    def get_orientation(self) -> np.ndarray:
        """Roll, pitch, yaw [rad], ZYX Euler convention."""
        return self.get_pose().rpy

    def get_joint_positions(self) -> np.ndarray:
        """12 angles [rad], in joint_names (actuator) order; independent copy."""
        return self.data.qpos[self._qa].copy()

    def get_state(self) -> dict:
        p = self.get_pose()
        return {
            "mode": self.mode, "time_s": self.time,
            "position_m": p.position.tolist(), "quaternion_wxyz": p.quaternion_wxyz.tolist(),
            "rpy_rad": p.rpy.tolist(),
            "linear_velocity_world_m_s": self.data.qvel[self._root_v:self._root_v+3].tolist(),
            "angular_velocity_body_rad_s": self.data.qvel[self._root_v+3:self._root_v+6].tolist(),
            "joint_positions_rad": dict(zip(self.joint_names, self.get_joint_positions().tolist())),
        }

    def set_joint_targets(self, targets) -> None:
        """Position targets [rad], converted to bounded motor torque by PD."""
        if self.mode != "physics":
            raise RuntimeError("Joint targets require mode='physics'")
        target = finite_vector(targets, 12, "targets")
        limits = self.model.jnt_range[self._jids]
        if np.any(target < limits[:, 0]) or np.any(target > limits[:, 1]):
            raise ValueError("Joint target outside model limits")
        self._target = target.copy()

    def stand(self) -> None:
        """Hold home joint angles. Not fall recovery or a walking controller."""
        self.set_joint_targets(self._home)

    def set_velocity(self, vx=0.0, vy=0.0, yaw_rate=0.0) -> None:
        """Ideal body-frame velocity [m/s, m/s, rad/s], kinematic mode ONLY."""
        if self.mode != "kinematic":
            raise NotImplementedError("No walking policy. Use mode='kinematic' for ideal planar motion.")
        command = finite_vector([vx, vy, yaw_rate], 3, "velocity")
        if np.linalg.norm(command[:2]) > 0.5 or abs(command[2]) > 1.5:
            raise ValueError("Teaching limits: planar speed <= 0.5 m/s, yaw rate <= 1.5 rad/s")
        self._command = command
        self._update_kinematic_velocity()
        mujoco.mj_forward(self.model, self.data)

    def set_planar_pose(self, x: float, y: float, yaw: float) -> None:
        """Reposition for a coordinate exercise; kinematic mode only."""
        if self.mode != "kinematic":
            raise RuntimeError("Repositioning requires mode='kinematic'")
        x, y, yaw = finite_vector([x, y, yaw], 3, "pose")
        q = self._root_q
        self.data.qpos[q:q+2] = [x, y]
        self.data.qpos[q+3:q+7] = [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]
        self.stop()

    def stop(self) -> None:
        """Kinematic: zero velocity now. Physics: hold current joint positions.

        A physics base retains inertia; this is not an instantaneous brake.
        """
        self._command[:] = 0
        if self.mode == "kinematic":
            self.data.qvel[:] = 0
        else:
            self._target = self.get_joint_positions()
        mujoco.mj_forward(self.model, self.data)

    def step(self, duration: float = 0.02) -> None:
        """Advance simulation time; duration must be an integer physics timestep."""
        dt = self.model.opt.timestep
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("duration must be finite and > 0")
        n = round(duration / dt)
        if n < 1 or not math.isclose(n * dt, duration, rel_tol=0, abs_tol=1e-9):
            raise ValueError(f"duration must be a positive multiple of {dt} s")
        if self.mode == "physics":
            for _ in range(n):
                torque = self.kp * (self._target - self.data.qpos[self._qa]) - self.kd * self.data.qvel[self._va]
                self.data.ctrl[:] = np.clip(torque, self.model.actuator_ctrlrange[:, 0],
                                           self.model.actuator_ctrlrange[:, 1])
                mujoco.mj_step(self.model, self.data)
            # Derived positions/sensors must correspond to the NEW qpos/qvel.
            mujoco.mj_forward(self.model, self.data)
        else:
            yaw = self.get_pose().rpy[2]
            vx, vy, omega = self._command
            delta = omega * duration
            # Exact SE(2) integration, stable also when omega -> 0.
            a = duration * np.sinc(delta / np.pi)
            b = duration * (delta / 2) * np.sinc(delta / (2*np.pi)) ** 2
            dx, dy = a*vx - b*vy, b*vx + a*vy
            q = self._root_q
            self.data.qpos[q:q+2] += [math.cos(yaw)*dx - math.sin(yaw)*dy,
                                     math.sin(yaw)*dx + math.cos(yaw)*dy]
            theta = yaw + delta
            self.data.qpos[q+3:q+7] = [math.cos(theta/2), 0, 0, math.sin(theta/2)]
            self.data.time += duration
            self._update_kinematic_velocity()
            mujoco.mj_forward(self.model, self.data)
        if not np.all(np.isfinite(self.data.qpos)) or not np.all(np.isfinite(self.data.qvel)):
            raise RuntimeError("Simulation diverged; reset and inspect controller settings")

    def _update_kinematic_velocity(self) -> None:
        yaw = self.get_pose().rpy[2]
        vx, vy, omega = self._command
        self.data.qvel[:] = 0
        v = self._root_v
        self.data.qvel[v:v+2] = [math.cos(yaw)*vx - math.sin(yaw)*vy,
                               math.sin(yaw)*vx + math.cos(yaw)*vy]
        self.data.qvel[v+5] = omega

    def get_imu(self) -> dict:
        """Ideal MuJoCo IMU at 'imu' site, site-frame SI units, physics only.

        Accelerometer is specific force, including gravity support at rest.
        No sensor noise, bias, calibration, or hardware timing is modeled.
        """
        if self.mode != "physics":
            raise NotImplementedError("IMU dynamics are undefined for ideal kinematic motion")
        return {"gyro_rad_s": self.data.sensor("seminar_gyro").data.copy(),
                "specific_force_m_s2": self.data.sensor("seminar_accel").data.copy()}

    def get_ranges(self, angles=None, max_distance: float = 5.0) -> np.ndarray:
        """Ideal horizontal rays from base origin, relative to yaw; not Go2 LiDAR.

        Only scene group 0 is sensed; robot visual/collision groups 2/3 excluded.
        No return is +inf. Used for 2D exercises, ignores roll/pitch.
        """
        if not math.isfinite(max_distance) or max_distance <= 0:
            raise ValueError("max_distance must be positive and finite")
        angles = np.asarray([0.0] if angles is None else angles, dtype=float)
        if angles.ndim != 1 or not np.all(np.isfinite(angles)):
            raise ValueError("angles must be a finite one-dimensional array")
        pose = self.get_pose()
        group = np.array([1, 0, 0, 0, 0, 0], dtype=np.uint8)
        result = []
        for a in angles + pose.rpy[2]:
            direction = np.array([math.cos(a), math.sin(a), 0.0])
            distance = mujoco.mj_ray(self.model, self.data, pose.position, direction,
                                     group, 1, -1, np.array([-1], dtype=np.int32))
            result.append(distance if 0 <= distance <= max_distance else np.inf)
        return np.asarray(result)

    def get_range(self, max_distance: float = 5.0) -> float:
        return float(self.get_ranges(max_distance=max_distance)[0])
