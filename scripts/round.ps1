<#
.SYNOPSIS
    Native Windows PowerShell port of launch-video-clone `round.sh` (Hybrid 80/20 Edition).
    Runs: unslop_check.py -> HyperFrames draft render (with native data-motion-blur="on" & --low-memory-mode)
          -> burst.py -> compare.py -> sbs.py -> appends metrics to LOG-numbers.txt.
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
    [string]$Fps = "",

    [Parameter(Mandatory = $false)]
    [string]$CompSubdir = "",

    [Parameter(Mandatory = $false)]
    [string]$RefVideo = "",

    [Parameter(Mandatory = $false)]
    [switch]$SkipSbs
)

$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture

# 1. Auto-discover WinGet FFmpeg / FFprobe if not already on PATH
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    $wingetFfmpeg = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter "ffmpeg.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($wingetFfmpeg) {
        $env:Path = "$env:Path;$($wingetFfmpeg.DirectoryName)"
    }
}

$P = (Resolve-Path -LiteralPath $ProjectDir -ErrorAction Stop).Path
New-Item -ItemType Directory -Force -Path $RenderRoot | Out-Null
$R = (Resolve-Path -LiteralPath $RenderRoot -ErrorAction Stop).Path
$S = $PSScriptRoot

# Resolve composition folder (`hf` for launch-video-clone layout, or `composition` for local-video-studio layout)
if ($CompSubdir) {
    $compDir = Join-Path $P $CompSubdir
} elseif (Test-Path (Join-Path $P "hf\index.html")) {
    $compDir = Join-Path $P "hf"
} elseif (Test-Path (Join-Path $P "composition\index.html")) {
    $compDir = Join-Path $P "composition"
} else {
    $compDir = $P
}

# Resolve reference video & reference burst analysis
if (-not $RefVideo) {
    $RefVideo = Join-Path $P "reference\ref.mp4"
}
$refAnalysis = Join-Path $P "reference\analysis"
if ((Test-Path $RefVideo) -and -not (Test-Path (Join-Path $refAnalysis "analysis.json"))) {
    Write-Output "=== [0/5] Analyzing Reference Video with burst.py ==="
    New-Item -ItemType Directory -Force -Path $refAnalysis | Out-Null
    & python "$S\burst.py" $RefVideo $refAnalysis
}

if (-not $Fps) {
    if (Test-Path $RefVideo) {
        $Fps = (& ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 $RefVideo).Trim()
    }
    if (-not $Fps) { $Fps = "30" }
}

# 2. Run deterministic Anti-Slop check if available
$unslopPy = Join-Path $PSScriptRoot "unslop_check.py"
if (Test-Path $unslopPy) {
    Write-Output "=== [1/5] Anti-Slop & Manifest Check ==="
    & python $unslopPy $compDir
}

# 3. Render draft MP4 via HyperFrames launcher (respecting 8GB RAM low-memory mode & native motion blur)
$outMp4 = Join-Path $R "$VersionTag.mp4"
$pluginCli = Join-Path $env:USERPROFILE ".gemini\config\skills\hyperframes\scripts\plugin-cli.mjs"
Write-Output "=== [2/5] Rendering Draft ($Fps fps) -> $outMp4 ==="
Push-Location $compDir
try {
    if (Test-Path $pluginCli) {
        & node $pluginCli render --quality draft --low-memory-mode --fps $Fps --output $outMp4 2>&1 | Select-String -Pattern "rendered in|Render complete|rror"
    } else {
        & npx hyperframes render --quality draft --low-memory-mode --fps $Fps --output $outMp4 2>&1 | Select-String -Pattern "rendered in|Render complete|rror"
    }
} finally {
    Pop-Location
}

if (-not (Test-Path $outMp4)) {
    throw "Draft render failed: $outMp4 was not created."
}

# 4. Burst & Compare against reference
$vAnalysis = Join-Path $R "$VersionTag-analysis"
$vCompare = Join-Path $R "$VersionTag-compare"
Write-Output "=== [3/5] Running burst.py on $VersionTag.mp4 ==="
& python "$S\burst.py" $outMp4 $vAnalysis | Out-Null

if (Test-Path (Join-Path $refAnalysis "analysis.json")) {
    Write-Output "=== [4/5] Running compare.py against Reference ==="
    & python "$S\compare.py" $refAnalysis $vAnalysis $vCompare
    $compareMd = Join-Path $vCompare "COMPARE.md"
    if (Test-Path $compareMd) {
        $lines = Get-Content -LiteralPath $compareMd -Encoding UTF8
        $summaryHits = ($lines | Select-String -Pattern "matched|correlation|Mean visual|Total motion" | ForEach-Object { $_.Line }) -join " | "
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::AppendAllText((Join-Path $P "LOG-numbers.txt"), "$VersionTag  $summaryHits`n", $utf8NoBom)
        Write-Output "--- COMPARE SUMMARY ($VersionTag) ---"
        Write-Output $summaryHits
        $worstIdx = ($lines | Select-String -Pattern "Worst seconds" | Select-Object -First 1).LineNumber
        if ($worstIdx) {
            $lines[($worstIdx - 1)..([Math]::Min($lines.Count - 1, $worstIdx + 6))] | ForEach-Object { Write-Output $_ }
        }
    }

    if (-not $SkipSbs -and (Test-Path $RefVideo)) {
        $sbsOut = Join-Path $R "$VersionTag-side-by-side.mp4"
        Write-Output "=== [5/5] Building Side-by-Side Review MP4 -> $sbsOut ==="
        & python "$S\sbs.py" $RefVideo $outMp4 $sbsOut
    }
}
