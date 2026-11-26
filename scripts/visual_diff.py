#!/usr/bin/env python3
"""
Stage 3 of Motion-REA: Visual Closed-Loop QA (`visual_diff.py`).

Supports:
  - `stills`: Gate 1 hero-frame parity check ([Ref | Render | Diff Heatmap] + SSIM + Sobel Edge IoU)
  - `video`:  Gate 2 4fps filmstrip parity check + +/-3 frame temporal lag detector
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, sobel

try:
    from skimage.metrics import structural_similarity as skimage_ssim  # type: ignore

    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False


def resolve_ffmpeg() -> str:
    """Locate ffmpeg binary, including Windows WinGet packages."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg and os.name == "nt":
        winget_root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        if winget_root.is_dir():
            for exe in winget_root.rglob("ffmpeg.exe"):
                ffmpeg = str(exe)
                break
    if not ffmpeg:
        raise FileNotFoundError("ffmpeg is required on PATH (or via WinGet Gyan.FFmpeg).")
    return ffmpeg


def compute_ssim(img_a_rgb: np.ndarray, img_b_rgb: np.ndarray) -> float:
    """Compute Wang et al. (2004) SSIM on luminance [0..255] in [0, 1]."""
    ya = 0.299 * img_a_rgb[..., 0] + 0.587 * img_a_rgb[..., 1] + 0.114 * img_a_rgb[..., 2]
    yb = 0.299 * img_b_rgb[..., 0] + 0.587 * img_b_rgb[..., 1] + 0.114 * img_b_rgb[..., 2]

    if HAS_SKIMAGE:
        return float(skimage_ssim(ya, yb, data_range=255.0))

    ya = ya.astype(np.float64)
    yb = yb.astype(np.float64)
    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2

    mu1 = gaussian_filter(ya, sigma=1.5)
    mu2 = gaussian_filter(yb, sigma=1.5)
    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = gaussian_filter(ya * ya, sigma=1.5) - mu1_sq
    sigma2_sq = gaussian_filter(yb * yb, sigma=1.5) - mu2_sq
    sigma12 = gaussian_filter(ya * yb, sigma=1.5) - mu1_mu2

    num = (2.0 * mu1_mu2 + c1) * (2.0 * sigma12 + c2)
    den = (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)
    ssim_map = num / np.maximum(den, 1e-12)
    return float(np.mean(ssim_map))


def compute_edge_alignment(img_a_rgb: np.ndarray, img_b_rgb: np.ndarray) -> float:
    """Compute Sobel edge IoU to verify typography & geometry alignment."""
    ya = (0.299 * img_a_rgb[..., 0] + 0.587 * img_a_rgb[..., 1] + 0.114 * img_a_rgb[..., 2]).astype(np.float32)
    yb = (0.299 * img_b_rgb[..., 0] + 0.587 * img_b_rgb[..., 1] + 0.114 * img_b_rgb[..., 2]).astype(np.float32)

    ga = np.hypot(sobel(ya, axis=0), sobel(ya, axis=1))
    gb = np.hypot(sobel(yb, axis=0), sobel(yb, axis=1))

    ta = ga > max(20.0, float(np.percentile(ga, 85)))
    tb = gb > max(20.0, float(np.percentile(gb, 85)))
    union = int(np.sum(ta | tb))
    if union == 0:
        return 1.0
    return float(np.sum(ta & tb) / union)


def make_diff_heatmap(img_a_rgb: np.ndarray, img_b_rgb: np.ndarray) -> np.ndarray:
    """Create a false-color RGB error heatmap from absolute pixel difference."""
    err = np.mean(np.abs(img_a_rgb.astype(np.float32) - img_b_rgb.astype(np.float32)), axis=2)
    norm = np.clip(err / 96.0, 0.0, 1.0)
    heat = np.zeros_like(img_a_rgb, dtype=np.uint8)
    heat[..., 0] = np.clip(norm * 255.0 * 1.4, 0, 255).astype(np.uint8)
    heat[..., 1] = np.clip((norm - 0.35) * 255.0 * 1.5, 0, 255).astype(np.uint8)
    heat[..., 2] = np.clip((1.0 - norm) * 60.0 + norm * 90.0, 0, 255).astype(np.uint8)
    return heat


def compare_pair(ref_rgb: np.ndarray, ren_rgb: np.ndarray) -> dict[str, Any]:
    """Compare two same-size RGB frames and produce metrics + patch hints."""
    ssim_val = compute_ssim(ref_rgb, ren_rgb)
    edge_iou = compute_edge_alignment(ref_rgb, ren_rgb)

    ya = 0.299 * ref_rgb[..., 0] + 0.587 * ref_rgb[..., 1] + 0.114 * ref_rgb[..., 2]
    yb = 0.299 * ren_rgb[..., 0] + 0.587 * ren_rgb[..., 1] + 0.114 * ren_rgb[..., 2]
    luma_delta = float(np.mean(yb) - np.mean(ya))
    mae = float(np.mean(np.abs(ren_rgb.astype(np.float32) - ref_rgb.astype(np.float32))))

    hints: list[str] = []
    if abs(luma_delta) > 15.0:
        direction = "brighter" if luma_delta > 0 else "darker"
        hints.append(f"Render is {direction} than reference (luma_delta={luma_delta:+.1f}); adjust scrim or ground tone.")
    if edge_iou < 0.45:
        hints.append(f"Low edge alignment (edge_iou={edge_iou:.3f}); check font size, element scale, or position.")
    if mae > 24.0:
        hints.append(f"High pixel MAE ({mae:.1f}); inspect diff heatmap for misaligned or missing foreground elements.")

    return {
        "ssim": round(ssim_val, 4),
        "edge_iou": round(edge_iou, 4),
        "luma_delta": round(luma_delta, 2),
        "mae": round(mae, 2),
        "patch_hints": hints,
    }


def render_triptych(
    ref_rgb: np.ndarray, ren_rgb: np.ndarray, out_path: Path, title: str, metrics: dict[str, Any], tile_w: int = 640
) -> None:
    """Save a [Reference | Render | Diff Heatmap] side-by-side image with metrics banner."""
    h, w, _ = ref_rgb.shape
    tile_h = int(round(tile_w * h / max(1, w)))
    heat_rgb = make_diff_heatmap(ref_rgb, ren_rgb)

    pad = 12
    banner_h = 44
    canvas = Image.new("RGB", (tile_w * 3 + pad * 4, tile_h + banner_h + pad * 2), (10, 12, 18))
    draw = ImageDraw.Draw(canvas)

    status = f"{title}   |   SSIM: {metrics['ssim']:.4f}   Edge IoU: {metrics['edge_iou']:.3f}   Luma dY: {metrics['luma_delta']:+.1f}"
    draw.text((pad, 14), status, fill=(204, 255, 0) if metrics["ssim"] >= 0.80 else (251, 113, 133))

    for idx, (arr, tag) in enumerate([(ref_rgb, "REFERENCE"), (ren_rgb, "HYPERFRAMES"), (heat_rgb, "DIFF HEATMAP")]):
        x0 = pad + idx * (tile_w + pad)
        y0 = banner_h
        tile = Image.fromarray(arr).resize((tile_w, tile_h), Image.Resampling.BILINEAR)
        canvas.paste(tile, (x0, y0))
        draw.rectangle([x0 + 6, y0 + 6, x0 + 132, y0 + 26], fill=(8, 10, 15))
        draw.text((x0 + 12, y0 + 10), tag, fill=(244, 241, 234))

    canvas.save(out_path, quality=92)


def run_stills(args: argparse.Namespace) -> dict[str, Any]:
    """Gate 1: Compare single or directory of hero still PNG/JPG pairs."""
    ref_p = Path(args.ref).resolve()
    ren_p = Path(args.render).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    pairs: list[tuple[Path, Path]] = []
    if ref_p.is_file() and ren_p.is_file():
        pairs.append((ref_p, ren_p))
    elif ref_p.is_dir() and ren_p.is_dir():
        ref_files = sorted(p for p in ref_p.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
        ren_files = sorted(p for p in ren_p.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
        for rf, nf in zip(ref_files, ren_files):
            pairs.append((rf, nf))
    else:
        raise ValueError("--ref and --render must both be files or both be directories.")

    results: list[dict[str, Any]] = []
    for idx, (rf, nf) in enumerate(pairs):
        ref_img = Image.open(rf).convert("RGB")
        ren_img = Image.open(nf).convert("RGB").resize(ref_img.size, Image.Resampling.BILINEAR)
        ref_arr = np.array(ref_img)
        ren_arr = np.array(ren_img)
        m = compare_pair(ref_arr, ren_arr)
        passed = m["ssim"] >= args.ssim_thresh
        sheet_path = out_dir / f"gate1_pair_{idx:02d}.jpg"
        render_triptych(ref_arr, ren_arr, sheet_path, f"GATE 1 #{idx}", m)
        results.append({"ref": str(rf), "render": str(nf), "sheet": str(sheet_path), "passed": passed, **m})

    mean_ssim = float(np.mean([r["ssim"] for r in results])) if results else 0.0
    report = {
        "gate": "gate1_stills",
        "ssim_threshold": args.ssim_thresh,
        "mean_ssim": round(mean_ssim, 4),
        "passed": all(r["passed"] for r in results) if results else False,
        "pairs": results,
    }
    (out_dir / "qa_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _decode_sampled_frames(ffmpeg: str, video_path: Path, fps: float, max_sec: float | None, width: int = 640, height: int = 360) -> np.ndarray:
    """Decode video frames at sample rate `fps` into (N, H, W, 3) numpy array."""
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error"]
    if max_sec is not None:
        cmd.extend(["-t", f"{max_sec:.3f}"])
    cmd.extend(
        [
            "-i",
            str(video_path),
            "-vf",
            f"fps={fps:.3f},scale={width}:{height}:flags=bilinear",
            "-pix_fmt",
            "rgb24",
            "-f",
            "rawvideo",
            "-",
        ]
    )
    proc = subprocess.run(cmd, capture_output=True, check=True)
    fb = width * height * 3
    n = len(proc.stdout) // fb
    return np.frombuffer(proc.stdout[: n * fb], dtype=np.uint8).reshape((n, height, width, 3))


def run_video(args: argparse.Namespace) -> dict[str, Any]:
    """Gate 2: Sample both videos at N fps, compute SSIM + +/-3 frame lag check + grid sheet."""
    ffmpeg = resolve_ffmpeg()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ref_frames = _decode_sampled_frames(ffmpeg, Path(args.ref).resolve(), args.fps, args.max_sec)
    ren_frames = _decode_sampled_frames(ffmpeg, Path(args.render).resolve(), args.fps, args.max_sec)
    n = min(len(ref_frames), len(ren_frames))
    if n == 0:
        raise RuntimeError("Failed to decode frames from reference or render video.")

    frame_reports: list[dict[str, Any]] = []
    lags: list[int] = []
    worst_idx = 0
    worst_ssim = 2.0

    for i in range(n):
        m = compare_pair(ref_frames[i], ren_frames[i])
        # +/- 3 frame temporal lag probe
        best_lag = 0
        best_lag_ssim = m["ssim"]
        for lag in (-3, -2, -1, 1, 2, 3):
            ri = i + lag
            if 0 <= ri < len(ref_frames):
                s = compute_ssim(ref_frames[ri], ren_frames[i])
                if s > best_lag_ssim + 0.015:
                    best_lag_ssim = s
                    best_lag = lag
        lag_ms = int(round((best_lag / args.fps) * 1000))
        lags.append(lag_ms)
        if best_lag != 0:
            m["patch_hints"].append(
                f"Frame matches reference shifted by {lag_ms:+d}ms ({best_lag:+d} sample frames); adjust GSAP start offset."
            )

        if m["ssim"] < worst_ssim:
            worst_ssim = m["ssim"]
            worst_idx = i

        frame_reports.append(
            {
                "frame_idx": i,
                "t_sec": round(i / args.fps, 3),
                "best_temporal_match_offset_ms": lag_ms,
                "passed": m["ssim"] >= args.ssim_thresh,
                **m,
            }
        )

    # Save triptych for worst-scoring frame + start/mid/end summary grid
    worst_path = out_dir / "gate2_worst_frame.jpg"
    render_triptych(
        ref_frames[worst_idx],
        ren_frames[worst_idx],
        worst_path,
        f"WORST @ {worst_idx / args.fps:.2f}s",
        frame_reports[worst_idx],
    )

    sample_grid_indices = np.linspace(0, n - 1, min(6, n), dtype=int)
    grid_rows: list[Image.Image] = []
    for gi in sample_grid_indices:
        tmp_p = out_dir / f"_tmp_tile_{gi}.jpg"
        render_triptych(ref_frames[gi], ren_frames[gi], tmp_p, f"t={gi / args.fps:.2f}s", frame_reports[gi], tile_w=420)
        grid_rows.append(Image.open(tmp_p).convert("RGB"))
        tmp_p.unlink(missing_ok=True)

    if grid_rows:
        gw = max(im.width for im in grid_rows)
        gh = sum(im.height for im in grid_rows)
        sheet = Image.new("RGB", (gw, gh), (10, 12, 18))
        y_off = 0
        for im in grid_rows:
            sheet.paste(im, (0, y_off))
            y_off += im.height
        sheet.save(out_dir / "gate2_filmstrip_diff.jpg", quality=90)

    mean_ssim = float(np.mean([f["ssim"] for f in frame_reports]))
    min_ssim = float(np.min([f["ssim"] for f in frame_reports]))
    mean_edge = float(np.mean([f["edge_iou"] for f in frame_reports]))

    report = {
        "gate": "gate2_video",
        "sample_fps": args.fps,
        "frames_checked": n,
        "ssim_threshold": args.ssim_thresh,
        "mean_ssim": round(mean_ssim, 4),
        "min_ssim": round(min_ssim, 4),
        "mean_edge_iou": round(mean_edge, 4),
        "median_temporal_offset_ms": int(round(float(np.median(lags)))),
        "passed": mean_ssim >= args.ssim_thresh,
        "worst_frame_sheet": str(worst_path),
        "filmstrip_sheet": str(out_dir / "gate2_filmstrip_diff.jpg"),
        "frames": frame_reports,
    }
    (out_dir / "qa_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Motion-REA Stage 3: Visual Closed-Loop QA")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_stills = sub.add_parser("stills", help="Gate 1: Compare still image pairs")
    p_stills.add_argument("--ref", required=True, help="Reference image or folder")
    p_stills.add_argument("--render", required=True, help="Rendered image or folder")
    p_stills.add_argument("--out", default=".motion_rea/qa_gate1", help="QA output folder")
    p_stills.add_argument("--ssim-thresh", type=float, default=0.85, help="Minimum passing SSIM")

    p_vid = sub.add_parser("video", help="Gate 2: Compare reference vs render video at N fps")
    p_vid.add_argument("--ref", required=True, help="Reference MP4")
    p_vid.add_argument("--render", required=True, help="Rendered MP4")
    p_vid.add_argument("--out", default=".motion_rea/qa_gate2", help="QA output folder")
    p_vid.add_argument("--fps", type=float, default=4.0, help="Sampling rate (fps)")
    p_vid.add_argument("--ssim-thresh", type=float, default=0.80, help="Minimum passing mean SSIM")
    p_vid.add_argument("--max-sec", type=float, default=None, help="Optional max seconds to compare")

    args = parser.parse_args()
    report = run_stills(args) if args.mode == "stills" else run_video(args)
    summary = {k: v for k, v in report.items() if k not in {"frames", "pairs"}}
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
