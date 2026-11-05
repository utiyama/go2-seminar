"""week04: /scan を見て /cmd_vel を出す状態遷移（FSM）のノード。

ROS環境で実行します。先に sim_bridge（または実機）を動かしておきます。
    python exercises/week04/fsm.py
    python exercises/week04/fsm.py --speed 0.1 --stop-distance 0.4
"""
import argparse
import math
from pathlib import Path
import time

import numpy as np

from go2_seminar.ros.scan import sector_min  # 第3回で使った扇形の最小距離


class Controller:
    """状態（FORWARD / STOP / TURN）を持ち、状態ごとの速度指令を決める。

    使う変数と関数:
      self.state            いまの状態の名前（文字列）
      self.state_since      いまの状態に入った時刻 [s]
      self.transition(名前, t)  状態を切り替え、state_since に t を記録する
      self.stop_distance    停止する前方距離 [m]（--stop-distance）
      self.turn_rate        旋回速度 [rad/s]（--turn-rate）。正で左、負で右
      self.turn_seconds     旋回を続ける時間 [s]（--turn-seconds）
    """

    def __init__(self, *, speed, stop_distance, turn_rate, turn_seconds):
        self.speed = speed
        self.stop_distance = stop_distance
        self.turn_rate = turn_rate
        self.turn_seconds = turn_seconds
        self.state = "FORWARD"
        self.state_since = 0.0
        self.front = self.left = self.right = math.inf

    def update(self, t, front, left, right):
        """0.1秒ごとに呼ばれる。t は開始からの秒数、front/left/right は各方向の最小距離 [m]。

        ここで「いつ状態を切り替えるか」を決め、新しい状態を返す。
        """
        self.front, self.left, self.right = front, left, right

        if self.state == "FORWARD" and front < self.stop_distance:
            self.transition("STOP", t)

        # --- 穴埋め1（実習2）: STOP になったら TURN に移る ---
        # 下の2行の先頭の「# 」を消し、??? を状態の名前に置き換えてください。
        # elif self.state == "STOP":
        #     self.transition(???, t)

        # --- 穴埋め2（実習2）: TURN を turn_seconds だけ続けたら FORWARD に戻る ---
        # t - self.state_since は、いまの状態に入ってからの秒数です。
        # elif self.state == "TURN" and t - self.state_since >= ???:
        #     self.transition("FORWARD", t)

        return self.state

    def command(self):
        """現在の状態に対応する (前進速度 [m/s], 旋回速度 [rad/s]) を返す。0.1秒ごとに呼ばれる。"""
        if self.state == "FORWARD":
            return self.speed, 0.0   # 発展（壁沿い）: 0.0 を左の距離から決めた旋回速度に置き換える
        if self.state == "TURN":
            return 0.0, self.turn_rate
        return 0.0, 0.0              # STOP

    def transition(self, new_state, t):
        """状態を new_state に変え、入った時刻を記録する。"""
        # --- 穴埋め3（実習4）: TURN に入るとき、空いている側へ回る向きを決める ---
        # self.left と self.right は update() で保存した左右の最小距離です。
        # 左のほうが広ければ正（左旋回）、右のほうが広ければ負（右旋回）にします。
        # if new_state == "TURN":
        #     self.turn_rate = abs(self.turn_rate) if ??? else -abs(self.turn_rate)
        self.state = new_state
        self.state_since = t


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--speed", type=float, default=0.15, help="前進速度 [m/s]（上限0.22）")
    parser.add_argument("--stop-distance", type=float, default=0.5, help="停止する前方距離 [m]")
    parser.add_argument("--turn-rate", type=float, default=math.pi / 4, help="旋回速度 [rad/s]")
    parser.add_argument("--turn-seconds", type=float, default=2.0, help="旋回を続ける時間 [s]")
    parser.add_argument("--half-angle", type=float, default=15.0, help="距離を見る扇形の半分の角度 [度]")
    parser.add_argument("--output", type=Path, default=Path("results/week04-fsm"), help="保存先の名前（拡張子なし）")
    parser.add_argument("--seconds", type=float, default=None, help="指定秒数で終了（省略時はCtrl+Cまで）")
    args = parser.parse_args(argv)
    if not 0 < args.speed <= 0.22 or args.stop_distance <= 0 or args.turn_seconds <= 0:
        parser.error("--speed は0より大きく0.22以下、--stop-distance と --turn-seconds は正にしてください。")

    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import TwistStamped
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import LaserScan

    controller = Controller(speed=args.speed, stop_distance=args.stop_distance,
                            turn_rate=args.turn_rate, turn_seconds=args.turn_seconds)
    distances = {"front": math.inf, "left": math.inf, "right": math.inf}
    odom_xy = [0.0, 0.0]
    rows = []
    start = time.monotonic()

    rclpy.init()
    node = rclpy.create_node("fsm")
    publisher = node.create_publisher(TwistStamped, "cmd_vel", 10)

    def on_scan(scan):
        distances["front"] = sector_min(scan, 0.0, args.half_angle)
        distances["left"] = sector_min(scan, 90.0, args.half_angle)
        distances["right"] = sector_min(scan, 270.0, args.half_angle)

    def on_odom(odom):
        odom_xy[0] = odom.pose.pose.position.x
        odom_xy[1] = odom.pose.pose.position.y

    def step():
        t = time.monotonic() - start
        before = controller.state
        state = controller.update(t, distances["front"], distances["left"], distances["right"])
        if state != before:
            print(f"t={t:5.1f} s  {before} → {state}  前方 {distances['front']:.2f} m", flush=True)
        v, w = controller.command()
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.twist.linear.x, msg.twist.angular.z = float(v), float(w)
        publisher.publish(msg)
        rows.append([t, state, distances["front"], distances["left"], distances["right"], v, w, *odom_xy])

    node.create_subscription(LaserScan, "scan", on_scan, qos_profile_sensor_data)
    node.create_subscription(Odometry, "odom", on_odom, 10)
    node.create_timer(0.1, step)  # 10 Hz で指令を出し続ける（止まると橋渡し・実機は0.5秒で停止）
    print(f"開始: 速度 {args.speed} m/s、停止距離 {args.stop_distance} m。終了は Ctrl+C。", flush=True)
    try:
        while rclpy.ok() and (args.seconds is None or time.monotonic() - start < args.seconds):
            rclpy.spin_once(node, timeout_sec=0.05)
    except KeyboardInterrupt:
        pass
    finally:
        stop = TwistStamped()
        stop.header.frame_id = "base_link"
        publisher.publish(stop)
        rclpy.spin_once(node, timeout_sec=0.1)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if not rows:
        print("scanを受信できませんでした。sim_bridgeが動いているか確認してください。")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.with_suffix(".csv").open("w", encoding="utf-8") as stream:
        stream.write("time_s,state,front_m,left_m,right_m,v_m_s,w_rad_s,odom_x_m,odom_y_m\n")
        for row in rows:
            stream.write(",".join(str(v) for v in row) + "\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t = np.array([r[0] for r in rows])
    front = np.array([r[2] for r in rows])
    states = [r[1] for r in rows]
    xy = np.array([[r[7], r[8]] for r in rows])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    for name, color in [("FORWARD", "tab:blue"), ("STOP", "tab:red"), ("TURN", "tab:orange")]:
        mask = np.array([s == name for s in states]) & np.isfinite(front)
        if mask.any():
            ax1.plot(t[mask], front[mask], ".", color=color, label=name)
    ax1.axhline(args.stop_distance, color="gray", ls="--", label="stop distance")
    ax1.set(xlabel="time [s]", ylabel="front distance [m]"); ax1.grid(); ax1.legend()
    ax2.plot(xy[:, 0], xy[:, 1], "-", color="tab:blue"); ax2.plot(xy[0, 0], xy[0, 1], "go"); ax2.plot(xy[-1, 0], xy[-1, 1], "rs")
    ax2.set(xlabel="odom x [m]", ylabel="odom y [m]", aspect="equal", title="odometry path"); ax2.grid()
    fig.tight_layout(); fig.savefig(args.output.with_suffix(".png")); plt.close(fig)
    print(f"最終状態: {controller.state}  保存先: {args.output.with_suffix('.csv')}、{args.output.with_suffix('.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
