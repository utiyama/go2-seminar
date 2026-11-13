"""week07: オドメトリだけを頼りに正方形を一周し、出発点に戻れたかを調べるノード。

ROS環境で実行します。先に sim_bridge（または実機）を動かしておきます。
    python exercises/week07/square.py --reset
"""
import argparse
import math
from pathlib import Path
import signal
import time

import numpy as np


def wrap_angle(angle):
    """角度を −π〜π の範囲に直す。"""
    return math.atan2(math.sin(angle), math.cos(angle))


def corners(side, left=False):
    """出発点を (0, 0)、最初の向きを +x としたときの、正方形の角の座標。最後は出発点。"""
    sign = 1.0 if left else -1.0  # 右回りでは y が負の側を回る
    return [(side, 0.0), (side, sign * side), (0.0, sign * side), (0.0, 0.0)]


def to_odom(point, start):
    """出発時の位置と向き start = (x, y, yaw) を基準にした点を、odom座標に直す。"""
    x, y, yaw = start
    return (x + point[0] * math.cos(yaw) - point[1] * math.sin(yaw),
            y + point[0] * math.sin(yaw) + point[1] * math.cos(yaw))


def relative(pose, origin):
    """位置と向き pose = (x, y, yaw) を、origin から見た (x, y, yaw) に直す。to_odom() の逆。"""
    dx, dy = pose[0] - origin[0], pose[1] - origin[1]
    c, s = math.cos(origin[2]), math.sin(origin[2])
    return (c * dx + s * dy, -s * dx + c * dy, wrap_angle(pose[2] - origin[2]))


def steer(pose, target, speed):
    """目標点 target へ向かう (前進速度, 旋回速度)。第6回の steer() と同じ考え方。"""
    x, y, yaw = pose
    error = wrap_angle(math.atan2(target[1] - y, target[0] - x) - yaw)
    v = speed if abs(error) < 0.1 else 0.0  # 向きが合うまでは、その場で回る
    return v, max(-1.0, min(1.0, 2.0 * error))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--side", type=float, default=0.8, help="正方形の一辺 [m]")
    parser.add_argument("--speed", type=float, default=0.15, help="前進速度 [m/s]（上限0.22）")
    parser.add_argument("--left", action="store_true", help="左回りにする（省略時は右回り）")
    parser.add_argument("--reset", action="store_true", help="開始前にシミュレータの位置を出発点に戻す（実機では何も起きない）")
    parser.add_argument("--output", type=Path, default=Path("results/week07-square"), help="保存先の名前（拡張子なし）")
    parser.add_argument("--seconds", type=float, default=120.0, help="この秒数で打ち切る")
    args = parser.parse_args(argv)
    if not 0 < args.speed <= 0.22 or not 0.2 <= args.side <= 2.0:
        parser.error("--speed は0より大きく0.22以下、--side は0.2以上2以下にしてください。")

    import rclpy
    from rclpy.signals import SignalHandlerOptions
    from geometry_msgs.msg import PoseStamped, TwistStamped
    from nav_msgs.msg import Odometry

    state = {"odom": None, "truth": None}
    odom_path, truth_path = [], []
    started = time.monotonic()

    # Ctrl+C では rclpy を終了させない。finally で停止指令を送ってから終了する
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = rclpy.create_node("square")
    publisher = node.create_publisher(TwistStamped, "cmd_vel", 10)

    def send(v, w):
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.twist.linear.x, msg.twist.angular.z = float(v), float(w)
        publisher.publish(msg)

    def yaw_of(orientation):
        return 2 * math.atan2(orientation.z, orientation.w)

    def on_odom(msg):
        pose = msg.pose.pose
        state["odom"] = (pose.position.x, pose.position.y, yaw_of(pose.orientation))

    def on_truth(msg):
        state["truth"] = (msg.pose.position.x, msg.pose.position.y, yaw_of(msg.pose.orientation))

    def spin_until(condition, timeout):
        end = min(time.monotonic() + timeout, started + args.seconds)
        while rclpy.ok() and not condition() and time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.05)
        return condition()

    def drive(command, done):
        """0.1秒ごとに command() の速度を送り、done() が True になるまで続ける。"""
        next_step = time.monotonic()
        while rclpy.ok() and time.monotonic() - started < args.seconds:
            rclpy.spin_once(node, timeout_sec=0.02)
            if time.monotonic() < next_step:
                continue
            next_step += 0.1
            odom_path.append(relative(state["odom"], start)[:2])
            if truth_start is not None:
                truth_path.append(relative(state["truth"], truth_start)[:2])
            if done():
                return True
            send(*command())
        return False

    finished = False
    start = truth_start = None
    try:
        if args.reset:
            from std_msgs.msg import Empty
            reset_pub = node.create_publisher(Empty, "sim/reset", 10)
            spin_until(lambda: False, 1.0)  # 橋渡しノードがこのノードを見つけるまで少し待つ
            reset_pub.publish(Empty())
            spin_until(lambda: False, 0.5)
            print("シミュレータを出発点に戻しました。", flush=True)
        node.create_subscription(Odometry, "odom", on_odom, 10)
        node.create_subscription(PoseStamped, "sim/ground_truth", on_truth, 10)
        if not spin_until(lambda: state["odom"] is not None, 5.0):
            print("/odom を受信できませんでした。sim_bridgeが動いているか確認してください。")
        else:
            spin_until(lambda: state["truth"] is not None, 0.5)
            start, truth_start = state["odom"], state["truth"]
            direction = "左回り" if args.left else "右回り"
            print(f"開始: 一辺 {args.side} m の正方形を{direction}に一周します。", flush=True)
            finished = True
            for number, corner in enumerate(corners(args.side, args.left), start=1):
                target = to_odom(corner, start)
                if not drive(lambda: steer(state["odom"], target, args.speed),
                             lambda: math.dist(state["odom"][:2], target) < 0.03):
                    finished = False
                    break
                print(f"角 {number} に到着（odom {state['odom'][0]:.2f}, {state['odom'][1]:.2f}）", flush=True)
            if finished:  # 最後に、出発時の向きに戻す
                finished = drive(lambda: (0.0, max(-1.0, min(1.0, 2.0 * wrap_angle(start[2] - state["odom"][2])))),
                                 lambda: abs(wrap_angle(start[2] - state["odom"][2])) < 0.02)
            send(0.0, 0.0)
            spin_until(lambda: False, 1.0)  # 止まるのを待つ
    except KeyboardInterrupt:
        finished = False
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # ここから先は Ctrl+C を無視する（終了処理と図の保存を中断させない）
        send(0.0, 0.0)
        rclpy.spin_once(node, timeout_sec=0.1)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if start is None or not odom_path:
        return 1

    def gap(pose, origin):
        x, y, yaw = relative(pose, origin)
        return math.hypot(x, y), abs(math.degrees(yaw))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    xy = np.array(odom_path)
    ax.plot(xy[:, 0], xy[:, 1], "-", color="tab:orange", label="odometry")
    if truth_path:
        xy = np.array(truth_path)
        ax.plot(xy[:, 0], xy[:, 1], "-", color="black", label="truth")
        ax.plot(xy[-1, 0], xy[-1, 1], "s", color="tab:red", label="end (truth)")
    ax.plot(0.0, 0.0, "o", color="tab:green", label="start")
    ax.set(xlabel="x from start [m]", ylabel="y from start [m]", aspect="equal"); ax.grid(); ax.legend()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(args.output.with_suffix(".png"), dpi=120); plt.close(fig)

    if not finished:
        print("一周する前に終了しました。")
    distance, angle = gap(state["odom"], start)
    print(f"オドメトリでは  出発点まで {distance:.2f} m、向きの差 {angle:.0f} 度")
    if truth_start is not None:
        distance, angle = gap(state["truth"], truth_start)
        print(f"実際の位置では  出発点まで {distance:.2f} m、向きの差 {angle:.0f} 度")
    print(f"保存先: {args.output.with_suffix('.png')}")
    return 0 if finished else 1


if __name__ == "__main__":
    raise SystemExit(main())
