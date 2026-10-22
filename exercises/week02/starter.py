"""week02: 座標系と姿勢. See README.md for the exercise."""
from pathlib import Path
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from go2_seminar import Go2Sim
from go2_seminar.runtime import body_to_world


def world_to_body(points, xy, yaw):
    """world座標の点 (N, 2) を、位置 xy・向き yaw [rad] のロボットから見たbody座標に直す。

    TODO: body_to_world の逆の計算を書いてください。いまは受け取った値をそのまま返しています。
    ヒント: 先に xy を引いてから、-yaw だけ回転します。math.cos と math.sin が使えます。
    """
    return np.asarray(points, dtype=float)


robot = Go2Sim("kinematic")
# TODO: Try 0, 45, 90 degrees; keep API angles in radians.
robot.set_planar_pose(0.5, 0.2, np.deg2rad(45))
pose = robot.get_pose()
xy, yaw = pose.position[:2], pose.rpy[2]
local = np.array([[0, 0], [1, 0], [0, 0.5]])
world = body_to_world(local, xy, yaw)
print("body points:\n", local)
print("world points:\n", np.round(world, 4))

# 実習2・3: world座標から戻し、元のbody座標と一致するか確かめる。
back = world_to_body(world, xy, yaw)
print("back to body:\n", np.round(back, 4))
if np.allclose(back, local):
    print("往復の結果が元のbody座標と一致しました。")
else:
    print("往復の結果が元のbody座標と一致しません。world_to_body() を完成させてください。")

fig, ax = plt.subplots()
ax.plot(world[:2, 0], world[:2, 1], "r-o", label="body x")
ax.plot(world[[0, 2], 0], world[[0, 2], 1], "g-o", label="body y")
ax.set(xlabel="world x [m]", ylabel="world y [m]", aspect="equal", title="Coordinate transform")
ax.grid(); ax.legend()
Path("results").mkdir(exist_ok=True)
fig.savefig("results/week02.png"); plt.close(fig)
