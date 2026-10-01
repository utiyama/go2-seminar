"""week07: Localization / Sensor Fusion. See README.md for the exercise."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(42)
t = np.arange(101) * 0.1
truth = 0.2 * t
increments = np.diff(truth) + 0.003 + rng.normal(0, 0.008, len(t) - 1)
odom = np.r_[0, np.cumsum(increments)]
measurement = truth + rng.normal(0, 0.1, len(t))
estimate = np.zeros(len(t))
gain = 0.2  # TODO: compare 0, 0.2, 1; then make uncertainty-dependent.
for i in range(1, len(t)):
    predicted = estimate[i-1] + increments[i-1]
    estimate[i] = predicted + gain * (measurement[i] - predicted)
for name, values in [("odometry", odom), ("measurement", measurement), ("fusion", estimate)]:
    print(name, "RMSE [m] =", np.sqrt(np.mean((values - truth)**2)))
fig, ax = plt.subplots()
for name, values in [("truth", truth), ("odometry", odom), ("measurement", measurement), ("fusion", estimate)]:
    ax.plot(t, values, label=name, alpha=0.8)
ax.set(xlabel="time [s]", ylabel="position [m]", title="Synthetic 1D localization"); ax.legend()
Path("results").mkdir(exist_ok=True)
fig.savefig("results/week07.png"); plt.close(fig)
np.savetxt("results/week07.csv", np.column_stack([t, truth, odom, measurement, estimate]),
           delimiter=",", header="time_s,truth_m,odometry_m,measurement_m,estimate_m", comments="")
