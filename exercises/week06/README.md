# 第6回　経路計画：グリッド上の探索

2026年11月20日

教科書：13.1–13.3、13.5（抜粋版 64–75ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md)

格子状の地図で、障害物を避けてゴールに至る経路を探します。この回はMuJoCoを使わず、探索アルゴリズムだけをPythonで試します。

## 実行方法

教材の `README.md` があるフォルダから実行します。

macOS:

```bash
bash scripts/run.sh exercises/week06/starter.py
```

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 exercises/week06/starter.py
```

## 実習

最初のコードは幅優先探索（BFS）です。経路と展開したノード数が `results/week06.json` に保存されます。座標はworldのx・yではなく、グリッドの行・列で表しています。

1. BFSをA*に変更してください。優先度には、そこまでのコストとゴールまでのマンハッタン距離を使います。
2. 同じ地図で経路長と展開ノード数を比べてください。
3. ゴールに到達できない地図と、出発点がゴールと同じ場合でも試してください。

実習の結果や疑問点は授業中に話し合います。提出物はありません。記録を残したい場合は [notes.md](notes.md) を自由に使ってください。
