"""week04: Reactive Control / FSM. See README.md for the exercise."""
from go2_seminar import Go2Sim
from go2_seminar.runtime import run

robot = Go2Sim("kinematic", obstacles=True)
state = "FORWARD"
# TODO: Add TURN and a timed transition back to FORWARD.
def control(sim):
    global state
    if state == "FORWARD" and sim.get_range() < 0.65:
        state = "STOP"
        print("STOP at", sim.time, "s; range=", sim.get_range())
    if state == "FORWARD":
        sim.set_velocity(vx=0.2)
    else:
        sim.stop()

run(robot, seconds=6.0, control=control, csv_path="results/week04.csv")
print(state, robot.get_state())
print("Kinematic mode has no collision response; the FSM must stop it.")
