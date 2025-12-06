# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude skill for browser automation using Playwright. It provides a CLI tool (`browser.py`) for web scraping, screenshots, form filling, file downloads/uploads, Google Images scraping, YouTube video downloading, and TikTok video downloading.

## Running Commands

All commands must be run from the scripts directory:

```bash
cd .claude/skills/browser-use/scripts
uv run browser.py <command> [options]
```

### Common Commands

```bash
# Navigation and screenshots
uv run browser.py goto https://example.com
uv run browser.py screenshot https://example.com -o page.png

# Form interaction
uv run browser.py fill "https://google.com" "input[name=q]" "search" --press Enter
uv run browser.py click https://example.com "button.submit"

# Data extraction
uv run browser.py text https://example.com --selector "h1"
uv run browser.py links https://example.com
uv run browser.py extract https://example.com "img" --attr src --all

# Authentication (creates persistent Chrome profile)
uv run browser.py create-login https://example.com --account myaccount
uv run browser.py accounts

# Google Images (DuckDuckGo - no browser needed, fastest)
uv run browser.py google-image "keyword" -n 100 -o ~/Downloads  # Auto mode (DuckDuckGo first)
uv run browser.py google-image "keyword" -n 100 -o ~/Downloads -S duckduckgo  # DuckDuckGo only
uv run browser.py google-image "keyword" -n 100 -o ~/Downloads -S duckduckgo -s Large  # With size filter
uv run browser.py google-image "keyword" -n 20 -o ~/Downloads -s 4k  # 4K images (3840px+)
uv run browser.py google-image "keyword" -n 50 -o ~/Downloads -s fullhd  # FullHD images (1920px+)
uv run browser.py google-image "keyword" -a myaccount -n 50 -o ~/Downloads -S google  # Google mode (needs account)

# YouTube (with duration filtering)
uv run browser.py youtube-search "keyword" -n 10
uv run browser.py youtube-search "keyword" -n 5 -min 4 -max 20  # 4-20 min videos only
uv run browser.py youtube-download "https://youtube.com/watch?v=..." -o ~/Downloads -q 720p
uv run browser.py youtube-download "keyword" --search -n 5 -o ~/Downloads
uv run browser.py youtube-download "keyword" --search -n 5 -min 4 -max 20 -o ~/Downloads

# TikTok (uses Playwright for search, yt-dlp for download)
# Note: Use --no-headless for search - TikTok blocks headless browsers
uv run browser.py tiktok-login -a mytiktok  # Login and save session
uv run browser.py tiktok-login -a mytiktok -w 180  # Wait 3 min for login
uv run browser.py tiktok-search "keyword" -n 10 --no-headless
uv run browser.py tiktok-search "#dance" -n 5 --no-headless  # Search by hashtag
uv run browser.py tiktok-search "keyword" -n 10 -a mytiktok --no-headless  # With account
uv run browser.py tiktok-download "https://tiktok.com/@user/video/123" -o ~/Downloads
uv run browser.py tiktok-download "keyword" --search -n 5 -o ~/Downloads --no-headless
uv run browser.py tiktok-download "#funny" --search -n 10 -o ~/Downloads -p 3 --no-headless
```

## Architecture

### File Structure

- `.claude/skills/browser-use/scripts/` - Main code directory
  - `browser.py` - Main CLI entry point with all commands
  - `google_image.py` - GoogleImage dataclass for Google Images automation
  - `youtube.py` - YouTubeSearch and YouTubeDownload dataclasses for YouTube
  - `tiktok.py` - TikTokSearch and TikTokDownload dataclasses for TikTok
  - `pyproject.toml` - Dependencies (playwright, requests, yt-dlp)

### Key Patterns

**Dataclass CLI Pattern**: Feature modules (`google_image.py`, `youtube.py`, `tiktok.py`) use dataclasses with class variables for CLI metadata:
- `_cli_name`, `_cli_description` - Command registration
- `_cli_help`, `_cli_choices`, `_cli_short` - Argument configuration
- `add_to_parser()` - Auto-generates argparse from dataclass fields
- `from_args()` - Creates instance from parsed args

**Authentication**: Uses Chrome persistent profiles stored in `.auth/profiles/<account>/` with stealth flags to bypass automation detection. Commands accept `--account` to use saved sessions.

**Browser Context Pattern**: Most functions in `browser.py` follow this pattern:
```python
with sync_playwright() as p:
    if account:
        context = p.chromium.launch_persistent_context(user_data_dir, ...)
    else:
        browser = p.chromium.launch(...)
        context = browser.new_context(...)
    page = context.pages[0] if context.pages else context.new_page()
    # ... do work ...
    context.close()
```

### Dependencies

Python 3.14+, managed via uv:
- `playwright` - Browser automation
- `requests` - HTTP for image downloads
- `yt-dlp` - YouTube video downloading
- `duckduckgo-search` - Image search without browser
