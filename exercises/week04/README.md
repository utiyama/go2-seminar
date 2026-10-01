# 第4回　反応型制御と状態遷移

2026年11月6日

教科書：11.1–11.3（抜粋版 42–50ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md)

前方の障害物までの距離を使って、前進と停止を切り替えます。状態を追加し、障害物の前で向きを変えてから進む動作を作ります。

## 実行方法

教材の `README.md` があるフォルダから実行します。

macOS:

```bash
bash scripts/run.sh exercises/week04/starter.py
```

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 exercises/week04/starter.py
```

## 実習

最初のコードは `FORWARD` から `STOP` への切り替えだけを行います。実行して、停止した時刻と距離、`results/week04.csv` を確認してください。

1. `TURN` 状態を追加し、停止後に旋回するようにしてください。
2. 一定時間旋回したら `FORWARD` に戻るようにしてください。
3. 前進速度と、停止する距離のしきい値を変えて動作を比べてください。

この回は平面移動モードです。障害物に触れても自動では止まらないため、距離を見て停止する処理が必要です。

実習の結果や疑問点は授業中に話し合います。提出物はありません。
