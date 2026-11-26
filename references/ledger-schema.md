# `MOTION_LEDGER.json` Schema & GSAP Mapping

`decompile.py` separates every decompiled reference video into two top-level blocks so **Motion DNA** can be reused independently of **Visual Brand Skin**.

## Top-Level Structure

```json
{
  "schema_version": "1.0.0",
  "metadata": {
    "source_video": "path/to/ref.mp4",
    "width": 1920,
    "height": 1080,
    "fps": 30.0,
    "duration_sec": 5.0,
    "duration_ms": 5000,
    "has_audio": true,
    "engines": {
      "shot_slicer": "ffmpeg+hyperframes",
      "optical_flow": "numpy_block_lk",
      "audio_rhythm": "hyperframes_audio+ffmpeg_pcm",
      "stt": "faster_whisper"
    }
  },
  "KINETIC_DNA": {
    "bpm": 112.1,
    "beats_ms": [565, 1105, 1635],
    "downbeats_ms": [565, 2715],
    "onsets_ms": [{"t_ms": 550, "strength": 0.66}],
    "rms_envelope": [{"t_ms": 0, "rms": 0.12}],
    "shots": [
      {
        "scene_id": "sc_01",
        "start_ms": 0,
        "end_ms": 2133,
        "duration_ms": 2133,
        "hold_ms": 967,
        "hold_ratio": 0.453,
        "peak_velocity_ms": 233,
        "mean_speed_px": 4.28,
        "max_speed_px": 18.9,
        "motion_type": "pan_left",
        "dominant_direction": "left",
        "easing_guess": "power4.out",
        "transition_in": "hard_cut",
        "velocity_curve_norm": [0.95, 1.0, 0.58, 0.21, 0.04]
      }
    ]
  },
  "BRAND_SKIN": {
    "global_palette_hex": ["#0D1117", "#F8FAFC", "#CCFF00", "#38BDF8"],
    "shots": [
      {
        "scene_id": "sc_01",
        "bg_hex": "#0D1117",
        "ink_hex": "#F8FAFC",
        "accent_hex": "#CCFF00",
        "palette_hex": ["#0D1117", "#1E293B", "#F8FAFC", "#CCFF00", "#38BDF8"],
        "contrast_ratio": 16.4,
        "safe_margins_pct": {"top": 11.1, "bottom": 10.2, "left": 8.3, "right": 7.3},
        "transcript_segment": "AFTER EFFECTS PRECISION",
        "word_cues": [{"word": "AFTER", "start_ms": 220, "end_ms": 510}],
        "stills": {
          "start": "stills/sc_01_start.png",
          "peak": "stills/sc_01_peak.png",
          "hero": "stills/sc_01_hero.png",
          "end": "stills/sc_01_end.png"
        },
        "filmstrip": "filmstrips/filmstrip_sc_01.jpg"
      }
    ]
  }
}
```

## Velocity-to-GSAP Easing Lookup

| `easing_guess` | Measured Velocity Signature | Recommended GSAP Tween |
| --- | --- | --- |
| `power4.out` | Peak in first 0–22% of shot, rapid exponential decay | `{ ease: "power4.out", duration: 0.35–0.55 }` |
| `expo.out` | Peak in first 0–18%, ultra-long tail settle | `{ ease: "expo.out", duration: 0.45–0.65 }` |
| `power2.inOut` | Symmetric bell peak around 35–65% of move | `{ ease: "power2.inOut", duration: 0.4–0.7 }` |
| `power3.in` | Accelerating velocity peaking >72% into exit/cut | `{ ease: "power3.in", duration: 0.2–0.35 }` |
| `back.out(1.4)` | Peak early followed by slight directional reversal | `{ ease: "back.out(1.4)", duration: 0.35–0.5 }` |
| `none` | Constant speed (`std / mean < 0.25`) | `{ ease: "none" }` |
| `static` | Mean proxy displacement < 0.15 px/frame | Hold `tl.set` / zero motion |
