"""week05: /scan と /odom から占有格子地図を作るノード。

ROS環境で実行します。先に sim_bridge（または実機）を動かしておきます。
    python exercises/week05/mapping.py
    python exercises/week05/mapping.py --resolution 0.1 --output results/week05-coarse
"""
import argparse
import math
from pathlib import Path
import time

import numpy as np

from go2_seminar.runtime import body_to_world  # 第2回の座標変換: body_to_world(点, [x, y], yaw)

# 地図にする範囲（odom座標）。左下の角が (X_MIN, Y_MIN) です。
X_MIN, Y_MIN = -3.0, -3.0     # [m]
WIDTH_M, HEIGHT_M = 8.0, 6.0  # [m]


def read_scan(scan):
    """LaserScan から、物に当たった光線の距離 r [m] と角度 a [rad] を取り出す。"""
    ranges = np.asarray(scan.ranges, dtype=float)
    angles = scan.angle_min + np.arange(len(ranges)) * scan.angle_increment
    valid = np.isfinite(ranges) & (ranges > scan.range_min)  # inf（届かない）と近すぎる値を除く
    return ranges[valid], angles[valid]


def polar_to_xy(r, a):
    """距離 r と角度 a を、ロボット座標の点 (N, 2) にする。x が前、y が左。"""
    return np.column_stack([r * np.cos(a), r * np.sin(a)])


def ray_points(r, a, step):
    """各光線が通り抜けた点（ロボット座標）。ロボットから物の手前までを step [m] 間隔で並べる。"""
    d = np.arange(0.0, r.max() if r.size else 0.0, step)
    passed = d[None, :] < r[:, None] - step
    x = (d[None, :] * np.cos(a)[:, None])[passed]
    y = (d[None, :] * np.sin(a)[:, None])[passed]
    return np.column_stack([x, y])


def to_cells(points, resolution):
    """点 (N, 2) [m] を、格子の列番号 col（x方向）と行番号 row（y方向）にする。

    resolution はセルの一辺 [m]。地図の左下の角 (X_MIN, Y_MIN) にあるセルが (col, row) = (0, 0)。
    """
    x, y = points[:, 0], points[:, 1]

    # --- 穴埋め1（実習2）: 座標をセル番号にする ---
    # 下の3行の先頭の「# 」を消し、??? をセルの一辺を表す変数に置き換えてください。
    # col = np.floor((x - X_MIN) / ???).astype(int)
    # row = np.floor((y - Y_MIN) / ???).astype(int)
    # return col, row

    return np.zeros(0, dtype=int), np.zeros(0, dtype=int)  # 穴埋め1の前: どのセルにも入れない


def to_odom(local, pose):
    """ロボット座標の点 local (N, 2) を、odom座標に変換する。pose は (x, y, yaw)。"""
    x, y, yaw = pose

    # --- 穴埋め2（実習3）: ロボットの位置と向きを使って変換する ---
    # 下の行の先頭の「# 」を消し、??? を上の x、y、yaw で置き換えてください。
    # return body_to_world(local, [???, ???], ???)

    return local  # 穴埋め2の前: 変換しない（ロボットが原点で前を向いていると仮定したのと同じ）


class Grid:
    """占有格子地図。セルごとに、物に当たった回数と光線が通り抜けた回数を数える。"""

    def __init__(self, resolution):
        self.resolution = resolution
        self.cols = round(WIDTH_M / resolution)
        self.rows = round(HEIGHT_M / resolution)
        self.hits = np.zeros((self.rows, self.cols), dtype=int)    # 物に当たった回数
        self.passes = np.zeros((self.rows, self.cols), dtype=int)  # 通り抜けた回数

    def add(self, counts, col, row):
        """counts（hits か passes）の (row, col) を1ずつ増やす。地図の外は無視する。"""
        inside = (col >= 0) & (col < self.cols) & (row >= 0) & (row < self.rows)
        np.add.at(counts, (row[inside], col[inside]), 1)

    def occupancy(self, min_hits):
        """各セルを 100（占有）、0（空き）、-1（未観測）に分ける。ROSの OccupancyGrid と同じ値。"""
        result = np.full(self.hits.shape, -1, dtype=np.int8)
        result[self.passes > 0] = 0
        result[self.hits >= min_hits] = 100
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--resolution", type=float, default=0.05, help="セルの一辺 [m]")
    parser.add_argument("--min-hits", type=int, default=2, help="この回数以上当たったセルを占有とする")
    parser.add_argument("--truth", action="store_true",
                        help="/odom の代わりに誤差のない位置 /sim/ground_truth を使う（シミュレータのみ）")
    parser.add_argument("--output", type=Path, default=Path("results/week05-map"), help="保存先の名前（拡張子なし）")
    parser.add_argument("--seconds", type=float, default=None, help="指定秒数で終了（省略時はCtrl+Cまで）")
    args = parser.parse_args(argv)
    if not 0.01 <= args.resolution <= 0.5 or args.min_hits < 1:
        parser.error("--resolution は0.01以上0.5以下、--min-hits は1以上にしてください。")

    import rclpy
    from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
    from geometry_msgs.msg import PoseStamped
    from nav_msgs.msg import OccupancyGrid, Odometry
    from sensor_msgs.msg import LaserScan

    grid = Grid(args.resolution)
    state = {"pose": None, "local": np.zeros((0, 2)), "scans": 0}
    path = []
    start = time.monotonic()

    rclpy.init()
    node = rclpy.create_node("mapping")
    map_pub = node.create_publisher(OccupancyGrid, "map",
                                    QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))

    def set_pose(pose):
        # 平面上の向き（yaw）は、クォータニオンの z と w から求まる（第2回）。
        yaw = 2 * math.atan2(pose.orientation.z, pose.orientation.w)
        state["pose"] = (pose.position.x, pose.position.y, yaw)

    def on_scan(scan):
        if state["pose"] is None:  # まだ位置を受け取っていない
            return
        pose = state["pose"]
        r, a = read_scan(scan)
        state["local"] = polar_to_xy(r, a)

        hit = to_odom(state["local"], pose)                      # 物に当たった点
        grid.add(grid.hits, *to_cells(hit, args.resolution))
        free = to_odom(ray_points(r, a, args.resolution), pose)  # 光線が通り抜けた点
        grid.add(grid.passes, *to_cells(free, args.resolution))

        path.append(pose[:2])
        state["scans"] += 1

    def publish_map():
        msg = OccupancyGrid()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = "odom"
        msg.info.resolution = float(args.resolution)
        msg.info.width, msg.info.height = grid.cols, grid.rows
        msg.info.origin.position.x, msg.info.origin.position.y = X_MIN, Y_MIN
        msg.info.origin.orientation.w = 1.0
        msg.data = grid.occupancy(args.min_hits).ravel().tolist()
        map_pub.publish(msg)

    node.create_subscription(LaserScan, "scan", on_scan, qos_profile_sensor_data)
    if args.truth:
        node.create_subscription(PoseStamped, "sim/ground_truth", lambda m: set_pose(m.pose), 10)
    else:
        node.create_subscription(Odometry, "odom", lambda m: set_pose(m.pose.pose), 10)
    node.create_timer(1.0, publish_map)  # 1秒ごとに /map を配信（RViz2 の Map に表示される）
    source = "/sim/ground_truth" if args.truth else "/odom"
    print(f"開始: セル {args.resolution} m、位置は {source}。終了は Ctrl+C。", flush=True)
    try:
        while rclpy.ok() and (args.seconds is None or time.monotonic() - start < args.seconds):
            rclpy.spin_once(node, timeout_sec=0.05)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if not state["scans"]:
        print("scanか位置を受信できませんでした。sim_bridgeが動いているか確認してください。")
        return 1

    occupancy = grid.occupancy(args.min_hits)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    local = state["local"]
    ax1.plot(local[:, 0], local[:, 1], ".", color="tab:red", ms=3)
    ax1.plot(0, 0, "g^")
    ax1.set(xlabel="robot x [m] (forward)", ylabel="robot y [m] (left)", aspect="equal", title="last scan, robot frame")
    ax1.grid()
    image = np.select([occupancy == 100, occupancy == 0], [0.0, 1.0], default=0.6)  # 黒: 占有、白: 空き、灰: 未観測
    ax2.imshow(image, cmap="gray", vmin=0, vmax=1, origin="lower",
               extent=[X_MIN, X_MIN + WIDTH_M, Y_MIN, Y_MIN + HEIGHT_M])
    xy = np.array(path)
    ax2.plot(xy[:, 0], xy[:, 1], "-", color="tab:blue", lw=1)
    ax2.plot(xy[0, 0], xy[0, 1], "go")
    ax2.plot(xy[-1, 0], xy[-1, 1], "rs")
    ax2.set(xlabel="odom x [m]", ylabel="odom y [m]", title=f"occupancy grid ({args.resolution} m, pose: {source})")
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output.with_suffix(".png"), dpi=120)
    plt.close(fig)
    np.savez(args.output.with_suffix(".npz"), occupancy=occupancy, resolution=args.resolution,
             x_min=X_MIN, y_min=Y_MIN)  # 地図の数値データ（occupancy[row, col]）
    print(f"scan {state['scans']} 回  占有セル {int((occupancy == 100).sum())} 個  "
          f"空きセル {int((occupancy == 0).sum())} 個  保存先: {args.output.with_suffix('.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
