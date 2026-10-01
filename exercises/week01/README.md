# 第1回　自律ロボット：状態と行動

2026年10月9日

教科書：1.1–1.4、2.1–2.2（抜粋版 3–11ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md)

速度の指令を変えて、ロボットの軌跡がどう変わるか調べます。今回は胴体の位置を直接更新する平面移動モードを使います。

## 実行方法

教材の `README.md` があるフォルダから実行します。

macOS:

```bash
bash scripts/run.sh exercises/week01/starter.py
```

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 exercises/week01/starter.py
```

## 実習

まず `starter.py` を実行し、`results/week01.csv` を開いてください。最初のコードでは、前進速度と旋回速度を同時に与えています。

1. 前進・横移動・旋回の速度や動かす時間を変え、終点を予想してから実行してください。
2. 予想した位置とCSVの値を比べてください。向きが変わると、同じ前進指令でも軌跡が変わることに注目します。
3. 停止後も少し時間を進め、位置が変わらないことを確かめてください。

実習の結果や疑問点は授業中に話し合います。提出物はありません。記録を残したい場合は [notes.md](notes.md) を自由に使ってください。
