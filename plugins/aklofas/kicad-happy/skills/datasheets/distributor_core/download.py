"""Download transport: requests → urllib → playwright cascade with PDF sniffing,
manufacturer redirect normalisation (opt-in per provider), the Microchip alternative pattern."""

import os
import shutil
import threading
import urllib.error
import urllib.parse
import urllib.request


_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"


# Try to import optional dependencies; graceful fallback if not installed
try:
    import requests as _requests
except ImportError:
    _requests = None


try:
    from playwright.sync_api import sync_playwright as _sync_playwright
except ImportError:
    _sync_playwright = None


_transport = threading.local()


_ACCESS_REFUSED = (401, 403)


def _http_status(exc: BaseException):
    status = getattr(exc, "code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    return status if isinstance(status, int) else None


def is_transport_error(exc: BaseException) -> bool:
    """True for a failure of the network rather than an answer from it: a timeout, a refused
    or reset connection, a DNS failure, an HTTP 429 (rate limit) or 5xx. Any other HTTP 4xx
    is an answer."""
    status = _http_status(exc)
    if status is not None:
        return status == 429 or status >= 500
    return isinstance(exc, OSError)


def note_transport_failure(exc: BaseException) -> None:
    """Record, for this thread, that a distributor search failed without an answer: in
    transport (see ``is_transport_error``) or refused access (HTTP 401/403). The sync driver
    reads the message with ``take_transport_failure``."""
    status = _http_status(exc)
    if is_transport_error(exc):
        _transport.failure = f"network failure, retried next run: {type(exc).__name__}: {exc}"
    elif status in _ACCESS_REFUSED:
        _transport.failure = (f"access refused (HTTP {status}), check the API credentials: "
                              f"{type(exc).__name__}: {exc}")


def take_transport_failure() -> str | None:
    """Return and clear this thread's recorded failure message."""
    failure = getattr(_transport, "failure", None)
    _transport.failure = None
    return failure


def normalize_url(url: str, *, resolve_redirects: bool = True) -> str:
    """Convert manufacturer-specific redirect URLs to direct PDF URLs.

    DigiKey's DatasheetUrl field often points to manufacturer redirect pages
    rather than direct PDFs. This function extracts the actual PDF URL.
    """
    # Protocol-relative URLs from DigiKey (//mm.digikey.com/...)
    if url.startswith("//"):
        url = "https:" + url

    if not resolve_redirects:
        return url

    # TI redirect: extract the gotoUrl parameter which contains the direct link
    if "ti.com/general/docs/suppproductinfo" in url:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        goto = params.get("gotoUrl", [""])[0]
        if goto:
            return goto

    # Microchip redirect: extract the actual URL from the redirect wrapper
    if "microchip.com/filehandler/redirect" in url.lower():
        idx = url.find("?")
        if idx >= 0:
            return url[idx + 1:]

    return url


def download_pdf(url: str, output_path: str, *, resolve_redirects: bool = True) -> bool:
    """Download a PDF from a URL, trying multiple methods.

    Strategy:
    1. Try requests library (handles HTTP/2, redirects, all manufacturer sites)
    2. Fall back to Python urllib (HTTP/1.1 only — some sites may timeout)

    Returns True if a valid PDF was downloaded. Each method writes to
    ``<output_path>.part``, which replaces ``output_path`` only once it sniffs
    as a PDF, so a failed attempt never removes a file already there.
    """
    url = normalize_url(url, resolve_redirects=resolve_redirects)
    part_path = output_path + ".part"

    methods = []
    if _requests is not None:
        methods.append(("requests", _download_requests))
    methods.append(("urllib", _download_urllib))
    if _sync_playwright is not None:
        methods.append(("playwright", _download_playwright))

    for name, fn in methods:
        try:
            if fn(url, part_path):
                # Verify it's actually a PDF
                with open(part_path, "rb") as f:
                    header = f.read(8)
                if header.startswith(b"%PDF"):
                    os.replace(part_path, output_path)
                    size = os.path.getsize(output_path)
                    print(f"Downloaded {size:,} bytes via {name}: {output_path}")
                    return True
                # Not a PDF (probably HTML error page or JS redirect)
        except Exception:
            pass
        if os.path.exists(part_path):
            os.remove(part_path)

    return False


# ---------------------------------------------------------------------------
# Download methods
# ---------------------------------------------------------------------------

def _download_requests(url: str, output_path: str) -> bool:
    """Download using the requests library (handles HTTP/2, all manufacturers)."""
    if _requests is None:
        return False
    resp = _requests.get(
        url,
        headers={"User-Agent": _USER_AGENT},
        timeout=20,
        allow_redirects=True,
    )
    resp.raise_for_status()
    if len(resp.content) == 0:
        return False
    with open(output_path, "wb") as f:
        f.write(resp.content)
    return True


def _download_urllib(url: str, output_path: str) -> bool:
    """Download using Python urllib (fallback, HTTP/1.1 only)."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        with open(output_path, "wb") as f:
            shutil.copyfileobj(resp, f)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 0


def _download_playwright(url: str, output_path: str) -> bool:
    """Download using Playwright headless browser.

    Last-resort fallback for sites that require JavaScript execution
    (Broadcom doc viewer, Espressif, etc.). Handles two patterns:
    1. Page triggers a file download (intercepted via expect_download)
    2. Page navigates directly to a PDF (read from response body)
    """
    with _sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # First try: expect a download event (some sites trigger JS downloads)
            try:
                with page.expect_download(timeout=15000) as dl_info:
                    page.goto(url, timeout=15000, wait_until="domcontentloaded")
                download = dl_info.value
                download.save_as(output_path)
                return os.path.exists(output_path) and os.path.getsize(output_path) > 0
            except Exception:
                pass

            # Second try: navigate and read the response body directly
            resp = page.goto(url, timeout=20000, wait_until="domcontentloaded")
            if resp is None:
                return False
            body = resp.body()
            if body and body[:4] == b"%PDF":
                with open(output_path, "wb") as f:
                    f.write(body)
                return True
            return False
        finally:
            page.close()
            browser.close()


def try_alternative_sources(mpn: str, output_path: str) -> bool:
    """Try downloading from known mirror/alternative datasheet sources.

    When the primary manufacturer URL fails (Microchip 403, ST timeout),
    try alternative sources that host the same datasheets.
    """
    alternatives = []
    mpn_upper = mpn.upper()

    # Microchip: try direct product document URL
    if any(x in mpn_upper for x in ("ATMEGA", "ATTINY", "PIC", "SAMD", "SAM")):
        alternatives.append(
            f"https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/{mpn}-DataSheet.pdf"
        )

    for alt_url in alternatives:
        if download_pdf(alt_url, output_path):
            return True

    return False
