param(
    [ValidateSet('none', 'quick', 'named')]
    [string]$TunnelMode = 'none'
)
$ErrorActionPreference = 'Stop'
$needsCloudflared = $TunnelMode -in @('quick', 'named')

function Invoke-WinGetInstall([string]$PackageId) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) { throw "winget is required to install $PackageId automatically on Windows." }
    $output = & $winget.Source install --id $PackageId --exact --silent --accept-source-agreements --accept-package-agreements 2>&1
    $exitCode = $LASTEXITCODE
    foreach ($line in $output) { [Console]::Error.WriteLine([string]$line) }
    if ($exitCode -ne 0) { throw "winget failed to install $PackageId (exit $exitCode)." }
}

function Get-PythonRuntime {
    $candidates = [Collections.Generic.List[object]]::new()
    $windowsAppsRoots = @(
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps'),
        (Join-Path $env:ProgramFiles 'WindowsApps')
    ) | Where-Object { $_ }

    function Test-IsWindowsAppsAlias([string]$Path) {
        if (-not $Path) { return $false }
        $fullPath = [IO.Path]::GetFullPath($Path)
        foreach ($root in $windowsAppsRoots) {
            $fullRoot = [IO.Path]::GetFullPath($root).TrimEnd('\') + '\'
            if ($fullPath.StartsWith($fullRoot, [StringComparison]::OrdinalIgnoreCase)) { return $true }
        }
        return $false
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        foreach ($versionArg in @('-3.13', '-3.12', '-3.11')) {
            $candidates.Add([pscustomobject]@{ Exe = $py.Source; Args = @($versionArg) })
        }
    }
    foreach ($name in @('python3.13', 'python3.12', 'python3.11', 'python3', 'python')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        # WindowsApps execution aliases can throw from native stdout redirection
        # before Python starts. Ignore these aliases and continue to real runtimes.
        if ($cmd -and -not (Test-IsWindowsAppsAlias $cmd.Source)) {
            $candidates.Add([pscustomobject]@{ Exe = $cmd.Source; Args = @() })
        }
    }
    foreach ($path in @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:ProgramFiles\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:ProgramFiles\Python311\python.exe"
    )) {
        if (Test-Path -LiteralPath $path) { $candidates.Add([pscustomobject]@{ Exe = $path; Args = @() }) }
    }
    foreach ($candidate in $candidates) {
        $prefix = $candidate.Args
        # Keep Python source free of nested quotes. Windows PowerShell 5.1
        # strips them while rebuilding native command-line arguments.
        $version = & $($candidate.Exe) @prefix -c 'import sys; print(sys.version_info[0], sys.version_info[1], sep=chr(46))' 2>$null
        if ($LASTEXITCODE -eq 0 -and $version -match '^\d+\.\d+$') {
            $parts = $version -split '\.' | ForEach-Object { [int]$_ }
            if (($parts[0] -gt 3) -or ($parts[0] -eq 3 -and $parts[1] -ge 11)) {
                $actualExe = & $($candidate.Exe) @prefix -c 'import sys; print(sys.executable)' 2>$null
                if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $actualExe)) {
                    return @{ exe = $actualExe; args = @(); version = $version }
                }
            }
        }
    }
    return $null
}

function Get-InstalledCommand([string]$Name, [string[]]$Paths) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command }
    foreach ($path in $Paths) {
        if (Test-Path -LiteralPath $path) { return @{ Source = $path } }
    }
    return $null
}

$python = Get-PythonRuntime
if (-not $python) {
    Invoke-WinGetInstall 'Python.Python.3.13'
    $python = Get-PythonRuntime
    if (-not $python) { throw 'Python 3.13 installed but no supported Python runtime was found in this shell.' }
}

$gitCmd = Get-InstalledCommand 'git' @(
    "$env:ProgramFiles\Git\cmd\git.exe",
    "${env:ProgramFiles(x86)}\Git\cmd\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
)
if (-not $gitCmd) {
    Invoke-WinGetInstall 'Git.Git'
    $gitCmd = Get-InstalledCommand 'git' @(
        "$env:ProgramFiles\Git\cmd\git.exe",
        "${env:ProgramFiles(x86)}\Git\cmd\git.exe",
        "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
    )
    if (-not $gitCmd) { throw 'Git installed but not available in this shell. Restart the terminal and run MCP setup again.' }
}

$cloudflared = $null
if ($needsCloudflared) {
    $cloudflared = Get-InstalledCommand 'cloudflared' @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links\cloudflared.exe",
        "$env:ProgramFiles\cloudflared\cloudflared.exe",
        "${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe"
    )
    if (-not $cloudflared) {
        Invoke-WinGetInstall 'Cloudflare.cloudflared'
        $cloudflared = Get-InstalledCommand 'cloudflared' @(
            "$env:LOCALAPPDATA\Microsoft\WinGet\Links\cloudflared.exe",
            "$env:ProgramFiles\cloudflared\cloudflared.exe",
            "${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe"
        )
        if (-not $cloudflared) { throw 'cloudflared installed but not available in this shell. Restart the terminal and run MCP setup again.' }
    }
}

$repo = $env:CHATGPT_AGENT_SOURCE
if (-not $repo -and (Test-Path -LiteralPath (Join-Path (Get-Location) 'agentctl.py'))) { $repo = (Get-Location).Path }
if (-not $repo) {
    $candidate = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    if (Test-Path -LiteralPath (Join-Path $candidate 'agentctl.py')) { $repo = $candidate }
}
if ($repo) { $repo = (Resolve-Path -LiteralPath $repo).Path }

if (-not $repo) {
    $stateHome = Join-Path $env:LOCALAPPDATA 'chatgpt-agent'
    $repo = Join-Path $stateHome 'package'
    if (Test-Path -LiteralPath (Join-Path $repo '.git')) {
        $status = & $gitCmd.Source -C $repo status --porcelain
        if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the installed Bridge package.' }
        if ($status) { throw "The installed Bridge package has local changes at $repo; review them before updating." }
        $output = & $gitCmd.Source -C $repo pull --ff-only 2>&1
        $exitCode = $LASTEXITCODE
        foreach ($line in $output) { [Console]::Error.WriteLine([string]$line) }
        if ($exitCode -ne 0) { throw 'Could not update the installed Bridge package with a fast-forward.' }
    } elseif (Test-Path -LiteralPath $repo) {
        throw "The Bridge install path exists but is not a Git checkout: $repo"
    } else {
        $parent = Split-Path -Parent $repo
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        $ref = $env:CHATGPT_AGENT_REF
        if ($ref) {
            $output = & $gitCmd.Source clone --depth 1 --branch $ref 'https://github.com/TohmaN233/chatgpt-review-agent-skill.git' $repo 2>&1
        } else {
            $output = & $gitCmd.Source clone --depth 1 'https://github.com/TohmaN233/chatgpt-review-agent-skill.git' $repo 2>&1
        }
        $exitCode = $LASTEXITCODE
        foreach ($line in $output) { [Console]::Error.WriteLine([string]$line) }
        if ($exitCode -ne 0) { throw 'Could not download the Bridge package from GitHub.' }
    }
}

foreach ($required in @('agentctl.py', 'mcp_server.py', 'cloudflare_tunnel.py')) {
    if (-not (Test-Path -LiteralPath (Join-Path $repo $required))) { throw "Bridge package is incomplete: $required is missing from $repo" }
}

$cloudflaredPath = if ($cloudflared) { $cloudflared.Source } else { $null }
[ordered]@{ repository = $repo; python = $python; tunnel_mode = $TunnelMode; cloudflared = $cloudflaredPath } | ConvertTo-Json -Compress
