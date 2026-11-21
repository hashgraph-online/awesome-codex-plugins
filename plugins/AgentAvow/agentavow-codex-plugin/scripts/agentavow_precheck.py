#!/usr/bin/env python3
"""AgentAvow SessionStart pre-check — OPT-IN, warn-only, fail-open.

Scans the MCP servers THIS session can use (user scope, this project's local
scope, the project's .mcp.json / settings, and the servers your installed plugins
bring) that haven't been scanned yet and
injects a one-line AgentAvow trust verdict into the session, so you see it BEFORE
you rely on a newly added tool. Servers configured for other projects are counted
in the summary and graded when those projects are opened.
It also grades the project's DIRECT dependencies (package.json "dependencies", or
"devDependencies" when there are none; requirements.txt / pyproject
[project].dependencies; Cargo.toml [dependencies]; in a workspace root with none of
its own, the manifests one folder down), up to DEPS_CAP per session
start in manifest order, the rest on later starts, re-graded only when the declared
version changes. Most projects have no MCP servers but every project has
dependencies, so this is what gives a first session something to say. Dependencies
are already installed, so their answer is advice, never a stop.
Every line leads with one of three answers — "Safe to connect", "Review before you
connect" or "Do not connect" — and the one reason behind it, read from the API's
``decision`` (decided here by the same rule when an older response lacks it), then
the 0-100 score; " · Certified" rides beside the answer when the tool carries the mark.
AGENTAVOW_PRECHECK_DEPS=off turns the pass off. "This project" is the ``cwd`` Claude Code
passes in the hook payload (the session's folder), so a session moved into a project
and then cleared (/clear) is graded for that project. Covers both:
  • Remote HTTP(S) MCP servers  -> scan_mcp_server (the live tool definitions).
  • Local stdio servers run from an npm or PyPI package (npx / uvx / pipx / bunx)
    -> scan_package on the resolved package coordinate.
Local servers that run a hand-written script (node foo.js, python foo.py) have no
published package to grade and are skipped. So are MCP URLs on localhost or a
private network: AgentAvow can't reach them, so they never leave your machine.
A URL whose path looks like it carries a secret (a long token or a UUID) is not
sent either; it is reported as not scanned.
The first time there is nothing to scan at all, the hook shows one line saying so
(and how to scan a tool on demand), then never repeats it. That line makes no request.
In a folder with nothing of its own whose servers were all graded before, it says
once a day what they read ("your 3 tools are fine"), from the cache, no request.
Each verdict (score, tier, grade, the signed per-tool digests) is kept in the cache
file so the per-call gate (agentavow_pretool_gate.py) can act on it without a request.
How the result reaches the person: Claude Code never displays a SessionStart hook's
``additionalContext`` (it goes to the model only), and ``systemMessage`` is not rendered
by every client. So the hook does both, and the context block asks Claude to open its
first reply with the one-line summary — the one channel every surface shows.
A server whose tool definitions the gate saw change since the grade is re-graded here
at the next session start, and reported again.
Once a UTC day the hook also sends one small "active" request: the anonymous install
ID, the plugin version and the app type (desktop, cli, sdk, cloud or other). Nothing
about your tools, servers, files or code. It lets AgentAvow count machines the plugin
protects. AGENTAVOW_ANON_ID=off turns it off along with the install ID.

In Codex (which runs this same plugin's hooks), the servers come from Codex's own config:
``[mcp_servers.<name>]`` in ~/.codex/config.toml ($CODEX_HOME), each ``.codex/config.toml``
of a project you trusted, and the servers your enabled Codex plugins bring. Codex is
recognised from the hook payload (see detect_host); everything else is Claude Code.

Design guarantees (deliberate):
  • OPT-IN — nothing runs unless YOU install this hook. AgentAvow's MCP server never
    forces a scan; that would be an injection vector and is not how this works.
  • WARN, never BLOCK — it only adds context. A low score never stops your session.
  • FAIL-OPEN — a network hiccup, an unknown config shape, anything unexpected: the
    hook stays silent and exits 0. It can never break session startup.

Install / test: https://agentavow.com/docs/auto-scan-claude-code
"""
from __future__ import annotations

import ipaddress
import json
import os
import pathlib
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

__version__ = "0.1.45"

API = "https://agentavow.com/api/v1/public/scan"
WEB = "https://agentavow.com"
CACHE = pathlib.Path.home() / ".cache" / "agentavow" / "scanned.json"
TIMEOUT = 8  # seconds per scan; short so startup is never held up
BUDGET = 20  # seconds for the whole run; stays inside the hook's 30s timeout
RETRY_UNSCANNABLE = 7 * 24 * 3600  # re-try a server the API refused after a week
META_KEY = "_agentavow"  # cache entry holding hook state; never treated as a server name
# Direct dependencies graded per session start; the rest follow next time. The public
# scan routes allow 20 requests/min per IP, and the server pass runs first, so 8 keeps
# a normal start (a handful of servers + 8) under the limit.
DEPS_CAP = 8
DEPS_ENV = "AGENTAVOW_PRECHECK_DEPS"  # set to "off" to skip the dependency pass
DEP_PREFIX = "dep:"  # cache keys for dependencies, so they never collide with server names

# stdio runners we can map to a package registry. node/python/etc. are hand-written
# scripts with no published package to grade, so they're intentionally absent.
_NPM_RUNNERS = {"npx", "bunx", "pnpm-dlx"}
_PYPI_RUNNERS = {"uvx", "pipx"}


class _UnscannableError(Exception):
    """The API refused this target (needs sign-in, not publicly reachable, unknown
    coordinate). Retrying every session can't change that, so it is cached."""


class _QueuedError(Exception):
    """No stored grade yet; the API queued a scan (HTTP 202). Ask again next session."""


# A server whose scan has not answered within this session start's time budget (a slow
# first scan can take the API ~100 s) is reported as "still being checked" and NOT
# recorded as graded, so the next session start asks again and reports the real answer.
# It is retried at most PENDING_MAX_TRIES times or for PENDING_MAX_AGE, then reported
# once as "not checked: check timed out" and left alone like an unscannable server.
PENDING_MAX_TRIES = 5
PENDING_MAX_AGE = 24 * 3600


def _no_answer_yet(e: BaseException) -> bool:
    """The API is slow, busy or still scanning (a timeout, 202 queued, 408/429/5xx),
    as opposed to this machine being offline (no route, DNS failure), which stays silent."""
    if isinstance(e, (_QueuedError, TimeoutError, socket.timeout, urllib.error.HTTPError)):
        return True
    if isinstance(e, urllib.error.URLError):
        return isinstance(e.reason, (TimeoutError, socket.timeout))
    return False


# The three headline phrases (src/trust_tiers.py DECISIONS; tests/test_trust_tiers.py pins
# every copy) and the flag each line starts with.
DECISION_PHRASES = {
    "safe": "Safe to connect",
    "review": "Review before you connect",
    "do_not_connect": "Do not connect",
}
_DECISION_FLAG = {"safe": "✅", "review": "⚠️", "do_not_connect": "⛔"}
RETRY_QUEUED = 10 * 60  # seconds before a queued dependency is asked about again


def _strip_npm_version(spec: str) -> str:
    """'@scope/name@1.2' -> '@scope/name'; 'name@1.2' -> 'name'."""
    return _split_npm_spec(spec)[0]


def _split_npm_spec(spec: str) -> tuple[str, str]:
    """'@scope/name@1.2.3' -> ('@scope/name', '1.2.3'); 'name' -> ('name', '')."""
    if spec.startswith("@"):
        parts = spec.split("@")  # ['', 'scope/name', '1.2']
        if len(parts) < 2:
            return spec, ""
        return "@" + parts[1], "@".join(parts[2:])
    pkg, _, ver = spec.partition("@")
    return pkg, ver


def _npm_target(spec: str) -> tuple[str, str]:
    """The package an npm spec really installs: an alias (``name@npm:other@1.2.3`` or
    ``npm:other@1.2.3``) installs ``other``, so (``other``, ``1.2.3``) is graded, never
    the alias name. Otherwise the same as _split_npm_spec."""
    for _ in range(3):  # an alias of an alias is not valid npm; stop early anyway
        if spec[:4].lower() == "npm:":
            spec = spec[4:]
            continue
        pkg, ver = _split_npm_spec(spec)
        if ver[:4].lower() != "npm:":
            return pkg, ver
        spec = ver[4:]
    return _split_npm_spec(spec)


def _strip_pypi_version(spec: str) -> str:
    """'mcp-server-git==0.1' / 'pkg[extra]>=1' / 'pkg@1.2' -> 'mcp-server-git' / 'pkg'."""
    return _split_pypi_spec(spec)[0]


def _split_pypi_spec(spec: str) -> tuple[str, str]:
    """'pkg[extra]==1.2.3' -> ('pkg', '==1.2.3'); 'pkg@1.2.3' (uvx) -> ('pkg', '@1.2.3')."""
    spec = spec.strip()
    pkg = re.split(r"[=<>!~\[@;\s]", spec, 1)[0].strip()
    rest = spec[len(pkg):].strip()
    if rest.startswith("["):  # extras: pkg[cli]==1.0
        rest = rest.split("]", 1)[1].strip() if "]" in rest else ""
    return pkg, rest.split(";", 1)[0].strip()  # drop environment markers


# An exact release, as opposed to a range or a tag. A pinned server or package is graded
# at that release (the API's ``?version=``); a range ("^1.2", ">=1", "1.x"), a tag
# ("latest", "next") or no spec is graded at the latest release, as before.
_NPM_EXACT = re.compile(r"^v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
_PYPI_EXACT = re.compile(
    r"^(?:\d+!)?\d+(?:\.\d+)*(?:[-_.]?(?:a|b|rc|c|alpha|beta|pre|preview)[-_.]?\d*)?"
    r"(?:[-_.]?(?:post|rev|r)[-_.]?\d*)?(?:[-_.]?dev[-_.]?\d*)?"
    r"(?:\+[a-z0-9]+(?:[-_.][a-z0-9]+)*)?$", re.IGNORECASE)


def _exact_version(registry: str, spec: str) -> str | None:
    """The exact release a version spec pins, or None for a range, a tag or no spec.
    npm: '1.2.3', '=1.2.3', 'v1.2.3'. PyPI: '==1.2.3', '===1.2.3', and uv's '@1.2.3'."""
    s = (spec or "").strip()
    if registry == "npm":
        s = s[1:].strip() if s.startswith("=") else s
        if not _NPM_EXACT.match(s):
            return None
        return s[1:] if s[:1] in ("v", "V") else s
    if registry == "pypi":
        for op in ("===", "==", "@"):
            if s.startswith(op):
                v = s[len(op):].strip()
                return v if _PYPI_EXACT.match(v) else None
    return None


def _pinned_name(registry: str, pkg: str, version: str | None) -> str:
    """How a package is named to the person: 'name@1.2.3' (npm), 'name==1.2.3' (PyPI),
    or the bare name when no exact release is pinned."""
    if not version:
        return pkg
    return f"{pkg}=={version}" if registry == "pypi" else f"{pkg}@{version}"


def _target_coord(t: dict) -> str:
    """A server target as shown in a line: its URL, or 'registry:name' with the pinned
    release when there is one ('npm:name@1.2.3')."""
    if t["kind"] == "mcp":
        return t["url"]
    return f"{t['registry']}:{_pinned_name(t['registry'], t['pkg'], t.get('version'))}"


def _package_target(name: str, registry: str, pkg: str, version: str | None) -> dict:
    """A package server target. A pinned one carries ``version`` and an id of its own
    ('npm:name==1.2.3'), so a grade for one release never answers for another and the
    latest release's grade never answers for a pin (or the other way round)."""
    t = {"name": name, "kind": "package", "registry": registry, "pkg": pkg,
         "id": f"{registry}:{pkg}" + (f"=={version}" if version else "")}
    if version:
        t["version"] = version
    return t


# Runner flags whose NEXT token is a value, never the package (npx / bunx / pnpm dlx;
# uvx / pipx run), so ``uvx --python 3.12 pkg`` is not read as a package named '3.12'.
# ``--flag=value`` is one token and needs no entry.
_RUNNER_VALUE_FLAGS = frozenset({
    # npx / bunx / pnpm dlx
    "--registry", "--cache", "--userconfig", "--prefix", "-w", "--workspace", "-C", "--dir",
    "-c", "--call", "--loglevel", "--node-options", "--shell", "--script-shell",
    # uvx / uv tool run
    "--python", "--with", "--with-editable", "--with-requirements", "--index",
    "--default-index", "-i", "--index-url", "--extra-index-url", "-f", "--find-links",
    "--constraints", "--overrides", "--build-constraints", "--exclude-newer",
    "--exclude-newer-package", "--prerelease", "--resolution", "--index-strategy",
    "--keyring-provider", "-P", "--upgrade-package", "--reinstall-package",
    "--refresh-package", "--no-build-package", "--no-binary-package", "--config-setting",
    "--config-settings-package", "--link-mode", "--cache-dir", "--directory", "--project",
    "--config-file", "--color", "--python-preference", "--allow-insecure-host",
    "--env-file", "--torch-backend", "--fork-strategy",
    # pipx run
    "--pip-args", "--backend", "--suffix",
})


def _pkg_from_args(args: list[str], flag_takes_pkg: tuple[str, ...]) -> str | None:
    """First real package token in a runner's args, honoring a 'flag then package'
    form (npx -p PKG, uvx --from PKG, --package=PKG) and skipping the value of a flag
    that takes one (uvx --python 3.12 PKG)."""
    want_next = skip_next = False
    for a in args:
        if want_next:
            return a
        if skip_next:
            skip_next = False
            continue
        if a in flag_takes_pkg:
            want_next = True
            continue
        flag, eq, value = a.partition("=")
        if eq and value and flag in flag_takes_pkg:
            return value
        if a in _RUNNER_VALUE_FLAGS:
            skip_next = True
            continue
        if a.startswith("-") or a in ("run", "--"):
            continue
        return a
    return None


def _sanitize_url(url: str) -> str:
    """Strip any embedded credential (user:pass@) and the query/fragment before a URL
    leaves the machine. A scan needs only scheme+host+path, never a '?token=' or a
    'user:pass@' a server config might carry, so the precheck can't forward a secret
    to the scan API."""
    try:
        p = urllib.parse.urlsplit(url)
        host = p.hostname or ""
        if p.port:
            host = f"{host}:{p.port}"
        return urllib.parse.urlunsplit((p.scheme, host, p.path, "", ""))
    except Exception:
        return url.split("?", 1)[0].split("#", 1)[0]


def _is_local_host(url: str) -> bool:
    """True for a URL AgentAvow could never reach from outside: localhost, a
    single-label or .local/.internal name, or a loopback/private/link-local IP.
    Unparseable URLs count as local, so they are skipped rather than sent."""
    try:
        host = (urllib.parse.urlsplit(url).hostname or "").lower().rstrip(".")
    except Exception:
        return True
    if not host:
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return (
            "." not in host
            or host.endswith((".localhost", ".local", ".internal", ".lan", ".home.arpa"))
        )
    return not ip.is_global


_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def _has_secret_path(url: str) -> bool:
    """True when a URL path segment looks like a credential rather than a route: a
    UUID, a 32+ character unbroken run, or a 16+ character run mixing letters with
    several digits. Some hosted MCP servers put the user's key in the path, and a
    path is sent as-is, so these are withheld. Words, versions and dates (split on
    - _ . ~) pass."""
    try:
        path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    except Exception:
        return True
    for segment in path.split("/"):
        if _UUID.search(segment):
            return True
        for run in re.split(r"[-_.~]", segment):
            if len(run) >= 32 and run.isalnum():
                return True
            if (len(run) >= 16 and re.search(r"[A-Za-z]", run)
                    and len(re.findall(r"\d", run)) >= 3):
                return True
    return False


def _resolve_target(name: str, cfg: dict) -> dict | None:
    """Classify one MCP server config into a scannable target, or None to skip."""
    url = cfg.get("url") or cfg.get("endpoint")
    if isinstance(url, str) and url.startswith("http"):
        # A ${VAR} placeholder is expanded by Claude Code from the environment; the hook
        # never reads the environment, so such a URL is not the real one: skip it.
        if _is_local_host(url) or "${" in url:
            return None
        safe = _sanitize_url(url)
        if _has_secret_path(safe):
            host = urllib.parse.urlsplit(safe).hostname or ""
            return {"name": name, "kind": "withheld", "id": f"withheld:{host}", "host": host}
        return {"name": name, "kind": "mcp", "id": safe, "url": safe}

    cmd = cfg.get("command")
    if not isinstance(cmd, str):
        return None
    args = [a for a in (cfg.get("args") or []) if isinstance(a, str)]
    runner = os.path.basename(cmd)
    # `pnpm dlx x` arrives as command=pnpm, args=[dlx, x]
    if runner == "pnpm" and args[:1] == ["dlx"]:
        runner, args = "pnpm-dlx", args[1:]

    if runner in _NPM_RUNNERS:
        spec = _pkg_from_args(args, ("-p", "--package"))
        if spec:
            pkg, ver = _npm_target(spec)
            return _package_target(name, "npm", pkg, _exact_version("npm", ver))
    elif runner in _PYPI_RUNNERS:
        spec = _pkg_from_args(args, ("--from", "--spec"))
        if spec:
            pkg, ver = _split_pypi_spec(spec)
            return _package_target(name, "pypi", pkg, _exact_version("pypi", ver))
    return None


def _take(servers: object, seen: dict[str, dict], scope: str = "project") -> None:
    """Add each scannable server in an ``mcpServers`` map to ``seen``. ``scope`` says
    where it came from: "user" (every session on this machine), "project" (this
    folder) or "plugin" (bundled by an installed plugin)."""
    if not isinstance(servers, dict):
        return
    for sname, cfg in servers.items():
        if sname in seen or sname == META_KEY or not isinstance(cfg, dict):
            continue
        t = _resolve_target(sname, cfg)
        if t:
            t["scope"] = scope
            seen[sname] = t


def _walk_for_servers(data: object, seen: dict[str, dict]) -> None:
    """Defensive walk of a project-level config file: every ``mcpServers`` map, at
    any depth (shapes vary by Claude Code version)."""
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            _take(node.get("mcpServers"), seen)
            stack.extend(v for v in node.values() if isinstance(v, (dict, list)))
        elif isinstance(node, list):
            stack.extend(v for v in node if isinstance(v, (dict, list)))


def _read_json(path: pathlib.Path) -> object:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


# The folder the SESSION is in. Claude Code passes it as ``cwd`` in the hook payload;
# that is what "this project" means, and it differs from the process directory when
# the session was moved (Claude Desktop's Code tab starts in a scratch workspace and
# the person cd's into the project). Set by main() from stdin; falls back to the
# process cwd.
_SESSION_CWD: pathlib.Path | None = None


def _cwd() -> pathlib.Path:
    return _SESSION_CWD or pathlib.Path.cwd()


def _set_session_cwd(payload: object) -> None:
    global _SESSION_CWD
    _SESSION_CWD = None
    if isinstance(payload, dict):
        raw = payload.get("cwd")
        if isinstance(raw, str) and raw.strip():
            try:
                cand = pathlib.Path(raw).expanduser()
                if cand.is_dir():
                    _SESSION_CWD = cand
            except Exception:
                _SESSION_CWD = None


# --------------------------------------------------------------------------- #
# Which app is running the hook: Claude Code, or Codex (OpenAI) running this same plugin
# --------------------------------------------------------------------------- #
# Codex runs Claude Code plugin hooks (same hooks.json, same JSON in and out), but its
# MCP servers live in ~/.codex/config.toml, it has its own `codex mcp add`, and a
# PreToolUse hook there cannot "ask" (only deny). Every Codex-only path below is taken
# only when the hook is sure it runs in Codex; anything else is Claude Code, unchanged.
HOST_ENV = "AGENTAVOW_HOST"  # OPTIONAL override: "codex" or "claude"
_HOST: str | None = None  # "codex" or "claude", set by main() from the payload


def _codex_home() -> pathlib.Path:
    """$CODEX_HOME, else ~/.codex (where Codex keeps config.toml, sessions and plugins)."""
    raw = os.environ.get("CODEX_HOME", "").strip()
    return pathlib.Path(raw).expanduser() if raw else pathlib.Path.home() / ".codex"


def _inside(path: object, root: pathlib.Path) -> bool:
    if not isinstance(path, str) or not path.strip():
        return False
    try:
        p, r = os.path.realpath(os.path.expanduser(path)), os.path.realpath(root)
        return p == r or p.startswith(r.rstrip(os.sep) + os.sep)
    except Exception:
        return False


def detect_host(payload: object) -> str:
    """"codex" when the hook payload or environment can only come from Codex: a
    ``turn_id`` (Codex adds it to every tool hook; Claude Code never sends one), a
    transcript under the Codex home, or a plugin root (PLUGIN_ROOT, which Codex sets
    beside CLAUDE_PLUGIN_ROOT) under the Codex home. "claude" otherwise."""
    forced = os.environ.get(HOST_ENV, "").strip().lower()
    if forced in ("codex", "claude"):
        return forced
    home = _codex_home()
    if isinstance(payload, dict):
        if isinstance(payload.get("turn_id"), str) and payload["turn_id"]:
            return "codex"
        if _inside(payload.get("transcript_path"), home):
            return "codex"
    if _inside(os.environ.get("PLUGIN_ROOT"), home):
        return "codex"
    return "claude"


def _set_host(payload: object) -> None:
    global _HOST
    try:
        _HOST = detect_host(payload)
    except Exception:
        _HOST = "claude"


def _in_codex() -> bool:
    return _HOST == "codex"


def _toml_load(text: str) -> dict:
    """config.toml as a dict: tomllib (Python 3.11+), else a small reader that only
    understands what MCP server tables need (``[a.b."c"]`` headers, strings, booleans,
    numbers and one-line string arrays). {} on anything it cannot read."""
    try:
        import tomllib  # type: ignore[import-not-found]
    except ImportError:
        tomllib = None
    if tomllib is not None:
        try:
            data = tomllib.loads(text)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return _mini_toml(text)


_TOML_KEY = r'(?:"(?:[^"\\]|\\.)*"|\'[^\']*\'|[A-Za-z0-9_-]+)'
_TOML_HEADER = re.compile(r"^\[(?!\[)\s*(" + _TOML_KEY + r"(?:\s*\.\s*" + _TOML_KEY
                          + r")*)\s*\]\s*(?:#.*)?$")
_TOML_PAIR = re.compile(r"^(" + _TOML_KEY + r")\s*=\s*(.+?)\s*$")


def _toml_key_parts(dotted: str) -> list[str]:
    parts = re.findall(_TOML_KEY, dotted)
    return [p[1:-1] if p[:1] in "\"'" else p for p in parts]


def _toml_value(raw: str) -> object:
    raw = raw.strip()
    if raw.startswith('"') or raw.startswith("'"):
        m = re.match(r'^"((?:[^"\\]|\\.)*)"|^\'([^\']*)\'', raw)
        if not m:
            raise ValueError(raw)
        return (json.loads('"' + m.group(1) + '"') if m.group(1) is not None
                else m.group(2))
    if raw.startswith("["):
        end = raw.rfind("]")
        if end < 0:
            raise ValueError(raw)
        items = re.findall(r'"(?:[^"\\]|\\.)*"|\'[^\']*\'', raw[1:end])
        return [_toml_value(i) for i in items]
    word = raw.split("#", 1)[0].strip()
    if word in ("true", "false"):
        return word == "true"
    return word


def _mini_toml(text: str) -> dict:
    root: dict = {}
    table = root
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = _TOML_HEADER.match(s)
        if m:
            table = root
            for part in _toml_key_parts(m.group(1)):
                nxt = table.get(part)
                table[part] = nxt = nxt if isinstance(nxt, dict) else {}
                table = nxt
            continue
        if s.startswith("[["):
            table = {}  # arrays of tables are not needed here
            continue
        m = _TOML_PAIR.match(s)
        if not m:
            continue
        try:
            parts = _toml_key_parts(m.group(1))
            table[parts[-1]] = _toml_value(m.group(2))
        except Exception:
            continue
    return root


def _read_toml(path: pathlib.Path) -> dict:
    try:
        return _toml_load(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _codex_project_dirs(user_cfg: dict) -> list[pathlib.Path]:
    """The folders whose ``.codex/config.toml`` Codex loads for this session, nearest
    last: the session folder and each parent up to the project root (the nearest folder
    holding .git), and only when the person trusted the project
    (``[projects."<path>"] trust_level = "trusted"`` for the session folder or the
    project root). An untrusted project's config is loaded but switched off by Codex,
    so its servers never run and are not graded here."""
    cwd = _cwd()
    try:
        cwd = cwd.resolve()
    except Exception:
        pass
    chain = [cwd, *cwd.parents]
    root = next((d for d in chain if (d / ".git").exists()), None)
    upto = chain[:chain.index(root) + 1] if root is not None else [cwd]
    projects = user_cfg.get("projects") if isinstance(user_cfg.get("projects"), dict) else {}

    def trust(d: pathlib.Path) -> str | None:
        for key in (str(d), os.path.realpath(d)):
            entry = projects.get(key)
            if isinstance(entry, dict) and isinstance(entry.get("trust_level"), str):
                return entry["trust_level"]
        return None

    decided = trust(cwd) or (trust(root) if root is not None else None)
    if decided != "trusted":
        return []
    return list(reversed(upto))


def _codex_server_map(cfg: dict) -> dict[str, dict]:
    servers = cfg.get("mcp_servers")
    return {k: v for k, v in servers.items() if isinstance(k, str) and isinstance(v, dict)} \
        if isinstance(servers, dict) else {}


def codex_servers() -> dict[str, tuple[dict, str]]:
    """{name: (server table, scope)} for the MCP servers a Codex session here can use:
    ``[mcp_servers.<name>]`` in $CODEX_HOME/config.toml ("user") and, in a trusted
    project, each ``.codex/config.toml`` from the project root down to the session
    folder ("project"; nearer wins). A server switched off (``enabled = false``) is left
    out. Never raises."""
    out: dict[str, tuple[dict, str]] = {}
    try:
        user_cfg = _read_toml(_codex_home() / "config.toml")
        layers = [(user_cfg, "user")]
        for d in _codex_project_dirs(user_cfg):
            layers.append((_read_toml(d / ".codex" / "config.toml"), "project"))
        for cfg, scope in layers:
            for name, server in _codex_server_map(cfg).items():
                out[name] = (server, scope)
    except Exception:
        return out
    return {k: v for k, v in out.items() if v[0].get("enabled") is not False}


def _codex_plugin_dirs() -> list[pathlib.Path]:
    """Install folders of the plugins enabled in Codex (``[plugins."<name>@<market>"]
    enabled = true``), newest installed version of each, from $CODEX_HOME/plugins/cache."""
    cfg = _read_toml(_codex_home() / "config.toml")
    plugins = cfg.get("plugins") if isinstance(cfg.get("plugins"), dict) else {}
    out: list[pathlib.Path] = []
    for key, entry in plugins.items():
        if not isinstance(key, str) or "@" not in key or not isinstance(entry, dict):
            continue
        if entry.get("enabled") is False:
            continue
        name, market = key.split("@", 1)
        base = _codex_home() / "plugins" / "cache" / market / name
        try:
            versions = [d for d in base.iterdir() if d.is_dir()]
        except Exception:
            continue
        if versions:
            out.append(max(versions, key=lambda d: d.stat().st_mtime))
    _note_past_cap("installed Codex plugins", [d.parent.name for d in out[PLUGIN_DIRS_CAP:]],
                   "their MCP servers were not checked")
    return out[:PLUGIN_DIRS_CAP]


# What a session start left unread because of a cap (more plugins or sub-projects than it
# reads). Never silent: the lines are added to the report (or, on a quiet start, to the
# list Claude is given), naming what was not read. Reset at the start of each run.
_NOT_READ: list[str] = []
NOT_READ_NAMES = 8  # names listed per note; the rest are counted


def _note_past_cap(what: str, names: list[str], why: str) -> None:
    if not names:
        return
    shown = ", ".join(names[:NOT_READ_NAMES])
    more = f" and {len(names) - NOT_READ_NAMES} more" if len(names) > NOT_READ_NAMES else ""
    line = (f"➖ not read: {len(names)} more {what} than one session start reads "
            f"({shown}{more}); {why}.")
    if line not in _NOT_READ:  # a list may be read twice in one start
        _NOT_READ.append(line)


def _codex_targets() -> list[dict]:
    """The Codex counterpart of _targets(): the servers in Codex's config.toml files,
    then the servers Codex plugins bring (AgentAvow's own connector left out)."""
    seen: dict[str, dict] = {}
    for name, (server, scope) in codex_servers().items():
        if name == META_KEY:
            continue
        t = _resolve_target(name, server)
        if t:
            t["scope"] = scope
            seen[name] = t
    try:
        for pdir in _codex_plugin_dirs():
            pname, servers = _plugin_server_map(pdir)
            if (pname or pdir.parent.name) == OWN_PLUGIN:
                continue
            _add_plugin_servers(pname or pdir.parent.name, servers, seen)
    except Exception:
        pass  # fail-open: a plugin's config can never break the rest of the list
    return list(seen.values())


def _cwd_keys() -> set[str]:
    cwd = _cwd()
    keys = {str(cwd)}
    try:
        keys.add(str(cwd.resolve()))
    except Exception:
        pass
    return keys


def _targets() -> list[dict]:
    """The servers THIS session can connect to — what ``claude mcp list`` shows here:
    user scope (``~/.claude.json`` top-level ``mcpServers``), this project's local
    scope (``~/.claude.json`` → ``projects[cwd].mcpServers``), and project scope
    (``./.mcp.json``, ``./.claude/settings*.json``). Servers configured for other
    projects are graded when those projects are opened (see _servers_elsewhere), so
    the summary matches the list the person can see. In Codex: _codex_targets()."""
    if _in_codex():
        return _codex_targets()
    seen: dict[str, dict] = {}
    data = _read_json(pathlib.Path.home() / ".claude.json")
    if isinstance(data, dict):
        _take(data.get("mcpServers"), seen, "user")
        projects = data.get("projects")
        if isinstance(projects, dict):
            for key in _cwd_keys():
                proj = projects.get(key)
                if isinstance(proj, dict):
                    _take(proj.get("mcpServers"), seen)
    for path in (_cwd() / ".mcp.json",
                 _cwd() / ".claude" / "settings.json",
                 _cwd() / ".claude" / "settings.local.json"):
        node = _read_json(path)
        if node is not None:
            _walk_for_servers(node, seen)
    try:
        _plugin_servers(seen)
    except Exception:
        pass  # fail-open: a plugin's config can never break the rest of the list
    return list(seen.values())


# --------------------------------------------------------------------------- #
# MCP servers bundled by installed Claude Code plugins
# --------------------------------------------------------------------------- #
OWN_PLUGIN = "agentavow-trust"
OWN_HOSTS = ("agentavow.com", "agentgraph.co")  # our own connector: not graded by itself
PLUGIN_DIRS_CAP = 50


def _plugin_dirs() -> list[tuple[str, pathlib.Path]]:
    """(plugin name, install folder) for each plugin Claude Code has installed for this
    session: ``~/.claude/plugins/installed_plugins.json`` (user scope, or a project
    scope for this folder; a plugin switched off in ``~/.claude/settings.json``
    ``enabledPlugins`` is left out) and plugins synced from a claude.ai account
    (``~/.claude/plugins/synced/<account>/<plugin>/``). Marketplace checkouts that are
    not installed are never read."""
    root = pathlib.Path.home() / ".claude" / "plugins"
    settings = _read_json(pathlib.Path.home() / ".claude" / "settings.json")
    enabled = settings.get("enabledPlugins") if isinstance(settings, dict) else None
    enabled = enabled if isinstance(enabled, dict) else {}
    here = _cwd_keys()
    out: list[tuple[str, pathlib.Path]] = []
    data = _read_json(root / "installed_plugins.json")
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if isinstance(plugins, dict):
        for key, entries in plugins.items():
            if not isinstance(key, str) or enabled.get(key) is False:
                continue
            for e in entries if isinstance(entries, list) else [entries]:
                if not isinstance(e, dict) or not isinstance(e.get("installPath"), str):
                    continue
                scope = e.get("scope") or "user"
                if scope != "user" and str(e.get("projectPath") or "") not in here:
                    continue
                out.append((key.split("@", 1)[0], pathlib.Path(e["installPath"])))
    try:
        for account in sorted((root / "synced").iterdir()):
            if not account.is_dir() or account.name.startswith("."):
                continue
            for d in sorted(account.iterdir()):
                if d.is_dir() and not d.name.startswith(".") and (d / ".claude-plugin").is_dir():
                    out.append(("", d))
    except Exception:
        pass
    _note_past_cap("installed plugins", [n or d.name for n, d in out[PLUGIN_DIRS_CAP:]],
                   "their MCP servers were not checked")
    return out[:PLUGIN_DIRS_CAP]


def _plugin_server_map(pdir: pathlib.Path) -> tuple[str, dict]:
    """(the plugin's own name, its ``mcpServers`` map) from ``.claude-plugin/plugin.json``
    (an inline map, or a path or list of paths inside the plugin) or the default
    ``.mcp.json``. Both ``{"mcpServers": {...}}`` and a bare ``{name: config}`` file are
    read."""
    manifest = _read_json(pdir / ".claude-plugin" / "plugin.json")
    manifest = manifest if isinstance(manifest, dict) else {}
    name = manifest.get("name") if isinstance(manifest.get("name"), str) else ""
    spec = manifest.get("mcpServers", "./.mcp.json")
    servers: dict = {}
    for part in spec if isinstance(spec, list) else [spec]:
        if isinstance(part, dict):
            servers.update(part)
            continue
        if not isinstance(part, str):
            continue
        try:
            path = (pdir / part).resolve()
            path.relative_to(pdir.resolve())  # stay inside the plugin folder
        except Exception:
            continue
        node = _read_json(path)
        if isinstance(node, dict):
            inner = node.get("mcpServers")
            servers.update(inner if isinstance(inner, dict) else node)
    return name, {k: v for k, v in servers.items() if isinstance(k, str) and isinstance(v, dict)}


def _own_connector(t: dict) -> bool:
    host = (urllib.parse.urlsplit(t.get("url") or "").hostname or "").lower()
    return host in OWN_HOSTS or host.endswith(tuple("." + h for h in OWN_HOSTS))


def _plugin_servers(seen: dict[str, dict]) -> None:
    """Add the MCP servers that installed plugins bring. Each is keyed by its own
    name, as the per-call gate looks it up (a plugin's tool arrives as
    ``mcp__plugin_<plugin>_<server>__<tool>`` and the gate tries every cut); when that
    name is already taken by a different server here, it is keyed
    ``plugin_<plugin>_<server>``, the gate's first candidate. AgentAvow's own
    connector is left out."""
    for key_name, pdir in _plugin_dirs():
        name, servers = _plugin_server_map(pdir)
        name = name or key_name
        if name == OWN_PLUGIN:
            continue
        _add_plugin_servers(name, servers, seen)


def _add_plugin_servers(name: str, servers: dict, seen: dict[str, dict]) -> None:
    """Add one plugin's servers to ``seen`` (see _plugin_servers for the keys)."""
    for sname, cfg in servers.items():
        t = _resolve_target(sname, cfg)
        if not t or _own_connector(t):
            continue
        if sname in seen and seen[sname]["id"] == t["id"]:
            continue  # the same server, already listed from your own config
        key = sname if sname not in seen and sname != META_KEY else f"plugin_{name}_{sname}"
        if key in seen:
            continue
        t["name"] = key
        t["scope"] = "plugin"
        seen[key] = t


# --------------------------------------------------------------------------- #
# Direct dependencies of the project in cwd
# --------------------------------------------------------------------------- #
_PY_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")


def _deps_enabled() -> bool:
    return os.environ.get(DEPS_ENV, "").strip().lower() not in ("off", "0", "false", "no")


def _dep(registry: str, pkg: str, spec: str) -> dict:
    """A dependency or an installed package. One pinned to an exact release is graded at
    that release; its id ('dep:npm:name==1.2.3') differs from every range/unpinned id
    ('dep:npm:name@^1.2', and those written before pins were graded), so the two kinds
    of grade never answer for each other."""
    spec = (spec or "").strip()
    t = {"name": f"{DEP_PREFIX}{registry}:{pkg}", "kind": "package", "registry": registry,
         "pkg": pkg, "spec": spec, "id": f"{DEP_PREFIX}{registry}:{pkg}@{spec}"}
    version = _exact_version(registry, spec)
    if version:
        t["version"] = version
        t["id"] = f"{DEP_PREFIX}{registry}:{pkg}=={version}"
    return t


def _npm_deps(data: object) -> list[dict]:
    """package.json → direct runtime dependencies (not transitive). When there are none
    (a tool, a template or a workspace root often lists only devDependencies), the
    devDependencies are read instead. Local / git / URL specs have no registry grade
    and are skipped."""
    if not isinstance(data, dict):
        return []
    out = _npm_dep_map(data.get("dependencies"))
    return out or _npm_dep_map(data.get("devDependencies"))


def _npm_dep_map(deps: object) -> list[dict]:
    if not isinstance(deps, dict):
        return []
    out = []
    for name, spec in deps.items():
        if not isinstance(name, str) or not isinstance(spec, str):
            continue
        low = spec.strip().lower()
        if low.startswith("npm:"):
            # "name": "npm:other@1.2.3" installs other: grade that, at its pin
            target, ver = _npm_target(spec.strip())
            if target:
                out.append(_dep("npm", target, ver))
            continue
        if low.startswith(("file:", "link:", "git", "http", "workspace:", ".", "/")):
            continue
        out.append(_dep("npm", name, spec))
    return out


def _pypi_name_spec(line: str) -> tuple[str, str] | None:
    line = line.split("#", 1)[0].strip()
    if not line or line.startswith("-") or "://" in line or line.startswith((".", "/")):
        return None
    m = _PY_NAME.match(line)
    if not m:
        return None
    name = m.group(0)
    rest = line[m.end():].split(";", 1)[0].strip()  # drop environment markers
    if rest.startswith("["):  # extras: requests[security]>=2
        rest = rest.split("]", 1)[1].strip() if "]" in rest else ""
    return name, rest


def _requirements_deps(text: str) -> list[dict]:
    out = []
    for raw in text.splitlines():
        hit = _pypi_name_spec(raw)
        if hit:
            out.append(_dep("pypi", hit[0], hit[1]))
    return out


def _toml_string_list(text: str, start: int) -> list[str]:
    """The quoted strings of a TOML array that opens at ``text[start] == '['``, read
    with quote awareness so a ']' inside an entry ("uvicorn[standard]>=0.24") does
    not end the list. Stops at the matching close bracket; comments are skipped."""
    out: list[str] = []
    i, n = start + 1, len(text)
    while i < n:
        c = text[i]
        if c == "]":
            break
        if c == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c in "\"'":
            j = text.find(c, i + 1)
            if j < 0:
                break
            out.append(text[i + 1:j])
            i = j + 1
            continue
        i += 1
    return out


def _pyproject_deps(text: str) -> list[dict]:
    """[project].dependencies from pyproject.toml. tomllib when available (3.11+),
    else a fallback that finds the [project] table's ``dependencies = [`` and reads
    the list quote-aware (the system python3 on many Macs is 3.9)."""
    deps: list[str] = []
    try:
        import tomllib  # type: ignore[import-not-found]
        data = tomllib.loads(text)
        raw = (data.get("project") or {}).get("dependencies") or []
        deps = [d for d in raw if isinstance(d, str)]
    except Exception:
        m = re.search(r"^\[project\][ \t]*\n(.*?)(?=^\[|\Z)", text, re.S | re.M)
        if m:
            body = m.group(1)
            m2 = re.search(r"^dependencies\s*=\s*\[", body, re.M)
            if m2:
                deps = _toml_string_list(body, m2.end() - 1)
    out = []
    for d in deps:
        hit = _pypi_name_spec(d)
        if hit:
            out.append(_dep("pypi", hit[0], hit[1]))
    return out


_CARGO_KEY = re.compile(r"""^\s*("?)([A-Za-z0-9_-]+)\1\s*=\s*(.+?)\s*$""")


def _cargo_entry(name: str, val: object) -> dict | None:
    """One Cargo.toml dependency: ``name = "1.0"`` or ``name = { version = "1", ... }``
    (``package = "real-name"`` renames it). A path, git or workspace dependency has no
    crates.io grade and is skipped."""
    if isinstance(val, str):
        return _dep("crates", name, val)
    if not isinstance(val, dict) or any(k in val for k in ("path", "git", "workspace")):
        return None
    real = val.get("package") if isinstance(val.get("package"), str) else name
    ver = val.get("version") if isinstance(val.get("version"), str) else ""
    return _dep("crates", real, ver)


def _cargo_deps(text: str) -> list[dict]:
    """Cargo.toml [dependencies] (crates.io), or a workspace root's
    [workspace.dependencies] when the root has none. tomllib when available, else a
    line reader for the two common forms."""
    try:
        import tomllib  # type: ignore[import-not-found]
        data = tomllib.loads(text)
        deps = data.get("dependencies")
        if not deps:
            deps = (data.get("workspace") or {}).get("dependencies")
        items = list(deps.items()) if isinstance(deps, dict) else []
    except Exception:
        items = []
        for table in ("dependencies", "workspace.dependencies"):
            m = re.search(r"^\[" + re.escape(table) + r"\][ \t]*\n(.*?)(?=^\[|\Z)",
                          text, re.S | re.M)
            if not m:
                continue
            for line in m.group(1).splitlines():
                hit = _CARGO_KEY.match(line.split("#", 1)[0])
                if not hit:
                    continue
                raw = hit.group(3)
                if raw.startswith(("'", '"')):
                    items.append((hit.group(2), raw.strip("'\"")))
                elif raw.startswith("{"):
                    fields = dict(re.findall(r"""(\w+)\s*=\s*["']([^"']*)["']""", raw))
                    if re.search(r"\b(path|git|workspace)\s*=", raw):
                        fields["path"] = "x"
                    items.append((hit.group(2), fields))
            if items:
                break
    out = []
    for name, val in items:
        t = _cargo_entry(name, val) if isinstance(name, str) else None
        if t:
            out.append(t)
    return out


def _manifest_deps(folder: pathlib.Path) -> list[dict]:
    """Every direct dependency the manifests in one folder declare."""
    found: list[dict] = []
    pj = _read_json(folder / "package.json")
    if pj is not None:
        found += _npm_deps(pj)
    for fname, parse in (("requirements.txt", _requirements_deps),
                         ("pyproject.toml", _pyproject_deps),
                         ("Cargo.toml", _cargo_deps)):
        try:
            found += parse((folder / fname).read_text())
        except Exception:
            pass
    return found


# Folders never read for a sub-project's manifest: dependencies, builds, environments.
_SKIP_SUBDIRS = frozenset({"node_modules", "venv", "env", "target", "dist", "build",
                           "vendor", "site-packages", "__pycache__"})
SUBPROJECTS_CAP = 5  # sub-folders with a manifest read in a workspace root
SUBDIRS_SCAN_CAP = 60  # sub-folders looked at in one start


def _subproject_deps(cwd: pathlib.Path) -> list[dict]:
    """In a workspace root with nothing of its own to grade (a monorepo folder, a
    folder of services), the manifests one level down: the first SUBPROJECTS_CAP
    sub-folders with one, by name. Never in the home folder, where the sub-folders
    are unrelated projects."""
    try:
        if cwd.resolve() == pathlib.Path.home().resolve():
            return []
        every = sorted(d for d in cwd.iterdir()
                       if d.is_dir() and not d.name.startswith(".")
                       and d.name not in _SKIP_SUBDIRS)
    except Exception:
        return []
    subdirs = every[:SUBDIRS_SCAN_CAP]
    found: list[dict] = []
    projects = 0
    skipped: list[str] = []
    for d in subdirs:
        deps = _manifest_deps(d)
        if deps:
            if projects >= SUBPROJECTS_CAP:
                skipped.append(d.name)
                continue
            found += deps
            projects += 1
    if projects:  # only a workspace root whose sub-projects are read at all
        _note_past_cap("sub-folders with a manifest", skipped,
                       "their dependencies were not checked")
        _note_past_cap("sub-folders", [d.name for d in every[SUBDIRS_SCAN_CAP:]],
                       "they were not looked at for a manifest")
    return found


def _dependency_targets() -> list[dict]:
    """Direct dependencies declared by the project in cwd, in manifest order (one level
    down in a workspace root with none of its own); [] when there is no manifest or
    the pass is off. Same package under two manifests → once."""
    if not _deps_enabled():
        return []
    cwd = _cwd()
    found = _manifest_deps(cwd) or _subproject_deps(cwd)
    seen: dict[str, dict] = {}
    for t in found:
        seen.setdefault(t["name"], t)
    return list(seen.values())


def _dep_needs_look(r: dict) -> bool:
    """A dependency whose answer is not "Safe to connect". Dependencies are already
    installed, so this is advice for the summary count, never a stop."""
    return _dval(r) in ("review", "do_not_connect")


def _dep_coord(t: dict) -> str:
    return f"{t['registry']}:{t['pkg']}" + (f"@{t['spec']}" if t.get("spec") else "")


def _dep_lines_and_graded(cache: dict, deps: list[dict], now: float, started: float
                          ) -> tuple[list[str], list[tuple[str, dict]], bool]:
    """Grade up to DEPS_CAP not-yet-graded dependencies within the shared time budget.
    Returns (report lines for the newly graded ones, (name, verdict) for EVERY graded
    dependency of this manifest incl. cached ones, whether the API throttled us). A
    429 or a 5xx stops the pass for this session: burning the budget on refused
    requests helps nobody, and the rest are picked up next time."""
    lines: list[str] = []
    new = 0
    throttled = False
    queued = 0
    for t in deps:
        entry = cache.get(t["name"])
        if _is_cached(entry, t["id"], now):
            continue
        if new >= DEPS_CAP or time.monotonic() - started > BUDGET:
            break
        new += 1
        refresh = _refresh_only(entry, t["id"], now)
        unscannable_reason = ""
        try:
            r: dict | None = _scan(t, stored=True)
        except _UnscannableError as e:
            r = None
            unscannable_reason = str(e) if not str(e).isdigit() else ""
            unscannable_reason = unscannable_reason.replace("Not scannable: ", "")[:120]
        except _QueuedError:
            # Not graded yet; the API queued it. Ask again in a few minutes, not next week.
            cache[t["name"]] = {"id": t["id"], "retry_after": now + RETRY_QUEUED}
            queued += 1
            continue
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                throttled = True
                break
            continue
        except Exception:
            continue  # transient; next session
        if r is None:
            cache[t["name"]] = {"id": t["id"], "retry_after": now + RETRY_UNSCANNABLE,
                                "reason": unscannable_reason}
            why = f" ({unscannable_reason})" if unscannable_reason else ""
            lines.append(f"➖ dependency '{t['pkg']}' ({_dep_coord(t)}): not scanned — "
                         f"AgentAvow couldn't grade it{why}. Neither safe nor unsafe.")
            continue
        rec = _record(t, r, now)
        rec["spec"] = t.get("spec", "")
        cache[t["name"]] = rec
        if refresh and _dval(r) == _dval(entry):
            continue  # routine re-check, same answer: nothing to say
        was = f"updated grade (was: {_answer(entry)}): " if refresh else ""
        sandbox = f"; {r['sandbox']}" if r.get("sandbox") else ""
        # Already installed: the answer is advice, never a stop.
        lines.append(f"{_flag(r)} dependency '{t['pkg']}' ({_dep_coord(t)}): "
                     f"{was}{_answer(r)}{sandbox}.")
    graded: list[tuple[str, dict]] = []
    unscannable = 0
    for t in deps:
        e = cache.get(t["name"])
        if isinstance(e, dict) and e.get("id") == t["id"] and "score" in e:
            graded.append((t["pkg"], e))
        elif (isinstance(e, dict) and e.get("id") == t["id"] and "retry_after" in e
              and "reason" in e):
            unscannable += 1
    _UNSCANNABLE_COUNT[0] = unscannable
    if queued and not lines:
        lines.append(f"⏳ {queued} dependenc{'y' if queued == 1 else 'ies'} not checked yet: "
                     "AgentAvow has queued the scans; they are reported at a later session start.")
    return lines, graded, throttled, queued


_UNSCANNABLE_COUNT = [0]  # dependencies AgentAvow refused (set by _dep_lines_and_graded)


def _deps_clause(graded: list[tuple[str, dict]], total: int, throttled: bool = False,
                 queued: int = 0) -> str:
    """' Dependencies: checked 12 of 38 — 11 Safe, 1 Review (needs attention: ...).'"""
    if not total:
        return ""
    paused = " (paused: rate limited; continues next session)" if throttled else ""
    if queued:
        paused += f" ({queued} queued for grading)"
    nos = _UNSCANNABLE_COUNT[0]
    if nos:
        paused += f" ({nos} could not be checked)"
    done = len(graded) + nos
    if not done:
        return f" Dependencies: 0 of {total} checked yet{paused}."
    of = f"{done} of {total}" if done < total else f"all {total}"
    out = f" Dependencies: checked {of} — " + _counts(graded)
    worst = _worst(graded)
    if worst:
        name, r = worst
        out += f" (needs attention: '{name}' {_headline(r)}{_why(r)})"
    return out + paused + "."


_RANK = {"do_not_connect": 0, "review": 1, "safe": 2}


def _counts(graded: list[tuple[str, dict]]) -> str:
    """'3 Safe, 1 Review, 0 Don't connect' — the short labels of the three answers."""
    n = {k: 0 for k in _RANK}
    for _, r in graded:
        n[_dval(r)] += 1
    out = f"{n['safe']} Safe, {n['review']} Review"
    return out + (f", {n['do_not_connect']} Don't connect" if n["do_not_connect"] else "")


def _worst(graded: list[tuple[str, dict]]) -> tuple[str, dict] | None:
    """The graded item that needs attention most (Do not connect first, then Review,
    lowest score breaking ties); None when every one is Safe to connect."""
    risky = [g for g in graded if _dval(g[1]) != "safe"]
    if not risky:
        return None
    return min(risky, key=lambda g: (_RANK[_dval(g[1])],
                                     int(g[1].get("score") or 0)))


def _previously_graded(cache: dict, targets: list[dict], deps: list[dict],
                       new_lines: list[str]) -> list[str]:
    """One compact line per server / dependency of THIS session already graded at an
    earlier start, so "show the pre-check" can always answer in full, not only for
    what changed today. Items reported in ``new_lines`` are skipped."""
    out: list[str] = []
    for t in targets:
        e = cache.get(t["name"])
        if not (isinstance(e, dict) and e.get("id") == t["id"]):
            continue
        if any(f"MCP '{t['name']}'" in ln for ln in new_lines):
            continue
        if "score" in e:
            out.append(f"  {_flag(e)} MCP '{t['name']}': {_answer(e)}")
        elif e.get("reason"):
            out.append(f"  ➖ MCP '{t['name']}': not checked ({e['reason']})")
    for t in deps:
        e = cache.get(t["name"])
        if any(f"dependency '{t['pkg']}'" in ln for ln in new_lines):
            continue
        if isinstance(e, dict) and e.get("id") == t["id"] and "score" in e:
            out.append(f"  {_flag(e)} dependency '{t['pkg']}': {_answer(e)}")
        elif isinstance(e, dict) and e.get("id") == t["id"] and e.get("reason"):
            out.append(f"  ➖ dependency '{t['pkg']}': not checked ({e['reason']})")
    return out


_LEGEND = ("Legend: each line leads with one of three answers and its reason. ✅ Safe to "
           "connect. ⚠️ Review before you connect (a high finding, an advisory for this "
           "version, deprecation, or a score under 51). ⛔ Do not "
           "connect (a critical finding, a planted credential leaving the sandbox, or a "
           "known-malicious package). '· Certified' marks a tool that passed the full "
           "Certified gate. ➖ not checked, with the reason. ⏳ still being checked: no "
           "answer yet, asked again next session; its tools run without a grade until then. "
           "Dependencies are already "
           "installed: their answer is advice, never a stop. Do not interpret the raw cache "
           "file; this list is the pre-check.")


def _quiet_context(cache: dict, targets: list[dict], deps: list[dict],
                   not_read: list[str] | None = None) -> None:
    """Nothing new since the last start: say nothing to the person (no systemMessage),
    but give Claude the full graded list so "show the AgentAvow pre-check" answers from
    the same rules as the summary instead of guessing from the cache file. ``not_read``:
    what a cap left unread this start, named at the end of that list."""
    try:
        earlier = _previously_graded(cache, targets, deps, []) + list(not_read or [])
    except Exception:
        return
    if not earlier:
        return
    context = (
        "AgentAvow pre-check: nothing new since the last session start. Do NOT mention "
        "AgentAvow unless the user asks about it. If they ask for the pre-check, this is the "
        "complete current list:\n" + "\n".join(earlier) + "\n" + _LEGEND
        + " Full reports: https://agentavow.com/check")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": context}}))


def _servers_elsewhere(here: list[dict]) -> int:
    """How many scannable servers are configured for OTHER projects on this machine
    (not in this session's list). Reported as a count only; they are graded when
    those projects are opened. 0 on any error, and 0 in Codex (its config.toml has no
    per-project server lists of other folders)."""
    if _in_codex():
        return 0
    try:
        data = _read_json(pathlib.Path.home() / ".claude.json")
        if not isinstance(data, dict) or not isinstance(data.get("projects"), dict):
            return 0
        skip = _cwd_keys()
        have = {t["id"] for t in here}
        elsewhere: dict[str, dict] = {}
        for key, proj in data["projects"].items():
            if key in skip or not isinstance(proj, dict):
                continue
            _take(proj.get("mcpServers"), elsewhere)
        return len({t["id"] for t in elsewhere.values()} - have)
    except Exception:
        return 0


def _advisory_applies(a: object) -> bool:
    """Does a raw advisory entry apply to the installed version? An explicit flag wins
    (the API's raw shape sends ``affects_scanned_version``); otherwise only an advisory
    with no fix counts. A fixed one with no version match is history, not evidence
    against this version."""
    if not isinstance(a, dict):
        return False
    for key in ("affects_scanned_version", "affects_current_version", "current_version_affected"):
        if key in a:
            return bool(a[key])
    return not (a.get("fixed_in") or a.get("fixed") or a.get("fixed_version"))


def _sev(i: dict) -> str:
    return str(i.get("severity") or "").lower()


def _blocking_item(i: dict) -> bool:
    """Item-level mirror of the scanner's blocking rule (src/scanner/verdict.py)."""
    if "malicious" in str(i.get("name") or "").lower() and i.get("kind") != "capability":
        return True
    if i.get("kind") == "capability" or i.get("installed") is False:
        return False
    if i.get("category") == "install_hook":
        return True
    if i.get("category") in ("dependency", "known_vulnerability"):
        return False
    return i.get("shipped") is not False


def _decision(data: dict, advisories: int, incident: bool) -> tuple[str, str, bool]:
    """(decision, reason, final): the API's own ``decision`` when the response carries
    one; else the same rule over what this response has (src/scanner/verdict.decide):
    do_not_connect on a critical finding, a planted credential leaving the sandbox,
    a critical sandbox finding or a malicious package; review on a high finding, an
    advisory for this version, deprecation, or a score under 51; safe otherwise,
    including little code with nothing found (the reason says so). Adoption is never
    an input."""
    dec = data.get("decision")
    if dec in DECISION_PHRASES:
        return (dec, str(data.get("decision_reason") or ""),
                data.get("decision_final") is not False)
    score = int(data.get("trust_score") or 0)
    f = data.get("findings") if isinstance(data.get("findings"), dict) else {}
    items = [i for i in (f.get("items") or []) if isinstance(i, dict)]
    b = data.get("behavioral") if isinstance(data.get("behavioral"), dict) else {}
    pending = bool(b.get("pending"))
    live = bool(b.get("ran")) and not pending and b.get("plan") != "live-probe" \
        and b.get("advisory") is not True
    b_items = [x for x in (b.get("findings") or []) if isinstance(x, dict)] if live else []
    suffix = "; sandbox still running" if pending else ""

    def out(d: str, why: str) -> tuple[str, str, bool]:
        return d, why + suffix, not pending

    def count(sev: str) -> int:
        n = f.get(sev)
        if isinstance(n, int) and not isinstance(n, bool):
            return n
        return sum(1 for i in items if _sev(i) == sev and _blocking_item(i))

    if live and (b.get("canary_exfil") or any(
            x.get("rule") == "credential_canary_exfiltrated" for x in b_items)):
        return out("do_not_connect", "a planted credential left the sandbox")
    if incident or any("malicious" in str(i.get("name") or "").lower() for i in items):
        return out("do_not_connect", "a known-malicious package or dependency")
    if count("critical"):
        return out("do_not_connect", f"{count('critical')} critical finding(s)")
    if any(_sev(x) == "critical" for x in b_items):
        return out("do_not_connect", "the sandbox caught a critical behavior")
    if count("high") or any(_sev(x) == "high" for x in b_items):
        return out("review", "a high finding")
    if advisories:
        return out("review", "a published advisory affects this version")
    if data.get("deprecation"):
        return out("review", "the maintainer has deprecated this package")
    if score < 51:
        return out("review", f"trust score {score}/100 is under 51")
    # A remote MCP server whose tool list could not be read, or was read only in part,
    # reads Review: the tool definitions are what AgentAvow exists to read (Kenne, 10-20).
    gaps = data.get("coverage_gaps") if isinstance(data.get("coverage_gaps"), dict) else {}
    if gaps.get("tool_list_unread") is True:
        return out("review", "the server's tool list could not be read")
    if gaps.get("tool_list_paged") is True:
        return out("review", "only part of the server's tool list could be read")
    files = (data.get("metadata") or {}).get("files_scanned")
    found = any(_sev(i) in ("critical", "high", "medium") and i.get("kind") != "capability"
                for i in items)
    # Thin coverage: 0-7 files read with nothing found (0 = the package held no code,
    # e.g. a metapackage whose code ships in a dependency). Missing files_scanned = unknown.
    if isinstance(files, int) and not isinstance(files, bool) and 0 <= files < 8 \
            and not found:
        remote_mcp = any(isinstance(data.get(k), dict) and data[k].get("surface") == "mcp"
                         for k in ("coverage", "surface_detail"))
        if remote_mcp:
            return out("safe", "tool definitions clean; server code not inspected")
        return out("safe", "nothing found; little code to inspect" if files
                   else "nothing found; no code to inspect")
    return out("safe", "no critical or high findings")


def _legacy_decision(r: dict) -> tuple[str, str]:
    """(decision, reason) for a cache record written before 0.1.20, which stored the
    old verdict, its machine ``reason``, the counts and the score but no decision.
    The same rule as decide() over what the record kept: a critical finding → do not
    connect; a high finding, an advisory, deprecation or a score under 51 → review;
    nothing found → safe, thin coverage included (it says so)."""
    score = int(r.get("score") or 0)
    critical = int(r.get("critical") or 0)
    blocking = int(r.get("blocking") or 0)
    if r.get("incident"):
        return "do_not_connect", "a known-malicious package or dependency"
    if critical:
        return "do_not_connect", f"{critical} critical finding(s)"
    if blocking:
        return "review", f"{blocking} high finding(s)"
    if int(r.get("advisories") or 0):
        return "review", "a published advisory affects this version"
    if r.get("deprecated"):
        return "review", "the maintainer has deprecated this package"
    if score < 51:
        return "review", f"trust score {score}/100 is under 51"
    if r.get("reason") == "thin_coverage":
        return "safe", "nothing found; little code to inspect"
    return "safe", "nothing found" + (" (low signals only)" if r.get("reason") == "low_signals"
                                      else "")


def _dval(r: dict) -> str:
    """The decision value of a verdict / cache record (a pre-0.1.20 record is
    decided from what it stored, see _legacy_decision)."""
    d = r.get("decision")
    if d in DECISION_PHRASES:
        return d
    return _legacy_decision(r)[0]


def _headline(r: dict) -> str:
    """'Safe to connect · Certified' — the answer, with the mark when earned."""
    dval = _dval(r)
    # The mark only ever sits beside Safe to connect.
    return DECISION_PHRASES[dval] + (" · Certified" if r.get("certified") and dval == "safe"
                                     else "")


def _why(r: dict) -> str:
    """' — <the one reason>' for a line; every line, full or compact, carries it."""
    if r.get("decision") in DECISION_PHRASES:
        why = str(r.get("decision_reason") or "")
    else:
        why = _legacy_decision(r)[1]
    return f" — {why}" if why else ""


def _answer(r: dict) -> str:
    """'Review before you connect — one high finding: … · AgentAvow 85/100'."""
    return f"{_headline(r)}{_why(r)} · AgentAvow {r.get('score')}/100"


def _flag(r: dict) -> str:
    return _DECISION_FLAG[_dval(r)]


def _verdict(data: dict) -> dict:
    """The parts of a scan response the hook reports and the gate acts on."""
    score = int(data.get("trust_score") or 0)
    items = (data.get("findings") or {}).get("items") or []
    blocking = sum(1 for i in items if i.get("severity") in ("critical", "high"))
    critical = sum(1 for i in items if i.get("severity") == "critical")
    # Advisories for the installed version. ``advisories_affecting_version`` (MCP shape)
    # is already filtered: count it all. The raw ``advisories`` list is the package's
    # HISTORY (fastapi: a CSRF fixed in 0.65.2, current 0.142.2), so an entry counts
    # only if it says it affects the current version, or has no fix at all.
    adv = data.get("advisories_affecting_version")
    if isinstance(adv, list):
        advisories = len(adv)
    else:
        raw = data.get("advisories") if isinstance(data.get("advisories"), list) else []
        advisories = sum(1 for a in raw if _advisory_applies(a))
    # A past incident (chalk, Sep 2025) only matters if the installed version is affected.
    ih = data.get("incident_history") if isinstance(data.get("incident_history"), dict) else {}
    incident = bool(data.get("incident")) or bool(ih.get("current_version_affected"))
    digests = data.get("tool_digests")
    decision, decision_reason, decision_final = _decision(data, advisories, incident)
    return {
        "stale": bool(data.get("stale")),
        "score": score,
        # The three-phrase answer every line leads with; the gate denies on do_not_connect.
        "decision": decision,
        "decision_reason": decision_reason,
        "decision_final": decision_final,
        # The Certified MARK (the API's display rule: Safe to connect, final, score >= 81,
        # not thin), never the raw provenance gate; a response without it shows no mark.
        "certified": data.get("certified_mark") is True,
        # Legacy two-way field for older cache readers; follows the answer.
        "verdict": "safe" if decision == "safe" else "needs review",
        "reason": str(data.get("verdict_reason") or ""),
        "blocking": blocking,
        "critical": critical,
        "advisories": advisories,
        "incident": incident,
        "tier": str(data.get("trust_tier") or ""),
        "grade": str(data.get("grade") or ""),
        "tool_digests": digests if isinstance(digests, dict) else {},
        "tool_manifest_digest": data.get("tool_manifest_digest") or None,
        "sandbox": _sandbox_summary(data.get("behavioral")),
        "deprecated": bool(data.get("deprecation")),
        # What the scan could not read (``coverage_gaps`` kinds: oversized_files,
        # package_skipped, fetch_failed, tool_list_unread …), so a Safe answer that left
        # part of the target unread can say so at install time.
        "gaps": sorted(k for k, v in (data.get("coverage_gaps") or {}).items()
                       if v and k not in _GAP_METADATA)
        if isinstance(data.get("coverage_gaps"), dict) else [],
    }


# Keys in ``coverage_gaps`` that describe a gap rather than being one (the file cap that
# applied, how many tool-list pages were read, why image layers went unread). Gap kinds
# themselves are counts, booleans or a "failed" string, so they are kept by truthiness.
_GAP_METADATA = frozenset({"file_cap", "pages_read", "image_layers_reason"})


# Package-registry hosts an install always reaches; left out of the one-line network
# clause so it names the hosts the tool itself contacted.
_REGISTRY_HOSTS = frozenset({
    "registry.npmjs.org", "registry.yarnpkg.com", "pypi.org", "files.pythonhosted.org",
    "github.com", "codeload.github.com", "objects.githubusercontent.com",
    "registry-1.docker.io", "auth.docker.io", "production.cloudflare.docker.com",
})
# A behavioral rule in a few words, for "sandbox: CAUGHT <...>".
_RULE_SHORT = {
    "credential_canary_exfiltrated": "a planted credential leaving the sandbox",
    "ssrf_internal_fetch": "following a caller-supplied URL to an internal address",
    "behavioral_undeclared_egress": "undeclared network egress",
    "annotation_readonly_violated": "a read-only tool writing files",
    "annotation_open_world_violated": "closed-world tools reaching the network",
    "canary_echoed_in_result": "a secret echoed in tool output",
    "tool_call_crashed_server": "a tool call crashing the server",
}
_START_SHORT = {
    "needs_credentials": "needs credentials", "missing_binary": "missing a program",
    "no_entrypoint": "no entry point", "resource_limit": "hit the resource limit",
    "install_failed": "install failed", "timeout": "timed out", "crashed": "crashed on start",
}
_SEV = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _needs_what(detail: str) -> str:
    low = (detail or "").lower()
    if any(k in low for k in ("database url", "connection string", "dsn", "postgres")):
        return "needs a database URL"
    if "url" in low:
        return "needs a URL argument"
    if "path" in low or "directory" in low:
        return "needs a path argument"
    return "needs a startup argument"


def _hosts(hosts: list, limit: int = 2) -> str:
    return ", ".join(hosts[:limit]) + (f" +{len(hosts) - limit}" if len(hosts) > limit else "")


def _sandbox_summary(b: object) -> str:
    """One clause about the behavioral sandbox run AgentAvow did on the package (it runs
    automatically on the first scan and is cached for a day): what it caught, what it
    called and where it connected, why the server did not start, or that it is still
    running. Empty when there is nothing to say. Read-only; no extra request."""
    if not isinstance(b, dict):
        return ""
    if b.get("pending") and b.get("state") == "queued":
        pos = b.get("queue_position")
        return "sandbox: waiting for a free slot" + (
            f" (position {pos} in the queue)" if isinstance(pos, int) else "")
    if b.get("pending"):
        return "sandbox: running now, results in about a minute"
    if not b.get("ran") and b.get("state") == "unavailable":
        return "sandbox: unavailable, static analysis only"
    if not b.get("ran"):
        # A run that did not happen is not a clean run: say so (as the MCP output does).
        why = " ".join(str(b.get("reason") or b.get("error") or "").split())[:120]
        return f"sandbox: did not run{f' ({why})' if why else ''}, static analysis only"
    findings = [f for f in (b.get("findings") or []) if isinstance(f, dict)]
    if b.get("canary_exfil") and not any(
            f.get("rule") == "credential_canary_exfiltrated" for f in findings):
        findings.append({"rule": "credential_canary_exfiltrated", "severity": "critical"})
    if findings:
        findings.sort(key=lambda f: (f.get("rule") != "credential_canary_exfiltrated",
                                     _SEV.get(str(f.get("severity")), 4)))
        top = findings[0]
        what = _RULE_SHORT.get(str(top.get("rule") or ""),
                               str(top.get("name") or top.get("rule") or "a behavior"))
        sev = str(top.get("severity") or "")
        more = f" +{len(findings) - 1} more" if len(findings) > 1 else ""
        return f"sandbox: CAUGHT {what}" + (f" ({sev})" if sev else "") + more
    ex = b.get("exercise") if isinstance(b.get("exercise"), dict) else None
    hosts = sorted({str(h) for h in (b.get("egress_hosts") or []) if h} - _REGISTRY_HOSTS)
    net = f"network only {_hosts(hosts)}" if hosts else "no network beyond the registry"
    # A run stopped by its time limit is partial; never let it read as a full run.
    partial = bool(b.get("timed_out") or (ex or {}).get("timed_out"))
    if ex and ex.get("launch_ok"):
        called = len({c.get("tool") for c in (ex.get("calls") or [])
                      if isinstance(c, dict) and c.get("tool")})
        return ("sandbox: " + ("ran partly (hit its time limit), " if partial else "")
                + f"called {called} tool{'' if called == 1 else 's'}, {net}")
    plan = str(b.get("plan") or "")
    if ex is not None or plan.endswith("-mcp"):
        gs = b.get("grade_summary") if isinstance(b.get("grade_summary"), dict) else {}
        reason = str(gs.get("start_reason") or "")
        if reason == "needs_arguments":
            why = _needs_what(str(gs.get("start_reason_detail") or ""))
        else:
            why = _START_SHORT.get(reason, "")
        return "sandbox: not started" + (f" ({why})" if why else "")
    if partial:
        return f"sandbox: ran partly (hit its time limit), {net}"
    return f"sandbox: installed, {net}"


# Cached grades go stale: the API's scoring improves (the 2026-10-08 precision pass moved
# fastapi from 40 to 88) and packages publish new versions under an unchanged pin. A
# cached grade is re-checked when it is older than GRADE_MAX_AGE or was written under an
# older GRADE_EPOCH (bump the epoch whenever server-side scoring changes materially).
# A re-check whose decision (Safe / Review / Do not connect) is unchanged is silent;
# a changed decision is reported, naming the old answer.
GRADE_EPOCH = "2026-10-28"
GRADE_MAX_AGE = 7 * 24 * 3600


def _stale(entry: dict, now: float) -> bool:
    if entry.get("epoch") != GRADE_EPOCH:
        return True
    try:
        return now - float(entry.get("approved_at") or 0) > GRADE_MAX_AGE
    except (TypeError, ValueError):
        return True


def _refresh_only(entry: object, target_id: str, now: float) -> bool:
    """A graded record for this exact target that is due only because it is old (not
    because its definitions drifted): re-check it quietly."""
    return (isinstance(entry, dict) and entry.get("id") == target_id
            and "approved_at" in entry and not _drifted(entry) and _stale(entry, now))


def _record(target: dict, result: dict, now: float) -> dict:
    """The cache entry for a graded server: the target's identity (name is the key,
    id is the sanitized URL or package coordinate), the verdict, the signed per-tool
    digests, the report link, and when it was approved. The gate reads this."""
    # A ``stale`` answer (the API's 7-day copy, served while it refreshes) is shown but
    # not stamped with the current epoch, so the next session start checks again.
    rec = {"id": target["id"], "kind": target["kind"], "approved_at": now,
           "epoch": "stale-copy" if result.get("stale") else GRADE_EPOCH}
    if target["kind"] == "mcp":
        rec["url"] = target["url"]
        rec["report_url"] = (
            f"{WEB}/check/mcp?endpoint={urllib.parse.quote(target['url'], safe='')}")
    else:
        rec["registry"] = target["registry"]
        rec["pkg"] = target["pkg"]
        rec["report_url"] = _package_report_url(target)
        if target.get("version"):
            rec["version"] = target["version"]
        result = dict(result, tool_digests={}, tool_manifest_digest=None)  # not live-served
    rec.update(result)
    return rec


def _package_report_url(target: dict) -> str:
    """The package's report page; a pinned release's page when one is pinned."""
    url = f"{WEB}/check/pkg/{target['registry']}/{target['pkg']}"
    if target.get("version"):
        url += "?version=" + urllib.parse.quote(str(target["version"]), safe="")
    return url


def _drifted(entry: dict) -> bool:
    """True when the gate saw this server serve tool definitions that differ from
    the ones its grade signed. Tools the gate could not hash are left out."""
    seen = entry.get("last_seen")
    approved = entry.get("tool_digests")
    if not isinstance(seen, dict) or not isinstance(approved, dict) or not approved:
        return False
    live = seen.get("tool_digests")
    if not isinstance(live, dict) or not live:
        return False
    skip = set(seen.get("unhashable") or [])
    return {k: v for k, v in approved.items() if k not in skip} != {
        k: v for k, v in live.items() if k not in skip}


def _install_source() -> str:
    # Installed as a plugin, this file sits at <plugin>/scripts/ beside .claude-plugin/.
    plugin_root = pathlib.Path(__file__).resolve().parent.parent
    return "plugin" if (plugin_root / ".claude-plugin").is_dir() else "manual"


# Which hook is calling, for AgentAvow's usage counts only. The install-time hook
# (agentavow_pre_install.py) reuses this module's scan code and sets this to
# "agentavow-preinstall" so install-time checks can be counted apart from session-start
# checks. Nothing else about the request changes.
UA_PRODUCT = "agentavow-precheck"


def _user_agent() -> str:
    # In Codex: "(plugin; codex)", so AgentAvow can count Codex installs apart.
    host = "; codex" if _in_codex() else ""
    return f"{UA_PRODUCT}/{__version__} ({_install_source()}{host})"


# A random install ID, made once per machine, so AgentAvow can count how many installs
# keep using the plugin (an IP address changes and is shared, so it undercounts). It is
# a UUIDv4 from the standard library: nothing about the person, the machine or its files
# goes into it. It rides only on this hook's own requests to agentavow.com (never to an
# MCP server) as one header. AGENTAVOW_ANON_ID=off: no file is made and no header is
# sent. Silent by design: nothing about it is ever printed, and any error means no header.
INSTALL_ID_NAME = "install_id"  # beside scanned.json in ~/.cache/agentavow
INSTALL_ID_ENV = "AGENTAVOW_ANON_ID"
INSTALL_ID_HEADER = "X-AgentAvow-Install"
_UUID4 = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
_install_id_memo: list[str | None] = []  # one lookup per run


def _install_id_off() -> bool:
    return os.environ.get(INSTALL_ID_ENV, "").strip().lower() in ("off", "0", "false", "no")


def _install_id_file() -> pathlib.Path:
    return CACHE.with_name(INSTALL_ID_NAME)


def _read_install_id() -> str | None:
    try:
        text = _install_id_file().read_text(encoding="ascii").strip().lower()
    except Exception:
        return None
    return text if _UUID4.fullmatch(text) else None


def _install_id() -> str | None:
    """This machine's install ID, made on first use (0600, written to a temp file and
    hard-linked into place, so two hooks starting at once agree on one ID and a reader
    never sees half a file). None when switched off or anything fails."""
    if _install_id_off():
        return None
    if _install_id_memo:
        return _install_id_memo[0]
    value = None
    path = _install_id_file()
    try:
        if path.exists():
            value = _read_install_id()  # unreadable or garbled: send nothing, keep the file
        else:
            import uuid

            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            try:
                with os.fdopen(fd, "w", encoding="ascii") as fh:
                    fh.write(str(uuid.uuid4()) + "\n")
                try:
                    os.link(tmp, path)  # fails if another hook got there first
                except FileExistsError:
                    pass
            finally:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
            value = _read_install_id()
    except Exception:
        value = None
    _install_id_memo.append(value)
    return value


def _headers() -> dict:
    headers = {"User-Agent": _user_agent()}
    iid = _install_id()
    if iid:
        headers[INSTALL_ID_HEADER] = iid
    return headers


# Once a UTC day, one small "active" request so AgentAvow can count the machines the
# plugin protects. Most session starts answer from the cache and send nothing, so the
# scan requests alone miss most protected machines. It carries the install ID (as the
# header above), the plugin version and the app type, and nothing else: no tool, server,
# path or repo name. Same opt-out as the install ID (AGENTAVOW_ANON_ID=off): no ID, no
# request. The day is written to the hook state before sending, so it never goes twice
# in a day; a failure is not retried until the next day. Silent, 2 s at most, and it
# runs beside the pre-check, so it never holds the session up.
ACTIVE_URL = "https://agentavow.com/api/v1/public/plugin/active"
ACTIVE_UA = "agentavow-active"  # its own User-Agent: never counted as a scan or a check
ACTIVE_TIMEOUT = 2  # seconds
ACTIVE_DAY_KEY = "active_day"  # meta: the UTC day the active request was last sent
APP_TYPES = ("desktop", "cli", "sdk", "cloud", "other")


def _app_type() -> str:
    """CLAUDE_CODE_ENTRYPOINT reduced to one of APP_TYPES, the same grouping AgentAvow
    applies to Claude Code's own User-Agent (scripts/ops/anthropic_traffic_snapshot.py)."""
    ep = os.environ.get("CLAUDE_CODE_ENTRYPOINT", "").strip().lower()
    if ep.startswith("remote"):
        return "cloud"
    if ep in ("claude-desktop", "local-agent") or ep.startswith("desktop"):
        return "desktop"
    if ep.startswith("sdk"):
        return "sdk"
    if ep == "cli" or ep.startswith(("claude-vscode", "claude-jetbrains")) or "ide" in ep:
        return "cli"
    return "other"


def _active_due(now: float) -> str | None:
    """The install ID when today's active request is still to send, after recording
    today in the hook state; None when it went already today, is switched off, or the
    state can't be written (so it can never repeat)."""
    if _install_id_off():
        return None
    day = time.strftime("%Y-%m-%d", time.gmtime(now))
    cache = _load_cache()
    meta = cache.get(META_KEY) if isinstance(cache.get(META_KEY), dict) else {}
    if meta.get(ACTIVE_DAY_KEY) == day:
        return None
    iid = _install_id()
    if not iid:
        return None
    cache[META_KEY] = dict(meta, **{ACTIVE_DAY_KEY: day})
    return iid if _save_cache(cache) else None


def _send_active(iid: str) -> None:
    body = json.dumps({"version": __version__, "app": _app_type()}).encode("utf-8")
    req = urllib.request.Request(ACTIVE_URL, data=body, method="POST", headers={
        "User-Agent": f"{ACTIVE_UA}/{__version__}",
        "Content-Type": "application/json",
        INSTALL_ID_HEADER: iid,
    })
    try:
        with urllib.request.urlopen(req, timeout=ACTIVE_TIMEOUT):  # noqa: S310 (https only)
            pass
    except Exception:
        pass  # fail-open and silent


def _start_active() -> threading.Thread | None:
    """Send today's active request on a background thread; None when not due."""
    try:
        iid = _active_due(time.time())
        if not iid:
            return None
        t = threading.Thread(target=_send_active, args=(iid,), daemon=True)
        t.start()
        return t
    except Exception:
        return None


def _fetch(path: str, params: dict) -> dict:
    url = f"{API}{path}?{urllib.parse.urlencode(params)}" if params else f"{API}{path}"
    req = urllib.request.Request(url, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310 (https only)
            data = json.load(resp)
            if resp.status == 202 or (isinstance(data, dict) and data.get("status") == "queued"):
                raise _QueuedError(str((data.get("detail") if isinstance(data, dict) else "")
                                       or "queued"))
            return data
    except urllib.error.HTTPError as e:
        # 4xx (bar rate limiting) is the API's answer about the target, not a hiccup.
        if 400 <= e.code < 500 and e.code not in (408, 429):
            reason = ""
            try:
                body = json.loads(e.read() or b"{}")
                reason = str(body.get("detail") or "") if isinstance(body, dict) else ""
            except Exception:
                reason = ""
            raise _UnscannableError(reason or str(e.code)) from e
        raise


def _scan(target: dict, force: bool = False, stored: bool = False) -> dict:
    """``stored``: ask for the last stored grade only (instant, no fresh scan, no
    fresh-scan budget); the API refreshes in the background and answers 202 → _QueuedError
    when it has nothing yet. Used for dependencies, which are many and already installed."""
    if target["kind"] == "mcp":
        params = {"endpoint": target["url"]}
        if force:
            params["force"] = "true"  # the definitions changed; a cached grade is stale
        return _verdict(_fetch("/mcp", params))
    params = {"stored": "true"} if stored else {}
    if target.get("version"):
        params["version"] = str(target["version"])  # the pinned release, not the latest
    return _verdict(_fetch(f"/package/{target['registry']}/{target['pkg']}", params))


def _load_cache() -> dict:
    try:
        data = json.loads(CACHE.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(cache: dict) -> bool:
    """Write the whole file at once (temp file + rename) so a gate call running at
    the same moment never reads a half-written file."""
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE.with_name(f"{CACHE.name}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(cache))
        os.replace(tmp, CACHE)
        return True
    except Exception:
        return False


def _intro_message() -> str:
    if _in_codex():
        return ("AgentAvow: nothing to grade here yet — no MCP servers it can grade and no "
                "package.json, requirements.txt, pyproject.toml or Cargo.toml in this folder. "
                "Add a server (for example `codex mcp add <name> --url <https url>` or "
                "`codex mcp add <name> -- npx <package>`) and it is checked before it is added "
                "and again at your next session start; open a project and its direct "
                "dependencies are checked too. To check any tool right now, ask Codex "
                '"is <tool> safe?" or open https://agentavow.com/check.')
    how = (
        "run /agentavow-trust:scan <MCP URL | npm or pypi package | owner/repo>"
        if _install_source() == "plugin"
        else 'ask Claude "is <tool> safe?" or open https://agentavow.com/check'
    )
    return ("AgentAvow: nothing to grade here yet — no MCP servers it can grade and no "
            "package.json, requirements.txt, pyproject.toml or Cargo.toml in this folder. "
            "Add a server (for example "
            "`claude mcp add <name> <https url>` or `claude mcp add <name> -- npx <package>`) "
            "and it is checked before it is added and again at your next session start; open "
            "a project and its direct dependencies are checked too. To check any tool right "
            f"now, {how}.")


INSTALL_STATS_KEY = "install_checks"  # written by agentavow_pre_install.py (STATS_KEY there)


def _install_clause(cache: dict) -> str:
    """' Since the last session AgentAvow checked 4 package installs — all Safe to
    connect.' from the install-time hook's counter in the meta entry, then reset it.
    Empty when nothing was installed (most session starts stay exactly as they were)."""
    meta = cache.get(META_KEY)
    if not isinstance(meta, dict):
        return ""
    st = meta.get(INSTALL_STATS_KEY)
    if not isinstance(st, dict):
        return ""
    try:
        n, flagged = int(st.get("count") or 0), int(st.get("flagged") or 0)
    except (TypeError, ValueError):
        n, flagged = 0, 0
    meta = dict(meta)
    meta.pop(INSTALL_STATS_KEY, None)
    cache[META_KEY] = meta
    if n <= 0:
        return ""
    what = f"{n} package install{'' if n == 1 else 's'}"
    if not flagged:
        return f" Since the last session AgentAvow checked {what} — all Safe to connect."
    return (f" Since the last session AgentAvow checked {what}; {flagged} needed a look "
            "(reported at the time).")


def _print_install_only(clause: str) -> None:
    """The quiet line when the install counter is the only news: one sentence for the
    person, and Claude is asked to relay it once."""
    print(json.dumps({
        "systemMessage": "AgentAvow: " + clause,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                "AgentAvow install checks. The user has NOT seen this. At the start of your "
                f"first reply, in one short line, tell them: \"AgentAvow: {clause}\" Then "
                "carry on; do not mention it again."),
        },
    }))


def _show_intro_once() -> None:
    """On the first session with nothing to scan, tell the user so (a silent hook
    looks broken) and how to scan on demand. Shown once per machine, recorded in
    the cache; if the cache can't be written it is not shown, so it can never nag.
    No request is made."""
    cache = _load_cache()
    meta = cache.get(META_KEY)
    if isinstance(meta, dict) and meta.get("intro_shown"):
        return
    cache[META_KEY] = dict(meta if isinstance(meta, dict) else {}, intro_shown=__version__)
    if _save_cache(cache):
        print(json.dumps({"systemMessage": _intro_message()}))


def _fine_message(cache: dict, targets: list[dict]) -> str:
    """'AgentAvow: your 3 tools are fine — all Safe to connect. …' for a session in a
    folder with nothing of its own (no project servers, no dependencies) whose servers
    (your user-scope servers and the ones your plugins bring) were all graded earlier.
    Empty when any server here belongs to the project, or none has a grade yet."""
    if not targets or any(t.get("scope") not in ("user", "plugin") for t in targets):
        return ""
    graded = []
    for t in targets:
        e = cache.get(t["name"])
        if isinstance(e, dict) and e.get("id") == t["id"] and "score" in e:
            graded.append((t["name"], e))
    if not graded:
        return ""
    n = len(graded)
    tools = f"{n} tool{'' if n == 1 else 's'}"
    tail = (" Open a project folder and its direct dependencies are checked too. "
            "Ask for the AgentAvow pre-check for details.")
    worst = _worst(graded)
    if not worst:
        return (f"AgentAvow: your {tools} {'is' if n == 1 else 'are'} fine — "
                f"{'Safe' if n == 1 else 'all Safe'} to connect." + tail)
    name, r = worst
    return (f"AgentAvow: your {tools}: {_counts(graded)} "
            f"(needs attention: '{name}' {_headline(r)}{_why(r)})." + tail)


FINE_SHOWN_KEY = "fine_shown_day"  # meta: the day the "your N tools" line was last shown


def _show_fine_once_a_day(cache: dict, targets: list[dict], now: float) -> bool:
    """In a folder with nothing of its own, say once a day what the person's own tools
    read, instead of the intro line or silence. Shown to the person only; recorded in
    the cache so it never repeats that day (and is skipped if the cache can't be
    written). No request. True when shown."""
    msg = _fine_message(cache, targets)
    if not msg:
        return False
    day = time.strftime("%Y-%m-%d", time.localtime(now))
    meta = cache.get(META_KEY) if isinstance(cache.get(META_KEY), dict) else {}
    if meta.get(FINE_SHOWN_KEY) == day:
        return False
    cache[META_KEY] = dict(meta, **{FINE_SHOWN_KEY: day})
    if not _save_cache(cache):
        return False
    earlier = _previously_graded(cache, targets, [], [])
    print(json.dumps({
        "systemMessage": msg,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                "AgentAvow pre-check: nothing new since the last session start; the user was "
                f"shown: \"{msg}\" Do NOT mention AgentAvow unless the user asks about it. If "
                "they ask for the pre-check, this is the complete current list:\n"
                + "\n".join(earlier) + "\n" + _LEGEND
                + " Full reports: https://agentavow.com/check"),
        },
    }))
    return True


def _waiting_clause(pending: int, timed_out: int, alone: bool) -> str:
    """'1 still being checked; its answer shows next session' and/or '1 not graded:
    check timed out'. ``alone``: nothing was graded, so the clause names the servers."""
    parts = []
    if pending:
        noun = f"MCP server{'' if pending == 1 else 's'} " if alone else ""
        parts.append(f"{pending} {noun}still being checked; "
                     f"{'its answer shows' if pending == 1 else 'their answers show'} "
                     "next session")
    if timed_out:
        noun = f"MCP server{'' if timed_out == 1 else 's'} " if alone else ""
        parts.append(f"{timed_out} {noun}not checked: check timed out")
    return "; ".join(parts)


def _summary(graded: list[tuple[str, dict]], elsewhere: int = 0, deps: str = "",
             servers_present: bool = True, server_news: bool = True,
             pending: int = 0, timed_out: int = 0) -> str:
    """One line a person can act on: how many servers were graded, how many are safe,
    and the one that needs attention most, then the dependency clause. Shown as the
    hook's systemMessage and relayed by Claude at the top of its first reply.
    ``elsewhere`` = servers configured for other projects, mentioned so nothing looks
    silently skipped. ``servers_present`` False = this project has no MCP servers and
    the line is about dependencies only."""
    n = len(graded)
    tail = (f" {elsewhere} more MCP server{'' if elsewhere == 1 else 's'} configured for other "
            "projects, checked when you open them." if elsewhere else "")
    if not servers_present:
        return ("AgentAvow pre-check: no MCP servers in this project." + deps
                + " Ask for the AgentAvow pre-check for details." + tail)
    if not n and not server_news:
        # Every server was already graded; only dependencies are new this time.
        return ("AgentAvow pre-check: MCP servers unchanged." + deps
                + " Ask for the AgentAvow pre-check for details." + tail)
    if not n and (pending or timed_out):
        return ("AgentAvow pre-check: " + _waiting_clause(pending, timed_out, True) + "."
                + deps + " Ask for the AgentAvow pre-check for details." + tail)
    if not n:
        return ("AgentAvow pre-check: a configured MCP server could not be scanned; "
                "ask for the AgentAvow pre-check for details." + deps + tail)
    parts = [f"AgentAvow pre-check: checked {n} MCP server{'' if n == 1 else 's'} — "
             + _counts(graded)]
    worst = _worst(graded)
    if worst:
        name, r = worst
        parts.append(f" (needs attention: '{name}' {_headline(r)}{_why(r)})")
    if pending or timed_out:
        parts.append("; " + _waiting_clause(pending, timed_out, False))
    parts.append("." + deps + " Ask for the AgentAvow pre-check for details." + tail)
    return "".join(parts)


def _is_cached(entry: object, target_id: str, now: float) -> bool:
    """A graded target is cached as a record ({"id", "approved_at", verdict, ...})
    and stays cached until the gate reports its definitions drifted. An unscannable
    one is cached as {"id", "retry_after"} until that time passes. A withheld URL is
    cached as its id string. A bare id string for a graded target was written by a
    version before the gate existed and carries no verdict, so it is graded once more."""
    if isinstance(entry, str):
        return entry == target_id and target_id.startswith("withheld:")
    if not isinstance(entry, dict) or entry.get("id") != target_id:
        return False
    if "approved_at" in entry:
        return not _drifted(entry) and not _stale(entry, now)
    try:
        return now < float(entry.get("retry_after") or 0)
    except (TypeError, ValueError):
        return False


def _stored_fallback(t: dict, e: BaseException, started: float) -> dict | None:
    """A package server whose fresh scan did not answer in time: ask for its stored
    grade instead (instant when the catalog has one; 202 queues a background scan).
    None when there is no answer yet, no time left, or the target is a live URL."""
    if t["kind"] != "package" or isinstance(e, _QueuedError):
        return None
    if time.monotonic() - started + TIMEOUT > BUDGET:
        return None
    try:
        return _scan(t, stored=True)
    except Exception:
        return None


def _pending(cache: dict, t: dict, entry: object, now: float, asked: bool,
             lines: list[str]) -> str:
    """Record and report a server that has no answer yet. A server already graded for
    this id keeps its grade (a routine re-check that ran out of time says nothing): "".
    Otherwise the cache holds {"id", "pending_since", "tries"} (never read as a grade,
    so the next start asks again and the gate treats it as ungraded) and the line says
    it is still being checked: "pending". Past PENDING_MAX_TRIES requests or
    PENDING_MAX_AGE it is reported once as timed out and then left alone for
    RETRY_UNSCANNABLE, like an unscannable server: "timed_out"."""
    if isinstance(entry, dict) and entry.get("id") == t["id"] and "approved_at" in entry:
        return ""
    coord = _target_coord(t)
    prior = entry if (isinstance(entry, dict) and entry.get("id") == t["id"]
                      and "pending_since" in entry) else {}
    try:
        since = float(prior.get("pending_since") or now)
        tries = int(prior.get("tries") or 0)
    except (TypeError, ValueError):
        since, tries = now, 0
    tries += 1 if asked else 0
    if tries >= PENDING_MAX_TRIES or now - since >= PENDING_MAX_AGE:
        cache[t["name"]] = {"id": t["id"], "retry_after": now + RETRY_UNSCANNABLE,
                            "reason": "check timed out"}
        lines.append(f"➖ MCP '{t['name']}' ({coord}): not checked: check timed out — "
                     "AgentAvow had no answer after several session starts; it is checked "
                     "again in a week. Scan it on demand at https://agentavow.com/check.")
        return "timed_out"
    cache[t["name"]] = {"id": t["id"], "pending_since": since, "tries": tries}
    lines.append(f"⏳ MCP '{t['name']}' ({coord}): still being checked — AgentAvow had no "
                 "answer within this session start's time limit; its answer shows next "
                 "session. Until then its tools run without a grade.")
    return "pending"


def main() -> None:
    started = time.monotonic()
    active = _start_active()
    try:
        _main()
    finally:
        if active is not None:  # wait for it only up to ACTIVE_TIMEOUT from the start
            active.join(max(0.0, ACTIVE_TIMEOUT - (time.monotonic() - started)))


def _main() -> None:
    payload = None
    _NOT_READ.clear()
    try:
        payload = json.load(sys.stdin)  # the SessionStart payload: ``cwd`` is the session folder
    except Exception:
        payload = None
    try:
        _set_session_cwd(payload)
    except Exception:
        pass
    _set_host(payload)

    try:
        targets = _targets()
    except Exception:
        return
    try:
        deps = _dependency_targets()
    except Exception:
        deps = []
    if not targets and not deps:
        cache = _load_cache()
        clause = _install_clause(cache)
        if clause and _save_cache(cache):
            _print_install_only(clause.strip())
            return
        _show_intro_once()
        return

    cache = _load_cache()
    install_clause = _install_clause(cache)
    started = time.monotonic()
    now = time.time()
    results: dict[str, dict | None] = {}  # id -> verdict, None = unscannable
    lines: list[str] = []
    graded: list[tuple[str, dict]] = []  # (server name, verdict) for the summary line
    pending = timed_out = 0  # servers still being checked / given up on, this session
    for t in targets:
        entry = cache.get(t["name"])
        if _is_cached(entry, t["id"], now):
            continue
        regraded = isinstance(entry, dict) and _drifted(entry)
        refresh = _refresh_only(entry, t["id"], now)
        if t["kind"] == "withheld":
            cache[t["name"]] = t["id"]
            lines.append(f"➖ MCP '{t['name']}' ({t['host']}): not scanned — its URL looks "
                         "like it contains a secret, so it was not sent to AgentAvow.")
            continue
        coord = _target_coord(t)
        if t["id"] not in results:  # the same coordinate under two names scans once
            if time.monotonic() - started > BUDGET:
                # Out of time: not asked this session. Said, not silently skipped.
                state = _pending(cache, t, entry, now, asked=False, lines=lines)
                pending += state == "pending"
                timed_out += state == "timed_out"
                continue
            try:
                results[t["id"]] = _scan(t, force=regraded)
            except _UnscannableError:
                results[t["id"]] = None
            except Exception as e:
                slow = _no_answer_yet(e)
                answer = _stored_fallback(t, e, started) if slow else None
                if answer is None:
                    if slow:
                        state = _pending(cache, t, entry, now, asked=True, lines=lines)
                        pending += state == "pending"
                        timed_out += state == "timed_out"
                    continue  # fail-open; no answer, so never cached as graded
                results[t["id"]] = answer
        result = results[t["id"]]
        if result is None:
            cache[t["name"]] = {"id": t["id"], "retry_after": now + RETRY_UNSCANNABLE}
            lines.append(f"➖ MCP '{t['name']}' ({coord}): not scanned — AgentAvow "
                         "couldn't read it (it may need sign-in).")
            continue
        cache[t["name"]] = _record(t, result, now)
        if refresh and _dval(result) == _dval(entry):
            continue  # routine re-check, same answer: nothing to say
        graded.append((t["name"], result))
        changed = ("its tool definitions changed since the last grade; re-checked: "
                   if regraded else
                   f"updated grade (was: {_answer(entry)}): " if refresh else "")
        sandbox = f"; {result['sandbox']}" if result.get("sandbox") else ""
        lines.append(f"{_flag(result)} MCP '{t['name']}' ({coord}): {changed}"
                     f"{_answer(result)}{sandbox}.")

    server_lines = len(lines)
    dep_clause = ""
    if deps:
        try:
            dep_lines, dep_graded, throttled, queued = _dep_lines_and_graded(
                cache, deps, now, started)
            lines += dep_lines
            dep_clause = _deps_clause(dep_graded, len(deps), throttled, queued)
            if throttled and not lines:
                lines.append("➖ dependencies: the AgentAvow API rate-limited this session start; "
                             "grading continues next session.")
        except Exception:
            pass  # fail-open: the dependency pass can never break the server report

    _save_cache(cache)
    if not lines:
        if install_clause:
            _print_install_only(install_clause.strip())
            return
        try:
            if not deps and not _NOT_READ and _show_fine_once_a_day(cache, targets, now):
                return
        except Exception:
            pass
        _quiet_context(cache, targets, deps, list(_NOT_READ))
        return
    lines += _NOT_READ  # what a cap left unread, named (never silent)

    try:
        elsewhere = _servers_elsewhere(targets)
    except Exception:
        elsewhere = 0
    summary = _summary(graded, elsewhere, dep_clause, servers_present=bool(targets),
                       server_news=bool(server_lines), pending=pending,
                       timed_out=timed_out) + install_clause
    try:
        earlier = _previously_graded(cache, targets, deps, lines)
    except Exception:
        earlier = []
    if earlier:
        lines.append("Checked at an earlier session start (unchanged since):")
        lines += earlier
    context = (
        "AgentAvow pre-check — new MCP servers and direct dependencies checked before you "
        "rely on them.\n"
        "The user has NOT seen this (hook output is not displayed to them). At the very "
        "start of your first reply in this session, before anything else, tell them in one "
        f"or two lines: \"{summary}\" Then carry on with whatever they asked. If they want "
        "details, use the lines below; do not repeat the summary in later replies.\n"
        + "\n".join(lines)
        + "\n" + _LEGEND + " Full reports: https://agentavow.com/check"
    )
    print(json.dumps({
        "systemMessage": summary,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
