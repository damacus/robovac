#!/usr/bin/env python3
"""Cache eufy support PDFs for RoboVac/eufy Clean vacuum products."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MANUAL_INDEX_URL = "https://support.eufy.com/s/articleRecommend?type=DownLoad&secondType=Manuals"
DEFAULT_CACHE_DIR = Path(".cache/eufy-support-pdfs")
USER_AGENT = "robovac-support-cache/1.0"


@dataclass(frozen=True)
class Product:
    """A eufy support product record."""

    pn: str
    name: str
    series: str
    url: str


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
        "--product",
        action="append",
        default=[],
        help="limit to one product number; repeat for multiple products",
    )
    parser.add_argument("--limit", type=int, help="limit number of products")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="write the manifest without downloading PDFs",
    )
    parser.add_argument(
        "--all-documents",
        action="store_true",
        help="cache every support document instead of one primary owner manual per product",
    )
    parser.add_argument(
        "--from-manifest",
        type=Path,
        help="download PDFs from an existing extracted-downloads manifest",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=30_000,
        help="page-load timeout for each product page",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="show the browser while collecting download links",
    )
    return parser.parse_args()


def fetch_text(url: str) -> str:
    """Fetch text from a URL."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def load_products() -> list[Product]:
    """Load RoboVac/eufy Clean vacuum products from eufy's manual index."""
    index_html = fetch_text(MANUAL_INDEX_URL)
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        index_html,
    )
    if match is None:
        raise RuntimeError("could not find __NEXT_DATA__ in eufy manual index")

    data = json.loads(html.unescape(match.group(1)))
    products: dict[str, Product] = {}

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return

        if not isinstance(node, dict):
            return

        for product in node.get("products") or []:
            pn = str(product.get("pn") or "")
            name = str(product.get("name") or "")
            lowered_name = name.lower()
            if (
                "robovac" not in lowered_name
                and "eufy clean" not in lowered_name
                and not pn.startswith("T22")
            ):
                continue

            url = str(product.get("url") or "")
            if not url:
                continue

            products[url] = Product(
                pn=pn,
                name=name,
                series=str(product.get("secondCategory") or ""),
                url=url,
            )

        for value in node.values():
            walk(value)

    walk(data["props"]["pageProps"]["categoryMap"])
    return sorted(products.values(), key=lambda p: (p.series, p.pn, p.name))


def collect_downloads(products: list[Product], timeout_ms: int, headless: bool) -> list[dict[str, Any]]:
    """Render product pages and collect their PDF download links."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as err:
        raise RuntimeError(
            "Playwright is required to refresh the eufy PDF cache. "
            "Install it in your dev environment, then run "
            "`uv run playwright install chromium`."
        ) from err

    product_entries: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()
        page.set_default_timeout(timeout_ms)

        for product in products:
            page.goto(product.url, wait_until="load")
            try:
                page.wait_for_function(
                    """
                    () => {
                      const host = document.querySelector('c-product-description');
                      const root = host && host.shadowRoot;
                      return root && root.querySelectorAll('.div-20[data-id]').length > 0;
                    }
                    """
                )
                downloads = page.evaluate(
                    """
                    () => {
                      const root = document.querySelector('c-product-description').shadowRoot;
                      return [...root.querySelectorAll('.div-20[data-id]')].map((el) => ({
                        name: (el.innerText || '').replace(/\\s*Download\\s*$/, '').trim(),
                        url: el.getAttribute('data-id')
                      }));
                    }
                    """
                )
                error = None
            except Exception as exc:  # noqa: BLE001 - keep cache refresh best-effort.
                downloads = []
                error = str(exc)

            product_entries.append(
                {
                    "pn": product.pn,
                    "name": product.name,
                    "series": product.series,
                    "url": product.url,
                    "downloads": downloads,
                    **({"error": error} if error else {}),
                }
            )

        browser.close()

    return product_entries


def safe_filename(value: str) -> str:
    """Return a filesystem-safe filename stem."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-")
    return safe[:120] or "download"


def primary_manual_score(download: dict[str, Any]) -> tuple[int, str] | None:
    """Return a ranking score for likely owner manuals."""
    name = str(download.get("name") or "")
    normalized = name.lower()
    if "manual" not in normalized and "user guide" not in normalized:
        return None
    if any(
        excluded in normalized
        for excluded in (
            "quick start",
            "declaration",
            " eu doc",
            " uk&ca",
            "product introduction",
        )
    ):
        return None

    compact = re.sub(r"[^a-z0-9]+", "_", normalized)
    if "user_guide" in compact:
        score = 0
    elif "manual_us" in compact or "en_manual" in compact:
        score = 0
    elif "manual_en" in compact:
        score = 1
    elif "manual_eu" in compact or "eu_manual" in compact:
        score = 5
    elif "manual_other" in compact:
        score = 8
    elif "manual_jp" in compact:
        score = 20
    else:
        score = 10

    return (score, name)


def keep_primary_manuals(product_entries: list[dict[str, Any]]) -> None:
    """Reduce each product's downloads to one best owner manual."""
    for product in product_entries:
        downloads = list(product.get("downloads") or [])
        ranked = [
            (score, download)
            for download in downloads
            if (score := primary_manual_score(download)) is not None
        ]
        product["available_download_count"] = len(downloads)
        product["downloads"] = [min(ranked, key=lambda item: item[0])[1]] if ranked else []


def download_pdf(url: str, name: str, pdf_dir: Path) -> dict[str, Any]:
    """Download a PDF and return cache metadata."""
    url_key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    target = pdf_dir / f"{url_key}-{safe_filename(name)}.pdf"
    if target.exists():
        data = target.read_bytes()
        return {
            "status": "cached",
            "path": str(target),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=120) as response:
            content_type = response.headers.get("content-type", "")
            data = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        return {"status": "error", "error": str(exc)}

    if "pdf" not in content_type.lower() and not data.startswith(b"%PDF"):
        return {
            "status": "skipped_non_pdf",
            "content_type": content_type,
            "bytes": len(data),
        }

    target.write_bytes(data)
    return {
        "status": "downloaded",
        "path": str(target),
        "content_type": content_type,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def write_manifest(cache_dir: Path, manifest: dict[str, Any]) -> None:
    """Write the cache manifest."""
    manifest_path = cache_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    """Refresh the eufy support PDF cache."""
    args = parse_args()
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir = args.cache_dir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    if args.from_manifest is not None:
        extracted = json.loads(args.from_manifest.read_text())
        product_entries = extracted["products"]
        if args.product:
            wanted = {product.upper() for product in args.product}
            product_entries = [
                product
                for product in product_entries
                if str(product.get("pn", "")).upper() in wanted
            ]
        if args.limit is not None:
            product_entries = product_entries[: args.limit]
    else:
        products = load_products()
        if args.product:
            wanted = {product.upper() for product in args.product}
            products = [product for product in products if product.pn.upper() in wanted]
        if args.limit is not None:
            products = products[: args.limit]

        product_entries = collect_downloads(
            products=products,
            timeout_ms=args.timeout_ms,
            headless=not args.headful,
        )

    if not args.all_documents:
        keep_primary_manuals(product_entries)

    download_count = 0
    unique_urls: dict[str, dict[str, Any]] = {}
    if not args.skip_download:
        for product in product_entries:
            for download in product["downloads"]:
                url = str(download.get("url") or "")
                name = str(download.get("name") or "")
                if not url:
                    continue
                if url not in unique_urls:
                    unique_urls[url] = download_pdf(url, name, pdf_dir)
                download["cache"] = unique_urls[url]
                if unique_urls[url]["status"] in {"downloaded", "cached"}:
                    download_count += 1

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": MANUAL_INDEX_URL,
        "product_count": len(product_entries),
        "unique_download_count": len(unique_urls),
        "cached_download_count": download_count,
        "products": product_entries,
    }
    write_manifest(args.cache_dir, manifest)
    print(
        f"Wrote {args.cache_dir / 'manifest.json'} "
        f"for {len(product_entries)} products and {len(unique_urls)} unique downloads"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - CLI should print a concise failure.
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
