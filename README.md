# REA Motion

**Evidence-First Kinetic Video Engineering Skill & Pipeline for Windows 11 + HyperFrames**

`github.com/baehaqi-rf/rea-motion` is the **Single Source of Truth** skill repository for **REA Motion**—applying the **Evidence → Reconstruct → Closed-Loop Verify** philosophy of *Reverse Engineer Anything (REA)* to motion graphics, SaaS product launches, explainers, and beat-synced lyric videos.

Instead of spreading overlapping tools across 5 separate skills, **REA Motion** unifies:
- **CV Reference Cloning (`launch-video-clone`):** `burst.py`, `camtrack.py`, `camtrack_sift.py`, `cursortrack.py`, `colormatch.py`, `compare.py`, `sbs.py`, `types/*`, `subskills/*`, and Windows-native `round.ps1` / `round_mb.ps1`.
- **21 Style & Art Medium Modules (`reelmimic-styles`):** `motion-doctrine`, `cut-the-curve`, `seam-craft`, `oversized-cursor`, `faceless-explainer`, `paper-cutout`, `painted-animation`, `anime-cel`, `whiteboard`, `pixel-art`, `crayon-storybook`, etc. (without `.claude` hooks or core `hyperframes` duplicates).
- **Motion-REA Telemetry & Anti-Slop Layer:** `decompile.py` (`MOTION_LEDGER.json` + `--seam-probes` 30fps `tile=6x5`), `visual_diff.py` (SSIM + Sobel Edge IoU + $\pm 3$-frame lag diff), `beats.py` (`scipy.signal` 20–150 Hz sub-bass + RMS + HyperFrames beats), `unslop_check.py` (incl. `--original`), `rhythm.py` (render cadence/dead-moment/metronome audit), `VIDEO_MANIFEST.template.md`, `brands/`, and `GLOBAL_LESSONS.md`.
- **Deterministic Runtime Helpers (`lib/` & `vendor/`):** `lib/motion.js` (`logScale`, Catmull-Rom `path`, closed-form `spring`/`springFrames`, `E.bez`, seeded noise), `vendor/camera-dop.js` (`HFCameraDoP` 13 camera presets), `vendor/vfx-cgi-suite.js` (`HFVfxSuite` deterministic Canvas2D VFX), and offline `vendor/gsap.min.js`.

---

## Repository = Skill Structure

```text
rea-motion/                        # Clone directly as a single skill or run install.ps1
├── SKILL.md                       # Master router & 3-stage workflow
├── GLOBAL_LESSONS.md              # Compound cross-project rules & Windows/8GB RAM guardrails
├── install.ps1                    # Installs `rea-motion` to ~/.gemini/config/skills & ~/.agents/skills & removes legacy splits
├── lib/                           # motion.js (frame-pure math/springs/logScale) + motion.test.js
├── vendor/                        # Offline gsap.min.js, camera-dop.js (HFCameraDoP), vfx-cgi-suite.js (HFVfxSuite)
├── scripts/
│   ├── beats.py                   # Sub-bass (20–150 Hz), snare flux, RMS & HyperFrames beat grid
│   ├── decompile.py               # Video + audio -> MOTION_LEDGER.json (KINETIC_DNA vs BRAND_SKIN) + 30fps seam probes
│   ├── rhythm.py                  # Quantitative render rhythm check (dead moments, metronome, hard-stops, off-beat)
│   ├── visual_diff.py             # Gate 1/2 SSIM + Sobel Edge IoU + lag offset + [Ref | Render | Diff] sheets
│   ├── unslop_check.py            # Deterministic Anti-Slop & --original VIDEO_MANIFEST.md auditor
│   ├── burst.py, camtrack.py, cursortrack.py, compare.py, sbs.py, ... (35 CV tools)
│   └── round.ps1, round_mb.ps1, Run-BrainAutopilotVerify.ps1, Invoke-ReaVideoInspect.ps1
├── references/                    # clone-guide.md, ledger-schema.md, motion-feel.md, living-stills.md, examples/
├── types/                         # 6 clone blueprints (ui-showcase, abstract-3d-diagram, 3d-product, ...)
├── subskills/                     # 4 hybrid footage subskills (paper-world, word-synced-ui, footage-transitions, vo-beat-timing)
├── modules/                       # 21 stylized 2D/3D mediums & motion doctrines
├── brands/                        # Saved brand skins (editorial-obsidian.md)
├── presets/                       # JSON motion/typography style presets
├── templates/                     # VIDEO_MANIFEST.template.md
└── docs/                          # Curated registry map, white-box HyperFrames spec, prompt playbook
```

---

## Quick Start (Windows 11 + PowerShell)

### Prerequisites
- **Node.js 22+** & **HyperFrames** (`npm i -g hyperframes` + official `hyperframes`, `hyperframes-cli`, `hyperframes-registry` skills)
- **Python 3.11–3.14**
- **FFmpeg & FFprobe** (e.g. `winget install --id Gyan.FFmpeg -e`; scripts auto-discover WinGet installs)

### Install / Update from GitHub
```powershell
git clone https://github.com/baehaqi-rf/rea-motion.git
cd rea-motion
powershell -ExecutionPolicy Bypass -File .\install.ps1
```
`install.ps1` installs Python dependencies (`numpy`, `pillow`, `scipy`, `opencv-python-headless`, `matplotlib`), installs this repo as `~/.gemini/config/skills/rea-motion` and `~/.agents/skills/rea-motion`, and removes redundant legacy folders (`hyperframes-motion-rea`, `launch-video-clone`, `reelmimic-styles`, `local-hyperframes-pro`).

---

## Copy-Paste Agent Prompts

- **Clone / Re-skin a Reference Video:**
  > *"Pakai `rea-motion` untuk mengkloning `@[path/ref.mp4]`, lalu re-skin ke brand `editorial-obsidian` / `[nama/URL produk]`. Jalankan `burst.py` + `camtrack.py`, buat `VIDEO_MANIFEST.md`, loop `round.ps1` + `unslop_check.py` sampai 0 error, lalu render MP4 `delivery`."*
- **Explainer / Stylized 2D Video (Topic Swap):**
  > *"Pakai `rea-motion` (modul `faceless-explainer` / `paper-cutout` / `whiteboard`) untuk membuat video `[X detik]` tentang `[topik]`. Sinkronkan dengan `beats.py` dari `@[vo.mp3]`, audit via `unslop_check.py` + Brain Autopilot, lalu render MP4."*
- **Beat-Synced Lyric / Music Video:**
  > *"Pakai `rea-motion` (`beats.py` + STT per kata + GSAP `data-motion-blur="on"` shutter 360° + Three.js `hf-seek`) untuk membuat video lirik `1920x1080` dari `@[lagu.mp3]`, audit `unslop_check.py` + `Run-BrainAutopilotVerify.ps1`, lalu render MP4 `delivery`."*
- **Original Product Launch from URL:**
  > *"Pakai `rea-motion` mode Original untuk membuat video launch `[25s]` dari `[https://url-produk.com]` (`hyperframes capture`), patuhi `VIDEO_MANIFEST.md`, audit dengan `unslop_check.py` + `round.ps1`, lalu render MP4 final."*

---

## Attribution
Built on top of open-source work from:
- [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) (Apache-2.0)
- [per-simmons/launch-video-clone](https://github.com/per-simmons/launch-video-clone)
- [02ui/02ui-video-copy](https://github.com/02ui/02ui-video-copy) (MIT — `lib/motion.js`, `rhythm.py`, `--original` lint rules)
- [ThaddeusHackz/THE-AI-VIDEO-EDITOR](https://github.com/ThaddeusHackz/THE-AI-VIDEO-EDITOR) (`camera-dop.js`, `vfx-cgi-suite.js`, `motion-quality-gates`, seam probe workflows)
- [edenfunf/reelmimic](https://github.com/edenfunf/reelmimic)
- Anti-slop rules inspired by [pbakaus/impeccable](https://github.com/pbakaus/impeccable) and [heydamir/unslop](https://github.com/heydamir/unslop)
