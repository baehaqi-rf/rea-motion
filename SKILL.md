---
name: rea-motion
description: Unified REA Motion skill (Hybrid 80/20 Video Engineering Pipeline) built on HyperFrames. Combines launch-video-clone CV tracking (burst, camtrack, cursortrack, compare, sbs, round.ps1), ReelMimic 21 style & art mediums (faceless-explainer, paper-cutout, anime-cel, cut-the-curve, motion-doctrine, seam-craft, whiteboard), Motion-REA decompiler & visual QA (decompile.py, visual_diff.py), beats.py sub-bass audio telemetry, VIDEO_MANIFEST.md anti-slop contracts, and Brain Autopilot 3D CDP verification. Use for any video cloning, style transfer, beat-synced music/lyric video, or product launch film.
---

# REA Motion — Evidence-First Video Engineering Pipeline

**GitHub Single Source of Truth:** `https://github.com/baehaqi-rf/rea-motion`
All paths below are relative to `<SKILL_DIR>` (the folder holding this `SKILL.md`). Set `S="<SKILL_DIR>/scripts"`.

---

## Pick Your Mode First

| Mode | When to Use | What to Read First |
| --- | --- | --- |
| **1. Clone / Re-skin** | Rebuild a reference video 1:1 (or swap its brand skin) | `references/clone-guide.md`, `references/motion-feel.md`, and 1 matching `types/*.md` |
| **2. Style-Transfer / 2D Medium** | New topic/script using a proven explainer pacing or stylized 2D/3D medium | 1 matching `modules/<slug>/SKILL.md` (`faceless-explainer`, `paper-cutout`, `cut-the-curve`, `motion-doctrine`, `seam-craft`, `anime-cel`, `whiteboard`, etc.) |
| **3. Audio / Lyric Beat-Sync** | Music video, lyric typography, or audio-reactive 3D stage | `docs/PROMPT_PLAYBOOK_HYPERFRAMES_PRO.md` (Kondisi A) + `references/ledger-schema.md` |
| **4. Original Product Launch** | Launch film from a live website URL (`hyperframes capture`) or UI screenshots | `references/clone-guide.md` (Original mode) + `types/ui-showcase.md` + `brands/editorial-obsidian.md` |
| **5. Hybrid Footage** | Live presenter / camera footage mixed with paper-collage, UI, or transitions | Matching `subskills/<name>/SKILL.md` (`paper-world`, `word-synced-ui`, `footage-transitions`, `vo-beat-timing`) |

---

## Stage 1: Evidence & Manifest (Before Writing Code)
1. **Load Compound Rules:** Read `GLOBAL_LESSONS.md`.
2. **Create `VIDEO_MANIFEST.md`:** Copy `templates/VIDEO_MANIFEST.template.md` into the project root (inherit a saved brand from `brands/*.md` when appropriate) to lock **Brand Skin**, **Kinetic DNA**, and the **Anti-Slop Banned List**.
3. **Measure Reference & Audio (Zero-Guessing):**
    - **CV Burst + Energy Curves:** `python "$S/burst.py" reference/ref.mp4 reference/analysis` (inspect `ANALYSIS.md`, `overview.png`, `burst.png`, `trail.png`, `curve.png`).
    - **Camera & Cursor Tracking:** `python "$S/camtrack.py"` (one-takes), `camtrack_sift.py` (cut shots), `cursortrack.py`, `colormatch.py`.
    - **Decompiled Motion Ledger (`MOTION_LEDGER.json`) + 30fps Seam Probes:** `python "$S/decompile.py" reference/ref.mp4 --seam-probes --out .motion_rea` (separates `KINETIC_DNA` from `BRAND_SKIN` and extracts 30fps `tile=6x5` seam contact sheets).
    - **Audio Beats & Sub-Bass (`20–150 Hz`):** `python "$S/beats.py" <audio_or_video> --out beats.json` (extracts `bpm`, `beats_ms`, `downbeats_ms`, `kick_hits_ms`, `snare_hits_ms`, per-frame `rms`).

---

## Stage 2: Deterministic HyperFrames Synthesis
- **Virtual-Clock Contract:** Drive GSAP (`tl.seek(t)`) and Three.js (`window.addEventListener("hf-seek", ...)`, `preserveDrawingBuffer: true`) from timeline seconds only. Never use `requestAnimationFrame`, `Date.now()`, `performance.now()`, unseeded `Math.random()`, `repeat: -1`, CSS `transition`, or CSS `animation: ... infinite`.
- **Frame-Pure Math (`lib/motion.js`):** Use `M.logScale()` for perceptually constant camera zoom, `M.path()` (Catmull-Rom) for multi-keyframe camera paths without middle-key stalls, `M.spring()` / `M.springFrames()` for settled physical overshoots, `M.E.bez()`, `M.drift()`, `M.cutIn()`, and seeded `M.rnd()` / `M.noise()` / `M.fbm()` / `M.wobble()`.
- **DoP Camera & Canvas VFX (`vendor/`):** Load local `vendor/gsap.min.js`, `vendor/camera-dop.js` (`window.HFCameraDoP`: `dolly-zoom`, `crash-zoom`, `orbit-360`, `bullet-time`, `whip-pan`, `push-to-glass`, `crane-up`, `rack-focus`, `fpv-drone`, etc.), and `vendor/vfx-cgi-suite.js` (`window.HFVfxSuite`: deterministic `mulberry32` portal vortex, plasma lightning, anamorphic flare) for offline zero-network reliability.
- **Opaque Stage Ground & Motion Blur Guards:** Set an opaque background on `#root` (prevents 1-frame white flash at crossfade seams per `modules/seam-craft`), enable `data-motion-blur="on"` (`data-motion-blur-shutter="360"`) on `#root`, snap all cut/scene timestamps to exact frames (`Math.floor(f) / fps`), give 35mm SVG `feTurbulence` grain explicit `width="256" height="256"` + `background-size: 256px 256px`, and include `<link rel="icon" href="data:," />` in `<head>`.
- **Dead-Still Reads:** Landed headlines hold 100% still for `>= 0.3s + 0.06s/word` minimum (`0.5s + 0.3s/word`, `>= 2.0s` on closing lines for hero lyric cards).
- **Reusable Blocks:** Check `docs/CURATED_REGISTRY_MAP.md` or `hyperframes catalog` before hand-coding common transitions/overlays.

---

## Stage 3: Tiered Closed-Loop QA (8 GB RAM Safe)
1. **Gate 1 — Stills, Anti-Slop & Native Diff (Fast, No Full Render):**
   - `python "$S/unslop_check.py" <comp_dir>` (add `--original` in Original Mode to ban `backdrop-filter`, `radial-gradient` blobs, and repetitive slide-ups)
   - `npx hyperframes check --json` (`0` errors)
   - `npx hyperframes diff ref.mp4 . --at="0.5,2.4,5.0"` (instant SSIM + worst-cell visual diff without full render) or `npx hyperframes snapshot --at="0.45,1.8,..."` + `python "$S/visual_diff.py" stills`
   - `node "<SKILL_DIR>/modules/motion-doctrine/scripts/seam-gate.mjs" verify --ledger ledger.json --project <comp_dir>`
2. **Gate 2 — Draft Motion Parity & Rhythm Audit (Windows PowerShell):**
   - `powershell -ExecutionPolicy Bypass -File "$S/round.ps1" <project_dir> <renders_dir> v1` (runs `unslop_check.py` -> `draft` render with `--low-memory-mode` -> `burst.py` -> `compare.py` -> `sbs.py`)
   - `python "$S/rhythm.py" <renders_dir>/v1-analysis/analysis.json` (flags `dead` moments, `metronome` cuts CV < 0.2, `hard-stop` settles, `staged-cut`, `off-beat` cuts; supports `--donor <ref_analysis>`)
   - Use `round_mb.ps1` (8x subframe `tmix`) **only** for short clips `<= 10s`.
   - For SSIM + Edge IoU + $\pm 3$-frame lag diagnostics: `python "$S/visual_diff.py" video --ref <ref.mp4> --render <v1.mp4>`
3. **Gate 3 — 3D CDP, Quality Gates & Final Delivery:**
   - `powershell -ExecutionPolicy Bypass -File "$S/Run-BrainAutopilotVerify.ps1" -CompositionDir <comp_dir>` (run solo, never concurrently with `snapshot`)
   - Verify broadcast gates (`ffmpeg blackdetect` `d=0.04`, `freezedetect` `> 0.5s`, audio true-peak `<= -1 dBTP`) + Critic review (`writer != critic`, log `>= 3` timestamped flaws before sign-off).
   - Final render: `npx hyperframes render --quality delivery --low-memory-mode -o renders/final.mp4`
4. **Learn:** Append newly discovered pitfalls or verified recipes to `GLOBAL_LESSONS.md`.
