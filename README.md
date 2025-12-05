# Skill Browser Use

Claude skill for browsing websites and interacting with web pages using Playwright.

## Features

- Browser automation with Chrome/Edge support
- Authentication persistence (bypass automation detection)
- Screenshot, PDF export, text extraction
- Form filling, clicking, file upload/download
- **Image search & download** - DuckDuckGo (no browser, 12x faster) + Google fallback
- **YouTube search & download** - yt-dlp powered (no browser, 4x faster search)

## Example Prompts

### Common Usage

```
take a screenshot of https://example.com

extract all links from https://example.com

fill the search box on google.com with "hello world" and press Enter

download the PDF from https://example.com/document.pdf
```

### Image Search & Download

```
download 100 images of "landscape wallpaper"

download 50 large images of "nature photography"

download 20 4k images of "wallpaper" to ./downloads

download 50 fullhd images of "nature" to ./downloads

search and download 100 "beautiful city" images to ./downloads
```

Size options: `4k` (3840px+), `fullhd` (1920px+), `Large` (1000px+), `Medium` (400px+), `Icon`

### YouTube

```
search YouTube for "python tutorial" and get the top 10 results

download YouTube video https://youtube.com/watch?v=... in 720p

download audio only from YouTube video as mp3

search and download 5 "lofi music" videos from YouTube
```

## Documentation

- [SKILL.md](.claude/skills/browser-use/SKILL.md) - Main skill documentation
- [scripts/README.md](.claude/skills/browser-use/scripts/README.md) - Full command reference

### Tips & Best Practices

- [Google Images Optimization](.claude/skills/browser-use/references/tips/google-images-optimization.md) - DuckDuckGo + parallel downloads (12x faster)
- [YouTube Optimization](.claude/skills/browser-use/references/tips/youtube-optimization.md) - yt-dlp ytsearch (4x faster)
- [Browser Automation Best Practices](.claude/skills/browser-use/references/tips/browser-automation.md) - When to avoid browsers
