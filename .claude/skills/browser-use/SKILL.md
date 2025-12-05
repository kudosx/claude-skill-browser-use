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
uv run browser.py google-image "landscape wallpaper" myaccount --size Large -o results.png
```

### Google Images Size Filters
- `tbs=isz:l` - Large images
- `tbs=isz:m` - Medium images
- `tbs=isz:i` - Icon size

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
