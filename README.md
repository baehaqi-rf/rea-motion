# REA Motion

**Evidence-First Kinetic Video Engineering Pipeline (Hybrid 80/20 Stack for Windows 11 + HyperFrames)**

REA Motion applies the **Evidence → Reconstruct → Closed-Loop Verify** discipline of *Reverse Engineer Anything (REA)* to motion graphics, SaaS launch films, YouTube explainers, and beat-synced lyric videos—eliminating "AI motion slop" (uniform `power2.out` easings, guessing camera speeds, floating text, and 8-bit banding).

---

## Architecture (Hybrid 80/20 Stack)

| Stage | Web REA Equivalent | REA Motion Stack |
| --- | --- | --- |
| **1. Evidence (Zero-Guessing)** | DOM + CSS + HAR → `EVIDENCE_LEDGER` | `burst.py` + `camtrack.py` / `cursortrack.py` (`launch-video-clone`) + `beats.py` (20–150 Hz sub-bass & RMS) + `decompile.py` → `MOTION_LEDGER.json` + `VIDEO_MANIFEST.md` |
| **2. Reconstruct** | React / Tailwind 1:1 | HyperFrames (`GSAP 3.15` + `Three.js` `hf-seek` + native `data-motion-blur="on"` shutter 360°) + `reelmimic-styles` (21 art mediums & pacing workflows) |
| **3. Closed-Loop Verify** | Playwright / Brain Autopilot DOM assertions | **Gate 1:** `unslop_check.py` + `hyperframes check` + `visual_diff.py stills`<br>**Gate 2:** `round.ps1` (`draft` MP4 + `burst.py` + `compare.py` + `sbs.py`)<br>**Gate 3:** `Run-BrainAutopilotVerify.ps1` (`WebGL3DEngine` CDP) → `delivery` MP4 |

---

## Repository Layout

```text
rea-motion/
├── install.ps1                        # One-command Windows installer for Python deps + Antigravity skills
├── GLOBAL_LESSONS.md                  # Compound cross-project rules & Windows/8GB RAM guardrails
├── brands/
│   └── editorial-obsidian.md          # Saved dark cinema brand skin tokens
├── presets/                           # JSON motion/typography style presets
├── templates/
│   └── VIDEO_MANIFEST.template.md     # Per-project Brand Skin + Kinetic DNA + Anti-Slop contract
├── docs/                              # Curated registry map, white-box HyperFrames spec, prompt playbook
├── scripts/
│   ├── beats.py                       # scipy.signal sub-bass (20–150 Hz), snare flux, RMS & HyperFrames beats
│   ├── unslop_check.py                # Deterministic Anti-Slop & manifest linter (impeccable/unslop rules)
│   ├── Build-BeatSheet.mjs            # Scene cuts × word-level STT synchronizer
│   ├── Invoke-ReaVideoInspect.ps1     # Local ffprobe + FFmpeg scene/interval keyframes + WAV extraction
│   ├── Run-ParityCheck.ps1            # HyperFrames check + snapshot parity
│   ├── Run-BrainAutopilotVerify.ps1   # Brain Autopilot WebGL3DEngine CDP verification runner
│   └── harness_hyperframes_3d.py      # Declarative Brain Autopilot 3D verification harness
└── skills/
    ├── rea-motion/                    # Unified top-level Antigravity router skill
    ├── hyperframes-motion-rea/        # Video/audio decompiler (decompile.py) + visual_diff.py QA
    ├── launch-video-clone/            # CV tracking & cloning suite + Windows round.ps1 / round_mb.ps1
    └── reelmimic-styles/              # Compact 21-module router (paper-cutout, anime-cel, faceless-explainer, etc.)
```

---

## Quick Start (Windows 11 + PowerShell)

### 1. Prerequisites
- **Node.js 22+** & **HyperFrames CLI** (`npm i -g hyperframes`)
- **Python 3.11–3.14**
- **FFmpeg & FFprobe** (e.g. `winget install --id Gyan.FFmpeg -e`; scripts auto-discover WinGet packages)

### 2. Install Skills & Python Dependencies
```powershell
git clone https://github.com/baehaqi-rf/rea-motion.git
cd rea-motion
powershell -ExecutionPolicy Bypass -File .\install.ps1
```
*(Pass `-IncludeClaude` if you also want the skills copied to `~/.claude/skills`.)*

---

## Copy-Paste Agent Prompts

### 1. Clone / Re-skin a Reference Video
> *"Gunakan `rea-motion` (`launch-video-clone`) untuk mengkloning video referensi `@[path/ref.mp4]`, lalu re-skin ke brand `editorial-obsidian` / brand saya `[nama/URL]`. Ukur kamera & kurva gerak dulu, buat `VIDEO_MANIFEST.md`, jalankan loop `round.ps1` + `unslop_check.py` + Brain Autopilot sampai 0 error, lalu render MP4 `delivery`."*

### 2. Explainer / Stylized 2D Video (Topic Swap)
> *"Gunakan `rea-motion` (`reelmimic-styles`: `faceless-explainer` / `paper-cutout` / `whiteboard`) untuk membuat video `[X detik]` tentang `[topik]`. Sinkronkan pacing dengan `beats.py` dari audio `@[vo.mp3]`, patuhi `VIDEO_MANIFEST.md` + `unslop_check.py`, verifikasi via Gate Stills & Brain Autopilot, lalu render MP4."*

### 3. Beat-Synced Music / Lyric Video
> *"Gunakan `rea-motion` (`beats.py` sub-bass & BPM + STT per kata + `hyperframes`) untuk membuat video lirik `1920x1080` dari `@[lagu.mp3]` dengan GSAP `data-motion-blur="on"` (shutter 360°) dan objek 3D Three.js `hf-seek`, audit via `unslop_check.py` + `Run-BrainAutopilotVerify.ps1`, lalu render MP4 `delivery`."*

### 4. Original Product Launch from Live URL
> *"Gunakan `rea-motion` (`launch-video-clone` mode Original) untuk membuat video launch `[25s]` untuk website `[https://url-produk.com]`. Capture token & UI asli (`hyperframes capture`), pakai `VIDEO_MANIFEST.md`, audit dengan `unslop_check.py` + `hyperframes check` + `Run-BrainAutopilotVerify.ps1`, lalu render MP4 final."*

---

## Attribution
Built on top of open-source work from:
- [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) (Apache-2.0)
- [per-simmons/launch-video-clone](https://github.com/per-simmons/launch-video-clone)
- [edenfunf/reelmimic](https://github.com/edenfunf/reelmimic)
- Anti-slop audit rules inspired by [pbakaus/impeccable](https://github.com/pbakaus/impeccable) and [heydamir/unslop](https://github.com/heydamir/unslop)
