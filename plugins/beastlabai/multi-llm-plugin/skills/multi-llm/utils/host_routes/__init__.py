"""Package routes: a second way in, and the one thing ``--check`` never asked.

A host may load this skill from a package (npm for OpenCode, the codex
marketplace for Codex) as well as from a file shim. One resolver per
``package.registry`` answers whether that route is installed:
:mod:`utils.host_routes.npm` and :mod:`utils.host_routes.codex`.
``host_install.package_route`` dispatches to them and ``--check`` prints the note.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple


@dataclass
class PackageRoute:
    """What a package-route probe found, if a package route exists at all."""

    #: The spec string exactly as the host config declares it.
    spec: str
    #: The package name — the spec minus a trailing ``@<range>``, scope kept.
    name: str
    #: The one location that would hold the resolved payload.
    payload: Optional[Path]
    #: Whether that location exists.
    resolved: bool
    #: The config file the declaration was read from.
    declared_in: Path
    #: Which ``package.registry`` resolver produced this — the key
    #: :data:`_NOTE_FORMS` and the row-1 carve-out are selected by.
    registry: str = "npm"
    #: Activation, where the host records it separately from installation (the
    #: codex ``[plugins."<id>"]`` table's ``enabled``). ``None`` is "not
    #: recorded", which on npm is every route: a listed spec *is* the activation.
    enabled: Optional[bool] = None
    #: Every *other* install of the same package the resolver found — on codex,
    #: the same plugin carried by a second marketplace. Never a guess at which
    #: one the host loads.
    siblings: Tuple["PackageRoute", ...] = ()
    #: The installed version the host reported, or ``None`` when nothing that
    #: was read says (a ``config.toml`` table carries activation only).
    version: Optional[str] = None
    #: What the route was read from, in words the note can print.
    evidence: str = ""
    #: Version directories beside the one the host reported — leftovers, named
    #: and never ranked. Only ever filled when a version was reported *and* its
    #: directory answered, so "newest wins" is never inferred.
    leftovers: Tuple[Path, ...] = ()


#: What the route note says, per registry and per state. **User-facing copy
#: with one owner**: the codex sentences are D5's table, the npm ones are the
#: sentences this note has always printed. Neither registry's words survive on
#: the other — "re-run the host with a network connection" is false for a
#: marketplace copy, and "replaces the file shim's wholesale" is false where
#: both skills are advertised.
_NOTE_FORMS: Dict[str, Dict[str, str]] = {
    "npm": {
        "unresolved": (
            "a package route is DECLARED but did not resolve: "
            "{declared_in} lists '{spec}', and no payload is "
            "installed{where}. On this host that failure is silent — the entry "
            "stays listed and the exit code is 0 — so nothing is loading from "
            "it. Re-run the host with a network connection, or remove the entry."
        ),
        "package_only": (
            "installed as a package: {declared_in} lists '{spec}', "
            "resolved at {payload}. Rows 2-4 grade a file shim and there "
            "is none to grade."
        ),
        "both": (
            "BOTH routes are installed. {declared_in} lists '{spec}' "
            "(resolved at {payload}), and the package's command replaces the "
            "file shim's wholesale at startup — so the file below is dead weight: "
            "still on disk, never invoked, and the host reports nothing about it. "
            "Remove it with `{uninstall}`."
        ),
    },
    "codex-marketplace": {
        # `{activation}` is "enabled" only when activation was READ as true;
        # an unread activation says so rather than guessing (D5).
        "enabled_known": (
            "installed as a codex plugin: '{spec}' version {version}, "
            "{activation}, at {payload} ({evidence})."
        ),
        "enabled_unknown": (
            "installed as a codex plugin: '{spec}', {activation}; version and "
            "install directory unknown ({evidence})."
        ),
        "two_copies": (
            " Two copies of this skill are advertised — `multi-llm:multi-llm` "
            "from the plugin and `multi-llm` from this file shim, with "
            "different baked paths. Keep one: `codex plugin remove {spec}` "
            "removes the plugin, `{uninstall} --global` removes the shim."
        ),
        "leftover": (
            " {leftover} is also on disk: a leftover from an earlier install, "
            "not the version codex loads."
        ),
        "disabled": (
            "installed as a codex plugin but disabled: '{spec}' is not "
            "advertised, so the file route is the only surface ({evidence})."
        ),
        "several": (
            "{ids} are ALL installed: more than one marketplace carries this "
            "plugin, and each advertises its own `multi-llm:multi-llm`, so "
            "which one a session uses is not something `--check` can tell. "
            "Keep one — `codex plugin remove <pluginId>` removes the others."
        ),
        "python3_missing": (
            "`python3` is not on this PATH, so the plugin's server cannot "
            "start: the skill is advertised and its `multi_llm` tool never "
            "appears. The server needs `python3` >= {floor}, under that name."
        ),
        "python3_below_floor": (
            "`python3` on this PATH is {interpreter} (Python {found}), below "
            "the plugin server's floor of {floor}: the server cannot start, so "
            "the skill is advertised and its `multi_llm` tool never appears."
        ),
    },
}
