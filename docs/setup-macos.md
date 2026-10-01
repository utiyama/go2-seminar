# macOSのセットアップ

[教材トップ](../README.md) ／ [Windowsの手順](setup-windows.md)

Apple SiliconとIntelのMacに対応しています。ターミナルを使って作業します。

## 1. Pythonの確認

ターミナルを開き、次を実行します。

```bash
python3.11 --version
```

`Python 3.11.x` と表示されれば、そのまま次に進めます。見つからない場合は [Python 3.11.9公式ダウンロードページ](https://www.python.org/downloads/release/python-3119/) の
`macOS 64-bit universal2 installer` を使います。完了後にターミナルを開き直してください。
3.11系であれば、3.11.9以外でも使えます。

画面表示にはApple Command Line Toolsも使います。まだ入っていない場合は、次を実行してインストールしてください。

```bash
xcode-select --install
```

インストール済みと表示された場合、再インストールは不要です。ただし、Gitが `Failed to locate 'git'` などのエラーで動かない場合は、Command Line ToolsではなくXcode側を参照していることがあります。[参照先を切り替える手順](troubleshooting.md#macでgitが見つからない場合)を試してください。

## 2. 教材のフォルダへ移動する

[教材トップ](../README.md)の案内から教材を取得し、ZIPの場合は展開します。
Finderで `README.md` があるフォルダを確認します。
ターミナルに `cd `（最後に半角スペース）と入力し、そのフォルダをターミナルへドラッグしてEnterを押してください。

```bash
ls scripts/install.sh
```

`scripts/install.sh` が表示されれば正しい場所です。
見つからない場合は、`scripts` が見えるフォルダへ移動してください。

## 3. インストール

```bash
bash scripts/install.sh
```

必要なソフトとGo2モデルをダウンロードするので、初回は少し時間がかかります。
最後に `"status": "PASS"` と「セットアップ完了」が出たら、インストールは完了です。
環境の確認結果は `results/environment.json` に保存されます。Pythonの仮想環境は教材フォルダ内の `.venv` に作られ、以後のコマンドから自動で使われます。

## 4. Go2の表示

```bash
bash scripts/run.sh examples/00_view.py
```

Go2が表示されたら、マウスで視点を変えてみてください。
60秒経つと終了します。先にウィンドウを閉じても構いません。
`PASS` は計算に必要な環境の確認結果です。画面が表示されることも確かめてください。

Macでは画面表示に `mjpython` が必要ですが、`scripts/run.sh` が自動で切り替えます。サンプルは上記の方法で起動してください。

## 5. 操作と記録

前のコマンドが終了してから、次を1行ずつ実行します。

```bash
bash scripts/run.sh examples/01_pose.py
bash scripts/run.sh examples/02_joint_motion.py --viewer
bash scripts/run.sh examples/03_planar_motion.py --viewer
bash scripts/run.sh examples/04_log_state.py
bash scripts/run.sh examples/05_plot_trajectory.py
```

`results/trajectory.png` を開き、軌跡の図を確認します。
各サンプルで確認することは[初回の確認項目](day0.md)にまとめています。エラーが出た場合は[トラブル対処](troubleshooting.md)を参照してください。
