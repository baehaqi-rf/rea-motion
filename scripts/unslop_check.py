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


def audit_html_file(html_path: Path, is_root: bool, manifest_text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    src = html_path.read_text(encoding="utf-8", errors="replace")

    if is_root:
        if 'rel="icon"' not in src and "rel='icon'" not in src:
            findings.append(
                {
                    "rule": "missing_favicon_guard",
                    "severity": "error",
                    "file": str(html_path),
                    "message": 'Add <link rel="icon" href="data:," /> in <head> to prevent 404 network/console errors.',
                }
            )
        if 'data-motion-blur="on"' not in src:
            findings.append(
                {
                    "rule": "missing_motion_blur",
                    "severity": "warning",
                    "file": str(html_path),
                    "message": 'Root composition lacks data-motion-blur="on" (recommended with shutter 360 for fast 2D moves).',
                }
            )

    # 1. Nondeterministic clock / loop traps
    for pat, label in [
        (r"\brequestAnimationFrame\s*\(", "requestAnimationFrame()"),
        (r"\bsetInterval\s*\(", "setInterval()"),
        (r"\bDate\.now\s*\(", "Date.now()"),
        (r"\bMath\.random\s*\(", "unseeded Math.random()"),
        (r"repeat\s*:\s*-1", "GSAP repeat: -1"),
    ]:
        if re.search(pat, src):
            findings.append(
                {
                    "rule": "nondeterministic_clock",
                    "severity": "error",
                    "file": str(html_path),
                    "message": f"Forbidden non-deterministic API `{label}` breaks frame-accurate HyperFrames seeking.",
                }
            )

    # 2. Infinite CSS keyframes
    if re.search(r"animation\s*:[^;{}]*\binfinite\b", src, re.IGNORECASE):
        findings.append(
            {
                "rule": "infinite_css_animation",
                "severity": "error",
                "file": str(html_path),
                "message": "CSS `animation: ... infinite` found; replace with finite step count matching root duration.",
            }
        )

    # 3. Unpinned SVG feTurbulence raster bomb
    if "feTurbulence" in src and "background-size" not in src and 'id="wpc' not in src:
        findings.append(
            {
                "rule": "unpinned_grain_svg",
                "severity": "warning",
                "file": str(html_path),
                "message": "SVG feTurbulence grain found without explicit `background-size: 256px 256px` tiling.",
            }
        )

    # 4. Three.js preserveDrawingBuffer contract
    if "WebGLRenderer" in src and "preserveDrawingBuffer" not in src:
        findings.append(
            {
                "rule": "threejs_missing_preserve_buffer",
                "severity": "error",
                "file": str(html_path),
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
                "file": str(html_path),
                "message": f"Default AI purple/violet hex {sorted(set(slop_matches))} used without brand authorization in VIDEO_MANIFEST.md.",
            }
        )

    # 6. Emoji inside visible HTML markup (strip comments and scripts first)
    markup_only = re.sub(r"<script\b[^>]*>.*?</script>", "", src, flags=re.DOTALL | re.IGNORECASE)
    markup_only = re.sub(r"<style\b[^>]*>.*?</style>", "", markup_only, flags=re.DOTALL | re.IGNORECASE)
    markup_only = re.sub(r"<!--.*?-->", "", markup_only, flags=re.DOTALL)
    if EMOJI_RE.search(markup_only):
        findings.append(
            {
                "rule": "emoji_in_hero_copy",
                "severity": "warning",
                "file": str(html_path),
                "message": "Emoji character detected in HTML markup; replace with crisp SVG vector or mono label.",
            }
        )

    # 7. Monotonous easing check (`power2.out` overuse)
    eases = re.findall(r'ease\s*:\s*["\']([^"\']+)["\']', src)
    if len(eases) >= 4:
        p2_count = sum(1 for e in eases if e.strip() == "power2.out")
        if p2_count / len(eases) > 0.7:
            findings.append(
                {
                    "rule": "monotonous_default_ease",
                    "severity": "warning",
                    "file": str(html_path),
                    "message": f"{p2_count}/{len(eases)} tweens use flat `power2.out`; vary by role (`power4.out`, `expo.out`, `power3.inOut`, `power3.in`).",
                }
            )

    # 8. `tl.from(` seek-back drift warning inside sub-compositions
    if not is_root and re.search(r"\btl\.from\s*\(", src):
        findings.append(
            {
                "rule": "gsap_from_seek_trap",
                "severity": "warning",
                "file": str(html_path),
                "message": "Sub-composition uses `tl.from(...)`; prefer `tl.fromTo(...)` so re-seeking never drifts.",
            }
        )

    return findings


def run_audit(comp_dir: Path) -> dict[str, Any]:
    findings = check_manifest(comp_dir)
    manifest_text = ""
    for candidate in (comp_dir / "VIDEO_MANIFEST.md", comp_dir.parent / "VIDEO_MANIFEST.md"):
        if candidate.is_file():
            manifest_text = candidate.read_text(encoding="utf-8", errors="replace")
            break

    index_html = comp_dir / "index.html"
    files_scanned = 0
    if index_html.is_file():
        files_scanned += 1
        findings.extend(audit_html_file(index_html, is_root=True, manifest_text=manifest_text))

    sub_dir = comp_dir / "compositions"
    if sub_dir.is_dir():
        for p in sorted(sub_dir.rglob("*.html")):
            files_scanned += 1
            findings.extend(audit_html_file(p, is_root=False, manifest_text=manifest_text))

    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    return {
        "ok": len(errors) == 0,
        "composition_dir": str(comp_dir),
        "files_scanned": files_scanned,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Motion-REA Impeccable/Unslop Deterministic Checker")
    parser.add_argument("composition_dir", help="Path to HyperFrames composition directory")
    parser.add_argument("--strict", action="store_true", help="Fail exit code on warnings as well as errors")
    args = parser.parse_args()

    report = run_audit(Path(args.composition_dir).resolve())
    print(json.dumps(report, indent=2))
    if report["error_count"] > 0 or (args.strict and report["warning_count"] > 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
