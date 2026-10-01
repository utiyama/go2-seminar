# APIと設計

`Go2Sim` でモデルと状態を管理し、`runtime.run` で一定時間の実行、画面表示、CSVへの保存を行います。画面を表示せずに計算だけ実行することもできます。発展課題でMuJoCoを直接操作できるように、`model` と `data` も公開しています。

## 座標系と単位

距離はm、時間はs、角度はradで表します。world座標系はz軸が上向きです。ロボットに固定したbody座標系は、x軸が前方、y軸が左、z軸が上を向きます。

- `Pose.position` は、胴体原点のworld座標です。
- `quaternion_wxyz` は、bodyからworldへの回転を表すクォータニオンです。
- `Pose.rpy` と `get_orientation()` は、ZYX Euler角のroll、pitch、yawを返します。特異姿勢の付近では値の解釈に注意してください。
- `set_velocity()` の並進速度はbody座標で与えます。正の `yaw_rate` は上から見て反時計回りです。
- `get_state()` が返す並進速度は胴体原点のworld座標での値、角速度はbody座標での値です。戻り値はJSONに変換できます。
- 関節の順序は `joint_names` で確認できます。FL/FR/RL/RRの各脚にhip/thigh/calfがあります。関節を指定するときは、配列の番号だけでなく名前も確認してください。

## 主な関数

| API | 動作 |
|---|---|
| `Go2Sim(mode='physics', obstacles=False, cache_dir=None)` | 固定した版のモデルを読み込みます。`obstacles=True` の場合はx=1.5に箱を追加します |
| `reset()` | home姿勢に戻し、時刻と速度を0にします |
| `get_pose()`, `get_state()`, `get_joint_positions()` | 状態のコピーを返します。戻り値を変更してもシミュレータの状態には影響しません |
| `stand()` | physicsモードで、homeの関節角をPD制御の目標にします。倒れた状態からの復帰には使えません |
| `set_joint_targets(12 angles)` | physicsモードの関節目標です。可動域外の値やNaNを渡すとエラーになります |
| `set_velocity(vx,vy,yaw_rate)` | kinematicモードの速度を指定します。並進速度は0.5 m/s以下、角速度は1.5 rad/s以下です |
| `set_planar_pose(x,y,yaw)` | kinematicモードで位置と向きを変え、速度を0にします |
| `step(duration=0.02)` | シミュレーションの時間を進めます。時間はMuJoCoのtimestepの正の整数倍で指定します |
| `stop()` | kinematicモードでは速度を直ちに0にします。physicsモードでは現在の関節角を保ちますが、胴体の慣性は残ります |
| `get_imu()` | physicsモードのIMUの値を返します。imu siteの局所座標で表したgyroとspecific forceで、ノイズは加えていません |
| `get_range()`, `get_ranges(angles,max_distance=5)` | yawを基準に水平なレイで距離を測ります。ロボット自身は除外し、範囲内に何もなければ `inf` を返します |

## センサ

IMUには、Menagerieモデルに追加したMuJoCoのgyroとaccelerometerを使っています。静止中でも、加速度計は通常約9.81 m/s²の値を示します。これは機体を支える力に対応するもので、`qacc` や重力を除いた並進加速度とは異なります。kinematicモードでは力学を計算していないため、`get_imu()` は使えません。

距離計測は、胴体原点から水平面内にレイを伸ばす簡単なモデルです。実機Go2のLiDARの位置や視野、点群の仕様は再現していません。計測対象はシーンのgeom group 0で、Go2本体のgroup 2/3は除外しています。障害物を追加する場合はgroup 0にしてください。

## 制御と時間

物理計算は、既定では2 ms刻みです。各刻みで `tau = 45*(target-q) - 3*qvel` を計算し、モデルのmotorが許容する範囲に収めます。モデルはposition actuatorではないので、home keyframeの `ctrl` を関節角の指令としてそのまま使うことはできません。

各 `step` の後に `mj_forward` を呼び、派生する状態やセンサの値を更新します。描画は20 msごとに行い、viewerのlockを取ってから状態を更新します。ウィンドウを閉じた場合や例外が起きた場合も、終了処理を行います。

計算が遅いPCでは、画面上の動きも実時間より遅くなります。CSVの時刻はシミュレーション内の時刻です。

`run(..., viewer=True, trail=True, keep_open=True)` で、床に軌跡を描き、動作終了後も画面を開いておけます。待機中はシミュレーションの時間を進めません。CSVは待機に入る前に保存します。軌跡と始点・終点は描画用の目印で、接触や距離計測には影響しません。

`visualization.plot_planar_motion(states, path)` は、上から見た軌跡と、位置・yawの時間変化を画像に保存します。yawは±πの境界でグラフが飛ばないよう、連続した角度に直して描きます。`examples/06_replay.py` では平面移動のCSVからx・y・yawを読み、記録の間を補間して再生します。高さや関節角、物理モードの接触動作は再生しません。

## 実習を組み合わせるには

week02の座標変換、week03のノイズ生成、week04の状態遷移を、それぞれ関数として取り出すと再利用しやすくなります。ノイズ生成ではseedも引数にしておくと、同じ条件で比較できます。

week05の観測点をweek06の地図に載せるには、座標系と解像度をそろえる必要があります。機体の大きさを考慮した衝突判定は、経路計画の側に追加してください。さらにweek07を組み合わせる場合は、推定した位置を経路計画に渡し、シミュレータの真の位置は評価に使います。

歩行を扱うには、別途、動作確認済みの歩行制御器が必要です。制御器を追加する際は、速度指令の受け渡しに加え、停止の動作、遅延、速度などの制限も確認してください。この教材には学習済みモデル、ROS、通信処理、実機用コマンドは含まれておらず、そのままUnitree実機を制御することはできません。
