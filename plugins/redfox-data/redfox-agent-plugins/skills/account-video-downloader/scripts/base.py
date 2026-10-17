#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared base — API Key management, works cache, file download, output formatting
========================================================================
Each platform subclass inherits BaseDownloader and only implements fetch_works() and get_download_info().
"""

import json
import os
import re
import sys
import time
import warnings
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

import requests

warnings.filterwarnings("ignore", category=Warning)
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

# ─── Config ─────────────────────────────────────────────────────────────────────────
API_BASE = "https://redfox.hk"
ENV_KEY = "REDFOX_API_KEY"

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
DEFAULT_RATE_LIMIT = 1.0

SUPPORT_EMAIL = "redfoxdata@proton.me"

# ── Redfox channel attribution ──
# Appends the running AI client to the API `source` field for per-platform stats.
# Priority: REDFOX_CHANNEL env var (documented in SKILL.md) > client env markers > "github".
# NOTE: SOURCE_BASE stays in Chinese on purpose — it is the backend skill identifier
# used for stats/whitelisting, not user-facing copy. Only the suffix is dynamic.
SOURCE_BASE = "多平台主页作品提取"


def detect_channel():
    """Best-effort detection of the AI client that is running this skill."""
    ch = os.environ.get("REDFOX_CHANNEL", "").strip().lower()
    if ch:
        return ch
    markers = (
        ("claude", ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_PLUGIN_ROOT")),
        ("cursor", ("CURSOR_TRACE_ID", "CURSOR_AGENT", "CURSOR_PLUGIN_ROOT")),
        ("codex", ("CODEX_SANDBOX", "CODEX_PLUGIN_ROOT", "CODEX_HOME")),
        ("gemini", ("GEMINI_CLI", "GEMINI_PLUGIN_ROOT")),
    )
    for name, keys in markers:
        if any(os.environ.get(k) for k in keys):
            return name
    return "github"


def build_source():
    """Return the API `source` value with a channel suffix, e.g. `<base>-Claude`."""
    canonical = {"claude": "Claude", "codex": "Codex", "cursor": "Cursor", "gemini": "Gemini", "github": "GitHub"}
    ch = detect_channel()
    return f"{SOURCE_BASE}-{canonical.get(ch, ch.capitalize())}"


# ─── Works-list cache (full-fetch optimization) ──────────────────────────────────────
CACHE_DIR = Path.home() / ".redfox" / "account_video_extractor_cache"
CACHE_TTL_SECONDS = 1800  # 30 minutes

# ─── Terminal colors ──────────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def info(msg: str):
    print(f"{GREEN}[OK]{RESET} {msg}")


def warn(msg: str):
    print(f"{YELLOW}[!!]{RESET} {msg}")


def error(msg: str):
    print(f"{RED}[XX]{RESET} {msg}")


def step(msg: str):
    print(f"{CYAN}[>>]{RESET} {msg}")


# ─── API Key management ──────────────────────────────────────────────────────────────────
def get_api_key() -> Optional[str]:
    """Read the API Key from the REDFOX_API_KEY environment variable."""
    return os.environ.get(ENV_KEY)


# ─── Number formatting ────────────────────────────────────────────────────────────────────
def format_number(n) -> str:
    """Format a number: >=1B -> x.xB, >=1M -> x.xM, >=1k -> x.xk, else comma-separated."""
    if n is None:
        return "-"
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)
    if n >= 1000000000:
        return f"{n / 1000000000:.1f}B"
    if n >= 1000000:
        return f"{n / 1000000:.1f}M"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return f"{n:,}"


# ─── Chinese detection ──────────────────────────────────────────────────────────────────────
def _is_chinese(text: str) -> bool:
    """Return True if the input contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


# ─── Works-list cache (full-fetch optimization) ──────────────────────────────────────

def _cache_key(platform: str, account_id: str) -> str:
    """Build the cache file name (hashed to prevent path injection)."""
    import hashlib
    raw = f"{platform}:{account_id.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16] + ".json"


def _load_works_cache(platform: str, account_id: str) -> Optional[dict]:
    """
    Read the cache. Returns a data dict or None.
    The dict contains: account, works, timestamp
    """
    if not CACHE_DIR.exists():
        return None
    cache_file = CACHE_DIR / _cache_key(platform, account_id)
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        age = time.time() - data.get("timestamp", 0)
        if age > CACHE_TTL_SECONDS:
            cache_file.unlink(missing_ok=True)
            return None
        return data
    except (json.JSONDecodeError, OSError):
        cache_file.unlink(missing_ok=True)
        return None


def _save_works_cache(platform: str, account_id: str, data: dict):
    """Persist the works-list cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["timestamp"] = time.time()
    cache_file = CACHE_DIR / _cache_key(platform, account_id)
    cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


# ─── Filename sanitizing ────────────────────────────────────────────────────────────────────
def safe_filename(text: str) -> str:
    """Convert text into a safe filename (strip illegal chars, cap length)."""
    text = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', text)
    text = text.strip().strip('.')
    if len(text) > 80:
        text = text[:80]
    return text or "video"


# ─── Abstract base class ──────────────────────────────────────────────────────────────────────

class BaseDownloader(ABC):
    """Base class for the multi-platform video downloader."""

    def __init__(self, api_key: str, platform_key: str, platform_label: str):
        """
        Args:
            api_key: API key
            platform_key: platform identifier (e.g. "kuaishou", "bilibili")
            platform_label: human-readable platform name (e.g. "Kuaishou", "Bilibili")
        """
        self.api_key = api_key
        self.platform_key = platform_key
        self.platform_label = platform_label

    # ── Must be implemented by subclasses ────────────────────────────────────────────────────────────

    @abstractmethod
    def fetch_works(self, account_id: str, page_size: int = DEFAULT_PAGE_SIZE, page_num: int = 1,
                    date_start: str = "", date_end: str = "") -> dict:
        """
        Fetch the account's works list.

        Returns:
            dict: {
                "success": bool,
                "account": dict | None,
                "works": list[dict],
                "error": str | None,
                "rate_limited": bool
            }
            Each work dict has already been normalized via _normalize_work().
        """
        ...

    @abstractmethod
    def get_download_info(self, work_url: str) -> dict:
        """
        Resolve the video download link.

        Returns:
            dict: {"success": bool, "download_url": str|None, "title": str|None,
                   "cover": str|None, "duration": int|None, "resources": list, "error": str|None}
        """
        ...

    # ── Optional overrides ────────────────────────────────────────────────────────────────

    def validate_account_id(self, account_id: str) -> tuple:
        """
        Validate the account identifier format. Rejects pure-Chinese input by default.

        Returns:
            (is_valid: bool, message: str)
        """
        if _is_chinese(account_id):
            return False, (
                f"'{account_id}' looks like an account nickname rather than a unique identifier.\n"
                "Please provide the account's unique ID for an accurate lookup."
            )
        if not account_id or len(account_id) < 2:
            return False, f"'{account_id}' is not a valid account identifier. Please provide a correct ID."
        return True, ""

    def description_hint(self) -> str:
        """Return the account-identifier hint for this platform, used to prompt the user for the right format."""
        return f"Please provide the unique account identifier for {self.platform_label} (e.g. the user ID)."

    # ── Shared implementation ────────────────────────────────────────────────────────────────

    def download_video(self, download_url: str, output_path: str) -> bool:
        """
        Download a video file to local disk.

        Args:
            download_url: direct video download link
            output_path: save path

        Returns:
            bool: whether the download succeeded
        """
        try:
            resp = requests.get(download_url, timeout=120, stream=True)
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            # Verify file size
            if total > 0 and downloaded < total * 0.9:
                warn(f"  File may be incomplete: {downloaded}/{total} bytes")
                return False

            return True
        except requests.exceptions.RequestException as e:
            error(f"  Download failed: {e}")
            return False
        except OSError as e:
            error(f"  File write failed: {e}")
            return False

    # ── Field normalization (subclasses may override) ────────────────────────────────────────────────

    def _normalize_work(self, work: dict, account_id: str) -> dict:
        """
        Map platform-specific fields onto the common schema. Subclasses may override
        to support platform-specific field names.

        Common schema:
        {
            "title": str,
            "workUrl": str,
            "publishTime": str (YYYY-MM-DD),
            "likeCount": int,
            "commentCount": int,
            "collectCount": int,
            "shareCount": int,
            "authorName": str,
            "followerCount": int
        }
        """
        return {
            "title": work.get("title") or work.get("content") or work.get("desc") or "",
            "workUrl": work.get("workUrl") or work.get("opusUrl") or work.get("url") or work.get("link") or "",
            "publishTime": work.get("publishTime") or work.get("createTime") or work.get("created_at") or work.get("pubdate") or "",
            "likeCount": work.get("likeCount") or work.get("diggCount") or work.get("like_count") or 0,
            "commentCount": work.get("commentCount") or work.get("comment_count") or 0,
            "collectCount": work.get("collectCount") or work.get("collect_count") or work.get("favoriteCount") or 0,
            "shareCount": work.get("shareCount") or work.get("share_count") or 0,
            "authorName": work.get("authorName") or work.get("nickname") or work.get("name") or account_id,
            "followerCount": work.get("authorFansCount") or work.get("authorFans") or work.get("followerCount") or work.get("follower_count") or 0,
        }


# ─── Main processing flow ────────────────────────────────────────────────────────────────────

def process_account(
    downloader: BaseDownloader,
    account_id: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    page_num: int = 1,
    date_start: str = "",
    date_end: str = "",
    rate_limit: float = DEFAULT_RATE_LIMIT,
    do_download: bool = False,
    output_dir: str = "",
) -> tuple:
    """
    Process a single account: fetch works -> date filter -> resolve download links -> download videos.

    Args:
        downloader: platform downloader instance
        account_id: account identifier
        page_size: items per page
        page_num: page number
        date_start: start date YYYY-MM-DD
        date_end: end date YYYY-MM-DD
        rate_limit: seconds between requests
        do_download: whether to download files
        output_dir: download directory

    Returns:
        (account_info: dict, results: list[dict])
    """
    # Step 1: fetch works
    label = downloader.platform_label
    date_info = ""
    if date_start or date_end:
        date_info = f" (dates {date_start}~{date_end})"
    step(f"Fetching {label} account works: {account_id}{date_info}")

    works_result = downloader.fetch_works(account_id, page_size, page_num=page_num,
                                                date_start=date_start, date_end=date_end)

    if not works_result["success"]:
        error(f"Fetch failed: {works_result['error']}")
        return works_result.get("account") or {"accountId": account_id}, []

    account = works_result["account"]
    works = works_result["works"]
    has_more_api = works_result.get("has_more")  # YouTube pagination flag
    if has_more_api is not None:
        account["_has_more"] = has_more_api
    info(f"Fetched {len(works)} works — {account.get('accountName', account_id)}")

    if not works:
        warn("This account has no works yet")
        return account, []

    # Step 1.5: client-side date filter
    if date_start or date_end:
        original_count = len(works)
        filtered = []
        for w in works:
            pt = w.get("publishTime", "")
            if not pt:
                filtered.append(w)
                continue
            if date_start and pt[:10] < date_start:
                continue
            if date_end and pt[:10] > date_end:
                continue
            filtered.append(w)
        works = filtered
        skipped = original_count - len(works)
        if skipped > 0:
            info(f"Date filter: {original_count} -> {len(works)} works ({skipped} skipped)")

    if not works:
        warn("No works in the given date range")
        return account, []

    # Step 1.6: client-side pagination truncation (for platforms like YouTube that return everything)
    if page_size > 0 and len(works) > page_size:
        works = works[:page_size]

    # Step 2: resolve each download link
    results = []
    total = len(works)

    for i, work in enumerate(works, 1):
        work_url = work.get("workUrl") or ""
        title = work.get("title") or "Untitled"

        print(f"\n  [{i}/{total}] {CYAN}Resolving:{RESET} {title[:50]}{'...' if len(title) > 50 else ''}")

        if not work_url:
            warn(f"  No work link, skipping")
            results.append({
                "title": title,
                "work_url": "",
                "likeCount": work.get("likeCount", 0),
                "shareCount": work.get("shareCount", 0),
                "commentCount": work.get("commentCount", 0),
                "collectCount": work.get("collectCount", 0),
                "publishTime": work.get("publishTime", ""),
                "download_success": False,
                "download_error": "No work link",
                "download_url": None,
                "cover": None,
                "duration": None,
                "resources": [],
                "local_path": None,
            })
            continue

        # Prefer the watermark-free direct link already in the works list (Kuaishou), skipping the download API
        direct_url = work.get("directVideoUrl")
        if direct_url:
            dl_result = {
                "success": True,
                "download_url": direct_url,
                "title": title,
                "cover": work.get("coverUrl") or "",
                "duration": None,
                "resources": [{"type": "video", "downloadUrl": direct_url}],
                "error": None,
            }
            info(f"  ✓ No resolution needed (works list includes a watermark-free direct link)")
        else:
            dl_result = downloader.get_download_info(work_url)

        result_entry = {
            "title": title,
            "work_url": work_url,
            "likeCount": work.get("likeCount", 0),
            "shareCount": work.get("shareCount", 0),
            "commentCount": work.get("commentCount", 0),
            "collectCount": work.get("collectCount", 0),
            "publishTime": work.get("publishTime", ""),
            "download_success": dl_result["success"],
            "download_error": dl_result.get("error"),
            "download_url": dl_result.get("download_url"),
            "cover": dl_result.get("cover"),
            "duration": dl_result.get("duration"),
            "resources": dl_result.get("resources", []),
            "local_path": None,
        }

        if dl_result["success"] and dl_result.get("download_url"):
            resources = dl_result.get("resources", [])
            is_image_post = (
                not any(r.get("type") == "video" for r in resources if isinstance(r, dict))
                and any(r.get("type") == "image" for r in resources if isinstance(r, dict))
            )
            media_label = "image" if is_image_post else "video"
            info(f"  Resolved ({media_label})" + (f" | duration: {dl_result['duration']}s" if dl_result.get("duration") else ""))

            # Step 3: download
            if do_download:
                dl_url = dl_result["download_url"]
                pub_time = work.get("publishTime", "")
                time_part = pub_time[:10].replace("-", "") if pub_time else datetime.now().strftime("%Y%m%d")
                safe_title = safe_filename(title)

                VIDEO_EXTS = ("mp4", "mov", "webm", "avi")
                IMAGE_EXTS = ("jpg", "jpeg", "png", "webp", "gif", "bmp")
                ext = ".jpg" if is_image_post else ".mp4"
                parsed = urlparse(dl_url)
                path_part = unquote(parsed.path)
                if "." in path_part.rsplit("/", 1)[-1]:
                    url_ext = path_part.rsplit(".", 1)[-1].split("?")[0].lower()
                    if is_image_post and url_ext in IMAGE_EXTS:
                        ext = f".{url_ext}"
                    elif not is_image_post and url_ext in VIDEO_EXTS:
                        ext = f".{url_ext}"

                filename = f"{time_part}_{safe_title}{ext}"
                out_path = os.path.join(output_dir, filename)

                print(f"  {CYAN}Downloading...{RESET}", end="", flush=True)
                if downloader.download_video(dl_url, out_path):
                    file_size = os.path.getsize(out_path)
                    size_mb = file_size / (1024 * 1024)
                    info(f"\r  Download complete: {filename} ({size_mb:.1f} MB)")
                    result_entry["local_path"] = out_path
                else:
                    warn(f"\r  Download failed")
                    result_entry["download_success"] = False
                    result_entry["download_error"] = "File download failed"
        else:
            warn(f"  Resolution failed: {dl_result.get('error', 'unknown error')}")

        results.append(result_entry)

        # Rate limiting
        if i < total:
            time.sleep(rate_limit)

    return account, results


# ─── Markdown output ────────────────────────────────────────────────────────────────

def print_markdown_table(
    downloader: BaseDownloader,
    account: dict,
    results: list,
    page_num: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
):
    """
    Print the results as a Markdown table.

    ⛔ Mandatory rule: the calling Agent MUST render this function's full output verbatim. The following are forbidden:
    - Do not drop or merge any column
    - Do not omit the pagination hint line
    - Do not omit the date-range hint or the download prompt
    - Do not replace the full table content with "..." or a summary
    - Every work must be shown line by line (including the full resource download links)
    """
    name = account.get("accountName", account.get("accountId", "unknown"))
    fans = format_number(account.get("followerCount"))
    label = downloader.platform_label

    # Follower count: None means the platform has no such data, so don't show it
    fans_display = f" (followers: {fans})" if account.get("followerCount") is not None else ""
    print(f"\n## 📥 {label} Video Download — @{name}{fans_display}")
    print()
    total = len(results)

    # Pagination hint: YouTube uses a continuation token; other platforms use pageNum
    yt_has_more = account.get("_has_more")
    show_more = yt_has_more if yt_has_more is not None else (total >= page_size)

    page_info = f"Currently on **page {page_num}**, {total} works in total"
    if show_more:
        next_page = page_num + 1
        page_info += f" | more works available, pass `--page {next_page}` to view the next page"
    print(page_info)
    print()
    print("| # | Published | Work | Likes | Comments | Saves | Shares | Download |")
    print("|---|----------|------|-----|------|------|------|------|")

    success_count = 0
    fail_count = 0

    for i, r in enumerate(results, 1):
        title_raw = (r.get("title") or "Untitled")[:25]
        title = title_raw.replace("|", "\\|").replace("\n", " ")
        work_url = r.get("work_url", "")

        if work_url:
            title_display = f"[{title}]({work_url})"
        else:
            title_display = title

        pub_time = r.get("publishTime", "")[:10] if r.get("publishTime") else "-"
        likes = format_number(r.get("likeCount"))
        comments = format_number(r.get("commentCount"))
        collects = format_number(r.get("collectCount"))
        shares = format_number(r.get("shareCount"))

        # Resource download column
        resources = r.get("resources", [])
        resource_parts = []
        seen_types = set()
        has_video = False
        for res in resources:
            if not isinstance(res, dict):
                continue
            rtype = res.get("type", "")
            rurl = res.get("downloadUrl") or res.get("url") or ""
            if rtype and rurl and rtype not in seen_types:
                seen_types.add(rtype)
                if rtype == "video":
                    has_video = True
                    resource_parts.append(f"[Video]({rurl})")
                elif rtype == "image":
                    resource_parts.append(f"[Cover]({rurl})")
                elif rtype == "audio":
                    resource_parts.append(f"[Audio]({rurl})")
                else:
                    resource_parts.append(f"[{rtype}]({rurl})")

        cover = r.get("cover")
        if cover and "image" not in seen_types:
            resource_parts.append(f"[Cover]({cover})")

        # YouTube CDN links are IP-locked signed URLs that a browser cannot open directly
        if downloader.platform_key == "youtube" and resource_parts:
            resource_parts = ["[▶ Play]({}) · ⚠️ download requires `--download`".format(work_url)] if work_url else ["⚠️ download requires `--download`"]

        resource_display = "<br>".join(resource_parts) if resource_parts else "-"

        if r.get("download_success") and has_video:
            success_count += 1
        elif r.get("download_success"):
            success_count += 1
        else:
            fail_count += 1

        print(f"| {i} | {pub_time} | {title_display} | {likes} | {comments} | {collects} | {shares} | {resource_display} |")

    print()
    parts = [f"{success_count} downloadable"]
    if fail_count > 0:
        parts.append(f"{fail_count} failed")
    print(f"**Total:** {total} works, {', '.join(parts)}")
    if fail_count > 0:
        print(f"\n> ⚠️ A failed video may have been deleted by its author. For data verification, contact the support email **{SUPPORT_EMAIL}**.")
    print(f"\n> 💡 You can specify a publish-date range to extract, e.g. `--date-start 2026-07-01 --date-end 2026-07-20`")
    if success_count > 0:
        print(f"> 💾 Want to batch-download these {success_count} works to your machine? Just let me know.")


# ─── JSON output ────────────────────────────────────────────────────────────────────

def print_json_output(account: dict, results: list):
    """Print the results as JSON."""
    output = {
        "account": account,
        "total": len(results),
        "success": sum(1 for r in results if r.get("download_success")),
        "failed": sum(1 for r in results if not r.get("download_success")),
        "results": results,
        "generated_at": datetime.now().isoformat(),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
