"""week01: 自律ロボット：状態と行動. See README.md for the exercise."""
from go2_seminar import Go2Sim
from go2_seminar.runtime import run

robot = Go2Sim("kinematic")
# TODO: Change body velocity and duration, predict the endpoint before running.
robot.set_velocity(vx=0.15, yaw_rate=0.3)
run(robot, seconds=4.0, csv_path="results/week01.csv")
print(robot.get_state())
print("This is ideal planar motion, not physical walking.")
