param(
  [Parameter(Position = 0)]
  [ValidateSet("status", "open", "repair-live", "inspect", "path", "models", "limits", "limits-summary", "quick", "live", "setup", "doctor", "privacy", "devtools-health", "submission-guide", "offload-advice", "handoff-template", "prepare-offload", "submit-offload")]
  [string] $Command = "status",

  [string] $Goal = "",
  [string] $Workspace = "",
  [string] $StatusFile = "notes/antigravity-status.md",
  [string] $NextStep = "Inspect the relevant files and write a compact status checkpoint.",
  [string] $ExpectedProject = "",
  [string] $ExpectedChat = "",
  [object] $Submit = $false,
  [object] $FillOnly = $false,
  [object] $HasWorkspaceWork = $true,
  [int] $EstimatedCodexInputTokens = 2000
)

$ErrorActionPreference = "Stop"

$installRoot = Join-Path $env:LOCALAPPDATA "Programs\Antigravity"
$exePath = Join-Path $installRoot "Antigravity.exe"
$userDataPath = Join-Path $env:APPDATA "Antigravity"
$devToolsPortFile = Join-Path $userDataPath "DevToolsActivePort"
$repoRoot = Split-Path -Parent $PSScriptRoot

function Get-AntigravityProcess {
  Get-Process -Name "Antigravity" -ErrorAction SilentlyContinue
}

function ConvertTo-BooleanValue {
  param(
    [object] $Value,
    [bool] $Default = $true
  )

  if ($null -eq $Value) {
    return $Default
  }
  if ($Value -is [bool]) {
    return [bool]$Value
  }
  if ($Value -is [int]) {
    return ([int]$Value) -ne 0
  }

  $text = ([string]$Value).Trim()
  if ([string]::IsNullOrWhiteSpace($text)) {
    return $Default
  }
  if ($text -match "^(true|1|yes|y)$") {
    return $true
  }
  if ($text -match "^(false|0|no|n)$") {
    return $false
  }

  return $Default
}

function Get-DevToolsPort {
  if (Test-Path -LiteralPath $devToolsPortFile) {
    $lines = @(Get-Content -LiteralPath $devToolsPortFile -ErrorAction SilentlyContinue)
    if ($lines.Count -gt 0) {
      return [string]$lines[0]
    }
  }
  return $null
}

function Get-DevToolsPages {
  $port = Get-DevToolsPort
  if (-not $port) {
    return @()
  }

  try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:$port/json/list" -TimeoutSec 5 -ErrorAction Stop
    foreach ($page in $response) {
      $page
    }
  } catch {
    @()
  }
}

function Wait-DevToolsPages {
  param(
    [int] $TimeoutSeconds = 20
  )

  $deadline = [datetime]::UtcNow.AddSeconds($TimeoutSeconds)
  do {
    $pages = @(Get-DevToolsPages)
    if ($pages.Count -gt 0) {
      return $pages
    }
    Start-Sleep -Milliseconds 500
  } while ([datetime]::UtcNow -lt $deadline)

  return @()
}

function Stop-AntigravityForRepair {
  $processes = @(Get-AntigravityProcess)
  foreach ($process in $processes) {
    try {
      if ($process.MainWindowHandle -ne 0) {
        [void]$process.CloseMainWindow()
      }
    } catch {
      # Fall through to the bounded hard stop below.
    }
  }

  if ($processes.Count -gt 0) {
    Start-Sleep -Seconds 3
  }

  $remaining = @(Get-AntigravityProcess)
  foreach ($process in $remaining) {
    try {
      Stop-Process -Id $process.Id -Force -ErrorAction Stop
    } catch {
      # Ignore processes that exited between enumeration and stop.
    }
  }
}

function Stop-DevToolsMcpProcesses {
  $stopped = @()
  $processes = @(Get-CimInstance Win32_Process -Filter "Name = 'node.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*chrome-devtools-mcp*" })

  foreach ($process in $processes) {
    try {
      Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
      $stopped += [int]$process.ProcessId
    } catch {
      # Ignore processes that exited between enumeration and stop.
    }
  }

  $stopped
}

function Start-AntigravityAndWait {
  param(
    [int] $TimeoutSeconds = 20
  )

  if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Antigravity.exe was not found at $exePath"
  }

  if (Test-Path -LiteralPath $devToolsPortFile) {
    Remove-Item -LiteralPath $devToolsPortFile -Force -ErrorAction SilentlyContinue
  }

  Start-Process -FilePath $exePath -WorkingDirectory $installRoot
  [void](Wait-DevToolsPages -TimeoutSeconds $TimeoutSeconds)
}

function Repair-LiveDevTools {
  $before = Get-LiveReportObject
  if ($before.Running -and $before.PageCount -gt 0) {
    return [PSCustomObject]@{
      Source = "Antigravity live DevTools repair"
      GeneratedAtUtc = [datetime]::UtcNow.ToString("o")
      Action = "none"
      Reason = "Live DevTools already has pages."
      Before = $before
      After = $before
      ReadyForLiveUiInspection = $true
    }
  }

  $stoppedMcpBefore = @(Stop-DevToolsMcpProcesses)
  Stop-AntigravityForRepair
  Start-AntigravityAndWait -TimeoutSeconds 25
  $stoppedMcpAfter = @(Stop-DevToolsMcpProcesses)
  $after = Get-LiveReportObject

  [PSCustomObject]@{
    Source = "Antigravity live DevTools repair"
    GeneratedAtUtc = [datetime]::UtcNow.ToString("o")
    Action = "restart-antigravity"
    Reason = "Live DevTools had no inspectable pages."
    Before = $before
    After = $after
    StoppedDevToolsMcpProcessIds = @($stoppedMcpBefore + $stoppedMcpAfter)
    StaleMcpNote = "If repair-live restarted Antigravity, any already-started antigravity-devtools MCP process must reconnect to the new DevTools port before UI actions."
    ReadyForLiveUiInspection = [bool]($after.Running -and $after.PageCount -gt 0)
  }
}

function Get-LanguageServerProcess {
  $proc = Get-CimInstance Win32_Process -Filter "Name = 'language_server.exe'" -ErrorAction SilentlyContinue |
    Select-Object -First 1
  if (-not $proc) {
    $proc = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -like "*language_server.exe*" } |
      Select-Object -First 1
  }
  $proc
}

function Get-LanguageServerInfo {
  $process = Get-LanguageServerProcess
  if (-not $process) {
    throw "Antigravity language_server.exe is not running. Open Antigravity first."
  }

  $csrfToken = $null
  if ($process.CommandLine -match "--csrf_token\s+([^\s]+)") {
    $csrfToken = $Matches[1]
  }

  $ports = @(Get-NetTCPConnection -OwningProcess $process.ProcessId -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalAddress -eq "127.0.0.1" } |
    Select-Object -ExpandProperty LocalPort |
    Sort-Object)

  $httpPort = $null
  $httpsPort = $null
  foreach ($port in $ports) {
    try {
      $headers = @{}
      if ($csrfToken) {
        $headers["X-Csrf-Token"] = $csrfToken
      }
      $health = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$port/healthz" -Headers $headers -TimeoutSec 2 -ErrorAction Stop
      if ($health.StatusCode -eq 200) {
        $httpPort = $port
        break
      }
    } catch {
      # The HTTPS gRPC-web port rejects plain HTTP; continue probing.
    }
  }

  if ($ports.Count -gt 0) {
    $httpsPort = @($ports | Where-Object { $_ -ne $httpPort } | Select-Object -First 1)[0]
  }

  [PSCustomObject]@{
    ProcessId = $process.ProcessId
    HttpPort = $httpPort
    HttpsPort = $httpsPort
    CsrfToken = $csrfToken
  }
}

function Invoke-AntigravityGrpcJson {
  param(
    [Parameter(Mandatory = $true)]
    [int] $Port,
    [Parameter(Mandatory = $true)]
    [string] $CsrfToken,
    [Parameter(Mandatory = $true)]
    [string] $Method,
    [Parameter(Mandatory = $true)]
    [object] $Message
  )

  $previousCallback = [System.Net.ServicePointManager]::ServerCertificateValidationCallback
  [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

  try {
    $json = $Message | ConvertTo-Json -Depth 20 -Compress
    $messageBytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    $body = New-Object byte[] (5 + $messageBytes.Length)
    $body[0] = 0
    $body[1] = [byte](($messageBytes.Length -shr 24) -band 0xff)
    $body[2] = [byte](($messageBytes.Length -shr 16) -band 0xff)
    $body[3] = [byte](($messageBytes.Length -shr 8) -band 0xff)
    $body[4] = [byte]($messageBytes.Length -band 0xff)
    [Array]::Copy($messageBytes, 0, $body, 5, $messageBytes.Length)

    $request = [System.Net.HttpWebRequest]::Create("https://127.0.0.1:$Port/exa.language_server_pb.LanguageServerService/$Method")
    $request.Method = "POST"
    $request.ContentType = "application/grpc-web+json"
    $request.Headers.Add("X-Grpc-Web", "1")
    $request.Headers.Add("X-User-Agent", "CONNECT_ES_USER_AGENT")
    $request.Headers.Add("x-codeium-csrf-token", $CsrfToken)
    $request.ContentLength = $body.Length

    $requestStream = $request.GetRequestStream()
    try {
      $requestStream.Write($body, 0, $body.Length)
    } finally {
      $requestStream.Dispose()
    }

    try {
      $response = $request.GetResponse()
    } catch [System.Net.WebException] {
      if ($_.Exception.Response) {
        $_.Exception.Response.Dispose()
      }
      throw $_
    }
    try {
      $memory = New-Object System.IO.MemoryStream
      $response.GetResponseStream().CopyTo($memory)
      $bytes = $memory.ToArray()
    } finally {
      $response.Dispose()
    }

    $offset = 0
    $messages = @()
    $trailers = ""
    while ($offset + 5 -le $bytes.Length) {
      $flag = [int]$bytes[$offset]
      $length = ([int]$bytes[$offset + 1] -shl 24) -bor ([int]$bytes[$offset + 2] -shl 16) -bor ([int]$bytes[$offset + 3] -shl 8) -bor [int]$bytes[$offset + 4]
      $offset += 5
      if ($length -lt 0 -or $offset + $length -gt $bytes.Length) {
        throw "Invalid gRPC-web frame length from Antigravity language server."
      }

      $frameBytes = New-Object byte[] $length
      [Array]::Copy($bytes, $offset, $frameBytes, 0, $length)
      $offset += $length

      if (($flag -band 0x80) -ne 0) {
        $trailers = [System.Text.Encoding]::UTF8.GetString($frameBytes)
      } else {
        $messages += [System.Text.Encoding]::UTF8.GetString($frameBytes) | ConvertFrom-Json
      }
    }

    if ($trailers -and $trailers -notmatch "grpc-status:\s*0") {
      throw "Antigravity gRPC-web call failed: $trailers"
    }
    if ($messages.Count -eq 0) {
      return $null
    }
    return $messages[0]
  } finally {
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = $previousCallback
  }
}

function Get-NodeInfo {
  $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
  if (-not $nodeCommand) {
    return [PSCustomObject]@{
      Found = $false
      Path = $null
      Version = $null
    }
  }

  $version = $null
  try {
    $version = (& $nodeCommand.Source --version 2>$null)
  } catch {
    $version = $null
  }

  [PSCustomObject]@{
    Found = $true
    Path = $nodeCommand.Source
    Version = $version
  }
}

function Get-SetupReportObject {
  $status = Write-Status | ConvertFrom-Json
  $inspect = $null
  try {
    $inspect = & $PSCommandPath inspect | ConvertFrom-Json
  } catch {
    $inspect = $null
  }

  $languageServer = $null
  if ($status.Running) {
    try {
      $ls = Get-LanguageServerInfo
      $languageServer = [PSCustomObject]@{
        Running = $true
        ProcessId = $ls.ProcessId
        HttpPort = $ls.HttpPort
        HttpsPort = $ls.HttpsPort
        HasCsrfToken = [bool]$ls.CsrfToken
      }
    } catch {
      $languageServer = [PSCustomObject]@{
        Running = $false
        Error = $_.Exception.Message
      }
    }
  } else {
    $languageServer = [PSCustomObject]@{
      Running = $false
    }
  }

  $node = Get-NodeInfo
  $devToolsPages = Get-DevToolsPages

  [PSCustomObject]@{
    PluginRoot = $repoRoot
    Installed = $status.Installed
    AntigravityExe = $status.ExePath
    AntigravityUserData = $status.UserDataPath
    AntigravityRunning = $status.Running
    DevToolsPort = $status.DevToolsPort
    DevToolsReachable = $devToolsPages.Count -gt 0
    Node = $node
    ChromeDevToolsMcpFound = [bool]($inspect -and $inspect.BundledPackageFiles -and $inspect.BundledPackageFiles.Count -gt 0)
    LanguageServer = $languageServer
    ReadyForModelLimits = [bool]($languageServer.Running -and $languageServer.HttpsPort -and $languageServer.HasCsrfToken)
    ReadyForLiveUiInspection = [bool]($status.Running -and $status.DevToolsPort -and $devToolsPages.Count -gt 0)
  }
}

function Get-SetupReport {
  Get-SetupReportObject | ConvertTo-Json -Depth 8
}

function Get-LiveReportObject {
  $status = Write-Status | ConvertFrom-Json
  $pages = Get-DevToolsPages | ForEach-Object {
    [PSCustomObject]@{
      Type = $_.type
      Title = $_.title
      Url = $_.url
      WebSocketDebuggerUrl = $_.webSocketDebuggerUrl
    }
  }

  [PSCustomObject]@{
    Source = "Antigravity Chromium DevTools endpoint"
    GeneratedAtUtc = [datetime]::UtcNow.ToString("o")
    Running = $status.Running
    DevToolsPort = $status.DevToolsPort
    PageCount = @($pages).Count
    Pages = @($pages)
    Note = "Use the DevTools page WebSocket or the antigravity-devtools MCP server for verified live UI inspection and interaction."
  }
}

function Get-LiveReport {
  Get-LiveReportObject | ConvertTo-Json -Depth 8
}

function Get-PrivacyReport {
  $patterns = @(
    "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "C:\\Users\\[^\\]+",
    ("pass" + "word"),
    ("sec" + "ret"),
    ("tok" + "en\s*[:=]"),
    "api[_-]?key",
    "BEGIN (RSA|OPENSSH|PRIVATE)",
    "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
  )

  $findings = @()
  $scanFiles = @(Get-ChildItem -LiteralPath $repoRoot -Recurse -File -Force -ErrorAction SilentlyContinue |
    Where-Object {
      $_.FullName -notmatch "\\.git\\" -and
      $_.FullName -notmatch "\\node_modules\\" -and
      $_.FullName -notmatch "\\.pytest_cache\\" -and
      $_.FullName -notmatch "\\__pycache__\\"
    })
  foreach ($pattern in $patterns) {
    $matches = @($scanFiles |
      Select-String -Pattern $pattern -ErrorAction SilentlyContinue |
      Where-Object { $_.Line -notmatch "csrfToken|csrf_token|x-codeium-csrf-token" } |
      Select-Object Path, LineNumber, Pattern)
    foreach ($match in $matches) {
      $findings += [PSCustomObject]@{
        Path = $match.Path
        LineNumber = $match.LineNumber
        Pattern = $pattern
      }
    }
  }

  [PSCustomObject]@{
    Source = "Local repository pattern scan"
    GeneratedAtUtc = [datetime]::UtcNow.ToString("o")
    FindingCount = $findings.Count
    Findings = $findings
    Note = "Review findings manually before publishing. Runtime CSRF handling in code is expected; actual runtime token values must never be committed."
  } | ConvertTo-Json -Depth 6
}

function Convert-QuotaInfo {
  param(
    [object] $QuotaInfo
  )

  if (-not $QuotaInfo) {
    return [PSCustomObject]@{
      Status = "unknown"
      RemainingFraction = $null
      RemainingPercent = $null
      ResetTimeUtc = $null
    }
  }

  $remainingFraction = $null
  if ($QuotaInfo.PSObject.Properties.Name -contains "remainingFraction") {
    $remainingFraction = [double]$QuotaInfo.remainingFraction
  }

  $resetTimeUtc = $null
  if ($QuotaInfo.PSObject.Properties.Name -contains "resetTime") {
    $resetTimeUtc = $QuotaInfo.resetTime
  }

  $status = "available"
  if ($remainingFraction -ne $null) {
    if ($remainingFraction -le 0) {
      $status = "exhausted"
    } elseif ($remainingFraction -lt 0.2) {
      $status = "low"
    }
  } elseif ($resetTimeUtc) {
    try {
      if ([System.DateTimeOffset]::Parse($resetTimeUtc).UtcDateTime -gt [datetime]::UtcNow) {
        $status = "exhausted"
      }
    } catch {
      $status = "unknown"
    }
  } else {
    $status = "unknown"
  }

  $remainingPercent = $null
  if ($remainingFraction -ne $null) {
    $remainingPercent = [math]::Round($remainingFraction * 100, 1)
  }

  [PSCustomObject]@{
    Status = $status
    RemainingFraction = $remainingFraction
    RemainingPercent = $remainingPercent
    ResetTimeUtc = $resetTimeUtc
  }
}

function Get-AntigravityModelsObject {
  $server = Get-LanguageServerInfo
  if (-not $server.CsrfToken) {
    throw "Could not find the Antigravity language server CSRF token in the running process command line."
  }
  if (-not $server.HttpsPort) {
    throw "Could not find the Antigravity language server HTTPS gRPC-web port."
  }

  $modelsResponse = Invoke-AntigravityGrpcJson -Port $server.HttpsPort -CsrfToken $server.CsrfToken -Method "GetAvailableModels" -Message @{ forceRefresh = $false }
  $creditsResponse = Invoke-AntigravityGrpcJson -Port $server.HttpsPort -CsrfToken $server.CsrfToken -Method "GetLoadCodeAssist" -Message @{ forceRefresh = $false }

  $models = @()
  $rawModels = $null
  if ($modelsResponse -and $modelsResponse.response) {
    $rawModels = $modelsResponse.response.models
  }
  if ($rawModels) {
    foreach ($modelId in @($rawModels.PSObject.Properties.Name | Sort-Object)) {
      $model = $rawModels.$modelId
      $quota = Convert-QuotaInfo -QuotaInfo $model.quotaInfo
      $models += [PSCustomObject]@{
        Id = $modelId
        DisplayName = $model.displayName
        ApiProvider = $model.apiProvider
        Disabled = [bool]$model.disabled
        Quota = $quota
      }
    }
  }

  $creditInfo = $null
  $tier = $null
  if ($creditsResponse -and $creditsResponse.response) {
    $tier = $creditsResponse.response.currentTier
  }
  $availableCredits = @()
  if ($tier -and $tier.PSObject.Properties.Name -contains "availableCredits") {
    $availableCredits = @($tier.availableCredits)
  }
  $creditInfo = [PSCustomObject]@{
    CurrentTierId = $tier.id
    CurrentTierName = $tier.name
    AvailableCredits = $availableCredits
    UpgradeSubscriptionType = $tier.upgradeSubscriptionType
  }

  [PSCustomObject]@{
    Source = "Antigravity local language server gRPC-web"
    GeneratedAtUtc = [datetime]::UtcNow.ToString("o")
    LanguageServer = [PSCustomObject]@{
      ProcessId = $server.ProcessId
      HttpPort = $server.HttpPort
      HttpsPort = $server.HttpsPort
    }
    Note = "Antigravity exposes per-model quota fraction/reset metadata, not a raw token ledger."
    CreditStatus = $creditInfo
    Models = $models
  }
}

function Get-AntigravityModels {
  Get-AntigravityModelsObject | ConvertTo-Json -Depth 12
}

function Get-LimitsSummaryObject {
  $report = Get-AntigravityModelsObject
  $namedModels = @($report.Models | Where-Object { $_.DisplayName })
  $available = @($namedModels | Where-Object { $_.Quota.Status -eq "available" })
  $low = @($namedModels | Where-Object { $_.Quota.Status -eq "low" })
  $exhausted = @($namedModels | Where-Object { $_.Quota.Status -eq "exhausted" })
  $unknown = @($namedModels | Where-Object { $_.Quota.Status -eq "unknown" })

  $recommended = @($available |
    Sort-Object `
      @{ Expression = { if ($_.DisplayName -match "Sonnet") { 0 } elseif ($_.DisplayName -match "Gemini") { 1 } else { 2 } } },
      @{ Expression = { if ($_.Quota.RemainingPercent -ne $null) { -1 * $_.Quota.RemainingPercent } else { 0 } } },
      DisplayName |
    Select-Object -First 4 |
    ForEach-Object {
      [PSCustomObject]@{
        Id = $_.Id
        DisplayName = $_.DisplayName
        RemainingPercent = $_.Quota.RemainingPercent
        ResetTimeUtc = $_.Quota.ResetTimeUtc
      }
    })

  $blocked = @($exhausted |
    Sort-Object @{ Expression = { $_.Quota.ResetTimeUtc } }, DisplayName |
    Select-Object -First 8 |
    ForEach-Object {
      [PSCustomObject]@{
        Id = $_.Id
        DisplayName = $_.DisplayName
        ResetTimeUtc = $_.Quota.ResetTimeUtc
      }
    })

  [PSCustomObject]@{
    Source = $report.Source
    GeneratedAtUtc = $report.GeneratedAtUtc
    Note = $report.Note
    Counts = [PSCustomObject]@{
      NamedModels = $namedModels.Count
      Available = $available.Count
      Low = $low.Count
      Exhausted = $exhausted.Count
      Unknown = $unknown.Count
    }
    CreditStatus = $report.CreditStatus
    RecommendedAvailable = $recommended
    BlockedOrResetting = $blocked
  }
}

function Get-LimitsSummary {
  Get-LimitsSummaryObject | ConvertTo-Json -Depth 8
}

function Get-QuickReport {
  $setup = Get-SetupReportObject
  $live = Get-LiveReportObject
  $limitsSummary = $null
  $limitsError = $null

  if ($setup.ReadyForModelLimits) {
    try {
      $limitsSummary = Get-LimitsSummaryObject
    } catch {
      $limitsError = $_.Exception.Message
    }
  }

  [PSCustomObject]@{
    Source = "Antigravity local bridge quick report"
    GeneratedAtUtc = [datetime]::UtcNow.ToString("o")
    Setup = [PSCustomObject]@{
      Installed = $setup.Installed
      Running = $setup.AntigravityRunning
      ReadyForModelLimits = $setup.ReadyForModelLimits
      ReadyForLiveUiInspection = $setup.ReadyForLiveUiInspection
      DevToolsReachable = $setup.DevToolsReachable
      NodeFound = $setup.Node.Found
    }
    Live = [PSCustomObject]@{
      PageCount = $live.PageCount
      ActivePageTitle = if (@($live.Pages).Count -gt 0) { @($live.Pages)[0].Title } else { $null }
      DevToolsPort = $live.DevToolsPort
    }
    Limits = if ($limitsSummary) {
      [PSCustomObject]@{
        GeneratedAtUtc = $limitsSummary.GeneratedAtUtc
        Counts = $limitsSummary.Counts
        RecommendedAvailable = $limitsSummary.RecommendedAvailable
        BlockedOrResetting = $limitsSummary.BlockedOrResetting
      }
    } else {
      $null
    }
    LimitsError = $limitsError
    NextToolHint = "Use antigravity-local quick first. If ReadyForLiveUiInspection is false, call repair-live once. If repair restarts Antigravity, reconnect DevTools before UI calls. Use limits-summary for compact quota checks, full limits only when needed. If UI handoff is blocked, use handoff-template."
  } | ConvertTo-Json -Depth 10
}

function Get-OffloadDecisionObject {
  param(
    [string] $TaskGoal,
    [bool] $NeedsWorkspace,
    [int] $EstimatedTokens
  )

  $lowerGoal = $TaskGoal.ToLowerInvariant()
  $trivial = $lowerGoal -match "\b(2\s*\+\s*2|add\s+2\s*\+\s*2|what\s+is|time|date|summari[sz]e\s+this\s+short|one\s+line|yes\s+or\s+no)\b"
  if ((-not $NeedsWorkspace) -and $EstimatedTokens -gt 0 -and $EstimatedTokens -lt 400) {
    $trivial = $true
  }

  $workspaceLikely = $NeedsWorkspace -or
    ($lowerGoal -match "\b(repo|workspace|project|files?|diff|logs?|tests?|build|lint|implement|refactor|debug|apply|continue\s+chat|job\s+search|browser|ui|analy[sz]e|review|plan|research|inspect|investigate|fix|patch|error|failure|trace|search|compare)\b") -or
    ($EstimatedTokens -ge 800)

  $shouldOffload = $workspaceLikely -and (-not $trivial)
  if ($shouldOffload) {
    [PSCustomObject]@{
      Decision = "offload-to-antigravity"
      Reason = "The task appears to benefit from Antigravity inspecting the local workspace or running longer reasoning while Codex reads back a compact artifact."
      ShouldOffload = $true
    }
  } else {
    [PSCustomObject]@{
      Decision = "codex-direct"
      Reason = "The task is small enough that DevTools navigation, project context scanning, and Antigravity startup/agent overhead will likely cost more time and tokens than Codex answering directly."
      ShouldOffload = $false
    }
  }
}

function Get-HandoffTemplateText {
  param(
    [string] $TaskGoal,
    [string] $TaskWorkspace,
    [string] $TaskStatusFile,
    [string] $TaskNextStep
  )

  if ([string]::IsNullOrWhiteSpace($TaskGoal)) {
    $TaskGoal = "<goal>"
  }
  if ([string]::IsNullOrWhiteSpace($TaskWorkspace)) {
    $TaskWorkspace = "<workspace/path>"
  }

  @(
    "Use this as a compact Antigravity offload handoff:",
    "",
    '```text',
    "Goal: $TaskGoal",
    "Workspace: $TaskWorkspace",
    "Constraints: inspect files locally; do not paste full files, full logs, or full source; use search before reading whole files.",
    "Token rule: work token-efficiently; write progress to $TaskStatusFile; output max 10 bullets plus changed file list.",
    "Next step: $TaskNextStep",
    "If blocked: ask one concise question; otherwise continue autonomously.",
    '```',
    "",
    "Codex follow-up rule: do not read the full Antigravity chat. Read only the status artifact, targeted diffs, or a compact visible UI status."
  ) -join [Environment]::NewLine
}

function Get-SubmissionGuideText {
  @(
    "AntigravitySubmissionGuide:",
    "1. Verify the target project, conversation, model, and idle composer first.",
    "2. Fill or type the prompt into the composer only. Do not include submitKey in the fill/type call.",
    "3. Prefer clicking the visible Send/arrow button after the composer contains the prompt.",
    "4. If a keyboard submit is required, use a separate key tool call with a simple accepted key such as Enter. Do not use Control+Enter, Ctrl+Enter, or chord strings unless the active tool schema explicitly lists that exact value.",
    "5. After submitting, verify Antigravity accepted the message by checking for a working/streaming state or a new visible user message.",
    "6. If the key or click fails once, stop retrying the same submit method. Report the blocker or use handoff-template for manual paste.",
    "",
    "Reason: some Codex DevTools tools reject chord strings like Control+Enter with Unknown key, even after the prompt was typed correctly."
  ) -join [Environment]::NewLine
}

function Get-DevToolsHealthText {
  $live = Get-LiveReportObject
  $pageCount = [int]$live.PageCount
  $ready = $live.Running -and $pageCount -gt 0
  $status = if ($ready) { "ready" } else { "not-ready" }
  $next = if ($ready) {
    "If antigravity-devtools still says Transport closed, do not retry the same MCP transport. Restart Codex so the DevTools MCP server is re-created, or use handoff-template/manual paste for this turn."
  } else {
    "Run repair-live once. If it restarts Antigravity, restart Codex before calling antigravity-devtools again."
  }

  @(
    "DevToolsHealth: $status",
    "Running: $($live.Running)",
    "DevToolsPort: $($live.DevToolsPort)",
    "PageCount: $pageCount",
    "Next: $next",
    "",
    "Rule: local helper commands can report health even when antigravity-devtools/list_pages fails with Transport closed."
  ) -join [Environment]::NewLine
}

function Get-OffloadAdviceText {
  $needsWorkspace = ConvertTo-BooleanValue -Value $HasWorkspaceWork -Default $true
  $decision = Get-OffloadDecisionObject -TaskGoal $Goal -NeedsWorkspace $needsWorkspace -EstimatedTokens $EstimatedCodexInputTokens
  @(
    "Decision: $($decision.Decision)",
    "Reason: $($decision.Reason)",
    "",
    "Rules:",
    "- Use Codex direct only for arithmetic, short factual answers, tiny commands, and small summaries.",
    "- Use Antigravity by default for nontrivial workspace tasks, UI/project continuation, job-search/application work, debugging, implementation, reviews, research, planning, and analysis that would make Codex read files or long output.",
    "- In existing project chats, assume Antigravity may scan attached folders. For small tests, use a blank/no-workspace chat when available or do not offload.",
    "- If Antigravity unexpectedly starts broad folder exploration for a small task, cancel and report that offload is not token-efficient.",
    "- When offloading, send a compact handoff and ask Antigravity to write a small status artifact; Codex should read only that artifact or a targeted diff."
  ) -join [Environment]::NewLine
}

function Get-PrepareOffloadText {
  $quick = Get-QuickReport | ConvertFrom-Json
  $needsWorkspace = ConvertTo-BooleanValue -Value $HasWorkspaceWork -Default $true
  $decision = Get-OffloadDecisionObject -TaskGoal $Goal -NeedsWorkspace $needsWorkspace -EstimatedTokens $EstimatedCodexInputTokens
  $recommended = $null
  if ($quick.Limits -and $quick.Limits.RecommendedAvailable -and @($quick.Limits.RecommendedAvailable).Count -gt 0) {
    $recommended = @($quick.Limits.RecommendedAvailable)[0]
  }

  $bestModel = if ($recommended) {
    "{0} ({1}% remaining)" -f $recommended.DisplayName, $recommended.RemainingPercent
  } else {
    "<unknown>"
  }

  $nextAction = if ($decision.ShouldOffload) {
    "Use antigravity-devtools only to select the project/chat/model, fill the handoff, and click the Send/arrow button. Then stop monitoring and read only the status artifact or targeted diff."
  } else {
    "Do not open or drive Antigravity for this task. Answer or act directly in Codex."
  }

  $handoff = Get-HandoffTemplateText -TaskGoal $Goal -TaskWorkspace $Workspace -TaskStatusFile $StatusFile -TaskNextStep $NextStep
  $handoff = $handoff -replace "^Use this as a compact Antigravity offload handoff:\r?\n\r?\n", ""

  @(
    "FastAntigravityOffloadPlan:",
    "Decision: $($decision.Decision)",
    "Reason: $($decision.Reason)",
    "",
    "Readiness:",
    "Installed: $($quick.Setup.Installed)",
    "Running: $($quick.Setup.Running)",
    "LiveReady: $($quick.Setup.ReadyForLiveUiInspection)",
    "PageCount: $($quick.Live.PageCount)",
    "BestModel: $bestModel",
    "",
    "NextAction:",
    $nextAction,
    "",
    "SubmitRule:",
    "Fill/type the prompt without submitKey. Prefer clicking the visible Send/arrow button. If keyboard submit is required, use a separate simple Enter key call. Never use Control+Enter unless the active tool schema explicitly accepts it.",
    "",
    "CompactHandoff:",
    $handoff
  ) -join [Environment]::NewLine
}

function Invoke-SubmitOffload {
  $submitValue = ConvertTo-BooleanValue -Value $Submit -Default $false
  $fillOnlyValue = ConvertTo-BooleanValue -Value $FillOnly -Default $false
  $localMcpScript = Join-Path $PSScriptRoot "antigravity-local-mcp.js"
  if (-not (Test-Path -LiteralPath $localMcpScript)) {
    throw "antigravity-local-mcp.js was not found at $localMcpScript"
  }

  $payload = [PSCustomObject]@{
    goal = $Goal
    workspace = $Workspace
    statusFile = $StatusFile
    nextStep = $NextStep
    expectedProject = $ExpectedProject
    expectedChat = $ExpectedChat
    submit = $submitValue
    fillOnly = $fillOnlyValue
  } | ConvertTo-Json -Compress

  $payloadFile = Join-Path ([System.IO.Path]::GetTempPath()) ("antigravity-submit-offload-{0}.json" -f ([guid]::NewGuid().ToString("N")))
  try {
    [System.IO.File]::WriteAllText($payloadFile, $payload, [System.Text.UTF8Encoding]::new($false))
    & node $localMcpScript submit-offload-cli --json-file $payloadFile
    if ($LASTEXITCODE -ne 0) {
      throw "submit-offload failed with exit code $LASTEXITCODE"
    }
  } finally {
    Remove-Item -LiteralPath $payloadFile -Force -ErrorAction SilentlyContinue
  }
}

function Write-Status {
  $processes = @(Get-AntigravityProcess)
  $devToolsPort = Get-DevToolsPort

  [PSCustomObject]@{
    Installed = Test-Path -LiteralPath $exePath
    ExePath = $exePath
    UserDataPath = $userDataPath
    Running = $processes.Count -gt 0
    ProcessIds = @($processes | Select-Object -ExpandProperty Id)
    DevToolsPort = $devToolsPort
  } | ConvertTo-Json -Depth 4
}

switch ($Command) {
  "path" {
    Write-Output $exePath
  }

  "status" {
    Write-Status
  }

  "open" {
    if (-not (Test-Path -LiteralPath $exePath)) {
      throw "Antigravity.exe was not found at $exePath"
    }

    $existing = @(Get-AntigravityProcess)
    if ($existing.Count -eq 0) {
      Start-Process -FilePath $exePath -WorkingDirectory $installRoot
      Start-Sleep -Seconds 2
    }

    Write-Status
  }

  "repair-live" {
    Repair-LiveDevTools | ConvertTo-Json -Depth 10
  }

  "inspect" {
    $packageFiles = @(
      Join-Path $installRoot "resources\app.asar.unpacked\node_modules\chrome-devtools-mcp\package.json"
    )

    $existingPackageFiles = @($packageFiles | Where-Object { Test-Path -LiteralPath $_ })
    $binPath = Join-Path $installRoot "resources\bin"
    $binFiles = @()
    if (Test-Path -LiteralPath $binPath) {
      $binFiles = @(Get-ChildItem -LiteralPath $binPath -File | Select-Object -ExpandProperty Name)
    }

    [PSCustomObject]@{
      InstallRoot = $installRoot
      ExePath = $exePath
      UserDataPath = $userDataPath
      DevToolsPort = Get-DevToolsPort
      BundledPackageFiles = $existingPackageFiles
      BinFiles = $binFiles
    } | ConvertTo-Json -Depth 5
  }

  "models" {
    Get-AntigravityModels
  }

  "limits" {
    Get-AntigravityModels
  }

  "limits-summary" {
    Get-LimitsSummary
  }

  "quick" {
    Get-QuickReport
  }

  "live" {
    Get-LiveReport
  }

  "devtools-health" {
    Get-DevToolsHealthText
  }

  "submission-guide" {
    Get-SubmissionGuideText
  }

  "offload-advice" {
    Get-OffloadAdviceText
  }

  "handoff-template" {
    Get-HandoffTemplateText -TaskGoal $Goal -TaskWorkspace $Workspace -TaskStatusFile $StatusFile -TaskNextStep $NextStep
  }

  "prepare-offload" {
    Get-PrepareOffloadText
  }

  "submit-offload" {
    Invoke-SubmitOffload
  }

  "setup" {
    Get-SetupReport
  }

  "doctor" {
    Get-SetupReport
  }

  "privacy" {
    Get-PrivacyReport
  }
}
