"""理想平面移動: 前進→左横移動→左旋回→停止。脚は歩きません。"""
import argparse
from go2_seminar import Go2Sim
from go2_seminar.runtime import run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--viewer", action="store_true")
parser.add_argument("--headless", action="store_true")
args = parser.parse_args()
robot = Go2Sim("kinematic", obstacles=True)

def control(sim):
    t = sim.time
    if t < 2 - 1e-9:
        sim.set_velocity(vx=0.2)
    elif t < 3 - 1e-9:
        sim.set_velocity(vy=0.15)
    elif t < 5 - 1e-9:
        sim.set_velocity(yaw_rate=0.5)
    else:
        sim.stop()

run(robot, seconds=6.0, viewer=args.viewer and not args.headless,
    control=control, csv_path="results/planar_motion.csv")
print(robot.get_state())
print("Expected: x=0.4 m, y=0.15 m, yaw=1.0 rad, final velocity=0")
