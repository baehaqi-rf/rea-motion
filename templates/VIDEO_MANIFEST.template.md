# VIDEO MANIFEST — {{PROJECT_NAME}}

- **Inherited Brand:** `brands/editorial-obsidian.md`
- **Inherited Kinetic Recipe:** `recipes/{{RECIPE_SLUG}}.json` (or `reference/analysis`)
- **Canvas & Rate:** `1920x1080` · `30fps` · `data-motion-blur="on"` (`shutter="360"`)

## Brand Skin
- **Ground:** `#0D1117` (radial glow + `grain-overlay` 256x256 tiled)
- **Primary Ink:** `#F8FAFC`
- **Accent:** `#CCFF00` / `#38BDF8`
- **Fonts:** `Outfit` (Display), `JetBrains Mono` (Labels)
- **Copy Tone:** Direct, concrete, zero marketing filler or emojis.

## Kinetic DNA
- **Mode:** `Clone` / `Original` / `Style-Transfer`
- **Beat Grid (`beats.json`):** Locked to downbeats & sub-bass `kick_hits_ms` (entrances start 40–120ms pre-hit).
- **Role-Based Easing:**
  - Arrivals: `power4.out` / `expo.out` (`0.35s–0.50s`)
  - Camera / Whip Transitions: `power3.inOut` (`0.40s–0.60s`)
  - Exits: `power3.in` (`0.16s–0.25s`)
- **Holds:** Every headline holds dead-still (`0.5s + 0.3s/word`); closing shot holds >= `2.0s`.

## Anti-Slop Banned List
- [x] No full-bleed 8-bit `linear-gradient` without grain (prevents H.264 banding).
- [x] No unmotivated floating/breathing/bobbing loops on landed text or UI cards.
- [x] No monotonous `power2.out` across all elements.
- [x] No emojis, generic glowing drop-shadows, or fake dashboard chrome.
- [x] Favicon guard `<link rel="icon" href="data:," />` and `preserveDrawingBuffer: true` verified.
