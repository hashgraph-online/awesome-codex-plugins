"""Shared constants, privacy sanitization, and report defaults."""

import re
import unicodedata

DEFAULT_BROWSER_THRESHOLD = 120.0
MAX_TITLE_LENGTH = 160
URL_PATTERN = re.compile(
    r"(?:https?://|www\.|\b[\w.-]+\.(?:com|net|org|cn|io|app|dev)\b)", re.IGNORECASE
)
BROWSER_APP_PATTERN = re.compile(
    r"(?:chrome|firefox|safari|edge|brave|arc|browser|浏览器)", re.IGNORECASE
)
BROWSER_TITLE_SUFFIXES = (
    re.compile(r"\s+-\s+Google Chrome(?:\s+-\s+.+)?$", re.IGNORECASE),
    re.compile(r"\s+-\s+(?:Doubao Browser|豆包浏览器)$", re.IGNORECASE),
)
MEMORY_SUFFIX = re.compile(
    r"\s+-\s+内存用量高\s+-\s+[\d.,]+\s*(?:MB|GB)", re.IGNORECASE
)


def safe_title(title):
    """Remove URL-like titles and bound the remaining sensitive context."""
    title = " ".join((title or "").split())
    return "[URL omitted]" if URL_PATTERN.search(title) else title[:MAX_TITLE_LENGTH]


def normalize_title(title):
    """Normalize watcher noise before grouping or classifying titles."""
    title = unicodedata.normalize("NFKC", title or "")
    title = "".join(
        character for character in title if unicodedata.category(character) != "Cf"
    )
    title = MEMORY_SUFFIX.sub("", " ".join(title.split()))
    for suffix in BROWSER_TITLE_SUFFIXES:
        title = suffix.sub("", title)
    return safe_title(title) or "(untitled)"


def format_duration(value):
    total = round(value)
    hours, remainder = divmod(total, 3600)
    minutes, seconds_value = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds_value:02}"


def safe_cell(value):
    """Prevent spreadsheet formula evaluation when a cell is pasted/imported."""
    text = str(value)
    return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text
