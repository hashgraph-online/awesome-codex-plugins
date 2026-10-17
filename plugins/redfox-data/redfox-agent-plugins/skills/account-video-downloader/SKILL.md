---
name: account-video-downloader
description: Multi-platform account video extractor — provide a platform name and account ID/link to automatically fetch homepage works from Douyin, Kuaishou, Bilibili, and YouTube, resolve download links, and batch-download. Use cases: breaking down competitor content frame by frame, saving all works from favorite creators before they get deleted, gathering material for re-editing, backing up your own account works locally, hoarding course/tutorial videos for offline viewing, and pulling a creator's works for due diligence before a collaboration. Trigger words: homepage video download, batch video download, account video extraction, Kuaishou homepage download, Bilibili video extraction, YouTube channel download, video saving, watermark-free download, competitor video download, creator video backup.
---

> **Note:** `{SKILL_DIR}` in the commands below means the absolute path of the directory containing this SKILL.md — resolve it before execution.

> **Channel attribution:** replace `claude` in the `REDFOX_CHANNEL=claude` prefix below with the AI client you are currently running in: `claude` (Claude Code), `codex` (OpenAI Codex), `cursor` (Cursor), `gemini` (Gemini CLI). If the client is unknown, omit the prefix entirely — the script auto-detects the client from environment markers and falls back to `github`.

# Multi-Platform Account Video Extractor

> Platform + account -> fetch works list -> resolve download links -> one-click download to local

---

## Overview

A batch downloader for account homepage videos across multiple platforms. It supports **Douyin, Kuaishou, Bilibili, and YouTube**: provide the platform name and account identifier, and it automatically fetches the account's recent works, resolves the direct download link for each video/image post, and supports one-click batch downloading to your machine.

---

## Features

| Feature            | Description                                                            |
| ------------------ | ---------------------------------------------------------------------- |
| 📋 Work fetching   | Get recent homepage works by account (title, engagement data, work link) |
| 🔗 Link resolution | Call the resolve API per work to get the direct video/image download link |
| 📥 Batch download  | One-click download of all works (video + image posts) to the local `output/` directory |
| 📊 Data display    | Markdown table / JSON dual-format output with full engagement data      |
| 📄 Pagination      | Page through to view more works                                         |
| 📅 Date filtering  | Filter by work publish date                                             |
| 🌐 Multi-platform  | One tool covering Douyin / Kuaishou / Bilibili / YouTube                |

---

## Supported Platforms

| --platform | Platform | Account identifier       | Example                                |
| :--------- | :------- | :----------------------- | :------------------------------------- |
| `douyin`   | Douyin   | Douyin ID                | e.g. `Fish688688`                      |
| `kuaishou` | Kuaishou | Kuaishou ID (kwaiId)     | e.g. `Fish688688`                      |
| `bilibili` | Bilibili | Homepage URL (accountUrl)| e.g. `https://space.bilibili.com/123456` |
| `youtube`  | YouTube  | Channel URL (channel)    | e.g. `https://www.youtube.com/@channel`  |

---

## API

This skill calls the redfox.hk API. Each platform takes two steps:

| Step             | Endpoint                                              | Description                          |
| ---------------- | ----------------------------------------------------- | ------------------------------------ |
| 1. Fetch works   | `POST /story/api/{platform}/...`                      | Get the works list by account identifier |
| 2. Resolve download | `POST /story/api/parseWork/videoDownload/{platform}` | Get the direct download link by work URL |

### Authentication

Get an API Key at [RedfoxHub](https://redfox.hk/settings/api-keys?source=github) and set it as an environment variable:

```bash
# macOS / Linux
export REDFOX_API_KEY=ak_your_key

# Windows PowerShell
$env:REDFOX_API_KEY="ak_your_key"
```

---

## Usage

### CLI

```bash
# Douyin: basic usage
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform douyin --account "Fish688688"

# Kuaishou: basic usage
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform kuaishou --account "kwaiId"

# Bilibili: fetch works and resolve download links (no file download)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform bilibili --account "https://space.bilibili.com/123456"

# YouTube: download videos to local
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform youtube --account "https://www.youtube.com/@channel" --download

# YouTube: specify a download directory
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform youtube --account "https://www.youtube.com/@channel" --download --output-dir ./my_videos

# Set the number of works (default 10, max 50)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform bilibili --account "MID" --count 20 --download

# Page through to view more works
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform kuaishou --account "userID" --page 2

# Filter works by date range
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform bilibili --account "MID" --date-start 2026-07-01 --date-end 2026-07-31

# Multiple accounts (comma-separated)
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform bilibili --accounts "MID1,MID2" --download

# Combined: page 2 + date filter + download
REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform bilibili --account "MID" --page 2 --count 20 --date-start 2026-06-01 --download
```

### Parameters

| Parameter      | Description                              |
| -------------- | ---------------------------------------- |
| `--platform`   | Target platform (required, see table above) |
| `--account`    | A single account identifier              |
| `--accounts`   | Multiple account identifiers, comma-separated |
| `--count`      | Number of works to fetch (default 10, max 50) |
| `--page`       | Page number (default 1)                  |
| `--date-start` | Start date YYYY-MM-DD                    |
| `--date-end`   | End date YYYY-MM-DD                      |
| `--download`   | Download video files to local            |
| `--output-dir` | Download directory (default `output/`)   |
| `--json`       | Output in JSON format                    |
| `--rate-limit` | Seconds between requests (default 1.0)   |

### Dependencies

| Dependency | Install command         |
| ---------- | ----------------------- |
| `requests` | `pip3 install requests` |

---

## Account Identifier Requirements

Each platform has different requirements for the account identifier — **you must provide the platform's unique identifier**:

| Platform | Requirement            | URL support    | How to obtain                                       |
| :------- | :--------------------- | :------------- | :-------------------------------------------------- |
| Bilibili | Homepage URL (accountUrl) | ✅ Supported | Copy the personal-space page URL directly            |
| YouTube  | Channel URL (channel)  | ✅ Supported   | Copy the channel page URL directly                   |
| Douyin   | Douyin ID (uniqueName) | ❌ Not supported | Douyin APP -> target profile -> the 'Douyin ID: xxx' field below the avatar |
| Kuaishou | Account ID (kwaiId)    | ❌ Not supported | Kuaishou APP -> target profile -> the ID shown below the nickname |

> ⚠️ **Douyin and Kuaishou do not support homepage links!** If the user pastes a URL, you must prompt them for the unique identifier above.

**Important:** if the user only enters an account name without the unique identifier, you must prompt them for the exact unique identifier.

> 📸 **How to find the Douyin ID:** open the Douyin APP -> go to the target user's profile -> below the avatar and follower stats you'll see the 'Douyin ID: xxx' field. If the user isn't sure where it is, show an annotated screenshot (with the 'Douyin ID' location highlighted) to help them locate it.

---

## Agent Integration Guide

### Trigger words

- homepage video download / batch video download / account video extraction
- Douyin download / Douyin video extraction / download Douyin works
- Bilibili video extraction / Bilibili video download
- YouTube channel download / YouTube video extraction
- "download the homepage videos of xxx"

### Agent execution flow

```
Step 1: Confirm the user's intent, platform, and account identifier
  - Identify the target platform from the user's input (Douyin/Kuaishou/Bilibili/YouTube)
  - If the platform is unclear, ask: "Which platform do you want to download from?"
  - Confirm the account identifier format is correct; if the user gave a nickname, prompt for the unique ID

Step 2: Recognize any time range in the user's input
  - If the user mentions a work time range, recognize it and convert to --date-start / --date-end:
    - "7.1~7.20" -> --date-start 2026-07-01 --date-end 2026-07-20
    - "July 1 to July 20" -> --date-start 2026-07-01 --date-end 2026-07-20
    - "the last week" -> 7 days back from today
    - "last month" -> the 1st to the last day of the previous month
    - "works from July" -> --date-start 2026-07-01 --date-end 2026-07-31
  - Dates are always YYYY-MM-DD; the year defaults to the current year
  - If the user asks to "continue"/"next page", add --page N

Step 3: Call the script to fetch works + resolve download links
  REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform <platform> --account "<id>"

Step 4: Show results + ask about pagination
  - Show the Markdown table with clickable work links and download links
  - On failures: note "the video may have been deleted by its author; for data verification contact redfoxdata@proton.me"
  - If more pages exist: tell the user "more works are available — view the next page?" and page on request
  - Remind the user that extracting by time range is supported

Step 5: Ask whether the user wants a batch download
  - Use AskUserQuestion: "Batch-download the downloadable videos to your machine?"
  - Options: "Download to local" / "Just show the links"

Step 6: Run the download after the user confirms
  REDFOX_CHANNEL=claude python3 "{SKILL_DIR}/scripts/main.py" --platform <platform> --account "<id>" --download
  - Tell the user where the files were saved
```

### Agent output spec

After resolution, output in the following format (natural-language style, aimed at ordinary users).

#### ⛔ Mandatory rule: do not simplify the output

> **The Agent MUST render the full table returned by the script verbatim. The following are forbidden:**
>
> - ❌ Do not drop or merge any column (Published, Work, Likes, Comments, Saves, Shares, Download — all are required)
> - ❌ Do not omit the pagination hint line
> - ❌ Do not omit the date-range hint ("💡 You can specify a publish-date range to extract…")
> - ❌ Do not omit the download prompt ("💾 Want to batch-download these X works to your machine?")
> - ❌ Do not replace the full table content with "..." or a summary
> - ✅ Every work must be shown line by line with its full info (including resource download links)

#### Output template

```markdown
## 📥 {Platform} Video Download — @accountName (followers: X)

Currently on **page 1**, 10 works in total | more works available, pass `--page 2` to view the next page

| #   | Published | Work              | Likes | Comments | Saves | Shares | Download                                      |
| --- | --------- | ----------------- | ----- | -------- | ----- | ------ | --------------------------------------------- |
| 1   | 07-28     | [Work title](link)| 5.2k  | 67       | 689   | 5.8k   | [🎬Video](...) · [🖼Cover](...) · [🎵Audio](...) |
| 2   | 07-24     | [Work title 2](link)| 3.1k | 22      | 136   | 865    | [🖼Cover](...)                                |
| 3   | …         | …                 | …     | …        | …     | …      | …                                             |

**Total:** 10 works, 8 downloadable, 2 failed

> ⚠️ A failed video may have been deleted by its author. For data verification, contact the support email **redfoxdata@proton.me**.

> 💡 Want works from a specific time range? Just tell me the range, e.g. "7.1~7.20" or "the last week".

> 💾 Want to batch-download these X works to your machine? Just let me know.
```

The platform name is substituted automatically for the actual platform (Kuaishou / Bilibili / YouTube).

---

## FAQ

**Q: How do I get an API Key?**
A: Register at [redfox.hk](https://redfox.hk/settings/api-keys?source=github) to get one.

**Q: Are the downloaded videos watermarked?**
A: No. The direct video/image links returned by the API are watermark-free.

**Q: Can image posts be downloaded?**
A: Yes. Image posts (slideshows, galleries) automatically download the first image as JPG/PNG/WebP.

**Q: Why do I see "rate limit exceeded"?**
A: The API returns code=3108 when requests come too fast and trigger throttling. Increase the interval with `--rate-limit 2.0`.

**Q: Which platforms are supported?**
A: Douyin, Kuaishou, Bilibili, and YouTube.

**Q: Where do I find each platform's account identifier?**
A: Douyin needs the Douyin ID (e.g. JCLjiangchenglan); Kuaishou needs the account ID / kwaiId (below the account name); Bilibili needs the homepage link; YouTube needs the channel URL.
