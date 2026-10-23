# Prepare the ROS 2 (pixi) environment used from week03 on. The first run downloads a few GB.
# Messages are kept in ASCII so that Windows PowerShell 5.1 parses this file without a BOM.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$env:PYTHONUTF8 = "1"
$PixiVersion = "v0.82.1"
Push-Location (Join-Path $PSScriptRoot "..")
try {
    if ((Get-Location).Path -match "OneDrive") {
        Write-Host "WARNING: this folder is inside OneDrive. The ROS environment (about 3.5 GB, many files)"
        Write-Host "         would be synced and may break. Move the course folder to a plain location such as"
        Write-Host "         C:\Users\<name>\go2-seminar first. See docs/setup-ros.md."
    }
    $PixiBin = Join-Path $env:USERPROFILE ".pixi\bin"
    $PixiExe = Join-Path $PixiBin "pixi.exe"
    if (-not (Get-Command pixi -ErrorAction SilentlyContinue)) {
        if (-not (Test-Path $PixiExe)) {
            # Download pixi directly instead of running its installer script, which hides network
            # errors behind an unrelated '$ZIP_FILE' error on Windows PowerShell 5.1.
            Write-Host "Downloading pixi $PixiVersion into $PixiBin"
            [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
            New-Item -ItemType Directory -Path $PixiBin -Force | Out-Null
            $Zip = Join-Path $env:TEMP "pixi-$PixiVersion.zip"
            $Url = "https://github.com/prefix-dev/pixi/releases/download/$PixiVersion/pixi-x86_64-pc-windows-msvc.zip"
            try {
                Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Zip
            } catch {
                throw "Could not download pixi from $Url. Check the network or proxy, or install pixi with 'winget install prefix-dev.pixi' and run this script again. ($($_.Exception.Message))"
            }
            Expand-Archive -Path $Zip -DestinationPath $PixiBin -Force
            Remove-Item $Zip -ErrorAction SilentlyContinue
        }
        $env:Path = "$PixiBin;$env:Path"
        $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if (($UserPath -split ";") -notcontains $PixiBin) {
            [Environment]::SetEnvironmentVariable("Path", "$PixiBin;$UserPath", "User")
            Write-Host "Added $PixiBin to your PATH. Open a new PowerShell window after this script finishes."
        }
    }
    pixi --version
    if ($LASTEXITCODE -ne 0) { throw "pixi could not be started" }
    pixi install
    if ($LASTEXITCODE -ne 0) { throw "pixi install failed; check the network and run this script again" }
    pixi run check
    if ($LASTEXITCODE -ne 0) { throw "ROS environment check failed; see docs/troubleshooting.md" }
    Write-Host "ROS environment ready. Next: docs/setup-ros.md (section 2)"
} finally { Pop-Location }
