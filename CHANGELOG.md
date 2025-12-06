# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.0 - 2025-12-06

### Added
- Browser automation CLI tool using Playwright
- Navigation, screenshots, and page interaction commands (`goto`, `screenshot`, `click`, `fill`)
- Data extraction commands (`text`, `links`, `extract`)
- Persistent Chrome profile authentication (`create-login`, `accounts`)
- Google Images automation with DuckDuckGo fallback (`google-image`)
- Image size filtering (4K, FullHD, Large, Medium, etc.)
- YouTube search and download functionality (`youtube-search`, `youtube-download`)
- YouTube duration filtering (`-min`, `-max` options)
- YouTube date filtering for search results
- TikTok search and download automation (`tiktok-search`, `tiktok-download`, `tiktok-login`)
- Hashtag search support for TikTok
- Claude plugin marketplace configuration

### Fixed
- Unicode characters now allowed in YouTube download filenames
