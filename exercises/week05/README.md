# 第5回　地図作成：2回の観測を重ねる

2026年11月13日

教科書：12.1–12.4、17.1（任意）（抜粋版 51–63ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md)

2か所から測った障害物の位置を、world座標に変換して重ねます。ロボットの位置の見積もりがずれると、地図にどんな影響が出るか調べます。

## 実行方法

教材の `README.md` があるフォルダから実行します。

macOS:

```bash
bash scripts/run.sh exercises/week05/starter.py
```

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 exercises/week05/starter.py
```

## 実習

まず `results/week05.png` を開き、2回の観測が重なっていることを確認してください。

1. 2回目の観測を変換するときだけ、推定位置 `estimated_xy` をx方向に0.15 mずらしてください。シミュレータ上のロボットの位置は変えません。
2. 変更前後の図を比べ、同じ障害物が二重に見える理由を説明してください。

距離はシミュレータ内のレイ計測で求めています。実機のLiDARやSLAMを再現したものではありません。

実習の結果や疑問点は授業中に話し合います。提出物はありません。記録を残したい場合は [notes.md](notes.md) を自由に使ってください。
