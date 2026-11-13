# 第7回　自己位置推定とセンサ融合

2026年11月27日

教科書：15.1、15.3、16.1–16.2（抜粋版 76–88ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md) ／ [ROS 2環境](../../docs/setup-ros.md)

オドメトリは移動量を積み重ねるので、誤差も積み重なります。まず正方形を一周して、そのずれを測ります。次に、壁に向かって直進しながら、オドメトリとLiDARの2つから進んだ距離を推定します。コードの穴埋めで「LiDARによる観測」「予測の補正」を完成させ、発展で「ゲインの決め方」を扱います。

## 準備

`pixi shell` に入ったターミナルを3つ使います。

ターミナル1（シミュレータ）。実機に近づけるため、オドメトリとLiDARに誤差を入れて起動します。

```text
python scripts/launch.py -m go2_seminar.ros.sim_bridge --viewer --odom-linear-scale 1.1 --odom-angular-scale 1.05 --scan-noise 0.03
```

| オプション | 意味 |
|---|---|
| `--odom-linear-scale 1.1` | `/odom` が、進んだ距離を10%多めに見積もる |
| `--odom-angular-scale 1.05` | `/odom` が、回った角度を5%多めに見積もる |
| `--scan-noise 0.03` | `/scan` の距離に、標準偏差0.03 mの雑音が加わる |

ターミナル2（RViz2）:

```text
rviz2 -d exercises/ros/seminar.rviz
```

ターミナル3で、以下のノードを実行します。数値は雑音のため、実行のたびに少し変わります。

## 実習1　正方形を一周する

`square.py` は、`/odom` の位置と向きだけを見て、一辺0.8 mの正方形を右回りに一周します。穴埋めはありません。

```text
python exercises/week07/square.py --reset
```

```text
シミュレータを出発点に戻しました。
開始: 一辺 0.8 m の正方形を右回りに一周します。
角 1 に到着（odom 0.77, 0.00）
角 2 に到着（odom 0.80, -0.78）
角 3 に到着（odom 0.02, -0.80）
角 4 に到着（odom 0.00, -0.02）
オドメトリでは  出発点まで 0.02 m、向きの差 1 度
実際の位置では  出発点まで 0.17 m、向きの差 18 度
保存先: results/week07-square.png
```

`/odom` の上では出発点に戻っていますが、実際には戻れていません。`results/week07-square.png` には、`/odom` の軌跡（オレンジ）と実際の軌跡（黒）が重ねて描かれます。

- 実際の軌跡の一辺は、何 m くらいですか。準備の表のどの設定と対応しますか。
- 向きの差は、角を曲がるたびにどう増えていきますか。一周で回った角度の合計から、18度を説明できますか。
- 一辺を `--side 0.4` にした場合と比べてください。出発点までの距離と向きの差は、それぞれどう変わりますか。

## コードの構成

ここからは `exercises/week07/localize.py` を使います。ロボットは正面の箱（壁）に向かって直進し、壁まで0.4 mで止まります。その間、出発点から進んだ距離を3通りに求めます。

| 求め方 | 図の色 | 性質 |
|---|---|---|
| オドメトリ | オレンジ | `/odom` の位置から求める。なめらかだが、進むほどずれる |
| LiDAR | 緑の点 | 壁までの距離から求める。ずれは増えないが、毎回ばらつく |
| 推定 | 青 | オドメトリで進め、LiDARで少しずつ直す |

編集するのは `measure()`、`correct()`、`kalman_gain()` です。scanを1回受け取るたびに、`Estimator.update()` が次の順で処理します。

| 順 | 行 | 役割 |
|---|---|---|
| 1 予測 | `predicted = self.estimate + moved` | 前回の推定値を、オドメトリが進んだ分 `moved` だけ進める |
| 2 観測 | `measured = measure(wall, front)` | LiDARから、進んだ距離を求める。**穴埋め1** |
| 3 補正 | `self.estimate = correct(predicted, measured, gain)` | 予測を、観測に `gain` の割合だけ近づける。**穴埋め2** |

`gain` は `--gain` で指定します（初期値0.2）。`--kalman` を付けたときは `kalman_gain()` で決めます（**穴埋め3**、発展）。

## 実習2　LiDARで距離を求める（穴埋め1）

まず、そのまま実行します。

```text
python exercises/week07/localize.py --reset
```

```text
シミュレータを出発点に戻しました。
開始: 壁まで 1.39 m、速度 0.1 m/s、ゲイン 0.2
終了時の距離  オドメトリ 1.060 m  LiDAR --  推定 1.060 m  実際 0.964 m
誤差（RMSE）  オドメトリ 0.061 m  LiDAR --  推定 0.061 m
保存先: results/week07-localize.csv、results/week07-localize.png
```

LiDARをまだ使っていないので、推定はオドメトリと同じです。約1 m進む間に、0.1 mずれています。「実際」はシミュレータ上の本当の位置で、実機では表示されません。RMSEは、走行中の誤差の大きさをまとめた値です（誤差の2乗の平均の平方根）。

`measure()` の中の `# --- 穴埋め1` の下の1行を有効にし、`???` を埋めます。

```python
    return wall - front
```

`wall` は出発点で測った壁までの距離、`front` はいまの壁までの距離です。壁が近づいた分だけ、ロボットは進んでいます。例えば、出発点で1.40 m、いま1.00 mなら、0.40 m進んだことになります。

```text
python exercises/week07/localize.py --reset
```

```text
終了時の距離  オドメトリ 1.111 m  LiDAR 0.949 m  推定 1.111 m  実際 1.010 m
誤差（RMSE）  オドメトリ 0.064 m  LiDAR 0.034 m  推定 0.064 m
```

`results/week07-localize.png` の上の図が進んだ距離、下の図が実際との差です。

- オドメトリの誤差と、LiDARの誤差は、時間とともにどう変わりますか。
- もっと長い距離を走ると、それぞれの誤差はどうなりそうですか。

## 実習3　予測を観測で補正する（穴埋め2）

`correct()` の中の `# --- 穴埋め2` の下の1行を有効にし、`???` を埋めます。

```python
    return predicted + gain * (measured - predicted)
```

`predicted` はオドメトリによる予測、`measured` はLiDARによる観測です。2つの差に `gain` を掛けた分だけ、予測を観測に近づけます。例えば、予測が0.50 m、観測が0.40 m、`gain` が0.2なら、0.50 + 0.2 × (0.40 − 0.50) = 0.48 m になります。

```text
python exercises/week07/localize.py --reset
```

```text
終了時の距離  オドメトリ 1.135 m  LiDAR 1.040 m  推定 1.043 m  実際 1.032 m
誤差（RMSE）  オドメトリ 0.065 m  LiDAR 0.032 m  推定 0.018 m
```

推定の誤差が、オドメトリとLiDARのどちらよりも小さくなります。

ゲインを変えて比べます。実行前に、青い線がどうなるか予想してください。

```text
python exercises/week07/localize.py --reset --gain 0 --output results/week07-gain0
python exercises/week07/localize.py --reset --gain 1 --output results/week07-gain1
python exercises/week07/localize.py --reset --gain 0.05 --output results/week07-gain005
```

- `--gain 0` と `--gain 1` の推定は、それぞれ何と同じになりますか。式から説明してください。
- ゲインを小さくすると、青い線のなめらかさと、実際からのずれはどう変わりますか。
- 0.2 が良い値になるのは、どういう条件のときだと思いますか。LiDARの雑音がもっと大きい場合はどうですか。

## 発展　ゲインを不確かさから決める（穴埋め3）

ゲインを固定せず、「予測がどのくらい不確かか」と「観測がどのくらい不確かか」から決めます。1次元のカルマンフィルタです。

`kalman_gain()` の中の `# --- 穴埋め3` の下の1行を有効にし、`???` を埋めます。

```python
    return p / (p + r)
```

| 変数 | 意味 |
|---|---|
| `p` | 予測の分散 [m²]。出発点では0で、進むたびに増え（`self.p += self.q * abs(moved)`）、補正のたびに減る（`self.p = (1.0 - gain) * self.p`） |
| `r` | 観測の分散 [m²]。`--scan-sigma`（LiDARの誤差の標準偏差、初期値0.03 m）の2乗 |
| `self.q` | 1 m進むごとに `p` に加える量。`--odom-sigma`（1 m進んだときのオドメトリの誤差の標準偏差、初期値0.1 m）の2乗 |

予測が不確か（`p` が大きい）ならゲインは1に近づき、観測が不確か（`r` が大きい）ならゲインは0に近づきます。

```text
python exercises/week07/localize.py --reset --kalman
```

```text
終了時の距離  オドメトリ 1.038 m  LiDAR 0.937 m  推定 0.963 m  実際 0.944 m
誤差（RMSE）  オドメトリ 0.060 m  LiDAR 0.031 m  推定 0.017 m
走行中のゲイン  最初 0.20  最後 0.40
```

ゲインは `results/week07-localize.csv` の最後の列にも記録されます。

不確かさの設定を変えて比べます。

```text
python exercises/week07/localize.py --reset --kalman --scan-sigma 0.3 --output results/week07-scan03
python exercises/week07/localize.py --reset --kalman --odom-sigma 0.01 --output results/week07-odom001
```

- それぞれ、ゲインはどうなりましたか。推定は、オドメトリとLiDARのどちらに近づきましたか。
- `--odom-sigma 0.01` は「オドメトリは1 mで0.01 mしかずれない」という設定です。実際のずれと合っていますか。設定が実際と違うと、何が起こりますか。

## 実機では

実機でも、同じ `square.py` と `localize.py` を動かせます。`--reset` は何もしません。

- 本当の位置（`/sim/ground_truth`）がないので、「実際」とRMSEは表示されません。床にテープで出発点の印を付け、メジャーで測って比べます。
- `square.py` では、一周した後の出発点からの距離を測ります。右回りと左回り（`--left`）で、ずれる向きを比べます。
- `localize.py` では、ロボットを平らな壁に向けて、1.5 mほど離して置きます。止まった後に進んだ距離を測り、オドメトリ・LiDAR・推定のどれが近いかを確かめます。
- 壁に対して斜めに置くと、正面の距離の減り方が、進んだ距離と合わなくなります。

ROS環境が使えない場合は、同じ補正の式を人工データで試す `starter.py` があります。

```text
python scripts/launch.py exercises/week07/starter.py
```
