"""立位のGo2を表示。ウィンドウを閉じるか60秒で終了。"""
import argparse
from go2_seminar import Go2Sim
from go2_seminar.runtime import run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--headless", action="store_true")
parser.add_argument("--seconds", type=float, default=60.0)
args = parser.parse_args()
robot = Go2Sim("physics")
robot.stand()
run(robot, seconds=args.seconds, viewer=not args.headless)
print(robot.get_state())
