# Browser Automation Script

A command-line tool for browser automation using Playwright with Chrome/Edge support and authentication persistence.

## Installation

Dependencies are managed via `pyproject.toml`. Run commands with:
```bash
cd .claude/skills/browser-use/scripts
uv run browser.py <command> [options]
```

## Commands

### Quick Reference

| Command | Description |
|---------|-------------|
| `create-login` | Save login session for reuse |
| `accounts` | List saved accounts |
| `goto` | Navigate to URL |
| `screenshot` | Take screenshot |
| `text` | Extract text content |
| `links` | Extract all links |
| `pdf` | Save page as PDF |
| `click` | Click an element |
| `fill` | Fill input field |
| `extract` | Extract attribute from elements |
| `download` | Download file by clicking |
| `upload` | Upload files |
| `download-images` | Download images from src |
| `download-from-gallery` | Download from click-to-reveal galleries |
| `google-image` | Search Google Images with filters |

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

### `click` - Click Element

Click an element on a page.

```bash
uv run browser.py click <url> <selector> [options]
```

**Options:**
- `--wait, -w` - Wait time after click (default: 1)
- `--screenshot, -s` - Save screenshot after click
- `--button, -b` - Mouse button: `left`, `right`, `middle`
- `--dblclick` - Double click
- `--shift` - Hold Shift while clicking
- `--ctrl` - Hold Control while clicking
- `--force` - Force click even if element is obscured
- `--no-headless` - Show browser window
- `--account, -a` - Use saved account

### `fill` - Fill Input Field

Fill an input field and optionally press a key.

```bash
uv run browser.py fill <url> <selector> <value> [options]
```

**Options:**
- `--press, -p` - Key to press after filling (e.g., `Enter`)
- `--screenshot, -s` - Save screenshot after action
- `--wait, -w` - Extra wait time after pressing key
- `--no-headless` - Show browser window
- `--account, -a` - Use saved account

**Example:**
```bash
uv run browser.py fill "https://google.com" "input[name=q]" "search term" --press Enter
```

### `extract` - Extract Attribute

Extract attribute value(s) from element(s).

```bash
uv run browser.py extract <url> <selector> [options]
```

**Options:**
- `--attr` - Attribute to extract (default: `src`). Use `text` for text content.
- `--all` - Extract from all matching elements
- `--no-headless` - Show browser window
- `--account, -a` - Use saved account

### `download` - Download File

Download a file by clicking an element that triggers download.

```bash
uv run browser.py download <url> <selector> [options]
```

**Options:**
- `--output-dir, -o` - Directory to save file (default: `.`)
- `--account, -a` - Use saved account
- `--timeout, -t` - Download timeout in ms (default: 30000)

### `upload` - Upload Files

Upload files to a page using a file input element.

```bash
uv run browser.py upload <url> <selector> <files...> [options]
```

**Options:**
- `--submit, -s` - CSS selector of submit button
- `--account, -a` - Use saved account

### `upload-chooser` - Upload via File Chooser

Upload files via file chooser dialog (for dynamic inputs).

```bash
uv run browser.py upload-chooser <url> <trigger> <files...> [options]
```

---

## Image Download Commands

### `download-images` - Download from src

Download images directly from `src` attribute.

```bash
uv run browser.py download-images <url> <selector> [options]
```

**Options:**
- `--num, -n` - Number of images (default: 5)
- `--output-dir, -o` - Directory to save images
- `--no-headless` - Show browser window
- `--account, -a` - Use saved account

### `download-from-gallery` - Download from Gallery (Optimized)

Download full-size images from click-to-reveal galleries. **Optimized for Google Images with 19x faster extraction.**

```bash
uv run browser.py download-from-gallery <url> <thumb_selector> <full_selector> [options]
```

**Arguments:**
- `url` - Gallery page URL
- `thumb_selector` - CSS selector for thumbnails
- `full_selector` - CSS selector for full-size image after click

**Options:**
- `--num, -n` - Number of images (default: 5)
- `--output-dir, -o` - Directory to save images
- `--no-headless` - Show browser window
- `--account, -a` - Use saved account

**Example - Google Images:**
```bash
# Download 100 large images of "keyword"
uv run browser.py download-from-gallery \
  "https://www.google.com/search?q=keyword&tbm=isch&tbs=isz:l" \
  "div[data-id] img" \
  "img[jsname='kn3ccd']" \
  -n 100 \
  -o ./downloads \
  -a myaccount
```

**Performance:**
| Method | Time for 20 images |
|--------|-------------------|
| Click-based | ~110 seconds |
| Fast regex extraction | ~5.7 seconds |

### `google-image` - Search Google Images

Search Google Images with size filters.

```bash
uv run browser.py google-image <keyword> <account> [options]
```

**Arguments:**
- `keyword` - Search keyword
- `account` - Account name for authentication

**Options:**
- `--size, -s` - Size filter: `Large`, `Medium`, `Icon` (default: Large)
- `--output, -o` - Screenshot output path
- `--no-headless` - Show browser window
- `--keep-open, -k` - Keep browser open for N seconds

**Example:**
```bash
uv run browser.py google-image "landscape wallpaper" myaccount --size Large -o results.png
```

---

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
