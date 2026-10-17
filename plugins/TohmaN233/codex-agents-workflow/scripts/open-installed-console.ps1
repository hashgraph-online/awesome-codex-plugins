$ErrorActionPreference = 'Stop'
$consoleArguments = @($args)
try {
    $registryText = (& codex plugin list --marketplace codex-agents-workflow --json | Out-String)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read the installed plugin registry.' }
    $registry = $registryText | ConvertFrom-Json
    $installed = @($registry.installed | Where-Object { $_.pluginId -eq 'codex-agents-workflow@codex-agents-workflow' -and $_.installed })
    if ($installed.Count -ne 1) { throw 'Expected exactly one installed codex-agents-workflow plugin.' }
    $version = [string]$installed[0].version
    if ($version -notmatch '^[0-9][A-Za-z0-9.+_-]*$') { throw 'Invalid installed plugin version.' }
    $codexDirectory = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
    $pluginRoot = Join-Path $codexDirectory "plugins/cache/codex-agents-workflow/codex-agents-workflow/$version"
    $entry = Join-Path $pluginRoot 'control-plane/open-console.mjs'
    foreach ($required in @($entry, (Join-Path $pluginRoot 'control-plane/web/workflows.html'))) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Installed plugin is incomplete. Reinstall codex-agents-workflow. Missing: $required" }
    }
    $port = 58712
    $portIndex = [Array]::IndexOf($consoleArguments, '--port')
    if ($portIndex -ge 0) {
        if ($portIndex + 1 -ge $consoleArguments.Count -or $consoleArguments[$portIndex + 1] -notmatch '^[0-9]+$') { throw 'Invalid --port.' }
        $port = [int]$consoleArguments[$portIndex + 1]
        if ($port -lt 1 -or $port -gt 65535) { throw 'Use a fixed port between 1 and 65535.' }
    }
    if ($consoleArguments -notcontains '--help' -and $consoleArguments -notcontains '-h') {
        $listeners = @(Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -eq $port })
        $owners = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
        $verified = @()
        $cachePrefix = [IO.Path]::GetFullPath((Join-Path $codexDirectory 'plugins/cache/codex-agents-workflow/codex-agents-workflow')).Replace('\','/').TrimEnd('/') + '/'
        foreach ($ownerId in $owners) {
            $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerId"
            $command = [string]$owner.CommandLine
            if ($owner.Name -ne 'node.exe' -or $command -notmatch '^(?:"[^"\r\n]+"|\S+)\s+(?:"(?<entry>[^"\r\n]+)"|(?<entry>\S+))(?:\s.*)?$') { throw "Port $port is owned by an unrecognized process $ownerId; nothing was stopped." }
            $runningEntry = $Matches['entry'].Replace('\','/')
            $allowed = '^' + [regex]::Escape($cachePrefix) + '[0-9][A-Za-z0-9.+_-]*/control-plane/open-console\.mjs$'
            if ($runningEntry -notmatch $allowed) { throw "Port $port belongs to another program ($ownerId); nothing was stopped." }
            $verified += $owner
        }
        foreach ($owner in $verified) {
            $again = Get-CimInstance Win32_Process -Filter "ProcessId=$($owner.ProcessId)"
            if (-not $again -or $again.CreationDate -ne $owner.CreationDate -or $again.CommandLine -cne $owner.CommandLine) { throw 'Console process identity changed; retry launch.' }
            Write-Host "Stopping previous Workflow console PID $($owner.ProcessId) on port $port."
            Stop-Process -Id $owner.ProcessId -ErrorAction Stop
            $process = Get-Process -Id $owner.ProcessId -ErrorAction SilentlyContinue
            if ($process) { $process | Wait-Process -Timeout 10 -ErrorAction Stop }
        }
        if (@(Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -eq $port }).Count) { throw "Port $port is still occupied; console was not started." }
    }
    & node $entry @consoleArguments
    exit $LASTEXITCODE
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
