"""Timed body-frame commands for the week01 motion-composition exercise."""
from bisect import bisect_right
from dataclasses import dataclass
from itertools import accumulate
import math


@dataclass(frozen=True)
class Action:
    """One constant command: seconds [s], vx/vy [m/s], yaw_rate [rad/s]."""

    name: str
    seconds: float
    vx: float = 0.0
    vy: float = 0.0
    yaw_rate: float = 0.0

    def __post_init__(self):
        ticks = self.seconds / 0.02
        if not math.isfinite(ticks) or ticks <= 0 or not math.isclose(ticks, round(ticks)):
            raise ValueError(f"{self.name}: 時間は0.02秒の正の整数倍にしてください。")
        if not all(math.isfinite(v) for v in (self.vx, self.vy, self.yaw_rate)):
            raise ValueError(f"{self.name}: 速度には有限の数値を指定してください。")
        if math.hypot(self.vx, self.vy) > 0.5 or abs(self.yaw_rate) > 1.5:
            raise ValueError(f"{self.name}: 並進速度は0.5 m/s以下、旋回速度は1.5 rad/s以下です。")


class SequenceController:
    """Run Actions in order, then stop. Pass this as runtime.run's control.

    Scheduling uses integer 20 ms ticks to avoid drift at action boundaries.
    A repeat continues from the current pose; it never resets the robot.
    """

    def __init__(self, actions, *, repeat=1, start_time=0.0, announce=True):
        self.actions = tuple(actions)
        if not self.actions or not all(isinstance(action, Action) for action in self.actions):
            raise ValueError("動作列にはActionを1つ以上入れてください。")
        if isinstance(repeat, bool) or not isinstance(repeat, int) or repeat < 1:
            raise ValueError("繰り返し回数は1以上の整数にしてください。")
        if not math.isfinite(start_time) or start_time < 0:
            raise ValueError("開始時刻は0以上の有限の数値にしてください。")
        self.repeat = repeat
        self.start_time = start_time
        self.announce = announce
        self._ends = tuple(accumulate(round(action.seconds / 0.02) for action in self.actions))
        self._last_index = None

    @property
    def duration(self):
        return self._ends[-1] * self.repeat * 0.02

    def __call__(self, sim):
        if sim.mode != "kinematic":
            raise ValueError("動作列はkinematicモードで実行してください。")
        if sim.time < self.start_time:
            sim.stop()
            return
        tick = round((sim.time - self.start_time) / 0.02)
        cycle, within_cycle = divmod(tick, self._ends[-1])
        if cycle >= self.repeat:
            index = len(self.actions) * self.repeat
            sim.stop()
            message = "動作列終了 → 停止"
        else:
            within_index = bisect_right(self._ends, within_cycle)
            index = cycle * len(self.actions) + within_index
            action = self.actions[within_index]
            # Set every velocity component, including zeros, at each step.
            sim.set_velocity(action.vx, action.vy, action.yaw_rate)
            message = f"{cycle + 1}周目 / 動作{within_index + 1}: {action.name}"
        if self.announce and index != self._last_index:
            print(f"t={sim.time:.2f} s  {message}", flush=True)
        self._last_index = index
