$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendScript = Join-Path $repoRoot "scripts\run-backend.ps1"
$frontendDir = Join-Path $repoRoot "frontend"
$backendHealthUrl = "http://127.0.0.1:8000/health"
$frontendUrl = "http://localhost:5173"

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

if (Test-HttpEndpoint -Url $backendHealthUrl) {
  Write-Host "Backend is already running." -ForegroundColor Green
}
else {
  Write-Host "Starting backend in a separate PowerShell window..." -ForegroundColor Cyan
  Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", $backendScript
  )
}

Write-Host "Waiting for backend health check..." -ForegroundColor Cyan
$maxAttempts = 20
$backendReady = $false
for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
  try {
    $response = Invoke-RestMethod -Uri $backendHealthUrl -Method Get -TimeoutSec 2
    if ($response.status -eq "ok") {
      $backendReady = $true
      break
    }
  }
  catch {
    Start-Sleep -Seconds 1
  }
}

if (-not $backendReady) {
  throw "Backend did not become ready at $backendHealthUrl within 20 seconds."
}

Write-Host "Backend is ready." -ForegroundColor Green

if (Test-HttpEndpoint -Url $frontendUrl) {
  Write-Host "Frontend is already running at $frontendUrl. Reuse that tab or hard refresh it." -ForegroundColor Green
  exit 0
}

Write-Host "Launching frontend on $frontendUrl..." -ForegroundColor Green
Push-Location $frontendDir
try {
  npm run dev
}
finally {
  Pop-Location
}
