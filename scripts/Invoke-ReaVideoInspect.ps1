<#
.SYNOPSIS
    Layer 1: REA Local Video Inspection & Audio Extraction Engine (Windows 11)
    Replaces paid `/reverse-any-video` cloud gating with 100% local ffprobe + FFmpeg + optional `hyperframes measure`.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$VideoPath,

    [Parameter(Mandatory = $true)]
    [string]$ProjectDir,

    [Parameter(Mandatory = $false)]
    [double]$SceneThreshold = 0.25,

    [Parameter(Mandatory = $false)]
    [double]$IntervalFps = 1.0
)

$ErrorActionPreference = "Continue"
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture
[System.Threading.Thread]::CurrentThread.CurrentUICulture = [System.Globalization.CultureInfo]::InvariantCulture

$resolvedVideo = (Resolve-Path -LiteralPath $VideoPath -ErrorAction Stop).Path
$inspectDir = Join-Path $ProjectDir ".rea_inspect"
$sceneDir = Join-Path $inspectDir "keyframes_scene"
$intervalDir = Join-Path $inspectDir "keyframes_interval"
$audioDir = Join-Path $inspectDir "audio"
$flowSttDir = Join-Path $inspectDir "flow_stt"

New-Item -ItemType Directory -Force -Path $sceneDir, $intervalDir, $audioDir, $flowSttDir | Out-Null

# 1. Probe metadata with ffprobe
$probeJsonRaw = & ffprobe -v quiet -print_format json -show_format -show_streams -- $resolvedVideo
$probeData = ($probeJsonRaw -join "`n") | ConvertFrom-Json

$videoStream = $probeData.streams | Where-Object { $_.codec_type -eq "video" } | Select-Object -First 1
$audioStream = $probeData.streams | Where-Object { $_.codec_type -eq "audio" } | Select-Object -First 1

if (-not $videoStream) {
    throw "No video stream found in $resolvedVideo"
}

$fpsParts = ($videoStream.r_frame_rate -split "/")
$fps = if ($fpsParts.Count -eq 2 -and [double]$fpsParts[1] -gt 0) {
    [Math]::Round([double]$fpsParts[0] / [double]$fpsParts[1], 4)
} else {
    [double]$videoStream.r_frame_rate
}
$durationSec = [Math]::Round([double]$probeData.format.duration, 4)
$width = [int]$videoStream.width
$height = [int]$videoStream.height

# FFmpeg 5.1+ uses -fps_mode vfr
$vfrArgs = @("-fps_mode", "vfr")

# 2. Scene-cut keyframes with showinfo
$threshStr = $SceneThreshold.ToString("0.###", [System.Globalization.CultureInfo]::InvariantCulture)
$sceneFilter = "select='eq(n\,0)+gt(scene\,$threshStr)',showinfo"
$scenePattern = Join-Path $sceneDir "scene_%04d.png"
$showinfoLog = Join-Path $inspectDir "showinfo_scene.log"

$ffArgsScene = @("-hide_banner", "-y", "-i", $resolvedVideo, "-vf", $sceneFilter) + $vfrArgs + @($scenePattern)
$sceneLogLines = & ffmpeg @ffArgsScene 2>&1
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($showinfoLog, [string[]]$sceneLogLines, $utf8NoBom)

$sceneKeyframes = @()
$sceneFiles = @(Get-ChildItem -LiteralPath $sceneDir -Filter "scene_*.png" | Sort-Object Name)
$ptsMatches = @(Select-String -Path $showinfoLog -Pattern "pts_time:([0-9]+\.?[0-9]*)" -AllMatches)

for ($i = 0; $i -lt $sceneFiles.Count; $i++) {
    $ts = 0.0
    if ($i -lt $ptsMatches.Count) {
        $val = $ptsMatches[$i].Matches[0].Groups[1].Value
        [void][double]::TryParse($val, [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$ts)
    }
    $sceneKeyframes += [ordered]@{
        index          = $i
        file           = $sceneFiles[$i].FullName
        timestamp_sec  = [Math]::Round($ts, 3)
        frame_estimate = [int][Math]::Floor($ts * $fps)
    }
}

# 3. Baseline interval keyframes
$intFpsStr = $IntervalFps.ToString("0.###", [System.Globalization.CultureInfo]::InvariantCulture)
$intervalPattern = Join-Path $intervalDir "interval_%04d.png"
$null = & ffmpeg -hide_banner -y -i $resolvedVideo -vf "fps=$intFpsStr" $intervalPattern 2>&1

$intervalKeyframes = @()
$intFiles = @(Get-ChildItem -LiteralPath $intervalDir -Filter "interval_*.png" | Sort-Object Name)
for ($j = 0; $j -lt $intFiles.Count; $j++) {
    $ts = [Math]::Round($j / $IntervalFps, 3)
    $intervalKeyframes += [ordered]@{
        index         = $j
        file          = $intFiles[$j].FullName
        timestamp_sec = $ts
    }
}

# 4. Clean WAV 16kHz Mono PCM extraction for Google Flow STT
$wavOut = $null
if ($audioStream) {
    $wavOut = Join-Path $audioDir "stt_input_16k_mono.wav"
    $null = & ffmpeg -hide_banner -y -i $resolvedVideo -vn -acodec pcm_s16le -ar 16000 -ac 1 $wavOut 2>&1
}

# 5. Run HyperFrames native Apache-2.0 `measure cuts` if available
$hfCuts = $null
if (Get-Command hyperframes -ErrorAction SilentlyContinue) {
    try {
        $hfCutsRaw = & hyperframes measure cuts $resolvedVideo --json 2>$null
        if ($LASTEXITCODE -eq 0 -and $hfCutsRaw) {
            $hfCuts = ($hfCutsRaw -join "`n") | ConvertFrom-Json
        }
    } catch {}
}

$manifest = [ordered]@{
    schema_version      = "1.1.0"
    inspected_at        = (Get-Date).ToString("o")
    source_video        = $resolvedVideo
    metadata            = [ordered]@{
        width        = $width
        height       = $height
        fps          = $fps
        fps_rational = $videoStream.r_frame_rate
        duration_sec = $durationSec
        video_codec  = $videoStream.codec_name
        has_audio    = [bool]($null -ne $audioStream)
        aspect_ratio = if ($width -gt $height) { "16:9" } elseif ($height -gt $width) { "9:16" } else { "1:1" }
    }
    stt_audio_wav       = $wavOut
    scene_keyframes     = $sceneKeyframes
    interval_keyframes  = $intervalKeyframes
    hyperframes_measure = $hfCuts
}

$manifestPath = Join-Path $inspectDir "inspect_manifest.json"
[System.IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 10), $utf8NoBom)

Write-Output "Inspection complete -> $manifestPath"
