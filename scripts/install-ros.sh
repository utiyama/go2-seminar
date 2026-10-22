#!/usr/bin/env bash
# week03以降で使うROS 2環境（pixi）を用意します。初回は数GBをダウンロードします。
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v pixi >/dev/null 2>&1; then
  if [ -x "$HOME/.pixi/bin/pixi" ]; then
    export PATH="$HOME/.pixi/bin:$PATH"
  else
    echo 'pixiをインストールします（~/.pixi/bin）。'
    curl -fsSL https://pixi.sh/install.sh | sh
    export PATH="$HOME/.pixi/bin:$PATH"
  fi
fi
pixi --version
pixi install
pixi run check
echo 'ROS環境の準備完了。次は docs/setup-ros.md の「動作確認」に進んでください。'
