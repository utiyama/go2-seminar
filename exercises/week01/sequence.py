"""week01: 動作の順序・繰り返し・帰り道を考える。"""
import argparse
import math
from pathlib import Path

from go2_seminar import Go2Sim
from go2_seminar.runtime import run
from go2_seminar.sequence import Action, SequenceController
from go2_seminar.visualization import plot_planar_motion


# TODO: このリストを編集します。上から順に実行されます。
# seconds: 秒、vx/vy: ロボットから見た前方/左方向のm/s、yaw_rate: rad/s。
# 指定しなかった速度は0です。位置や向きは次の動作へ引き継がれます。
ACTIONS = [
    Action("前進", seconds=2.0, vx=0.2),
    Action("左に90度旋回", seconds=2.0, yaw_rate=math.pi / 4),
    Action("短く前進", seconds=1.0, vx=0.2),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--viewer", action="store_true", help="Go2と軌跡を画面に表示")
    parser.add_argument("--headless", action="store_true", help="画面を表示せずCSVと図を保存")
    parser.add_argument("--auto-close", action="store_true", help="動作終了時に画面を自動で閉じる")
    parser.add_argument("--repeat", type=int, default=1, help="動作列全体の繰り返し回数")
    parser.add_argument("--output", type=Path, default=Path("results/week01-sequence"),
                        help="保存先の名前（拡張子なし）")
    parser.add_argument("--target", nargs=3, type=float, metavar=("X", "Y", "YAW_DEG"),
                        help="目標のworld座標x・y [m] と向き [度]。結果の誤差を表示")
    args = parser.parse_args()
    try:
        sequence = SequenceController(ACTIONS, repeat=args.repeat)
        if args.target is not None and not all(math.isfinite(v) for v in args.target):
            raise ValueError("目標には有限の数値を指定してください。")
    except ValueError as error:
        parser.error(str(error))

    robot = Go2Sim("kinematic")
    initial = robot.get_state()
    print(f"動作列: {sequence.duration:.2f}秒、その後2秒停止", flush=True)
    states = run(robot, seconds=sequence.duration + 2.0, control=sequence,
                 viewer=args.viewer and not args.headless, trail=True,
                 keep_open=not args.auto_close, csv_path=args.output.with_suffix(".csv"))
    plot_planar_motion([initial, *states], args.output.with_suffix(".png"))
    pose = robot.get_pose()
    x, y = pose.position[:2]
    yaw = pose.rpy[2]
    if robot.time < sequence.duration - 1e-9:
        print("途中で終了しました。結果は実行できたところまでです。")
    print(f"最終状態: x={x:.3f} m, y={y:.3f} m, yaw={math.degrees(yaw):.2f}度")
    if args.target is not None:
        tx, ty, target_degrees = args.target
        angle = yaw - math.radians(target_degrees)
        heading_error = math.degrees(math.atan2(math.sin(angle), math.cos(angle)))
        print(f"目標との差: 位置={math.hypot(x - tx, y - ty):.4f} m, 向き={heading_error:+.2f}度")
    print(f"保存先: {args.output.with_suffix('.csv')}、{args.output.with_suffix('.png')}")
    print("平面移動モードです。脚の姿勢は固定しています。")


if __name__ == "__main__":
    main()
