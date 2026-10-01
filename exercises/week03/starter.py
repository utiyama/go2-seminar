"""week03: センサとノイズ. See README.md for the exercise."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from go2_seminar import Go2Sim

robot = Go2Sim("physics")
robot.step(2.0)  # settle
rng = np.random.default_rng(42)
sigma = 0.05  # TODO: compare noise standard deviations [rad/s].
samples = []
for _ in range(150):
    robot.step()
    truth = robot.get_imu()["gyro_rad_s"][1]
    samples.append([robot.time, truth, truth + rng.normal(0, sigma)])
samples = np.array(samples)
Path("results").mkdir(exist_ok=True)
np.savetxt("results/week03.csv", samples, delimiter=",", header="time_s,ideal_gyro_y_rad_s,noisy_gyro_y_rad_s", comments="")
fig, ax = plt.subplots()
ax.plot(samples[:, 0], samples[:, 1], label="ideal")
ax.plot(samples[:, 0], samples[:, 2], alpha=0.6, label="synthetic noise")
ax.set(xlabel="simulation time [s]", ylabel="gyro y [rad/s]"); ax.legend()
fig.savefig("results/week03.png"); plt.close(fig)
print("IMU:", robot.get_imu())
