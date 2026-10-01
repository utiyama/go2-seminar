"""Ground trails for MuJoCo and saved plots of planar motion."""
from pathlib import Path
import csv

import mujoco
import numpy as np


def load_planar_csv(path):
    """Read time/x/y/yaw from a kinematic log; do not infer missing joints."""
    states = []
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"time_s", "mode", "x_m", "y_m", "yaw_rad"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("CSVには time_s, mode, x_m, y_m, yaw_rad の列が必要です。")
        for row in reader:
            if row["mode"] != "kinematic":
                raise ValueError("再生できるのは平面移動（kinematic）のCSVです。")
            try:
                t, x, y, yaw = [float(row[key]) for key in ("time_s", "x_m", "y_m", "yaw_rad")]
            except (ValueError, TypeError) as error:
                raise ValueError(f"CSVの{reader.line_num}行目に読み取れない数値があります。") from error
            if not np.all(np.isfinite([t, x, y, yaw])) or t < 0:
                raise ValueError("時刻・座標・角度は有限の数値、時刻は0以上にしてください。")
            if states and t <= states[-1]["time_s"]:
                raise ValueError("CSVの時刻は行ごとに増える必要があります。")
            states.append({"time_s": t, "position_m": [x, y, 0.0], "rpy_rad": [0.0, 0.0, yaw]})
    if not states:
        raise ValueError("CSVに再生するデータがありません。")
    return states


def add_planar_trail(scene, positions):
    """Append a blue ground trail, green start, and orange end to an MjvScene.

    These are rendering-only geoms: no contacts or changes to the robot model.
    Downsample long paths to fit the scene while retaining both endpoints.
    """
    available = scene.maxgeom - scene.ngeom
    if not len(positions) or available < 2:
        return
    xy = np.asarray(positions, dtype=float)[:, :2]
    xy = xy[np.r_[True, np.any(np.abs(np.diff(xy, axis=0)) > 1e-10, axis=1)]]
    indices = np.unique(np.linspace(0, len(xy) - 1, min(len(xy), 201, available - 1), dtype=int))
    points = np.column_stack([xy[indices], np.full(len(indices), 0.018)])
    for start, end in zip(points[:-1], points[1:]):
        geom = scene.geoms[scene.ngeom]
        mujoco.mjv_initGeom(geom, mujoco.mjtGeom.mjGEOM_CAPSULE, np.zeros(3),
                           np.zeros(3), np.eye(3).ravel(), [0.1, 0.45, 1, 1])
        mujoco.mjv_connector(geom, mujoco.mjtGeom.mjGEOM_CAPSULE, 0.006, start, end)
        scene.ngeom += 1
    for point, color in [(xy[0], [0.1, 0.8, 0.3, 1]), (xy[-1], [1, 0.45, 0.05, 1])]:
        mujoco.mjv_initGeom(scene.geoms[scene.ngeom], mujoco.mjtGeom.mjGEOM_SPHERE,
                           [0.025, 0, 0], [*point, 0.025], np.eye(3).ravel(), color)
        scene.ngeom += 1


def plot_planar_motion(states, path):
    """Save an overhead path, heading arrows, and position/yaw time series."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not states:
        return
    times = np.array([s["time_s"] for s in states])
    xy = np.array([s["position_m"][:2] for s in states])
    yaw = np.array([s["rpy_rad"][2] for s in states])
    fig = plt.figure(figsize=(10, 5), layout="constrained")
    grid = fig.add_gridspec(2, 2)
    path_ax = fig.add_subplot(grid[:, 0])
    position_ax = fig.add_subplot(grid[0, 1])
    yaw_ax = fig.add_subplot(grid[1, 1], sharex=position_ax)
    path_ax.plot(xy[:, 0], xy[:, 1], color="tab:blue", label="Path")
    # Sample arrows only while moving; keep a single arrow when stationary.
    changed = np.r_[True, np.any(np.abs(np.diff(xy, axis=0)) > 1e-10, axis=1)
                    | (np.abs(np.diff(yaw)) > 1e-10)]
    moving = np.flatnonzero(changed)
    arrows = moving[np.unique(np.linspace(0, len(moving) - 1, min(6, len(moving)), dtype=int))]
    path_ax.quiver(xy[arrows, 0], xy[arrows, 1], 0.08 * np.cos(yaw[arrows]),
                   0.08 * np.sin(yaw[arrows]), angles="xy", scale_units="xy", scale=1,
                   color="0.3", width=0.006, label="Robot heading")
    path_ax.scatter(*xy[0], color="tab:green", s=55, label="Start", zorder=3)
    path_ax.scatter(*xy[-1], color="tab:orange", s=55, label="End", zorder=3)
    path_ax.set(xlabel="world x [m]", ylabel="world y [m]", title="View from above", aspect="equal")
    # Include the heading arrows even for a straight or stationary run.
    path_ax.set_xlim(xy[:, 0].min() - 0.12, xy[:, 0].max() + 0.12)
    path_ax.set_ylim(xy[:, 1].min() - 0.12, xy[:, 1].max() + 0.12)
    position_ax.plot(times, xy[:, 0], label="x")
    position_ax.plot(times, xy[:, 1], label="y")
    position_ax.set(ylabel="position [m]", title="Position over time")
    yaw_ax.plot(times, np.unwrap(yaw), color="tab:purple", label="yaw (unwrapped)")
    yaw_ax.set(xlabel="simulation time [s]", ylabel="yaw [rad]", title="Heading over time")
    for ax in [path_ax, position_ax, yaw_ax]:
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=160)
    finally:
        plt.close(fig)
