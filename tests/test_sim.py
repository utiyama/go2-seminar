"""Behavioral checks against the REAL pinned Go2 model (no model mocks)."""
import json
import math
import numpy as np
import pytest

from go2_seminar import Go2Sim
from go2_seminar.runtime import body_to_world, run


@pytest.fixture(scope="module")
def physical():
    return Go2Sim("physics")


@pytest.fixture(scope="module")
def planar():
    return Go2Sim("kinematic", obstacles=True)


@pytest.fixture(autouse=True)
def clean(physical, planar):
    physical.reset()
    planar.reset()


def test_stand_stable_and_torques_bounded(physical):
    for _ in range(250):
        physical.step()
        assert np.all(np.isfinite(physical.data.qpos))
        assert np.all(physical.data.ctrl >= physical.model.actuator_ctrlrange[:, 0])
        assert np.all(physical.data.ctrl <= physical.model.actuator_ctrlrange[:, 1])
    pose = physical.get_pose()
    assert 0.20 < pose.position[2] < 0.35
    assert np.linalg.norm(pose.position[:2]) < 0.15
    assert np.max(np.abs(pose.rpy[:2])) < 0.1
    assert np.linalg.norm(physical.get_imu()["specific_force_m_s2"]) == pytest.approx(9.81, abs=0.2)


def test_joint_command_changes_actual_motion(physical):
    physical.step(0.3)
    baseline = physical.get_joint_positions()
    physical.reset()
    target = physical.get_joint_positions()
    target[1::3] += 0.06
    physical.set_joint_targets(target)
    physical.step(0.3)
    assert np.linalg.norm(physical.get_joint_positions() - baseline) > 0.02


def test_straight_stop_and_body_frame(planar):
    planar.set_planar_pose(1, 2, math.pi/2)
    planar.set_velocity(vx=0.2)
    planar.step(1.0)
    np.testing.assert_allclose(planar.get_pose().position[:2], [1, 2.2], atol=1e-12)
    np.testing.assert_allclose(planar.get_state()["linear_velocity_world_m_s"], [0, .2, 0], atol=1e-12)
    before = planar.get_pose().position
    planar.stop()
    planar.step(1.0)
    np.testing.assert_allclose(planar.get_pose().position, before)
    assert not np.any(planar.data.qvel)


def test_exact_curved_motion_and_partition_invariance(planar):
    planar.set_velocity(vx=0.2, yaw_rate=0.5)
    planar.step(2.0)
    expected = [.4 * math.sin(1), .4 * (1 - math.cos(1))]
    np.testing.assert_allclose(planar.get_pose().position[:2], expected, atol=1e-12)
    assert planar.get_pose().rpy[2] == pytest.approx(1)
    planar.reset()
    planar.set_velocity(vx=0.2, yaw_rate=0.5)
    for _ in range(100):
        planar.step()
    np.testing.assert_allclose(planar.get_pose().position[:2], expected, atol=1e-12)


def test_negative_yaw_and_lateral_motion(planar):
    planar.set_velocity(vy=0.2, yaw_rate=-0.5)
    planar.step(2)
    np.testing.assert_allclose(planar.get_pose().position[:2], [.4*(1-math.cos(1)), .4*math.sin(1)], atol=1e-12)
    assert planar.get_pose().rpy[2] == pytest.approx(-1)


def test_reset_and_state_are_independent_copies(planar):
    planar.set_velocity(.2)
    planar.step(1)
    pose = planar.get_pose()
    pose.position[:] = 999
    joint_copy = planar.get_joint_positions()
    joint_copy[:] = 999
    state = planar.get_state()
    json.dumps(state)
    state["position_m"][0] = 999
    assert planar.get_pose().position[0] == pytest.approx(.2)
    assert np.max(planar.get_joint_positions()) < 10
    planar.reset()
    assert planar.time == 0
    planar.step(1)
    np.testing.assert_allclose(planar.get_pose().position[:2], [0, 0])


def test_range_excludes_self_and_respects_max_range(planar):
    assert planar.get_range() == pytest.approx(1.4)
    assert math.isinf(planar.get_range(max_distance=1.0))
    assert math.isinf(planar.get_ranges([math.pi])[0])
    planar.set_planar_pose(.4, 0, 0)
    assert planar.get_range() == pytest.approx(1.0)


@pytest.mark.parametrize("duration", [0, -1, float("nan"), float("inf"), .003])
def test_invalid_time_is_rejected(planar, duration):
    with pytest.raises(ValueError):
        planar.step(duration)
    assert planar.time == 0


@pytest.mark.parametrize("command", [[float("nan"), 0, 0], [1, 0, 0], [.4, .4, 0], [0, 0, 2]])
def test_invalid_velocity_is_rejected(planar, command):
    with pytest.raises(ValueError):
        planar.set_velocity(*command)


def test_mode_contracts(physical, planar):
    with pytest.raises(NotImplementedError):
        physical.set_velocity(.1)
    with pytest.raises(RuntimeError):
        physical.set_planar_pose(0, 0, 0)
    with pytest.raises(NotImplementedError):
        planar.get_imu()
    with pytest.raises(RuntimeError):
        planar.stand()
    with pytest.raises(ValueError):
        physical.set_joint_targets(np.full(12, 100))
    with pytest.raises(ValueError):
        physical.set_joint_targets([1, 2])


def test_coordinate_transform():
    actual = body_to_world([[1, 0], [0, 1]], [2, 3], math.pi/2)
    np.testing.assert_allclose(actual, [[2, 4], [1, 3]])


def test_run_csv_and_stop_on_error(planar, tmp_path):
    path = tmp_path / "subdir/state.csv"
    planar.set_velocity(.1)
    states = run(planar, seconds=.1, csv_path=path)
    assert len(states) == 5
    assert len(path.read_text().splitlines()) == 6
    assert states[-1]["time_s"] == pytest.approx(.1)
    assert not np.any(planar.data.qvel)
    def fail(sim):
        sim.set_velocity(.2)
        raise RuntimeError("controller failed")
    with pytest.raises(RuntimeError, match="controller failed"):
        run(planar, seconds=.1, control=fail)
    assert not np.any(planar.data.qvel)
