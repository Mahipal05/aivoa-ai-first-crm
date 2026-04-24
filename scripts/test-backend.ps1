$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$backendDir = Join-Path $repoRoot "backend"

if (-not (Test-Path -LiteralPath $pythonExe)) {
  throw "Virtual environment not found at $pythonExe. Run: python -m venv .venv"
}

Push-Location $backendDir
try {
  & $pythonExe -m pytest app\tests\test_api.py
}
finally {
  Pop-Location
}
