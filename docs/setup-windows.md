# Windowsのセットアップ

[教材トップ](../README.md) ／ [macOSの手順](setup-macos.md)

Windows x86-64のPCで、PowerShellを使って作業します。

## 1. Pythonの確認

PowerShellを開き、次を実行します。

```powershell
py -3.11 --version
```

`Python 3.11.x` と表示されれば、そのまま次に進めます。見つからない場合は [Python 3.11.9公式ダウンロードページ](https://www.python.org/downloads/release/python-3119/) の
`Windows installer (64-bit)` を使います。インストーラの `Add python.exe to PATH` とPython Launcherを有効にし、
完了後にPowerShellを開き直してください。3.11系であれば、3.11.9以外でも使えます。

Python 3.12以降だけが入っている場合も、この教材用に3.11を追加してください。

## 2. 教材のフォルダを開く

[教材トップ](../README.md)の案内から教材を取得し、ZIPの場合は必ず展開します。
エクスプローラーで `README.md` があるフォルダを開き、アドレスバーに `powershell` と入力してEnterを押します。

```powershell
Test-Path .\scripts\install.ps1
```

`True` と表示されれば正しい場所です。`False` の場合は、`scripts` が見えるフォルダへ移動してください。

## 3. インストール

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

必要なソフトとGo2モデルをダウンロードするので、初回は少し時間がかかります。
最後に `"status": "PASS"` と `Setup complete` が出たら、インストールは完了です。
環境の確認結果は `results/environment.json` に保存されます。Pythonの仮想環境は教材フォルダ内の `.venv` に作られ、以後のコマンドから自動で使われます。
`ExecutionPolicy Bypass`はこの起動プロセスにだけ適用され、永続設定を変更しません。

## 4. Go2の表示

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 examples/00_view.py
```

Go2が表示されたら、マウスで視点を変えてみてください。
60秒経つと終了します。先にウィンドウを閉じても構いません。
`PASS` は計算に必要な環境の確認結果です。画面が表示されることも確かめてください。

## 5. 操作と記録

前のコマンドが終了してから、次を1行ずつ実行します。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 examples/01_pose.py
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 examples/02_joint_motion.py --viewer
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 examples/03_planar_motion.py --viewer
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 examples/04_log_state.py
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 examples/05_plot_trajectory.py
```

`results/trajectory.png` を開き、軌跡の図を確認します。
各サンプルで確認することは[初回の確認項目](day0.md)にまとめています。エラーが出た場合は[トラブル対処](troubleshooting.md)を参照してください。
