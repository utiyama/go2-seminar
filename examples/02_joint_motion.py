"""小さな関節目標の変化をPD制御で確認。歩行ではありません。"""
import argparse
import math
from go2_seminar import Go2Sim
from go2_seminar.runtime import run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--viewer", action="store_true")
parser.add_argument("--headless", action="store_true")
parser.add_argument("--seconds", type=float, default=6.0)
args = parser.parse_args()
robot = Go2Sim()
home = robot.get_joint_positions()

def control(sim):
    target = home.copy()
    # Four thigh joints oscillate by only +/- 0.06 rad.
    for i, name in enumerate(sim.joint_names):
        if "thigh" in name:
            target[i] += 0.06 * math.sin(2 * math.pi * 0.5 * sim.time)
    sim.set_joint_targets(target)

run(robot, seconds=args.seconds, viewer=args.viewer and not args.headless,
    control=control, csv_path="results/joint_motion.csv")
print(robot.get_state())
