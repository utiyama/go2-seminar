"""03_planar_motion.py が生成したCSVを図にする。"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

source = Path("results/planar_motion.csv")
if not source.exists():
    raise SystemExit("Run examples/03_planar_motion.py first")
data = np.genfromtxt(source, delimiter=",", names=True, dtype=None, encoding="utf-8")
fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), layout="constrained")
axes[0].plot(data["x_m"], data["y_m"])
axes[0].set(xlabel="world x [m]", ylabel="world y [m]", title="Ideal planar motion", aspect="equal")
axes[1].plot(data["time_s"], data["yaw_rad"])
axes[1].set(xlabel="time [s]", ylabel="yaw [rad]")
for ax in axes:
    ax.grid(True)
fig.savefig("results/trajectory.png", dpi=150)
plt.close(fig)
print("Saved results/trajectory.png")
