#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Douyin platform video downloader
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


class DouyinDownloader(BaseDownloader):
    """Douyin account video downloader"""

    WORKS_ENDPOINT = "/story/api/dy/data/listWorkByAccount"
    DOWNLOAD_ENDPOINT = "/story/api/parseWork/videoDownload/douyin"

    def __init__(self, api_key: str):
        super().__init__(api_key, "douyin", "Douyin")

    def validate_account_id(self, account_id: str) -> tuple:
        """Douyin only accepts the Douyin ID (uniqueName); rejects URL / nickname / sec_uid."""
        if not account_id or len(account_id) < 2:
            return False, "Please enter the Douyin ID."

        # Reject homepage links
        if "douyin.com" in account_id:
            return False, (
                "Douyin does not support homepage links. Please provide the **Douyin ID**.\n"
                "How to find it: Douyin APP -> target account profile -> the 'Douyin ID: xxx' field below the avatar (e.g. JCLjiangchenglan)."
            )

        # Reject Chinese nicknames
        if re.search(r'[\u4e00-\u9fff]', account_id):
            return False, (
                f"'{account_id}' is an account nickname, not a Douyin ID. Nicknames can be duplicated, so please provide the unique **Douyin ID**.\n"
                "How to find it: Douyin APP -> target account profile -> the 'Douyin ID: xxx' field below the avatar."
            )

        # Reject sec_uid (a long hash, not the Douyin ID)
        if len(account_id) > 20:
            return False, (
                "This looks like an encrypted user ID (sec_uid), not a Douyin ID. Please provide the **Douyin ID**.\n"
                "How to find it: Douyin APP -> target account profile -> the 'Douyin ID: xxx' field below the avatar (e.g. JCLjiangchenglan)."
            )

        return True, ""

    def description_hint(self) -> str:
        return "Please provide the Douyin ID (Douyin APP -> target profile -> the 'Douyin ID' field below the avatar, e.g. JCLjiangchenglan)."

    def fetch_works(self, account_id: str, page_size: int = DEFAULT_PAGE_SIZE, page_num: int = 1,
                    date_start: str = "", date_end: str = "") -> dict:
        payload = {
            "uniqueName": account_id,
            "shortId": "",
            "pageNum": page_num,
            "pageSize": min(page_size, MAX_PAGE_SIZE),
            "source": build_source(),
        }
        if date_start:
            payload["startDate"] = date_start
        if date_end:
            payload["endDate"] = date_end

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
        """Normalize Douyin video fields."""
        return {
            "title": work.get("content") or work.get("title") or "",
            "workUrl": work.get("opusUrl") or work.get("workUrl") or "",
            "publishTime": work.get("publishTime") or "",
            "likeCount": work.get("likeCount", 0),
            "commentCount": work.get("commentCount", 0),
            "collectCount": work.get("collectCount", 0),
            "shareCount": work.get("shareCount", 0),
            "authorName": work.get("authorName") or work.get("nickname") or account_id,
            "followerCount": work.get("authorFansCount") or work.get("followerCount") or 0,
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
