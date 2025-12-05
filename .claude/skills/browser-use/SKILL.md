---
name: browser-use
description: Browse and interact with websites using Playwright. Use when the user asks to visit a URL, scrape web content, take screenshots, fill forms, click buttons, or automate browser interactions.
allowed-tools: Bash, Read, Write, Edit
---

# Browser Use Skill

## Overview
This skill enables browsing websites and interacting with web pages using Playwright.

## Quick Start - Use Scripts

**Important:** All `uv run` commands must be executed from the scripts folder (not the project root):

```bash
cd .claude/skills/browser-use/scripts

# Navigate to a URL and get content
uv run browser.py goto https://example.com

# Take a screenshot
uv run browser.py screenshot https://example.com -o screenshot.png

# Extract text from a page
uv run browser.py text https://example.com --selector "h1"

# Get all links from a page
uv run browser.py links https://example.com

# Save page as PDF
uv run browser.py pdf https://example.com -o page.pdf

# Download a file by clicking a download link
uv run browser.py download https://example.com/downloads "a.download-btn" -o ./downloads

# Upload file(s) to a page
uv run browser.py upload https://example.com/upload "input[type=file]" myfile.pdf
uv run browser.py upload https://example.com/upload "input[type=file]" file1.txt file2.txt --submit "button[type=submit]"

# Upload via file chooser dialog (for dynamic inputs)
uv run browser.py upload-chooser https://example.com/upload "button.upload-trigger" myfile.pdf

# Click an element
uv run browser.py click https://example.com "button.submit"

# Fill an input field and press Enter
uv run browser.py fill https://google.com "input[name=q]" "search term" --press Enter

# Extract attribute from elements
uv run browser.py extract https://example.com "img" --attr src --all
```

## Image Download Commands

Download images from websites with optimized performance:

```bash
cd .claude/skills/browser-use/scripts

# Download images directly from src attribute
uv run browser.py download-images https://example.com "img.gallery" -n 10 -o ./images

# Download from Google Images (19x faster with regex extraction)
uv run browser.py download-from-gallery \
  "https://www.google.com/search?q=keyword&tbm=isch&tbs=isz:l" \
  "div[data-id] img" \
  "img[jsname='kn3ccd']" \
  -n 100 \
  -o ./downloads \
  -a myaccount

# Search Google Images with size filter
uv run browser.py google-image "landscape wallpaper" -n 50 -o ./downloads -s Large

# Download 4K images (3840px+ minimum)
uv run browser.py google-image "wallpaper" -n 20 -o ./downloads -s 4k

# Download FullHD images (1920px+ minimum)
uv run browser.py google-image "wallpaper" -n 50 -o ./downloads -s fullhd
```

### Google Images Size Filters
CLI size options (filters by minimum dimension):
- `-s 4k` - 3840px minimum (4K resolution)
- `-s fullhd` - 1920px minimum (Full HD)
- `-s Large` - 1000px minimum
- `-s Medium` - 400px minimum
- `-s Icon` - No minimum

Google URL params (used internally):
- `tbs=isz:l` - Large images
- `tbs=isz:m` - Medium images
- `tbs=isz:i` - Icon size

## YouTube Commands

Search and download YouTube videos with duration filtering:

```bash
cd .claude/skills/browser-use/scripts

# Search YouTube and get video URLs (returns JSON)
uv run browser.py youtube-search "python tutorial" -n 10
uv run browser.py youtube-search "lofi music" -n 5 -o results.json -s screenshot.png

# Search with duration filter (4-20 minutes)
uv run browser.py youtube-search "lofi music" -n 5 -min 4 -max 20

# Download a single video by URL
uv run browser.py youtube-download "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o ./downloads

# Download with quality options
uv run browser.py youtube-download "https://youtube.com/watch?v=..." -q 720p -o ./downloads
uv run browser.py youtube-download "https://youtube.com/watch?v=..." -q 1080p -o ./downloads

# Download audio only (mp3)
uv run browser.py youtube-download "https://youtube.com/watch?v=..." -a -o ./music

# Search and download in one command
uv run browser.py youtube-download "lofi hip hop" --search -o ./downloads
uv run browser.py youtube-download "python tutorial" --search -n 3 -o ./downloads

# Search and download with duration filter (4-20 min videos only)
uv run browser.py youtube-download "lofi music" --search -n 5 -min 4 -max 20 -o ./downloads
```

### YouTube Duration Filters
- `-min N` - Minimum duration in minutes
- `-max N` - Maximum duration in minutes
- Filters use YouTube URL parameters for speed, with Python-side validation as backup

### YouTube Quality Options
- `best` - Best available quality (default)
- `1080p` - 1080p or lower
- `720p` - 720p or lower
- `480p` - 480p or lower
- `360p` - 360p or lower
- `audio` - Best audio only

### YouTube Search Output Format
```json
[
  {
    "url": "https://www.youtube.com/watch?v=...",
    "title": "Video Title",
    "channel": "Channel Name",
    "duration": "10:30",
    "views": "1.2M views"
  }
]
```

## Authentication

Save and reuse login sessions across browser commands. Uses Chrome with stealth mode to bypass automation detection (works with Google, etc.):

```bash
# Run from scripts folder
cd .claude/skills/browser-use/scripts

# Step 1: Create a login session (opens Chrome for manual login)
# Browser will open maximized - login manually then close the browser
uv run browser.py create-login https://gemini.google.com/app --account myaccount

# Options:
#   --wait, -w    Seconds to wait for login (default: 120)
#   --channel, -c Browser: chrome, msedge, chromium (default: chrome)

# Step 2: List saved accounts
uv run browser.py accounts

# Step 3: Use saved account with any command
uv run browser.py goto https://gemini.google.com/app --account myaccount
uv run browser.py screenshot https://gemini.google.com/app -o gemini.png --account myaccount
```

Authentication is stored in `.auth/profiles/` directory (browser profile) and `.auth/*.json` (cookies). Both are automatically added to .gitignore.


### Best Practices
- Use `headless=True` for automation tasks
- Use `headless=False` when debugging or when visual confirmation is needed
- Always close the browser after use
- Use specific selectors (id, data-testid) over generic ones when possible
- Add appropriate waits for dynamic content
- Handle timeouts gracefully with try/except blocks

### Common Selectors
- By ID: `#element-id`
- By class: `.class-name`
- By text: `text=Button Text`
- By role: `role=button[name="Submit"]`
- By CSS: `div.container > p.content`
- By XPath: `xpath=//div[@class='item']`
