#!/usr/bin/env python3
"""Analyze cached eufy support PDFs for model names and documented features."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_CACHE_DIR = Path(".cache/eufy-support-pdfs")

CLEAN_MODE_PATTERNS = {
    "auto": r"\bAuto[- ]cleaning mode\b|\bAuto cleaning\b",
    "spot": r"\bSpot[- ]cleaning mode\b|\bSpot cleaning\b",
    "edge": r"\bEdge[- ]cleaning mode\b|\bEdge cleaning\b",
    "single_room": r"\b(?:Single|Small) Room(?:[- ]cleaning)? mode\b",
    "manual": r"\bManual[- ]cleaning mode\b",
}

SUCTION_PATTERNS = {
    "quiet": r"\bQuiet\b",
    "pure": r"\bPure\b",
    "standard": r"\bStandard\b",
    "turbo": r"\bTurbo\b",
    "max": r"\bMax(?:imum)?\b",
    "boost_iq": r"\bBoost\s*IQ\b|\bBoostIQ\b",
}

FEATURE_PATTERNS = {
    "boost_iq": r"\bBoost\s*IQ\b|\bBoostIQ\b",
    "mopping": r"\bMopping System\b|\bWater Tank\b|\bmopping mode\b",
    "boundary_strip": r"\bBoundary Strip\b",
    "room_cleaning": r"\broom cleaning\b|\bRoom(?:s)?\b",
    "zone_cleaning": r"\bzone cleaning\b|\bNo-Go Zone\b|\bvirtual boundary\b",
    "map": r"\bMap\b|\bmapping\b",
    "find_robot": r"\bFind My Robot\b|\bFind Robot\b",
    "scheduling": r"\bSchedule Cleaning\b|\bscheduled cleaning\b",
    "auto_empty": r"\bAuto[- ]Empty\b|\bself-empty\b",
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help=f"cache directory (default: {DEFAULT_CACHE_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write JSON report to this path",
    )
    return parser.parse_args()


def load_manifest(cache_dir: Path) -> dict[str, Any]:
    """Load the PDF cache manifest."""
    manifest_path = cache_dir / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"cache manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text())


def extract_text(pdf_path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        from pypdf import PdfReader
    except ImportError as err:
        raise RuntimeError(
            "pypdf is required for PDF analysis. Run with "
            "`uv run --with pypdf python scripts/analyze_eufy_support_pdfs.py`."
        ) from err

    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def clean_text(text: str) -> str:
    """Normalize whitespace in extracted PDF text."""
    return re.sub(r"\s+", " ", text)


def find_keys(text: str, patterns: dict[str, str]) -> list[str]:
    """Return pattern keys found in text."""
    return [
        key
        for key, pattern in patterns.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]


def parse_supported_models(path: Path) -> dict[str, str]:
    """Parse site_docs/supported-models.md into model-code friendly names."""
    model_names: dict[str, str] = {}
    row_pattern = re.compile(r"^\|\s*(T\d+)\s*\|\s*([^|]+?)\s*\|")
    for line in path.read_text().splitlines():
        match = row_pattern.match(line)
        if match:
            model_names[match.group(1)] = match.group(2).strip()
    return model_names


def mentioned_model_codes(text: str) -> list[str]:
    """Return T-model codes mentioned in extracted PDF text."""
    return sorted(set(re.findall(r"\bT\d{4}\b", text)))


def analyze_product(product: dict[str, Any]) -> dict[str, Any]:
    """Analyze cached PDFs for one product."""
    combined_text = ""
    analyzed_downloads: list[dict[str, Any]] = []
    for download in product.get("downloads") or []:
        cache = download.get("cache") or {}
        path = cache.get("path")
        if not path:
            continue

        pdf_path = Path(path)
        if not pdf_path.exists():
            analyzed_downloads.append(
                {
                    "name": download.get("name"),
                    "path": path,
                    "error": "cached PDF missing",
                }
            )
            continue

        try:
            text = clean_text(extract_text(pdf_path))
        except Exception as exc:  # noqa: BLE001 - keep the cache audit moving.
            analyzed_downloads.append(
                {
                    "name": download.get("name"),
                    "path": path,
                    "error": str(exc),
                }
            )
            continue

        combined_text += " " + text
        analyzed_downloads.append(
            {
                "name": download.get("name"),
                "path": path,
                "model_codes": mentioned_model_codes(text),
                "clean_modes": find_keys(text, CLEAN_MODE_PATTERNS),
                "suction_levels": find_keys(text, SUCTION_PATTERNS),
                "features": find_keys(text, FEATURE_PATTERNS),
                "supported_functions": find_keys(text, FEATURE_PATTERNS),
            }
        )

    combined_text = clean_text(combined_text)
    return {
        "pn": product["pn"],
        "friendly_name": product["name"],
        "series": product.get("series"),
        "support_url": product.get("url"),
        "manual_count": len(product.get("downloads") or []),
        "documented_model_codes": mentioned_model_codes(combined_text),
        "clean_modes": find_keys(combined_text, CLEAN_MODE_PATTERNS),
        "suction_levels": find_keys(combined_text, SUCTION_PATTERNS),
        "features": find_keys(combined_text, FEATURE_PATTERNS),
        "supported_functions": find_keys(combined_text, FEATURE_PATTERNS),
        "downloads": analyzed_downloads,
    }


def build_report(cache_dir: Path) -> dict[str, Any]:
    """Build the eufy support PDF analysis report."""
    manifest = load_manifest(cache_dir)
    site_docs_names = parse_supported_models(Path("site_docs/supported-models.md"))

    products = [analyze_product(product) for product in manifest["products"]]
    support_names = {
        product["pn"]: product["friendly_name"]
        for product in products
        if product.get("friendly_name")
    }

    supported_name_mismatches = []
    for model_code, docs_name in sorted(site_docs_names.items()):
        support_name = support_names.get(model_code)
        if support_name is not None and docs_name != support_name:
            supported_name_mismatches.append(
                {
                    "model_code": model_code,
                    "supported_models_name": docs_name,
                    "eufy_support_name": support_name,
                }
            )

    products_by_manual: dict[str, list[str]] = defaultdict(list)
    for product in products:
        for download in product["downloads"]:
            path = download.get("path")
            if path:
                products_by_manual[path].append(product["pn"])

    return {
        "cache_manifest": str(cache_dir / "manifest.json"),
        "product_count": len(products),
        "products": products,
        "supported_name_mismatches": supported_name_mismatches,
        "products_without_primary_manual": [
            {
                "pn": product["pn"],
                "friendly_name": product["friendly_name"],
            }
            for product in products
            if product["manual_count"] == 0
        ],
        "shared_manuals": {
            path: sorted(model_codes)
            for path, model_codes in sorted(products_by_manual.items())
            if len(model_codes) > 1
        },
    }


def main() -> int:
    """Run the analysis."""
    args = parse_args()
    report = build_report(args.cache_dir)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
        print(f"Wrote {args.output}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - CLI should print a concise failure.
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
