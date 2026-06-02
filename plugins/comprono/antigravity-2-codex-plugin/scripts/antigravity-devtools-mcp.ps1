$ErrorActionPreference = "Stop"

$installRoot = Join-Path $env:LOCALAPPDATA "Programs\Antigravity"
$exePath = Join-Path $installRoot "Antigravity.exe"
$userDataPath = Join-Path $env:APPDATA "Antigravity"
$devToolsPortFile = Join-Path $userDataPath "DevToolsActivePort"
$helperScript = Join-Path (Split-Path -Parent $PSScriptRoot) "scripts\antigravity.ps1"
$mcpBin = Join-Path $installRoot "resources\app.asar.unpacked\node_modules\chrome-devtools-mcp\build\src\bin\chrome-devtools-mcp.js"
$logFile = Join-Path $env:TEMP "antigravity-devtools-mcp.log"

if (-not (Test-Path -LiteralPath $exePath)) {
  throw "Antigravity.exe was not found at $exePath"
}

if (-not (Test-Path -LiteralPath $mcpBin)) {
  throw "chrome-devtools-mcp was not found at $mcpBin"
}

$processes = @(Get-Process -Name "Antigravity" -ErrorAction SilentlyContinue)
if ($processes.Count -eq 0) {
  Start-Process -FilePath $exePath -WorkingDirectory $installRoot
  Start-Sleep -Seconds 3
}

function Get-LivePageCount {
  if (-not (Test-Path -LiteralPath $devToolsPortFile)) {
    return 0
  }
  $lines = @(Get-Content -LiteralPath $devToolsPortFile -ErrorAction SilentlyContinue)
  if ($lines.Count -eq 0 -or [string]::IsNullOrWhiteSpace([string]$lines[0])) {
    return 0
  }
  try {
    $pages = @(Invoke-RestMethod -Uri "http://127.0.0.1:$($lines[0])/json/list" -TimeoutSec 3 -ErrorAction Stop)
    return $pages.Count
  } catch {
    return 0
  }
}

if ((Get-LivePageCount) -eq 0) {
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helperScript repair-live | Out-Null
  Start-Sleep -Seconds 2
}

if (-not (Test-Path -LiteralPath $devToolsPortFile)) {
  throw "Antigravity is running, but DevToolsActivePort was not found at $devToolsPortFile"
}

$lines = @(Get-Content -LiteralPath $devToolsPortFile)
if ($lines.Count -eq 0 -or [string]::IsNullOrWhiteSpace([string]$lines[0])) {
  throw "DevToolsActivePort exists but does not contain a port."
}

$port = [string]$lines[0]
$browserUrl = "http://127.0.0.1:$port"

if ((Get-LivePageCount) -eq 0) {
  throw "Antigravity DevTools has no inspectable pages after repair. Run antigravity-local.live or antigravity-local.repair-live, then restart Codex so the DevTools MCP transport can reconnect."
}

& node $mcpBin --browserUrl $browserUrl --no-usage-statistics --no-performance-crux --acceptInsecureCerts --logFile $logFile
exit $LASTEXITCODE
