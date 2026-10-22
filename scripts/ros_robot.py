"""実機（TurtleBot3）に接続する設定の切り替え: pixi run robot on / off / status

on のときは、次に pixi shell に入ったときから scripts/cyclonedds-robot.xml が使われ、
ロボット（turtlebot.local）を探索の相手に含めます。シミュレータだけのときは off にします。
"""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
FLAG = ROOT / ".ros_robot"


def main(argv):
    command = argv[0] if argv else "status"
    if command == "on":
        FLAG.write_text("on\n", encoding="utf-8")
        print("実機接続: on（ドメイン30、ロボットを探索の相手に含めます）")
    elif command == "off":
        FLAG.unlink(missing_ok=True)
        print("実機接続: off（自分のPC内だけを探索します）")
    elif command == "status":
        uri = os.environ.get("CYCLONEDDS_URI", "(未設定)").split("/")[-1]
        domain = os.environ.get("ROS_DOMAIN_ID", "(未設定)")
        print(f"保存されている設定: {'on' if FLAG.exists() else 'off'}  "
              f"このターミナル: ROS_DOMAIN_ID={domain}, 設定ファイル={uri}")
        return 0
    else:
        print("使い方: pixi run robot on | off | status", file=sys.stderr)
        return 1
    print("開いているターミナルで exit してから、もう一度 pixi shell に入ると反映されます。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
