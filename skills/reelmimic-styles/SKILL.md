---
name: reelmimic-styles
description: Compact router for 21 ReelMimic HyperFrames motion-craft doctrines, explainer workflows, and 2D/3D visual art mediums (motion-doctrine, cut-the-curve, seam-craft, oversized-cursor, faceless-explainer, paper-cutout, painted-animation, anime-cel, whiteboard, pixel-art, crayon-storybook, embedded-captions, talking-head-recut, pr-to-video). Activate when transferring a YouTube/explainer pacing style to new content or authoring stylized 2D/3D animation in HyperFrames.
---

# ReelMimic Style & Craft Router (Antigravity Native Edition)

Curated from `edenfunf/reelmimic` with `.claude/harness` hook lock-in and duplicate core `hyperframes-*` skills stripped. Read **only** the matching `modules/<slug>/SKILL.md` (relative to this folder) for the current task, then combine it with `VIDEO_MANIFEST.md` and `beats.py` in our Hybrid 80/20 workflow.

## 1. Motion Craft & Transition Primitives
| Module | Path | When to Load |
| --- | --- | --- |
| `motion-doctrine` | `modules/motion-doctrine/SKILL.md` | Core physics, spacing, anticipation, settle, and anti-robotic motion principles |
| `cut-the-curve` | `modules/cut-the-curve/SKILL.md` | Match-velocity cuts mid-motion so consecutive shots feel continuous |
| `seam-craft` | `modules/seam-craft/SKILL.md` | Transition engineering across scene boundaries (whips, masks, wipes, J/L audio cuts) |
| `oversized-cursor` | `modules/oversized-cursor/SKILL.md` | Tactile oversized cursor choreography, click depression, and camera follow |
| `motion-graphics` | `modules/motion-graphics/SKILL.md` | General editorial & geometric 2D motion graphics composition patterns |

## 2. Pacing & Format Workflows (Content Swap / Style-Transfer)
| Module | Path | When to Load |
| --- | --- | --- |
| `faceless-explainer` | `modules/faceless-explainer/SKILL.md` | YouTube/Vox-style narrated explainers: pacing from donor video + original visuals |
| `product-launch-video` | `modules/product-launch-video/SKILL.md` | Story arc & beat pacing for SaaS/feature launch announcements |
| `music-to-video` | `modules/music-to-video/SKILL.md` | Audio-driven visual chapters, downbeat cuts, and lyric/rhythm staging |
| `pr-to-video` | `modules/pr-to-video/SKILL.md` | Turning a GitHub PR / changelog diff into a tight developer launch clip |
| `talking-head-recut` | `modules/talking-head-recut/SKILL.md` | Punch-ins, B-roll inserts, and graphical callouts over presenter footage |
| `video-clone` | `modules/video-clone/SKILL.md` | Structural pacing & 2D vector-rig (`modules/video-clone/assets/vector_rig/`) cloning |
| `embedded-captions` | `modules/embedded-captions/SKILL.md` | Cinematic depth-integrated captions (`dna/` & `modes/cinematic/`) |
| `captions-overlay` | `modules/captions-overlay/SKILL.md` | Clean word-synced speaker captions inside safe zones |

## 3. Stylized 2D & 3D Art Mediums
| Module | Path | When to Load |
| --- | --- | --- |
| `paper-cutout` | `modules/paper-cutout/SKILL.md` | Tactile layered paper, torn edges, drop-shadow elevation, stop-motion step feel |
| `painted-animation` | `modules/painted-animation/SKILL.md` | Watercolor / gouache / brush-stroke animated plates (`modules/painted-animation/template/`) |
| `anime-cel` | `modules/anime-cel/SKILL.md` | 2D cel-shaded character & FX animation (`GUIDE.md` + reference sheets in `docs/`) |
| `whiteboard` | `modules/whiteboard/SKILL.md` | Hand-drawn SVG stroke reveal and diagram build explainers |
| `crayon-storybook` | `modules/crayon-storybook/SKILL.md` | Warm illustrated storybook texture and gentle boil |
| `pixel-art` | `modules/pixel-art/SKILL.md` | Crisp nearest-neighbor pixel-grid sprite & UI scenes |
| `blender-product-film` | `modules/blender-product-film/SKILL.md` | Hybrid Blender turntable/render passes composited into HyperFrames |
| `general-video` | `modules/general-video/SKILL.md` | General multi-scene video Fallback when no specialized medium applies |

## Hybrid 80/20 Integration Rules
1. **Before writing scenes:** Create `VIDEO_MANIFEST.md` from `local-video-studio/templates/VIDEO_MANIFEST.template.md` and run `beats.py` on the voiceover/music track to generate `beats.json`.
2. **Gate 1 (Fast Stills + Anti-Slop):** Run `unslop_check.py`, `hyperframes check --json`, and `hyperframes snapshot` (`visual_diff.py` if matching a reference) before rendering full video.
3. **Compound Learning:** Record newly discovered pitfalls in `local-video-studio/GLOBAL_LESSONS.md`.
