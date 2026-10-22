# week03以降で使うROS 2環境（pixi）を用意します。初回は数GBをダウンロードします。
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Push-Location (Join-Path $PSScriptRoot "..")
try {
    $PixiBin = Join-Path $env:USERPROFILE ".pixi\bin"
    if (-not (Get-Command pixi -ErrorAction SilentlyContinue)) {
        if (-not (Test-Path (Join-Path $PixiBin "pixi.exe"))) {
            Write-Host "pixiをインストールします ($PixiBin)。"
            Invoke-Expression (Invoke-RestMethod -UseBasicParsing https://pixi.sh/install.ps1)
        }
        $env:Path = "$PixiBin;$env:Path"
    }
    pixi --version
    if ($LASTEXITCODE -ne 0) { throw "pixi が起動できません" }
    pixi install
    if ($LASTEXITCODE -ne 0) { throw "pixi install に失敗しました。ネットワークを確認して再実行してください" }
    pixi run check
    if ($LASTEXITCODE -ne 0) { throw "ROS環境の確認に失敗しました" }
    Write-Host "ROS環境の準備完了。次は docs/setup-ros.md の「動作確認」に進んでください。"
} finally { Pop-Location }
