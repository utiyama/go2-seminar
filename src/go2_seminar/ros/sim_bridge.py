"""シミュレータをTurtleBot3 Burgerに見立ててROS 2に接続する橋渡しノード。

購読: /cmd_vel (geometry_msgs/TwistStamped、--twist で Twist)
配信: /odom (nav_msgs/Odometry)、/scan (sensor_msgs/LaserScan)、/tf、/tf_static、
      /sim/ground_truth (geometry_msgs/PoseStamped、誤差のない真の位置)

差動二輪として動かすため、横方向の速度は無視します。速度の上限はBurgerに合わせて
0.22 m/s、旋回は教材の上限 1.5 rad/s です。脚は歩かず、胴体の位置だけを更新します。

実行例（ROS環境の中で）:
    python scripts/launch.py -m go2_seminar.ros.sim_bridge --viewer
"""
import argparse
import math
import sys
import time

import numpy as np

from go2_seminar import Go2Sim

MAX_LINEAR = 0.22        # m/s, TurtleBot3 Burger
MAX_ANGULAR = 1.5        # rad/s, teaching limit of Go2Sim (Burger itself allows 2.84)
STEP = 0.02              # s, simulation step
SCAN_COUNT = 360         # LDS-02 style: 1 deg resolution, counter-clockwise from +x
SCAN_RANGE = (0.12, 3.5) # m
BASE_TO_SCAN = (-0.032, 0.0, 0.172)  # m, base_link -> base_scan on the Burger


def quaternion_about_z(yaw):
    return (0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2))  # x, y, z, w


class OdometryModel:
    """Integrates the commanded motion with optional systematic errors.

    linear_scale / angular_scale multiply the commanded speeds (1.0 = exact);
    angular_bias [rad/s] is added to the commanded yaw rate; noise_sigma adds
    Gaussian noise to each integration step (m/s and rad/s).
    """

    def __init__(self, *, linear_scale=1.0, angular_scale=1.0, angular_bias=0.0,
                 noise_sigma=0.0, seed=0):
        self.linear_scale = linear_scale
        self.angular_scale = angular_scale
        self.angular_bias = angular_bias
        self.noise_sigma = noise_sigma
        self.rng = np.random.default_rng(seed)
        self.x = self.y = self.yaw = 0.0
        self.v = self.w = 0.0

    def integrate(self, v_cmd, w_cmd, dt):
        v = v_cmd * self.linear_scale
        w = w_cmd * self.angular_scale + (self.angular_bias if (v_cmd or w_cmd) else 0.0)
        if self.noise_sigma and (v_cmd or w_cmd):
            v += self.rng.normal(0, self.noise_sigma)
            w += self.rng.normal(0, self.noise_sigma)
        mid = self.yaw + w * dt / 2
        self.x += v * math.cos(mid) * dt
        self.y += v * math.sin(mid) * dt
        self.yaw = math.atan2(math.sin(self.yaw + w * dt), math.cos(self.yaw + w * dt))
        self.v, self.w = v, w


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--viewer", action="store_true", help="MuJoCoの画面も表示する")
    parser.add_argument("--headless", action="store_true", help="画面を表示しない（既定）")
    parser.add_argument("--twist", action="store_true", help="/cmd_vel を Twist 型で受ける（既定は TwistStamped）")
    parser.add_argument("--scene", choices=["room", "wall", "empty"], default="room",
                        help="障害物。room: 壁と箱（既定）、wall: 前方1.4 mの箱のみ、empty: なし")
    parser.add_argument("--start", nargs=3, type=float, default=[0.0, 0.0, 0.0], metavar=("X", "Y", "YAW_DEG"),
                        help="開始位置（world座標 m）と向き（度）")
    parser.add_argument("--scan-rate", type=float, default=5.0, help="LiDARの周期 [Hz]")
    parser.add_argument("--scan-noise", type=float, default=0.0, help="距離に加える雑音の標準偏差 [m]")
    parser.add_argument("--odom-linear-scale", type=float, default=1.0, help="オドメトリの並進の倍率（1.0で誤差なし）")
    parser.add_argument("--odom-angular-scale", type=float, default=1.0, help="オドメトリの旋回の倍率")
    parser.add_argument("--odom-angular-bias", type=float, default=0.0, help="オドメトリの旋回に加える一定のずれ [rad/s]")
    parser.add_argument("--odom-noise", type=float, default=0.0, help="オドメトリの積分に加える雑音の標準偏差")
    parser.add_argument("--cmd-timeout", type=float, default=0.5, help="指令が途切れたら停止するまでの秒数")
    parser.add_argument("--seconds", type=float, default=None, help="指定した秒数で終了（テスト用）")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import PoseStamped, TransformStamped, Twist, TwistStamped
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import LaserScan
    from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster

    obstacles = {"room": "room", "wall": True, "empty": False}[args.scene]
    sim = Go2Sim("kinematic", obstacles=obstacles)
    sim.set_planar_pose(args.start[0], args.start[1], math.radians(args.start[2]))
    odom_model = OdometryModel(linear_scale=args.odom_linear_scale, angular_scale=args.odom_angular_scale,
                               angular_bias=args.odom_angular_bias, noise_sigma=args.odom_noise)
    scan_angles = np.arange(SCAN_COUNT) * (2 * math.pi / SCAN_COUNT)
    rng = np.random.default_rng(1)

    rclpy.init()
    node = Node("sim_bridge")
    command = {"v": 0.0, "w": 0.0, "stamp": None}

    def on_twist(linear_x, angular_z):
        if not (math.isfinite(linear_x) and math.isfinite(angular_z)):
            node.get_logger().warn("cmd_vel に有限でない値があります。無視します。")
            return
        command["v"] = float(np.clip(linear_x, -MAX_LINEAR, MAX_LINEAR))
        command["w"] = float(np.clip(angular_z, -MAX_ANGULAR, MAX_ANGULAR))
        command["stamp"] = time.monotonic()

    if args.twist:
        node.create_subscription(Twist, "cmd_vel", lambda m: on_twist(m.linear.x, m.angular.z), 10)
    else:
        node.create_subscription(TwistStamped, "cmd_vel", lambda m: on_twist(m.twist.linear.x, m.twist.angular.z), 10)
    odom_pub = node.create_publisher(Odometry, "odom", 10)
    scan_pub = node.create_publisher(LaserScan, "scan", qos_profile_sensor_data)
    truth_pub = node.create_publisher(PoseStamped, "sim/ground_truth", 10)
    tf_pub = TransformBroadcaster(node)
    static_pub = StaticTransformBroadcaster(node)
    static = TransformStamped()
    static.header.stamp = node.get_clock().now().to_msg()
    static.header.frame_id, static.child_frame_id = "base_link", "base_scan"
    static.transform.translation.x, static.transform.translation.y, static.transform.translation.z = BASE_TO_SCAN
    static.transform.rotation.w = 1.0
    static_pub.sendTransform(static)

    handle = None
    if args.viewer and not args.headless:
        import mujoco.viewer
        try:
            handle = mujoco.viewer.launch_passive(sim.model, sim.data)
        except RuntimeError as error:
            raise RuntimeError("Viewer failed. On macOS start with scripts/launch.py and --viewer.") from error
        with handle.lock():
            handle.cam.distance, handle.cam.azimuth, handle.cam.elevation = 4.0, 135, -50
            handle.cam.lookat[:] = [1.0, 0.0, 0.0]

    state = {"scan_due": 0.0, "steps": 0}

    def publish_scan(now_msg):
        ranges = sim.get_ranges(scan_angles, max_distance=SCAN_RANGE[1])
        if args.scan_noise:
            ranges = ranges + rng.normal(0, args.scan_noise, ranges.shape)
        ranges = np.where(ranges < SCAN_RANGE[0], SCAN_RANGE[0], ranges)
        # base_scan is behind base_link by 32 mm; rays are cast from the base origin, which
        # is a simplification kept on purpose (see docs/architecture.md).
        msg = LaserScan()
        msg.header.stamp = now_msg
        msg.header.frame_id = "base_scan"
        msg.angle_min, msg.angle_max = 0.0, float(scan_angles[-1])
        msg.angle_increment = float(2 * math.pi / SCAN_COUNT)
        msg.time_increment = 0.0
        msg.scan_time = 1.0 / args.scan_rate
        msg.range_min, msg.range_max = SCAN_RANGE
        msg.ranges = [float(r) for r in ranges]
        scan_pub.publish(msg)

    def tick():
        now = time.monotonic()
        if command["stamp"] is not None and now - command["stamp"] > args.cmd_timeout:
            command["v"] = command["w"] = 0.0
            command["stamp"] = None
        v, w = command["v"], command["w"]
        with handle.lock() if handle else _NullContext():
            sim.set_velocity(vx=v, vy=0.0, yaw_rate=w)
            sim.step(STEP)
        odom_model.integrate(v, w, STEP)
        if handle:
            handle.sync()
        state["steps"] += 1
        now_msg = node.get_clock().now().to_msg()
        odom = Odometry()
        odom.header.stamp = now_msg
        odom.header.frame_id, odom.child_frame_id = "odom", "base_link"
        odom.pose.pose.position.x, odom.pose.pose.position.y = odom_model.x, odom_model.y
        qx, qy, qz, qw = quaternion_about_z(odom_model.yaw)
        odom.pose.pose.orientation.x, odom.pose.pose.orientation.y = qx, qy
        odom.pose.pose.orientation.z, odom.pose.pose.orientation.w = qz, qw
        odom.twist.twist.linear.x, odom.twist.twist.angular.z = odom_model.v, odom_model.w
        odom_pub.publish(odom)
        tf = TransformStamped()
        tf.header.stamp = now_msg
        tf.header.frame_id, tf.child_frame_id = "odom", "base_link"
        tf.transform.translation.x, tf.transform.translation.y = odom_model.x, odom_model.y
        tf.transform.rotation.x, tf.transform.rotation.y, tf.transform.rotation.z, tf.transform.rotation.w = qx, qy, qz, qw
        tf_pub.sendTransform(tf)
        pose = sim.get_pose()
        truth = PoseStamped()
        truth.header.stamp = now_msg
        truth.header.frame_id = "world"
        truth.pose.position.x, truth.pose.position.y = float(pose.position[0]), float(pose.position[1])
        tx, ty, tz, tw = quaternion_about_z(float(pose.rpy[2]))
        truth.pose.orientation.x, truth.pose.orientation.y, truth.pose.orientation.z, truth.pose.orientation.w = tx, ty, tz, tw
        truth_pub.publish(truth)
        if sim.time >= state["scan_due"]:
            publish_scan(now_msg)
            state["scan_due"] = sim.time + 1.0 / args.scan_rate

    node.create_timer(STEP, tick)
    node.get_logger().info(
        f"sim_bridge: scene={args.scene}, cmd_vel={'Twist' if args.twist else 'TwistStamped'}, "
        f"limits {MAX_LINEAR} m/s / {MAX_ANGULAR} rad/s, odom scale=({args.odom_linear_scale}, "
        f"{args.odom_angular_scale}) bias={args.odom_angular_bias} rad/s")
    start = time.monotonic()
    try:
        while rclpy.ok():
            if handle is not None and not handle.is_running():
                break
            if args.seconds is not None and time.monotonic() - start >= args.seconds:
                break
            rclpy.spin_once(node, timeout_sec=0.05)
    except KeyboardInterrupt:
        pass
    finally:
        sim.stop()
        if handle:
            handle.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


class _NullContext:
    def __enter__(self):
        return None

    def __exit__(self, *exc):
        return False


if __name__ == "__main__":
    sys.exit(main())
