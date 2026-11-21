# install_3d.ps1: install components of the optional brief2mp4 3D pack on Windows. No admin rights needed.
#
#   powershell -ExecutionPolicy Bypass -File install_3d.ps1                       # core only
#   powershell -ExecutionPolicy Bypass -File install_3d.ps1 -Components core,cad  # pick what the brief needs
#   powershell -ExecutionPolicy Bypass -File install_3d.ps1 -Uninstall            # remove the install folder (only if this script made it)
#
# Components
#   core     node: three, GSAP, glTF Transform, meshoptimizer, Jolt, fonts
#            python: numpy, scipy, trimesh, manifold3d (in a venv, Python 3.12 or 3.13)
#   cad      CadQuery (large: ships the OpenCascade kernel). Needs core.
#   blender  checks for a system Blender and prints how to install it. Installs nothing.
#   dev      pytest, for tests\run_tests.sh. Needs core.
#
# Installs into $env:B2M3D_HOME (default $env:USERPROFILE\.brief2mp4\3d), including its own copy of the pack,
# so moving or deleting the folder you ran this from does not break it. Safe to run again.
param([string[]]$Components = @("core"), [switch]$Uninstall)
$ErrorActionPreference = "Stop"

$Pack = Split-Path -Parent $MyInvocation.MyCommand.Path
$HomeDir = if ($env:B2M3D_HOME) { $env:B2M3D_HOME } else { Join-Path $env:USERPROFILE ".brief2mp4\3d" }
$Venv = Join-Path $HomeDir "venv"
$VPy = Join-Path $Venv "Scripts\python.exe"

$Marker = Join-Path $HomeDir ".installed-by-brief2mp4-3d"
# Only these entries are ever created in $HomeDir. Uninstall removes exactly these, then the folder
# itself only if nothing else is left in it.
$Owned = @("venv", "node_modules", "pack", "js", "package.json", "package-lock.json", ".node-stamp", ".components", ".installed-by-brief2mp4-3d")
if ($Uninstall) {
    if (-not (Test-Path $HomeDir)) { Write-Output "nothing to remove at $HomeDir"; exit 0 }
    if (-not (Test-Path $Marker)) { throw "$HomeDir was not created by this script; left it alone" }
    foreach ($e in $Owned) { $p = Join-Path $HomeDir $e; if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force } }
    if (@(Get-ChildItem -LiteralPath $HomeDir -Force).Count -eq 0) { Remove-Item -LiteralPath $HomeDir -Force; Write-Output "removed $HomeDir" }
    else { Write-Output "removed the 3D pack from $HomeDir; other files in it were left alone" }
    exit 0
}
# Never adopt a folder that already holds someone else's files: the marker would let uninstall touch it.
if ((Test-Path $HomeDir) -and -not (Test-Path $Marker) -and (@(Get-ChildItem -LiteralPath $HomeDir -Force).Count -gt 0)) {
    throw "$HomeDir already exists and was not created by this installer. Set B2M3D_HOME to a new or empty folder."
}
# Accept "-Components core,cad" (an array), "core cad" or "core,cad" (one string) alike.
$wanted = @($Components | ForEach-Object { $_ -split "[,\s]+" } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($wanted.Count -eq 0) { throw "-Components needs a value, e.g. core,cad" }
foreach ($c in $wanted) {
    if (@("core", "cad", "blender", "dev") -notcontains $c) { throw "unknown component '$c' (core, cad, blender, dev)" }
}
if ((($wanted -contains "cad") -or ($wanted -contains "dev")) -and ($wanted -notcontains "core")) { $wanted = @("core") + $wanted }

function Get-SizeMB([string]$path) {
    if (-not (Test-Path $path)) { return 0 }
    $sum = (Get-ChildItem -Path $path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    return [int](($sum + 0) / 1MB)
}

function Find-Python {
    if ($env:B2M3D_PYTHON) { return ,@($env:B2M3D_PYTHON) }
    $candidates = @(@("py", "-3.13"), @("py", "-3.12"), @("python"), @("python3"))
    foreach ($cand in $candidates) {
        if (-not (Get-Command $cand[0] -ErrorAction SilentlyContinue)) { continue }
        $extra = @($cand | Select-Object -Skip 1)
        try { $v = (& $cand[0] @extra -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null) } catch { continue }
        if (@("3.12", "3.13") -contains $v) { return ,$cand }
    }
    return $null
}

function Invoke-Checked([scriptblock]$block, [string]$what) {
    & $block
    if ($LASTEXITCODE -ne 0) { throw "$what failed (exit $LASTEXITCODE)" }
}

function Install-NodePackages {
    Write-Output "core: installing three, gsap, glTF Transform, meshoptimizer, jolt-physics, fonts"
    Copy-Item (Join-Path $Pack "package.json") (Join-Path $HomeDir "package.json") -Force
    $lockSrc = Join-Path $Pack "package-lock.json"
    $lock = Join-Path $HomeDir "package-lock.json"
    if (Test-Path $lockSrc) { Copy-Item $lockSrc $lock -Force }
    $stampFile = Join-Path $HomeDir ".node-stamp"
    $stamp = (Get-FileHash (Join-Path $HomeDir "package.json")).Hash
    if (Test-Path $lock) { $stamp += (Get-FileHash $lock).Hash }
    if ((Test-Path (Join-Path $HomeDir "node_modules\three")) -and (Test-Path $stampFile) -and ((Get-Content $stampFile -Raw).Trim() -eq $stamp)) {
        Write-Output "core: node packages already up to date"
        return
    }
    Push-Location $HomeDir
    try {
        $verb = if (Test-Path $lock) { "ci" } else { "install" }
        Invoke-Checked { npm.cmd $verb --omit=dev --no-audit --no-fund --loglevel=error } "npm $verb"
    } finally { Pop-Location }
    $stamp = (Get-FileHash (Join-Path $HomeDir "package.json")).Hash
    if (Test-Path $lock) { $stamp += (Get-FileHash $lock).Hash }
    Set-Content -Path $stampFile -Value $stamp
}

function Write-Utf8([string]$path, [string]$text) {
    [System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding $false))
}

function Link-Pack {
    # Copy the pack into the install home and point a .pth file at the copy, so `python -m b2m3d`
    # works from any folder and keeps working if the clone or plugin cache moves.
    $dest = Join-Path $HomeDir "pack"
    $tmp = "$dest.new"
    if (Test-Path $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    foreach ($part in @("b2m3d", "js", "templates", "presets", "examples")) {
        $src = Join-Path $Pack $part
        if (Test-Path $src) { Copy-Item -Recurse -Path $src -Destination $tmp }
    }
    Get-ChildItem -Path $tmp -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    if (Test-Path $dest) { Remove-Item -LiteralPath $dest -Recurse -Force }
    Move-Item -LiteralPath $tmp -Destination $dest
    $site = (& $VPy -c "import sysconfig; print(sysconfig.get_paths()['purelib'])").Trim()
    Write-Utf8 (Join-Path $site "b2m3d-pack.pth") "$dest`n"
    Write-Utf8 (Join-Path $Venv "Scripts\brief2mp4-3d.cmd") "@echo off`r`n`"$VPy`" -m b2m3d %*`r`n"
    Invoke-Checked { & $VPy -c "import b2m3d.cli" } "importing the pack copy in $dest"
    Write-Output "core: command ready: $Venv\Scripts\brief2mp4-3d.cmd   (or: $VPy -m b2m3d)"
}

function Install-Core {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "node not found. Install Node.js 22 or newer: winget install OpenJS.NodeJS.LTS" }
    if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw "npm not found. It ships with Node.js: https://nodejs.org" }
    $major = [int](node -p "process.versions.node.split('.')[0]")
    if ($major -lt 22) { throw "Node.js $major is too old: 22 or newer is needed." }
    $py = Find-Python
    if (-not $py) { throw "Python 3.12 or 3.13 not found. Install it: winget install Python.Python.3.13 (then open a new terminal)." }

    New-Item -ItemType Directory -Force -Path $HomeDir | Out-Null
    Write-Utf8 $Marker "brief2mp4 3D pack`n"
    $before = (Get-SizeMB $Venv) + (Get-SizeMB (Join-Path $HomeDir "node_modules"))
    Write-Output "core: python venv ($($py -join ' ')) at $Venv"
    if (-not (Test-Path $VPy)) {
        $extra = @($py | Select-Object -Skip 1)
        Invoke-Checked { & $py[0] @extra -m venv $Venv } "venv creation"
    }
    Write-Output "core: installing numpy, scipy, trimesh, manifold3d"
    Invoke-Checked { & $VPy -m pip install --disable-pip-version-check -q -r (Join-Path $Pack "requirements-core.txt") } "pip install (core)"
    Install-NodePackages
    Link-Pack
    $after = (Get-SizeMB $Venv) + (Get-SizeMB (Join-Path $HomeDir "node_modules"))
    Write-Output "core: done, $($after - $before) MB added (venv $(Get-SizeMB $Venv) MB, node_modules $(Get-SizeMB (Join-Path $HomeDir 'node_modules')) MB)"
}

function Install-Cad {
    $before = Get-SizeMB $Venv
    Write-Output "cad: installing CadQuery (large download)"
    Invoke-Checked { & $VPy -m pip install --disable-pip-version-check -q -r (Join-Path $Pack "requirements-cad.txt") } "pip install (cad)"
    Write-Output "cad: done, $((Get-SizeMB $Venv) - $before) MB added"
}

function Install-Dev {
    Write-Output "dev: installing pytest"
    Invoke-Checked { & $VPy -m pip install --disable-pip-version-check -q -r (Join-Path $Pack "requirements-dev.txt") } "pip install (dev)"
}

function Check-Blender {
    $found = $null
    if ($env:B2M3D_BLENDER -and (Test-Path $env:B2M3D_BLENDER)) { $found = $env:B2M3D_BLENDER }
    elseif (Get-Command blender -ErrorAction SilentlyContinue) { $found = (Get-Command blender).Source }
    else {
        $roots = @($env:ProgramFiles, "C:\Program Files") | Where-Object { $_ } | Select-Object -Unique
        foreach ($root in $roots) {
            $hit = Get-ChildItem -Path (Join-Path $root "Blender Foundation\Blender *\blender.exe") -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
            if ($hit) { $found = $hit.FullName; break }
        }
    }
    if ($found) {
        $ver = ""
        try { $ver = (& $found --version 2>&1 | Select-Object -First 1) } catch { $ver = "version unknown" }
        Write-Output "blender: found $found ($ver)"
    }
    else {
        Write-Output "blender: not found. Install it yourself:"
        Write-Output "  winget install BlenderFoundation.Blender   (or https://www.blender.org/download/)"
    }
}

if ($wanted -contains "core") { Install-Core }
if ($wanted -contains "cad") { Install-Cad }
if ($wanted -contains "dev") { Install-Dev }
if ($wanted -contains "blender") { Check-Blender }

New-Item -ItemType Directory -Force -Path $HomeDir | Out-Null
$marker = Join-Path $HomeDir ".components"
$all = @()
if (Test-Path $marker) { $all += Get-Content $marker }
$all = @($all + $wanted | Where-Object { $_ } | Sort-Object -Unique)
Set-Content -Path $marker -Value $all
Write-Output ("installed components: " + ($all -join ",") + "   total on disk: $(Get-SizeMB $HomeDir) MB in $HomeDir")
