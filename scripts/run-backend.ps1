$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$backendDir = Join-Path $repoRoot "backend"
$backendHealthUrl = "http://127.0.0.1:8000/health"

function Test-HttpEndpoint {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Url
  )

  try {
    $null = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 2
    return $true
  }
  catch {
    return $false
  }
}

function Test-TcpPort {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Address,
    [Parameter(Mandatory = $true)]
    [int]$Port
  )

  $client = New-Object System.Net.Sockets.TcpClient
  try {
    $asyncResult = $client.BeginConnect($Address, $Port, $null, $null)
    if (-not $asyncResult.AsyncWaitHandle.WaitOne(1000, $false)) {
      return $false
    }
    $client.EndConnect($asyncResult)
    return $true
  }
  catch {
    return $false
  }
  finally {
    $client.Dispose()
  }
}

if (-not (Test-Path -LiteralPath $pythonExe)) {
  throw "Virtual environment not found at $pythonExe. Run: python -m venv .venv"
}

if (Test-HttpEndpoint -Url $backendHealthUrl) {
  Write-Host "Backend is already running at http://127.0.0.1:8000. Reuse that server or open /health in the browser." -ForegroundColor Green
  exit 0
}

if (Test-TcpPort -Address "127.0.0.1" -Port 8000) {
  throw "Port 8000 is already in use by another process. Close the existing service on 127.0.0.1:8000, then run 'npm run backend' again."
}

Push-Location $backendDir
try {
  & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
}
finally {
  Pop-Location
}
