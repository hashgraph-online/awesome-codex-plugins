"""Shared helpers for the scientific-slides image-generation scripts.

Holds the pieces that the schematic and slide-image entry points have in common:
credential lookup, the minimal subprocess environment, quality-review parsing,
and an OpenRouter client base class. Only the standard library is required at
import time; ``requests`` is imported lazily by the client and checked up front
with ``require_requests``.
"""

import base64
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, NamedTuple, Optional

DATA_IMAGE_PREFIX = "data:image"

# Variables forwarded to the generation subprocess. The child needs the
# OpenRouter credential; the rest keep networking, TLS, and locale working.
# Copying the whole parent environment instead would hand the child every
# unrelated secret that happens to be exported in the calling shell.
FORWARDED_ENV_VARS = (
    "PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "PYTHONPATH",
    "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
    "http_proxy", "https_proxy", "no_proxy",
    "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE",
    # Windows needs these for sockets, temp files, and interpreter startup.
    "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT",
    "APPDATA", "LOCALAPPDATA", "USERPROFILE", "TEMP", "TMP",
)


def require_requests() -> Any:
    """Import and return ``requests``, exiting with a clear message when absent."""
    try:
        import requests
    except ImportError:
        print("Error: requests library not found. Install with: uv pip install requests")
        sys.exit(1)
    return requests


def _key_from_env_file(env_file: Path) -> Optional[str]:
    """Return OPENROUTER_API_KEY from a .env file, or None when absent or unreadable."""
    if not env_file.is_file():
        return None
    try:
        content = env_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for raw in content.splitlines():
        line = raw.strip()
        if line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        if name.strip() == "OPENROUTER_API_KEY":
            value = value.strip().strip('"').strip("'")
            if value:
                return value
    return None


def resolve_api_key(explicit: Optional[str] = None) -> Optional[str]:
    """Resolve the OpenRouter key from --api-key, the environment, then any .env file.

    The .env scan walks up from the working directory and finally checks the
    script's own directory, so running from anywhere inside a project picks up
    the key at its root. Only the standard library is used: python-dotenv is a
    common omission, and a missing optional dependency should not read as a
    missing credential.
    """
    if explicit:
        return explicit

    from_env = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if from_env:
        return from_env

    cwd = Path.cwd()
    for directory in [cwd, *cwd.parents, Path(__file__).resolve().parent]:
        value = _key_from_env_file(directory / ".env")
        if value:
            return value

    return None


def build_subprocess_env(api_key: Optional[str]) -> Dict[str, str]:
    """Return a minimal environment for the AI generation subprocess."""
    env = {name: os.environ[name] for name in FORWARDED_ENV_VARS if name in os.environ}
    if api_key:
        env["OPENROUTER_API_KEY"] = api_key
    return env


class ReviewResult(NamedTuple):
    """The outcome of one quality review.

    A named tuple rather than a bare tuple because the review has several
    failure modes -- the model returns no choices, the request raises, the
    answer arrives in an unexpected shape -- and each of them used to be a
    chance to return the wrong number of values to the caller.

    `score` is None whenever no usable number was parsed, and `reviewed` is
    False whenever the review never produced an answer at all. Neither case
    invents a score: an image whose quality was not measured is reported as
    unmeasured, not as passing.
    """

    critique: str
    score: Optional[float]
    needs_improvement: bool
    reviewed: bool
    error: Optional[str] = None


# Markdown decoration the reviewer routinely wraps its answer in. Gemini writes
# "**SCORE:** 8.5" far more often than the bare "SCORE: 8.5" the rubric asks
# for, and a pattern that does not allow for it silently scores every image
# at whatever the default happens to be.
_MARKUP = re.compile(r"[*_`#]")

_SCORE_PATTERN = re.compile(r"\bSCORE\s*:?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
_LOOSE_SCORE_PATTERN = re.compile(
    r"(?:score|rating|quality)\s*[:\s]\s*(\d+(?:\.\d+)?)\s*(?:/\s*10)?", re.IGNORECASE
)
# The underscore is optional because normalization strips it out of
# NEEDS_IMPROVEMENT along with the surrounding markdown.
_VERDICT_PATTERN = re.compile(
    r"^\s*VERDICT\s*:?\s*(ACCEPTABLE|NEEDS[_ ]?IMPROVEMENT)", re.IGNORECASE | re.MULTILINE
)


def _normalize_review_text(text: str) -> str:
    """Strip markdown decoration so the rubric's fields can be found."""
    return _MARKUP.sub("", text or "")


def parse_score(text: str) -> Optional[float]:
    """Return the reviewer's 0-10 score, or None when there isn't a usable one.

    None rather than a default: a fabricated score is indistinguishable from a
    real one once it reaches the review log, and a default near the middle of
    the range quietly passes lenient thresholds while failing strict ones.
    """
    normalized = _normalize_review_text(text)
    match = _SCORE_PATTERN.search(normalized) or _LOOSE_SCORE_PATTERN.search(normalized)
    if not match:
        return None
    score = float(match.group(1))
    # A number outside the rubric's range means something other than the score
    # was matched -- a count, a percentage, an iteration number.
    return score if 0.0 <= score <= 10.0 else None


def parse_verdict(text: str) -> Optional[str]:
    """Return ACCEPTABLE / NEEDS_IMPROVEMENT from the verdict line, or None.

    Anchored to the start of a line. The rubric prompt spells out both tokens
    when it explains the response format, so a reviewer that echoes those
    instructions back would fail a perfectly good image under a plain
    substring search.
    """
    match = _VERDICT_PATTERN.search(_normalize_review_text(text))
    if not match:
        return None
    verdict = match.group(1).upper().replace(" ", "").replace("_", "")
    return "NEEDS_IMPROVEMENT" if verdict == "NEEDSIMPROVEMENT" else "ACCEPTABLE"


def _strip_whitespace(value: str) -> str:
    """Remove newlines, carriage returns and spaces from a base64 payload."""
    return value.replace("\n", "").replace("\r", "").replace(" ", "")


def _image_url_of(block: Dict[str, Any]) -> Any:
    """Return the URL string of an ``image_url`` content block."""
    url = block.get("image_url", {})
    if isinstance(url, dict):
        url = url.get("url", "")
    return url


def _image_from_images_field(message: Dict[str, Any], log: Callable[[str], None]) -> Optional[bytes]:
    """Decode the first image in the message's ``images`` field, if present."""
    images = message.get("images", [])
    if not (images and len(images) > 0):
        return None
    log(f"Found {len(images)} image(s) in 'images' field")
    first_image = images[0]
    if not isinstance(first_image, dict) or first_image.get("type") != "image_url":
        return None
    url = _image_url_of(first_image)
    if url and url.startswith(DATA_IMAGE_PREFIX) and "," in url:
        base64_str = _strip_whitespace(url.split(",", 1)[1])
        log(f"Extracted base64 data (length: {len(base64_str)})")
        return base64.b64decode(base64_str)
    return None


def _image_from_content_string(content: str, log: Callable[[str], None]) -> Optional[bytes]:
    """Decode an inline ``data:image`` URL embedded in a text content string."""
    match = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=\n\r]+)', content, re.DOTALL)
    if not match:
        return None
    base64_str = _strip_whitespace(match.group(1))
    log(f"Found image in content field (length: {len(base64_str)})")
    return base64.b64decode(base64_str)


def _image_from_content_blocks(content: List[Any], log: Callable[[str], None]) -> Optional[bytes]:
    """Decode the first ``image_url`` block in a list-valued content field."""
    for i, block in enumerate(content):
        if isinstance(block, dict) and block.get("type") == "image_url":
            url = _image_url_of(block)
            if url and url.startswith(DATA_IMAGE_PREFIX) and "," in url:
                base64_str = _strip_whitespace(url.split(",", 1)[1])
                log(f"Found image in content block {i}")
                return base64.b64decode(base64_str)
    return None


def extract_image_from_response(
    response: Dict[str, Any],
    log: Callable[[str], None],
    verbose_details: bool = False,
) -> Optional[bytes]:
    """Extract the base64-encoded image from an API response, or None if absent.

    Images normally arrive in the message's ``images`` field; the ``content``
    field is checked as a fallback for other models or future changes. When
    ``verbose_details`` is true, extra diagnostics are emitted.
    """
    try:
        choices = response.get("choices", [])
        if not choices:
            log("No choices in response")
            return None

        message = choices[0].get("message", {})
        found = _image_from_images_field(message, log)
        if found is not None:
            return found

        content = message.get("content", "")
        if verbose_details:
            log(f"Content type: {type(content)}, length: {len(str(content))}")
        if isinstance(content, str) and DATA_IMAGE_PREFIX in content:
            found = _image_from_content_string(content, log)
            if found is not None:
                return found
        if isinstance(content, list):
            found = _image_from_content_blocks(content, log)
            if found is not None:
                return found

        log("No image data found in response")
        return None
    except Exception as e:
        log(f"Error extracting image: {str(e)}")
        if verbose_details:
            traceback.print_exc()
        return None


def _review_text(message: Dict[str, Any]) -> Any:
    """Return the review text from a message, falling back to its reasoning field."""
    content = message.get("content", "")

    # Some models put their analysis in a separate reasoning field
    reasoning = message.get("reasoning", "")
    if reasoning and not content:
        content = reasoning

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        content = "\n".join(text_parts)
    return content


def interpret_review_response(
    response: Dict[str, Any],
    threshold: float,
    log: Callable[[str], None],
    log_verdict: bool = False,
) -> ReviewResult:
    """Turn a review-model response into a ReviewResult without inventing a score."""
    choices = response.get("choices", [])
    if not choices:
        # A normal enough outcome -- a rate limit, a content filter, a
        # provider hiccup. The image itself is fine; only its review is
        # missing, and saying so beats inventing a score.
        reason = "the review model returned no choices"
        log(f"⚠ Review unavailable: {reason}")
        return ReviewResult(
            f"Review unavailable: {reason}.",
            None, False, reviewed=False, error=reason,
        )

    content = _review_text(choices[0].get("message", {}))

    score = parse_score(content)
    verdict = parse_verdict(content)

    if score is None and verdict is None:
        reason = "no score or verdict found in the review"
        log(f"⚠ Review unusable: {reason}")
        return ReviewResult(
            content if content else f"Review unusable: {reason}.",
            None, False, reviewed=True, error=reason,
        )

    needs_improvement = verdict == "NEEDS_IMPROVEMENT" or (
        score is not None and score < threshold
    )

    shown = f"{score}/10" if score is not None else "not stated"
    log(f"✓ Review complete (Score: {shown}, Threshold: {threshold}/10)")
    if log_verdict:
        log(f"  Verdict: {'Needs improvement' if needs_improvement else 'Acceptable'}")

    return ReviewResult(
        content if content else "Review returned no text",
        score,
        needs_improvement,
        reviewed=True,
        error=None if score is not None else "no score found in the review",
    )


class OpenRouterImageClient:
    """Base class holding the OpenRouter plumbing shared by the generators.

    Subclasses set ``X_TITLE`` and may enable ``VERBOSE_EXTRACT_DETAILS`` to
    keep their extra diagnostics when extracting images in verbose mode.
    """

    X_TITLE = "Scientific Image Generator"
    VERBOSE_EXTRACT_DETAILS = False

    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        """Resolve the API key (argument, environment, then .env) and set model slugs."""
        self.api_key = resolve_api_key(api_key)

        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. Please either:\n"
                "  1. Set the OPENROUTER_API_KEY environment variable\n"
                "  2. Add OPENROUTER_API_KEY to your .env file\n"
                "  3. Pass api_key parameter to the constructor\n"
                "Get your API key from: https://openrouter.ai/keys"
            )

        self.verbose = verbose
        self._last_error = None
        self.base_url = "https://openrouter.ai/api/v1"
        # An image-output model. The slug must support image output; a text-only
        # chat model is rejected with "No endpoints found that support the
        # requested output modalities".
        # https://openrouter.ai/google/gemini-3.1-flash-image
        self.image_model = "google/gemini-3.1-flash-image"
        # Gemini 3.6 Flash for quality review - reads the image, answers in text
        self.review_model = "google/gemini-3.7-flash"

    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def _make_request(self, model: str, messages: List[Dict[str, Any]],
                      modalities: Optional[List[str]] = None) -> Dict[str, Any]:
        """Make a request to the OpenRouter chat-completions API and return its JSON."""
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/scientific-writer",
            "X-Title": self.X_TITLE
        }

        payload = {
            "model": model,
            "messages": messages
        }

        if modalities:
            payload["modalities"] = modalities

        self._log(f"Making request to {model}...")

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )

            try:
                response_json = response.json()
            except json.JSONDecodeError:
                response_json = {"raw_text": response.text[:500]}

            if response.status_code != 200:
                error_detail = response_json.get("error", response_json)
                self._log(f"HTTP {response.status_code}: {error_detail}")
                raise RuntimeError(f"API request failed (HTTP {response.status_code}): {error_detail}")

            return response_json
        except requests.exceptions.Timeout:
            raise RuntimeError("API request timed out after 120 seconds")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {str(e)}")

    def _extract_image_from_response(self, response: Dict[str, Any]) -> Optional[bytes]:
        """Extract base64-encoded image from API response."""
        return extract_image_from_response(
            response,
            self._log,
            verbose_details=self.VERBOSE_EXTRACT_DETAILS and self.verbose,
        )

    def _image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 data URL."""
        with open(image_path, "rb") as f:
            image_data = f.read()

        ext = Path(image_path).suffix.lower()
        mime_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }.get(ext, "image/png")

        base64_data = base64.b64encode(image_data).decode("utf-8")
        return f"data:{mime_type};base64,{base64_data}"

    def _request_review(
        self,
        messages: List[Dict[str, Any]],
        threshold: float,
        log_verdict: bool = False,
    ) -> ReviewResult:
        """Send a review request and interpret the answer; a failure is never a pass."""
        try:
            response = self._make_request(model=self.review_model, messages=messages)
            return interpret_review_response(response, threshold, self._log, log_verdict)
        except Exception as e:
            # A failed review must not fail the run -- the image is already
            # generated and saved -- but it must not read as a pass either.
            self._log(f"⚠ Review failed: {str(e)}")
            return ReviewResult(
                f"Review failed: {str(e)}",
                None, False, reviewed=False, error=str(e),
            )
