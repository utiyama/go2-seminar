"""ROS_DOMAIN_ID を教材フォルダの .ros_domain_id に保存します: pixi run domain 31"""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / ".ros_domain_id"


def main(argv):
    current = os.environ.get("ROS_DOMAIN_ID", "(未設定)")
    if len(argv) != 1:
        saved = FILE.read_text(encoding="utf-8").strip() if FILE.exists() else "(なし)"
        print(f"現在のROS_DOMAIN_ID: {current}  保存されている値: {saved}")
        print("変更するには番号を指定します。例: pixi run domain 31")
        return 0
    try:
        value = int(argv[0])
        if not 0 <= value <= 232:
            raise ValueError
    except ValueError:
        print("0〜232の整数を指定してください。授業では各自の番号（31〜34）、実機操作時は30です。", file=sys.stderr)
        return 1
    FILE.write_text(f"{value}\n", encoding="utf-8")
    print(f"ROS_DOMAIN_ID={value} を {FILE.name} に保存しました。")
    print("開いているターミナルで exit してから、もう一度 pixi shell に入ると反映されます。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
