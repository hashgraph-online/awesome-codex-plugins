#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili platform video downloader
"""

import json
import re

import requests

from .base import (
    API_BASE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    BaseDownloader,
    build_source,
)


class BilibiliDownloader(BaseDownloader):
    """Bilibili account video downloader"""

    WORKS_ENDPOINT = "/story/api/bili/data/accountWorkList"
    DOWNLOAD_ENDPOINT = "/story/api/parseWork/videoDownload/bilibili"

    def __init__(self, api_key: str):
        super().__init__(api_key, "bilibili", "Bilibili")

    @staticmethod
    def _extract_mid(account_id: str) -> str:
        """Extract the mid from a Bilibili homepage link."""
        m = re.search(r'space\.bilibili\.com/(\d+)', account_id)
        return m.group(1) if m else ""

    def validate_account_id(self, account_id: str) -> tuple:
        """The Bilibili account identifier is the homepage link (accountUrl)."""
        if not account_id or len(account_id) < 5:
            return False, f"'{account_id}' is not a valid Bilibili homepage link. Please provide the full personal-space URL."
        if "bilibili.com" not in account_id and "b23.tv" not in account_id:
            return False, f"'{account_id}' is not a Bilibili domain link. Please provide a homepage URL like https://space.bilibili.com/123456."
        return True, ""

    def description_hint(self) -> str:
        return "Please provide the Bilibili account's homepage link (e.g. https://space.bilibili.com/123456)."

    def fetch_works(self, account_id: str, page_size: int = DEFAULT_PAGE_SIZE, page_num: int = 1,
                    date_start: str = "", date_end: str = "") -> dict:
        mid = self._extract_mid(account_id)
        payload = {
            "accountUrl": account_id,
            "page": page_num,
            "pageSize": min(page_size, MAX_PAGE_SIZE),
            "order": "time",
            "source": build_source(),
        }
        if mid:
            payload["mid"] = mid

        url = f"{API_BASE}{self.WORKS_ENDPOINT}"
        headers = {
            "Content-Type": "application/json",
            "REDFOX_API_KEY": self.api_key,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            result = resp.json()
        except requests.exceptions.Timeout:
            return {"success": False, "account": None, "works": [], "error": "Request timed out, please try again later"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "account": None, "works": [], "error": f"Network request failed: {e}"}
        except json.JSONDecodeError:
            return {"success": False, "account": None, "works": [], "error": "API returned invalid data"}

        code = result.get("code")
        msg = result.get("msg", "")

        if code in (200, 2000):
            data_raw = result.get("data", {})
            if not data_raw:
                return {"success": False, "account": None, "works": [],
                        "error": "No works found for this account; it may not be indexed yet"}

            # The Bilibili API returns data.workList
            raw_works = data_raw.get("workList", []) if isinstance(data_raw, dict) else []

            works = [self._normalize_work(w, account_id) for w in raw_works]

            # Extract account info: use the first work's author as the account name
            account_info = {"accountId": account_id}
            if works:
                account_info["accountName"] = works[0].get("authorName", account_id)
            else:
                account_info["accountName"] = account_id
            # The Bilibili API returns no follower count
            account_info["followerCount"] = None

            # The Bilibili API returns total (total works), used to determine has_more accurately
            total_count = data_raw.get("total", 0)
            has_more = (page_num * min(page_size, MAX_PAGE_SIZE)) < total_count

            return {
                "success": True,
                "account": account_info,
                "works": works,
                "error": None,
                "has_more": has_more,
            }

        if code == 3108:
            return {"success": False, "account": None, "works": [],
                    "error": "Rate limit exceeded, please try again later or increase --rate-limit"}
        if code in (3106, 3107):
            return {"success": False, "account": None, "works": [],
                    "error": f"Invalid API Key (code {code}), please check your configuration"}
        if code == 400:
            return {"success": False, "account": None, "works": [],
                    "error": f"Invalid request parameters: {msg}"}

        return {"success": False, "account": None, "works": [],
                "error": f"API error (code {code}): {msg}"}

    def _normalize_work(self, work: dict, account_id: str) -> dict:
        """Normalize Bilibili video fields."""
        bv_id = work.get("bvId", "")
        return {
            "title": work.get("title") or "",
            "workUrl": f"https://www.bilibili.com/video/{bv_id}" if bv_id else (work.get("url") or ""),
            "publishTime": work.get("created") or work.get("publishTime") or "",
            "likeCount": work.get("likeCount", 0),
            "commentCount": work.get("commentCount", 0),
            "collectCount": work.get("favoriteCount", 0),
            "shareCount": work.get("shareCount", 0),
            "authorName": work.get("author") or work.get("authorName") or account_id,
            "followerCount": 0,
        }

    def get_download_info(self, work_url: str) -> dict:
        payload = {"url": work_url, "source": build_source()}
        url = f"{API_BASE}{self.DOWNLOAD_ENDPOINT}"
        headers = {
            "Content-Type": "application/json",
            "REDFOX_API_KEY": self.api_key,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            data = resp.json()
        except requests.exceptions.Timeout:
            return {"success": False, "download_url": None, "title": None, "cover": None,
                    "duration": None, "resources": [], "error": "Resolution timed out"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "download_url": None, "title": None, "cover": None,
                    "duration": None, "resources": [], "error": f"Network request failed: {e}"}
        except json.JSONDecodeError:
            return {"success": False, "download_url": None, "title": None, "cover": None,
                    "duration": None, "resources": [], "error": "API returned invalid data"}

        code = data.get("code")
        msg = data.get("msg", "")

        if not str(code).startswith("2"):
            if code == 3108:
                err = "Rate limit exceeded"
            elif code in (3106, 3107):
                err = "Invalid API Key"
            elif code == 400:
                err = f"Invalid parameters: {msg}"
            else:
                err = f"API error (code {code}): {msg}"
            return {"success": False, "download_url": None, "title": None, "cover": None,
                    "duration": None, "resources": [], "error": err}

        return self._parse_download_data(data.get("data"))

    def _parse_download_data(self, payload_data) -> dict:
        """Parse the download API response."""
        result = {
            "success": True,
            "download_url": None,
            "title": None,
            "cover": None,
            "duration": None,
            "resources": [],
            "error": None,
        }

        if not payload_data:
            return {**result, "success": False, "error": "API returned empty data"}

        if isinstance(payload_data, dict):
            result["title"] = payload_data.get("desc") or payload_data.get("title")
            result["cover"] = payload_data.get("cover") or payload_data.get("coverUrl")

            dur = payload_data.get("duration") or payload_data.get("durationSeconds")
            if isinstance(dur, (int, float)):
                result["duration"] = int(dur)

            resources = payload_data.get("resources", [])
            if isinstance(resources, list):
                result["resources"] = resources
                for res in resources:
                    if isinstance(res, dict):
                        rtype = res.get("type", "")
                        dl = res.get("downloadUrl") or res.get("url")
                        if dl and rtype == "video" and not result["download_url"]:
                            result["download_url"] = dl
                        if dl and rtype == "image":
                            if not result["cover"]:
                                result["cover"] = dl
                            if not result["download_url"]:
                                result["download_url"] = dl
                        res_dur = res.get("durationSeconds")
                        if isinstance(res_dur, (int, float)) and not result["duration"]:
                            result["duration"] = int(res_dur)

            if not result["download_url"]:
                result["download_url"] = (
                    payload_data.get("videoUrl")
                    or payload_data.get("video_url")
                    or payload_data.get("downloadUrl")
                    or payload_data.get("download_url")
                    or payload_data.get("playUrl")
                )

        return result
