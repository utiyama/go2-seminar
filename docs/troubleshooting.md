# うまく動かないとき

[教材トップ](../README.md) ／ [Windowsの手順](setup-windows.md) ／ [macOSの手順](setup-macos.md)

表示されたエラーに近い項目を確認してください。解決しない場合は、実行したコマンド、エラーの末尾、OSとCPU、`results/environment.json` を添えて教員に相談してください。

## インストール・起動

| 症状 | 対処 |
|---|---|
| Pythonが見つからない、または3.12などが使われる | Windowsは `py -3.11 --version`、Macは `python3.11 --version` で確認します。既存の `.venv` が別の版で作られている場合は、フォルダ名を変えてからセットアップをやり直してください |
| `No matching distribution` | Python 3.11の64 bit版か、対応するOS・CPUかを確認してください。Windows ARMは対象外です。依存ソフトの版は動作確認のため固定してあるので、まず環境を確認します |
| PowerShellでスクリプトを実行できない | [Windowsの手順](setup-windows.md)にある `powershell -NoProfile -ExecutionPolicy Bypass -File ...` で起動してください。学校の管理ポリシーで禁止されている場合は教員に相談してください |
| `ModuleNotFoundError: go2_seminar` | セットアップを最後まで実行し、`scripts/run.sh` または `scripts/run.ps1` から起動してください。VS Codeを使う場合も、Python環境には教材の `.venv` を選びます |
| モデルのダウンロード、SSL、proxyのエラー | 初回はGitHub releasesへの接続が必要です。PCの時刻、学校のproxy、証明書の設定を確認してください。証明書の検証は無効にせず、必要なら教員が用意したモデルキャッシュを使います |
| MacでGitが見つからない、またはXcodeのライセンスが表示される | 下の「MacでGitが見つからない場合」を参照してください。インストール済みのCommand Line Toolsを指定して試します |

## MacでGitが見つからない場合

`git` で `Failed to locate 'git'` や `xcodebuild ... failed` と表示される一方、`xcode-select --install` では `Command line tools are already installed` と表示されることがあります。Command Line Toolsは入っていても、Gitを探す先がXcode側になっている場合です。

まず、Command Line ToolsのGitを直接呼んで確認します。

```bash
/Library/Developer/CommandLineTools/usr/bin/git --version
```

バージョンが表示されたら、同じターミナルで次を実行してください。

```bash
export DEVELOPER_DIR=/Library/Developer/CommandLineTools
git --version
```

こちらでもバージョンが表示されれば、先ほど失敗したGitコマンドをやり直せます。この指定は現在のターミナル内で有効です。新しくターミナルを開いて同じエラーが出たら、もう一度実行してください。

最初のコマンドでもGitが見つからない場合は、この手順では解決できません。エラーを教員に見せるか、教材をDownload ZIPで取得してください。

参照：[Appleのコマンドラインツール設定](https://developer.apple.com/documentation/xcode/configuring-command-line-tools-settings)

## 画面表示

| 症状 | 対処 |
|---|---|
| `launch_passive ... mjpython` | Macでは `bash scripts/run.sh examples/00_view.py` で起動します。自作のGUIスクリプトは `.venv/bin/mjpython` から起動してください |
| `otool` が見つからない、または終了コード69 | `xcode-select --install` でApple Command Line Toolsを導入してください。教材のランチャーは、起動したプロセス内でCommand Line Toolsを優先して使います。システムのXcode設定は変更しません |
| `libpython3.11.dylib` を読み込めない | uvなどで入れたPythonでは `bash scripts/run.sh` を使ってください。ランチャーが必要なライブラリの場所を設定します |
| GLFWやOpenGLのエラー、黒い画面 | まずリモート接続ではなくPCの画面で試し、GPUドライバも確認してください。`--headless` で計算だけ動くか調べると、表示の問題かどうかを切り分けられます |
| 動作が遅い | 他の重いアプリを終了して試してください。画面を表示せずに計算する方法もあります。CSVの時刻は、実際に待った時間ではなくシミュレーション内の時刻です |

画面を表示しないテストが通っても、GUIが使えるかどうかは別途確認が必要です。

## シミュレータの動作

| 症状 | 説明・対処 |
|---|---|
| Go2が滑るように移動する | kinematicモードでは胴体の位置を直接更新します。足で歩くための制御器は含まれていません |
| physicsモードで `set_velocity()` がエラーになる | 速度指令はkinematicモードで使います。physicsモードでは関節角を指定してください |
| kinematicモードで `get_imu()` がエラーになる | IMUの値を得るにはphysicsモードを使います。week03が使用例です |
| 距離が `inf` になる | 計測範囲内に障害物がありません。`obstacles=True` になっているか、レイの向きや最大距離も確認してください |
| 時間の引数でエラーになる | 既定の設定では、`step` の時間は0.002秒の整数倍、`run` の `seconds` は0.02秒の整数倍で指定してください |
