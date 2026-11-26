<#
.SYNOPSIS
    Installs REA Motion as a single unified Antigravity skill (~/.gemini/config/skills/rea-motion),
    removes legacy fragmented skill folders, and installs Python CV/audio dependencies.
#>
[CmdletBinding()]
param(
    [switch]$SkipPip,
    [switch]$IncludeClaude,
    [switch]$KeepLegacy
)

$ErrorActionPreference = "Stop"
$repoRoot = $PSScriptRoot

if (-not $SkipPip) {
    Write-Output "=== [1/3] Installing Python dependencies (numpy, pillow, scipy, opencv-python-headless, matplotlib) ==="
    python -m pip install --upgrade numpy pillow scipy opencv-python-headless matplotlib
}

$targetRoots = @((Join-Path $env:USERPROFILE ".gemini\config\skills"))
if ($IncludeClaude) {
    $targetRoots += (Join-Path $env:USERPROFILE ".claude\skills")
}

$legacyNames = @("hyperframes-motion-rea", "launch-video-clone", "reelmimic-styles", "local-hyperframes-pro")

Write-Output "=== [2/3] Installing unified rea-motion skill ==="
foreach ($destRoot in $targetRoots) {
    New-Item -ItemType Directory -Force -Path $destRoot | Out-Null

    if (-not $KeepLegacy) {
        foreach ($old in $legacyNames) {
            $oldPath = Join-Path $destRoot $old
            if (Test-Path $oldPath) {
                Remove-Item -Path $oldPath -Recurse -Force
                Write-Output "  Removed redundant legacy skill: $oldPath"
            }
        }
    }

    $dest = Join-Path $destRoot "rea-motion"
    if (Test-Path $dest) {
        Remove-Item -Path $dest -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Get-ChildItem -Path $repoRoot -Force | Where-Object { $_.Name -ne ".git" } | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
    }
    Write-Output "  Installed rea-motion -> $dest"
}

Write-Output "=== [3/3] Done! Invoke 'rea-motion' in Antigravity (alongside core hyperframes skills). ==="
