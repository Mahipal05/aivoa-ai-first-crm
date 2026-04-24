$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$backendDir = Join-Path $repoRoot "backend"

if (-not (Test-Path -LiteralPath $pythonExe)) {
  throw "Virtual environment not found at $pythonExe. Run: python -m venv .venv"
}

Push-Location $backendDir
try {
  & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
}
finally {
  Pop-Location
}
