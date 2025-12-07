# Skill Browser Use

Claude skill for browser automation, web scraping, and media downloading.

## Features

- **Manual browsing** - Open browser for user interaction with `open` command
- **Headless automation** - Screenshot, PDF export, text extraction with `auto` command
- Authentication persistence (shared across projects in `~/.auth/`)
- Session recording with screenshots and traces
- Form filling, clicking, file upload/download
- **Image search & download** - DuckDuckGo (no browser, 12x faster) + Google fallback
- **YouTube search & download** - yt-dlp powered (no browser, 4x faster search) with date filtering
- **TikTok search & download** - Playwright search + yt-dlp download

## Example Prompts

### Web Scraping & Screenshots

```
screenshot dantri.com and extract top news headlines

take a full-page screenshot of https://github.com/trending

extract all product prices from https://amazon.com/deals

get the text content of all h2 headings from https://news.ycombinator.com

save https://arxiv.org/pdf/2508.08322v1 as PDF
```

### Image Search & Download

```
download 100 "sunset beach" wallpapers in 4K resolution

download 50 "minimalist desk setup" images for inspiration

get 30 "cute dog" photos in fullhd quality

download "vintage car" images from last month
```

Size options: `4k` (3840px+), `fullhd` (1920px+), `Large` (1000px+), `Medium` (400px+)

### YouTube

```
find top 10 "machine learning tutorial" videos under 20 minutes

download the audio from this YouTube video as mp3

search YouTube for "cooking recipes" videos uploaded this week

download 5 "lo-fi beats" videos between 30-60 minutes for studying

find "react tutorial" videos from 2024
```

### TikTok

```
search TikTok for trending "#lifehacks" videos

download this TikTok video: https://tiktok.com/@user/video/123

find and download 10 "#productivity" TikTok videos
```

Note: TikTok requires `--no-headless` mode due to bot detection.

## Documentation

- [SKILL.md](.claude/skills/browser-use/SKILL.md) - Main skill documentation
- [scripts/README.md](.claude/skills/browser-use/scripts/README.md) - Full command reference

### Tips & Best Practices

- [Authentication & Sessions](.claude/skills/browser-use/references/tips/authentication-sessions.md) - Login persistence, shared auth
- [Browser Manual](.claude/skills/browser-use/references/tips/browser-manual.md) - Manual browsing with `open` command
- [Web Scraping](.claude/skills/browser-use/references/tips/web-scraping.md) - Data extraction patterns
- [Browser Automation](.claude/skills/browser-use/references/tips/browser-automation.md) - When to avoid browsers
- [Google Images Optimization](.claude/skills/browser-use/references/tips/google-images-optimization.md) - DuckDuckGo + parallel downloads (12x faster)
- [YouTube Optimization](.claude/skills/browser-use/references/tips/youtube-optimization.md) - yt-dlp ytsearch (4x faster)
- [TikTok Optimization](.claude/skills/browser-use/references/tips/tiktok-optimization.md) - Anti-detection and best practices
