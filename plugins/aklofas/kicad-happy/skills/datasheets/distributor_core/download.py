"""Download transport: requests → urllib → playwright cascade with PDF sniffing,
manufacturer redirect normalisation (opt-in per provider), the Microchip alternative pattern.

Every URL, and every redirect, must be http or https on a public address (see
``url_problem``); a download stops at ``MAX_DOWNLOAD_BYTES`` or after
``DOWNLOAD_TIMEOUT_S`` seconds."""

import argparse
import errno
import http.client
import ipaddress
import math
import os
import socket
import ssl
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from distributor_core.manifest import DEFAULT_FILE_MODE


_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"


MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
DOWNLOAD_TIMEOUT_S = 120.0

_SOCKET_TIMEOUT_S = 20
_MAX_REDIRECTS = 5
_CHUNK_BYTES = 65536
_REDIRECT_CODES = (301, 302, 303, 307, 308)


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


_NETWORK_ERRNOS = {errno.ENETUNREACH, errno.EHOSTUNREACH, errno.ECONNREFUSED, errno.ECONNRESET,
                   errno.ETIMEDOUT}


def _local_failure(exc: BaseException) -> bool:
    """True for an OSError of this machine (a file the download could not write, a full disk),
    which ``is_transport_error`` would count as the network's."""
    network = (ConnectionError, TimeoutError, socket.gaierror, ssl.SSLError, urllib.error.URLError)
    if _requests is not None:
        network += (_requests.exceptions.RequestException,)
    return (isinstance(exc, OSError) and _http_status(exc) is None and not isinstance(exc, network)
            and exc.errno not in _NETWORK_ERRNOS)


class DownloadRefused(urllib.error.URLError):
    """A URL or a redirect the download policy does not allow."""


class DownloadRedirectLimit(DownloadRefused):
    """More than ``_MAX_REDIRECTS`` redirects: an answer from the server, not an outage. Unlike
    a refused hop it does not end the download; the next method is tried."""


class DownloadLimitExceeded(OSError):
    """A download larger than ``MAX_DOWNLOAD_BYTES`` or slower than ``DOWNLOAD_TIMEOUT_S``."""


def _resolve(host: str) -> list[str]:
    """The addresses ``host`` resolves to. The only DNS lookup in this module."""
    return [info[4][0] for info in socket.getaddrinfo(host, None)]


def _address_problem(text: str) -> str | None:
    try:
        ip = ipaddress.ip_address(text.split("%", 1)[0])
    except ValueError:
        return f"{text} is not an IP address"
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if not ip.is_global or ip.is_multicast:
        return f"{text} is not a public address"
    return None


def url_problem(url: str, *, allow_private: bool) -> str | None:
    """``None`` when ``url`` may be downloaded, else a short reason. Only http and https
    with a host; every address the host resolves to must be public unless
    ``allow_private``."""
    # Parsers disagree on where the host of such a URL ends (urlsplit and urllib3 split
    # ``http://a\\@b/`` differently), and a datasheet URL never needs credentials.
    if any(c == "\\" or c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url):
        return "a backslash, blank or control character in the URL"
    try:
        parts = urllib.parse.urlsplit(url)
        host = parts.hostname
    except ValueError:
        return "not a valid URL"
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        return f"scheme {scheme or '(none)'} is not http or https"
    if not host:
        return "no host"
    if "@" in parts.netloc:
        return "credentials in the URL"
    if "%" in parts.netloc:
        return "a percent-encoded host or port"
    if not parts.netloc.isascii():
        return "a non-ASCII host"
    if allow_private:
        return None
    try:
        addresses = [str(ipaddress.ip_address(host))]
    except ValueError:
        try:
            addresses = _resolve(host)
        except (OSError, UnicodeError) as exc:
            return f"{host} does not resolve ({type(exc).__name__})"
        if not addresses:
            return f"{host} does not resolve"
    for address in addresses:
        problem = _address_problem(address)
        if problem:
            return problem if address == host else f"{host}: {problem}"
    return None


def _allow_private_hosts() -> bool:
    """True only when the user's own ``~/.kicad-happy.json`` sets
    ``datasheets.allow_private_hosts`` to ``true``."""
    try:
        kicad_scripts = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "kicad", "scripts")
        if kicad_scripts not in sys.path:
            sys.path.insert(0, kicad_scripts)
        from kicad_core.project import load_user_config
    except Exception:
        return False
    datasheets = load_user_config().get("datasheets", {})
    return isinstance(datasheets, dict) and datasheets.get("allow_private_hosts") is True


def _positive_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number")
    if not (math.isfinite(value) and value > 0):
        raise argparse.ArgumentTypeError(f"{text!r} must be a number greater than 0")
    return value


def add_download_args(parser) -> None:
    """Add ``--max-download-mb`` and ``--download-timeout`` to ``parser``."""
    parser.add_argument("--max-download-mb", type=_positive_float, default=50.0, metavar="MB",
                        help="Stop a datasheet download larger than this (default: 50)")
    parser.add_argument("--download-timeout", type=_positive_float, default=120.0,
                        metavar="SECONDS",
                        help="Stop a datasheet download that takes longer than this "
                             "(default: 120)")


def apply_download_args(args) -> None:
    """Set the module's download limits from ``add_download_args`` values."""
    global MAX_DOWNLOAD_BYTES, DOWNLOAD_TIMEOUT_S
    MAX_DOWNLOAD_BYTES = int(args.max_download_mb * 1024 * 1024)
    DOWNLOAD_TIMEOUT_S = float(args.download_timeout)


# The policy of the download_pdf call running on this thread, read by the transports.
_call = threading.local()


def _deadline() -> float:
    deadline = getattr(_call, "deadline", None)
    return deadline if deadline is not None else time.monotonic() + DOWNLOAD_TIMEOUT_S


def _allow_private_now() -> bool:
    return bool(getattr(_call, "allow_private", False))


def _socket_timeout(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise DownloadLimitExceeded(f"took longer than {DOWNLOAD_TIMEOUT_S:g} s")
    return min(_SOCKET_TIMEOUT_S, remaining)


def _check_redirect(newurl: str) -> None:
    problem = url_problem(newurl, allow_private=_allow_private_now())
    if problem:
        raise DownloadRefused(f"redirect to {newurl}: {problem}")


def _copy_bounded(chunks, f, deadline: float) -> int:
    """Write ``chunks`` to ``f``; raise ``DownloadLimitExceeded`` past either limit."""
    total = 0
    for chunk in chunks:
        if not chunk:
            continue
        total += len(chunk)
        if total > MAX_DOWNLOAD_BYTES:
            raise DownloadLimitExceeded(f"larger than {MAX_DOWNLOAD_BYTES:,} bytes")
        if time.monotonic() > deadline:
            raise DownloadLimitExceeded(f"took longer than {DOWNLOAD_TIMEOUT_S:g} s")
        f.write(chunk)
    return total


def _find_socket(obj, depth: int = 0):
    """The socket under a response or connection object, if there is one."""
    if obj is None or depth > 6:
        return None
    if isinstance(obj, socket.socket):
        return obj
    for name in ("_sock", "sock", "raw", "fp", "_fp", "_connection"):
        found = _find_socket(getattr(obj, name, None), depth + 1)
        if found is not None:
            return found
    return None


def _shutdown(obj) -> None:
    sock = _find_socket(obj)
    if sock is not None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass


class _Watchdog:
    """Enforces the deadline from outside a blocked read: at the deadline every watched
    connection or response has its socket shut down, which ends a read that a server is
    feeding a byte at a time. Leaving the block after that raises
    ``DownloadLimitExceeded``."""

    def __init__(self, deadline: float):
        self.fired = False
        self._targets = []
        self._lock = threading.Lock()
        self._timer = threading.Timer(max(0.0, deadline - time.monotonic()), self._fire)
        self._timer.daemon = True

    def watch(self, obj) -> None:
        with self._lock:
            self._targets.append(obj)
            fired = self.fired
        if fired:
            _shutdown(obj)

    def _fire(self) -> None:
        with self._lock:
            self.fired = True
            targets = list(self._targets)
        for obj in targets:
            _shutdown(obj)

    def __enter__(self):
        _call.watchdog = self
        self._timer.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._timer.cancel()
        _call.watchdog = None
        if self.fired:
            raise DownloadLimitExceeded(f"took longer than {DOWNLOAD_TIMEOUT_S:g} s") from exc
        return False


def _watch_current(obj) -> None:
    watchdog = getattr(_call, "watchdog", None)
    if watchdog is not None:
        watchdog.watch(obj)


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


def _encode_spaces(url: str) -> str:
    """``url`` with each space after the host written as ``%20``, as KiCad Datasheet
    fields often hold them. A space in the scheme or host is left for the policy to
    refuse."""
    sep = url.find("://")
    if sep < 0:
        return url
    start = sep + 3
    end = min((i for i in (url.find(c, start) for c in "/?#") if i >= 0), default=len(url))
    return url[:end] + url[end:].replace(" ", "%20")


def download_pdf(url: str, output_path: str, *, resolve_redirects: bool = True) -> bool:
    """Download a PDF from a URL, trying multiple methods.

    Strategy:
    1. Try requests library (handles HTTP/2, all manufacturer sites)
    2. Fall back to Python urllib (HTTP/1.1 only — some sites may timeout)
    3. Fall back to a headless browser (playwright) when installed

    A URL the policy refuses (``url_problem``) is never fetched. A refused redirect or
    an exceeded limit ends the whole call: no other method is tried.

    Returns True if a valid PDF was downloaded. Each method writes to
    a uniquely named ``.part`` file beside ``output_path``, which replaces
    ``output_path`` only once it sniffs as a PDF, so a failed attempt never removes a
    file already there and a planted link is never written through.

    A method that fails in transport (``is_transport_error``, not a local file error) is
    recorded with ``note_transport_failure``, so the sync retries the part next run.
    """
    url = _encode_spaces(normalize_url(url, resolve_redirects=resolve_redirects))
    allow_private = _allow_private_hosts()
    problem = url_problem(url, allow_private=allow_private)
    if problem:
        print(f"Warning: download refused: {url}: {problem}", file=sys.stderr)
        return False

    fd, part_path = tempfile.mkstemp(
        dir=os.path.dirname(os.path.abspath(output_path)),
        prefix=os.path.basename(output_path) + ".", suffix=".part")
    os.close(fd)

    methods = []
    if _requests is not None:
        methods.append(("requests", _download_requests))
    methods.append(("urllib", _download_urllib))
    if _sync_playwright is not None:
        methods.append(("playwright", _download_playwright))

    # A refusal or an exceeded limit ends the call as permanent: it drops a transport failure an
    # earlier method of this call recorded, and keeps one recorded before the call.
    prior_failure = getattr(_transport, "failure", None)
    _call.deadline = time.monotonic() + DOWNLOAD_TIMEOUT_S
    _call.allow_private = allow_private
    try:
        for name, fn in methods:
            try:
                fetched = fn(url, part_path)
            except DownloadRedirectLimit:
                # Not an outage; a browser (cookies) may finish a loop that requests cannot
                fetched = False
            except DownloadRefused as exc:
                _transport.failure = prior_failure
                print(f"Warning: download refused: {url}: {exc.reason}", file=sys.stderr)
                return False
            except DownloadLimitExceeded as exc:
                _transport.failure = prior_failure
                print(f"Warning: download stopped: {url}: {exc}", file=sys.stderr)
                return False
            except Exception as exc:
                if not _local_failure(exc):
                    note_transport_failure(exc)
                fetched = False
            if fetched:
                try:
                    # Verify it's actually a PDF
                    with open(part_path, "rb") as f:
                        header = f.read(8)
                    if header.startswith(b"%PDF"):
                        os.chmod(part_path, DEFAULT_FILE_MODE)
                        os.replace(part_path, output_path)
                        size = os.path.getsize(output_path)
                        try:
                            print(f"Downloaded {size:,} bytes via {name}: {output_path}", file=sys.stderr)
                        except (OSError, UnicodeError, ValueError):
                            pass
                        return True
                    # Not a PDF (probably HTML error page or JS redirect)
                except OSError:
                    pass
            if os.path.exists(part_path):
                os.truncate(part_path, 0)
        return False
    finally:
        _call.deadline = None
        _call.allow_private = False
        try:
            os.remove(part_path)
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------------
# Download methods
# ---------------------------------------------------------------------------

def _get_before_deadline(url: str, deadline: float, **kwargs):
    """A ``requests`` GET on a worker thread, so the deadline also holds while a server sends the
    status line and headers, before there is a response whose socket can be watched. At the
    deadline the call is abandoned; a response that still arrives is closed by the worker."""
    box, lock = {}, threading.Lock()

    def run():
        try:
            with _requests.Session() as session:
                # Session.send reads a whole 3xx body even with allow_redirects=False;
                # _download_requests follows each hop itself.
                session.get_redirect_target = lambda resp: None
                resp = session.get(url, **kwargs)
        except BaseException as exc:
            with lock:
                box["exc"] = exc
            return
        with lock:
            if box.get("abandoned"):
                resp.close()
                return
            box["resp"] = resp

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(max(0.0, deadline - time.monotonic()))
    with lock:
        if not box:
            box["abandoned"] = True
            raise DownloadLimitExceeded(f"took longer than {DOWNLOAD_TIMEOUT_S:g} s")
    if "exc" in box:
        raise box["exc"]
    return box["resp"]


def _download_requests(url: str, output_path: str) -> bool:
    """Download using the requests library (handles HTTP/2, all manufacturers).
    Redirects are followed here, each one checked against the policy."""
    if _requests is None:
        return False
    deadline = _deadline()
    with _Watchdog(deadline) as watchdog:
        for _ in range(_MAX_REDIRECTS + 1):
            resp = _get_before_deadline(
                url,
                deadline,
                headers={"User-Agent": _USER_AGENT},
                timeout=_socket_timeout(deadline),
                allow_redirects=False,
                stream=True,
            )
            watchdog.watch(resp)
            try:
                location = resp.headers.get("Location")
                if resp.status_code in _REDIRECT_CODES and location:
                    url = urllib.parse.urljoin(url, location)
                    _check_redirect(url)
                    continue
                resp.raise_for_status()
                with open(output_path, "wb") as f:
                    total = _copy_bounded(resp.iter_content(_CHUNK_BYTES), f, deadline)
                return total > 0
            finally:
                resp.close()
    raise DownloadRedirectLimit(f"more than {_MAX_REDIRECTS} redirects")


class _CheckedRedirectHandler(urllib.request.HTTPRedirectHandler):
    max_redirections = _MAX_REDIRECTS

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _check_redirect(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


# No file:, ftp: or data: handler: only http(s), every redirect checked. The proxy handler
# keeps http_proxy/https_proxy working; the policy still checks the target URL.
class _WatchedHTTPConnection(http.client.HTTPConnection):
    def connect(self):
        super().connect()
        _watch_current(self.sock)


class _WatchedHTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        super().connect()
        _watch_current(self.sock)


class _WatchedHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(_WatchedHTTPConnection, req)


class _WatchedHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_WatchedHTTPSConnection, req, context=self._context)


_URLLIB_HANDLERS = [
    urllib.request.ProxyHandler,
    _WatchedHTTPHandler,
    _WatchedHTTPSHandler,
    urllib.request.HTTPDefaultErrorHandler,
    urllib.request.HTTPErrorProcessor,
    _CheckedRedirectHandler,
]


def _urllib_opener() -> urllib.request.OpenerDirector:
    opener = urllib.request.OpenerDirector()
    for handler in _URLLIB_HANDLERS:
        opener.add_handler(handler())
    return opener


def _download_urllib(url: str, output_path: str) -> bool:
    """Download using Python urllib (fallback, HTTP/1.1 only)."""
    deadline = _deadline()
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with _Watchdog(deadline) as watchdog:
        with _urllib_opener().open(req, timeout=_socket_timeout(deadline)) as resp:
            watchdog.watch(resp)
            with open(output_path, "wb") as f:
                total = _copy_bounded(iter(lambda: resp.read(_CHUNK_BYTES), b""), f, deadline)
    return total > 0


def _ms_left(deadline: float, cap_ms: float) -> float:
    return max(1.0, min(cap_ms, (deadline - time.monotonic()) * 1000))


def _policy_route(allow_private: bool, deadline: float):
    """A ``page.route`` handler for every browser request. The browser does not route
    the hops of a redirect, so the handler fetches each hop itself with redirects off,
    checks it against the policy, and fulfils the request with the final answer. A
    refused hop, too many hops, an answer over the size limit or any error aborts it."""
    def handle(route):
        try:
            url = route.request.url
            for _ in range(_MAX_REDIRECTS + 1):
                if url_problem(url, allow_private=allow_private):
                    break
                response = route.fetch(url=url, max_redirects=0,
                                       timeout=_ms_left(deadline, 30000))
                location = response.headers.get("location")
                if response.status in _REDIRECT_CODES and location:
                    url = urllib.parse.urljoin(url, location)
                    continue
                length = response.headers.get("content-length", "")
                if length.isdigit() and int(length) > MAX_DOWNLOAD_BYTES:
                    break
                route.fulfill(response=response)
                return
            route.abort("blockedbyclient")
        except Exception:
            try:
                route.abort("failed")
            except Exception:
                pass
    return handle


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
            deadline = _deadline()
            page.route("**/*", _policy_route(_allow_private_now(), deadline))
            # First try: expect a download event (some sites trigger JS downloads)
            try:
                with page.expect_download(timeout=_ms_left(deadline, 15000)) as dl_info:
                    page.goto(url, timeout=_ms_left(deadline, 15000),
                              wait_until="domcontentloaded")
                download = dl_info.value
                download.save_as(output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) > MAX_DOWNLOAD_BYTES:
                    os.remove(output_path)
                    return False
                return os.path.exists(output_path) and os.path.getsize(output_path) > 0
            except Exception:
                pass

            # Second try: navigate and read the response body directly
            resp = page.goto(url, timeout=_ms_left(deadline, 20000), wait_until="domcontentloaded")
            if resp is None:
                return False
            body = resp.body()
            if body and len(body) <= MAX_DOWNLOAD_BYTES and body[:4] == b"%PDF":
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
