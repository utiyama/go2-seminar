import mujoco
import numpy as np
import pytest

from go2_seminar.visualization import add_planar_trail, load_planar_csv


@pytest.fixture
def model():
    return mujoco.MjModel.from_xml_string("<mujoco/>")


@pytest.mark.parametrize("capacity", [1, 2, 3, 12])
def test_trail_fits_scene_and_preserves_existing_geometry(capacity, model):
    scene = mujoco.MjvScene(model, maxgeom=capacity + 1)
    scene.ngeom = 1
    scene.geoms[0].pos[:] = [10, 20, 30]
    positions = np.column_stack([np.linspace(0, 5, 10000), np.zeros(10000)])
    add_planar_trail(scene, positions)
    assert scene.ngeom <= scene.maxgeom
    np.testing.assert_array_equal(scene.geoms[0].pos, [10, 20, 30])
    if capacity >= 2:
        np.testing.assert_allclose(scene.geoms[scene.ngeom - 2].pos[:2], positions[0])
        np.testing.assert_allclose(scene.geoms[scene.ngeom - 1].pos[:2], positions[-1])


def test_stationary_trail_has_no_degenerate_connectors(model):
    scene = mujoco.MjvScene(model, maxgeom=20)
    add_planar_trail(scene, np.zeros((100, 3)))
    assert scene.ngeom == 2
    for geom in scene.geoms[:scene.ngeom]:
        assert geom.type == mujoco.mjtGeom.mjGEOM_SPHERE
        assert np.all(np.isfinite(geom.mat))


@pytest.mark.parametrize("content", [
    "x,y\n1,2\n",  # Missing columns.
    "time_s,mode,x_m,y_m,yaw_rad\n",  # No samples.
    "time_s,mode,x_m,y_m,yaw_rad\n0,physics,0,0,0\n",
    "time_s,mode,x_m,y_m,yaw_rad\n0,kinematic,nan,0,0\n",
    "time_s,mode,x_m,y_m,yaw_rad\n0,kinematic,0,0,0\n0,kinematic,1,0,0\n",
])
def test_invalid_or_unsupported_recording_is_rejected(tmp_path, content):
    path = tmp_path / "invalid.csv"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        load_planar_csv(path)


def test_recording_retains_time_and_heading_across_wrap(tmp_path):
    path = tmp_path / "motion.csv"
    path.write_text("time_s,mode,x_m,y_m,yaw_rad\n"
                    "1,kinematic,0.1,0.2,3.13\n1.04,kinematic,0.3,0.4,-3.13\n",
                    encoding="utf-8-sig")
    states = load_planar_csv(path)
    assert [s["time_s"] for s in states] == [1, 1.04]
    np.testing.assert_allclose(states[-1]["position_m"][:2], [0.3, 0.4])
    assert states[-1]["rpy_rad"][2] == -3.13
