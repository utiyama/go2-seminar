$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Push-Location (Join-Path $PSScriptRoot "..")
try {
    $VenvPython = Join-Path $PWD ".venv/Scripts/python.exe"
    if (-not (Test-Path $VenvPython)) { throw "Run scripts/install.ps1 first" }
    & $VenvPython scripts/launch.py @args
    $RunExitCode = $LASTEXITCODE
} finally { Pop-Location }
exit $RunExitCode
