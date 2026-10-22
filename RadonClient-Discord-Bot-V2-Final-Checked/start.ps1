$ErrorActionPreference = "Stop"
Write-Host "Radon Client - Starting Python bot"
Set-Location $PSScriptRoot

$python = $null
if (Get-Command python -ErrorAction SilentlyContinue) { $python = "python" }
elseif (Get-Command py -ErrorAction SilentlyContinue) { $python = "py" }
else {
    Write-Host "Python was not found. Install Python 3.12 or newer." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "First launch: creating local Python environment..."
    & $python -m venv .venv
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
Write-Host "Checking/installing required Python packages..."
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Package installation failed." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit $LASTEXITCODE
}

Write-Host "Starting bot..."
& $venvPython bot.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "The bot stopped because of an error. Read the message above." -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
