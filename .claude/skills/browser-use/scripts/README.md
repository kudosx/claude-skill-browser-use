# Browser Automation Script

A command-line tool for browser automation using Playwright with Chrome/Edge support and authentication persistence.

## Installation

Dependencies are managed via `pyproject.toml`. Run commands with:
```bash
uv run browser.py <command> [options]
```

## Commands

### `create-login` - Save Login Session

Opens a browser for manual login and saves the session for later use. Uses Chrome with stealth mode to bypass automation detection (works with Google, etc.).

```bash
uv run browser.py create-login <url> --account <name> [options]
```

**Arguments:**
- `url` - URL to open for login
- `--account, -a` - Account name to save as (required)
- `--wait, -w` - Seconds to wait for login (default: 120)
- `--channel, -c` - Browser: `chrome`, `msedge`, `chromium` (default: chrome)

**Example:**
```bash
uv run browser.py create-login https://gemini.google.com/app --account google --wait 180
```

### `accounts` - List Saved Accounts

```bash
uv run browser.py accounts
```

### `goto` - Navigate to URL

Navigate to a URL and return page content.

```bash
uv run browser.py goto <url> [options]
```

**Options:**
- `--screenshot, -s` - Save screenshot to file
- `--no-headless` - Show browser window
- `--wait, -w` - Extra wait time in seconds after page load
- `--account, -a` - Use saved account for authentication

**Example:**
```bash
uv run browser.py goto https://gemini.google.com/app --account google --screenshot output.png
```

### `screenshot` - Take Screenshot

```bash
uv run browser.py screenshot <url> [options]
```

**Options:**
- `--output, -o` - Output file (default: screenshot.png)
- `--no-full-page` - Capture viewport only instead of full page
- `--wait, -w` - Extra wait time in seconds after page load
- `--account, -a` - Use saved account for authentication

**Example:**
```bash
uv run browser.py screenshot https://example.com -o page.png --wait 2
```

### `text` - Extract Text

Extract text content from a page using CSS selector.

```bash
uv run browser.py text <url> [options]
```

**Options:**
- `--selector, -s` - CSS selector (default: body)

**Example:**
```bash
uv run browser.py text https://example.com --selector "h1"
```

### `links` - Extract Links

Extract all links from a page as JSON.

```bash
uv run browser.py links <url>
```

### `pdf` - Save as PDF

Save a page as PDF.

```bash
uv run browser.py pdf <url> [options]
```

**Options:**
- `--output, -o` - Output file (default: page.pdf)

## Authentication

Authentication data is stored in:
- `.auth/profiles/<account>/` - Browser profile (cookies, localStorage, etc.)
- `.auth/<account>.json` - Exported cookies

Both directories are automatically added to `.gitignore`.

### How it works

1. `create-login` opens Chrome with stealth flags to bypass automation detection
2. User logs in manually
3. Browser profile is saved to `.auth/profiles/<account>/`
4. Other commands use `launch_persistent_context` to reuse the saved profile

### Stealth Features

The script uses several techniques to avoid automation detection:
- Uses real Chrome browser (`channel="chrome"`)
- Disables automation flags (`--disable-blink-features=AutomationControlled`)
- Removes `--enable-automation` flag
- Uses persistent browser profile

## Python API

Functions can also be imported and used programmatically:

```python
from browser import goto, screenshot, create_login

# Navigate with authentication
content = goto("https://gemini.google.com/app", account="google")

# Take screenshot
screenshot("https://example.com", output="page.png", wait=2)
```
