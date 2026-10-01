# 第7回　自己位置推定とセンサ融合

2026年11月27日

教科書：15.1、15.3、16.1–16.2（抜粋版 76–88ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md)

移動量を積み重ねて位置を求めると、誤差も次第にたまります。別の位置観測を使ってそのずれを補正し、どの程度改善するか調べます。MuJoCoは使わず、1次元の人工データで実験します。

## 実行方法

教材の `README.md` があるフォルダから実行します。

macOS:

```bash
bash scripts/run.sh exercises/week07/starter.py
```

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 exercises/week07/starter.py
```

## 実習

`results/week07.png` と `results/week07.csv` には、真の位置、オドメトリ、位置観測、補正後の推定値が保存されます。実行時にはそれぞれのRMSEも表示されます。

1. 補正に使うゲイン `gain` を0、0.2、1に変えてください。
2. グラフとRMSEを比べ、それぞれの値でどの情報を使って位置を推定しているか説明してください。
3. 余裕があれば、推定や観測の不確かさに応じてゲインを変える方法を考えてください。

実習の結果や疑問点は授業中に話し合います。提出物はありません。
