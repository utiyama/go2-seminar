"""world座標の位置[m]、姿勢[rad]、quaternion(w,x,y,z)を取得。"""
import json
from go2_seminar import Go2Sim

robot = Go2Sim()
robot.step(1.0)
print(json.dumps(robot.get_state(), indent=2))
print("IMU (ideal, body-mounted site):", robot.get_imu())
