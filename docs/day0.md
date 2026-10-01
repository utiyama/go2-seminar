# 10月2日：セットアップと動作確認

[教材トップ](../README.md) ／ [Windowsの手順](setup-windows.md) ／ [macOSの手順](setup-macos.md)

初回は、自分のPCでGo2を表示して動かします。OS別の手順に沿って進め、できた項目にチェックを入れてください。

## セットアップ

- [ ] Python 3.11が使える。
- [ ] 教材を展開し、`README.md`、`scripts`、`examples` があるフォルダを開いた。
- [ ] セットアップの最後に `"status": "PASS"` と表示された。
- [ ] `results/environment.json` が保存されている。
- [ ] 別途配布する教科書PDFの受け取り方が分かった。

## サンプルの実行

OS別の手順にあるコマンドを、上から順に実行してください。

| サンプル | 確認すること |
|---|---|
| `00_view.py` | Go2が立った画面が出る。マウスで視点を変えられる |
| `01_pose.py` | `position_m`、`quaternion_wxyz`、`rpy_rad` と12関節の値が表示される |
| `02_joint_motion.py --viewer` | 脚や胴体が小さく動く |
| `03_planar_motion.py --viewer` | 前進、横移動、旋回の後に停止する。最終値はおよそ x=0.4 m、y=0.15 m、yaw=1.0 rad |
| `04_log_state.py` | `results/state.csv` ができる |
| `05_plot_trajectory.py` | `results/trajectory.png` ができる。先に03を実行しておく |

- [ ] Go2が画面に表示され、視点を変えられることを確認した。
- [ ] 位置はm、角度はradで表示されることを確認した。
- [ ] `results/planar_motion.csv` と軌跡の画像を開いた。
- [ ] 物理モードと平面移動のモードの違いが分かった。

03の平面移動では、胴体の位置を直接動かしています。歩行を計算しているわけではありません。停止後に位置が変わらなくなることも、CSVで確かめてください。

## 授業の最後に

提出物はありません。どこまで動いたかをその場で確認し、分からなかったことを話し合います。

途中で止まった場合は、できたところまでとエラー画面を教員に見せてください。環境を調べる際には、OS、CPU、Pythonのバージョンと `results/environment.json` を使います。

## 画面が出ない場合

[トラブル対処](troubleshooting.md)を見ても解決しなければ、教員に相談してください。

画面表示を使わずに計算だけ試すには、`00_view.py --headless --seconds 2` を実行します。他のサンプルでは `--viewer` を外します。この方法で動いても、画面表示は別途確認が必要です。

## 次回の準備

[ゼミの進め方](student-guide.md)と[week01](../exercises/week01/README.md)を読んでおいてください。教科書の指定範囲に目を通し、気になった用語や疑問点を次回の授業で取り上げてください。
