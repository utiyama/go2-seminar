# 第3回　センサとノイズ（ROS 2入門）

2026年10月30日

教科書：7.1–7.6（抜粋版 28–41ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md) ／ [ROS 2環境](../../docs/setup-ros.md)

この回からROS 2を使います。シミュレータをTurtleBot3 Burgerに見立てた橋渡しノードが、LiDARの距離 `/scan` とオドメトリ `/odom` を配信し、速度指令 `/cmd_vel` を受け取ります。実機が届いたら、同じコマンドとコードで実機を動かします。

前半でROS 2の基本操作を確かめ、後半でLiDARの値に雑音を加えて比べます。最後にMuJoCoの物理モードでIMUの雑音も扱います。

## 準備

[ROS 2環境のセットアップ](../../docs/setup-ros.md)を済ませておいてください。ターミナルを3つ開き、それぞれで教材のフォルダに移動して `pixi shell` を実行します。以下のコマンドはMacとWindowsで同じです。

ターミナル1（シミュレータ）:

```text
python scripts/launch.py -m go2_seminar.ros.sim_bridge --viewer
```

Go2が壁に囲まれた部屋の中に表示されます。部屋は4 m×3 mで、前方1.4 mに箱、ほかに2つの箱があります。`--viewer` を外すと画面なしで動きます。

ターミナル2（RViz2）:

```text
rviz2 -d exercises/ros/seminar.rviz
```

上から見た図が開きます。オレンジの点がLiDARで測った点、矢印がオドメトリの位置と向きです。`odom` 座標系を基準に描いています。

ターミナル3は、以下の操作に使います。

## ROS 2の基本操作

```text
ros2 node list
ros2 topic list
ros2 topic info /scan
ros2 topic hz /scan
ros2 topic echo /scan --once
```

`/scan` は `sensor_msgs/msg/LaserScan` で、1秒に5回届きます。`ranges` には360個の距離（m）が入り、`angle_min` から `angle_increment` ずつ反時計回りに並びます。先頭が前方、90番目が左、270番目が右です。3.5 mより遠い場合は `inf` です。

次に、キーボードで動かします。

```text
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

`i` で前進、`,` で後退、`j` と `l` でその場旋回、`k` で停止です。このノードが `/cmd_vel` に `TwistStamped` を配信し、橋渡しノードが受け取ります。速度の上限は実機と同じ0.22 m/sです。動かしながら、RViz2の点群と `ros2 topic echo /odom` の位置を見てください。キーを押すのをやめて0.5秒たつと止まります。

## 実習1　前方の距離を読む

ターミナル3で実行します。

```text
python exercises/week03/scan_front.py
```

1秒ごとに、前方±15度の範囲で最も近い距離を表示します。`Ctrl+C` で終了すると、`results/week03-scan.csv` と `results/week03-scan.png` に時間変化を保存します。

1. 別のターミナルでキーボード操作を動かし、箱に向かって前進しながら距離の減り方を見てください。箱の手前で止めます。
2. `sector_min()` を使って、左（90度）と右（270度）の最小距離も表示するようにしてください。
3. `--half-angle` を5度、45度に変え、箱の近くで最小距離がどう変わるか比べてください。扇形が広いほど、何を拾いやすくなるでしょうか。

## 実習2　雑音を加える

```text
python exercises/week03/scan_noise.py --sigma 0.05
```

`/scan` の各距離に標準偏差0.05 mの正規分布の雑音を加え、`/scan_noisy` として配信します。RViz2で `LaserScan` の表示をもう1つ追加し、Topicを `/scan_noisy` にすると2つを重ねて見られます。

1. `scan_front.py --topic /scan_noisy --output results/week03-scan-noisy` で前方の最小距離を記録し、雑音なしの結果と比べてください。雑音を加えると最小距離はどちらにずれるでしょうか。最小値を取る操作に注目します。
2. `--sigma` を0.02、0.1に変えて比べてください。
3. `smooth()` を、直近N回の平均を返すように書き換えてください。`--average 5` で動かし、静止時と移動時の結果を比べます。雑音が減る代わりに何が起きるでしょうか。

## 実習3　IMUの雑音

MuJoCoの物理モードでGo2のジャイロの値を読み、雑音を加えた場合と比べます。ROS環境のままでも、これまでの `.venv` でも実行できます。

```text
python scripts/launch.py exercises/week03/starter.py
```

`results/week03.csv` と `results/week03.png` に、理想的なセンサ値とノイズを加えた値が保存されます。

1. ノイズの標準偏差 `sigma` を0、0.05、0.2 rad/sに変え、平均とばらつきを比べてください。乱数のseedは同じ値にしておきます。
2. 静止しているときにも加速度計が0にならない理由を、教科書の説明と照らし合わせて考えてください。

## 実機との違い

橋渡しノードの距離は、胴体の中心から水平に伸ばしたレイで求めた正確な値です。実機のLDS-02は回転するレーザ距離計で、黒い物や透明な物、斜めの面では値が欠けたり、ばらついたりします。実機が届いたら、同じ `scan_front.py` で静止時のばらつきを測って比べます。
