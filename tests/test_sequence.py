import math

import numpy as np
import pytest

from go2_seminar import Go2Sim
from go2_seminar.runtime import run
from go2_seminar.sequence import Action, SequenceController


@pytest.fixture
def robot():
    return Go2Sim("kinematic")


def execute(robot, actions, repeat=1):
    sequence = SequenceController(actions, repeat=repeat, start_time=robot.time, announce=False)
    return run(robot, seconds=sequence.duration + 0.2, control=sequence)


def test_action_boundaries_and_stop_have_no_extra_or_missing_steps(robot):
    # Short actions make one-frame scheduling errors visible in the endpoint.
    states = execute(robot, [Action("forward", .06, vx=.2),
                             Action("left", .04, vy=.3)])
    np.testing.assert_allclose(states[2]["position_m"][:2], [.012, 0], atol=1e-12)
    np.testing.assert_allclose(states[4]["position_m"][:2], [.012, .012], atol=1e-12)
    for state in states[5:]:
        np.testing.assert_allclose(state["position_m"][:2], [.012, .012], atol=1e-12)
        np.testing.assert_array_equal(state["linear_velocity_world_m_s"], [0, 0, 0])


def test_translation_and_turn_do_not_commute(robot):
    forward = Action("forward", 2, vx=.2)
    turn = Action("turn", 2, yaw_rate=math.pi / 4)
    execute(robot, [forward, turn])
    np.testing.assert_allclose(robot.get_pose().position[:2], [.4, 0], atol=1e-12)
    robot.reset()
    execute(robot, [turn, forward])
    np.testing.assert_allclose(robot.get_pose().position[:2], [0, .4], atol=1e-12)
    assert robot.get_pose().rpy[2] == pytest.approx(math.pi / 2)


def test_square_closes_position_and_heading_but_missing_last_turn_does_not(robot):
    side = [Action("forward", 2, vx=.2), Action("left", 2, yaw_rate=math.pi / 4)]
    execute(robot, side, repeat=4)
    np.testing.assert_allclose(robot.get_pose().position[:2], [0, 0], atol=1e-12)
    assert robot.get_pose().rpy[2] == pytest.approx(0, abs=1e-12)
    robot.reset()
    execute(robot, (side * 4)[:-1])
    np.testing.assert_allclose(robot.get_pose().position[:2], [0, 0], atol=1e-12)
    assert robot.get_pose().rpy[2] == pytest.approx(-math.pi / 2)


def test_return_path_requires_reversed_order_and_negated_velocities(robot):
    outward = [Action("forward", 2, vx=.2), Action("turn", 2, yaw_rate=math.pi / 4),
               Action("short forward", 1, vx=.2)]
    negative = [Action(a.name, a.seconds, -a.vx, -a.vy, -a.yaw_rate) for a in outward]
    execute(robot, outward + negative)
    assert np.linalg.norm(robot.get_pose().position[:2]) > .1
    robot.reset()
    execute(robot, outward + list(reversed(negative)))
    np.testing.assert_allclose(robot.get_pose().position[:2], [0, 0], atol=1e-12)
    assert robot.get_pose().rpy[2] == pytest.approx(0, abs=1e-12)


def test_repeat_continues_from_current_pose_and_supports_nonzero_start_time(robot):
    robot.set_planar_pose(1, 2, math.pi / 2)
    robot.step(.12)
    execute(robot, [Action("forward", .1, vx=.2)], repeat=3)
    np.testing.assert_allclose(robot.get_pose().position[:2], [1, 2.06], atol=1e-12)


@pytest.mark.parametrize("kwargs", [
    {"seconds": 0}, {"seconds": .01}, {"seconds": float("nan")},
    {"seconds": 1, "vx": .4, "vy": .4},
    {"seconds": 1, "yaw_rate": math.pi / 2},
])
def test_invalid_actions_are_rejected_before_running(kwargs):
    with pytest.raises(ValueError):
        Action("invalid", **kwargs)


def test_empty_sequence_and_invalid_repeat_are_rejected():
    with pytest.raises(ValueError):
        SequenceController([])
    with pytest.raises(ValueError):
        SequenceController([Action("wait", 1)], repeat=0)
