#!/usr/bin/env python3
"""
Browser automation utilities using Playwright.
Run with: uv run browser.py <command> [options]
"""

import argparse
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeout


# Default auth directory relative to project root
AUTH_DIR = Path(__file__).parent.parent.parent.parent.parent / ".auth"


def get_auth_file(account: str) -> Path:
    """Get the auth file path for an account."""
    return AUTH_DIR / f"{account}.json"


def ensure_auth_dir() -> None:
    """Create .auth directory and add to .gitignore if needed."""
    AUTH_DIR.mkdir(parents=True, exist_ok=True)

    gitignore = AUTH_DIR.parent / ".gitignore"
    gitignore_entry = ".auth"

    if gitignore.exists():
        content = gitignore.read_text()
        if gitignore_entry not in content.split('\n'):
            with gitignore.open('a') as f:
                f.write(f"\n{gitignore_entry}\n")
    else:
        gitignore.write_text(f"{gitignore_entry}\n")


def wait_for_page_load(page: Page, timeout: int = 10000, extra_wait: float = 0) -> None:
    """Wait for page to load with fallback for sites with continuous network activity."""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except PlaywrightTimeout:
        # Fallback for sites like Gemini with continuous network activity
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)  # Allow JS to render

    if extra_wait > 0:
        time.sleep(extra_wait)


def create_browser(headless: bool = True) -> tuple[Browser, Page]:
    """Create a browser instance and return browser and page."""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    page = browser.new_page()
    return browser, page


def get_playwright_user_data_dir(account: str) -> Path:
    """Get a separate user data directory for Playwright (won't conflict with running Chrome)."""
    return AUTH_DIR / "profiles" / account


def create_login(url: str, account: str, wait_seconds: int = 120, channel: str | None = "chrome") -> None:
    """Open browser for manual login and save authentication state."""
    ensure_auth_dir()
    auth_file = get_auth_file(account)

    # Create a persistent profile directory for this account
    user_data_dir = get_playwright_user_data_dir(account)
    user_data_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        print(f"Using browser channel: {channel}")
        print(f"Using profile directory: {user_data_dir}")

        # Use persistent context to maintain login state and bypass automation detection
        context = p.chromium.launch_persistent_context(
            str(user_data_dir),
            headless=False,
            channel=channel,
            no_viewport=True,
            args=[
                "--disable-infobars",
                "--no-first-run",
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
            ignore_default_args=["--enable-automation"],
        )
        print(f"Browser version: {context.browser.version if context.browser else 'N/A'}")
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(url)

        print(f"Browser opened at: {url}")
        print(f"Please login manually. Session will be saved in {wait_seconds} seconds...")
        print("(Or close the browser tab when done)")

        # Wait for either timeout or page close
        elapsed = 0
        while elapsed < wait_seconds and not page.is_closed():
            time.sleep(1)
            elapsed += 1
            remaining = wait_seconds - elapsed
            if remaining > 0 and remaining % 30 == 0:
                print(f"  {remaining} seconds remaining...")

        # Save storage state (cookies, localStorage, etc.)
        if not context.pages:
            # If all pages closed, we can't save - reopen briefly
            print("Browser closed. Attempting to save session...")
        else:
            context.storage_state(path=str(auth_file))
            print(f"Authentication saved to: {auth_file}")

        context.close()


def list_accounts() -> list[str]:
    """List all saved accounts."""
    if not AUTH_DIR.exists():
        return []
    return [f.stem for f in AUTH_DIR.glob("*.json")]


def goto(url: str, headless: bool = True, screenshot: str | None = None, wait: float = 0, account: str | None = None, channel: str | None = None) -> str:
    """Navigate to a URL and return page content."""
    with sync_playwright() as p:
        if account:
            # Use persistent context with saved profile
            user_data_dir = get_playwright_user_data_dir(account)
            if not user_data_dir.exists():
                print(f"Warning: Account '{account}' not found. Run 'create-login' first.")
                return ""
            context = p.chromium.launch_persistent_context(
                str(user_data_dir),
                headless=headless,
                channel=channel or "chrome",
                viewport={"width": 1920, "height": 1080},
                args=["--disable-infobars"],
                ignore_default_args=["--enable-automation", "--no-sandbox"],
            )
            page = context.pages[0] if context.pages else context.new_page()
        else:
            browser = p.chromium.launch(headless=headless, channel=channel)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

        page.goto(url)
        wait_for_page_load(page, extra_wait=wait)

        if screenshot:
            page.screenshot(path=screenshot, full_page=True)
            print(f"Screenshot saved to: {screenshot}")

        content = page.content()
        context.close()
        return content


def screenshot(url: str, output: str = "screenshot.png", full_page: bool = True, wait: float = 0, account: str | None = None, channel: str | None = None) -> None:
    """Take a screenshot of a URL with full screen viewport."""
    with sync_playwright() as p:
        if account:
            # Use persistent context with saved profile
            user_data_dir = get_playwright_user_data_dir(account)
            if not user_data_dir.exists():
                print(f"Warning: Account '{account}' not found. Run 'create-login' first.")
                return
            context = p.chromium.launch_persistent_context(
                str(user_data_dir),
                headless=True,
                channel=channel or "chrome",
                viewport={"width": 1920, "height": 1080},
                args=["--disable-infobars"],
                ignore_default_args=["--enable-automation", "--no-sandbox"],
            )
            page = context.pages[0] if context.pages else context.new_page()
        else:
            browser = p.chromium.launch(headless=True, channel=channel)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

        page.goto(url)
        wait_for_page_load(page, extra_wait=wait)
        page.screenshot(path=output, full_page=full_page)
        print(f"Screenshot saved to: {output}")
        context.close()


def get_text(url: str, selector: str = "body") -> str:
    """Extract text content from a URL using a selector."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url)
        wait_for_page_load(page)

        text = page.locator(selector).text_content()
        browser.close()
        return text or ""


def get_links(url: str) -> list[dict]:
    """Extract all links from a URL."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url)
        wait_for_page_load(page)

        links = page.locator("a").all()
        result = []
        for link in links:
            href = link.get_attribute("href")
            text = link.text_content()
            if href:
                result.append({"href": href, "text": text.strip() if text else ""})

        browser.close()
        return result


def fill_form(url: str, fields: dict[str, str], submit_selector: str | None = None) -> str:
    """Fill a form and optionally submit it."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url)
        wait_for_page_load(page)

        for selector, value in fields.items():
            page.fill(selector, value)

        if submit_selector:
            page.click(submit_selector)
            wait_for_page_load(page)

        content = page.content()
        browser.close()
        return content


def click(url: str, selector: str, wait_after: bool = True) -> str:
    """Click an element on a page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url)
        wait_for_page_load(page)

        page.click(selector)

        if wait_after:
            wait_for_page_load(page)

        content = page.content()
        browser.close()
        return content


def pdf(url: str, output: str = "page.pdf") -> None:
    """Save a page as PDF."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url)
        wait_for_page_load(page)
        page.pdf(path=output)
        print(f"PDF saved to: {output}")
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="Browser automation with Playwright")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create-login command
    login_parser = subparsers.add_parser("create-login", help="Open browser for manual login and save session")
    login_parser.add_argument("url", help="URL to login page")
    login_parser.add_argument("--account", "-a", required=True, help="Account name to save as")
    login_parser.add_argument("--wait", "-w", type=int, default=120, help="Seconds to wait for login (default: 120)")
    login_parser.add_argument("--channel", "-c", default="chrome", help="Browser channel: chrome, msedge, chromium (default: chrome)")

    # accounts command
    subparsers.add_parser("accounts", help="List saved accounts")

    # goto command
    goto_parser = subparsers.add_parser("goto", help="Navigate to a URL")
    goto_parser.add_argument("url", help="URL to navigate to")
    goto_parser.add_argument("--screenshot", "-s", help="Save screenshot to file")
    goto_parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    goto_parser.add_argument("--wait", "-w", type=float, default=0, help="Extra wait time in seconds after page load")
    goto_parser.add_argument("--account", "-a", help="Use saved account for authentication")

    # screenshot command
    screenshot_parser = subparsers.add_parser("screenshot", help="Take a screenshot")
    screenshot_parser.add_argument("url", help="URL to screenshot")
    screenshot_parser.add_argument("--output", "-o", default="screenshot.png", help="Output file")
    screenshot_parser.add_argument("--no-full-page", action="store_true", help="Capture viewport only")
    screenshot_parser.add_argument("--wait", "-w", type=float, default=0, help="Extra wait time in seconds after page load")
    screenshot_parser.add_argument("--account", "-a", help="Use saved account for authentication")

    # text command
    text_parser = subparsers.add_parser("text", help="Extract text from a page")
    text_parser.add_argument("url", help="URL to extract text from")
    text_parser.add_argument("--selector", "-s", default="body", help="CSS selector")

    # links command
    links_parser = subparsers.add_parser("links", help="Extract links from a page")
    links_parser.add_argument("url", help="URL to extract links from")

    # pdf command
    pdf_parser = subparsers.add_parser("pdf", help="Save page as PDF")
    pdf_parser.add_argument("url", help="URL to save")
    pdf_parser.add_argument("--output", "-o", default="page.pdf", help="Output file")

    args = parser.parse_args()

    if args.command == "create-login":
        channel = args.channel if args.channel != "chromium" else None
        create_login(args.url, args.account, args.wait, channel)
    elif args.command == "accounts":
        accounts = list_accounts()
        if accounts:
            print("Saved accounts:")
            for acc in accounts:
                print(f"  - {acc}")
        else:
            print("No saved accounts. Use 'create-login' to save one.")
    elif args.command == "goto":
        content = goto(args.url, headless=not args.no_headless, screenshot=args.screenshot, wait=args.wait, account=args.account)
        print(content[:2000] if len(content) > 2000 else content)
    elif args.command == "screenshot":
        screenshot(args.url, args.output, full_page=not args.no_full_page, wait=args.wait, account=args.account)
    elif args.command == "text":
        text = get_text(args.url, args.selector)
        print(text)
    elif args.command == "links":
        links = get_links(args.url)
        print(json.dumps(links, indent=2))
    elif args.command == "pdf":
        pdf(args.url, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
