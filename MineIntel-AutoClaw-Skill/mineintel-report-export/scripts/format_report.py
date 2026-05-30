#!/usr/bin/env python3
"""Compatibility formatter for MineIntel deliverables.

This script no longer generates Word/DOCX. It exports the same competition
deliverables as the report-export flow: complete HTML report, presentation
deck, literature-review tex, and optional PDF.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


BASE_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = BASE_DIR.parent
OUTPUT_ROOT = PACKAGE_DIR / "output"


def safe_filename(title: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", title).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:60] or "mineintel_report"


def read_content(args: argparse.Namespace) -> str:
    if args.content_file:
        return Path(args.content_file).read_text(encoding="utf-8")
    if args.content:
        return args.content
    data = sys.stdin.read()
    if data.strip():
        return data
    raise ValueError("No report content provided. Use --content, --content-file, or stdin.")


def load_module(name: str, script: Path):
    spec = importlib.util.spec_from_file_location(name, script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def export(title: str, markdown: str, output_dir: Path, formats: list[str]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    requested = {fmt.lower() for fmt in formats}
    files: dict[str, str] = {}
    children: dict[str, dict] = {}
    if "html" in requested or "poster" in requested:
        module = load_module(
            "mineintel_html_poster",
            PACKAGE_DIR / "mineintel-html-poster" / "scripts" / "render_html_poster.py",
        )
        result = module.export(title, markdown, output_dir)
        children["html_poster"] = result
        files.update(result.get("files", {}))
    if requested.intersection({"deck", "ppt", "slides"}):
        module = load_module(
            "mineintel_deck_export",
            PACKAGE_DIR / "mineintel-deck-export" / "scripts" / "render_deck.py",
        )
        result = module.export(title, markdown, output_dir)
        children["deck"] = result
        files.update(result.get("files", {}))
    if requested.intersection({"tex", "latex", "pdf"}):
        module = load_module(
            "mineintel_literature_review",
            PACKAGE_DIR / "mineintel-literature-review" / "scripts" / "build_literature_review.py",
        )
        result = module.export(title, markdown, output_dir, compile_pdf="pdf" in requested)
        children["literature_review"] = result
        files.update(result.get("files", {}))
    return {
        "status": "success",
        "title": title,
        "formats_requested": sorted(requested),
        "files": files,
        "children": children,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export MineIntel HTML report, deck, and literature-review LaTeX/PDF.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--content")
    parser.add_argument("--content-file")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    parser.add_argument("--formats", default="html,deck,tex,pdf", help="Comma-separated formats: html, deck, tex, pdf.")
    args = parser.parse_args()
    try:
        formats = [x.strip().lower() for x in args.formats.split(",") if x.strip()]
        result = export(args.title, read_content(args), Path(args.output_dir), formats)
    except Exception as exc:
        result = {"status": "error", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
