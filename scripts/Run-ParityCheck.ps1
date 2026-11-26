<#
.SYNOPSIS
    Layer 4: Closed-Loop Visual Parity QA & Lint Gate for HyperFrames Compositions
    Runs `hyperframes check --json` + renders still snapshots at critical timestamps from `beat_sheet.json`.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$CompositionDir,

    [Parameter(Mandatory = $false)]
    [string]$BeatSheetPath,

    [Parameter(Mandatory = $false)]
    [string]$ReferenceVideoPath
)

$ErrorActionPreference = "Continue"
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture

$resolvedComp = (Resolve-Path -LiteralPath $CompositionDir -ErrorAction Stop).Path
$qaDir = Join-Path $resolvedComp "qa_stills"
New-Item -ItemType Directory -Force -Path $qaDir | Out-Null

Push-Location $resolvedComp
try {
    Write-Output "=== [1/3] Running HyperFrames Contract, Layout & Contrast Audit ==="
    $checkJson = & hyperframes check --json 2>$null
    $checkFile = Join-Path $qaDir "check_report.json"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    if ($checkJson) {
        [System.IO.File]::WriteAllText($checkFile, ($checkJson -join "`n"), $utf8NoBom)
    }

    # Determine critical timestamps to sample
    $timestamps = @("0.2", "1.2", "2.5", "4.0")
    if ($BeatSheetPath -and (Test-Path $BeatSheetPath)) {
        $bs = Get-Content -LiteralPath $BeatSheetPath -Raw | ConvertFrom-Json
        $sampled = @()
        foreach ($sc in $bs.scenes) {
            $mid = [Math]::Round(([double]$sc.start_sec + [double]$sc.end_sec) / 2.0, 2)
            $sampled += $mid.ToString("0.##", [System.Globalization.CultureInfo]::InvariantCulture)
        }
        if ($sampled.Count -gt 0) {
            $timestamps = $sampled | Select-Object -First 6
        }
    }
    $atArg = $timestamps -join ","

    Write-Output "=== [2/3] Capturing Deterministic Still Frames at t=[$atArg] ==="
    if ($ReferenceVideoPath -and (Test-Path $ReferenceVideoPath)) {
        $refResolved = (Resolve-Path -LiteralPath $ReferenceVideoPath).Path
        & hyperframes snapshot "--at=$atArg" "--against=$refResolved" "--output=$qaDir"
    } else {
        & hyperframes snapshot "--at=$atArg" "--output=$qaDir"
    }

    Write-Output "=== [3/3] QA Stills Ready in: $qaDir ==="
    Get-ChildItem -LiteralPath $qaDir | Select-Object Name, Length
} finally {
    Pop-Location
}
