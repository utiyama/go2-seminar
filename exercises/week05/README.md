# 第5回　地図の作成

2026年11月13日

教科書：12.1–12.4、17.1（任意）（抜粋版 51–63ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md) ／ [ROS 2環境](../../docs/setup-ros.md)

LiDARで測った点を格子に積み重ねて、占有格子地図（occupancy grid）を作ります。コードの穴埋めで「座標をセル番号にする」「ロボット座標をodom座標に変換する」の2か所を完成させ、ロボットを動かして地図を広げます。最後に、オドメトリがずれると地図がどうなるかを調べます。

## 準備

`pixi shell` に入ったターミナルを4つ使います。

ターミナル1（シミュレータ）:

```text
python scripts/launch.py -m go2_seminar.ros.sim_bridge --viewer
```

ターミナル2（RViz2）:

```text
rviz2 -d exercises/ros/seminar.rviz
```

ターミナル3（キーボード操作。第3回と同じ）:

```text
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

`i` で前進、`j` と `l` で旋回、`k` で停止です。キーはこのターミナルを選んだ状態で押します。

ターミナル4で、以下のノードを実行します。

## コードの構成

編集するのは `exercises/week05/mapping.py` の `to_cells()` と `to_odom()` です。scanを1回受け取るたびに、次の順で処理しています（`main()` の中の `on_scan()`）。

| 順 | 関数 | 役割 |
|---|---|---|
| 1 | `read_scan(scan)` | 物に当たった光線の距離 `r` と角度 `a` を取り出す |
| 2 | `polar_to_xy(r, a)` | ロボット座標の点にする。`x = r cos(a)`（前）、`y = r sin(a)`（左） |
| 3 | `to_odom(local, pose)` | ロボット座標の点をodom座標に変換する。**穴埋め2** |
| 4 | `to_cells(points, resolution)` | 座標 [m] を格子のセル番号にする。**穴埋め1** |
| 5 | `grid.add(grid.hits, col, row)` | そのセルの「当たった回数」を1増やす |

光線が物に当たるまでに通り抜けた点（`ray_points()`）にも同じ3〜5を行い、「通り抜けた回数」`grid.passes` を増やします。

地図は、各セルを次の3つに分けたものです（`Grid.occupancy()`）。

| 値 | 意味 | 条件 | 図・RViz2での色 |
|---|---|---|---|
| 100 | 占有（物がある） | 当たった回数が2回以上（`--min-hits`） | 黒 |
| 0 | 空き | 光線が通り抜けた | 白（RViz2では明るい灰色） |
| -1 | 未観測 | どちらでもない | 灰色 |

地図の範囲はxが−3〜5 m、yが−3〜3 mで、セルの一辺は0.05 m（`--resolution`）です。

## 実習1　まず動かす

```text
python exercises/week05/mapping.py
```

数秒たったら `Ctrl+C` で終了します。`results/week05-map.png` が保存されます。

```text
scan 28 回  占有セル 0 個  空きセル 0 個  保存先: results/week05-map.png
```

図の左は、最後のscanをロボット座標で描いたものです（緑の三角がロボット、右が前）。右の地図は、まだ全体が灰色（未観測）です。点をどのセルに入れるかを決めていないからです。

## 実習2　座標をセル番号にする（穴埋め1）

`to_cells()` の中の `# --- 穴埋め1` の下にある3行の、行頭の `# ` を消して有効にし、`???` を埋めます。

```python
    col = np.floor((x - X_MIN) / resolution).astype(int)
    row = np.floor((y - Y_MIN) / resolution).astype(int)
    return col, row
```

セル番号は「地図の端からの距離 ÷ セルの一辺」の整数部分です。`X_MIN`、`Y_MIN` は地図の左下の角（−3, −3）、`resolution` はセルの一辺 [m] です。`np.floor()` は小数点以下の切り捨て、`.astype(int)` は整数への変換です。

例えば、点 (1.42, 0.01) は、col = (1.42 + 3) ÷ 0.05 = 88.4 → 88、row = (0.01 + 3) ÷ 0.05 = 60.2 → 60 のセルに入ります。

ロボットを出発点に戻してから実行します。

```text
ros2 topic pub --once /sim/reset std_msgs/msg/Empty "{}"
python exercises/week05/mapping.py
```

```text
scan 30 回  占有セル 274 個  空きセル 2984 個  保存先: results/week05-map.png
```

右の図に、壁（黒）と空き（白）が出ます。箱の後ろなど、光線が届かない場所は灰色のままです。RViz2にも同じ地図が表示され、scanの点と重なります。

## 実習3　動かして地図を広げる（穴埋め2）

まず、穴埋め2をしないまま `mapping.py` を実行し、ターミナル3でロボットを動かしてください。地図が崩れます。RViz2では、scanの点（正しい位置）と地図がずれていきます。

いまの `to_odom()` は点を変換せずに返しているので、ロボットがどこにいても「出発点から前を向いて測った」ものとして地図に入れています。

`to_odom()` の中の `# --- 穴埋め2` の下の行を有効にし、`???` を埋めます。

```python
    return body_to_world(local, [x, y], yaw)
```

`body_to_world(点, [x, y], yaw)` は第2回で使った変換で、ロボットから見た点を、ロボットの位置 `[x, y]` と向き `yaw` を使って外の座標に移します。`x, y, yaw` は `/odom` から受け取ったロボットの位置と向きで、1行上の `x, y, yaw = pose` で取り出してあります。変換先は、出発点を原点とするodom座標です。

もう一度実行し、部屋を一回りしてから `Ctrl+C` で終了します。

```text
ros2 topic pub --once /sim/reset std_msgs/msg/Empty "{}"
python exercises/week05/mapping.py
```

壁の位置が動かなくなり、ロボットが進むにつれて灰色だった場所が埋まっていきます。図の青い線は、地図作成に使ったロボットの軌跡です。第4回の `fsm.py` を完成させた人は、キーボードの代わりに `python exercises/week04/fsm.py` で走らせても構いません。

## 実習4　オドメトリがずれると

ここまでは、シミュレータの `/odom` に誤差がありませんでした。実機では、車輪のすべりや寸法の誤差で `/odom` が少しずつずれます。ターミナル1を `Ctrl+C` で止め、旋回の角度を5%多めに見積もる設定で起動し直します。

```text
python scripts/launch.py -m go2_seminar.ros.sim_bridge --viewer --odom-angular-scale 1.05
```

実習3と同じように部屋を一回りして地図を作り、名前を付けて保存します。

```text
python exercises/week05/mapping.py --output results/week05-odom-error
```

同じ誤差のまま、`/odom` の代わりにシミュレータ上の本当の位置を使うと、どう変わるかも確かめます。

```text
python exercises/week05/mapping.py --truth --output results/week05-truth
```

2つの図を比べてください。

- 壁はどう見えますか。ずれは、直進しているときと旋回したときのどちらで増えますか。
- その場で何回も旋回した場合と、ほとんど旋回しなかった場合で、違いはありますか。
- 実機には `--truth` に当たるものがありません。ずれを直すには、何の情報が使えそうですか。

`--truth` のとき、RViz2のロボットの表示は `/odom` の位置のままなので、地図とは合いません。

## 実習5　セルの大きさと雑音

ターミナル1を、距離に雑音（標準偏差0.03 m）を加える設定で起動し直します。

```text
python scripts/launch.py -m go2_seminar.ros.sim_bridge --viewer --scan-noise 0.03
```

セルの一辺と、占有とみなす回数を変えて比べます。実行前に、壁の太さや抜けがどう変わるか予想してください。

```text
python exercises/week05/mapping.py --resolution 0.02 --output results/week05-fine
python exercises/week05/mapping.py --resolution 0.2 --output results/week05-coarse
python exercises/week05/mapping.py --min-hits 1 --output results/week05-hits1
python exercises/week05/mapping.py --min-hits 10 --output results/week05-hits10
```

セルを小さくすると、1つのセルに当たる回数はどうなりますか。大きくすると、幅0.3 mの箱や、壁と箱のすき間はどう表されますか。

## 実機では

実機でも、同じ `mapping.py` を `/scan` と `/odom` につないで動かせます。違いは次の点です。

- `/odom` は必ずずれるので、長く走るほど実習4のような地図になります。scan同士を重ねて位置を直す方法（SLAM、教科書17.1）が必要になります。
- LiDARは1回転に0.2秒かかります。旋回中は、1回のscanの中で向きが変わるので、点がゆがみます。地図を作るときはゆっくり動かします。
- 地図の範囲（`X_MIN`、`Y_MIN`、`WIDTH_M`、`HEIGHT_M`）は、部屋に合わせて `mapping.py` の先頭で変えます。

ROS環境が使えない場合は、2か所から測った点を重ねる `starter.py` で、穴埋め2と同じ変換を試せます。

```text
python scripts/launch.py exercises/week05/starter.py
```
