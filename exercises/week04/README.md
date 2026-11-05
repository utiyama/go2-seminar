# 第4回　反応型制御と状態遷移

2026年11月6日

教科書：11.1–11.3（抜粋版 42–50ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md) ／ [ROS 2環境](../../docs/setup-ros.md)

LiDARで測った前方の距離を使って、前進と停止を切り替えるノードを動かします。コードの穴埋めで状態を1つ追加し、障害物の前で向きを変えてから進む動作を作ります。実機が届いていれば、同じノードで実機も走らせます。

## 準備

第3回と同じく、`pixi shell` に入ったターミナルを3つ使います。

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

編集するのは `exercises/week04/fsm.py` の `class Controller` だけです。中に3つの関数があります。

| 関数 | 呼ばれる頻度 | 役割 |
|---|---|---|
| `update(t, front, left, right)` | 0.1秒ごと | 距離を見て、状態を切り替えるかどうか決める。**今回の穴埋めはここ** |
| `command()` | 0.1秒ごと | いまの状態に応じた（前進速度, 旋回速度）を返す。`TURN` のときは `(0, turn_rate)` を返すように書いてある |
| `transition(new_state, t)` | 状態が変わるとき | `self.state` を書き換え、入った時刻を `self.state_since` に記録する |

`update()` に渡される値は次のとおりです。

| 名前 | 意味 |
|---|---|
| `t` | 開始からの秒数 |
| `front` | 前方±15度で最も近い物までの距離 [m]。何もなければ `inf` |
| `left`、`right` | 左（90度）と右（270度）の同じ値 |

距離は第3回の `sector_min()` で計算しています。`inf` は「3.5 m以内に何もない」という意味で、`front < 0.5` のような比較は常に偽になります。

## 実習1　まず動かす

```text
python exercises/week04/fsm.py
```

最初のコードは `FORWARD` から `STOP` への切り替えだけを行い、前方0.5 m以内で停止します。ターミナルに `FORWARD → STOP` と時刻・距離が出ます。`Ctrl+C` で終了すると、`results/week04-fsm.csv` と `results/week04-fsm.png`（前方距離の変化と、オドメトリの軌跡）が保存されます。

停止距離は0.5 mなのに、表示された距離は0.5 mより少し小さいはずです。次の2つで比べてください。

```text
python exercises/week04/fsm.py --speed 0.05
python exercises/week04/fsm.py --speed 0.22
```

scanは0.2秒に1回しか届きません。速いほど、検出してから止まるまでに進む距離が増えます。

## 実習2　TURN 状態を追加する（穴埋め1・2）

`fsm.py` の `update()` の中に `# --- 穴埋め1` と `# --- 穴埋め2` があります。どちらも、行頭の `# ` を消して有効にし、`???` を埋めます。

穴埋め1は「`STOP` になったら `TURN` に移る」です。

```python
        elif self.state == "STOP":
            self.transition("TURN", t)
```

`self.transition("TURN", t)` は、状態を `TURN` にして、入った時刻 `t` を `self.state_since` に記録します。

穴埋め2は「`TURN` に入ってから `turn_seconds` 秒たったら `FORWARD` に戻る」です。`t - self.state_since` が、いまの状態に入ってからの秒数です。

```python
        elif self.state == "TURN" and t - self.state_since >= self.turn_seconds:
            self.transition("FORWARD", t)
```

保存して実行すると、`FORWARD → STOP → TURN → FORWARD` と繰り返し、箱の前で止まって左に90度回り、また進みます。

```text
t=  4.5 s  FORWARD → STOP  前方 0.47 m
t=  4.6 s  STOP → TURN  前方 0.47 m
t=  6.6 s  TURN → FORWARD  前方 1.45 m
```

`elif` の順番にも注意してください。`update()` は0.1秒ごとに呼ばれ、1回の呼び出しで状態は1段階しか進みません。

## 実習3　旋回角度を変える

旋回角度は `--turn-rate`（rad/s）×`--turn-seconds`（秒）です。既定は π/4 × 2 秒 = 90度です。

```text
python exercises/week04/fsm.py --turn-seconds 1
python exercises/week04/fsm.py --turn-seconds 4
```

1秒なら45度、4秒なら180度です。実行前に、ロボットがどこで止まり、その後どこへ向かうかを予想してください。RViz2の軌跡と `results/week04-fsm.png` の右側の図で比べます。保存名を変えて残すには `--output results/week04-turn1` のように指定します。

## 実習4　空いている側へ回る（穴埋め3）

いまは必ず左に回ります。`transition()` の中の `# --- 穴埋め3` を有効にし、`???` に「左のほうが右より広い」という条件を書きます。

```python
        if new_state == "TURN":
            self.turn_rate = abs(self.turn_rate) if self.left >= self.right else -abs(self.turn_rate)
```

`self.left` と `self.right` は `update()` の最初の行で保存している左右の最小距離です。`abs()` は絶対値なので、`turn_rate` の符号だけを左右で切り替えています。正が左旋回、負が右旋回です。

部屋の右寄り（`--start 0 -1 0`）や左寄り（`--start 0 1 0`）から出発させると、回る向きが変わることを確かめます。これは橋渡しノード側の指定です。

```text
python scripts/launch.py -m go2_seminar.ros.sim_bridge --viewer --start 0 -1 0
```

## 発展　壁に沿って走る

`command()` の `FORWARD` の行を、左の壁までの距離を0.5 mに保つ旋回速度に変えます。

```python
        if self.state == "FORWARD":
            error = self.left - 0.5          # 正なら壁から遠い、負なら近い
            w = max(-0.5, min(0.5, 1.0 * error))
            return self.speed, w
```

`error` に掛ける係数（1.0）を大きくすると、壁に近づく・離れるを繰り返して蛇行します。左に壁がないとき（`self.left` が `inf`）にどうなるかも確かめてください。

## 実機では

実機の `/scan` には欠測や外れ値があり、1回の値で状態を切り替えると `FORWARD` と `STOP` を往復することがあります。「連続して3回しきい値を下回ったら遷移する」ように `update()` に回数を数える変数を足すか、第3回の平均化を使います。

ROS環境が使えない場合は、MuJoCoだけで同じ内容を試す `starter.py` もあります。

```text
python scripts/launch.py exercises/week04/starter.py
```
