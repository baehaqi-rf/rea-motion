#!/usr/bin/env python3
"""
Motion-REA 20% Layer: Fast Beat, Sub-Bass (20-150Hz) & Loudness Telemetry (`beats.py`).

Replaces heavy `librosa`/`numba` with pure `scipy.signal` Butterworth band-splitting +
FFmpeg 44.1kHz PCM + native `hyperframes audio/beats` integration on Windows Python 3.14.
Outputs deterministic `beats.json` ready for HyperFrames GSAP & Three.js `hf-seek`.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from scipy.signal import butter, find_peaks, sosfiltfilt


def resolve_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg and os.name == "nt":
        winget = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        if winget.is_dir():
            for exe in winget.rglob("ffmpeg.exe"):
                ffmpeg = str(exe)
                os.environ["PATH"] = f"{os.environ.get('PATH', '')};{exe.parent}"
                break
    if not ffmpeg:
        raise FileNotFoundError("ffmpeg not found on PATH or WinGet packages.")
    return ffmpeg


def resolve_hyperframes_cmd() -> list[str] | None:
    hf = shutil.which("hyperframes")
    if hf:
        return [hf]
    candidates = [
        Path.home() / ".gemini" / "config" / "skills" / "hyperframes" / "scripts" / "plugin-cli.mjs",
        Path(__file__).resolve().parents[1] / "skills" / "hyperframes" / "scripts" / "plugin-cli.mjs",
    ]
    for c in candidates:
        if c.is_file() and shutil.which("node"):
            return ["node", str(c)]
    return None


def decode_mono_pcm(ffmpeg: str, media_path: Path, sr: int = 44100, max_sec: float | None = None) -> np.ndarray:
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error"]
    if max_sec is not None:
        cmd.extend(["-t", f"{max_sec:.3f}"])
    cmd.extend(["-i", str(media_path), "-vn", "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "1", "-ar", str(sr), "-"])
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0 or not proc.stdout:
        return np.zeros(0, dtype=np.float32)
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


def _band_rms_per_frame(signal: np.ndarray, sr: int, fps: float) -> np.ndarray:
    hop = max(1, int(round(sr / fps)))
    n_frames = max(1, int(np.ceil(len(signal) / hop)))
    out = np.zeros(n_frames, dtype=np.float32)
    for i in range(n_frames):
        chunk = signal[i * hop : min(len(signal), (i + 1) * hop)]
        if len(chunk) > 0:
            out[i] = float(np.sqrt(np.mean(chunk * chunk)))
    mx = float(np.max(out))
    return out / mx if mx > 1e-7 else out


def extract_beats_and_envelopes(
    media_path: Path, fps: float = 30.0, max_sec: float | None = None
) -> dict[str, Any]:
    ffmpeg = resolve_ffmpeg()
    hf_cmd = resolve_hyperframes_cmd()
    sr = 44100
    pcm = decode_mono_pcm(ffmpeg, media_path, sr=sr, max_sec=max_sec)

    if len(pcm) == 0:
        return {
            "ok": True,
            "has_audio": False,
            "fps": fps,
            "bpm": None,
            "beats_sec": [],
            "beats_ms": [],
            "downbeats_ms": [],
            "kick_hits_ms": [],
            "snare_hits_ms": [],
            "sections": [],
            "frames": [],
        }

    duration_sec = len(pcm) / sr

    # 1. Sub-bass / Kick (20 - 150 Hz) & Mid / Snare-Vocal (200 - 4000 Hz) Butterworth filtering
    sos_bass = butter(4, [20.0, 150.0], btype="bandpass", fs=sr, output="sos")
    sos_mid = butter(4, [200.0, 4000.0], btype="bandpass", fs=sr, output="sos")
    bass_sig = sosfiltfilt(sos_bass, pcm).astype(np.float32)
    mid_sig = sosfiltfilt(sos_mid, pcm).astype(np.float32)

    rms_full = _band_rms_per_frame(pcm, sr, fps)
    rms_bass = _band_rms_per_frame(bass_sig, sr, fps)
    rms_mid = _band_rms_per_frame(mid_sig, sr, fps)

    # Detect sub-bass kick peaks & transient snare/onset peaks on frame grid
    bass_flux = np.maximum(0.0, np.diff(rms_bass, prepend=rms_bass[0]))
    mid_flux = np.maximum(0.0, np.diff(rms_mid, prepend=rms_mid[0]))
    min_dist = max(1, int(round(0.22 * fps)))

    kick_idx, _ = find_peaks(rms_bass, height=0.38, prominence=0.12, distance=min_dist)
    snare_idx, _ = find_peaks(mid_flux, height=0.22, prominence=0.10, distance=min_dist)

    kick_hits_ms = [int(round((int(idx) / fps) * 1000)) for idx in kick_idx]
    snare_hits_ms = [int(round((int(idx) / fps) * 1000)) for idx in snare_idx]

    # 2. Query HyperFrames audio analyzer for BPM, beat grid, downbeats, and sections
    bpm = None
    beats_sec: list[float] = []
    downbeats_ms: list[int] = []
    sections: list[dict[str, Any]] = []
    limit_s = max_sec if max_sec is not None else duration_sec + 1.0

    if hf_cmd:
        try:
            proc = subprocess.run(
                [*hf_cmd, "audio", str(media_path), "--only", "beats,downbeats,bpm,sections", "--json"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                raw = json.loads(proc.stdout)
                item = raw["items"][0] if "items" in raw else raw[0]
                bpm = item.get("bpm", {}).get("value")
                beats_sec = [round(float(t), 4) for t in item.get("beats", {}).get("times", []) if t <= limit_s]
                downbeats_ms = [
                    int(round(float(t) * 1000)) for t in item.get("downbeats", {}).get("times", []) if t <= limit_s
                ]
                sections = [
                    s for s in item.get("sections", {}).get("spans", []) if float(s.get("start", 0)) < limit_s
                ]
        except Exception:
            pass

    # Fallback BPM estimation from bass autocorrelation if HyperFrames beats was unavailable
    if not beats_sec and len(kick_hits_ms) >= 3:
        ibis = np.diff(kick_hits_ms) / 1000.0
        valid = ibis[(ibis >= 0.28) & (ibis <= 1.2)]
        if len(valid) > 0:
            med_ibi = float(np.median(valid))
            bpm = round(60.0 / med_ibi, 1)
            beats_sec = [round(k / 1000.0, 4) for k in kick_hits_ms]

    frames_telemetry = [
        {
            "frame": int(i),
            "t_ms": int(round((i / fps) * 1000)),
            "rms": round(float(rms_full[i]), 4),
            "sub_bass": round(float(rms_bass[i]), 4),
            "mid_flux": round(float(mid_flux[i]), 4),
        }
        for i in range(len(rms_full))
    ]

    return {
        "ok": True,
        "source": str(media_path),
        "has_audio": True,
        "duration_sec": round(duration_sec, 4),
        "fps": fps,
        "bpm": bpm,
        "beats_sec": beats_sec,
        "beats_ms": [int(round(t * 1000)) for t in beats_sec],
        "downbeats_ms": downbeats_ms,
        "kick_hits_ms": kick_hits_ms,
        "snare_hits_ms": snare_hits_ms,
        "sections": sections,
        "frames": frames_telemetry,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Motion-REA Fast Audio Beat & Sub-Bass Telemetry (Python 3.14)")
    parser.add_argument("input", help="Path to audio (.mp3/.wav) or video (.mp4) file")
    parser.add_argument("--out", default="beats.json", help="Output JSON path (default: beats.json)")
    parser.add_argument("--fps", type=float, default=30.0, help="Target composition frame rate (default: 30)")
    parser.add_argument("--max-sec", type=float, default=None, help="Optional max duration in seconds")
    args = parser.parse_args()

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = extract_beats_and_envelopes(Path(args.input).resolve(), fps=args.fps, max_sec=args.max_sec)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": data["ok"],
                "out": str(out_path),
                "bpm": data["bpm"],
                "beats": len(data["beats_ms"]),
                "kick_hits": len(data["kick_hits_ms"]),
                "frames": len(data["frames"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
