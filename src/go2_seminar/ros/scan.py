"""LaserScan を扱う小さな補助関数。rclpy は不要で、.venv でも読み込めます。"""
import math

import numpy as np


def sector_min(scan, center_deg, half_deg):
    """center_deg を中心に ±half_deg の範囲で最小距離 [m] を返す。測定なしなら inf。

    LaserScan の ranges は angle_min から angle_increment 刻みで並び、
    TurtleBot3 では 0 度が前方、90 度が左（反時計回り）です。
    inf（遠すぎる）と range_min 未満（近すぎる・欠測）の値は除きます。
    """
    ranges = np.asarray(scan.ranges, dtype=float)
    angles = scan.angle_min + np.arange(len(ranges)) * scan.angle_increment
    offset = np.degrees(np.angle(np.exp(1j * (angles - math.radians(center_deg)))))  # -180..180
    selected = ranges[np.abs(offset) <= half_deg]
    selected = selected[np.isfinite(selected) & (selected >= scan.range_min)]
    return float(selected.min()) if selected.size else math.inf
