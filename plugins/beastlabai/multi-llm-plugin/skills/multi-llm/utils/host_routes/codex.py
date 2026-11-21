"""The codex-marketplace route resolver and its note (D5).

The one piece of per-host logic that is code rather than data: it reads Codex's
own ``codex plugin list --json`` and ``config.toml``. Used by
``host_install.package_route`` through its ``_ROUTE_RESOLVERS`` table, and by
``host_install.package_route_note`` for the note.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import _NOTE_FORMS, PackageRoute


# ---------------------------------------------------------------------------
# The codex-marketplace resolver (D5): plugin list -> config.toml scan -> stat
# ---------------------------------------------------------------------------

#: The plugin server's own interpreter floor. **A copy, not the owner**: the
#: owner is ``MIN_PYTHON`` in ``packaging/codex/ingestion_rules.py``, and this
#: module cannot import it because the skill tree ships inside the plugin
#: *without* ``packaging/``. ``tests/test_codex_route.py`` asserts the two agree
#: whenever that module is present. Deliberately below the payload's own
#: ``requires-python``: that one is uv's to satisfy, while nothing fetches an
#: interpreter for the server, which runs on the bare ``python3`` on ``PATH``.
CODEX_SERVER_MIN_PYTHON: Tuple[int, int] = (3, 9)

#: Seconds ``codex plugin list --json`` gets before its answer is abandoned and
#: the ``config.toml`` scan answers instead. Short on purpose: this is a note on
#: a check, and a wedged host binary must not wedge ``--check`` with it.
CODEX_LIST_TIMEOUT_S = 10

#: The two files that make a version directory a payload rather than a husk
#: (``cache/<marketplace>/`` survives a remove as an empty directory, R25).
_CODEX_PAYLOAD_MARKERS: Tuple[str, ...] = (
    os.path.join("skills", "multi-llm", "SKILL.md"),
    ".mcp.json",
)


def codex_home(env: Optional[Dict[str, str]] = None) -> Optional[Path]:
    """``${CODEX_HOME:-$HOME/.codex}`` — codex's own root, never plain ``HOME``."""
    environment = os.environ if env is None else env
    explicit = environment.get("CODEX_HOME")
    if explicit:
        return Path(explicit)
    home = environment.get("HOME") or environment.get("USERPROFILE")
    return Path(home) / ".codex" if home else None


def _codex_payload_dir(
    root: Path, marketplace_name: str, plugin: str, version: str
) -> Path:
    """``<codex home>/plugins/cache/<marketplaceName>/<plugin>/<version>`` (B3)."""
    return root / "plugins" / "cache" / marketplace_name / plugin / version


def _codex_payload_answers(path: Path) -> bool:
    """Step 3: one stat per marker, never a directory listing."""
    return all((path / marker).is_file() for marker in _CODEX_PAYLOAD_MARKERS)


def _codex_plugin_list(
    env: Optional[Dict[str, str]],
) -> Optional[List[Dict[str, Any]]]:
    """Step 1: the entries ``codex plugin list --json`` prints, or ``None``.

    ``None`` means *the binary did not answer* — absent, non-zero, timed out,
    unparsable, or a shape this reader does not know — and every one of those
    falls through to the ``config.toml`` scan. An empty list is an answer: the
    host says nothing is installed.
    """
    environment = dict(os.environ if env is None else env)
    search = environment.get("PATH")
    if search is None:
        return None
    binary = shutil.which("codex", path=search)
    if not binary:
        return None
    try:
        completed = subprocess.run(
            [binary, "plugin", "list", "--json"],
            capture_output=True, text=True, env=environment,
            timeout=CODEX_LIST_TIMEOUT_S, stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if completed.returncode != 0:
        return None
    try:
        document = json.loads(completed.stdout)
    except (ValueError, TypeError):
        return None
    # Recorded on codex 0.156.1 (container row 5, run 20260923T191255Z):
    # `{"installed": [...], "available": [...]}`, each entry with `source` and
    # `marketplaceSource` objects and no `installedPath`. Only the `installed`
    # array is read — an `available` row is a catalog entry, never an install.
    # A bare array is tolerated too; anything else is "did not answer" rather
    # than "nothing installed".
    if isinstance(document, dict):
        document = document.get("installed")
    if not isinstance(document, list):
        return None
    return [item for item in document if isinstance(item, dict)]


def _strip_toml_comment(line: str) -> str:
    """Drop from the first ``#`` that is not inside a double-quoted string."""
    in_string = False
    index = 0
    while index < len(line):
        char = line[index]
        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "#":
            return line[:index]
        index += 1
    return line


_TOML_ENABLED_KEY_RE = re.compile(r"^enabled[ \t]*=")
_TOML_ENABLED_RE = re.compile(r"^enabled[ \t]*=[ \t]*(true|false)$")
_TOML_TOP_LEVEL_PLUGINS_RE = re.compile(r"^plugins[ \t]*=")


def _is_plugins_family_header(line: str) -> bool:
    """Whether a trimmed ``[`` line opens ``[plugins]`` or a table under it.

    Deliberately loose about spacing and quoting — ``[ plugins . "x" ]``,
    ``["plugins".x]``, ``[[plugins…]]`` all count — because this decides
    where a near-miss is *looked for*, and a wider net only abstains more.
    """
    compact = re.sub(r"[ \t]", "", line).lstrip("[")
    if compact[:1] in ("'", '"'):
        compact = compact[1:]
    return compact.startswith("plugins") and compact[7:8] in ("]", ".", "'", '"')


class _Abstain(Exception):
    """The file is outside the scan's grammar: say nothing rather than guess."""


def _scan_codex_config(
    config: Path, plugin: str
) -> Optional[List[Tuple[str, Optional[bool]]]]:
    """Step 2: ``[(pluginId, enabled), …]`` from ``config.toml``, or ``None``.

    A table-header scan, not a TOML parser (``tomllib`` is 3.11+ and the
    payload's floor is lower), so its grammar is written down and nothing
    outside it is guessed at:

    - lines, each comment-stripped outside double-quoted strings, then trimmed;
      an empty remainder is skipped;
    - the header is byte-exact — ``[plugins."<plugin>@<marketplace>"]`` — and any
      other ``[`` line ends the current block;
    - ``enabled`` is read only inside a matched block, as ``enabled = true`` or
      ``false`` with optional spaces/tabs around ``=``, the key case-sensitive;
    - anything else that could carry the answer — a second ``enabled``, a
      non-boolean value, a near-miss header, a dotted or inline entry, a
      top-level ``plugins =`` — makes the whole read **abstain** (``None``),
      and so does a matched header whose block has no readable ``enabled``;
    - the id is matched on a name boundary (``x-multi-llm@…`` is another
      plugin), and a non-header line naming it abstains only at the top level
      or under a ``[plugins]``-family header — an ``[mcp_servers.*]`` args
      entry naming our id carries no activation and is not read;
    - a leading UTF-8 BOM is not part of the first line.

    An empty list means the file answered and holds no table: removed.
    Abstaining and "no file" both return ``None`` / ``[]`` respectively, and
    neither ever becomes a *removed* verdict for a table that exists.
    """
    try:
        raw = config.read_bytes()
    except OSError:
        return []
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None
    marker = f"{plugin}@"
    prefix = f'[plugins."{marker}'
    # Name-boundary anchored: `x-multi-llm@…` names a different plugin.
    names_ours = re.compile(
        r"(?<![A-Za-z0-9_.\-])" + re.escape(marker)
    ).search
    in_plugins_family = True  # the top level can carry `plugins.…` keys too
    found: List[Tuple[str, Optional[bool]]] = []
    current: Optional[str] = None
    enabled: Optional[bool] = None
    seen_enabled = False
    seen_header = False

    def close() -> None:
        if current is None:
            return
        if not seen_enabled:
            # The table exists; its activation is unreadable. Not a removal.
            raise _Abstain()
        found.append((current, enabled))

    try:
        for original in text.splitlines():
            line = _strip_toml_comment(original).strip()
            if not line:
                continue
            if line.startswith("["):
                close()
                current, enabled, seen_enabled = None, None, False
                seen_header = True
                in_plugins_family = _is_plugins_family_header(line)
                if (
                    line.startswith(prefix) and line.endswith('"]')
                    and len(line) > len(prefix) + 2
                    and '"' not in line[len(prefix):-2]
                ):
                    plugin_id = line[len('[plugins."'):-2]
                    if any(existing == plugin_id for existing, _ in found):
                        raise _Abstain()  # a duplicate table is not valid TOML
                    current = plugin_id
                elif in_plugins_family and names_ours(line):
                    raise _Abstain()  # a near-miss header: padded, single-quoted…
                continue
            if not seen_header and _TOML_TOP_LEVEL_PLUGINS_RE.match(line):
                raise _Abstain()  # `plugins = { … }` at the top level
            if in_plugins_family and names_ours(line):
                raise _Abstain()  # a dotted or inline entry under [plugins]
            if current is None:
                continue
            if _TOML_ENABLED_KEY_RE.match(line):
                match = _TOML_ENABLED_RE.match(line)
                if match is None or seen_enabled:
                    raise _Abstain()
                seen_enabled = True
                enabled = match.group(1) == "true"
        close()
    except _Abstain:
        return None
    return found


def _codex_route(
    host_id: str,
    entry: Dict[str, Any],
    package: Dict[str, Any],
    *,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> Optional[PackageRoute]:
    """The codex plugin route: list first, ``config.toml`` second, stat third.

    Every step is keyed on ``CODEX_HOME`` (falling back to ``~/.codex`` exactly
    as codex does), and the npm route's JSON/XDG helpers are not consulted.
    The path is **computed, never globbed**: ``plugin list`` reports
    ``marketplaceName`` and ``version``, the one directory those name is stat'ed
    once, and a missing field or a directory that does not answer leaves the
    path unknown rather than picking one of the sibling version directories a
    cache can hold at once. ``None`` is silence: removed, or unanswerable.
    """
    root = codex_home(env)
    if root is None:
        return None
    plugin = package["name"]
    config = root / "config.toml"

    listed = _codex_plugin_list(env)
    if listed is not None:
        routes: List[PackageRoute] = []
        for item in listed:
            plugin_id = item.get("pluginId")
            if not isinstance(plugin_id, str):
                continue
            left, sep, right = plugin_id.partition("@")
            if left != plugin or not sep or not right:
                continue
            if item.get("installed") is False:
                continue  # a catalog row, not an install
            marketplace_name = item.get("marketplaceName")
            version = item.get("version")
            enabled = item.get("enabled")
            payload: Optional[Path] = None
            leftovers: Tuple[Path, ...] = ()
            if isinstance(marketplace_name, str) and marketplace_name and (
                isinstance(version, str) and version
            ):
                candidate = _codex_payload_dir(
                    root, marketplace_name, plugin, version
                )
                if _codex_payload_answers(candidate):
                    payload = candidate
                    parent = candidate.parent
                    try:
                        leftovers = tuple(sorted(
                            child for child in parent.iterdir()
                            if child.is_dir() and child.name != version
                        ))
                    except OSError:
                        leftovers = ()
            routes.append(PackageRoute(
                spec=plugin_id,
                name=plugin,
                payload=payload,
                resolved=payload is not None,
                declared_in=config,
                registry="codex-marketplace",
                enabled=enabled if isinstance(enabled, bool) else None,
                version=version if isinstance(version, str) and version else None,
                evidence="read from `codex plugin list --json`",
                leftovers=leftovers,
            ))
        if not routes:
            return None  # the host answered: nothing installed
        if routes[0].enabled is None:
            # The list omitted activation; the table is activation evidence.
            scanned = _scan_codex_config(config, plugin) or []
            table = dict(scanned)
            routes = [
                _with_enabled(route, table.get(route.spec)) for route in routes
            ]
        routes.sort(key=lambda route: route.enabled is not True)
        primary = routes[0]
        return _with_siblings(primary, tuple(routes[1:]))

    scanned = _scan_codex_config(config, plugin)
    if not scanned:
        return None  # removed, or abstaining — both are silence
    routes = [
        PackageRoute(
            spec=plugin_id,
            name=plugin,
            payload=None,
            resolved=False,
            declared_in=config,
            registry="codex-marketplace",
            enabled=enabled,
            version=None,
            evidence=(
                f"read from `{config}`; run `codex plugin list --json` to "
                "resolve them"
            ),
        )
        for plugin_id, enabled in scanned
    ]
    routes.sort(key=lambda route: route.enabled is not True)
    return _with_siblings(routes[0], tuple(routes[1:]))


def _with_enabled(route: PackageRoute, enabled: Optional[bool]) -> PackageRoute:
    return replace(route, enabled=enabled)


def _with_siblings(
    route: PackageRoute, siblings: Tuple[PackageRoute, ...]
) -> PackageRoute:
    return replace(route, siblings=siblings)


def _python3_problem(env: Optional[Dict[str, str]]) -> Optional[str]:
    """The codex plugin server's interpreter, as seen from this ``PATH``.

    ``None`` when it resolves at or above the floor — or when this process was
    handed no ``PATH`` to judge by, since "missing" would then be an invention.
    """
    environment = os.environ if env is None else env
    search = environment.get("PATH")
    if search is None:
        return None
    # `uv run` (the documented way to run this check) activates the skill's
    # own venv: it sets ``VIRTUAL_ENV`` and puts that venv's ``bin`` first on
    # ``PATH``, and every venv carries a ``python3``. Codex never sees that
    # entry — it launches the server from the user's own ``PATH`` — so it is
    # dropped here, or a machine with no ``python3`` at all reads as green
    # (measured 2026-09-24, Phase 1 row 9(c): the same home, the same PATH,
    # named the missing interpreter under the venv's python directly and said
    # nothing under ``uv run``).
    venv = environment.get("VIRTUAL_ENV")
    if venv:
        activated = {
            os.path.normcase(os.path.realpath(os.path.join(venv, name)))
            for name in ("bin", "Scripts")
        }
        search = os.pathsep.join(
            entry for entry in search.split(os.pathsep)
            if not entry
            or os.path.normcase(os.path.realpath(entry)) not in activated
        )
    floor = ".".join(str(part) for part in CODEX_SERVER_MIN_PYTHON)
    interpreter = shutil.which("python3", path=search)
    if not interpreter:
        return _NOTE_FORMS["codex-marketplace"]["python3_missing"].format(
            floor=floor
        )
    try:
        completed = subprocess.run(
            [interpreter, "--version"], capture_output=True, text=True,
            timeout=CODEX_LIST_TIMEOUT_S, stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    match = re.search(
        r"Python\s+(\d+)\.(\d+)(?:\.\d+)?",
        (completed.stdout or "") + (completed.stderr or ""),
    )
    if not match:
        return None
    found = (int(match.group(1)), int(match.group(2)))
    if found >= CODEX_SERVER_MIN_PYTHON:
        return None
    return _NOTE_FORMS["codex-marketplace"]["python3_below_floor"].format(
        interpreter=interpreter, found=f"{found[0]}.{found[1]}", floor=floor
    )


def _codex_note(
    route: PackageRoute,
    *,
    file_present: bool,
    uninstall: str,
    env: Optional[Dict[str, str]],
) -> str:
    """The codex-marketplace half of ``host_install.package_route_note``.

    *uninstall* is ``host_install.uninstall_line`` for this host, spelled by
    the caller so this module needs nothing from the check.
    """
    forms = _NOTE_FORMS["codex-marketplace"]
    installs = (route,) + route.siblings
    if len(installs) > 1:
        return forms["several"].format(
            ids=" and ".join(f"'{item.spec}'" for item in installs)
        )
    words = {
        "spec": route.spec,
        "version": route.version,
        "payload": route.payload,
        "evidence": route.evidence,
        "uninstall": uninstall,
        "activation": (
            "enabled" if route.enabled is True
            else "activation not recorded"
        ),
    }
    if route.enabled is False:
        return forms["disabled"].format(**words)
    if route.payload is not None and route.version:
        note = forms["enabled_known"].format(**words)
        for leftover in route.leftovers:
            note += forms["leftover"].format(leftover=leftover)
    else:
        note = forms["enabled_unknown"].format(**words)
    if route.enabled is None:
        # Installed, activation unread: no collision is claimed on a guess.
        return note
    if file_present:
        note += forms["two_copies"].format(**words)
    problem = _python3_problem(env)
    if problem:
        note += "\n" + problem
    return note
