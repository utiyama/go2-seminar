"""Execute the distributed entrypoints, including all seven exercise baselines."""
from pathlib import Path
import csv
import math
import os
import subprocess
import sys
import tomllib
import pytest

ROOT = Path(__file__).resolve().parents[1]


def invoke(*args):
    env = dict(os.environ, MPLBACKEND="Agg", MPLCONFIGDIR=str(ROOT / ".cache/matplotlib"), PYTHONUTF8="1")
    result = subprocess.run([sys.executable, "scripts/launch.py", *args], cwd=ROOT, env=env,
                            capture_output=True, text=True, encoding="utf-8", timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr


def test_day0_samples():
    invoke("examples/00_view.py", "--headless", "--seconds", "0.1")
    invoke("examples/01_pose.py")
    invoke("examples/02_joint_motion.py", "--headless")
    invoke("examples/03_planar_motion.py", "--headless")
    invoke("examples/04_log_state.py")
    invoke("examples/05_plot_trajectory.py")
    with (ROOT / "results/planar_motion.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 300
    assert float(rows[-1]["x_m"]) == pytest.approx(.4)
    assert float(rows[-1]["y_m"]) == pytest.approx(.15)
    assert float(rows[-1]["yaw_rad"]) == pytest.approx(1.)
    assert float(rows[-1]["vx_world_m_s"]) == 0
    assert (ROOT / "results/trajectory.png").stat().st_size > 1000


@pytest.mark.parametrize("week", range(1, 8))
def test_lesson_baseline_runs(week):
    invoke(f"exercises/week{week:02d}/starter.py")
    assert list((ROOT / "results").glob(f"week{week:02d}.*"))
    if week == 1:
        with (ROOT / "results/week01.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == 300  # Four seconds moving, two seconds stopped.
        for row in rows[199:]:
            assert float(row["x_m"]) == pytest.approx(0.5 * math.sin(1.2))
            assert float(row["y_m"]) == pytest.approx(0.5 * (1 - math.cos(1.2)))
            assert float(row["yaw_rad"]) == pytest.approx(1.2)
        for row in rows[200:]:
            assert float(row["vx_world_m_s"]) == 0
            assert float(row["vy_world_m_s"]) == 0
        assert (ROOT / "results/week01.png").stat().st_size > 1000


def test_week01_headless_override_and_csv_replay():
    invoke("exercises/week01/starter.py", "--viewer", "--headless",
           "--vx", "0.2", "--yaw-rate", "0", "--seconds", "0.1")
    path = ROOT / "results/week01.csv"
    original = path.read_bytes()
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 105
    assert float(rows[-1]["x_m"]) == pytest.approx(0.02)
    assert float(rows[-1]["y_m"]) == pytest.approx(0)
    invoke("examples/06_replay.py", str(path), "--viewer", "--headless")
    assert path.read_bytes() == original
    assert (ROOT / "results/week01_replay.png").stat().st_size > 1000


def test_direct_pins_match_lock():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    lock = (ROOT / "requirements.txt").read_text()
    for requirement in project["dependencies"] + project["optional-dependencies"]["dev"]:
        assert requirement in lock
