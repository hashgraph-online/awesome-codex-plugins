# vendor_libs.ps1: copy pinned GSAP, three.js and web fonts into a project's vendor/ folder, so a render never touches
# the network (same pixels every run, works offline). The Windows twin of vendor_libs.sh: same versions, same files.
#
#   powershell -File vendor_libs.ps1 -Project PROJECT_DIR                       # GSAP only
#   powershell -File vendor_libs.ps1 -Project PROJECT_DIR -Three                # GSAP + three.js
#   powershell -File vendor_libs.ps1 -Project PROJECT_DIR -Fonts inter,space-grotesk
#
# Writes PROJECT_DIR\vendor\gsap.min.js, vendor\three.module.js (with -Three) and vendor\fonts\<family>-<weight>.woff2
# plus vendor\fonts\fonts.css (with -Fonts; weights 400 and 700, latin subset). Needs npm (it ships with Node.js) and
# tar (Windows 10 and later have it). Safe to run again.
param(
    [Parameter(Mandatory = $true)][string]$Project,
    [switch]$Three,
    [string]$Fonts = ""
)
$ErrorActionPreference = "Stop"

$GsapVersion = "3.15.0"
$ThreeVersion = "0.170.0"
$FontVersion = "5.3.0"

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Write-Error "vendor_libs.ps1: npm not found; install Node.js 22+"; exit 1 }
if (-not (Get-Command tar -ErrorAction SilentlyContinue)) { Write-Error "vendor_libs.ps1: tar not found (Windows 10 and later include it)"; exit 1 }

New-Item -ItemType Directory -Force -Path (Join-Path $Project "vendor") | Out-Null
$Vendor = (Resolve-Path (Join-Path $Project "vendor")).Path
$Work = Join-Path ([System.IO.Path]::GetTempPath()) ("b2m-vendor-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $Work | Out-Null

function Get-Package([string]$spec) {
    # npm pack the package, unpack it under $Work and return the folder that holds its files
    Push-Location $Work
    try {
        $tgz = (& npm pack $spec --silent 2>$null | Select-Object -Last 1).Trim()
        $dir = Join-Path $Work ([System.IO.Path]::GetFileNameWithoutExtension($tgz))
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        & tar -xzf (Join-Path $Work $tgz) -C $dir
        if ($LASTEXITCODE -ne 0) { throw "tar could not unpack $tgz" }
        return (Join-Path $dir "package")
    } finally { Pop-Location }
}

try {
    $pkg = Get-Package "gsap@$GsapVersion"
    Copy-Item (Join-Path $pkg "dist\gsap.min.js") (Join-Path $Vendor "gsap.min.js") -Force
    Write-Output "vendor: gsap $GsapVersion -> vendor/gsap.min.js"

    if ($Three) {
        $pkg = Get-Package "three@$ThreeVersion"
        Copy-Item (Join-Path $pkg "build\three.module.js") (Join-Path $Vendor "three.module.js") -Force
        Write-Output "vendor: three $ThreeVersion -> vendor/three.module.js"
    }

    if ($Fonts) {
        $fontDir = Join-Path $Vendor "fonts"
        New-Item -ItemType Directory -Force -Path $fontDir | Out-Null
        $css = Join-Path $fontDir "fonts.css"
        Set-Content -Path $css -Value "" -NoNewline -Encoding UTF8
        foreach ($fam in ($Fonts -split ",")) {
            $fam = $fam.Trim()
            if (-not $fam) { continue }
            $pkg = Get-Package "@fontsource/$fam@$FontVersion"
            $name = $fam
            $meta = Join-Path $pkg "metadata.json"
            if (Test-Path $meta) { $name = (Get-Content $meta -Raw | ConvertFrom-Json).family }
            $license = Join-Path $pkg "LICENSE"
            if (Test-Path $license) { Copy-Item $license (Join-Path $fontDir "LICENSE-$fam.txt") -Force }
            foreach ($w in @(400, 700)) {
                $src = Join-Path $pkg "files\$fam-latin-$w-normal.woff2"
                if (Test-Path $src) {
                    Copy-Item $src (Join-Path $fontDir "$fam-$w.woff2") -Force
                    Add-Content -Path $css -Encoding UTF8 -Value ('@font-face{font-family:"' + $name + '";font-weight:' + $w + ';font-style:normal;font-display:block;src:url("' + $fam + '-' + $w + '.woff2") format("woff2")}')
                }
            }
            Write-Output "vendor: font $name ($fam) -> vendor/fonts/"
        }
    }
} finally {
    Remove-Item -Recurse -Force $Work -ErrorAction SilentlyContinue
}
