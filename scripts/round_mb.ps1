<#
.SYNOPSIS
    Native Windows PowerShell port of launch-video-clone `round_mb.sh` (8x Subframe Supersampled Motion Blur).
    Recommended only for short clips (<= 10s) on 8 GB RAM machines; for longer videos use `round.ps1` with
    HyperFrames native `data-motion-blur="on" data-motion-blur-shutter="360"`.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$ProjectDir,

    [Parameter(Mandatory = $true, Position = 1)]
    [string]$RenderRoot,

    [Parameter(Mandatory = $true, Position = 2)]
    [string]$VersionTag,

    [Parameter(Mandatory = $false, Position = 3)]
    [int]$Subframes = 8,

    [Parameter(Mandatory = $false, Position = 4)]
    [int]$Fps = 30
)

$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    $wingetFfmpeg = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter "ffmpeg.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($wingetFfmpeg) { $env:Path = "$env:Path;$($wingetFfmpeg.DirectoryName)" }
}

$P = (Resolve-Path -LiteralPath $ProjectDir -ErrorAction Stop).Path
New-Item -ItemType Directory -Force -Path $RenderRoot | Out-Null
$R = (Resolve-Path -LiteralPath $RenderRoot -ErrorAction Stop).Path
$S = $PSScriptRoot

$compDir = if (Test-Path (Join-Path $P "hf\index.html")) { Join-Path $P "hf" } elseif (Test-Path (Join-Path $P "composition\index.html")) { Join-Path $P "composition" } else { $P }
$HI = $Fps * $Subframes
$shiftVal = (($Subframes - 1.0) / 2.0 / $HI).ToString("0.########", [System.Globalization.CultureInfo]::InvariantCulture)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $compDir "mb.js"), "window.MB_SHIFT = $shiftVal;`n", $utf8NoBom)

$rawMp4 = Join-Path $R "$VersionTag-raw.mp4"
$vMp4 = Join-Path $R "$VersionTag-v.mp4"
$outMp4 = Join-Path $R "$VersionTag.mp4"
$refMp4 = Join-Path $P "reference\ref.mp4"
$pluginCli = Join-Path $env:USERPROFILE ".gemini\config\skills\hyperframes\scripts\plugin-cli.mjs"

Push-Location $compDir
try {
    if (Test-Path $pluginCli) {
        & node $pluginCli render --quality draft --low-memory-mode --fps $HI --output $rawMp4 2>&1 | Select-String -Pattern "rendered in|Render complete|rror"
    } else {
        & npx hyperframes render --quality draft --low-memory-mode --fps $HI --output $rawMp4 2>&1 | Select-String -Pattern "rendered in|Render complete|rror"
    }
} finally {
    Pop-Location
}

& ffmpeg -v error -y -i $rawMp4 -vf "tmix=frames=$Subframes,select='not(mod(n+1\,$Subframes))',setpts=N/($Fps*TB)" -r $Fps -c:v libx264 -crf 16 -pix_fmt yuv420p -an $vMp4
if (Test-Path $refMp4) {
    & ffmpeg -v error -y -i $vMp4 -i $refMp4 -map 0:v -map "1:a?" -c copy -shortest $outMp4
} else {
    Move-Item -Force $vMp4 $outMp4
}

Remove-Item -Force $rawMp4, $vMp4 -ErrorAction SilentlyContinue
[System.IO.File]::WriteAllText((Join-Path $compDir "mb.js"), "window.MB_SHIFT = 0;`n", $utf8NoBom)

$vAnalysis = Join-Path $R "$VersionTag-analysis"
$vCompare = Join-Path $R "$VersionTag-compare"
$refAnalysis = Join-Path $P "reference\analysis"
& python "$S\burst.py" $outMp4 $vAnalysis | Out-Null
if (Test-Path (Join-Path $refAnalysis "analysis.json")) {
    & python "$S\compare.py" $refAnalysis $vAnalysis $vCompare
}
