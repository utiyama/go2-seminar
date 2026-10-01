"""保存した平面移動のCSVを、Go2と軌跡で再生する。元のCSVは変更しない。"""
import argparse
import math
from pathlib import Path

import numpy as np

from go2_seminar import Go2Sim
from go2_seminar.runtime import run
from go2_seminar.visualization import load_planar_csv, plot_planar_motion

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("csv", type=Path, nargs="?", default=Path("results/week01.csv"))
parser.add_argument("--viewer", action="store_true", help="Go2と軌跡を画面に表示")
parser.add_argument("--headless", action="store_true", help="画面を表示せず図を保存")
parser.add_argument("--auto-close", action="store_true", help="再生終了時に画面を自動で閉じる")
args = parser.parse_args()
try:
    states = load_planar_csv(args.csv)
except (OSError, ValueError) as error:
    parser.error(str(error))

plot_path = Path("results") / f"{args.csv.stem}_replay.png"
plot_planar_motion(states, plot_path)
print(f"軌跡の図: {plot_path}", flush=True)
if args.viewer and not args.headless:
    times = np.array([s["time_s"] for s in states])
    xy = np.array([s["position_m"][:2] for s in states])
    yaw = np.unwrap([s["rpy_rad"][2] for s in states])
    robot = Go2Sim("kinematic")
    robot.set_planar_pose(*xy[0], yaw[0])

    def control(sim):
        # Interpolate at the next display frame; unwrap yaw across +/- pi.
        t = min(times[-1], times[0] + sim.time + 0.02)
        sim.set_planar_pose(np.interp(t, times, xy[:, 0]),
                            np.interp(t, times, xy[:, 1]), np.interp(t, times, yaw))

    duration = max(1, math.ceil((times[-1] - times[0]) / 0.02 - 1e-9)) * 0.02
    print("CSVの最初の記録から、x・y・yawを再生します。脚の姿勢は固定です。", flush=True)
    run(robot, seconds=duration, viewer=True, trail=True,
        keep_open=not args.auto_close, control=control)
