#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube platform video downloader
"""

import json

import requests

from .base import (
    API_BASE,
    DEFAULT_PAGE_SIZE,
    BaseDownloader,
    build_source,
)


class YouTubeDownloader(BaseDownloader):
    """YouTube channel video downloader

    Pagination: uses YouTube's native continuation token, not the usual pageNum/pageSize.
    Each page holds about 100 videos.
    """

    WORKS_ENDPOINT = "/story/api/youtube/channel/videos"
    DOWNLOAD_ENDPOINT = "/story/api/parseWork/videoDownload/youtube"

    def __init__(self, api_key: str):
        super().__init__(api_key, "youtube", "YouTube")
        self._continuation_token = None   # pagination token
        self._has_more = False            # whether more pages remain

    def validate_account_id(self, account_id: str) -> tuple:
        """The YouTube channel identifier is the channel URL (channel)."""
        if not account_id or len(account_id) < 5:
            return False, f"'{account_id}' is not a valid YouTube channel identifier. Please provide the channel URL."
        return True, ""

    def description_hint(self) -> str:
        return "Please provide the YouTube channel URL (e.g. https://www.youtube.com/@channelname or https://www.youtube.com/channel/UC...)."

    def fetch_works(self, account_id: str, page_size: int = DEFAULT_PAGE_SIZE, page_num: int = 1,
                    date_start: str = "", date_end: str = "") -> dict:
        """
        Fetch the YouTube channel's video list.

        Pagination: the first page sends `channel`; subsequent pages send the continuation token.
        The page_size parameter has no effect on this platform (each page is fixed at ~100 items).
        """
        # Pagination: page_num==1 sends channel; later pages send the continuation token
        if page_num <= 1:
            self._continuation_token = None
            payload = {"channel": account_id, "source": build_source()}
        elif self._continuation_token:
            payload = {"continuation": self._continuation_token, "source": build_source()}
        else:
            return {"success": False, "account": None, "works": [],
                    "error": "No more pages to fetch (start from page 1 or wait for a continuation token)"}

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

        # The YouTube API response may be wrapped by redfox's {code, data, msg}, or returned directly
        code = result.get("code")
        msg = result.get("msg", "")

        if code is not None:
            # Standard redfox wrapper format
            if code not in (200, 2000):
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
            data_raw = result.get("data", result)
        else:
            # Data returned directly (no code wrapper)
            data_raw = result

        return self._parse_channel_response(data_raw, account_id)

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

    def _parse_channel_response(self, data_raw: dict, account_id: str) -> dict:
        """Parse the YouTube channel-videos API response.

        Response structure:
        {
          "results": [...],
          "playlist_info": {"title": "...", "numVideos": "5200", ...},
          "continuation_token": "...",
          "has_more": true
        }
        """
        if not data_raw or not isinstance(data_raw, dict):
            return {"success": False, "account": None, "works": [],
                    "error": "No works found for this channel; it may not be indexed yet"}

        # Extract the video list
        raw_works = data_raw.get("results", [])
        if not raw_works:
            return {"success": True,
                    "account": {"accountId": account_id, "accountName": account_id},
                    "works": [], "error": None}

        works = [self._normalize_work(w, account_id) for w in raw_works]

        # Extract channel info
        playlist_info = data_raw.get("playlist_info", {}) or {}
        account_info = {
            "accountId": account_id,
            "accountName": playlist_info.get("title") or account_id,
            "followerCount": None,
        }

        # Store the pagination token
        self._continuation_token = data_raw.get("continuation_token")
        self._has_more = data_raw.get("has_more", False)

        return {
            "success": True,
            "account": account_info,
            "works": works,
            "error": None,
            "has_more": self._has_more,
            "continuation_token": self._continuation_token,
        }

    def _normalize_work(self, work: dict, account_id: str) -> dict:
        """Normalize YouTube video fields.

        API fields: videoId, title, lengthText, viewCountText,
        thumbnails, channelHandle, channelId, channelTitle, index
        """
        video_id = work.get("videoId", "")
        # Use the highest-resolution thumbnail as the cover
        thumbnails = work.get("thumbnails", []) or []
        cover = thumbnails[-1].get("url") if thumbnails else ""
        return {
            "title": work.get("title") or "",
            "workUrl": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
            "publishTime": "",
            "likeCount": 0,
            "commentCount": 0,
            "collectCount": 0,
            "shareCount": 0,
            "authorName": work.get("channelTitle") or account_id,
            "followerCount": None,
            "coverUrl": cover,
        }

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
            result["cover"] = payload_data.get("cover") or payload_data.get("coverUrl") or payload_data.get("thumbnail")

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
