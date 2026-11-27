# Global Compound Lessons — Local Video Studio (Hybrid 80/20 Stack)

Persistent engineering & motion-craft rules learned across production runs (`launch-video-clone` + `reelmimic-styles` + `Motion-REA` + `Brain Autopilot`). Read before starting a new video; append new verified discoveries at the end of a run.

## 1. Windows 11 & HyperFrames Runtime Invariants
- **Favicon 404 Guard:** Always place `<link rel="icon" href="data:," />` in `<head>` so live HTTP preview and Brain Autopilot CDP never log a `404 /favicon.ico`.
- **PowerShell Comma Arguments:** Always quote `--at="0.45,1.8,4.6"` with `=` so PowerShell does not split comma-separated numbers into `Object[]`.
- **Sub-Composition CSS Scoping in `?autopilot=1`:** When mounting `<template>` sub-compositions in plain HTTP preview, rewrite `#root` in both `<style>` and `<script>` to `#<comp-id>-root` and set `pointer-events: auto !important` on `#director-hud` so `pointer-events: none` never occludes HUD controls.
- **35mm Film Grain Performance:** Always give SVG `feTurbulence` grain explicit `width='256' height='256'` and `background-size: 256px 256px; background-repeat: repeat;` plus finite CSS keyframe steps (`steps(1) N both`). Unsized SVG filters rasterize across 3840×2160 on every frame (~120× slower).
- **8 GB RAM Safe Render Profile:** Run one headless Chrome process at a time (never run `snapshot` and `Brain Autopilot` concurrently) and prefer native `data-motion-blur="on"` (`shutter="360"`) with `--low-memory-mode` over 240fps `8x` subframe supersampling unless rendering clips <= 10s.

## 2. Motion & Anti-Slop Craft Rules
- **Intra-Shot Optical Flow:** Exclude frame `0` after a hard cut when measuring shot velocity so inter-shot pixel jumps do not masquerade as early motion peaks.
- **Dead-Still Reads:** Once a hero headline or lyric phrase lands, hold it 100% still for `0.5s + 0.3s/word` (`>= 2.0s` on the final frame); shift continuous motion to the 3D stage (`hf-seek`) or subtle background scale (`1.0 -> 1.06`).
- **Text Floor:** Keep all audited copy `>= 2.6%` of short frame side (`>= 29px` on `1080p`); mark purely decorative hairlines/watermarks with `data-layout-ignore`.

## 3. Cherry-Picked Production Gates (v1.1)
- **Opaque Stage Ground (`seam-craft`):** Always set an explicit opaque background on `#root` and scene containers (`background: var(--canvas-deep, #000)`) so cross-scene opacity dips never show Headless Chromium's default white canvas for 1 frame.
- **Frame-Grid Snapping:** Snap scene/transition timestamps to exact multiples of `1 / fps` (`Math.floor(f) / fps`) so sub-frame offsets never cause uneven easing velocity at cut boundaries.
- **High-Cadence Seam Probe (`30fps tile=6x5`):** Never judge transitions or motion blur from 1fps keyframes; use `decompile.py --seam-probes` (`ffmpeg -vf "fps=30,scale=640:-1,tile=6x5"`) around hard cuts.
- **Broadcast & Critic Gates (`motion-quality-gates`):** Fail delivery on any unintended black frames (`blackdetect d=0.04`), unintended freezes (`freezedetect > 0.5s`), or audio clipping (`true-peak > -1 dBTP`). Require a Critic pass (`writer != critic`) listing `>= 3` concrete timestamped flaws before final render.

## 4. Forensic Clone Precision (`v1.2`)
- **Use Local `hyperframes measure` Suite (Never `reverse start`):** Run `measure events --map`, `measure curve --roi`, `measure ink --at --roi`, `measure look --grid`, `measure extract --roi`, and `measure energy` locally to measure exact GSAP eases, font ink bounds, background grids, and real cropped sub-assets.
- **Truncate Frame Timestamps Down (`floor`):** Compute `frame / fps` floored to 6 decimals (never rounded up) so shot cuts and transitions land on the intended frame rather than 1 frame late.
- **Extract Complex Non-Text Assets (`measure extract`):** Do not rebuild intricate photographs, hand-drawn illustrations, or complex marks with crude SVG approximations; crop them cleanly from their peak-clarity source frame (`measure extract --at ... --roi ... --out ...`) and animate their wrapper in HTML/GSAP.
