#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON311="${PYTHON311:-python3.11}"
if ! command -v "$PYTHON311" >/dev/null 2>&1; then
  echo 'Python 3.11が必要です。docs/setup-macos.mdを確認してください。' >&2
  exit 1
fi
"$PYTHON311" -c 'import sys; assert sys.version_info[:2] == (3,11), "Python 3.11 required"'
if [ ! -d .venv ]; then "$PYTHON311" -m venv .venv; fi
.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3,11), "Existing .venv is not Python 3.11; rename it and retry"'
.venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python scripts/check_env.py --output results/environment.json
echo 'セットアップ完了。表示: bash scripts/run.sh examples/00_view.py'
