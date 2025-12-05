#!/usr/bin/env python3
"""
Image search and download utilities with multi-source support.

This module provides the GoogleImage class for searching and downloading images
from multiple sources with a tiered fallback strategy:

1. DuckDuckGo (fastest, no browser, ~2s for 100 images)
2. Bing (fast, no browser, ~5s for 100 images)
3. Google + Playwright (slowest, most reliable, ~15s for 50 images)

Optimizations applied:
- DuckDuckGo/Bing API search (no browser needed)
- Regex extraction from page source (19x faster than clicking thumbnails)
- Parallel downloads with ThreadPoolExecutor (10 workers)
- Smart scrolling to load more results

Usage via browser.py:
    uv run browser.py google-image "keyword" -a account --size Large
    uv run browser.py google-image "keyword" -a account -n 100 -o ./downloads
"""

import dataclasses
import logging
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Literal

import requests
from playwright.sync_api import sync_playwright, Page

logger = logging.getLogger(__name__)

# Constants for download optimization
DEFAULT_DOWNLOAD_WORKERS = 10
DEFAULT_DOWNLOAD_TIMEOUT = 15

# Size mapping for DuckDuckGo
DDGS_SIZE_MAP = {
    "4k": "Large",  # DuckDuckGo doesn't have 4K, use Large and filter by dimension
    "fullhd": "Large",  # DuckDuckGo doesn't have FullHD, use Large and filter by dimension
    "Large": "Large",
    "Medium": "Medium",
    "Icon": "Small",
}

# Minimum dimensions for size filters (width or height must meet this)
MIN_DIMENSION = {
    "4k": 3840,  # 4K resolution (3840x2160)
    "fullhd": 1920,  # Full HD resolution (1920x1080)
    "Large": 1000,
    "Medium": 400,
    "Icon": 0,
}


def search_duckduckgo_images(
    keyword: str,
    num: int = 100,
    size: str | None = None,
) -> list[dict]:
    """Search images using DuckDuckGo (no browser needed).

    This is the fastest method - ~2s for 100 images.

    Args:
        keyword: Search query
        num: Maximum number of results
        size: Size filter (Large, Medium, Small/Icon)

    Returns:
        List of dicts with 'url', 'title', 'source' keys
    """
    try:
        # Try new package name first (ddgs), fallback to old (duckduckgo_search)
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
    except ImportError:
        logger.debug("duckduckgo-search/ddgs not installed")
        return []

    try:
        ddgs_size = DDGS_SIZE_MAP.get(size) if size else None
        min_dim = MIN_DIMENSION.get(size, 0) if size else 0

        # Pagination: keep fetching until we have enough images meeting size criteria
        images = []
        seen_urls = set()
        filtered_count = 0
        batch_size = 100  # Fetch 100 at a time
        max_batches = 10  # Max 1000 images total to prevent infinite loops

        with DDGS() as ddgs:
            for batch_num in range(max_batches):
                if len(images) >= num:
                    break

                # Calculate offset for pagination
                offset = batch_num * batch_size

                results = list(ddgs.images(
                    keywords=keyword,
                    region="wt-wt",
                    safesearch="off",
                    size=ddgs_size,
                    max_results=batch_size + offset,
                ))

                # Skip already seen results (pagination returns cumulative results)
                new_results = results[offset:] if offset < len(results) else []

                if not new_results:
                    logger.info("DuckDuckGo: no more images available after %d results", offset)
                    break

                # Filter by actual dimensions
                for r in new_results:
                    url = r.get("image", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    width = r.get("width", 0)
                    height = r.get("height", 0)

                    # Filter by minimum dimension if size filter is specified
                    if min_dim > 0 and max(width, height) < min_dim:
                        filtered_count += 1
                        continue

                    images.append({
                        "url": url,
                        "title": r.get("title", ""),
                        "source": r.get("url", ""),
                        "width": width,
                        "height": height,
                    })

                    if len(images) >= num:
                        break

                logger.info("DuckDuckGo batch %d: found %d/%d images (filtered %d)",
                           batch_num + 1, len(images), num, filtered_count)

        if filtered_count > 0:
            logger.info("DuckDuckGo: total filtered out %d images smaller than %dpx", filtered_count, min_dim)
        logger.info("DuckDuckGo found %d images meeting size criteria", len(images))
        return images

    except Exception as e:
        logger.warning("DuckDuckGo search failed: %s", e)
        return []


# Size filter options (4k = 3840px, fullhd = 1920px minimum dimension)
SizeFilter = Literal["4k", "fullhd", "Large", "Medium", "Icon"]

# URL parameters for size filters
SIZE_PARAMS = {
    "4k": "isz:l",  # Google doesn't have 4K param, use Large
    "fullhd": "isz:l",  # Google doesn't have FullHD param, use Large
    "Large": "isz:l",
    "Medium": "isz:m",
    "Icon": "isz:i",
}


def extract_image_urls_from_source(html: str, limit: int = 100) -> list[str]:
    """Extract full-size image URLs from Google Images page source using regex.

    This is 19x faster than clicking thumbnails because URLs are embedded
    in AF_initDataCallback JavaScript functions.

    Args:
        html: Page source HTML
        limit: Maximum number of URLs to extract

    Returns:
        List of full-size image URLs
    """
    urls = []
    seen = set()

    # Pattern matches: ["https://example.com/image.jpg", width, height]
    pattern = r'\["(https?://[^"]+)",\s*\d+,\s*\d+\]'

    for match in re.finditer(pattern, html):
        url = match.group(1)

        # Skip Google's thumbnail CDN
        if "encrypted-tbn0.gstatic.com" in url:
            continue

        # Skip base64 data URLs
        if url.startswith("data:"):
            continue

        # Skip small preview images
        if "googleusercontent.com" in url and "=s" in url:
            continue

        try:
            # Decode unicode escapes (e.g., \u003d -> =)
            url = bytes(url, 'ascii').decode('unicode-escape')
        except (UnicodeDecodeError, ValueError):
            pass

        if url not in seen:
            seen.add(url)
            urls.append(url)
            if len(urls) >= limit:
                break

    return urls


def download_single_image(args: tuple) -> str | None:
    """Download a single image. Used by ThreadPoolExecutor.

    Args:
        args: Tuple of (index, url, output_dir)

    Returns:
        Path to downloaded file or None if failed
    """
    idx, url, output_dir = args

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://www.google.com/",
        }

        response = requests.get(url, headers=headers, timeout=DEFAULT_DOWNLOAD_TIMEOUT, stream=True)
        response.raise_for_status()

        # Determine file extension from content-type or URL
        content_type = response.headers.get("content-type", "")
        if "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "png" in content_type:
            ext = ".png"
        elif "gif" in content_type:
            ext = ".gif"
        elif "webp" in content_type:
            ext = ".webp"
        else:
            # Try to get from URL
            ext = Path(urllib.parse.urlparse(url).path).suffix or ".jpg"

        output_path = output_dir / f"image_{idx:04d}{ext}"

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.debug("Downloaded: %s", output_path.name)
        return str(output_path)

    except Exception as e:
        logger.debug("Failed to download %s: %s", url[:50], str(e)[:50])
        return None


@dataclass
class GoogleImage:
    """Google Images search automation with optimized downloading.

    This class handles searching Google Images with various filters and
    downloading images using fast regex extraction + parallel downloads.

    Optimizations:
    - Regex extraction from page source (19x faster than clicking)
    - Parallel downloads with 10 workers
    - Smart scrolling to load more results
    - Fallback to click method if regex fails

    Attributes:
        keyword: Search query string (required).
        account: Account name to use for authentication (required).
        size: Size filter to apply ('Large', 'Medium', 'Icon').
        download: Number of images to download (0 = no download).
        download_dir: Directory to save downloaded images.
        output: Screenshot output path (optional).
        headless: Run browser in headless mode.
        keep_open: Keep browser open for N seconds after completion.
        workers: Number of parallel download workers.
    """

    # CLI metadata (class variables)
    _cli_name: ClassVar[str] = "google-image"
    _cli_description: ClassVar[str] = "Search and download images (DuckDuckGo/Google)"
    _cli_help: ClassVar[dict] = {
        "keyword": "Search keyword",
        "account": "Account name for authentication (optional if using DuckDuckGo only)",
        "size": "Size filter",
        "download": "Number of images to download (0 = no download)",
        "download_dir": "Directory to save downloaded images",
        "source": "Image source (duckduckgo=fast no browser, google=more results)",
        "output": "Screenshot output path",
        "headless": "Run in headless mode",
        "keep_open": "Keep browser open for N seconds",
        "workers": "Number of parallel download workers",
    }
    _cli_choices: ClassVar[dict] = {
        "size": ["4k", "fullhd", "Large", "Medium", "Icon"],
        "source": ["auto", "duckduckgo", "google"],
    }
    _cli_short: ClassVar[dict] = {
        "account": "a",
        "size": "s",
        "download": "n",
        "download_dir": "o",
        "source": "S",
        "output": "O",
        "keep_open": "k",
        "workers": "w",
    }

    # Instance fields (order matters for positional args)
    keyword: str
    account: str = ""  # Optional now - not needed for DuckDuckGo
    size: SizeFilter = "Large"
    download: int = 0
    download_dir: str = "./downloads"
    source: str = "auto"  # auto, duckduckgo, google
    output: str | None = None
    headless: bool = True
    keep_open: int = 0
    workers: int = DEFAULT_DOWNLOAD_WORKERS

    def execute(self, page: Page) -> list[str]:
        """Execute the Google Images search and optionally download images.

        Args:
            page: Playwright page instance (already opened).

        Returns:
            List of downloaded file paths (empty if download=0).
        """
        # Build search URL with size filter
        encoded_keyword = urllib.parse.quote(self.keyword)
        size_param = SIZE_PARAMS.get(self.size, "isz:l")
        search_url = f"https://www.google.com/search?q={encoded_keyword}&tbm=isch&tbs={size_param}"

        logger.info("Searching Google Images: '%s' (size=%s)", self.keyword, self.size)
        page.goto(search_url)
        self._wait_for_load(page)

        downloaded_files = []

        # Download images if requested
        if self.download > 0:
            downloaded_files = self._download_images(page)

        if self.output:
            self._take_screenshot(page, self.output)

        return downloaded_files

    def _download_images(self, page: Page | None) -> list[str]:
        """Download images using tiered search + parallel downloads.

        Strategy (3-tier fallback):
        1. DuckDuckGo search (fastest, no browser, ~2s)
        2. Google regex extraction (fast, uses browser)
        3. Google with scrolling (slowest, most results)

        Args:
            page: Playwright page instance (can be None for DuckDuckGo-only).

        Returns:
            List of downloaded file paths.
        """
        output_dir = Path(self.download_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        collected_urls = []

        # Tier 1: Try DuckDuckGo first (fastest, no browser needed)
        logger.info("Trying DuckDuckGo search (no browser)...")
        ddg_results = search_duckduckgo_images(self.keyword, self.download, self.size)
        if ddg_results:
            collected_urls = [r["url"] for r in ddg_results if r.get("url")]
            logger.info("DuckDuckGo returned %d URLs", len(collected_urls))

        # Tier 2: Fall back to Google regex extraction if DuckDuckGo fails or insufficient
        if len(collected_urls) < self.download and page:
            logger.info("Extracting from Google (regex)...")
            html = page.content()
            google_urls = extract_image_urls_from_source(html, self.download * 2)

            # Add new URLs we haven't seen
            seen = set(collected_urls)
            for url in google_urls:
                if url not in seen:
                    collected_urls.append(url)
                    seen.add(url)

            logger.info("Google regex found %d additional URLs", len(google_urls))

        # Tier 3: Scroll for more if still insufficient
        if len(collected_urls) < self.download and page:
            logger.info("Scrolling for more images...")
            scroll_count = 0
            max_scrolls = 5

            while len(collected_urls) < self.download and scroll_count < max_scrolls:
                page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
                time.sleep(0.3)
                scroll_count += 1

                html = page.content()
                new_urls = extract_image_urls_from_source(html, self.download * 2)

                seen = set(collected_urls)
                for url in new_urls:
                    if url not in seen:
                        collected_urls.append(url)
                        seen.add(url)

        # Trim to requested number
        urls_to_download = collected_urls[:self.download]

        if not urls_to_download:
            logger.warning("No image URLs found")
            return []

        logger.info("Downloading %d images with %d workers...",
                    len(urls_to_download), self.workers)

        # Download in parallel
        downloaded_files = []
        download_args = [(i, url, output_dir) for i, url in enumerate(urls_to_download)]

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(download_single_image, args): args[0]
                for args in download_args
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    downloaded_files.append(result)

        success_rate = len(downloaded_files) / len(urls_to_download) * 100 if urls_to_download else 0
        logger.info("Downloaded %d/%d images (%.0f%%) to %s",
                    len(downloaded_files), len(urls_to_download), success_rate, output_dir)

        return downloaded_files

    def run(self) -> list[str]:
        """Run the image search and download.

        Supports 3 modes:
        - source='duckduckgo': No browser needed, fastest
        - source='google': Uses Playwright browser
        - source='auto': Try DuckDuckGo first, fallback to Google
        """
        # DuckDuckGo-only mode (no browser needed)
        if self.source == "duckduckgo" or (self.source == "auto" and self.download > 0 and not self.account):
            logger.info("Using DuckDuckGo (no browser)")
            return self._download_images(page=None)

        # Google mode or auto with account - needs browser
        if not self.account:
            logger.warning("No account specified. Use -a <account> for Google, or -S duckduckgo for no-browser mode")
            # Try DuckDuckGo anyway
            return self._download_images(page=None)

        from browser import create_authenticated_context, wait_with_browser_check

        with sync_playwright() as p:
            context = create_authenticated_context(p, self.account, self.headless)
            page = context.pages[0] if context.pages else context.new_page()

            try:
                result = self.execute(page)

                if self.keep_open > 0:
                    logger.info("Browser open for %ds (close browser to exit early)...", self.keep_open)
                    wait_with_browser_check(page, self.keep_open)

                return result
            finally:
                context.close()

    def _wait_for_load(self, page: Page, timeout: int = 5000) -> None:
        """Wait for page to load - optimized with minimal delay.

        Uses smart waiting instead of fixed delays:
        1. Wait for DOM content loaded
        2. Wait for image grid to appear
        """
        try:
            page.wait_for_load_state("domcontentloaded", timeout=timeout)
            # Wait for Google Images grid to appear
            page.wait_for_selector("div[data-ri]", timeout=timeout)
        except Exception:
            # Fallback: brief wait
            time.sleep(1)

    def _take_screenshot(self, page: Page, output_path: str) -> None:
        """Take a screenshot of the current page."""
        page.screenshot(path=output_path, full_page=True)
        logger.info("Screenshot saved: %s", output_path)

    @classmethod
    def add_to_parser(cls, subparsers) -> None:
        """Add this command to argparse subparsers.

        Args:
            subparsers: argparse subparsers object.
        """
        parser = subparsers.add_parser(cls._cli_name, help=cls._cli_description)

        for name, fld in cls.__dataclass_fields__.items():
            if name.startswith("_"):
                continue

            help_text = cls._cli_help.get(name, "")
            is_required = fld.default is dataclasses.MISSING
            default = fld.default if not is_required else None
            short = cls._cli_short.get(name)

            # Build argument names
            if is_required:
                names = [name]
            else:
                names = [f"--{name}"]
                if short:
                    names.insert(0, f"-{short}")

            # Build kwargs
            kwargs = {"help": help_text}

            if not is_required:
                kwargs["default"] = default

            if name in cls._cli_choices:
                kwargs["choices"] = cls._cli_choices[name]

            # Handle boolean flags
            if fld.type is bool or (hasattr(fld, 'type') and fld.type is bool):
                if default is True:
                    # --no-headless style
                    names = [f"--no-{name}"]
                    kwargs["action"] = "store_false"
                    kwargs["dest"] = name
                    kwargs.pop("default", None)
                else:
                    kwargs["action"] = "store_true"

            # Handle int type
            if fld.type is int:
                kwargs["type"] = int

            parser.add_argument(*names, **kwargs)

    @classmethod
    def from_args(cls, args) -> "GoogleImage":
        """Create instance from parsed args.

        Args:
            args: Parsed argparse namespace.

        Returns:
            GoogleImage instance.
        """
        kwargs = {}
        for name in cls.__dataclass_fields__:
            if name.startswith("_"):
                continue
            if hasattr(args, name):
                kwargs[name] = getattr(args, name)
        return cls(**kwargs)
