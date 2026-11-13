"""week06: 地図の上で経路を計画し、/cmd_vel で経路をたどるノード。

ROS環境で実行します。先に sim_bridge（または実機）を動かしておきます。
    python exercises/week06/planner.py
    python exercises/week06/planner.py --goal 2.6 -1.2 --follow
"""
import argparse
import heapq
import math
from pathlib import Path
import time

import numpy as np

from go2_seminar.ros.maps import load_map, room_map  # 地図の読み込み（src/go2_seminar/ros/maps.py）

# 隣のセルへの動き: (列の変化, 行の変化, コスト)。縦横は1、斜めは√2。
DIAGONAL = math.sqrt(2)
MOVES = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
         (1, 1, DIAGONAL), (1, -1, DIAGONAL), (-1, 1, DIAGONAL), (-1, -1, DIAGONAL)]
LOOKAHEAD = 0.3   # [m] 経路上で、これだけ先の点を目標にして進む
ARRIVED = 0.08    # [m] ゴールにこれだけ近づいたら到着とする


def to_cell(xy, grid):
    """座標 (x, y) [m] をセル (col, row) にする。第5回の穴埋め1と同じ計算。"""
    col = math.floor((xy[0] - grid["x_min"]) / grid["resolution"])
    row = math.floor((xy[1] - grid["y_min"]) / grid["resolution"])
    return col, row


def to_xy(cell, grid):
    """セル (col, row) の中心の座標 (x, y) [m]。"""
    return (grid["x_min"] + (cell[0] + 0.5) * grid["resolution"],
            grid["y_min"] + (cell[1] + 0.5) * grid["resolution"])


def inflate(occupied, margin, resolution):
    """通れないセル occupied（True / False の配列）を、margin [m] だけ外側に広げて返す。"""
    cells = 0  # 穴埋め2の前: 広げない（ロボットを大きさのない点とみなす）

    # --- 穴埋め2（実習3）: 広げる距離をセルの数にする ---
    # 下の行の先頭の「# 」を消し、??? を、広げる距離 [m] を表す変数に置き換えてください。
    # cells = round(??? / resolution)

    blocked = occupied.copy()
    rows, cols = np.nonzero(occupied)
    for dr in range(-cells, cells + 1):
        for dc in range(-cells, cells + 1):
            if dr * dr + dc * dc > cells * cells:  # 円の外
                continue
            r, c = rows + dr, cols + dc
            inside = (r >= 0) & (r < occupied.shape[0]) & (c >= 0) & (c < occupied.shape[1])
            blocked[r[inside], c[inside]] = True
    return blocked


def heuristic(cell, goal):
    """セル cell からゴール goal までの直線距離（セル数）。障害物を無視した、残りのコストの見積もり。"""
    return math.hypot(goal[0] - cell[0], goal[1] - cell[1])


def search(blocked, start, goal, weight=1.0):
    """start から goal までの経路を探す。セルは (col, row)、blocked[row, col] が True のセルは通れない。

    戻り値は (経路, 調べたセル)。経路は start から goal までのセルのリストで、見つからなければ空。
    """
    rows, cols = blocked.shape
    cost = {start: 0.0}        # 出発点からそのセルまでのコスト
    parent = {start: None}     # そのセルへ、どのセルから来たか
    queue = [(0.0, 0, start)]  # (優先度, 追加した順番, セル)。優先度が小さいものから取り出す
    done = set()               # 調べ終わったセル
    pushed = 0
    while queue:
        _priority, _order, cell = heapq.heappop(queue)
        if cell in done:
            continue
        done.add(cell)
        if cell == goal:
            path = []
            while cell is not None:  # ゴールから parent をたどって出発点まで戻る
                path.append(cell)
                cell = parent[cell]
            return path[::-1], done
        for dc, dr, step in MOVES:
            nxt = (cell[0] + dc, cell[1] + dr)
            if not (0 <= nxt[0] < cols and 0 <= nxt[1] < rows) or blocked[nxt[1], nxt[0]]:
                continue
            new_cost = cost[cell] + step
            if new_cost < cost.get(nxt, math.inf):
                cost[nxt] = new_cost
                parent[nxt] = cell
                priority = new_cost  # 穴埋め1の前: 出発点からのコストだけで順番を決める（ダイクストラ法）

                # --- 穴埋め1（実習2）: ゴールまでの見積もりを足す（A*）---
                # 下の行の先頭の「# 」を消し、??? を heuristic() の呼び出しに置き換えてください。
                # priority = new_cost + weight * ???

                pushed += 1
                heapq.heappush(queue, (priority, pushed, nxt))
    return [], done


def wrap_angle(angle):
    """角度を −π〜π の範囲に直す。"""
    return math.atan2(math.sin(angle), math.cos(angle))


def steer(pose, target, speed):
    """いまの位置と向き pose = (x, y, yaw) から、目標点 target = (x, y) へ向かう (前進速度, 旋回速度) を返す。"""
    x, y, yaw = pose
    direction = math.atan2(target[1] - y, target[0] - x)  # 目標点の方向 [rad]（odom座標）

    # --- 穴埋め3（実習4）: 目標点の方向と、いまの向きの差で旋回する ---
    # 下の3行の先頭の「# 」を消し、??? を、ロボットのいまの向きを表す変数に置き換えてください。
    # error = wrap_angle(direction - ???)
    # v = speed if abs(error) < 0.5 else 0.0  # 向きが大きくずれている間は、その場で回る
    # return v, max(-1.0, min(1.0, 1.5 * error))

    return 0.0, 0.0  # 穴埋め3の前: 動かない


def next_target(path_xy, position, index):
    """経路 path_xy のうち、ロボットから LOOKAHEAD 以上離れた最初の点（なければ最後の点）と、その番号。"""
    while index < len(path_xy) - 1 and math.dist(path_xy[index], position) < LOOKAHEAD:
        index += 1
    return path_xy[index], index


def path_length(path_xy):
    return sum(math.dist(a, b) for a, b in zip(path_xy[:-1], path_xy[1:]))


def save_figure(output, grid, occupied, blocked, done, path_xy, start, goal, driven, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgb

    occupancy = grid["occupancy"]
    image = np.ones(occupancy.shape + (3,))
    image[occupancy == -1] = 0.6                       # 未観測: 灰
    image[blocked & ~occupied] = to_rgb("navajowhite")  # 余裕の分
    for col, row in done:
        if not blocked[row, col]:
            image[row, col] = to_rgb("lightskyblue")    # 調べたセル
    image[occupancy == 100] = 0.0                      # 占有: 黒
    res = grid["resolution"]
    extent = [grid["x_min"], grid["x_min"] + occupancy.shape[1] * res,
              grid["y_min"], grid["y_min"] + occupancy.shape[0] * res]
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.imshow(image, origin="lower", extent=extent)
    if path_xy:
        xy = np.array(path_xy)
        ax.plot(xy[:, 0], xy[:, 1], "-", color="tab:red", lw=2, label="planned path")
    if len(driven) > 1:
        xy = np.array(driven)
        ax.plot(xy[:, 0], xy[:, 1], "--", color="tab:blue", lw=1.5, label="driven (odom)")
    ax.plot(*start, "o", color="tab:green", label="start")
    ax.plot(*goal, "*", color="tab:red", ms=14, label="goal")
    ax.plot([], [], "s", color="lightskyblue", label="expanded cells")
    ax.plot([], [], "s", color="navajowhite", label="margin")
    known = np.argwhere(occupancy != -1)
    if known.size:  # 地図のある範囲だけを表示する
        (r0, c0), (r1, c1) = known.min(axis=0), known.max(axis=0)
        ax.set_xlim(extent[0] + c0 * res - 0.2, extent[0] + (c1 + 1) * res + 0.2)
        ax.set_ylim(extent[2] + r0 * res - 0.2, extent[2] + (r1 + 1) * res + 0.2)
    ax.set(xlabel="odom x [m]", ylabel="odom y [m]", title=title)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3, fontsize=8)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".png"), dpi=120)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--goal", nargs=2, type=float, default=[2.5, 0.0], metavar=("X", "Y"), help="ゴールの座標 [m]（odom座標）")
    parser.add_argument("--map", type=Path, default=None, help="第5回で保存した地図（.npz）。省略時は教材の部屋の地図")
    parser.add_argument("--margin", type=float, default=0.25, help="障害物から離す距離 [m]")
    parser.add_argument("--weight", type=float, default=1.0, help="ゴールまでの見積もりに掛ける重み（穴埋め1の後で有効）")
    parser.add_argument("--follow", action="store_true", help="計画した経路をたどって動く")
    parser.add_argument("--speed", type=float, default=0.15, help="前進速度 [m/s]（上限0.22）")
    parser.add_argument("--rviz", action="store_true", help="ゴールを RViz2 の 2D Goal Pose で指定する（--goal は使わない。終了は Ctrl+C）")
    parser.add_argument("--reset", action="store_true", help="開始前にシミュレータの位置を出発点に戻す（実機では何も起きない）")
    parser.add_argument("--output", type=Path, default=Path("results/week06-plan"), help="保存先の名前（拡張子なし）")
    parser.add_argument("--seconds", type=float, default=None, help="指定秒数で終了（省略時は到着かCtrl+Cまで）")
    args = parser.parse_args(argv)
    if not 0 < args.speed <= 0.22 or not 0 <= args.margin <= 1.0 or args.weight < 0:
        parser.error("--speed は0より大きく0.22以下、--margin は0以上1以下、--weight は0以上にしてください。")

    import rclpy
    from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
    from geometry_msgs.msg import PoseStamped, TwistStamped
    from nav_msgs.msg import OccupancyGrid, Odometry
    from nav_msgs.msg import Path as PathMsg
    from sensor_msgs.msg import LaserScan

    grid = load_map(args.map) if args.map else room_map()
    res = grid["resolution"]
    occupied = grid["occupancy"] != 0  # 占有と未観測は通れない
    blocked = inflate(occupied, args.margin, res)
    name = str(args.map) if args.map else "教材の部屋"
    print(f"地図: {name}（セル {res} m）  通れないセル {int(blocked.sum())} 個、"
          f"うち余裕の分 {int((blocked & ~occupied).sum())} 個", flush=True)

    state = {"pose": None, "truth": None, "closest": math.inf, "goal": None, "plan": []}
    started = time.monotonic()

    rclpy.init()
    node = rclpy.create_node("planner")
    cmd_pub = node.create_publisher(TwistStamped, "cmd_vel", 10)
    plan_pub = node.create_publisher(PathMsg, "plan", 10)
    map_pub = node.create_publisher(OccupancyGrid, "map",
                                    QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))

    def on_odom(msg):
        pose = msg.pose.pose
        yaw = 2 * math.atan2(pose.orientation.z, pose.orientation.w)
        state["pose"] = (pose.position.x, pose.position.y, yaw)

    def on_scan(scan):
        ranges = np.asarray(scan.ranges, dtype=float)
        ranges = ranges[np.isfinite(ranges) & (ranges >= scan.range_min)]
        if ranges.size:
            state["closest"] = min(state["closest"], float(ranges.min()))

    def on_truth(msg):
        state["truth"] = (msg.pose.position.x, msg.pose.position.y)

    def on_goal(msg):
        state["goal"] = (msg.pose.position.x, msg.pose.position.y)

    def publish_map_and_plan():
        now = node.get_clock().now().to_msg()
        shown = grid["occupancy"].copy()
        shown[blocked & (grid["occupancy"] == 0)] = 50  # 余裕の分は灰色で表示される
        msg = OccupancyGrid()
        msg.header.stamp, msg.header.frame_id = now, "odom"
        msg.info.resolution = res
        msg.info.height, msg.info.width = shown.shape
        msg.info.origin.position.x, msg.info.origin.position.y = grid["x_min"], grid["y_min"]
        msg.info.origin.orientation.w = 1.0
        msg.data = shown.ravel().tolist()
        map_pub.publish(msg)
        plan = PathMsg()
        plan.header.stamp, plan.header.frame_id = now, "odom"
        for x, y in state["plan"]:
            pose = PoseStamped()
            pose.header = plan.header
            pose.pose.position.x, pose.pose.position.y = float(x), float(y)
            pose.pose.orientation.w = 1.0
            plan.poses.append(pose)
        plan_pub.publish(plan)

    def send(v, w):
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.twist.linear.x, msg.twist.angular.z = float(v), float(w)
        cmd_pub.publish(msg)

    def time_left():
        return args.seconds is None or time.monotonic() - started < args.seconds

    def spin_until(condition, timeout):
        end = time.monotonic() + timeout
        while rclpy.ok() and time_left() and not condition() and time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.05)
        return condition()

    def plan_to(goal):
        """いまの位置から goal までの経路を計画し、図を保存する。経路（座標のリスト）と図の題名を返す。"""
        start = state["pose"][:2]
        start_cell, goal_cell = to_cell(start, grid), to_cell(goal, grid)
        print(f"出発 ({start[0]:.2f}, {start[1]:.2f}) → ゴール ({goal[0]:.2f}, {goal[1]:.2f})", flush=True)
        rows, cols = blocked.shape
        for label, cell in (("出発点", start_cell), ("ゴール", goal_cell)):
            if not (0 <= cell[0] < cols and 0 <= cell[1] < rows):
                print(f"{label}が地図の外にあります。")
                return [], ""
        if blocked[goal_cell[1], goal_cell[0]]:
            hint = "別の場所を指定してください。" if args.rviz else "--goal か --margin を変えてください。"
            print("ゴールが障害物か、その余裕の範囲の中にあります。" + hint)
            return [], ""
        usable = blocked.copy()  # 出発点のまわり3セルは、余裕の範囲に入っていても通れることにする
        area = (slice(max(start_cell[1] - 3, 0), start_cell[1] + 4), slice(max(start_cell[0] - 3, 0), start_cell[0] + 4))
        usable[area] &= occupied[area]
        cells, done = search(usable, start_cell, goal_cell, args.weight)
        path_xy = [to_xy(cell, grid) for cell in cells]
        if not cells:
            print(f"経路が見つかりません。調べたセル {len(done)} 個")
            title = f"no path, {len(done)} cells expanded"
        else:
            print(f"経路の長さ {path_length(path_xy):.2f} m  調べたセル {len(done)} 個", flush=True)
            title = f"path {path_length(path_xy):.2f} m, {len(done)} cells expanded"
        state["plan"] = path_xy
        save_figure(args.output, grid, occupied, usable, done, path_xy, start, goal, [], title)
        state["figure"] = (usable, done, start, goal, title)
        return path_xy, title

    def follow(path_xy):
        """経路をたどる。到着したら True。"""
        index, driven = 0, [state["pose"][:2]]
        begin, begin_pose = time.monotonic(), state["pose"]
        state["closest"] = math.inf
        next_step = time.monotonic()
        arrived = False
        while rclpy.ok() and time_left() and state["goal"] is None:
            rclpy.spin_once(node, timeout_sec=0.02)
            if time.monotonic() < next_step:
                continue
            next_step += 0.1  # 0.1秒ごとに指令を出す
            pose = state["pose"]
            driven.append(pose[:2])
            if math.dist(pose[:2], path_xy[-1]) < ARRIVED:
                arrived = True
                break
            target, index = next_target(path_xy, pose[:2], index)
            send(*steer(pose, target, args.speed))
            moved = math.dist(pose[:2], begin_pose[:2]) + abs(wrap_angle(pose[2] - begin_pose[2]))
            if time.monotonic() - begin > 5.0 and moved < 0.01:
                print("ロボットが動いていません。steer() の穴埋め3を確認してください。")
                break
        send(0.0, 0.0)
        usable, done, start, goal, title = state["figure"]
        save_figure(args.output, grid, occupied, usable, done, path_xy, start, goal, driven, title)
        if arrived:
            text = f"到着しました。ゴールまで {math.dist(state['pose'][:2], path_xy[-1]):.2f} m（odom）"
            if state["truth"] is not None:
                text += f"、実際の位置では {math.dist(state['truth'], path_xy[-1]):.2f} m"
            closest = "--" if math.isinf(state["closest"]) else f"{state['closest']:.2f} m"
            print(f"{text}  所要 {time.monotonic() - begin:.1f} s  障害物までの最小距離 {closest}", flush=True)
        return arrived

    node.create_subscription(Odometry, "odom", on_odom, 10)
    node.create_subscription(LaserScan, "scan", on_scan, qos_profile_sensor_data)
    node.create_subscription(PoseStamped, "sim/ground_truth", on_truth, 10)
    node.create_subscription(PoseStamped, "goal_pose", on_goal, 10)
    node.create_timer(1.0, publish_map_and_plan)  # 1秒ごとに /map と /plan を配信（RViz2 の Map と Path）
    status = 0
    try:
        if args.reset:
            from std_msgs.msg import Empty
            reset_pub = node.create_publisher(Empty, "sim/reset", 10)
            spin_until(lambda: False, 1.0)  # 橋渡しノードがこのノードを見つけるまで少し待つ
            reset_pub.publish(Empty())
            state["pose"] = None
            spin_until(lambda: False, 0.5)
            print("シミュレータを出発点に戻しました。", flush=True)
        if not spin_until(lambda: state["pose"] is not None, 5.0):
            print("/odom を受信できませんでした。sim_bridgeが動いているか確認してください。")
            status = 1
        goal = None if args.rviz else tuple(args.goal)
        while status == 0 and rclpy.ok() and time_left():
            if goal is None:
                print("RViz2の 2D Goal Pose でゴールを指定してください。終了は Ctrl+C。", flush=True)
                publish_map_and_plan()
                spin_until(lambda: state["goal"] is not None, math.inf)
                goal, state["goal"] = state["goal"], None
                if goal is None:
                    break
            path_xy, _title = plan_to(goal)
            publish_map_and_plan()
            if path_xy and args.follow:
                follow(path_xy)
            if not args.rviz:
                if not path_xy:
                    status = 2
                break
            goal, state["goal"] = state["goal"], None  # 走行中に次のゴールが届いていれば、それを使う
        if status == 0 and not args.rviz:
            spin_until(lambda: False, 1.5)  # RViz2 に経路が届くまで少し待つ
    except KeyboardInterrupt:
        pass
    finally:
        send(0.0, 0.0)
        rclpy.spin_once(node, timeout_sec=0.1)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    if status != 1:
        print(f"保存先: {args.output.with_suffix('.png')}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
