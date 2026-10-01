$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Push-Location (Join-Path $PSScriptRoot "..")
try {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $PythonCommand = "py"
        $PythonArgs = @("-3.11")
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $PythonCommand = "python"
        $PythonArgs = @()
    } else {
        throw "Install Python 3.11 (64 bit) first. See README."
    }
    & $PythonCommand @PythonArgs -c 'import sys; assert sys.version_info[:2] == (3,11), "Python 3.11 required"'
    if ($LASTEXITCODE -ne 0) { throw "Python 3.11 check failed" }
    if (-not (Test-Path .venv)) {
        & $PythonCommand @PythonArgs -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "venv creation failed" }
    }
    $VenvPython = Join-Path $PWD ".venv/Scripts/python.exe"
    & $VenvPython -c 'import sys; assert sys.version_info[:2] == (3,11), "Existing .venv is not Python 3.11; rename it and retry"'
    if ($LASTEXITCODE -ne 0) { throw "Existing venv version mismatch" }
    & $VenvPython -m pip install --only-binary=:all: -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
    & $VenvPython -m pip install --no-deps --no-build-isolation -e .
    if ($LASTEXITCODE -ne 0) { throw "Package installation failed" }
    & $VenvPython scripts/check_env.py --output results/environment.json
    if ($LASTEXITCODE -ne 0) { throw "Environment check failed" }
    Write-Host 'Setup complete: .\scripts\run.ps1 examples/00_view.py'
} finally { Pop-Location }
