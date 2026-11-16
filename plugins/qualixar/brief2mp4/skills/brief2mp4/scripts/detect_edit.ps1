# detect_edit.ps1: say whether the optional edit pack is installed. Always exits 0, so a caller can branch on the text.
#
#   edit: ready (film,sound,effect,photo,vector)
#   edit: not installed
#
# A component is listed only when its pinned CLI is there AND runs (<cli> --version exits 0).
# It needs nothing but B2M_EDIT_HOME (default %USERPROFILE%\.brief2mp4\edit).
$HomeDir = if ($env:B2M_EDIT_HOME) { $env:B2M_EDIT_HOME } else { Join-Path $env:USERPROFILE ".brief2mp4\edit" }
$found = @()

function Test-Cli([string]$path) {
    # Run through .NET so native stderr never becomes a terminating error under $ErrorActionPreference = 'Stop'.
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $path
        $psi.Arguments = "--version"
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        $p = [System.Diagnostics.Process]::Start($psi)
        $null = $p.StandardOutput.ReadToEnd()
        $null = $p.StandardError.ReadToEnd()
        $p.WaitForExit()
        return ($p.ExitCode -eq 0)
    } catch { return $false }
}

foreach ($pair in @("film:filmcraft", "sound:soundcraft", "effect:effectcraft", "photo:photocraft", "vector:vectorcraft")) {
    $short, $name = $pair -split ":"
    $candidates = @(
        (Join-Path $HomeDir "$name\$name-cli.exe"),
        (Join-Path $HomeDir "$name\bin\$name-cli"),
        (Join-Path $HomeDir "$name\$name-cli"))
    foreach ($c in $candidates) {
        if ((Test-Path $c) -and (Test-Cli $c)) { $found += $short; break }
    }
}

if ($found.Count -gt 0) { Write-Output ("edit: ready (" + ($found -join ",") + ")") }
else { Write-Output "edit: not installed" }
exit 0
