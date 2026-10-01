"""物理モードの状態を5秒分CSV保存。"""
from go2_seminar import Go2Sim
from go2_seminar.runtime import run

robot = Go2Sim()
run(robot, seconds=5.0, csv_path="results/state.csv")
print("Saved results/state.csv (250 rows; world-frame position and velocity)")
