#!/usr/bin/env python3
"""
Motion-REA Deterministic Anti-Slop Auditor (`unslop_check.py`).

Inspired by `pbakaus/impeccable` and `heydamir/unslop`, adapted specifically for
HyperFrames HTML/CSS/GSAP/Three.js compositions + `VIDEO_MANIFEST.md`.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SLOP_HEX_PATTERNS = re.compile(r"#(?:6366f1|8b5cf6|a855f7|ec4899|7c3aed)\b", re.IGNORECASE)
DEFAULT_FONT_RE = re.compile(
    r"font-family\s*:\s*[^;\"']*\b(Arial|Helvetica|system-ui|-apple-system|Roboto|Segoe UI)\b",
    re.IGNORECASE,
)
SLIDE_UP_RE = re.compile(r"translateY\(\s*\$\{[^}]*\(\s*1\s*-|translateY\(\s*\d{2,}\s*px|\by\s*:\s*[2-9]\d\b")
SKIP_DIR_PARTS = ("node_modules", ".git", "renders", "vendor")
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\U00002700-\U000027BF"
    "]+"
)


def check_manifest(project_dir: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    manifest = project_dir / "VIDEO_MANIFEST.md"
    if not manifest.is_file():
        manifest_alt = project_dir.parent / "VIDEO_MANIFEST.md"
        if manifest_alt.is_file():
            manifest = manifest_alt
        else:
            findings.append(
                {
                    "rule": "manifest_missing",
                    "severity": "warning",
                    "file": str(project_dir / "VIDEO_MANIFEST.md"),
                    "message": "Missing VIDEO_MANIFEST.md. Copy templates/VIDEO_MANIFEST.template.md before rendering.",
                }
            )
            return findings

    text = manifest.read_text(encoding="utf-8", errors="replace")
    required_sections = ["## Brand Skin", "## Kinetic DNA", "## Anti-Slop Banned List"]
    for sec in required_sections:
        if sec.lower() not in text.lower():
            findings.append(
                {
                    "rule": "manifest_incomplete",
                    "severity": "warning",
                    "file": str(manifest),
                    "message": f"VIDEO_MANIFEST.md is missing required section '{sec}'.",
                }
            )
    return findings


def audit_source_file(
    file_path: Path, is_root: bool, manifest_text: str, original_mode: bool = False
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    src = file_path.read_text(encoding="utf-8", errors="replace")
    is_html = file_path.suffix.lower() in (".html", ".htm")

    if is_root and is_html:
        if 'rel="icon"' not in src and "rel='icon'" not in src:
            findings.append(
                {
                    "rule": "missing_favicon_guard",
                    "severity": "error",
                    "file": str(file_path),
                    "message": 'Add <link rel="icon" href="data:," /> in <head> to prevent 404 network/console errors.',
                }
            )
        if 'data-motion-blur="on"' not in src:
            findings.append(
                {
                    "rule": "missing_motion_blur",
                    "severity": "warning",
                    "file": str(file_path),
                    "message": 'Root composition lacks data-motion-blur="on" (recommended with shutter 360 for fast 2D moves).',
                }
            )

    # 1. Nondeterministic clock / loop / CSS transition traps
    for pat, label in [
        (r"\brequestAnimationFrame\s*\(", "requestAnimationFrame()"),
        (r"\bsetInterval\s*\(", "setInterval()"),
        (r"\bDate\.now\s*\(", "Date.now()"),
        (r"\bperformance\.now\s*\(", "performance.now()"),
        (r"\bnew Date\s*\(", "new Date()"),
        (r"\bMath\.random\s*\(", "unseeded Math.random() (use M.rnd/mulberry32)"),
        (r"repeat\s*:\s*-1", "GSAP repeat: -1"),
        (r"(?<![\w-])transition\s*:\s*(?!none)", "CSS transition (not seekable per-frame)"),
    ]:
        if re.search(pat, src):
            findings.append(
                {
                    "rule": "nondeterministic_clock",
                    "severity": "error",
                    "file": str(file_path),
                    "message": f"Forbidden non-deterministic API `{label}` breaks frame-accurate HyperFrames seeking.",
                }
            )

    # 2. Infinite CSS keyframes
    if re.search(r"animation\s*:[^;{}]*\binfinite\b", src, re.IGNORECASE):
        findings.append(
            {
                "rule": "infinite_css_animation",
                "severity": "error",
                "file": str(file_path),
                "message": "CSS `animation: ... infinite` found; replace with finite step count matching root duration.",
            }
        )

    # 3. Unpinned SVG feTurbulence raster bomb
    if "feTurbulence" in src and "background-size" not in src and 'id="wpc' not in src:
        findings.append(
            {
                "rule": "unpinned_grain_svg",
                "severity": "warning",
                "file": str(file_path),
                "message": "SVG feTurbulence grain found without explicit `background-size: 256px 256px` tiling.",
            }
        )

    # 4. Three.js preserveDrawingBuffer contract
    if "WebGLRenderer" in src and "preserveDrawingBuffer" not in src:
        findings.append(
            {
                "rule": "threejs_missing_preserve_buffer",
                "severity": "error",
                "file": str(file_path),
                "message": "THREE.WebGLRenderer must set `preserveDrawingBuffer: true` for deterministic capture & QA.",
            }
        )

    # 5. Generic AI purple/indigo gradient slop (unless explicitly declared in VIDEO_MANIFEST.md)
    slop_matches = SLOP_HEX_PATTERNS.findall(src)
    if slop_matches and not any(h.lower() in manifest_text.lower() for h in slop_matches):
        findings.append(
            {
                "rule": "ai_slop_palette",
                "severity": "warning",
                "file": str(file_path),
                "message": f"Default AI purple/violet hex {sorted(set(slop_matches))} used without brand authorization in VIDEO_MANIFEST.md.",
            }
        )

    # 6. Default safe-font fallback warning
    if DEFAULT_FONT_RE.search(src):
        findings.append(
            {
                "rule": "default_font_fallback",
                "severity": "warning",
                "file": str(file_path),
                "message": "Generic system/safe font detected; declare measured brand/editorial fonts with @font-face or fonts/.",
            }
        )

    # 7. Original-mode anti-slop bans (from 02ui/motionlint.py --original)
    if original_mode:
        if re.search(r"(?:-webkit-)?backdrop-filter\s*:", src, re.IGNORECASE):
            findings.append(
                {
                    "rule": "original_glass_banned",
                    "severity": "error",
                    "file": str(file_path),
                    "message": "Frosted glass (`backdrop-filter`) is banned in --original mode; use crisp solid/paper/ink surfaces.",
                }
            )
        if re.search(r"radial-gradient\s*\(", src, re.IGNORECASE):
            findings.append(
                {
                    "rule": "original_gradient_blob",
                    "severity": "error",
                    "file": str(file_path),
                    "message": "Radial gradient blob banned in --original mode; use a flat ground or measured canvas field.",
                }
            )
        slide_hits = len(SLIDE_UP_RE.findall(src))
        if slide_hits > 0:
            findings.append(
                {
                    "rule": "original_slide_up",
                    "severity": "error" if slide_hits >= 3 else "warning",
                    "file": str(file_path),
                    "message": f"{slide_hits} slide-up-from-below entrance(s) detected; vary with mask reveals, motion cuts, or camera moves.",
                }
            )

    # 8. Emoji inside visible HTML markup (strip comments and scripts first)
    if is_html:
        markup_only = re.sub(r"<script\b[^>]*>.*?</script>", "", src, flags=re.DOTALL | re.IGNORECASE)
        markup_only = re.sub(r"<style\b[^>]*>.*?</style>", "", markup_only, flags=re.DOTALL | re.IGNORECASE)
        markup_only = re.sub(r"<!--.*?-->", "", markup_only, flags=re.DOTALL)
        if EMOJI_RE.search(markup_only):
            findings.append(
                {
                    "rule": "emoji_in_hero_copy",
                    "severity": "warning",
                    "file": str(file_path),
                    "message": "Emoji character detected in HTML markup; replace with crisp SVG vector or mono label.",
                }
            )

    # 9. Monotonous easing check (`power2.out` overuse)
    eases = re.findall(r'ease\s*:\s*["\']([^"\']+)["\']', src)
    if len(eases) >= 4:
        p2_count = sum(1 for e in eases if e.strip() == "power2.out")
        if p2_count / len(eases) > 0.7:
            findings.append(
                {
                    "rule": "monotonous_default_ease",
                    "severity": "warning",
                    "file": str(file_path),
                    "message": f"{p2_count}/{len(eases)} tweens use flat `power2.out`; vary by role (`power4.out`, `expo.out`, `power3.inOut`, `power3.in`).",
                }
            )

    # 10. `tl.from(` seek-back drift warning inside sub-compositions
    if not is_root and re.search(r"\btl\.from\s*\(", src):
        findings.append(
            {
                "rule": "gsap_from_seek_trap",
                "severity": "warning",
                "file": str(file_path),
                "message": "Sub-composition uses `tl.from(...)`; prefer `tl.fromTo(...)` so re-seeking never drifts.",
            }
        )

    return findings


def _should_audit_asset(path: Path) -> bool:
    if any(part in SKIP_DIR_PARTS for part in path.parts):
        return False
    name = path.name.lower()
    if name == "motion.js" or ".min." in name or name in ("camera-dop.js", "vfx-cgi-suite.js"):
        return False
    return path.suffix.lower() in (".html", ".htm", ".js", ".mjs", ".css")


def run_audit(comp_dir: Path, original_mode: bool = False) -> dict[str, Any]:
    findings = check_manifest(comp_dir)
    manifest_text = ""
    for candidate in (comp_dir / "VIDEO_MANIFEST.md", comp_dir.parent / "VIDEO_MANIFEST.md"):
        if candidate.is_file():
            manifest_text = candidate.read_text(encoding="utf-8", errors="replace")
            break

    files_scanned = 0
    seen: set[Path] = set()
    index_html = comp_dir / "index.html"
    if index_html.is_file():
        files_scanned += 1
        seen.add(index_html.resolve())
        findings.extend(audit_source_file(index_html, is_root=True, manifest_text=manifest_text, original_mode=original_mode))

    for p in sorted(comp_dir.rglob("*")):
        if not p.is_file() or p.resolve() in seen or not _should_audit_asset(p):
            continue
        files_scanned += 1
        seen.add(p.resolve())
        findings.extend(audit_source_file(p, is_root=False, manifest_text=manifest_text, original_mode=original_mode))

    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    return {
        "ok": len(errors) == 0,
        "composition_dir": str(comp_dir),
        "files_scanned": files_scanned,
        "original_mode": original_mode,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Motion-REA Impeccable/Unslop Deterministic Checker")
    parser.add_argument("composition_dir", help="Path to HyperFrames composition directory")
    parser.add_argument("--strict", action="store_true", help="Fail exit code on warnings as well as errors")
    parser.add_argument(
        "--original",
        action="store_true",
        help="Also enforce Original-mode bans (backdrop-filter glass, radial-gradient blobs, slide-up entrances)",
    )
    args = parser.parse_args()

    report = run_audit(Path(args.composition_dir).resolve(), original_mode=args.original)
    print(json.dumps(report, indent=2))
    if report["error_count"] > 0 or (args.strict and report["warning_count"] > 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
