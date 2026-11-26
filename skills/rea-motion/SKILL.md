---
name: rea-motion
description: Unified REA Motion (Hybrid 80/20 Video Engineering Pipeline) built on HyperFrames, launch-video-clone CV tracking, reelmimic-styles art mediums, beats.py sub-bass telemetry, VIDEO_MANIFEST.md anti-slop contracts, and closed-loop visual QA. Use whenever the user asks to clone a reference motion video, build a beat-synced lyric/launch film, transfer a YouTube/explainer pacing style, or verify a HyperFrames composition with REA Motion.
---

# REA Motion — Hybrid 80/20 Kinetic Video Pipeline

**REA Motion** applies the **Evidence → Reconstruct → Closed-Loop Verify** philosophy of Reverse Engineer Anything (REA) to motion graphics, product launches, explainers, and beat-synced lyric films on Windows + HyperFrames.

## 1. Before Writing Any Code (Evidence & Guardrails)
1. **Read Compound Lessons:** Load `GLOBAL_LESSONS.md` (and `brands/*.md` if using a saved brand skin).
2. **Create `VIDEO_MANIFEST.md`:** Copy `templates/VIDEO_MANIFEST.template.md` into the project root to lock `Brand Skin`, `Kinetic DNA`, and the `Anti-Slop Banned List`.
3. **Measure, Never Guess:**
   - **Reference Video Clone (1:1 / Re-skin):** Activate `launch-video-clone` — run `burst.py`, `camtrack.py` / `camtrack_sift.py`, `cursortrack.py`, `colormatch.py` (or `hyperframes-motion-rea/scripts/decompile.py` for `MOTION_LEDGER.json`).
   - **Style / Medium Transfer (Original Content):** Activate `reelmimic-styles` and load ONLY the matching `modules/<slug>/SKILL.md` (`faceless-explainer`, `paper-cutout`, `cut-the-curve`, `motion-doctrine`, `seam-craft`, `anime-cel`, `whiteboard`, etc.).
   - **Audio / Beat Sync:** Run `scripts/beats.py <audio_or_video> --out beats.json` for `bpm`, `beats_ms`, `kick_hits_ms` (`20–150 Hz`), `snare_hits_ms`, and per-frame `rms`.

## 2. Deterministic HyperFrames Build Rules
- Bind GSAP (`tl.seek(t)`) and Three.js (`window.addEventListener("hf-seek", ...)`, `preserveDrawingBuffer: true`) to the paused virtual clock.
- Enable `data-motion-blur="on"` (`data-motion-blur-shutter="360"`) on `#root` for fast 2D moves.
- Include `<link rel="icon" href="data:," />` in `<head>` and explicit `width="256" height="256"` + `background-size: 256px 256px` on 35mm SVG `feTurbulence` grain.
- Hold landed hero headlines dead-still (`0.5s + 0.3s/word`, `>= 2.0s` on closing lines).

## 3. Tiered Closed-Loop QA (Low-Memory Safe)
1. **Gate 1 (Fast Stills & Anti-Slop):**
   - `python scripts/unslop_check.py <comp_dir>` (`0` errors)
   - `npx hyperframes check --json` (`0` errors)
   - `npx hyperframes snapshot --at="..."` (+ `hyperframes-motion-rea/scripts/visual_diff.py stills` when cloning)
2. **Gate 2 (Motion Trajectory & Parity):**
   - `powershell -ExecutionPolicy Bypass -File "<skills>/launch-video-clone/scripts/round.ps1" <project> <renders> v1` (runs draft render, `burst.py`, `compare.py`, `sbs.py`)
   - For short clips `<= 10s` needing 8x subframe supersampling: `round_mb.ps1`
3. **Gate 3 (3D CDP & Final Delivery):**
   - `powershell -ExecutionPolicy Bypass -File "scripts/Run-BrainAutopilotVerify.ps1" -CompositionDir <comp_dir>` (run alone, never concurrently with `snapshot`)
   - Final render: `npx hyperframes render --quality delivery --low-memory-mode -o renders/final.mp4`
4. **Learn:** Append new verified findings to `GLOBAL_LESSONS.md`.
