"""占有格子地図を読み込む補助関数。rclpy は不要で、.venv でも読み込めます。

地図は第5回の mapping.py が保存する形式です。
    occupancy[row, col]  100: 占有、0: 空き、-1: 未観測（row が y 方向、col が x 方向）
    resolution           セルの一辺 [m]
    x_min, y_min         地図の左下の角の座標 [m]（odom座標）
"""
import math
from pathlib import Path

import numpy as np

# 第5回の mapping.py と同じ範囲
X_MIN, Y_MIN = -3.0, -3.0     # [m]
WIDTH_M, HEIGHT_M = 8.0, 6.0  # [m]


def room_boxes():
    """sim_bridge の部屋（--scene room）にある壁と箱。(中心 x, 中心 y, 半分の幅 x, 半分の幅 y) [m]。"""
    from go2_seminar.sim import ROOM_BOXES
    boxes = [(1.5, 0.0, 0.1, 0.6)]  # 前方の箱（Go2Sim の classroom_wall）
    boxes += [(pos[0], pos[1], size[0], size[1]) for _name, pos, size in ROOM_BOXES]
    return boxes


def room_map(resolution=0.05):
    """sim_bridge の部屋の、誤差のない地図を作る。部屋の外は未観測（-1）にする。

    ロボットが橋渡しノードの既定の開始位置（原点、x軸向き）から出発したときの odom 座標で表す。
    """
    cols, rows = round(WIDTH_M / resolution), round(HEIGHT_M / resolution)
    occupancy = np.full((rows, cols), -1, dtype=np.int8)

    def span(low, high, minimum, count):
        first = math.floor(round((low - minimum) / resolution, 6))
        last = math.ceil(round((high - minimum) / resolution, 6))
        return max(first, 0), min(last, count)

    boxes = room_boxes()
    x_low = min(x - hx for x, _y, hx, _hy in boxes)
    x_high = max(x + hx for x, _y, hx, _hy in boxes)
    y_low = min(y - hy for _x, y, _hx, hy in boxes)
    y_high = max(y + hy for _x, y, _hx, hy in boxes)
    c0, c1 = span(x_low, x_high, X_MIN, cols)
    r0, r1 = span(y_low, y_high, Y_MIN, rows)
    occupancy[r0:r1, c0:c1] = 0
    for x, y, hx, hy in boxes:
        c0, c1 = span(x - hx, x + hx, X_MIN, cols)
        r0, r1 = span(y - hy, y + hy, Y_MIN, rows)
        occupancy[r0:r1, c0:c1] = 100
    return {"occupancy": occupancy, "resolution": float(resolution), "x_min": X_MIN, "y_min": Y_MIN}


def load_map(path):
    """mapping.py が保存した .npz を読み込む。"""
    with np.load(Path(path)) as data:
        return {"occupancy": data["occupancy"].astype(np.int8), "resolution": float(data["resolution"]),
                "x_min": float(data["x_min"]), "y_min": float(data["y_min"])}
