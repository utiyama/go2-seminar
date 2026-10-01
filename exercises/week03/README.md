# 第3回　センサとノイズ

2026年10月30日

教科書：7.1–7.6（抜粋版 28–41ページ）

[教科書の案内](../../materials/textbook/README.md) ／ [ゼミの進め方](../../docs/student-guide.md)

物理モードでGo2のIMUの値を読み、ノイズを加えた場合と比べます。コードではジャイロのy成分を使っています。

## 実行方法

教材の `README.md` があるフォルダから実行します。

macOS:

```bash
bash scripts/run.sh exercises/week03/starter.py
```

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1 exercises/week03/starter.py
```

## 実習

`results/week03.csv` と `results/week03.png` に、理想的なセンサ値とノイズを加えた値が保存されます。

1. ノイズの標準偏差 `sigma` を0、0.05、0.2 rad/sに変え、平均とばらつきを比べてください。乱数のseedは同じ値にしておきます。
2. 実行後に表示されるIMUの値から、加速度計の値も確認してください。
3. 静止しているときにも加速度計が0にならない理由を、教科書の説明と照らし合わせて考えてください。

実習の結果や疑問点は授業中に話し合います。提出物はありません。記録を残したい場合は [notes.md](notes.md) を自由に使ってください。
