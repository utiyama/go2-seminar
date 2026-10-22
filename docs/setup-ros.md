# ROS 2環境のセットアップ（第3回以降）

[教材トップ](../README.md) ／ [Windowsの手順](setup-windows.md) ／ [macOSの手順](setup-macos.md) ／ [トラブル対処](troubleshooting.md)

第3回（10/30）からは、ROS 2を使ってロボットを動かします。実機のTurtleBot3 Burgerが届くまでは、教材のシミュレータをROS 2から動かします。学生のPCには、初回に作った `.venv` とは別に、ROS 2用の環境を用意します。`.venv` はそのまま残してください。

## 授業前に済ませてください

インストールには数GBのダウンロードと時間がかかるので、授業前に自宅や学内で済ませてください。授業中に大学のWi-Fiで行うと、実習の時間がなくなります。

- 空き容量が5 GB以上あること。ダウンロードは数GB、展開後の大きさは約3.5 GBです。
- 所要時間は回線によって10〜30分です。途中で止まった場合は、同じコマンドをもう一度実行すると続きから進みます。
- Windowsでは、教材のフォルダは `C:\Users\名前\go2-seminar` のように短いパスに置いてください。深い場所にあると、ファイルのパスが長すぎて失敗することがあります。

## 1. インストール

教材の `README.md` があるフォルダで実行します。

macOS:

```bash
bash scripts/install-ros.sh
```

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-ros.ps1
```

このスクリプトは、パッケージ管理ツールのpixiをホームフォルダの `.pixi` に入れ、教材フォルダ内の `.pixi` にROS 2 Jazzy一式、RViz2、MuJoCoを入れます。最後に `"status": "PASS"` と「ROS環境の準備完了」が出れば完了です。確認結果は `results/ros-environment.json` に保存されます。

初めてpixiを入れた場合は、ターミナルまたはPowerShellを一度閉じて開き直してください。

## 2. 動作確認

教材のフォルダで次を実行し、ROS環境に入ります。プロンプトの先頭に `(go2-seminar-ros)` が付きます。

```text
pixi shell
```

続けて次を1行ずつ実行します。MacとWindowsで同じです。

```text
ros2 topic list
ros2 run turtlesim turtlesim_node
```

1つ目は `/parameter_events` と `/rosout` を表示します。2つ目は亀の描かれたウィンドウを開きます。表示されたら `Ctrl+C` で終了してください。

```text
rviz2
```

RViz2のウィンドウが開けば、画面表示の確認は完了です。ウィンドウを閉じ、`exit` でROS環境から抜けます。

## 3. 使い方

第3回以降のコマンドは、すべて `pixi shell` で入った環境の中で実行します。ターミナルを複数使うときは、それぞれで `pixi shell` を実行してください。

MuJoCoの画面を出すときは、これまでと同じ起動スクリプトを使います。ROS環境の中では、Macも次のコマンドで動きます。

```text
python scripts/launch.py exercises/week01/starter.py --viewer
```

この環境には、次の設定が自動で入ります。

| 設定 | 値 | 意味 |
|---|---|---|
| `RMW_IMPLEMENTATION` | `rmw_cyclonedds_cpp` | 通信にCyclone DDSを使います。既定のFast DDSはMacで止まることがあります |
| `ROS_DOMAIN_ID` | `30`（Windowsは実機接続時以外、PCごとの番号） | 同じ番号のPCどうしだけが通信します。ロボットは30です |
| `CYCLONEDDS_URI` | `scripts/cyclonedds.xml` など | 自分のPC内だけを相手に探索する設定です。隣の人のシミュレータとは混ざりません。Windowsは `cyclonedds-windows.xml` を使います |

## 実機に接続するとき

ロボットを動かす番になったら、PCのWi-Fiを大学のものから教員が用意したルータに切り替えます。このWi-Fiはロボットとの通信専用で、インターネットにはつながりません。`git pull` は切り替える前に済ませてください。続けて、教材のフォルダで次を実行します。

```text
pixi run robot on
```

次に `pixi shell` に入ったときから、ドメイン番号が30になり、ロボット（`turtlebot.local`）も探索の相手に含む設定（`scripts/cyclonedds-robot.xml`、Windowsは `cyclonedds-windows-robot.xml`）が使われます。すでに開いているターミナルには反映されないので、`exit` してから `pixi shell` に入り直してください。`ros2 topic hz /scan` でロボットの値が届けば接続できています。

終わったら次で戻し、Wi-Fiも大学のものに戻します。戻し忘れると、ロボットがいないときにノードの起動が数秒遅くなります。

```text
pixi run robot off
```

現在の設定は `pixi run robot status` で確認できます。ロボットに指令を送るPCは1台ずつです。

## 環境を作り直すとき

教材フォルダの `.pixi` を削除して、インストールをやり直します。`.venv` と `results/` には影響しません。
