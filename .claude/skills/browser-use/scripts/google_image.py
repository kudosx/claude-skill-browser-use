#!/usr/bin/env python3
"""
Google Images automation utilities using Playwright.

This module provides the GoogleImage class for searching and filtering images
on Google Images with authentication support.

Usage via browser.py:
    uv run browser.py google-image "keyword" -a account --size Large
    uv run browser.py google-image "keyword" -a account --size Large --download 100 -o ./downloads
"""

import base64
import dataclasses
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Literal

import requests
from playwright.sync_api import sync_playwright, Page


# Size filter options
SizeFilter = Literal["Large", "Medium", "Icon"]

# URL parameters for size filters
SIZE_PARAMS = {
    "Large": "isz:l",
    "Medium": "isz:m",
    "Icon": "isz:i",
}


@dataclass
class GoogleImage:
    """Google Images search automation.

    This class handles searching Google Images with various filters.
    Browser lifecycle is managed via browser.py utilities.

    Attributes:
        keyword: Search query string (required).
        account: Account name to use for authentication (required).
        size: Size filter to apply ('Large', 'Medium', 'Icon').
        output: Screenshot output path (optional).
        headless: Run browser in headless mode.
        keep_open: Keep browser open for N seconds after completion.
    """

    # CLI metadata (class variables)
    _cli_name: ClassVar[str] = "google-image"
    _cli_description: ClassVar[str] = "Search Google Images with filters"
    _cli_help: ClassVar[dict] = {
        "keyword": "Search keyword",
        "account": "Account name for authentication",
        "size": "Size filter",
        "output": "Screenshot output path",
        "headless": "Run in headless mode",
        "keep_open": "Keep browser open for N seconds",
    }
    _cli_choices: ClassVar[dict] = {
        "size": ["Large", "Medium", "Icon"],
    }
    _cli_short: ClassVar[dict] = {
        "account": "a",
        "size": "s",
        "output": "o",
        "keep_open": "k",
    }

    # Instance fields (order matters for positional args)
    keyword: str
    account: str
    size: SizeFilter = "Large"
    output: str | None = None
    headless: bool = True
    keep_open: int = 0

    def execute(self, page: Page) -> None:
        """Execute the Google Images search on the given page.

        Args:
            page: Playwright page instance (already opened).
        """
        # Build search URL with size filter
        encoded_keyword = urllib.parse.quote(self.keyword)
        size_param = SIZE_PARAMS.get(self.size, "isz:l")
        search_url = f"https://www.google.com/search?q={encoded_keyword}&tbm=isch&tbs={size_param}"

        print(f"Searching Google Images: '{self.keyword}' (size={self.size})")
        page.goto(search_url)
        self._wait_for_load(page)

        if self.output:
            self._take_screenshot(page, self.output)

    def run(self) -> None:
        """Run the complete search with browser management."""
        from browser import create_authenticated_context, wait_with_browser_check

        with sync_playwright() as p:
            context = create_authenticated_context(p, self.account, self.headless)
            page = context.pages[0] if context.pages else context.new_page()

            try:
                self.execute(page)

                if self.keep_open > 0:
                    print(f"Browser open for {self.keep_open}s (close browser to exit early)...")
                    wait_with_browser_check(page, self.keep_open)
            finally:
                context.close()

    def _wait_for_load(self, page: Page, timeout: int = 10000, extra_wait: float = 3) -> None:
        """Wait for page to fully load."""
        try:
            page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)

        if extra_wait > 0:
            time.sleep(extra_wait)

    def _take_screenshot(self, page: Page, output_path: str) -> None:
        """Take a screenshot of the current page."""
        page.screenshot(path=output_path, full_page=True)
        print(f"Screenshot saved: {output_path}")

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
