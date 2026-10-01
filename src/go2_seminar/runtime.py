"""Shared finite-duration runner, GUI lifecycle, CSV output."""
from contextlib import nullcontext
from pathlib import Path
import csv
import math
import time

import numpy as np


def run(sim, *, seconds=5.0, viewer=False, control=None, csv_path=None,
        trail=False, keep_open=False):
    """Run at 20 ms intervals; optionally show a ground trail and final view.

    keep_open only applies to viewer mode. CSV is saved before waiting for
    the user to close the window; the simulation does not advance meanwhile.
    """
    if not math.isfinite(seconds) or seconds <= 0 or not math.isclose(seconds/0.02, round(seconds/0.02)):
        raise ValueError("seconds must be a positive multiple of 0.02")
    handle = None
    if viewer:
        import mujoco.viewer
        try:
            handle = mujoco.viewer.launch_passive(sim.model, sim.data)
        except RuntimeError as error:
            raise RuntimeError("Viewer failed. On macOS use scripts/run.sh with --viewer.") from error
    rows = []
    positions = [sim.get_pose().position.copy()] if handle and trail else []
    if handle and trail:
        from go2_seminar.visualization import add_planar_trail
    print(f"mode={sim.mode}" + (" (ideal planar motion; no walking/contact response)" if sim.mode == "kinematic" else " (joint PD + MuJoCo dynamics)"))
    try:
        if handle:
            with handle.lock():
                handle.cam.distance = 1.8 if trail else 2.5
                handle.cam.azimuth = 135
                handle.cam.elevation = -55 if trail else -20
                handle.cam.lookat[:] = sim.get_pose().position
                if trail:
                    handle.user_scn.ngeom = 0
                    add_planar_trail(handle.user_scn, positions)
            handle.sync()
        start = time.monotonic()
        for index in range(round(seconds/0.02)):
            if handle and not handle.is_running():
                break
            with handle.lock() if handle else nullcontext():
                if control:
                    control(sim)
                sim.step()
                state = sim.get_state()
                if handle and trail:
                    positions.append(state["position_m"])
                    handle.user_scn.ngeom = 0
                    add_planar_trail(handle.user_scn, positions)
            rows.append(state)
            if handle:
                handle.sync()
                time.sleep(max(0, start + (index+1)*0.02 - time.monotonic()))
        with handle.lock() if handle and handle.is_running() else nullcontext():
            sim.stop()
        if csv_path:
            save_csv(rows, csv_path)
        if handle and keep_open and handle.is_running():
            print("動作が終わりました。視点を変えて確認し、ウィンドウを閉じてください。", flush=True)
            while handle.is_running():
                handle.sync()
                time.sleep(0.05)
    finally:
        with handle.lock() if handle and handle.is_running() else nullcontext():
            sim.stop()
        if handle:
            handle.close()
    return rows


def save_csv(states, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", "mode", "x_m", "y_m", "z_m", "roll_rad", "pitch_rad", "yaw_rad", "vx_world_m_s", "vy_world_m_s", "vz_world_m_s"])
        for state in states:
            writer.writerow([state["time_s"], state["mode"], *state["position_m"], *state["rpy_rad"], *state["linear_velocity_world_m_s"]])


def body_to_world(points, xy, yaw):
    """Transform (...,2) 2D points for week02/week05."""
    c, s = math.cos(yaw), math.sin(yaw)
    return np.asarray(points) @ np.array([[c, s], [-s, c]]) + np.asarray(xy)
