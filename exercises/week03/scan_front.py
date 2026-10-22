"""week03: /scan から前方の最小距離を読み、時間変化をCSVと図に残す。

ROS環境で実行します。先に sim_bridge（または実機）を動かしておきます。
    python exercises/week03/scan_front.py
    python exercises/week03/scan_front.py --topic /scan_noisy --output results/week03-scan-noisy
"""
import argparse
import math
from pathlib import Path
import time

import numpy as np


def sector_min(scan, center_deg, half_deg):
    """center_deg を中心に ±half_deg の範囲で最小距離 [m] を返す。測定なしなら inf。

    LaserScan の ranges は angle_min から angle_increment 刻みで並び、
    TurtleBot3 では 0 度が前方、90 度が左（反時計回り）です。
    """
    ranges = np.asarray(scan.ranges, dtype=float)
    angles = scan.angle_min + np.arange(len(ranges)) * scan.angle_increment
    offset = np.degrees(np.angle(np.exp(1j * (angles - math.radians(center_deg)))))  # -180..180
    selected = ranges[np.abs(offset) <= half_deg]
    selected = selected[np.isfinite(selected) & (selected >= scan.range_min)]
    return float(selected.min()) if selected.size else math.inf


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--topic", default="/scan", help="購読するLaserScanのトピック")
    parser.add_argument("--half-angle", type=float, default=15.0, help="扇形の半分の角度 [度]")
    parser.add_argument("--output", type=Path, default=Path("results/week03-scan"), help="保存先の名前（拡張子なし）")
    parser.add_argument("--seconds", type=float, default=None, help="指定秒数で終了（省略時はCtrl+Cまで）")
    args = parser.parse_args(argv)

    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan

    rows = []
    start = time.monotonic()
    last_print = -1.0

    def on_scan(scan):
        nonlocal last_print
        t = time.monotonic() - start
        front = sector_min(scan, 0.0, args.half_angle)
        # TODO: 左（90度）と右（270度）の最小距離も求め、rows と表示に加えてください。
        rows.append([t, front])
        if t - last_print >= 1.0:
            print(f"t={t:5.1f} s  前方{args.half_angle:.0f}度以内の最小距離: {front:.3f} m", flush=True)
            last_print = t

    rclpy.init()
    node = rclpy.create_node("scan_front")
    node.create_subscription(LaserScan, args.topic, on_scan, qos_profile_sensor_data)
    print(f"{args.topic} を待っています。終了は Ctrl+C。", flush=True)
    try:
        while rclpy.ok() and (args.seconds is None or time.monotonic() - start < args.seconds):
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if not rows:
        print("scanを受信できませんでした。sim_bridgeが動いているか、トピック名を確認してください。")
        return 1
    data = np.array(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(args.output.with_suffix(".csv"), data, delimiter=",", header="time_s,front_min_m", comments="")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    finite = np.isfinite(data[:, 1])
    ax.plot(data[finite, 0], data[finite, 1], ".-", label=f"front ±{args.half_angle:.0f}°")
    ax.set(xlabel="time [s]", ylabel="min distance [m]", title=f"{args.topic}")
    ax.grid(); ax.legend()
    fig.savefig(args.output.with_suffix(".png")); plt.close(fig)
    print(f"保存先: {args.output.with_suffix('.csv')}、{args.output.with_suffix('.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
