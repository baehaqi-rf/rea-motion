#!/usr/bin/env python3
"""
Stage 1 of Motion-REA: Deterministic Video & Audio Decompiler (`decompile.py`).

Decompiles a flat reference MP4 into a structured `MOTION_LEDGER.json`
separating `KINETIC_DNA` (shots, optical-flow velocity & easing, beats, RMS)
from `BRAND_SKIN` (Hex palette, contrast, safe margins, STT word cues, stills).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, uniform_filter

try:
    import cv2  # type: ignore

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from scenedetect import ContentDetector, detect as scenedetect_detect  # type: ignore

    HAS_SCENEDETECT = True
except ImportError:
    HAS_SCENEDETECT = False


def resolve_ffmpeg_binaries() -> tuple[str, str]:
    """Locate ffmpeg and ffprobe, including Windows WinGet package installs."""
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if (not ffmpeg or not ffprobe) and os.name == "nt":
        local_app = os.environ.get("LOCALAPPDATA", "")
        winget_root = Path(local_app) / "Microsoft" / "WinGet" / "Packages"
        if winget_root.is_dir():
            for exe in winget_root.rglob("ffmpeg.exe"):
                ffmpeg = ffmpeg or str(exe)
                probe_candidate = exe.parent / "ffprobe.exe"
                if probe_candidate.is_file():
                    ffprobe = ffprobe or str(probe_candidate)
                os.environ["PATH"] = f"{os.environ.get('PATH', '')};{exe.parent}"
                break
    if not ffmpeg or not ffprobe:
        raise FileNotFoundError("ffmpeg and ffprobe are required on PATH (or via WinGet Gyan.FFmpeg).")
    return ffmpeg, ffprobe


def resolve_hyperframes_cmd() -> list[str] | None:
    """Locate the HyperFrames CLI command if installed globally or via skill launcher."""
    hf = shutil.which("hyperframes")
    if hf:
        return [hf]
    for plugin_cli in (
        Path(__file__).resolve().parents[2] / "hyperframes" / "scripts" / "plugin-cli.mjs",
        Path.home() / ".gemini" / "config" / "skills" / "hyperframes" / "scripts" / "plugin-cli.mjs",
    ):
        if plugin_cli.is_file() and shutil.which("node"):
            return ["node", str(plugin_cli)]
    return None


def probe_video(ffprobe: str, video_path: Path) -> dict[str, Any]:
    """Probe video stream metadata using ffprobe."""
    cmd = [
        ffprobe,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(proc.stdout)
    streams = data.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if not v_stream:
        raise ValueError(f"No video stream found in {video_path}")

    fps_raw = v_stream.get("r_frame_rate", "30/1")
    num, _, den = fps_raw.partition("/")
    fps = float(num) / float(den) if den and float(den) > 0 else float(num)
    duration_sec = float(data.get("format", {}).get("duration") or v_stream.get("duration") or 0.0)
    width = int(v_stream["width"])
    height = int(v_stream["height"])
    return {
        "width": width,
        "height": height,
        "fps": round(fps, 4),
        "fps_rational": fps_raw,
        "duration_sec": round(duration_sec, 4),
        "duration_ms": int(round(duration_sec * 1000)),
        "has_audio": a_stream is not None,
        "video_codec": v_stream.get("codec_name", "unknown"),
        "aspect_ratio": f"{width}:{height}",
    }


def detect_cuts(
    ffmpeg: str,
    hf_cmd: list[str] | None,
    video_path: Path,
    duration_sec: float,
    fps: float,
    scene_thresh: float,
) -> tuple[list[dict[str, Any]], str]:
    """Slice video into shot boundaries [start_ms, end_ms] using PySceneDetect or FFmpeg+HyperFrames."""
    cut_times: list[float] = [0.0]
    transitions: list[dict[str, Any]] = []
    engine_used = "ffmpeg_scene"

    if HAS_SCENEDETECT:
        try:
            scene_list = scenedetect_detect(str(video_path), ContentDetector(threshold=27.0))
            if scene_list:
                cut_times = [round(s[0].get_seconds(), 4) for s in scene_list]
                engine_used = "pyscenedetect"
        except Exception:
            cut_times = [0.0]

    if len(cut_times) <= 1:
        # Try HyperFrames local `measure cuts` first if available
        if hf_cmd:
            try:
                proc = subprocess.run(
                    [*hf_cmd, "measure", "cuts", str(video_path), "--json"],
                    capture_output=True,
                    text=True,
                    timeout=90,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    hf_data = json.loads(proc.stdout)
                    for c in hf_data.get("cuts", []):
                        t = float(c.get("t", c.get("time", 0.0)))
                        if 0.25 < t < duration_sec - 0.2:
                            cut_times.append(t)
                    for nc in hf_data.get("not_cuts", []):
                        transitions.append({"t_ms": int(round(float(nc.get("t", 0.0)) * 1000)), "kind": "flash_or_whip"})
                    engine_used = "hyperframes_measure+ffmpeg"
            except Exception:
                pass

        # FFmpeg scene detection fallback / complement
        vf = f"select='eq(n\\,0)+gt(scene\\,{scene_thresh:.3f})',showinfo"
        cmd = [ffmpeg, "-hide_banner", "-i", str(video_path), "-vf", vf, "-f", "null", "-"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        for m in re.finditer(r"pts_time:([0-9]+(?:\.[0-9]+)?)", proc.stderr):
            t = float(m.group(1))
            if 0.25 < t < duration_sec - 0.2:
                cut_times.append(t)

    # Deduplicate cuts closer than 0.35s and snap to frame grid
    cut_times = sorted(set(round(round(t * fps) / fps, 4) for t in cut_times if 0.0 <= t < duration_sec))
    if not cut_times or cut_times[0] > 0.05:
        cut_times.insert(0, 0.0)

    merged: list[float] = [cut_times[0]]
    for t in cut_times[1:]:
        if t - merged[-1] >= 0.35:
            merged.append(t)

    shots: list[dict[str, Any]] = []
    for idx, start_t in enumerate(merged):
        end_t = merged[idx + 1] if idx + 1 < len(merged) else duration_sec
        if end_t - start_t < 0.2:
            continue
        shots.append(
            {
                "scene_id": f"sc_{idx + 1:02d}",
                "start_sec": round(start_t, 4),
                "end_sec": round(end_t, 4),
                "start_ms": int(round(start_t * 1000)),
                "end_ms": int(round(end_t * 1000)),
                "duration_ms": int(round((end_t - start_t) * 1000)),
                "transition_in": "hard_cut" if idx > 0 else "opening",
                "internal_events": [
                    tr for tr in transitions if int(round(start_t * 1000)) <= tr["t_ms"] < int(round(end_t * 1000))
                ],
            }
        )
    return shots, engine_used


def decode_proxy_frames(
    ffmpeg: str, video_path: Path, width: int, height: int, fps: float, proxy_height: int, max_sec: float | None
) -> tuple[np.ndarray, int, int]:
    """Decode proxy RGB frames directly into a uint8 numpy array (N, H, W, 3)."""
    scale_h = min(proxy_height, height)
    scale_w = int(round((width / height) * scale_h / 2) * 2)
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error"]
    if max_sec is not None:
        cmd.extend(["-t", f"{max_sec:.3f}"])
    cmd.extend(
        [
            "-i",
            str(video_path),
            "-vf",
            f"scale={scale_w}:{scale_h}:flags=bilinear",
            "-pix_fmt",
            "rgb24",
            "-f",
            "rawvideo",
            "-",
        ]
    )
    proc = subprocess.run(cmd, capture_output=True, check=True)
    frame_bytes = scale_w * scale_h * 3
    n_frames = len(proc.stdout) // frame_bytes
    arr = np.frombuffer(proc.stdout[: n_frames * frame_bytes], dtype=np.uint8).reshape((n_frames, scale_h, scale_w, 3))
    return arr, scale_w, scale_h


def _optical_flow_pair(prev_gray: np.ndarray, curr_gray: np.ndarray) -> tuple[float, float, float, float, float]:
    """
    Compute (mean_speed, p90_speed, mean_dx, mean_dy, radial_div) between two proxy gray frames.
    Uses OpenCV Farneback when installed, else vectorized Lucas-Kanade via SciPy uniform_filter.
    """
    if HAS_CV2:
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray.astype(np.uint8),
            curr_gray.astype(np.uint8),
            None,
            0.5,
            3,
            15,
            3,
            5,
            1.2,
            0,
        )
        u = flow[..., 0]
        v = flow[..., 1]
    else:
        g1 = gaussian_filter(prev_gray.astype(np.float32), sigma=1.0)
        g2 = gaussian_filter(curr_gray.astype(np.float32), sigma=1.0)
        iy, ix = np.gradient(0.5 * (g1 + g2))
        it = g2 - g1
        win = 15
        ix2 = uniform_filter(ix * ix, size=win) + 1e-4
        iy2 = uniform_filter(iy * iy, size=win) + 1e-4
        ixy = uniform_filter(ix * iy, size=win)
        ixt = uniform_filter(ix * it, size=win)
        iyt = uniform_filter(iy * it, size=win)
        det = ix2 * iy2 - ixy * ixy + 1e-3
        u = np.clip((-iy2 * ixt + ixy * iyt) / det, -24.0, 24.0)
        v = np.clip((ixy * ixt - ix2 * iyt) / det, -24.0, 24.0)

    mag = np.sqrt(u * u + v * v)
    mean_speed = float(np.mean(mag))
    p90_speed = float(np.percentile(mag, 90))
    mean_dx = float(np.mean(u))
    mean_dy = float(np.mean(v))

    h, w = prev_gray.shape
    yy, xx = np.mgrid[0:h, 0:w]
    rx = (xx - w / 2.0) / max(1.0, w / 2.0)
    ry = (yy - h / 2.0) / max(1.0, h / 2.0)
    radial_div = float(np.mean(rx * u + ry * v))
    return mean_speed, p90_speed, mean_dx, mean_dy, radial_div


def extract_seam_probe(
    ffmpeg: str, video_path: Path, cut_sec: float, duration_sec: float, out_png: Path
) -> str | None:
    """Extract a 30fps 6x5 high-cadence contact grid (1.0s centered on cut_sec) to expose blur & seam motion."""
    start_sec = max(0.0, min(max(0.0, duration_sec - 1.0), cut_sec - 0.5))
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{start_sec:.3f}",
        "-t",
        "1.0",
        "-i",
        str(video_path),
        "-vf",
        "fps=30,scale=640:-1,tile=6x5",
        "-frames:v",
        "1",
        str(out_png),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return out_png.name if proc.returncode == 0 and out_png.is_file() else None


def classify_easing_and_motion(
    speeds: np.ndarray, dxs: np.ndarray, dys: np.ndarray, divs: np.ndarray
) -> dict[str, Any]:
    """Infer GSAP easing curve, motion direction, and hold duration from velocity curve."""
    n = len(speeds)
    if n == 0:
        return {
            "easing_guess": "none",
            "motion_type": "static_hold",
            "dominant_direction": "none",
            "hold_frames": 0,
            "peak_idx": 0,
            "mean_speed_px": 0.0,
            "max_speed_px": 0.0,
            "velocity_curve_norm": [],
        }

    mean_sp = float(np.mean(speeds))
    max_sp = float(np.max(speeds))
    peak_idx = int(np.argmax(speeds))

    if max_sp < 0.18:
        return {
            "easing_guess": "static",
            "motion_type": "static_hold",
            "dominant_direction": "none",
            "hold_frames": n,
            "peak_idx": 0,
            "mean_speed_px": round(mean_sp, 3),
            "max_speed_px": round(max_sp, 3),
            "velocity_curve_norm": [0.0] * min(12, n),
        }

    norm = speeds / max(1e-6, max_sp)
    # Downsample curve to 10 buckets for compact ledger storage
    buckets = np.array_split(norm, min(10, n))
    curve_norm = [round(float(np.mean(b)), 3) for b in buckets]

    peak_tau = peak_idx / max(1, n - 1)
    hold_thresh = max(0.08, 0.12)
    hold_frames = int(np.sum(norm < hold_thresh))
    cv_ratio = float(np.std(speeds) / max(1e-6, mean_sp))

    # Classify easing from velocity profile
    if cv_ratio < 0.28:
        easing_guess = "none"
    elif peak_tau <= 0.25:
        tail_mean = float(np.mean(norm[max(1, n // 2) :]))
        easing_guess = "expo.out" if tail_mean < 0.12 else "power4.out"
    elif 0.30 <= peak_tau <= 0.68:
        easing_guess = "power3.inOut" if max_sp > 3.5 else "power2.inOut"
    elif peak_tau > 0.68:
        easing_guess = "power3.in"
    else:
        easing_guess = "power2.out"

    # Classify dominant direction / camera move
    avg_dx = float(np.mean(dxs))
    avg_dy = float(np.mean(dys))
    avg_div = float(np.mean(divs))
    if abs(avg_div) > max(abs(avg_dx), abs(avg_dy)) * 0.85 and abs(avg_div) > 0.12:
        motion_type = "zoom_in" if avg_div > 0 else "zoom_out"
        dom_dir = "in" if avg_div > 0 else "out"
    elif abs(avg_dx) >= abs(avg_dy) and abs(avg_dx) > 0.12:
        motion_type = "pan_right" if avg_dx > 0 else "pan_left"
        dom_dir = "right" if avg_dx > 0 else "left"
    elif abs(avg_dy) > 0.12:
        motion_type = "pan_down" if avg_dy > 0 else "pan_up"
        dom_dir = "down" if avg_dy > 0 else "up"
    else:
        motion_type = "kinetic_reveal"
        dom_dir = "center"

    return {
        "easing_guess": easing_guess,
        "motion_type": motion_type,
        "dominant_direction": dom_dir,
        "hold_frames": hold_frames,
        "peak_idx": peak_idx,
        "mean_speed_px": round(mean_sp, 3),
        "max_speed_px": round(max_sp, 3),
        "velocity_curve_norm": curve_norm,
    }


def _rgb_to_hex(rgb: np.ndarray) -> str:
    r, g, b = [int(np.clip(round(v), 0, 255)) for v in rgb]
    return f"#{r:02X}{g:02X}{b:02X}"


def _rel_luminance(rgb: np.ndarray) -> float:
    c = np.clip(rgb / 255.0, 0.0, 1.0)
    lin = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])


def _contrast_ratio(rgb1: np.ndarray, rgb2: np.ndarray) -> float:
    l1, l2 = _rel_luminance(rgb1), _rel_luminance(rgb2)
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 2)


def extract_design_tokens(frame_rgb: np.ndarray) -> dict[str, Any]:
    """Run foreground-aware K-Means palette extraction and active-region safe margin detection."""
    h, w, _ = frame_rgb.shape
    small = np.array(Image.fromarray(frame_rgb).resize((160, 90), Image.Resampling.BILINEAR), dtype=np.float32)
    pixels = small.reshape(-1, 3)

    # First estimate background from outer perimeter median
    small_3d = small
    border_pixels = np.concatenate(
        [small_3d[:3, :].reshape(-1, 3), small_3d[-3:, :].reshape(-1, 3), small_3d[:, :3].reshape(-1, 3), small_3d[:, -3:].reshape(-1, 3)],
        axis=0,
    )
    bg_est = np.median(border_pixels, axis=0)

    # Stratified sampling: 60% uniform + 40% high-contrast foreground pixels so bright hero type isn't swallowed
    rng = np.random.default_rng(42)
    uniform_idx = rng.choice(len(pixels), size=min(1500, len(pixels)), replace=False)
    dist_est = np.linalg.norm(pixels - bg_est[None, :], axis=1)
    fg_pool = np.where(dist_est > np.percentile(dist_est, 85))[0]
    if len(fg_pool) > 0:
        fg_idx = rng.choice(fg_pool, size=min(1000, len(fg_pool)), replace=True)
        pts = np.concatenate([pixels[uniform_idx], pixels[fg_idx]], axis=0)
    else:
        pts = pixels[uniform_idx]

    # Deterministic K-Means (k=5) seeded from quantiles of contrast distance
    k = 5
    pts_dist = np.linalg.norm(pts - bg_est[None, :], axis=1)
    q_order = np.argsort(pts_dist)
    centers = pts[q_order[np.linspace(0, len(pts) - 1, k, dtype=int)]].copy()
    for _ in range(15):
        dists = np.linalg.norm(pts[:, None, :] - centers[None, :, :], axis=2)
        labels = np.argmin(dists, axis=1)
        for ci in range(k):
            mask = labels == ci
            if np.any(mask):
                centers[ci] = np.mean(pts[mask], axis=0)

    dists_all = np.linalg.norm(pixels[:, None, :] - centers[None, :, :], axis=2)
    labels_all = np.argmin(dists_all, axis=1)
    counts = np.bincount(labels_all, minlength=k)
    order = np.argsort(-counts)
    sorted_centers = centers[order]

    # Background = cluster closest to perimeter median
    bg_cluster = int(np.argmin(np.linalg.norm(centers - bg_est[None, :], axis=1)))
    bg_rgb = centers[bg_cluster]

    # Ink = highest contrast vs bg; Accent = highest chroma not equal to bg
    best_ink = sorted_centers[0]
    best_cr = 1.0
    best_accent = sorted_centers[0]
    best_chroma = -1.0
    for c in sorted_centers:
        cr = _contrast_ratio(bg_rgb, c)
        if cr > best_cr:
            best_cr = cr
            best_ink = c
        chroma = float(np.max(c) - np.min(c))
        if np.linalg.norm(c - bg_rgb) > 28.0 and chroma > best_chroma:
            best_chroma = chroma
            best_accent = c

    # Safe margin detection: bounding box of high-contrast foreground pixels (ignoring subtle vignette/grain)
    diff_bg = np.linalg.norm(frame_rgb.astype(np.float32) - bg_rgb[None, None, :], axis=2)
    active = diff_bg > 56.0
    ys, xs = np.where(active)
    if len(xs) > 20:
        margins = {
            "top": round(float(np.min(ys) / h * 100.0), 1),
            "bottom": round(float((h - 1 - np.max(ys)) / h * 100.0), 1),
            "left": round(float(np.min(xs) / w * 100.0), 1),
            "right": round(float((w - 1 - np.max(xs)) / w * 100.0), 1),
        }
    else:
        margins = {"top": 50.0, "bottom": 50.0, "left": 50.0, "right": 50.0}

    return {
        "bg_hex": _rgb_to_hex(bg_rgb),
        "ink_hex": _rgb_to_hex(best_ink),
        "accent_hex": _rgb_to_hex(best_accent),
        "palette_hex": [_rgb_to_hex(c) for c in sorted_centers],
        "contrast_ratio": best_cr,
        "safe_margins_pct": margins,
    }


def save_shot_stills_and_filmstrip(
    frames: np.ndarray,
    speeds: np.ndarray,
    start_f: int,
    end_f: int,
    peak_local_f: int,
    fps: float,
    scene_id: str,
    stills_dir: Path,
    strips_dir: Path,
    n_tiles: int,
) -> tuple[dict[str, str], str]:
    """Save start/peak/hero/end stills and build an annotated contact sheet filmstrip."""
    span = max(1, end_f - start_f)
    hero_local = min(span - 1, max(peak_local_f, int(round(span * 0.65))))
    indices = {
        "start": start_f,
        "peak": min(end_f - 1, start_f + peak_local_f),
        "hero": min(end_f - 1, start_f + hero_local),
        "end": max(start_f, end_f - 1),
    }
    still_paths: dict[str, str] = {}
    for key, f_idx in indices.items():
        out_p = stills_dir / f"{scene_id}_{key}.png"
        Image.fromarray(frames[f_idx]).save(out_p)
        still_paths[key] = f"stills/{out_p.name}"

    # Build grid filmstrip
    tile_count = min(n_tiles, span)
    cols = 3 if tile_count >= 5 else max(1, tile_count)
    rows = math.ceil(tile_count / cols)
    tw, th = 426, 240
    pad = 8
    grid_w = cols * tw + (cols + 1) * pad
    grid_h = rows * th + (rows + 1) * pad
    sheet = Image.new("RGB", (grid_w, grid_h), (13, 17, 23))
    draw = ImageDraw.Draw(sheet)

    sample_indices = np.linspace(start_f, max(start_f, end_f - 1), tile_count, dtype=int)
    max_sp = max(1e-3, float(np.max(speeds[start_f:end_f])) if end_f > start_f else 1.0)
    for ti, f_idx in enumerate(sample_indices):
        r = ti // cols
        c = ti % cols
        x0 = pad + c * (tw + pad)
        y0 = pad + r * (th + pad)
        tile = Image.fromarray(frames[f_idx]).resize((tw, th), Image.Resampling.BILINEAR)
        sheet.paste(tile, (x0, y0))
        sp = float(speeds[f_idx]) if f_idx < len(speeds) else 0.0
        label = f"t={f_idx / fps:.2f}s  v={sp:.2f}px"
        draw.rectangle([x0 + 4, y0 + 4, x0 + 168, y0 + 24], fill=(8, 10, 15))
        draw.text((x0 + 8, y0 + 8), label, fill=(204, 255, 0))
        # Velocity meter bar
        bar_w = int(round((sp / max_sp) * 140))
        draw.rectangle([x0 + 4, y0 + 26, x0 + 4 + max(2, bar_w), y0 + 30], fill=(56, 189, 248))

    strip_path = strips_dir / f"filmstrip_{scene_id}.jpg"
    sheet.save(strip_path, quality=90)
    return still_paths, f"filmstrips/{strip_path.name}"


def analyze_audio(
    ffmpeg: str,
    hf_cmd: list[str] | None,
    video_path: Path,
    fps: float,
    n_frames: int,
    max_sec: float | None,
    enable_stt: bool,
    stt_model: str,
) -> dict[str, Any]:
    """Extract frame-aligned RMS envelope, HyperFrames beats/sections, and word-level STT."""
    result: dict[str, Any] = {
        "bpm": None,
        "beats_ms": [],
        "downbeats_ms": [],
        "onsets_ms": [],
        "rms_envelope": [],
        "words": [],
        "audio_engine": "ffmpeg_pcm",
        "stt_engine": "none",
    }

    # 1. Decode 16kHz mono PCM for RMS & STT
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error"]
    if max_sec is not None:
        cmd.extend(["-t", f"{max_sec:.3f}"])
    cmd.extend(["-i", str(video_path), "-vn", "-f", "s16le", "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", "-"])
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0 or not proc.stdout:
        return result

    pcm = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    samples_per_frame = max(1, int(round(16000.0 / fps)))
    rms_vals: list[float] = []
    for fi in range(n_frames):
        s0 = fi * samples_per_frame
        s1 = min(len(pcm), s0 + samples_per_frame)
        if s0 >= len(pcm):
            rms_vals.append(0.0)
        else:
            rms_vals.append(float(np.sqrt(np.mean(pcm[s0:s1] ** 2))))
    max_rms = max(1e-6, max(rms_vals) if rms_vals else 1.0)
    result["rms_envelope"] = [
        {"t_ms": int(round((fi / fps) * 1000)), "rms": round(v / max_rms, 4)} for fi, v in enumerate(rms_vals)
    ]

    # 2. HyperFrames beats/sections
    if hf_cmd:
        try:
            proc_hf = subprocess.run(
                [*hf_cmd, "audio", str(video_path), "--only", "beats,downbeats,bpm,onsets", "--json"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc_hf.returncode == 0 and proc_hf.stdout.strip():
                raw = json.loads(proc_hf.stdout)
                item = raw["items"][0] if "items" in raw else raw[0]
                result["bpm"] = item.get("bpm", {}).get("value")
                limit_ms = int(round(max_sec * 1000)) if max_sec else 10**9
                result["beats_ms"] = [
                    int(round(t * 1000)) for t in item.get("beats", {}).get("times", []) if t * 1000 <= limit_ms
                ]
                result["downbeats_ms"] = [
                    int(round(t * 1000)) for t in item.get("downbeats", {}).get("times", []) if t * 1000 <= limit_ms
                ]
                result["onsets_ms"] = [
                    {"t_ms": int(round(e["t"] * 1000)), "strength": round(float(e["strength"]), 3)}
                    for e in item.get("onsets", {}).get("events", [])
                    if e["t"] * 1000 <= limit_ms and e["strength"] >= 0.25
                ]
                result["audio_engine"] = "hyperframes_audio+ffmpeg_pcm"
        except Exception:
            pass

    # 3. Faster-Whisper word-level STT
    if enable_stt:
        try:
            from faster_whisper import WhisperModel  # type: ignore

            model = WhisperModel(stt_model, device="cpu", compute_type="int8", local_files_only=True)
            segments, _ = model.transcribe(pcm, word_timestamps=True, language="en")
            words: list[dict[str, Any]] = []
            for seg in segments:
                if seg.words:
                    for w in seg.words:
                        words.append(
                            {
                                "word": w.word.strip(),
                                "start_ms": int(round(w.start * 1000)),
                                "end_ms": int(round(w.end * 1000)),
                                "probability": round(float(w.probability), 3),
                            }
                        )
            result["words"] = words
            result["stt_engine"] = f"faster_whisper:{stt_model}"
        except Exception:
            result["stt_engine"] = "skipped_or_unavailable"

    return result


def run_hf_measure_forensics(
    hf_cmd: list[str] | None, video_path: Path, out_dir: Path, extract_strips: bool = False
) -> dict[str, Any]:
    """Run local open-source `hyperframes measure` probe, events --map, and optional event strips."""
    info: dict[str, Any] = {}
    if not hf_cmd:
        return info

    for key, subargs in (
        ("hf_probe", ["measure", "probe", str(video_path), "--json"]),
        ("hf_event_map", ["measure", "events", "--map", str(video_path), "--json"]),
    ):
        try:
            proc = subprocess.run([*hf_cmd, *subargs], capture_output=True, text=True, timeout=90)
            if proc.returncode == 0 and proc.stdout.strip():
                info[key] = json.loads(proc.stdout)
        except Exception:
            pass

    if extract_strips:
        strips_out = out_dir / "event_strips"
        strips_out.mkdir(parents=True, exist_ok=True)
        try:
            proc = subprocess.run(
                [*hf_cmd, "measure", "frames", "--events", str(video_path), "--out", str(strips_out), "--json"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.returncode == 0:
                info["hf_event_strips_dir"] = "event_strips"
        except Exception:
            pass
    return info


def decompile_video(args: argparse.Namespace) -> Path:
    """Run full Stage 1 decompilation and write MOTION_LEDGER.json."""
    ffmpeg, ffprobe = resolve_ffmpeg_binaries()
    hf_cmd = resolve_hyperframes_cmd()
    video_path = Path(args.video).resolve()
    out_dir = Path(args.out).resolve()
    stills_dir = out_dir / "stills"
    strips_dir = out_dir / "filmstrips"
    stills_dir.mkdir(parents=True, exist_ok=True)
    strips_dir.mkdir(parents=True, exist_ok=True)

    meta = probe_video(ffprobe, video_path)
    effective_dur = min(meta["duration_sec"], args.max_sec) if args.max_sec else meta["duration_sec"]
    fps = meta["fps"]

    hf_forensics = (
        {}
        if args.no_hf_measure
        else run_hf_measure_forensics(hf_cmd, video_path, out_dir, extract_strips=args.event_strips)
    )

    shots, cut_engine = detect_cuts(ffmpeg, hf_cmd, video_path, effective_dur, fps, args.scene_thresh)
    frames, pw, ph = decode_proxy_frames(
        ffmpeg, video_path, meta["width"], meta["height"], fps, args.proxy_height, args.max_sec
    )
    n_frames = len(frames)

    # Compute per-frame optical flow velocity across whole proxy clip
    grays = (0.299 * frames[..., 0] + 0.587 * frames[..., 1] + 0.114 * frames[..., 2]).astype(np.float32)
    speeds = np.zeros(n_frames, dtype=np.float32)
    dxs = np.zeros(n_frames, dtype=np.float32)
    dys = np.zeros(n_frames, dtype=np.float32)
    divs = np.zeros(n_frames, dtype=np.float32)
    for fi in range(1, n_frames):
        sp, _, dx, dy, dv = _optical_flow_pair(grays[fi - 1], grays[fi])
        speeds[fi] = sp
        dxs[fi] = dx
        dys[fi] = dy
        divs[fi] = dv

    audio_data = (
        analyze_audio(ffmpeg, hf_cmd, video_path, fps, n_frames, args.max_sec, not args.no_stt, args.stt_model)
        if meta["has_audio"]
        else {
            "bpm": None,
            "beats_ms": [],
            "downbeats_ms": [],
            "onsets_ms": [],
            "rms_envelope": [],
            "words": [],
            "audio_engine": "none",
            "stt_engine": "none",
        }
    )

    kinetic_shots: list[dict[str, Any]] = []
    brand_shots: list[dict[str, Any]] = []
    all_palette_hex: list[str] = []
    seam_probes_dir = out_dir / "seam_probes"
    seam_probe_files: list[str] = []
    if args.seam_probes or args.seam_probe is not None:
        seam_probes_dir.mkdir(parents=True, exist_ok=True)
    if args.seam_probe is not None:
        custom_name = extract_seam_probe(
            ffmpeg, video_path, float(args.seam_probe), effective_dur, seam_probes_dir / "seam_custom.png"
        )
        if custom_name:
            seam_probe_files.append(f"seam_probes/{custom_name}")

    for idx, shot in enumerate(shots):
        sf = max(0, min(n_frames - 1, int(round(shot["start_sec"] * fps))))
        ef = max(sf + 1, min(n_frames, int(round(shot["end_sec"] * fps))))

        # Exclude frame `sf` (inter-shot cut jump) when measuring intra-shot velocity
        flow_start = sf + 1 if (sf > 0 and ef - sf > 2) else sf
        kin = classify_easing_and_motion(
            speeds[flow_start:ef], dxs[flow_start:ef], dys[flow_start:ef], divs[flow_start:ef]
        )
        peak_local_in_shot = (flow_start - sf) + kin["peak_idx"]
        peak_abs = min(n_frames - 1, sf + peak_local_in_shot)
        still_paths, strip_rel = save_shot_stills_and_filmstrip(
            frames, speeds, sf, ef, peak_local_in_shot, fps, shot["scene_id"], stills_dir, strips_dir, args.filmstrip_frames
        )

        seam_probe_rel: str | None = None
        if args.seam_probes and idx > 0 and len(seam_probe_files) < args.seam_probe_max:
            probe_name = extract_seam_probe(
                ffmpeg,
                video_path,
                shot["start_sec"],
                effective_dur,
                seam_probes_dir / f"seam_{shot['scene_id']}.png",
            )
            if probe_name:
                seam_probe_rel = f"seam_probes/{probe_name}"
                seam_probe_files.append(seam_probe_rel)

        hero_idx = min(n_frames - 1, sf + max(peak_local_in_shot, int(round((ef - sf) * 0.65))))
        tokens = extract_design_tokens(frames[hero_idx])
        for hx in tokens["palette_hex"]:
            if hx not in all_palette_hex:
                all_palette_hex.append(hx)

        shot_words = [
            w for w in audio_data["words"] if shot["start_ms"] - 80 <= w["start_ms"] < shot["end_ms"]
        ]
        hold_ms = int(round((kin["hold_frames"] / fps) * 1000))
        beat_hits = [b for b in audio_data["beats_ms"] if shot["start_ms"] <= b < shot["end_ms"]]

        kinetic_shots.append(
            {
                "scene_id": shot["scene_id"],
                "start_ms": shot["start_ms"],
                "end_ms": shot["end_ms"],
                "duration_ms": shot["duration_ms"],
                "hold_ms": hold_ms,
                "hold_ratio": round(hold_ms / max(1, shot["duration_ms"]), 3),
                "peak_velocity_ms": int(round((peak_abs / fps) * 1000)),
                "mean_speed_px": kin["mean_speed_px"],
                "max_speed_px": kin["max_speed_px"],
                "motion_type": kin["motion_type"],
                "dominant_direction": kin["dominant_direction"],
                "easing_guess": kin["easing_guess"],
                "transition_in": shot["transition_in"],
                "beats_in_shot_ms": beat_hits,
                "velocity_curve_norm": kin["velocity_curve_norm"],
            }
        )

        brand_shots.append(
            {
                "scene_id": shot["scene_id"],
                **tokens,
                "transcript_segment": " ".join(w["word"] for w in shot_words),
                "word_cues": shot_words,
                "stills": still_paths,
                "filmstrip": strip_rel,
                **({"seam_probe": seam_probe_rel} if seam_probe_rel else {}),
            }
        )

    ledger = {
        "schema_version": "1.0.0",
        "metadata": {
            "source_video": str(video_path),
            "width": meta["width"],
            "height": meta["height"],
            "proxy_size": f"{pw}x{ph}",
            "fps": fps,
            "fps_rational": meta["fps_rational"],
            "duration_sec": round(effective_dur, 4),
            "duration_ms": int(round(effective_dur * 1000)),
            "has_audio": meta["has_audio"],
            "engines": {
                "shot_slicer": cut_engine,
                "optical_flow": "cv2_farneback" if HAS_CV2 else "numpy_scipy_lucas_kanade",
                "audio_rhythm": audio_data["audio_engine"],
                "stt": audio_data["stt_engine"],
            },
            **({"seam_probes": seam_probe_files} if seam_probe_files else {}),
            **({"hf_probe": hf_forensics["hf_probe"]} if "hf_probe" in hf_forensics else {}),
            **({"hf_event_strips_dir": hf_forensics["hf_event_strips_dir"]} if "hf_event_strips_dir" in hf_forensics else {}),
        },
        "KINETIC_DNA": {
            "bpm": audio_data["bpm"],
            "beats_ms": audio_data["beats_ms"],
            "downbeats_ms": audio_data["downbeats_ms"],
            "onsets_ms": audio_data["onsets_ms"],
            "rms_envelope": audio_data["rms_envelope"],
            "shots": kinetic_shots,
            **({"hf_event_map": hf_forensics["hf_event_map"]} if "hf_event_map" in hf_forensics else {}),
        },
        "BRAND_SKIN": {
            "global_palette_hex": all_palette_hex[:10],
            "shots": brand_shots,
        },
    }

    ledger_path = out_dir / "MOTION_LEDGER.json"
    ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    return ledger_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Motion-REA Stage 1: Deterministic Video & Audio Decompiler")
    parser.add_argument("video", help="Path to reference MP4 video")
    parser.add_argument("--out", default=".motion_rea", help="Output directory for MOTION_LEDGER.json & stills")
    parser.add_argument("--proxy-height", type=int, default=360, help="Proxy frame height for CPU analysis")
    parser.add_argument("--scene-thresh", type=float, default=0.14, help="FFmpeg scene cut threshold (0.10-0.35)")
    parser.add_argument("--filmstrip-frames", type=int, default=9, help="Frames per shot filmstrip grid")
    parser.add_argument("--max-sec", type=float, default=None, help="Optional max seconds from start to analyze")
    parser.add_argument("--stt-model", default="small.en", help="faster-whisper model name")
    parser.add_argument("--no-stt", action="store_true", help="Skip word-level STT extraction")
    parser.add_argument("--seam-probes", action="store_true", help="Extract 30fps tile=6x5 contact sheets across hard-cut seams")
    parser.add_argument("--seam-probe", type=float, default=None, help="Extract one 30fps tile=6x5 seam probe centered at timestamp (sec)")
    parser.add_argument("--seam-probe-max", type=int, default=8, help="Max seam probe grids to extract when --seam-probes is set")
    parser.add_argument("--event-strips", action="store_true", help="Extract native consecutive frame strips per event via hyperframes measure frames --events")
    parser.add_argument("--no-hf-measure", action="store_true", help="Skip calling local hyperframes measure probe/events CLI")
    args = parser.parse_args()

    ledger_path = decompile_video(args)
    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "ok": True,
                "ledger": str(ledger_path),
                "shots": len(data["KINETIC_DNA"]["shots"]),
                "bpm": data["KINETIC_DNA"]["bpm"],
                "beats": len(data["KINETIC_DNA"]["beats_ms"]),
                "engines": data["metadata"]["engines"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
