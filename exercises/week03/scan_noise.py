"""week03: /scan に雑音を加えて /scan_noisy として配信する。

ROS環境で実行します。
    python exercises/week03/scan_noise.py --sigma 0.05
"""
import argparse
from collections import deque
import time

import numpy as np


def smooth(history):
    """直近のscan（配列のdeque）から1つの配列を作る。

    TODO: いまは最新の値をそのまま返します。直近 N 回の平均に変えてください。
    inf（測定なし）は平均に含めないようにします。ヒント: np.nanmean と np.where。
    """
    return history[-1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sigma", type=float, default=0.05, help="距離に加える正規分布の雑音の標準偏差 [m]")
    parser.add_argument("--average", type=int, default=1, help="smooth() に渡す直近のscanの数")
    parser.add_argument("--input", default="/scan")
    parser.add_argument("--output", default="/scan_noisy")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--seconds", type=float, default=None, help="指定秒数で終了（省略時はCtrl+Cまで）")
    args = parser.parse_args(argv)
    if args.average < 1 or not np.isfinite(args.sigma) or args.sigma < 0:
        parser.error("--average は1以上、--sigma は0以上にしてください。")

    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan

    rng = np.random.default_rng(args.seed)
    history = deque(maxlen=args.average)
    count = 0

    rclpy.init()
    node = rclpy.create_node("scan_noise")
    publisher = node.create_publisher(LaserScan, args.output, qos_profile_sensor_data)

    def on_scan(scan):
        nonlocal count
        ranges = np.asarray(scan.ranges, dtype=float)
        noisy = ranges + rng.normal(0.0, args.sigma, ranges.shape)
        noisy = np.where(np.isfinite(ranges), np.clip(noisy, scan.range_min, scan.range_max), np.inf)
        history.append(noisy)
        out = LaserScan()
        out.header = scan.header
        out.angle_min, out.angle_max, out.angle_increment = scan.angle_min, scan.angle_max, scan.angle_increment
        out.time_increment, out.scan_time = scan.time_increment, scan.scan_time
        out.range_min, out.range_max = scan.range_min, scan.range_max
        out.ranges = [float(r) for r in smooth(history)]
        publisher.publish(out)
        count += 1
        if count % 25 == 1:
            print(f"{count} 回目: sigma={args.sigma} m, average={args.average}", flush=True)

    node.create_subscription(LaserScan, args.input, on_scan, qos_profile_sensor_data)
    print(f"{args.input} に雑音を加えて {args.output} へ配信します。終了は Ctrl+C。", flush=True)
    start = time.monotonic()
    try:
        while rclpy.ok() and (args.seconds is None or time.monotonic() - start < args.seconds):
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
