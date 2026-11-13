"""week07: 壁に向かって直進しながら、オドメトリとLiDARを合わせて進んだ距離を推定するノード。

ROS環境で実行します。先に sim_bridge（または実機）を動かしておきます。
    python exercises/week07/localize.py --reset
    python exercises/week07/localize.py --reset --gain 0.5
"""
import argparse
import math
from pathlib import Path
import time

import numpy as np


def front_distance(scan):
    """LaserScan から真正面（0度）の距離 [m] を取り出す。測定できていなければ nan。"""
    index = round((0.0 - scan.angle_min) / scan.angle_increment) % len(scan.ranges)
    value = float(scan.ranges[index])
    return value if math.isfinite(value) and value >= scan.range_min else math.nan


def measure(wall, front):
    """LiDARから求めた、出発点から進んだ距離 [m]。

    wall は出発点で測った壁までの距離、front はいまの壁までの距離。
    """
    # --- 穴埋め1（実習2）: 壁が近づいた分だけ進んでいる ---
    # 下の行の先頭の「# 」を消し、??? を、いまの壁までの距離を表す変数に置き換えてください。
    # return wall - ???

    return math.nan  # 穴埋め1の前: LiDARを使わない


def correct(predicted, measured, gain):
    """オドメトリによる予測 predicted を、LiDARによる観測 measured に gain の割合だけ近づける。"""
    # --- 穴埋め2（実習3）: 予測と観測の差に gain を掛けて足す ---
    # 下の行の先頭の「# 」を消し、??? を、観測を表す変数に置き換えてください。
    # return predicted + gain * (??? - predicted)

    return predicted  # 穴埋め2の前: 予測をそのまま使う


def kalman_gain(p, r):
    """予測の分散 p と観測の分散 r から、ゲインを決める。"""
    # --- 穴埋め3（発展）: 予測が不確かなほど、観測を信用する ---
    # 下の行の先頭の「# 」を消し、??? を、観測の分散を表す変数に置き換えてください。
    # return p / (p + ???)

    return 0.0  # 穴埋め3の前: 観測を使わない


class Estimator:
    """進んだ距離の推定値 estimate と、その分散 p を持つ。scan が届くたびに update() を呼ぶ。"""

    def __init__(self, gain, odom_sigma, scan_sigma, kalman=False):
        self.gain = gain              # 固定のゲイン（kalman が False のとき使う）
        self.q = odom_sigma ** 2      # 1 m 進むごとに増える予測の分散 [m²]
        self.r = scan_sigma ** 2      # 観測の分散 [m²]
        self.kalman = kalman
        self.estimate = 0.0           # 出発点から進んだ距離の推定値 [m]
        self.p = 0.0                  # 推定値の分散 [m²]。出発点では 0（位置が分かっている）
        self.last_gain = 0.0

    def update(self, moved, wall, front):
        """moved は前回からオドメトリが進んだ距離 [m]。推定値を返す。"""
        predicted = self.estimate + moved      # 予測: オドメトリの分だけ進める
        self.p += self.q * abs(moved)          # 進んだ分だけ不確かになる
        measured = measure(wall, front)        # 観測: LiDARから求めた距離
        if not math.isfinite(measured):        # 観測がなければ予測のまま
            self.estimate = predicted
            return self.estimate
        gain = kalman_gain(self.p, self.r) if self.kalman else self.gain
        self.estimate = correct(predicted, measured, gain)  # 補正
        self.p = (1.0 - gain) * self.p         # 観測を使った分だけ確かになる
        self.last_gain = gain
        return self.estimate


def rmse(values, truth):
    error = np.asarray(values, dtype=float) - np.asarray(truth, dtype=float)
    error = error[np.isfinite(error)]
    return float(np.sqrt(np.mean(error ** 2))) if error.size else math.nan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gain", type=float, default=0.2, help="観測に近づける割合（0〜1）")
    parser.add_argument("--kalman", action="store_true", help="ゲインを kalman_gain() で決める（発展）")
    parser.add_argument("--odom-sigma", type=float, default=0.1, help="1 m 進んだときのオドメトリの誤差の標準偏差 [m]（--kalman で使う）")
    parser.add_argument("--scan-sigma", type=float, default=0.03, help="LiDARの距離の誤差の標準偏差 [m]（--kalman で使う）")
    parser.add_argument("--speed", type=float, default=0.1, help="前進速度 [m/s]（上限0.22）")
    parser.add_argument("--stop-distance", type=float, default=0.4, help="壁までこの距離になったら止まる [m]")
    parser.add_argument("--reset", action="store_true", help="開始前にシミュレータの位置を出発点に戻す（実機では何も起きない）")
    parser.add_argument("--output", type=Path, default=Path("results/week07-localize"), help="保存先の名前（拡張子なし）")
    parser.add_argument("--seconds", type=float, default=60.0, help="この秒数で打ち切る")
    args = parser.parse_args(argv)
    if not 0 < args.speed <= 0.22 or not 0 <= args.gain <= 1 or args.stop_distance < 0.2:
        parser.error("--speed は0より大きく0.22以下、--gain は0以上1以下、--stop-distance は0.2以上にしてください。")
    if args.odom_sigma <= 0 or args.scan_sigma <= 0:
        parser.error("--odom-sigma と --scan-sigma は正にしてください。")

    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import PoseStamped, TwistStamped
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import LaserScan

    estimator = Estimator(args.gain, args.odom_sigma, args.scan_sigma, args.kalman)
    state = {"odom": None, "truth": None, "front": math.nan, "scans": 0,
             "wall": None, "odom_start": None, "truth_start": None, "odom_last": 0.0, "driving": False,
             "moving_rows": None}
    first_fronts = []  # 出発点で測った壁までの距離（平均して wall にする）
    rows = []          # [時刻, 実際, オドメトリ, LiDAR, 推定, ゲイン]
    started = time.monotonic()

    rclpy.init()
    node = rclpy.create_node("localize")
    publisher = node.create_publisher(TwistStamped, "cmd_vel", 10)

    def send(v):
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.twist.linear.x = float(v)
        publisher.publish(msg)

    def on_odom(msg):
        state["odom"] = (msg.pose.pose.position.x, msg.pose.pose.position.y)

    def on_truth(msg):
        state["truth"] = (msg.pose.position.x, msg.pose.position.y)

    def on_scan(scan):
        state["front"] = front_distance(scan)
        state["scans"] += 1
        if state["odom"] is None:
            return
        if state["wall"] is None:  # まだ動いていない。壁までの距離を5回測る
            if math.isfinite(state["front"]):
                first_fronts.append(state["front"])
            return
        if not state["driving"]:
            return
        odom = math.dist(state["odom"], state["odom_start"])  # オドメトリで見た、出発点からの距離
        estimate = estimator.update(odom - state["odom_last"], state["wall"], state["front"])
        state["odom_last"] = odom
        truth = math.dist(state["truth"], state["truth_start"]) if state["truth_start"] else math.nan
        rows.append([time.monotonic() - started, truth, odom, measure(state["wall"], state["front"]),
                     estimate, estimator.last_gain])

    def spin_until(condition, timeout):
        end = min(time.monotonic() + timeout, started + args.seconds)
        while rclpy.ok() and not condition() and time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.05)
        return condition()

    status = 0
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
        node.create_subscription(LaserScan, "scan", on_scan, qos_profile_sensor_data)
        spin_until(lambda: len(first_fronts) >= 5, 5.0)
        if state["odom"] is None or state["scans"] == 0:
            print("/odom か /scan を受信できませんでした。sim_bridgeが動いているか確認してください。")
            status = 1
        elif len(first_fronts) < 5:
            print("正面に壁が見えません。ロボットを壁に向け、3.5 m 以内に置いてください。")
            status = 1
        else:
            state["wall"] = float(np.mean(first_fronts))
            state["odom_start"], state["truth_start"] = state["odom"], state["truth"]
            mode = "kalman_gain() で決める" if args.kalman else f"{args.gain}"
            print(f"開始: 壁まで {state['wall']:.2f} m、速度 {args.speed} m/s、ゲイン {mode}", flush=True)
            if state["wall"] <= args.stop_distance + 0.1:
                print("壁が近すぎます。--reset を付けるか、ロボットを壁から離してください。")
                status = 1
        if status == 0:
            state["driving"] = True
            next_step = time.monotonic()
            while rclpy.ok() and time.monotonic() - started < args.seconds:
                rclpy.spin_once(node, timeout_sec=0.02)
                if state["front"] < args.stop_distance:  # 止まる判断は、LiDARの生の距離で行う
                    break
                if time.monotonic() >= next_step:
                    next_step += 0.1  # 0.1秒ごとに指令を出す
                    send(args.speed)
            send(0.0)
            state["moving_rows"] = len(rows)
            spin_until(lambda: False, 1.0)  # 止まった後も1秒記録する
    except KeyboardInterrupt:
        pass
    finally:
        send(0.0)
        rclpy.spin_once(node, timeout_sec=0.1)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if status != 0 or not rows:
        return 1

    data = np.array(rows, dtype=float)
    t, truth, odom, lidar, estimate, gain = data.T
    t = t - t[0]
    has_truth = bool(np.isfinite(truth).any())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(args.output.with_suffix(".csv"), np.column_stack([t, truth, odom, lidar, estimate, gain]),
               delimiter=",", header="time_s,truth_m,odometry_m,lidar_m,estimate_m,gain", comments="", fmt="%.4f")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2 if has_truth else 1, 1, figsize=(7, 6.5 if has_truth else 3.6), sharex=True, squeeze=False)
    ax = axes[0, 0]
    if has_truth:
        ax.plot(t, truth, "-", color="black", lw=2, label="truth")
    ax.plot(t, odom, "-", color="tab:orange", label="odometry")
    ax.plot(t, lidar, ".", color="tab:green", ms=4, label="lidar")
    ax.plot(t, estimate, "-", color="tab:blue", label="estimate")
    ax.set(ylabel="distance from start [m]"); ax.grid(); ax.legend()
    if has_truth:
        ax = axes[1, 0]
        ax.plot(t, odom - truth, "-", color="tab:orange", label="odometry")
        ax.plot(t, lidar - truth, ".", color="tab:green", ms=4, label="lidar")
        ax.plot(t, estimate - truth, "-", color="tab:blue", label="estimate")
        ax.axhline(0.0, color="black", lw=1)
        ax.set(ylabel="error [m]"); ax.grid(); ax.legend()
    ax.set(xlabel="time [s]")
    fig.tight_layout(); fig.savefig(args.output.with_suffix(".png"), dpi=120); plt.close(fig)

    def meters(value):
        return f"{value:.3f} m" if math.isfinite(value) else "--"

    text = f"終了時の距離  オドメトリ {meters(odom[-1])}  LiDAR {meters(lidar[-1])}  推定 {meters(estimate[-1])}"
    if has_truth:
        text += f"  実際 {meters(truth[-1])}"
    print(text)
    if has_truth:
        print(f"誤差（RMSE）  オドメトリ {meters(rmse(odom, truth))}  LiDAR {meters(rmse(lidar, truth))}  "
              f"推定 {meters(rmse(estimate, truth))}")
    if args.kalman and state["moving_rows"]:
        moving = gain[:state["moving_rows"]]
        print(f"走行中のゲイン  最初 {moving[0]:.2f}  最後 {moving[-1]:.2f}")
    print(f"保存先: {args.output.with_suffix('.csv')}、{args.output.with_suffix('.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
