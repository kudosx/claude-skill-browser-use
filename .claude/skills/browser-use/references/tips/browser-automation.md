---
title: "Web Automation Best Practices: Speed, Reliability & Scale"
author: Kudosx Team
date: 2025-12-05
tags: [automation, scraping, optimization, yt-dlp, playwright, requests, best-practices]
---

# Web Automation Best Practices

## The Golden Rule

**The fastest automation is no browser at all.**

Before writing any code, ask: What's the simplest tool for this job?

```
Speed & Reliability Hierarchy:

1. Official APIs        (~100ms)  - Best: rate limits, stable, documented
2. CLI Tools            (~1-2s)   - yt-dlp, curl, wget - battle-tested
3. HTTP + Regex/JSON    (~1-3s)   - requests + parsing, no JS needed
4. Headless Browser     (~5-10s)  - Playwright, Puppeteer, Selenium
5. Headed Browser       (~10-20s) - Visible browser, debugging only
```

---

## Tool Selection Guide

### When to Use What

| Task | Best Tool | Why |
|------|-----------|-----|
| YouTube search/download | `yt-dlp` | Purpose-built, handles all edge cases |
| Image search | `duckduckgo-search` | No browser, no API key, ~2s for 100 images |
| TikTok download | `yt-dlp` + cookies | Direct download, handles watermarks |
| TikTok search | Playwright (headful) | Headless is blocked by TikTok |
| API with JSON response | `requests` | Simple, fast, no overhead |
| Static HTML scraping | `requests` + `BeautifulSoup` | No JS needed |
| JS-rendered content | Playwright/Puppeteer | Need browser engine |
| Form with CSRF/cookies | `requests.Session` | Maintains state |
| Complex login flows | Playwright + persistent profile | Handles OAuth, CAPTCHA |
| File downloads | `aria2c`, `wget`, `curl` | Optimized for downloads |
| Image galleries | `requests` + threading | Parallel HTTP requests |

### Real Example: YouTube Search

```python
# SLOWEST: Selenium (~15-20s)
driver = webdriver.Chrome()
driver.get(f"https://youtube.com/results?search_query={keyword}")
# ... wait, scroll, parse DOM

# SLOW: Playwright (~6-10s)
page.goto(f"https://youtube.com/results?search_query={keyword}")
# ... wait for JS, extract data

# FAST: youtube-search-python (~2-3s)
from youtubesearchpython import VideosSearch
search = VideosSearch(keyword, limit=10)
results = search.result()

# FASTEST: yt-dlp CLI (~1.5s)
cmd = ["yt-dlp", f"ytsearch{num}:{keyword}", "--dump-json", "--flat-playlist"]
result = subprocess.run(cmd, capture_output=True, text=True)
```

**Lesson:** yt-dlp already solved YouTube scraping. Don't reinvent the wheel.

### Real Example: Image Search

```python
# SLOWEST: Click thumbnails (~110s for 20 images)
for thumb in page.locator("img[data-src]").all():
    thumb.click()
    # ... wait for full image, extract URL

# SLOW: Playwright + regex (~15s for 100 images)
page.goto(f"https://google.com/search?q={keyword}&tbm=isch")
html = page.content()
urls = re.findall(r'\["(https?://[^"]+)",\s*\d+,\s*\d+\]', html)

# FASTEST: DuckDuckGo library (~2-3s for 100 images, NO BROWSER)
from duckduckgo_search import DDGS

with DDGS() as ddgs:
    results = list(ddgs.images(keywords=keyword, max_results=100))
    urls = [r["image"] for r in results]
```

**Lesson:** DuckDuckGo provides free image search API. No browser, no API key needed.

### Real Example: TikTok Search & Download

```python
# WILL NOT WORK: Headless mode (TikTok blocks it)
browser = p.chromium.launch(headless=True)  # BLOCKED!
page.goto("https://tiktok.com/search?q=...")
# Error: Captcha detected or page blocked

# WORKS: Headful mode with stealth flags
browser = p.chromium.launch(
    headless=False,  # REQUIRED for TikTok
    args=[
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ]
)

# FASTEST: yt-dlp for downloads (~2-3s per video)
cmd = ["yt-dlp", "--cookies-from-browser", "chrome", url]
result = subprocess.run(cmd, capture_output=True)
```

**Lesson:** TikTok uses aggressive bot detection with a custom JS VM. Headless browsers are immediately blocked. Always use headful mode with stealth flags, and prefer yt-dlp with cookies for downloads.

---

## Architecture Patterns

### 1. Tiered Fallback Strategy

Never rely on a single method. Build systems that degrade gracefully:

```python
def search_youtube(keyword: str, num: int = 10) -> list[dict]:
    """3-tier fallback: CLI → Library → Browser"""

    # Tier 1: yt-dlp CLI (fastest, most reliable)
    results = _search_via_ytdlp(keyword, num)
    if results:
        return results

    # Tier 2: Python library (fast, no browser)
    results = _search_via_library(keyword, num)
    if results:
        return results

    # Tier 3: Browser automation (slowest, handles edge cases)
    logger.info("Fast methods failed, using browser fallback")
    return _search_via_browser(keyword, num)
```

**Benefits:**
- 95% of requests use the fast path
- Handles API changes gracefully
- No single point of failure
- Easy to add new tiers

### 2. Parallel Execution

Use the right parallelism for each task:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

# For I/O-bound tasks (downloads, HTTP requests)
def download_parallel(urls: list[str], max_workers: int = 3) -> list[str]:
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_single, url): url for url in urls}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    return results
```

**Worker Guidelines:**
- Downloads: 3 workers (avoid rate limiting)
- API calls: 5-10 workers
- Image downloads: 10-20 workers (lightweight)

### 3. When Browser IS Needed

Sometimes only a browser will work:

```python
# Complex scenarios requiring browser:
# - OAuth login flows
# - CAPTCHA solving
# - Heavy JS frameworks (React SPAs)
# - WebSocket connections
# - Cookie consent dialogs
# - TikTok (requires headful mode due to bot detection)

def browser_automation_pattern(headless=True):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 ...",
        )
        page = context.new_page()

        try:
            yield page
        finally:
            context.close()
            browser.close()
```

### 4. Platform-Specific Considerations

| Platform | Headless OK? | Key Requirement |
|----------|--------------|-----------------|
| YouTube | Yes | Use yt-dlp instead of browser |
| Google Images | Yes | Regex extraction from HTML |
| DuckDuckGo | N/A | No browser needed (HTTP API) |
| TikTok | **NO** | Must use headful + stealth flags |
| Instagram | No | Requires login + anti-detection |
| Twitter/X | Partial | API preferred, browser for auth |

---

## Performance Optimization

### 1. Batch Operations

**Problem:** Multiple API/DOM calls have overhead.

```python
# SLOW: 30 separate calls
for item in page.locator(".item").all():
    title = item.locator(".title").text_content()
    price = item.locator(".price").text_content()

# FAST: 1 JavaScript call
data = page.evaluate("""
    () => [...document.querySelectorAll('.item')].map(el => ({
        title: el.querySelector('.title')?.textContent,
        price: el.querySelector('.price')?.textContent,
    }))
""")
```

**Result:** 10-30x faster for DOM extraction.

### 2. Skip What You Don't Need

```python
# Block images, fonts, CSS when only scraping text
async def route_handler(route):
    if route.request.resource_type in ["image", "font", "stylesheet"]:
        await route.abort()
    else:
        await route.continue_()

await page.route("**/*", route_handler)
```

### 3. Download Optimization

For yt-dlp and similar tools:

```bash
# Optimized yt-dlp settings
yt-dlp \
  -N 8 \                    # 8 concurrent fragment downloads
  --buffer-size 64K \       # Larger buffer
  --http-chunk-size 10M \   # Reduce request overhead
  --no-mtime \              # Skip file time modification
  "$URL"
```

**Important:** aria2c is NOT faster for YouTube/DASH streams:
- YouTube uses separate video + audio streams
- Native yt-dlp handles merging better
- aria2c is only faster for direct HTTP downloads

### 4. Caching

Don't re-fetch what you already have:

```python
import hashlib
from pathlib import Path

def cached_fetch(url: str, cache_dir: Path = Path(".cache")) -> str:
    cache_dir.mkdir(exist_ok=True)
    cache_key = hashlib.md5(url.encode()).hexdigest()
    cache_file = cache_dir / f"{cache_key}.json"

    if cache_file.exists():
        return cache_file.read_text()

    response = requests.get(url)
    cache_file.write_text(response.text)
    return response.text
```

---

## Reliability Patterns

### 1. Retry with Exponential Backoff

```python
import time
import random

def retry_with_backoff(func, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s")
            time.sleep(delay)
```

### 2. Graceful Error Handling

```python
def safe_extract(extractor_func, default=None):
    """Wrap extraction in try/except, return default on failure."""
    try:
        result = extractor_func()
        return result if result else default
    except Exception:
        return default

# Usage
title = safe_extract(lambda: page.locator("h1").text_content(), default="Unknown")
```

### 3. Handle Common Obstacles

```python
def handle_cookie_consent(page):
    """Handle GDPR cookie dialogs."""
    selectors = [
        "button:has-text('Accept all')",
        "button:has-text('Accept')",
        "[data-testid='cookie-accept']",
        "#onetrust-accept-btn-handler",
    ]
    for selector in selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=2000):
                btn.click()
                time.sleep(0.5)
                return True
        except:
            continue
    return False
```

---

## Anti-Detection (When Needed)

### 1. Rotate User Agents

```python
import random

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36...",
]

headers = {"User-Agent": random.choice(USER_AGENTS)}
```

### 2. Add Human-like Delays

```python
import random
import time

def human_delay(min_sec=0.5, max_sec=2.0):
    """Random delay to mimic human behavior."""
    time.sleep(random.uniform(min_sec, max_sec))
```

### 3. Use Persistent Profiles

For sites requiring login:

```python
# Save session across runs
context = browser.launch_persistent_context(
    user_data_dir="./profiles/account_name",
    headless=True,
)
```

---

## CLI Tool Integration

### duckduckgo-search (Image Search)

```bash
# Install
pip install duckduckgo-search
# or
uv add duckduckgo-search
```

```python
from duckduckgo_search import DDGS

# Basic search
with DDGS() as ddgs:
    results = list(ddgs.images(
        keywords="nature wallpaper",
        max_results=100,
    ))

# With filters
with DDGS() as ddgs:
    results = list(ddgs.images(
        keywords="landscape",
        region="wt-wt",        # Worldwide
        safesearch="off",
        size="Large",          # Large, Medium, Small
        max_results=50,
    ))
```

### yt-dlp (Video/Audio)

```bash
# Search without downloading
yt-dlp "ytsearch10:python tutorial" --dump-json --flat-playlist

# Download with quality selection
yt-dlp -f "bestvideo[height<=720]+bestaudio" --merge-output-format mp4 "$URL"

# Audio only
yt-dlp -x --audio-format mp3 "$URL"
```

### curl/wget (HTTP)

```bash
# Simple download
curl -O "$URL"

# With headers
curl -H "Authorization: Bearer $TOKEN" "$URL"

# Resume interrupted download
wget -c "$URL"
```

### aria2c (Parallel Downloads)

```bash
# Multi-connection download (for direct HTTP, NOT for YouTube)
aria2c -x 16 -s 16 "$URL"

# Download from file list
aria2c -i urls.txt -j 5
```

---

## Quick Reference

### Speed Comparison

| Method | YouTube Search | Image Search | Image Download | API Call |
|--------|---------------|--------------|----------------|----------|
| CLI (yt-dlp) | 1.5s | N/A | 0.5s | 0.3s |
| DuckDuckGo lib | N/A | 2-3s | N/A | N/A |
| Python requests | N/A | N/A | 1s | 0.5s |
| Playwright headless | 6-10s | 15s | 3s | 2s |
| Selenium | 10-15s | 20s+ | 5s | 3s |

### Decision Tree

```
Need to automate web task?
│
├─ Has official API? → Use API
│
├─ CLI tool exists? (yt-dlp, curl) → Use CLI
│
├─ Static HTML? → requests + BeautifulSoup
│
├─ Need JS rendering?
│   ├─ TikTok/Instagram? → Playwright (HEADFUL + stealth)
│   └─ Other sites? → Playwright (headless)
│
└─ Complex interaction? → Playwright + persistent profile
```

### Best Practices Checklist

- [ ] Use simplest tool possible (API > CLI > HTTP > Browser)
- [ ] Implement tiered fallback strategy
- [ ] Batch operations to reduce overhead
- [ ] Add retry logic with backoff
- [ ] Cache responses when appropriate
- [ ] Respect rate limits
- [ ] Handle errors gracefully
- [ ] Log actions for debugging
- [ ] Clean up resources (close browsers, sessions)
- [ ] Check platform-specific requirements (headless vs headful)
- [ ] Use stealth flags for anti-detection platforms (TikTok, Instagram)

---

## References

- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [requests Documentation](https://docs.python-requests.org/)
- [aria2 Manual](https://aria2.github.io/manual/en/html/)
- [Web Scraping Best Practices 2025](https://www.scraperapi.com/blog/web-scraping-best-practices/)
- [How to Scrape TikTok - ScrapingBee](https://www.scrapingbee.com/blog/how-to-scrape-tiktok/)
- [TikTok Bot Detection Analysis - Castle.io](https://blog.castle.io/what-tiktoks-virtual-machine-tells-us-about-modern-bot-defenses/)
- [PyTok - Playwright TikTok Scraper](https://github.com/networkdynamics/pytok)
