"""week01: Go2の平面移動を表示し、軌跡と状態を保存する。"""
import argparse
import math

from go2_seminar import Go2Sim
from go2_seminar.runtime import run
from go2_seminar.visualization import plot_planar_motion

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--viewer", action="store_true", help="Go2と軌跡を画面に表示")
parser.add_argument("--headless", action="store_true", help="画面を表示せずCSVと図を保存")
parser.add_argument("--auto-close", action="store_true", help="動作終了時に画面を自動で閉じる")
# TODO: Change body velocity and duration; predict the path before running.
parser.add_argument("--vx", type=float, default=0.15, help="前進速度 [m/s]")
parser.add_argument("--vy", type=float, default=0.0, help="左向き速度 [m/s]")
parser.add_argument("--yaw-rate", type=float, default=0.3, help="左旋回の角速度 [rad/s]")
parser.add_argument("--seconds", type=float, default=4.0, help="移動時間 [s]、0.02の正の整数倍")
args = parser.parse_args()
if (not math.isfinite(args.seconds) or args.seconds <= 0
        or not math.isclose(args.seconds / 0.02, round(args.seconds / 0.02))):
    parser.error("--seconds は0.02の正の整数倍で指定してください。")

robot = Go2Sim("kinematic")
robot.set_velocity(vx=args.vx, vy=args.vy, yaw_rate=args.yaw_rate)
initial_state = robot.get_state()


def control(sim):
    if sim.time >= args.seconds - 1e-9:
        sim.stop()


# Keep simulating for two seconds after stopping, so the log shows the stop.
states = run(robot, seconds=args.seconds + 2.0,
             viewer=args.viewer and not args.headless, trail=True,
             keep_open=not args.auto_close, control=control,
             csv_path="results/week01.csv")
plot_planar_motion([initial_state, *states], "results/week01.png")
pose = robot.get_pose()
print(f"最終位置: x={pose.position[0]:.3f} m, y={pose.position[1]:.3f} m, yaw={pose.rpy[2]:.3f} rad")
print("保存先: results/week01.csv、results/week01.png")
print("平面移動モードです。脚の歩行や接触による停止は計算していません。")
