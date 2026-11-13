# 第6回　経路計画：グリッド上の探索

2026年11月20日

教科書：13.1–13.3、13.5（抜粋版 64–75ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md) ／ [ROS 2環境](../../docs/setup-ros.md)

占有格子地図の上で、出発点からゴールまでの経路を探し、ロボットにその経路をたどらせます。コードの穴埋めで「A*の優先度」「障害物から離す余裕」「経路へ向かう操舵」の3か所を完成させます。

## 準備

`pixi shell` に入ったターミナルを3つ使います。

ターミナル1（シミュレータ）:

```text
python scripts/launch.py -m go2_seminar.ros.sim_bridge --viewer
```

ターミナル2（RViz2）:

```text
rviz2 -d exercises/ros/seminar.rviz
```

ターミナル3で、以下のノードを実行します。

## コードの構成

編集するのは `exercises/week06/planner.py` の `search()`、`inflate()`、`steer()` です。`main()` は次の順で処理しています。

| 順 | 関数 | 役割 |
|---|---|---|
| 1 | `room_map()` | 地図を読み込む。第5回の `mapping.py` が保存するものと同じ形式で、セルの一辺は0.05 m |
| 2 | `inflate(occupied, margin, resolution)` | 通れないセルを `margin` [m] だけ外側に広げる。**穴埋め2** |
| 3 | `search(blocked, start, goal, weight)` | 出発セルからゴールのセルまでの経路を探す。**穴埋め1** |
| 4 | `next_target(path_xy, position, index)` | 経路の上で、ロボットから0.3 m先の点を選ぶ |
| 5 | `steer(pose, target, speed)` | その点へ向かう前進速度と旋回速度を決める。**穴埋め3** |

4と5は `--follow` を付けたときだけ、0.1秒ごとに実行します。

地図は、シミュレータの部屋の壁と箱をそのまま格子にしたものです。ロボットは出発点 (0, 0) にいて、ゴールは正面の箱の向こう側 (2.5, 0) です。

`search()` は、セルを1つ取り出しては、その隣の8セルを調べることを繰り返します。使っている変数は次のとおりです。

| 変数 | 意味 |
|---|---|
| `cell`、`nxt` | いま調べているセルと、その隣のセル。`(列, 行)` の組 |
| `cost[cell]` | 出発点からそのセルまでのコスト。隣へ進むと、縦横は1、斜めは√2増える |
| `parent[cell]` | そのセルへ、どのセルから来たか。ゴールからたどると経路になる |
| `queue` | これから調べるセルの列。`priority`（優先度）が小さいものから取り出される |
| `done` | 調べ終わったセル。この個数が「調べたセル」として表示される |
| `heuristic(cell, goal)` | そのセルからゴールまでの直線距離（セル数） |

## 実習1　まず動かす

```text
python exercises/week06/planner.py
```

```text
地図: 教材の部屋（セル 0.05 m）  通れないセル 14840 個、うち余裕の分 0 個
出発 (0.00, 0.00) → ゴール (2.50, 0.00)
経路の長さ 3.00 m  調べたセル 3965 個
保存先: results/week06-plan.png
```

`results/week06-plan.png` を開いてください。赤い線が経路、水色が調べたセルです。RViz2には、同じ経路が緑の線で表示されます。

いまの `search()` は、出発点からのコスト `new_cost` だけを優先度にしています（ダイクストラ法）。出発点に近いセルから順に調べるので、ゴールと反対の方向も含めて、ほぼ部屋全体を調べています。

経路が箱の角をかすめていることも見ておいてください。これは実習3で直します。

## 実習2　A*にする（穴埋め1）

`search()` の中の `# --- 穴埋め1` の下にある1行の、行頭の `# ` を消して有効にし、`???` を埋めます。字下げは、上の `priority = new_cost` の行にそろえます。

```python
                priority = new_cost + weight * heuristic(nxt, goal)
```

優先度を「出発点からそのセルまでのコスト」と「そのセルからゴールまでの見積もり」の和にします。ゴールに近づくセルほど先に調べられます。`nxt` は隣のセル、`goal` はゴールのセル、`weight` は見積もりに掛ける重み（`--weight`、初期値1）です。

```text
python exercises/week06/planner.py
```

```text
経路の長さ 3.00 m  調べたセル 954 個
```

経路の長さは同じで、調べたセルは約4分の1になります。図の水色の範囲がどう変わったかを見てください。

重みを変えて比べます。実行前に、調べたセルの数と経路の長さがどうなるか予想してください。

```text
python exercises/week06/planner.py --weight 0 --output results/week06-w0
python exercises/week06/planner.py --weight 5 --output results/week06-w5
```

- `--weight 0` は、どの方法と同じですか。
- `--weight 5` では、経路の長さはどうなりましたか。調べるセルが少ないことと、経路が最短であることは両立していますか。

## 実習3　ロボットの大きさを考える（穴埋め2）

ここまでの経路は、ロボットを大きさのない点とみなしています。障害物のセルを外側に広げておけば、点として探した経路でも、障害物から離れて通れます。

`inflate()` の中の `# --- 穴埋め2` の下の1行を有効にし、`???` を埋めます。

```python
    cells = round(margin / resolution)
```

広げる距離 `margin` [m] を、セルの一辺 `resolution` [m] で割って、セルの数にします。`round()` は四捨五入です。`margin` は `--margin` で指定し、初期値は0.25 mです。その下の2重の `for` が、障害物の各セルから半径 `cells` の円の中を「通れない」にしています。

```text
python exercises/week06/planner.py
```

```text
地図: 教材の部屋（セル 0.05 m）  通れないセル 16778 個、うち余裕の分 1938 個
出発 (0.00, 0.00) → ゴール (2.50, 0.00)
経路の長さ 3.20 m  調べたセル 825 個
```

図では、広げた分が薄いオレンジ色になります（RViz2では濃い灰色）。経路が箱の角から離れ、その分だけ長くなります。

余裕を変えて比べます。

```text
python exercises/week06/planner.py --margin 0.1 --output results/week06-m10
python exercises/week06/planner.py --margin 0.4 --output results/week06-m40
```

- `--margin 0.4` では経路が見つかりません。図を見て、理由を説明してください。箱と壁のすき間は0.85 mです。
- TurtleBot3 Burgerは、中心から最も遠い部分まで約0.1 mです。余裕を0.1 mちょうどにすると、何が心配ですか。

## 実習4　経路をたどる（穴埋め3）

`--follow` を付けると、計画した経路に沿って `/cmd_vel` を出します。まず、穴埋めの前に実行してみます。

```text
python exercises/week06/planner.py --follow
```

```text
ロボットが動いていません。steer() の穴埋め3を確認してください。
```

`steer()` の中の `# --- 穴埋め3` の下の3行を有効にし、`???` を埋めます。

```python
    error = wrap_angle(direction - yaw)
    v = speed if abs(error) < 0.5 else 0.0  # 向きが大きくずれている間は、その場で回る
    return v, max(-1.0, min(1.0, 1.5 * error))
```

| 変数・関数 | 意味 |
|---|---|
| `direction` | ロボットから見た目標点の方向 [rad]。1行上で `atan2` を使って求めてある |
| `yaw` | `/odom` から受け取った、ロボットのいまの向き [rad] |
| `wrap_angle(角度)` | 角度を −π〜π に直す。差が350度のとき、−10度として扱える |
| `error` | 向きのずれ。正なら目標点は左、負なら右にある |
| `1.5 * error` | ずれに比例した旋回速度。`max`、`min` で ±1.0 rad/s に収める |

第4回の発展（壁に沿って走る）と同じく、ずれに比例して旋回します。目標点はロボットが進むたびに経路の先へ移るので、追いかけ続けるとゴールに着きます。

```text
python exercises/week06/planner.py --follow
```

```text
経路の長さ 3.20 m  調べたセル 825 個
到着しました。ゴールまで 0.07 m（odom）、実際の位置では 0.08 m  所要 20.1 s  障害物までの最小距離 0.20 m
```

図の青い破線が、実際に走った軌跡です。「実際の位置では」は、シミュレータ上の本当の位置で測ったゴールまでの距離です。

2回目からは、ロボットがいまいる位置から計画します。出発点に戻すときは `--reset` を付けます。ゴールは `--goal X Y` で変えられます。

```text
python exercises/week06/planner.py --follow --goal 2.6 -1.2
python exercises/week06/planner.py --follow --goal -0.5 1.0
python exercises/week06/planner.py --follow --reset
```

- 走った軌跡は、計画した経路と同じですか。違うのはどこですか。
- 余裕は0.25 mなのに、障害物までの最小距離がそれより小さくなるのはなぜですか。
- `planner.py` の先頭にある `LOOKAHEAD`（目標点までの距離、0.3 m）を0.1や0.8に変えると、軌跡はどう変わりますか。

ゴールをRViz2で指定することもできます。

```text
python exercises/week06/planner.py --follow --rviz
```

RViz2の上にある「2D Goal Pose」を押し、地図の上でゴールにしたい場所をクリックします（そのまま少しドラッグして離します）。走っている途中で別の場所を指定すると、そこから計画し直します。終了は `Ctrl+C` です。

## 発展　自分の地図で計画する

第5回で保存した地図（`results/week05-map.npz`）があれば、それを使って計画できます。

```text
python exercises/week06/planner.py --map results/week05-map.npz --follow --reset
```

地図で未観測（灰色）のセルは、通れないものとして扱います。地図を作るときに見えなかった場所へは、経路を引けません。

次に、ターミナル1を `Ctrl+C` で止め、第5回の実習4と同じ、旋回を5%多めに見積もる設定で起動し直します。

```text
python scripts/launch.py -m go2_seminar.ros.sim_bridge --viewer --odom-angular-scale 1.05
```

ゴールまで行き、出発点へ戻ります。

```text
python exercises/week06/planner.py --follow
python exercises/week06/planner.py --follow --goal 0 0
```

「ゴールまで（odom）」と「実際の位置では」を比べてください。ロボットは `/odom` の位置を信じて経路をたどるので、`/odom` がずれると、着いたつもりの場所と実際の場所が離れていきます。第7回では、このずれを別のセンサで直す方法を扱います。

## 実機では

実機でも、同じ `planner.py` を `/odom` と `/cmd_vel` につないで動かせます。違いは次の点です。

- 教材の部屋の地図は使えません。実際の部屋で `mapping.py` を動かして地図を作り、`--map` で渡します。出発点は、地図を作り始めた位置と向きに合わせます。
- 走っている間は、LiDARを見ていません。地図にない物や人は避けられないので、第4回の「前方が近ければ止まる」を組み合わせる必要があります。
- `/odom` は必ずずれるので、長い経路ほど、発展で見たようにゴールから外れます。

ROS環境が使えない場合は、小さな格子の上で幅優先探索を試す `starter.py` があります。

```text
python scripts/launch.py exercises/week06/starter.py
```
