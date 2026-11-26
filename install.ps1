<#
.SYNOPSIS
    Installs REA Motion skills into Antigravity (~/.gemini/config/skills) and optional Python CV dependencies.
#>
[CmdletBinding()]
param(
    [switch]$SkipPip,
    [switch]$IncludeClaude
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

Write-Output "=== [2/3] Installing REA Motion skills ==="
$skillsDir = Join-Path $repoRoot "skills"
$skillFolders = Get-ChildItem -Path $skillsDir -Directory
foreach ($destRoot in $targetRoots) {
    New-Item -ItemType Directory -Force -Path $destRoot | Out-Null
    foreach ($sf in $skillFolders) {
        $dest = Join-Path $destRoot $sf.Name
        Copy-Item -Path $sf.FullName -Destination $dest -Recurse -Force
        Write-Output "  Installed $($sf.Name) -> $dest"
    }
}

Write-Output "=== [3/3] Done! Invoke 'rea-motion' in Antigravity or read README.md for copy-paste prompts. ==="
