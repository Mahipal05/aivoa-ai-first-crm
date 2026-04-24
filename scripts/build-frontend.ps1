$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot "frontend"

Push-Location $frontendDir
try {
  npm run build
}
finally {
  Pop-Location
}
