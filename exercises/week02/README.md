# 第2回　座標系と姿勢

2026年10月23日

教科書：2.3–2.4（抜粋版 12–27ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md)

ロボットから見た「前方1 m」の点を、地面に固定した座標系で表します。ロボットに固定した座標系をbody、地面に固定した座標系をworldと呼びます。

## 実行方法

教材の `README.md` があるフォルダから実行します。

macOS:

```bash
bash scripts/run.sh exercises/week02/starter.py
```

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 exercises/week02/starter.py
```

## 実習

実行すると、変換前後の座標が表示され、`results/week02.png` に図が保存されます。

1. yawを0度、45度、90度に変え、前方1 mの点がworld座標でどこに来るか比べてください。コードでは `np.deg2rad()` でradに変換します。
2. world座標からbody座標へ戻す変換を書いてください。
3. 変換して戻した値が、元の座標と一致するか確かめてください。

実習の結果や疑問点は授業中に話し合います。提出物はありません。
