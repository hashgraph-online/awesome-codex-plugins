# detect_3d.ps1: say whether the optional 3D pack is installed. Always exits 0, so a caller can branch on the text.
#
#   3d: ready (components: core,cad,blender)
#   3d: not installed
#
# "ready" needs the core component. cad and blender are listed when present.
# B2M3D_HOME overrides the install folder (default %USERPROFILE%\.brief2mp4\3d).
$HomeDir = if ($env:B2M3D_HOME) { $env:B2M3D_HOME } else { Join-Path $env:USERPROFILE ".brief2mp4\3d" }
$found = @()

$py = Join-Path $HomeDir "venv\Scripts\python.exe"
$hasCore = (Test-Path $py) -and
           (Test-Path (Join-Path $HomeDir "node_modules\three")) -and
           (Test-Path (Join-Path $HomeDir "node_modules\jolt-physics"))
# "ready" means the pack actually imports, not just that files exist.
if ($hasCore) {
    try { & $py -c "import b2m3d.cli" *> $null; $hasCore = ($LASTEXITCODE -eq 0) } catch { $hasCore = $false }
}
if ($hasCore) {
    $found += "core"
    try { & $py -c "import cadquery" *> $null; if ($LASTEXITCODE -eq 0) { $found += "cad" } } catch { }

    $blender = $false
    if ($env:B2M3D_BLENDER -and (Test-Path $env:B2M3D_BLENDER)) { $blender = $true }
    elseif (Get-Command blender -ErrorAction SilentlyContinue) { $blender = $true }
    else {
        $roots = @($env:ProgramFiles, "C:\Program Files") | Where-Object { $_ } | Select-Object -Unique
        foreach ($root in $roots) {
            if (Get-ChildItem -Path (Join-Path $root "Blender Foundation\Blender *\blender.exe") -ErrorAction SilentlyContinue) { $blender = $true }
        }
    }
    if ($blender) { $found += "blender" }
    Write-Output ("3d: ready (components: " + ($found -join ",") + ")")
} else {
    Write-Output "3d: not installed"
}
exit 0
