---
title: "YouTube Search & Download Optimization"
author: Kudosx Team
date: 2025-12-05
tags: [youtube, yt-dlp, optimization, performance, automation]
---

# YouTube Search & Download Optimization

Tài liệu này ghi lại các bài học từ quá trình tối ưu hóa tìm kiếm và tải video YouTube, dựa trên thực nghiệm thực tế.

## Tổng quan kết quả

| Metric | Trước | Sau | Cải thiện |
|--------|-------|-----|-----------|
| Search time | 6-10s | 1.5s | **4-5x** |
| Download (12 min video) | 12s | 8.5s | **30%** |
| Search + 5 downloads | 60s+ | 22s | **3x** |

---

## Phần 1: Tối ưu Search

### Vấn đề ban đầu

Sử dụng Playwright để tìm kiếm YouTube mất 6-10 giây:

```
22:38:41 - Searching YouTube: 'lofi music'
22:38:47 - Found 20 video elements          # 6 giây chỉ để tìm
```

**Nguyên nhân:**
- Khởi động browser (~2s)
- Load trang YouTube (~2-3s)
- Chờ JavaScript render (~1-2s)
- Parse DOM (~0.5s)

### Giải pháp: 3-Tier Fallback

```python
def search_youtube(keyword, num=10):
    # Tier 1: yt-dlp CLI (~1.5s) - Nhanh nhất
    results = _search_ytdlp_fast(keyword, num)
    if results:
        return results

    # Tier 2: youtube-search-python (~2-3s)
    results = _search_library(keyword, num)
    if results:
        return results

    # Tier 3: Playwright browser (~6-10s) - Fallback
    return _search_browser(keyword, num)
```

### Tier 1: yt-dlp ytsearch (Khuyên dùng)

**Tại sao nhanh:**
- Không cần browser
- `--flat-playlist` bỏ qua full extraction
- Trả về JSON trực tiếp

```python
def _search_ytdlp_fast(keyword, num=10, min_duration=None, max_duration=None):
    fetch_num = num * 5 if (min_duration or max_duration) else num

    cmd = [
        "yt-dlp",
        f"ytsearch{fetch_num}:{keyword}",
        "--dump-json",
        "--flat-playlist",      # Key: Bỏ qua full extraction
        "--skip-download",
        "--quiet",
        "--no-warnings",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    # Parse JSON lines
    videos = []
    for line in result.stdout.strip().split("\n"):
        v = json.loads(line)
        # Filter by duration if needed
        duration_sec = v.get("duration")
        if duration_sec and min_duration and duration_sec/60 < min_duration:
            continue
        if duration_sec and max_duration and duration_sec/60 > max_duration:
            continue
        videos.append({
            "url": f"https://www.youtube.com/watch?v={v['id']}",
            "title": v.get("title", ""),
            "duration": format_duration(duration_sec),
        })
        if len(videos) >= num:
            break
    return videos
```

**Kết quả thực nghiệm:**

```
23:27:39 - Starting search for: 'claude code'
23:27:40 - yt-dlp fast search found 5 videos    # 1 giây!
```

### Benchmark Search

| Method | Time | Browser | Reliability |
|--------|------|---------|-------------|
| yt-dlp + flat-playlist | 1.5s | No | High |
| youtube-search-python | 2-3s | No | Medium |
| Playwright | 6-10s | Yes | Highest |

---

## Phần 2: Tối ưu Download

### Vấn đề: aria2c KHÔNG nhanh hơn cho YouTube

**Thực nghiệm:**

```
# Test 1: Native yt-dlp
23:32:33 - Downloading...
23:32:41 - Downloaded              # 8 giây

# Test 2: aria2c
23:31:49 - Downloading...
23:32:18 - Downloaded              # 29 giây (!)
```

**Tại sao aria2c chậm hơn:**
- YouTube dùng DASH streams (video + audio riêng)
- aria2c download riêng rẽ, sau đó merge
- Native yt-dlp xử lý DASH tốt hơn

**Kết luận:** Dùng native yt-dlp với `-N` concurrent fragments.

### Cấu hình tối ưu

```python
cmd = [
    "yt-dlp",
    "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best",
    "-N", "8",                  # 8 concurrent fragments
    "--buffer-size", "64K",    # Tăng buffer
    "--http-chunk-size", "10M", # Chunk lớn hơn
    "--no-mtime",              # Bỏ set modification time
    "--no-check-certificates", # Bỏ verify SSL
    "-o", "%(title)s.%(ext)s",
    url
]
```

### Benchmark Download

**Video ngắn (2 phút):**
```
23:31:10 - Downloading Python_in_100_Seconds
23:31:18 - Downloaded              # 8 giây
```

**Video dài (12 phút):**
```
23:33:21 - Downloading How_I_use_Claude_Code
23:33:29 - Downloaded              # 8 giây
```

**So sánh concurrent fragments:**

| -N value | 2 min video | 12 min video |
|----------|-------------|--------------|
| 4 (default) | 8s | 12s |
| 8 | 7.5s | 8.5s |
| 16 | 7.4s | 8.5s |

**Kết luận:** `-N 8` là sweet spot, tăng thêm không cải thiện đáng kể.

---

## Phần 3: Parallel Downloads

### Vấn đề ban đầu

Download tuần tự:
```
22:50:04 - Downloading video 1...
22:50:13 - Downloaded
22:50:13 - Downloading video 2...
22:50:23 - Downloaded
# 5 videos = 57 giây
```

### Giải pháp: ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_parallel(urls, max_workers=3):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_single, url): url for url in urls}
        for future in as_completed(futures):
            result = future.result()
```

**Kết quả:**
```
23:08:48 - Downloading 5 video(s) with 3 parallel workers...
23:08:48 - Downloading: video1, video2, video3 (cùng lúc)
23:08:57 - Downloaded: video1
23:09:00 - Downloaded: video2, video3
23:09:06 - Downloaded: video4
23:09:10 - Downloaded: video5
23:09:10 - Downloaded 5 file(s)     # 22 giây (thay vì 57 giây)
```

**Tại sao max_workers=3:**
- Quá nhiều workers → Rate limiting
- 3 workers cân bằng tốc độ và stability

---

## Phần 4: Duration Filter

### Cách 1: URL Parameter (Nhanh nhưng hạn chế)

```python
# YouTube duration filters
# Short (< 4 min): sp=EgIYAQ%3D%3D
# Medium (4-20 min): sp=EgIYAw%3D%3D
# Long (> 20 min): sp=EgIYAg%3D%3D

search_url = f"https://youtube.com/results?search_query={keyword}"
if min_duration >= 4 and max_duration <= 20:
    search_url += "&sp=EgIYAw%3D%3D"
```

**Hạn chế:** Chỉ có 3 preset, không flexible.

### Cách 2: Filter trong code (Flexible)

```python
def filter_by_duration(videos, min_dur, max_dur):
    filtered = []
    for v in videos:
        duration_min = parse_duration(v["duration"])
        if min_dur and duration_min < min_dur:
            continue
        if max_dur and duration_min > max_dur:
            continue
        filtered.append(v)
    return filtered
```

**Thực nghiệm:**
```
23:08:48 - [1/5] 19.0 min: lofi songs for slow days
23:08:48 - [2/5] 18.6 min: ALBUM CHILL WITH VICKY NHUNG
23:08:48 - [3/5] 14.6 min: If Wiz Khalifa ft Post Malone...
```

---

## Phần 5: Các lỗi thường gặp

### Lỗi 1: Duration filter với string

```
23:27:47 - WARNING - yt-dlp search failed: '<' not supported between instances of 'float' and 'str'
```

**Nguyên nhân:** CLI truyền duration là string, không convert.

**Fix:**
```python
min_dur = int(min_duration) if min_duration else None
max_dur = int(max_duration) if max_duration else None
```

### Lỗi 2: Timeout click filter button

```
22:55:18 - WARNING - Could not apply duration filter: Locator.click: Timeout 2000ms exceeded.
```

**Nguyên nhân:** YouTube UI thay đổi.

**Fix:** Dùng URL parameter thay vì click UI.

### Lỗi 3: youtube-search-python lỗi proxies

```
23:27:47 - WARNING - Fast search failed: post() got an unexpected keyword argument 'proxies'
```

**Nguyên nhân:** Library version conflict.

**Fix:** Fallback xuống tier tiếp theo.

---

## CLI Commands

```bash
# Search nhanh (dùng yt-dlp)
uv run browser.py youtube-search "keyword" -n 10

# Search với duration filter
uv run browser.py youtube-search "keyword" -n 5 -min 4 -max 20

# Download trực tiếp
uv run browser.py youtube-download "URL" -o ./downloads -q 720p

# Search + download
uv run browser.py youtube-download "keyword" --search -n 5 -o ./downloads

# Full options
uv run browser.py youtube-download "lofi music" \
    --search \
    -n 5 \
    -min 4 -max 20 \
    -o ./downloads \
    -q 720p \
    -N 8
```

---

## Tổng kết Best Practices

### Search
1. **Ưu tiên yt-dlp ytsearch** với `--flat-playlist`
2. **Fallback strategy** để đảm bảo reliability
3. **Fetch nhiều hơn cần** khi có duration filter (5x)

### Download
1. **KHÔNG dùng aria2c** cho YouTube DASH streams
2. **Dùng `-N 8`** concurrent fragments
3. **Parallel downloads** với 3 workers
4. **Buffer 64K, chunk 10M** để tối ưu throughput

### Error Handling
1. **Convert types** từ CLI (string → int)
2. **Fallback** khi method nhanh fail
3. **Timeout hợp lý** (30s search, 600s download)

---

## References

- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [yt-dlp Speed Methods](https://github.com/yt-dlp/yt-dlp/issues/7987)
- [yt-dlp Format Selection](https://github.com/yt-dlp/yt-dlp#format-selection)
