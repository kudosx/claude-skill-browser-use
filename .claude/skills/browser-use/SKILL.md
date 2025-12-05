---
name: browser-use
description: Browse and interact with websites using Playwright. Use when the user asks to visit a URL, scrape web content, take screenshots, fill forms, click buttons, or automate browser interactions.
allowed-tools: Bash, Read, Write, Edit
---

# Browser Use Skill

## Overview
This skill enables browsing websites and interacting with web pages using Playwright.

## Quick Start - Use Scripts

Run browser commands from the scripts folder:

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
```

## Authentication

Save and reuse login sessions across browser commands. Uses Chrome with stealth mode to bypass automation detection (works with Google, etc.):

```bash
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

## Python API Usage

**Navigate to a URL:**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    content = page.content()
    browser.close()
```

**Take a screenshot:**
```python
page.screenshot(path="screenshot.png")
```

**Click elements:**
```python
page.click("button#submit")
page.click("text=Click me")
page.click("a[href='/login']")
```

**Fill forms:**
```python
page.fill("input[name='username']", "user@example.com")
page.fill("input[name='password']", "password123")
page.click("button[type='submit']")
```

**Extract text content:**
```python
text = page.locator("h1").text_content()
all_links = page.locator("a").all_text_contents()
```

**Wait for elements:**
```python
page.wait_for_selector("div.loaded")
page.wait_for_load_state("networkidle")
```

### Async Usage
```python
import asyncio
from playwright.async_api import async_playwright

async def browse():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://example.com")
        content = await page.content()
        await browser.close()
        return content

result = asyncio.run(browse())
```

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
