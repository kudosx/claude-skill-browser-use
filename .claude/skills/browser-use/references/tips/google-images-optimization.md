---
title: "Optimizing Google Images Scraping: From 110s to 5.7s (19x Faster)"
author: Kudosx Team
date: 2025-12-05
tags: [playwright, scraping, optimization, google-images]
---

# Optimizing Google Images Scraping: From 110s to 5.7s (19x Faster)

## Problem

The original approach to download images from Google Images was slow because it required:
1. Clicking each thumbnail individually
2. Waiting for the preview panel to load
3. Extracting the full-size image URL
4. Downloading sequentially

**Result:** ~5.5 seconds per image, 110 seconds for 20 images.

## Research Findings

After researching various approaches, I found that Google Images embeds full-size image URLs directly in the page source within `<script>` tags. The key insights came from:

- [ScrapingAnt - How to Scrape Google Images](https://scrapingant.com/blog/how-to-scrape-google-images)
- [GitHub Gist - Scraping full size images](https://gist.github.com/genekogan/ebd77196e4bf0705db51f86431099e57)
- [Stack Overflow - Regex extraction method](https://stackoverflow.com/questions/69597329/issue-requesting-when-scraping-images-from-google-using-src-tag-how-to-scrape)

### Key Insight

Google Images stores image data in `AF_initDataCallback` JavaScript functions. The full-size URLs are embedded in a format like:

```javascript
["https://example.com/full-size-image.jpg", 1920, 1080]
```

This means we can extract URLs using regex without clicking any thumbnails!

## Solution

### 1. Fast Regex Extraction

Instead of clicking thumbnails, parse the page source directly:

```python
def extract_urls_from_source(html: str, limit: int) -> list[str]:
    """Extract full-size image URLs from Google Images page source."""
    urls = []
    seen = set()

    # Pattern matches: ["https://example.com/image.jpg", width, height]
    pattern = r'\["(https?://[^"]+)",\s*\d+,\s*\d+\]'

    for match in re.finditer(pattern, html):
        url = match.group(1)

        # Skip thumbnails (hosted on Google's CDN)
        if "encrypted-tbn0.gstatic.com" in url:
            continue

        # Decode unicode escapes
        url = bytes(url, 'ascii').decode('unicode-escape')

        if url not in seen:
            seen.add(url)
            urls.append(url)
            if len(urls) >= limit:
                break

    return urls
```

### 2. Parallel Downloads

Use `ThreadPoolExecutor` to download multiple images simultaneously:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {
        executor.submit(download_single, (i, url)): i
        for i, url in enumerate(collected_urls)
    }

    for future in as_completed(futures):
        result = future.result()
        if result:
            downloaded_files.append(result)
```

### 3. Smart Scrolling

If initial extraction doesn't find enough URLs, scroll to load more:

```python
while len(collected_urls) < num_images and scroll_count < 10:
    page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
    time.sleep(0.5)
    html = page.content()
    new_urls = extract_urls_from_source(html, num_images * 2)
    # ... merge new URLs
```

### 4. Fallback to Click Method

If regex extraction fails (non-Google sites), fall back to clicking:

```python
if not collected_urls:
    print("Fallback: Clicking thumbnails...")
    # Original click-based method
```

## Results

| Metric | Before (Click) | After (Regex) | Improvement |
|--------|----------------|---------------|-------------|
| 20 images | 110 seconds | 5.7 seconds | **19x faster** |
| Per image | 5.5s | 0.3s | |
| Success rate | ~100% | ~80% | Trade-off |

### Why 80% Success Rate?

Some extracted URLs may fail to download due to:
- Hotlink protection on source websites
- Expired/rotated URLs
- Geographic restrictions

This is an acceptable trade-off given the massive speed improvement.

## Usage

```bash
# Fast mode (default) - uses regex extraction
uv run browser.py download-from-gallery \
  "https://www.google.com/search?q=keyword&tbm=isch&tbs=isz:l" \
  "div[data-id] img" \
  "img[jsname='kn3ccd']" \
  -n 100 \
  -o ./downloads \
  -a myaccount

# With size filter (Large)
uv run browser.py download-from-gallery \
  "https://www.google.com/search?q=keyword&tbm=isch&tbs=isz:l" \
  "div[data-id] img" \
  "img[jsname='kn3ccd']" \
  -n 100 \
  -o ./downloads \
  -a myaccount
```

## Technical Details

### URL Filter Patterns

| Pattern | Purpose |
|---------|---------|
| `encrypted-tbn0.gstatic.com` | Google's thumbnail CDN - skip |
| `data:image` | Base64 thumbnails - skip |
| `\["(https?://[^"]+)",\s*\d+,\s*\d+\]` | Full-size URL pattern |

### Size Filter URL Parameters

| Size | URL Parameter |
|------|---------------|
| Large | `tbs=isz:l` |
| Medium | `tbs=isz:m` |
| Icon | `tbs=isz:i` |

## Conclusion

By switching from a click-based approach to regex extraction from page source, we achieved a **19x speedup** in Google Images scraping. The key optimizations were:

1. **No clicking** - Extract URLs directly from HTML
2. **Parallel downloads** - 10 concurrent threads
3. **Smart fallback** - Click method for non-Google sites

This approach can be adapted for other image galleries that embed URLs in their page source.
