# install_edit.ps1: install the command-line tools of the optional brief2mp4 edit pack on Windows. No admin rights needed.
#
#   powershell -ExecutionPolicy Bypass -File install_edit.ps1                              # film + sound
#   powershell -ExecutionPolicy Bypass -File install_edit.ps1 -Components film,sound,effect,photo,vector
#   powershell -ExecutionPolicy Bypass -File install_edit.ps1 -Components all -DryRun      # show the plan, change nothing
#   powershell -ExecutionPolicy Bypass -File install_edit.ps1 -Uninstall                   # remove what this installer created
#   powershell -ExecutionPolicy Bypass -File install_edit.ps1 -Uninstall -Components photo
#
# Components (free ArtCraft apps by storytold, MIT or Apache-2.0, pinned in versions.json)
#   film FilmCraft, sound SoundCraft, effect EffectCraft, photo PhotoCraft, vector VectorCraft
#
# Each download is checked against the release's SHA256SUMS.txt and the hash pinned in versions.json.
# When gpg is installed, the signature on SHA256SUMS.txt is checked too (skipped, and said so, otherwise).
# Installs into $env:B2M_EDIT_HOME (default %USERPROFILE%\.brief2mp4\edit), copying versions.json and the
# recipes there. Safe to run again. Never touches the system PATH: it prints the line you can add.
[CmdletBinding()]
param(
    [string[]]$Components = @("film", "sound"),
    [switch]$DryRun,
    [switch]$Uninstall
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }

$Pack = Split-Path -Parent $MyInvocation.MyCommand.Path
$HomeDir = if ($env:B2M_EDIT_HOME) { $env:B2M_EDIT_HOME } else { Join-Path $env:USERPROFILE ".brief2mp4\edit" }
$Manifest = Join-Path $HomeDir ".b2m-edit-manifest"
$All = @("film", "sound", "effect", "photo", "vector")
$Utf8 = New-Object System.Text.UTF8Encoding($false)

# Both `-Components film,sound` (an array) and `-File ... -Components film,sound` (one string) arrive here.
$explicit = $PSBoundParameters.ContainsKey("Components")
$wanted = @($Components | ForEach-Object { $_ -split "[,\s]+" } | Where-Object { $_ } | ForEach-Object { $_.ToLowerInvariant() })
if ($wanted -contains "all") { $wanted = $All }
if ($wanted.Count -eq 0) { throw "-Components needs a value (film, sound, effect, photo, vector, all)" }
foreach ($c in $wanted) { if ($All -notcontains $c) { throw "unknown component '$c' (film, sound, effect, photo, vector, all)" } }
$wanted = @($wanted | Select-Object -Unique)

$Versions = ConvertFrom-Json ([System.IO.File]::ReadAllText((Join-Path $Pack "versions.json"), $Utf8))

function Get-PlatformKey {
    if ($env:B2M_EDIT_PLATFORM) { return $env:B2M_EDIT_PLATFORM }   # test hook
    if ((Get-Variable IsWindows -ErrorAction SilentlyContinue) -and -not $IsWindows) { throw "this is not Windows: run install_edit.sh instead" }
    $arch = ""
    try { $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString() } catch { }
    if (-not $arch) { $arch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE } }
    switch -Regex ($arch) {
        "^(X64|AMD64)$" { return "windows-x64" }
        "^ARM64$" { return "windows-arm64" }
        default { throw "no pinned build for Windows $arch (x64 and arm64 only)" }
    }
}

function Get-SizeMB([string]$path) {
    if (-not (Test-Path $path)) { return 0 }
    $item = Get-Item $path
    if (-not $item.PSIsContainer) { return [int]($item.Length / 1MB) }
    $sum = (Get-ChildItem -Path $path -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    return [int](($sum + 0) / 1MB)
}

# Runs a program through .NET so its stderr never becomes a terminating error (Windows PowerShell 5.1 turns
# redirected native stderr into one under $ErrorActionPreference = "Stop"). Returns exit code and stdout.
function Invoke-Native([string]$file, [string[]]$arguments, [hashtable]$environment = @{}) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $file
    $psi.Arguments = ($arguments | ForEach-Object { if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ } }) -join " "
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    foreach ($k in $environment.Keys) { $psi.EnvironmentVariables[$k] = $environment[$k] }
    try { $p = [System.Diagnostics.Process]::Start($psi) } catch { return [pscustomobject]@{ ExitCode = -1; Output = ""; Error = $_.Exception.Message } }
    $errTask = $p.StandardError.ReadToEndAsync()   # read both pipes at once, so neither can fill up and block
    $out = $p.StandardOutput.ReadToEnd()
    $p.WaitForExit()
    return [pscustomobject]@{ ExitCode = $p.ExitCode; Output = $out; Error = $errTask.Result }
}

function Add-ToManifest([string]$rel) {
    $lines = @()
    if (Test-Path $Manifest) { $lines = @([System.IO.File]::ReadAllLines($Manifest, $Utf8) | Where-Object { $_ }) }
    if ($lines -notcontains $rel) { [System.IO.File]::WriteAllLines($Manifest, @($lines + $rel), $Utf8) }
}

function Test-InManifest([string]$rel) {
    if (-not (Test-Path $Manifest)) { return $false }
    return @([System.IO.File]::ReadAllLines($Manifest, $Utf8)) -contains $rel
}

function Set-Claim([string]$rel) {
    # Before writing a path, move aside anything there that this installer did not create.
    $p = Join-Path $HomeDir $rel
    if ((Test-Path -LiteralPath $p) -and -not (Test-InManifest $rel)) {
        $aside = "$p.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Move-Item -LiteralPath $p -Destination $aside
        Write-Output "  kept your existing $rel at $aside (it was not created by this installer)"
    }
}

function Test-Hash([string]$file, [string]$asset, [string]$sums, [string]$pinned) {
    $line = [System.IO.File]::ReadAllLines($sums, $Utf8) | Where-Object { ($_ -split "\s+")[1] -eq $asset } | Select-Object -First 1
    if (-not $line) { throw "$asset is not listed in the release's SHA256SUMS.txt" }
    $listed = ($line -split "\s+")[0].ToLowerInvariant()
    if ($listed -ne $pinned.ToLowerInvariant()) { throw "SHA-256 in the release ($listed) differs from the one pinned in versions.json ($pinned). Refusing to install." }
    $actual = (Get-FileHash -Algorithm SHA256 -Path $file).Hash.ToLowerInvariant()
    if ($actual -ne $pinned.ToLowerInvariant()) { throw "SHA-256 mismatch for ${asset}: got $actual, expected $pinned." }
    Write-Output "  sha-256: OK ($asset)"
}

function Test-Signature([string]$dir, [string]$fingerprint) {
    $gpg = Get-Command gpg -ErrorAction SilentlyContinue
    if (-not $gpg) {
        Write-Output "  signature: SKIPPED (gpg not installed; the SHA-256 checks above still ran. Install Gpg4win to check the release signature too)"
        return
    }
    $gh = Join-Path ([System.IO.Path]::GetTempPath()) ("b2m-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
    New-Item -ItemType Directory -Force -Path $gh | Out-Null
    try {
        # Git for Windows ships an MSYS build of gpg that reads C:\x\y as a relative path and wants /c/x/y.
        # Gpg4win (native) wants ordinary Windows paths. Convert to whichever this gpg understands.
        $msys = $gpg.Source -match '\\usr\\bin\\gpg(\.exe)?$'
        $conv = { param([string]$p) if ($msys -and $p -match '^([A-Za-z]):[\\/](.*)$') { "/" + $Matches[1].ToLowerInvariant() + "/" + ($Matches[2] -replace '\\', '/') } else { $p } }
        $home2 = & $conv $gh
        $key = & $conv (Join-Path $dir "release-signing-key.asc")
        $sig = & $conv (Join-Path $dir "SHA256SUMS.txt.asc")
        $sums = & $conv (Join-Path $dir "SHA256SUMS.txt")
        $imp = Invoke-Native $gpg.Source @("--homedir", $home2, "--batch", "--quiet", "--import", $key)
        $ver = Invoke-Native $gpg.Source @("--homedir", $home2, "--batch", "--status-fd", "1", "--verify", $sig, $sums)
        $ok = $ver.Output -split "`n" | Where-Object { $_ -like "*VALIDSIG *" -and ($_.Trim() -split " ")[-1] -eq $fingerprint }
        if (-not $ok) {
            Write-Output "  gpg ($($gpg.Source)) import: exit $($imp.ExitCode) $($imp.Error.Trim())"
            Write-Output "  gpg verify: exit $($ver.ExitCode) $($ver.Error.Trim())"
            throw "the signature on SHA256SUMS.txt did not verify against the pinned key $fingerprint. Nothing was installed."
        }
        Write-Output ("  signature: OK (SHA256SUMS.txt signed by key " + $fingerprint.Substring(0, 8) + "..." + $fingerprint.Substring($fingerprint.Length - 8) + ")")
    } finally { Remove-Item -Recurse -Force $gh -ErrorAction SilentlyContinue }
}

function Install-App([string]$app, [string]$plat, [string]$stage) {
    $a = $Versions.apps.$app
    $asset = $a.assets.$plat
    if (-not $asset) { throw "$($a.name) $($a.version) has no build for $plat" }
    $url = "$($Versions.source)/$($a.name)/releases/download/$($a.tag)"
    $dest = Join-Path $HomeDir $a.name
    $cli = Join-Path $dest "$($a.name)-cli.exe"
    $mb = [math]::Round($asset.bytes / 1MB, 1)
    if ($DryRun) { Write-Output "${app}: $($a.name) $($a.version) ($plat) would download $($asset.file), $mb MB, from $url/$($asset.file)"; return }
    $stamp = Join-Path $dest ".b2m-version"
    if ((Test-Path $cli) -and (Test-Path $stamp) -and (([System.IO.File]::ReadAllText($stamp, $Utf8)).Trim() -eq $a.version)) {
        Write-Output "${app}: $($a.name) $($a.version) already installed ($(Get-SizeMB $dest) MB at $dest)"
        Write-Launcher $a; Add-ToManifest $a.name; return
    }
    Write-Output "${app}: downloading $($a.name) $($a.version) ($mb MB) for $plat"
    Invoke-WebRequest -UseBasicParsing -Uri "$url/$($asset.file)" -OutFile (Join-Path $stage $asset.file)
    foreach ($f in @("SHA256SUMS.txt", "SHA256SUMS.txt.asc", "release-signing-key.asc")) {
        Invoke-WebRequest -UseBasicParsing -Uri "$url/$f" -OutFile (Join-Path $stage $f)
    }
    Test-Hash (Join-Path $stage $asset.file) $asset.file (Join-Path $stage "SHA256SUMS.txt") $asset.sha256
    Test-Signature $stage $Versions.signing.fingerprint
    $x = Join-Path $stage "x-$app"
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory((Join-Path $stage $asset.file), $x)
    $tops = @(Get-ChildItem -LiteralPath $x -Directory | Where-Object { $_.Name -ne "__MACOSX" })
    if ($tops.Count -ne 1) { throw "$($asset.file) should hold exactly one top-level folder; found $($tops.Count)" }
    Set-Claim $a.name
    $old = "$dest.old"
    if (Test-Path -LiteralPath $old) { Remove-Item -LiteralPath $old -Recurse -Force }
    # Keep the previous version until the new one proves it runs, so a failed upgrade loses nothing.
    if (Test-Path -LiteralPath $dest) { Move-Item -LiteralPath $dest -Destination $old }
    Move-Item -LiteralPath $tops[0].FullName -Destination $dest
    Get-ChildItem -LiteralPath $dest -Recurse -File | Unblock-File -ErrorAction SilentlyContinue
    Write-Output "  windows: cleared any download block flag on the files (Unblock-File)"
    $ver = Invoke-Native $cli @("--version")
    if ($ver.ExitCode -ne 0) {
        Remove-Item -LiteralPath $dest -Recurse -Force
        if (Test-Path -LiteralPath $old) { Move-Item -LiteralPath $old -Destination $dest }
        throw "$cli was installed but does not run, so the previous version (if any) was kept. Try: & `"$cli`" --version"
    }
    if (Test-Path -LiteralPath $old) { Remove-Item -LiteralPath $old -Recurse -Force }
    [System.IO.File]::WriteAllText($stamp, $a.version + "`n", $Utf8)
    Write-Launcher $a; Add-ToManifest $a.name
    Write-Output "${app}: done, $(($ver.Output -split "`n")[0].Trim()), $(Get-SizeMB $dest) MB on disk"
}

function Write-Launcher($a) {
    # Relative to the .cmd, so the folder can move. Pure ASCII, so any user name works.
    New-Item -ItemType Directory -Force -Path (Join-Path $HomeDir "bin") | Out-Null
    Set-Claim "bin/$($a.name)-cli.cmd"
    $text = "@echo off`r`n`"%~dp0..\$($a.name)\$($a.name)-cli.exe`" %*`r`n"
    [System.IO.File]::WriteAllText((Join-Path $HomeDir "bin\$($a.name)-cli.cmd"), $text, (New-Object System.Text.UTF8Encoding($false)))
    Add-ToManifest "bin/$($a.name)-cli.cmd"
}

function Copy-SupportFiles {
    Set-Claim "versions.json"; Set-Claim "recipes"
    Copy-Item (Join-Path $Pack "versions.json") (Join-Path $HomeDir "versions.json") -Force
    $rec = Join-Path $HomeDir "recipes"
    if (Test-Path $rec) { Remove-Item -Recurse -Force $rec }
    New-Item -ItemType Directory -Force -Path $rec | Out-Null
    Copy-Item (Join-Path $Pack "recipes\*") $rec -Force
    Add-ToManifest "versions.json"; Add-ToManifest "recipes"
}

function Invoke-Uninstall {
    if (-not (Test-Path $Manifest)) { Write-Output "nothing to remove: $HomeDir has no edit-pack manifest (this installer created nothing there)"; return }
    $names = @(); foreach ($c in $wanted) { $names += $Versions.apps.$c.name; $names += "bin/$($Versions.apps.$c.cli).cmd" }
    $keep = @(); $freed = 0
    foreach ($rel in [System.IO.File]::ReadAllLines($Manifest, $Utf8)) {
        if (-not $rel) { continue }
        if ($rel -notmatch '^[A-Za-z0-9._][A-Za-z0-9._/-]*$' -or $rel -like "*..*") { Write-Output "skipping unsafe manifest entry: $rel"; $keep += $rel; continue }
        if ($explicit -and ($names -notcontains $rel)) { $keep += $rel; continue }
        $target = Join-Path $HomeDir ($rel -replace "/", "\")
        if (Test-Path $target) { $freed += Get-SizeMB $target; Remove-Item -Recurse -Force $target; Write-Output "removed $target" }
    }
    $support = @("versions.json", "recipes", ".components")
    $apps = @($keep | Where-Object { $support -notcontains $_ })
    if ($explicit -and $apps.Count -eq 0) {
        # The last app is gone: take the shared files this installer made too.
        foreach ($rel in $keep) {
            $t = Join-Path $HomeDir $rel
            if (Test-Path $t) { Remove-Item -Recurse -Force $t; Write-Output "removed $t" }
        }
        $keep = @()
    }
    if ($keep.Count -gt 0) {
        [System.IO.File]::WriteAllLines($Manifest, $keep, $Utf8)
        $marker = Join-Path $HomeDir ".components"
        if ($explicit -and (Test-Path $marker)) {
            $left = @([System.IO.File]::ReadAllLines($marker, $Utf8) | Where-Object { $_ -and ($wanted -notcontains $_) })
            [System.IO.File]::WriteAllLines($marker, $left, $Utf8)
        }
    } else {
        Remove-Item -Force $Manifest -ErrorAction SilentlyContinue
        foreach ($d in @((Join-Path $HomeDir "bin"), $HomeDir)) { if ((Test-Path $d) -and -not (Get-ChildItem -Force $d)) { Remove-Item -Force $d } }
    }
    Write-Output "uninstall done, about $freed MB freed. Anything else in $HomeDir was not created by this installer and was left alone."
}

if ($Uninstall) { Invoke-Uninstall; exit 0 }

$plat = Get-PlatformKey
$stage = $null
if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $HomeDir | Out-Null
    $stage = Join-Path $HomeDir (".stage-" + $PID)
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
}
try {
    Write-Output "brief2mp4 edit pack: ArtCraft apps by storytold (MIT or Apache-2.0), alpha software, versions pinned in versions.json"
    foreach ($app in $wanted) { Install-App $app $plat $stage }
    if (-not $DryRun) {
        Copy-SupportFiles
        $marker = Join-Path $HomeDir ".components"
        $all = @()
        if (Test-Path $marker) { $all += [System.IO.File]::ReadAllLines($marker, $Utf8) }
        $all = @($all + $wanted | Where-Object { $_ } | Sort-Object -Unique)
        [System.IO.File]::WriteAllLines($marker, $all, $Utf8)
        Add-ToManifest ".components"
        Write-Output ("installed components: " + ($all -join ",") + "   total on disk: $(Get-SizeMB $HomeDir) MB in $HomeDir")
        Write-Output "launchers are in $HomeDir\bin and recipes in $HomeDir\recipes. To type the launchers anywhere, run this yourself (this script does not):"
        Write-Output "  [Environment]::SetEnvironmentVariable('Path', '$HomeDir\bin;' + [Environment]::GetEnvironmentVariable('Path', 'User'), 'User')"
        Write-Output "to remove everything this installer created: install_edit.ps1 -Uninstall"
    }
} finally {
    if ($stage -and (Test-Path $stage)) { Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue }
}
