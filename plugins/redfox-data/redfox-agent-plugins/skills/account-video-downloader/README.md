# Account Video  Downloader — Multi-Platform Account Video Downloader

**English** | [简体中文](./README.zh.md)

---

## Overview

A multi-platform account video downloader supporting **Douyin**, **Kuaishou**, **Bilibili**, and **YouTube**. Provide the platform name and account identifier, and the tool automatically fetches the account's recent works, resolves download links, and supports batch downloading to your local machine.

---

## Supported Platforms

| --platform | Platform | Account ID | Notes |
|:---|:---|:---|:---|
| `douyin` | 抖音 (Douyin) | uniqueName | e.g. `Fish688688` |
| `kuaishou` | 快手 (Kuaishou) | kwaiId | Display ID |
| `bilibili` | 哔哩哔哩 (Bilibili) | Homepage URL (accountUrl) | e.g. `https://space.bilibili.com/123456` |
| `youtube` | YouTube | Channel URL (channel) | e.g. `https://www.youtube.com/@channel` |

---

## Features

- **Work Fetching**: Retrieve account works with titles, engagement data, and links.
- **Link Resolution**: Parse video/image download links (watermark-free).
- **Batch Download**: Download all works to local `output/` directory.
- **Pagination**: Browse more works across multiple pages.
- **Date Filtering**: Filter works by publish date range.
- **Multi-Platform**: Single tool for four major platforms.

---

## API Key

Get your API Key at [redfox.hk](https://redfox.hk/settings/api-keys?source=github).

```bash
export REDFOX_API_KEY=ak_your_key
```

---

## CLI Usage

```bash
# Kuaishou
python3 main.py --platform kuaishou --account "kwaiId"

# Bilibili
python3 main.py --platform bilibili --account "https://space.bilibili.com/123456" --download

# YouTube
python3 main.py --platform youtube --account "https://www.youtube.com/@channel" --date-start 2026-07-01
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `--platform` | Target platform (required) |
| `--account` | Single account ID |
| `--accounts` | Multiple account IDs, comma-separated |
| `--count` | Number of works to fetch (default 10, max 50) |
| `--page` | Page number (default 1) |
| `--date-start` | Start date YYYY-MM-DD |
| `--date-end` | End date YYYY-MM-DD |
| `--download` | Download video files to local |
| `--output-dir` | Download directory (default `output/`) |
| `--json` | JSON format output |
| `--rate-limit` | Request interval in seconds (default 1.0) |
| `--api-key` | API Key |

### Dependencies

```bash
pip3 install requests
```

---

## FAQ

**Q: Are downloaded videos watermarked?**
A: No. The API returns watermark-free direct links.

**Q: Can I download image posts?**
A: Yes. Image/gallery posts will download the cover image (JPG/PNG/WebP).

**Q: What does "rate limit exceeded" mean?**
A: API returned code=3108. Increase `--rate-limit 2.0` to add delay between requests.

**Q: How do I find the account ID for each platform?**
A: Check the platform-specific profile page URL. Each platform section above shows what to look for.
