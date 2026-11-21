#!/usr/bin/env python3
"""AgentAvow PreToolUse gate — checks each MCP tool call against the grade on file.

Runs before Claude Code calls an MCP tool (tool names `mcp__<server>__<tool>`). It
reads the verdict the SessionStart pre-check (agentavow_precheck.py) stored for that
server in ~/.cache/agentavow/scanned.json and decides:
  • deny  — the server's answer is "Do not connect" (a critical finding, a planted
            credential leaving the sandbox, a known-malicious package), or its grade is
            in the "blocked" tier (score 0-10). The reason leads with the answer and
            names the score and the report. The threshold is adjustable (below).
            The person (never Claude) can allow that one server after reviewing it:
            a line "<server name> <graded URL or package> <code>" in
            ~/.cache/agentavow/allowed-servers.txt. The code is a confirmation code
            shown ONLY to the person, in the refusal's systemMessage; Claude's copy
            of the refusal never carries it, so a line Claude writes does not count,
            however it reaches the file. Only an exact line for that server with its
            code counts; there is no pattern and no allow-everything. An allowed
            server's tools run (with one note per session), and a changed
            definition still asks. Where a surface does not show that message (the
            VS Code extension, for one), the person runs this script in their own
            terminal with `--allow-line <server name>` (below).
  • ask   — any MCP tool call whose input names AgentAvow's own files (the cache
            folder, the allow list, the allow key): only the person may read or
            change them.
  • ask   — a remote (HTTP) server now serves a definition for this tool that differs
            from the one AgentAvow graded (or a tool the grade never saw). The gate
            re-fetches `tools/list` from the server itself, at most once per server
            per recheck window, and recomputes the signed per-tool digest with the
            same derivation the attestation uses (agentavow.mcp-tool-definition.v1:
            RFC 8785 canonical JSON over name, title, description, inputSchema,
            outputSchema, annotations, numbers read as JSON.parse reads them;
            SHA-256). No call to AgentAvow is made. A definition holding text the
            digest cannot carry also asks: its digest proves nothing.
  • allow — everything else: an unknown server, no grade on file, a stdio server
            (verdict-only; it serves no definition to re-fetch), any network error
            or timeout, any definition the gate cannot hash.

Settings (environment, all OPTIONAL, read only, never sent anywhere):
  AGENTAVOW_GATE=off                   turn the gate off entirely (default: on)
  AGENTAVOW_GATE_DENY_BELOW            deny when the server's score is below this:
                                       a number 0-100, or a tier name (restricted,
                                       minimal, standard, trusted, verified) meaning
                                       that tier's floor; "off" never denies (not
                                       even on "Do not connect").
                                       Default: deny on "Do not connect" and on the
                                       "blocked" tier.
  AGENTAVOW_GATE_RECHECK_SECONDS       how often a remote server's tools/list is
                                       re-fetched for drift (default 900).

What leaves your machine: for a remote server with a grade on file, one short
`initialize` + `tools/list` exchange with THAT server, over the URL in your config
(user:password@ and #fragment removed). If the config has an Authorization header
for that server, it is sent to that server only, as Claude Code itself would; it is
never written to the cache or printed. Nothing is sent to AgentAvow, so the
install ID the other two hooks send (see agentavow_precheck.py) is never sent from here.

Design guarantees (deliberate):
  • FAIL-OPEN — any error, timeout, or unexpected shape means allow, silently.
  • NEVER BLOCKS ON DRIFT — drift asks; only "Do not connect" or a blocked-tier grade
    denies, unless you allowed that server. "Review before you connect" never prompts here.
  • ONE SHORT BUDGET — the whole run stays under the hook's 8-second timeout.

Allow line from a terminal (for the person, not for Claude):
  python3 agentavow_pretool_gate.py --allow-line <server name>
prints the exact allow line, code included, for a server with a grade on file. It
prints it only when both its input and its output are a terminal: run from Claude's
Bash tool (or anything else that captures the output), it refuses and prints no code.

In Codex (which runs this same plugin's hooks; tool names are the same
`mcp__<server>__<tool>`): a PreToolUse hook there cannot ask, only deny. So where
Claude Code asks (a changed definition, a call naming AgentAvow's own files), Codex
gets a deny whose reason says what was found and how to go ahead anyway, and the
servers are looked up in Codex's config.toml. Do not connect is a deny in both. All
the notes stay notes. Claude Code's output is unchanged
(tests/test_agentavow_claude_pins.py).

Install / test: https://agentavow.com/docs/auto-scan-claude-code
"""
from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import importlib.util
import io
import ipaddress
import json
import os
import pathlib
import re
import secrets
import shlex
import sys
import time
import urllib.parse
import urllib.request

__version__ = "0.1.45"

CACHE = pathlib.Path.home() / ".cache" / "agentavow" / "scanned.json"
META_KEY = "_agentavow"  # cache entry holding hook state; never a server name
# The person's own "I've reviewed this, allow it" list, beside the cache: one server per
# line, "<server name> <graded URL or package>", exactly as the refusal message gives it.
ALLOW_FILE_NAME = "allowed-servers.txt"
# The random key the confirmation codes on allow lines are derived from (HMAC-SHA256).
# The gate creates it (0600) the first time it refuses a server. It never leaves this
# machine and is never printed.
ALLOW_KEY_NAME = "allow.key"
ALLOW_CODE_LABEL = b"agentavow-allow-v1"

# The per-tool digest, exactly as the attestation signs it
# (docs/standards/tool-manifest-digest-vectors-v1).
PROFILE = "agentavow.mcp-tool-definition.v1"
DIGEST_FIELDS = ("name", "title", "description", "inputSchema", "outputSchema", "annotations")
_MAX_SAFE_INT = 2**53 - 1
_MAX_KEY_NAME = 128
_MAX_TOOL_DIGESTS = 500  # beyond this the signed map is folded; the gate cannot compare

DEFAULT_RECHECK_SECONDS = 900
REQUEST_TIMEOUT = 2.5  # per request to the server
BUDGET = 6.0  # for the whole tools/list fetch; the hook times out at 8

# Score floor of each tier (src/api/public_scan_router.py TRUST_TIERS).
TIER_FLOORS = {
    "blocked": 0, "restricted": 11, "minimal": 31, "standard": 51, "trusted": 81, "verified": 96,
}


# The three headline phrases (src/trust_tiers.py DECISIONS; pinned by tests).
DECISION_PHRASES = {
    "safe": "Safe to connect",
    "review": "Review before you connect",
    "do_not_connect": "Do not connect",
}


class UnhashableError(Exception):
    """A value RFC 8785 cannot represent: NaN or Infinity, an integer beyond 2^53
    handed to jcs() directly, a lone surrogate, a non-string key, a value that is not
    JSON. tool_digest() never raises it: such a definition gets the issuer's
    distinct-label digest instead."""


# ── RFC 8785 (JCS), byte-identical to the issuer's (rfc8785 + _as_ijson) ─────


def _ijson(value: object) -> object:
    """Read numbers the way ECMAScript JSON.parse does: every number is an IEEE 754
    double. An integer outside the safe range becomes its double (2^53 + 1 reads as
    2^53), as src.scanner.mcp_scan._as_ijson does before it signs."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value if -_MAX_SAFE_INT <= value <= _MAX_SAFE_INT else float(value)
    if isinstance(value, dict):
        return {str(k): _ijson(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_ijson(v) for v in value]
    return value


def _es_number(value: float) -> str:
    """ECMAScript Number::toString of a double, as RFC 8785 section 3.2.2.3 requires:
    the shortest digits that round-trip (Python's repr has the same digits), laid out
    as integer, decimal or exponent form by ES rules. -0 prints as 0."""
    if value != value or value in (float("inf"), float("-inf")):
        raise UnhashableError("NaN or Infinity")
    if value == 0:
        return "0"
    if value < 0:
        return "-" + _es_number(-value)
    mantissa, _, exp = repr(value).partition("e")
    whole, _, frac = mantissa.partition(".")
    raw = whole + frac
    significant = raw.lstrip("0")
    point = len(whole) - (len(raw) - len(significant)) + int(exp or 0)
    digits = significant.rstrip("0")
    k = len(digits)
    if k <= point <= 21:
        return digits + "0" * (point - k)
    if 0 < point <= 21:
        return digits[:point] + "." + digits[point:]
    if -6 < point <= 0:
        return "0." + "0" * -point + digits
    e = point - 1
    return (digits[0] + ("." + digits[1:] if k > 1 else "")
            + "e" + ("+" if e > 0 else "-") + str(abs(e)))


def _jcs_str(value: str) -> str:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise UnhashableError("lone surrogate") from None
    return json.dumps(value, ensure_ascii=False)


def jcs(value: object) -> str:
    """Canonical JSON per RFC 8785: keys sorted by UTF-16 code units, no whitespace,
    strings escaped as JSON.stringify does, non-ASCII kept literal, numbers as
    ECMAScript prints them. Accepts and refuses exactly what the issuer's rfc8785
    library does: an integer beyond 2^53 raises (tool_digest reads it as a double
    first), as do NaN, Infinity, lone surrogates and non-JSON values."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        if abs(value) > _MAX_SAFE_INT:
            raise UnhashableError("integer beyond 2^53")
        return str(int(value))
    if isinstance(value, str):
        return _jcs_str(value)
    if isinstance(value, float):
        return _es_number(float(value))
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(jcs(v) for v in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise UnhashableError("non-string key")
        try:
            keys = sorted(value, key=lambda k: k.encode("utf-16-be"))
        except UnicodeEncodeError:
            raise UnhashableError("lone surrogate") from None
        return "{" + ",".join(_jcs_str(k) + ":" + jcs(value[k]) for k in keys) + "}"
    raise UnhashableError(type(value).__name__)


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def tool_key(name: str) -> str:
    """`tool:<name>`: everything outside printable ASCII, plus % and =, is
    percent-encoded as UTF-8 bytes; an overlong key is cut and suffixed."""
    out = []
    for ch in name:
        if "\x21" <= ch <= "\x7e" and ch not in "%=":
            out.append(ch)
        else:
            out.extend(f"%{b:02X}" for b in ch.encode("utf-8", "surrogatepass"))
    enc = "".join(out)
    if len(enc) > _MAX_KEY_NAME:
        enc = enc[:96] + "~" + hashlib.sha256(
            name.encode("utf-8", "surrogatepass")).hexdigest()[:16]
    return "tool:" + enc


def tool_digest(tool: dict) -> str:
    """`sha256:<hex>` over JCS({"profile": PROFILE, "tool": <restricted definition>}),
    exactly as src.scanner.mcp_scan.tool_definition_digest signs it. A missing or
    null field is omitted; _meta and unknown fields are never hashed. Never raises: a
    definition JCS cannot represent (NaN or Infinity, a number too large for a double,
    a lone surrogate) gets the issuer's digest under a distinct label, which no
    portable digest can equal; lone surrogates are passed through into that text, so
    it still carries every character of the definition."""
    body = {f: tool[f] for f in DIGEST_FIELDS if tool.get(f) is not None}
    try:
        return _sha256(jcs({"profile": PROFILE, "tool": _ijson(body)}))
    except Exception:
        pass
    try:
        text = PROFILE + ".noncanonical\n" + json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
        return "sha256:" + hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()
    except Exception:
        return _sha256(PROFILE + ".unhashable")


# The issuer's digest for a definition that neither JCS nor the fallback can encode
# (json.dumps refuses it; a parsed tools/list never does, and before 2026-11 a lone
# surrogate did). It carries none of the definition, so two such definitions share
# it: equal digests here prove nothing, and a gate never binds to it.
UNBOUND_DIGEST = _sha256(PROFILE + ".unhashable")


def compute_digests(tools: list) -> tuple[dict[str, str], list[str]]:
    """({key: digest}, [keys that could not be hashed]) for a served tools/list.
    Tools sharing a name fold into one entry over their sorted digests, as the
    issuer does. Entries that are not objects are skipped."""
    by_key: dict[str, list[str]] = {}
    unhashable: list[str] = []
    for t in tools:
        if not isinstance(t, dict):
            continue
        key = tool_key(str(t.get("name", "") or "unnamed"))
        if key in unhashable:
            continue
        try:
            by_key.setdefault(key, []).append(tool_digest(t))
        except UnhashableError:
            by_key.pop(key, None)
            unhashable.append(key)
    digests = {
        key: UNBOUND_DIGEST if UNBOUND_DIGEST in ds else ds[0] if len(ds) == 1
        else _sha256(PROFILE + ".duplicates\n" + "\n".join(sorted(ds)))
        for key, ds in by_key.items()
    }
    return digests, unhashable


# ── tool name and server lookup ──────────────────────────────────────────────


def parse_tool_name(name: object) -> tuple[str, str] | None:
    """`mcp__<server>__<tool>` -> (server, tool). The server segment is the first
    one; a tool name may itself contain `__`, so the rest is the tool."""
    if not isinstance(name, str):
        return None
    parts = name.split("__")
    if len(parts) < 3 or parts[0] != "mcp" or not parts[1] or not parts[-1]:
        return None
    return parts[1], "__".join(parts[2:])


def server_candidates(server: str) -> list[str]:
    """Cache keys to try for a server segment. A plugin-bundled server arrives as
    `plugin_<plugin>_<server>`; the plugin name's own underscores make the split
    ambiguous, so every cut after `plugin_` is tried, longest first."""
    cands = [server]
    if server.startswith("plugin_"):
        rest = server[len("plugin_"):]
        cands.extend(rest[i + 1:] for i, ch in enumerate(rest) if ch == "_")
    return cands


def find_record(cache: dict, server: str) -> tuple[str, dict] | None:
    for cand in server_candidates(server):
        if cand == META_KEY:
            continue
        entry = cache.get(cand)
        if isinstance(entry, dict) and "approved_at" in entry and isinstance(entry.get("id"), str):
            return cand, entry
    return None


def _server_config(name: str) -> dict | None:
    """The `mcpServers[name]` entry from the same files the pre-check reads. Only
    the URL and an Authorization header are ever used from it."""
    if _in_codex():
        return _codex_server_config(name)
    candidates = [
        pathlib.Path.home() / ".claude.json",
        pathlib.Path.cwd() / ".mcp.json",
        pathlib.Path.cwd() / ".claude" / "settings.json",
    ]
    for path in candidates:
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                servers = node.get("mcpServers")
                if isinstance(servers, dict) and isinstance(servers.get(name), dict):
                    return servers[name]
                stack.extend(v for v in node.values() if isinstance(v, (dict, list)))
            elif isinstance(node, list):
                stack.extend(v for v in node if isinstance(v, (dict, list)))
    return None


# ── Codex ────────────────────────────────────────────────────────────────────
# Which app runs the hook ("codex" or "claude"), set by main(). Codex is recognised
# exactly as the pre-check recognises it (agentavow_precheck.detect_host).
_HOST = "claude"
_PAYLOAD_CWD: str | None = None


def _in_codex() -> bool:
    return _HOST == "codex"


def _precheck_module():
    """The session-start hook's module (same folder), for Codex host detection and
    config.toml reading, so the two hooks always agree."""
    spec = importlib.util.spec_from_file_location(
        "agentavow_precheck", pathlib.Path(__file__).resolve().parent / "agentavow_precheck.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def detect_host(payload: object) -> str:
    try:
        return _precheck_module().detect_host(payload)
    except Exception:
        return "claude"


def _codex_server_config(name: str) -> dict | None:
    """``[mcp_servers.<name>]`` from Codex's config.toml files, in the shape the gate
    reads (``url``, ``command``, ``headers`` from Codex's ``http_headers``)."""
    try:
        pc = _precheck_module()
        if _PAYLOAD_CWD:
            pc._set_session_cwd({"cwd": _PAYLOAD_CWD})
        found = pc.codex_servers().get(name)
    except Exception:
        return None
    if not found:
        return None
    server = dict(found[0])
    headers = server.get("http_headers")
    if isinstance(headers, dict):
        server["headers"] = headers
    return server


def _sanitize_url(url: str) -> str:
    """scheme + host + path only: the id the pre-check keyed the record by."""
    try:
        p = urllib.parse.urlsplit(url)
        host = p.hostname or ""
        if p.port:
            host = f"{host}:{p.port}"
        return urllib.parse.urlunsplit((p.scheme, host, p.path, "", ""))
    except Exception:
        return url.split("?", 1)[0].split("#", 1)[0]


ALLOWED_SCHEMES = ("https",)


def _call_url(url: str) -> str | None:
    """The URL the gate calls the server on: the configured one minus any
    user:password@ and #fragment. The query string stays, since it belongs to the
    server being called. https only."""
    try:
        p = urllib.parse.urlsplit(url)
        if p.scheme not in ALLOWED_SCHEMES or not p.hostname:
            return None
        host = p.hostname
        if p.port:
            host = f"{host}:{p.port}"
        return urllib.parse.urlunsplit((p.scheme, host, p.path, p.query, ""))
    except Exception:
        return None


def _config_url(cfg: dict) -> str | None:
    url = cfg.get("url") or cfg.get("endpoint")
    return url if isinstance(url, str) and url.startswith("http") else None


_PACKAGE_RUNNERS = {"npx", "bunx", "pnpm", "uvx", "pipx"}


def _gradable(cfg: dict | None) -> bool:
    """Whether the pre-check could grade this server at all: a remote URL that is
    not local or private, or a stdio server launched from a published package. A
    localhost server or a hand-written script is never graded, so the gate does not
    tell the user to expect a grade for one."""
    if not isinstance(cfg, dict):
        return False
    url = _config_url(cfg)
    if url:
        try:
            host = (urllib.parse.urlsplit(url).hostname or "").lower().rstrip(".")
        except Exception:
            return False
        if not host or "." not in host:
            return False
        if host.endswith((".localhost", ".local", ".internal", ".lan", ".home.arpa")):
            return False
        try:
            return ipaddress.ip_address(host).is_global
        except ValueError:
            return True
    cmd = cfg.get("command")
    return isinstance(cmd, str) and os.path.basename(cmd) in _PACKAGE_RUNNERS


def _authorization(cfg: dict) -> str | None:
    """The configured Authorization header for this server, if any. A value that
    still carries a `${...}` placeholder is not expanded (that would mean reading
    arbitrary environment variables) and is not sent."""
    headers = cfg.get("headers")
    if not isinstance(headers, dict):
        return None
    for k, v in headers.items():
        if isinstance(k, str) and k.lower() == "authorization" and isinstance(v, str):
            return None if "${" in v or not v.strip() else v
    return None


# ── settings ─────────────────────────────────────────────────────────────────


def _setting(name: str) -> str:
    """One of the gate's own knobs. The value is read and compared, never sent."""
    return (os.environ.get(name) or "").strip().lower()


def denies(record: dict, setting: str) -> bool:
    """Whether to deny: the answer on file is "Do not connect", or the grade is low
    enough (default: the blocked tier). ``off`` never denies."""
    if setting in ("off", "none", "never"):
        return False
    if record.get("decision") == "do_not_connect":
        return True
    try:
        score = int(record.get("score"))
    except (TypeError, ValueError):
        return False
    if setting in ("off", "none", "never"):
        return False
    if setting.isdigit():
        return score < min(int(setting), 101)
    if setting in TIER_FLOORS and setting != "blocked":
        return score < TIER_FLOORS[setting]
    tier = str(record.get("tier") or "")
    return tier == "blocked" or (not tier and score < TIER_FLOORS["restricted"])


def _recheck_seconds() -> float:
    raw = _setting("AGENTAVOW_GATE_RECHECK_SECONDS")
    try:
        return max(0.0, float(raw)) if raw else float(DEFAULT_RECHECK_SECONDS)
    except ValueError:
        return float(DEFAULT_RECHECK_SECONDS)


# ── the server's own tools/list (Streamable HTTP) ────────────────────────────


def _install_source() -> str:
    plugin_root = pathlib.Path(__file__).resolve().parent.parent
    return "plugin" if (plugin_root / ".claude-plugin").is_dir() else "manual"


def _user_agent() -> str:
    return f"agentavow-gate/{__version__} ({_install_source()})"


def _read_rpc(resp, want_id: int) -> dict | None:
    """The JSON-RPC response to request `want_id`, from a JSON body or an SSE stream.
    An SSE stream is read line by line and left as soon as the reply arrives, so a
    server that keeps the stream open cannot hold the gate past its timeout."""
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "text/event-stream" not in ctype:
        try:
            doc = json.loads(resp.read(4_000_000).decode("utf-8", "replace"))
        except Exception:
            return None
        return doc if isinstance(doc, dict) else None
    for raw in resp:
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload.startswith("{"):
            continue
        try:
            doc = json.loads(payload)
        except ValueError:
            continue
        if isinstance(doc, dict) and ("result" in doc or "error" in doc) and (
                doc.get("id") in (want_id, None)):
            return doc
    return None


def fetch_tools(url: str, auth: str | None, deadline: float) -> list | None:
    """initialize -> notifications/initialized -> tools/list against the server.
    None on any failure. Never raises."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": _user_agent(),
    }
    if auth:
        headers["Authorization"] = auth

    def post(body: dict, want_id: int | None) -> tuple[dict | None, dict]:
        remaining = deadline - time.monotonic()
        if remaining <= 0.2:
            raise TimeoutError
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(  # noqa: S310 (https only, user-configured server)
                req, timeout=min(REQUEST_TIMEOUT, remaining)) as resp:
            if want_id is None:
                return None, dict(resp.headers)
            return _read_rpc(resp, want_id), dict(resp.headers)

    try:
        init, resp_headers = post({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "agentavow-gate", "version": __version__}},
        }, 1)
        if init is None or "result" not in init:
            return None
        session = next((v for k, v in resp_headers.items()
                        if k.lower() == "mcp-session-id"), None)
        if session:
            headers["Mcp-Session-Id"] = session
        headers["MCP-Protocol-Version"] = "2025-06-18"
        try:
            post({"jsonrpc": "2.0", "method": "notifications/initialized"}, None)
        except Exception:
            pass  # a notification; some servers answer 202, some 4xx. Either is fine.
        listing, _ = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, 2)
        tools = ((listing or {}).get("result") or {}).get("tools")
        return tools if isinstance(tools, list) else None
    except Exception:
        return None


# ── cache ────────────────────────────────────────────────────────────────────


def _load_cache() -> dict:
    try:
        data = json.loads(CACHE.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(cache: dict) -> bool:
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE.with_name(f"{CACHE.name}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(cache))
        os.replace(tmp, CACHE)
        return True
    except Exception:
        return False


# ── decisions ────────────────────────────────────────────────────────────────


def _emit(decision: str, reason: str, message: str | None = None) -> None:
    """``reason`` reaches Claude; ``message`` (systemMessage) is shown to the person only."""
    out: dict = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }
    if message:
        out["systemMessage"] = message
    print(json.dumps(out))


def _note_once_per_session(cache: dict, session_id: object, message: str) -> None:
    """A user-visible line, at most once per session, recorded in the cache so a
    parallel call does not repeat it. Nothing enters Claude's context."""
    if not isinstance(session_id, str) or not session_id:
        return
    meta = cache.get(META_KEY)
    if not isinstance(meta, dict):
        meta = {}
    if meta.get("gate_noted_session") == session_id:
        return
    meta["gate_noted_session"] = session_id
    cache[META_KEY] = meta
    if _save_cache(cache):
        print(json.dumps({"systemMessage": message}))


# ── the person's own allow list ──────────────────────────────────────────────


def allow_file() -> pathlib.Path:
    return CACHE.with_name(ALLOW_FILE_NAME)


def _shown_path(path: pathlib.Path) -> str:
    """The allow file's path as a person would type it (~ for the home folder)."""
    try:
        return "~/" + path.relative_to(pathlib.Path.home()).as_posix()
    except ValueError:
        return str(path)


def allow_key_file() -> pathlib.Path:
    return CACHE.with_name(ALLOW_KEY_NAME)


def _allow_key(create: bool) -> bytes | None:
    """The machine's random allow key, or None. With ``create`` a missing or malformed
    key is replaced by a fresh one (0600). A new key voids every code made from the old
    one, so a key someone removed or garbled can only ever turn allow lines off."""
    path = allow_key_file()
    try:
        text = path.read_text(encoding="ascii").strip()
        if re.fullmatch(r"[0-9a-f]{64}", text):
            return bytes.fromhex(text)
    except Exception:
        pass
    if not create:
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="ascii") as fh:
            fh.write(secrets.token_hex(32) + "\n")
        os.replace(tmp, path)
        return bytes.fromhex(path.read_text(encoding="ascii").strip())
    except Exception:
        return None


def allow_code(key: bytes, name: str, server_id: str) -> str:
    """The confirmation code for one server: HMAC-SHA256 over (name, graded id) under
    the machine's allow key, as 10 base32 characters (50 bits) in two groups of five."""
    mac = hmac.new(key, ALLOW_CODE_LABEL + b"\0" + name.encode("utf-8") + b"\0"
                   + server_id.encode("utf-8"), hashlib.sha256).digest()
    code = base64.b32encode(mac).decode("ascii")[:10]
    return f"{code[:5]}-{code[5:]}"


def allow_line(name: str, record: dict, code: str) -> str:
    """The exact line that allows one server: its name, the URL or package its grade is
    for, and its confirmation code. Binding to name and id means a server whose config
    later points somewhere else is not allowed by an old line."""
    return f"{name} {record.get('id')} {code}"


def is_allowed(name: str, record: dict) -> bool:
    """Whether the person listed THIS server in the allow file: a line whose name and
    graded URL / package both match exactly and whose third field is this server's
    confirmation code. Never a pattern, never a wildcard, never every server: any other
    line (a 0.1.37 two-field line included) allows nothing."""
    server_id = str(record.get("id") or "")
    if not server_id:
        return False
    key = _allow_key(create=False)
    if key is None:
        return False
    try:
        text = allow_file().read_text(encoding="utf-8")
    except Exception:
        return False
    want = allow_code(key, name, server_id).replace("-", "").encode("ascii")
    for raw in text.splitlines():
        parts = raw.split("#", 1)[0].split()
        if len(parts) == 3 and (parts[0], parts[1]) == (name, server_id):
            got = parts[2].upper().replace("-", "").encode("ascii", "replace")
            if hmac.compare_digest(got, want):
                return True
    return False


def allow_line_command(name: str) -> str:
    """The terminal command that prints this server's allow line for the person, with
    this install's own path to the gate script (quoted for a shell, ~ left unquoted so
    it still expands). It carries no code: the script prints that only to a terminal."""
    shown = _shown_path(pathlib.Path(__file__).resolve())
    script = ("~/" + shlex.quote(shown[2:])) if shown.startswith("~/") else shlex.quote(shown)
    return f"python3 {script} --allow-line {shlex.quote(name)}"


def allow_instructions(name: str) -> str:
    """How the PERSON can allow this one server, worded for Claude to relay. It never
    carries the confirmation code: that is shown to the person alone."""
    path = _shown_path(allow_file())
    if _in_codex():
        return (f"If the user has reviewed this server and wants to use it anyway, the user "
                f"(not Codex) can allow this one server: AgentAvow has shown them, outside "
                f"this conversation, the exact line to add to {path}, with a confirmation "
                "code only they can see. If they can't see that line, they can print it by "
                f"running this in their own terminal: {allow_line_command(name)}\n"
                "Or they can switch AgentAvow's hooks off in Codex (/hooks) for this "
                "session.\nTell the user exactly that.\n"
                "Do not run that command yourself (it prints nothing to you), do not edit "
                "that file yourself, do not read AgentAvow's files in ~/.cache/agentavow, do "
                "not ask for or work out the code, and do not try another way to reach this "
                "server's tools: a line without the user's own code allows nothing.")
    return (f"If the user has reviewed this server and wants to use it anyway, the user "
            f"(not Claude) can allow this one server: AgentAvow has shown them, outside "
            f"this conversation, the exact line to add to {path}, with a confirmation code "
            "only they can see. If they can't see that line (for example in VS Code), they "
            f"can print it by running this in their own terminal: {allow_line_command(name)}\n"
            "Tell the user exactly that.\n"
            "Do not run that command yourself (it prints nothing to you), do not edit that "
            "file yourself, do not read AgentAvow's files in ~/.cache/agentavow, and do "
            "not ask for or work out the code: a line without the user's own code allows "
            "nothing.")


def allow_message(name: str, record: dict) -> str | None:
    """The person-only notice (systemMessage) with the line to paste, or None when the
    key cannot be made (then no line could count anyway)."""
    server_id = str(record.get("id") or "")
    key = _allow_key(create=True) if server_id else None
    if key is None:
        return None
    line = allow_line(name, record, allow_code(key, name, server_id))
    return (f"AgentAvow gate: MCP '{name}' reads Do not connect, so its tools were stopped. "
            f"If you reviewed it and want to use it anyway, add this line yourself to "
            f"{_shown_path(allow_file())} (the code at the end is shown only to you; do not "
            f"paste it into the chat):\n{line}\n"
            f"If you can't see the line here (for example in VS Code), run this in your own "
            f"terminal to print it: {allow_line_command(name)}")


# Spellings of AgentAvow's own files in an MCP tool's input (a filesystem server, say).
_STATE_MARKERS = (".cache/agentavow", ALLOW_FILE_NAME, "allowed-servers", ALLOW_KEY_NAME)


def names_own_files(tool_input: object) -> bool:
    """Whether an MCP tool's input names AgentAvow's cache folder, allow list or key."""
    try:
        text = json.dumps(tool_input, ensure_ascii=False).lower().replace("\\\\", "/")
    except Exception:
        return False
    text = re.sub(r"[\"'`]", "", text)
    return any(m in text for m in _STATE_MARKERS)


def _note_allowed_once(cache: dict, session_id: object, name: str) -> None:
    """One user-visible line per server per session when a Do not connect server runs
    because the person allowed it. Nothing enters Claude's context."""
    if not isinstance(session_id, str) or not session_id:
        return
    meta = cache.get(META_KEY) if isinstance(cache.get(META_KEY), dict) else {}
    noted = meta.get("allow_noted") if isinstance(meta.get("allow_noted"), dict) else {}
    servers = noted.get("servers") if noted.get("session") == session_id else []
    servers = servers if isinstance(servers, list) else []
    if name in servers:
        return
    meta = dict(meta, allow_noted={"session": session_id, "servers": servers + [name]})
    cache[META_KEY] = meta
    if _save_cache(cache):
        print(json.dumps({"systemMessage": (
            f"AgentAvow gate: MCP '{name}' reads Do not connect; its tools run because you "
            f"allowed it in {_shown_path(allow_file())}. Remove that line to stop them.")}))


def drift_decision(name: str, record: dict, cfg: dict | None, tool: str,
                   cache: dict) -> tuple[str, str] | None:
    """("ask", reason) when the server now serves this tool with a definition the
    grade did not sign; None to allow. Refreshes `last_seen` on the record (never
    the approved digests) at most once per recheck window."""
    approved = record.get("tool_digests")
    if not isinstance(approved, dict) or not approved or len(approved) > _MAX_TOOL_DIGESTS:
        return None
    now = time.time()
    seen = record.get("last_seen") if isinstance(record.get("last_seen"), dict) else {}
    try:
        last_at = float(seen.get("at") or 0)
    except (TypeError, ValueError):
        last_at = 0.0
    url = _call_url(_config_url(cfg) or "") if cfg else None
    if url and now - last_at >= _recheck_seconds():
        tools = fetch_tools(url, _authorization(cfg), time.monotonic() + BUDGET)
        fresh = {"at": now, "ok": tools is not None}
        if tools is not None:
            fresh["tool_digests"], fresh["unhashable"] = compute_digests(tools)
        else:  # keep the last good observation; back off for the window either way
            fresh["tool_digests"] = seen.get("tool_digests") or {}
            fresh["unhashable"] = seen.get("unhashable") or []
        record["last_seen"] = seen = fresh
        _save_cache(cache)

    key = tool_key(tool)
    if key in (seen.get("unhashable") or []):
        noted = record.setdefault("unhashable_noted", [])
        if key not in noted:  # say so once per tool, user-visible only
            noted.append(key)
            if _save_cache(cache):
                print(json.dumps({"systemMessage": (
                    f"AgentAvow gate: the definition of '{tool}' on MCP '{name}' uses a "
                    "number form the gate cannot canonicalize, so it is not checked for "
                    "drift.")}))
        return None
    live_map = seen.get("tool_digests")
    if not isinstance(live_map, dict) or not live_map:
        return None
    live = live_map.get(key)
    if live is None:
        return None  # the server no longer serves it; nothing to compare
    score = record.get("score")
    report = record.get("report_url") or "https://agentavow.com/check"
    expected = approved.get(key)
    if expected is None:
        return "ask", (f"AgentAvow: '{tool}' on MCP '{name}' was not among the tools AgentAvow "
                       f"checked ({score}/100); the server added it since. Review before "
                       f"running. Report: {report}")
    if live == UNBOUND_DIGEST:
        return "ask", (f"AgentAvow: the definition of '{tool}' on MCP '{name}' holds text "
                       "the signed digest cannot carry, so a change to it "
                       f"would not show. Review before running. Report: {report}")
    if expected != live:
        return "ask", (f"AgentAvow: the definition of '{tool}' on MCP '{name}' changed since "
                       f"AgentAvow checked this server ({score}/100). Review before running; "
                       f"it is re-checked at your next session start. Report: {report}")
    return None


def decide(payload: dict, cache: dict) -> tuple | None:
    """The gate's decision for one PreToolUse payload, or None to stay silent:
    (decision, reason for Claude) or (decision, reason, notice for the person only)."""
    parsed = parse_tool_name(payload.get("tool_name"))
    if not parsed:
        return None
    server, tool = parsed
    if names_own_files(payload.get("tool_input")):
        return "ask", ("AgentAvow: this MCP call names AgentAvow's own files "
                       "(~/.cache/agentavow: the grades, your allow list, its key). Only "
                       "approve it if you asked for this yourself.")
    found = find_record(cache, server)
    if not found:
        if _gradable(_server_config(server)):
            entry = cache.get(server)
            checking = isinstance(entry, dict) and "pending_since" in entry
            _note_once_per_session(cache, payload.get("session_id"), (
                f"AgentAvow gate: MCP '{server}' has no grade on file"
                + (" yet (AgentAvow is still checking it)" if checking else "")
                + ", so its tools run unchecked. It is checked at your next session start."))
        return None
    name, record = found
    cfg = _server_config(name)
    if cfg is not None:
        url = _config_url(cfg)
        if url is not None and _sanitize_url(url) != record.get("id"):
            return None  # the config points somewhere else now; the grade is for the old URL
    if denies(record, _setting("AGENTAVOW_GATE_DENY_BELOW")):
        if not is_allowed(name, record):
            report = record.get("report_url") or "https://agentavow.com/check"
            tier = record.get("tier") or "blocked"
            why = f" — {record['decision_reason']}" if record.get("decision_reason") else ""
            # Never " · Certified" here: the mark only ever sits beside Safe to connect.
            return ("deny", (f"AgentAvow: {DECISION_PHRASES['do_not_connect']}{why}. "
                             f"MCP '{name}' scored {record.get('score')}/100 (tier {tier}); "
                             f"'{tool}' was not run. Report: {report}\n"
                             + allow_instructions(name)),
                    allow_message(name, record))
        allowed = True  # the person's own line; a changed definition still asks
    else:
        allowed = False
    result = drift_decision(name, record, cfg, tool, cache) if record.get("kind") == "mcp" \
        else None
    if allowed and result is None:
        _note_allowed_once(cache, payload.get("session_id"), name)
    return result


def allow_line_cli(argv: list[str]) -> int:
    """`--allow-line <server name>`: print that server's allow line, for the person at a
    terminal. Refuses, printing no code, unless stdin AND stdout are both a terminal, so
    a tool that captures the output (Claude's Bash tool, a pipe, a file) gets nothing it
    could write into the allow list. Exit 0 on success, 1 when refused, 2 on bad use or
    an unknown server."""
    try:
        at_terminal = os.isatty(0) and os.isatty(1)
    except Exception:
        at_terminal = False
    if not at_terminal:
        print("AgentAvow: --allow-line prints the allow line only in your own terminal "
              "(input and output both a terminal). Run it there yourself; nothing was "
              "printed here.", file=sys.stderr)
        return 1
    if len(argv) != 1 or not argv[0].strip():
        print("usage: agentavow_pretool_gate.py --allow-line <server name>", file=sys.stderr)
        return 2
    found = find_record(_load_cache(), argv[0].strip())
    if not found:
        print(f"AgentAvow: no grade on file for an MCP server named '{argv[0].strip()}'. Use "
              "the name from the gate's refusal; servers are checked at session start.",
              file=sys.stderr)
        return 2
    name, record = found
    key = _allow_key(create=True)
    if key is None:
        print(f"AgentAvow: could not create the allow key {_shown_path(allow_key_file())}.",
              file=sys.stderr)
        return 2
    if not denies(record, _setting("AGENTAVOW_GATE_DENY_BELOW")):
        print(f"Note: MCP '{name}' does not read Do not connect right now, so the gate does "
              "not stop it; the line only matters if that changes.", file=sys.stderr)
    print(f"Add this line to {_shown_path(allow_file())} (do not paste it into the chat):")
    print(allow_line(name, record, allow_code(key, name, str(record.get("id")))))
    return 0


# Codex has no "ask": where Claude Code would ask the person, Codex gets a deny with
# what was found and how to go ahead anyway.
CODEX_NO_ASK = ("Codex cannot ask you before this call, so AgentAvow stopped it. To go "
                "ahead anyway: {how}")
CODEX_HOW_DRIFT = ("start a new Codex session (AgentAvow re-checks this server's tools at "
                   "session start, and the call runs if the new answer allows it), or switch "
                   "AgentAvow's hooks off in Codex (/hooks) for this session.")
CODEX_HOW_OWN_FILES = ("if you asked for this yourself, do it in your own terminal outside "
                       "Codex, or switch AgentAvow's hooks off in Codex (/hooks) for this "
                       "session.")


def codex_output(decision: tuple | None, printed: str) -> dict | None:
    """The one JSON object Codex gets for this call: the notes the gate printed along
    the way (systemMessage lines, shown to the person) joined, plus the decision with
    "ask" turned into "deny" and its reason saying how to go ahead anyway. Codex reads
    exactly one JSON object per hook run and refuses "ask"."""
    notes: list[str] = []
    for line in printed.splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("systemMessage"), str):
            notes.append(obj["systemMessage"])
    out: dict = {}
    if decision:
        verdict, reason = decision[0], decision[1]
        message = decision[2] if len(decision) > 2 else None
        if verdict == "ask":
            how = (CODEX_HOW_OWN_FILES if "AgentAvow's own files" in reason
                   else CODEX_HOW_DRIFT)
            verdict, reason = "deny", reason + "\n" + CODEX_NO_ASK.format(how=how)
            message = message or reason
        out["hookSpecificOutput"] = {"hookEventName": "PreToolUse",
                                     "permissionDecision": verdict,
                                     "permissionDecisionReason": reason}
        if message:
            notes.append(message)
    if notes:
        out["systemMessage"] = "\n".join(notes)
    return out or None


def _codex_main(payload: dict) -> None:
    global _PAYLOAD_CWD
    cwd = payload.get("cwd")
    _PAYLOAD_CWD = cwd if isinstance(cwd, str) and cwd.strip() else None
    buf = io.StringIO()
    decision = None
    try:
        with contextlib.redirect_stdout(buf):
            decision = decide(payload, _load_cache())
    except Exception:
        decision = None  # fail-open; notes already printed still reach the person
    out = codex_output(decision, buf.getvalue())
    if out:
        print(json.dumps(out))


def main() -> None:
    global _HOST
    if len(sys.argv) > 1 and sys.argv[1] == "--allow-line":
        sys.exit(allow_line_cli(sys.argv[2:]))
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    if not isinstance(payload, dict) or _setting("AGENTAVOW_GATE") in ("off", "0", "false", "no"):
        return
    _HOST = detect_host(payload)
    if _in_codex():
        _codex_main(payload)
        return
    try:
        decision = decide(payload, _load_cache())
    except Exception:
        return  # fail-open
    if decision:
        _emit(*decision)


if __name__ == "__main__":
    main()
