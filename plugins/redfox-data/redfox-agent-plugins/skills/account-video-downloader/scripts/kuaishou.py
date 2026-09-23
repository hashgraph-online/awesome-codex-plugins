#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kuaishou platform video downloader
"""

import json
import re
import sys

import requests

from .base import (
    API_BASE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    BaseDownloader,
    build_source,
    error,
    info,
    warn,
)


class KuaishouDownloader(BaseDownloader):
    """Kuaishou account video downloader"""

    # Platform endpoints
    WORKS_ENDPOINT = "/story/api/ksAllData/queryWorkList"
    DOWNLOAD_ENDPOINT = "/story/api/parseWork/videoDownload/kuaishou"

    def __init__(self, api_key: str):
        super().__init__(api_key, "kuaishou", "Kuaishou")

    def validate_account_id(self, account_id: str) -> tuple:
        """Kuaishou only accepts the kwaiId; rejects URL / nickname."""
        if not account_id or len(account_id) < 2:
            return False, "Please enter the Kuaishou account ID (kwaiId)."

        # Reject homepage links
        if "kuaishou.com" in account_id or "kuaishou.cn" in account_id:
            return False, (
                "Kuaishou does not support homepage links. Please provide the **account ID (kwaiId)**.\n"
                "How to find it: Kuaishou APP -> target account profile -> the ID shown below the nickname (e.g. junningjunning666)."
            )

        # Reject Chinese nicknames
        if re.search(r'[\u4e00-\u9fff]', account_id):
            return False, (
                f"'{account_id}' is an account nickname, not an ID. Nicknames can be duplicated, so please provide the unique **account ID (kwaiId)**.\n"
                "How to find it: Kuaishou APP -> target account profile -> the ID shown below the nickname."
            )

        return True, ""

    def description_hint(self) -> str:
        return "Please provide the Kuaishou account ID / kwaiId (Kuaishou APP -> target profile -> shown below the nickname, e.g. junningjunning666)."

    def fetch_works(self, account_id: str, page_size: int = DEFAULT_PAGE_SIZE, page_num: int = 1,
                    date_start: str = "", date_end: str = "") -> dict:
        payload = {
            "kwaiId": account_id,
            "page": page_num,
            "size": min(page_size, MAX_PAGE_SIZE),
            "source": build_source(),
        }

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

            if isinstance(data_raw, list):
                raw_works = data_raw
            elif isinstance(data_raw, dict):
                raw_works = data_raw.get("list") or []
            else:
                raw_works = []

            works = [self._normalize_work(w, account_id) for w in raw_works]

            # Extract account info: each Kuaishou item carries nickname / authorFans
            account_info = {"accountId": account_id}
            if works:
                account_info["accountName"] = works[0].get("authorName", account_id)
                account_info["followerCount"] = works[0].get("followerCount", 0)
            else:
                account_info["accountName"] = account_id

            return {
                "success": True,
                "account": account_info,
                "works": works,
                "error": None,
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
        """Normalize Kuaishou video fields."""
        photo_id = work.get("photoId", "")
        return {
            "title": work.get("caption") or work.get("title") or "",
            "workUrl": f"https://www.kuaishou.com/short-video/{photo_id}" if photo_id else (work.get("workUrl") or ""),
            "publishTime": work.get("publishTime") or "",
            "likeCount": work.get("likeCount", 0),
            "commentCount": work.get("commentCount", 0),
            "collectCount": work.get("collectCount") or 0,
            "shareCount": work.get("shareCount", 0),
            "authorName": work.get("nickname") or work.get("authorName") or account_id,
            "followerCount": work.get("authorFans") or work.get("authorFansCount") or 0,
            # The works-list API already returns a watermark-free mp4 URL, so no download API call is needed
            "directVideoUrl": work.get("videoUrl") or "",
            "coverUrl": work.get("coverUrl") or "",
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

        payload_data = data.get("data")
        if not payload_data:
            return {"success": False, "download_url": None, "title": None, "cover": None,
                    "duration": None, "resources": [], "error": "API returned empty data"}

        return self._parse_download_data(payload_data)

    def _parse_download_data(self, payload_data) -> dict:
        """Parse the download API response and extract resource links."""
        result = {
            "success": True,
            "download_url": None,
            "title": None,
            "cover": None,
            "duration": None,
            "resources": [],
            "error": None,
        }

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
