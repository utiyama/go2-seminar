"""week02: 座標系と姿勢. See README.md for the exercise."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from go2_seminar import Go2Sim
from go2_seminar.runtime import body_to_world

robot = Go2Sim("kinematic")
# TODO: Try 0, 45, 90 degrees; keep API angles in radians.
robot.set_planar_pose(0.5, 0.2, np.deg2rad(45))
pose = robot.get_pose()
local = np.array([[0, 0], [1, 0], [0, 0.5]])
world = body_to_world(local, pose.position[:2], pose.rpy[2])
print("body points:", local, "world points:", world)
fig, ax = plt.subplots()
ax.plot(world[:2, 0], world[:2, 1], "r-o", label="body x")
ax.plot(world[[0, 2], 0], world[[0, 2], 1], "g-o", label="body y")
ax.set(xlabel="world x [m]", ylabel="world y [m]", aspect="equal", title="Coordinate transform")
ax.grid(); ax.legend()
Path("results").mkdir(exist_ok=True)
fig.savefig("results/week02.png"); plt.close(fig)
