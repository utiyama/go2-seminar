"""week05: Mapping：2つのscanを重ねる. See README.md for the exercise."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from go2_seminar import Go2Sim
from go2_seminar.runtime import body_to_world

robot = Go2Sim("kinematic", obstacles=True)
angles = np.linspace(-np.pi / 3, np.pi / 3, 61)
fig, ax = plt.subplots()
for index, x in enumerate([0.0, 0.4]):
    robot.set_planar_pose(x, 0, 0)
    distances = robot.get_ranges(angles)
    valid = np.isfinite(distances)
    local = distances[valid, None] * np.column_stack([np.cos(angles[valid]), np.sin(angles[valid])])
    pose = robot.get_pose()
    estimated_xy = pose.position[:2].copy()
    if index == 1:
        estimated_xy[0] += 0.0  # TODO: inject 0.15 m pose error here.
    points = body_to_world(local, estimated_xy, pose.rpy[2])
    ax.scatter(points[:, 0], points[:, 1], s=12, label=f"scan {index}")
ax.set(xlabel="world x [m]", ylabel="world y [m]", aspect="equal", title="Ideal 2D ray mapping")
ax.legend(); ax.grid()
Path("results").mkdir(exist_ok=True)
fig.savefig("results/week05.png"); plt.close(fig)
print("Saved results/week05.png; this is ray geometry, not hardware LiDAR or SLAM.")
