<#
.SYNOPSIS
    Layer 4+5 Unified Runner: Brain Autopilot v3.1 (WebGL3DEngine) + HyperFrames Parity QA
    Starts a temporary local HTTP server for the composition, executes Brain Autopilot `check` and `run`
    at 1920x1080 viewport, and runs HyperFrames deterministic still snapshot capture.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$CompositionDir,

    [Parameter(Mandatory = $false)]
    [string]$HarnessPath = (Join-Path $PSScriptRoot "harness_hyperframes_3d.py"),

    [Parameter(Mandatory = $false)]
    [int]$Port = 8765
)

$ErrorActionPreference = "Continue"
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture

$resolvedComp = (Resolve-Path -LiteralPath $CompositionDir -ErrorAction Stop).Path
$cliPy = Join-Path $env:USERPROFILE ".gemini\brain-autopilot\brain_autopilot\cli.py"

# Ensure FFmpeg in PATH
$wingetFfmpeg = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter "ffmpeg.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($wingetFfmpeg) {
    $env:Path = "$env:Path;$($wingetFfmpeg.DirectoryName)"
}

Write-Output "=== [1/4] Starting Temporary Local HTTP Server on port $Port ==="
$serverProc = Start-Process -FilePath "python" -ArgumentList @("-m", "http.server", "$Port", "--bind", "127.0.0.1", "--directory", $resolvedComp) -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2

try {
    $liveUrl = "http://127.0.0.1:$Port"
    Write-Output "=== [2/4] Brain Autopilot Dry-Run Check ($liveUrl) ==="
    & python $cliPy check $HarnessPath --project $resolvedComp --url $liveUrl --viewport 1920x1080

    Write-Output "=== [3/4] Brain Autopilot Autonomous Episode Run ($liveUrl) ==="
    & python $cliPy run $HarnessPath --project $resolvedComp --url $liveUrl --viewport 1920x1080 --seconds 25
} finally {
    if ($serverProc -and -not $serverProc.HasExited) {
        Stop-Process -Id $serverProc.Id -Force -ErrorAction SilentlyContinue
    }
}

Write-Output "=== [4/4] HyperFrames Snapshot & 3D WebGL Still Verification ==="
$qaDir = Join-Path $resolvedComp "qa_stills"
New-Item -ItemType Directory -Force -Path $qaDir | Out-Null
Push-Location $resolvedComp
try {
    & hyperframes snapshot "--at=0.45,1.8,4.6" "--output=$qaDir"
} finally {
    Pop-Location
}
