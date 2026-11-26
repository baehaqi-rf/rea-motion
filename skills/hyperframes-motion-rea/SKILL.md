---
name: hyperframes-motion-rea
description: Motion-REA (Kinetic Decompiler Pipeline) for HyperFrames — decompiles flat MP4 reference videos and audio into a deterministic MOTION_LEDGER.json (KINETIC_DNA vs BRAND_SKIN) using shot slicing, optical-flow velocity/easing telemetry, beat/RMS/STT extraction, and design tokens, then verifies HyperFrames renders via Visual Closed-Loop QA (SSIM, edge alignment, temporal lag check, and side-by-side [Ref | Render | Diff] sheets).
---

# HyperFrames Motion-REA (Kinetic Decompiler Pipeline)

Motion-REA prevents *AI slop* when reconstructing or style-transferring motion graphics in HyperFrames. Instead of feeding raw video to an LLM to guess timing, easing, and proportions, run the deterministic 3-stage pipeline:

1. **Stage 1 — Inspect (`scripts/decompile.py`):** Decompile reference MP4 + audio into `MOTION_LEDGER.json`, hero keyframes, and 6–9 frame filmstrips.
2. **Stage 2 — Hybrid Synthesis (HyperFrames):** Build modular HyperFrames scenes (`GSAP` + `Three.js` + `Media Plates`) strictly bound to `KINETIC_DNA` (`start_ms`, `duration_ms`, `easing_guess`, `beats_ms`) and `BRAND_SKIN`.
3. **Stage 3 — Visual Closed-Loop QA (`scripts/visual_diff.py`):** Compare `[Ref | Render]` stills (Gate 1) and 4fps motion strips (Gate 2) with SSIM, Sobel edge alignment, and $\pm 3$-frame temporal lag detection before running a full MP4 render.

---

## Stage 1: Deterministic Video & Audio Decompiler

Run on any reference clip (ideally downscaled proxy analysis on CPU):

```bash
python "<SKILL_DIR>/scripts/decompile.py" "<ref.mp4>" --out "<project>/.motion_rea"
```

Useful flags:
- `--proxy-height 360`: Proxy resolution for optical-flow & K-Means speed (default `360`).
- `--scene-thresh 0.25`: Shot cut sensitivity (`0.18–0.35`).
- `--filmstrip-frames 9`: Frames per shot contact sheet (`6` or `9`).
- `--max-sec 10`: Limit analysis to the first `N` seconds (handy for long reels).
- `--no-stt`: Skip `faster-whisper` word-level STT when analyzing silent UI motion.

### What `decompile.py` produces
- `MOTION_LEDGER.json` (see `references/ledger-schema.md`):
  - **`KINETIC_DNA`:** Per-shot `start_ms`, `end_ms`, `duration_ms`, `hold_ms`, `easing_guess` (`power4.out`, `expo.out`, `power2.inOut`, `power3.in`, `back.out(1.4)`, `none`), `motion_type` (`pan_left`, `pan_right`, `zoom_in`, `zoom_out`, `kinetic_reveal`, `static_hold`), `peak_velocity_ms`, `beats_ms`, `rms_per_frame`.
  - **`BRAND_SKIN`:** Dominant Hex palette (`bg_hex`, `ink_hex`, `accent_hex`), WCAG contrast ratio, `safe_margins_pct`, `word_cues`, and paths to `hero_frame` / `filmstrip`.
- `filmstrips/filmstrip_scXX.jpg`: Annotated motion trajectory grid per shot.
- `stills/sc_XX_hero.png`: Peak settled frame per shot for Gate 1 QA.

---

## Stage 2: HyperFrames Hybrid Synthesis Rules

1. **Deterministic Clock Binding:** Bind GSAP (`tl.seek(t)`) and Three.js (`window.addEventListener("hf-seek", ...)`) strictly to timeline seconds derived from `KINETIC_DNA.shots[]`. Never use `requestAnimationFrame` or `repeat: -1`.
2. **Exact Easing & Hold Mapping:**
   - Map `easing_guess` directly into `gsap.fromTo(...)`.
   - Enforce dead-still holds matching `hold_ms` once hero typography lands.
   - Snap chorus/beat cuts to `KINETIC_DNA.beats_ms` (start entrances 40–120 ms before a hit, land `tl.set` on the hit).
3. **Hybrid Plate + Code:** Keep complex 3D/photorealistic subjects as high-res image/video media plates (or lightweight Three.js hero objects) and drive camera moves, `data-motion-blur="on"` (shutter `360`), glassmorphism, and typography in HyperFrames DOM/GSAP.
4. **Style-Transfer:** Keep `KINETIC_DNA` untouched and swap only `BRAND_SKIN` tokens (`colors`, `fonts`, `copy`, `media`) when adapting a reference template to a new brand.

---

## Stage 3: Visual Closed-Loop QA ("Motion-Autopilot")

### Gate 1 — Stills Before Motion (Hero Composition Audit)
Render only the hero timestamps via `hyperframes snapshot --at=...`, then compare against `stills/sc_XX_hero.png`:

```bash
python "<SKILL_DIR>/scripts/visual_diff.py" stills \
  --ref "<project>/.motion_rea/stills/sc_01_hero.png" \
  --render "<project>/composition/qa_stills/frame-00-at-1.2s.png" \
  --out "<project>/.motion_rea/qa_gate1"
```

### Gate 2 — Filmstrip Motion Audit (4 fps Trajectory & Lag Diff)
After rendering a draft MP4 (or range), run frame-by-frame SSIM, Sobel edge alignment, and $\pm 3$-frame temporal lag audit:

```bash
python "<SKILL_DIR>/scripts/visual_diff.py" video \
  --ref "<ref.mp4>" \
  --render "<render.mp4>" \
  --out "<project>/.motion_rea/qa_gate2" \
  --fps 4 \
  --ssim-thresh 0.80
```

### Gate 3 — Auto-Patch Loop
Inspect `<qa_dir>/qa_report.json` and the generated `[Ref | Render | Diff]` comparison image:
- `best_temporal_match_offset_ms != 0`: Shift GSAP tween start or clip `data-start` by that delta.
- `edge_iou < 0.45`: Adjust layout scale, font size, or element alignment.
- `abs(luma_delta) > 15`: Tune scrim opacity or palette tokens.
- Once all shots clear `passed: true`, run `npx hyperframes check --json` and execute the final `delivery` MP4 render.
