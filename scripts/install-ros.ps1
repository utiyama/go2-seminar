# Prepare the ROS 2 (pixi) environment used from week03 on. The first run downloads a few GB.
# Messages are kept in ASCII so that Windows PowerShell 5.1 parses this file without a BOM.
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Push-Location (Join-Path $PSScriptRoot "..")
try {
    $PixiBin = Join-Path $env:USERPROFILE ".pixi\bin"
    if (-not (Get-Command pixi -ErrorAction SilentlyContinue)) {
        if (-not (Test-Path (Join-Path $PixiBin "pixi.exe"))) {
            Write-Host "Installing pixi into $PixiBin"
            Invoke-Expression (Invoke-RestMethod -UseBasicParsing https://pixi.sh/install.ps1)
        }
        $env:Path = "$PixiBin;$env:Path"
    }
    pixi --version
    if ($LASTEXITCODE -ne 0) { throw "pixi could not be started" }
    pixi install
    if ($LASTEXITCODE -ne 0) { throw "pixi install failed; check the network and run this script again" }
    pixi run check
    if ($LASTEXITCODE -ne 0) { throw "ROS environment check failed; see docs/troubleshooting.md" }
    Write-Host "ROS environment ready. Next: docs/setup-ros.md (section 2)"
} finally { Pop-Location }
