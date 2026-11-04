#!/usr/bin/env python3
"""The reader for ``hosts/capabilities.yaml`` (D5b).

Three things live here, and nothing else:

* **Loading and validating** the capability data, cached per base directory
  because ``status`` must stay sub-second and every mode pays this on the way in.
* **Resolving a host id** — ``--host <id>`` (baked into a shim at install time),
  else ``$MULTI_LLM_HOST``, else ``claude-code``. An unknown id is exit 3 listing
  the ones that exist; Python **never sniffs the environment to guess its host**.
* **Rendering the sentences a host's capability decides** — the three verb
  sentences a shim bakes in (one fixed phrasing per enum value) and, on the same
  principle, the recovery instruction a failed batch prints (:func:`retry_instruction`,
  addressed by ``multi_turn`` to whoever that host leaves able to follow it).
  This is the whole point of the indirection: the capability is resolved to one
  concrete imperative *here*, in Python, so the driving agent resolves nothing
  and the matrix is never on an agent read path.

``providers.yaml`` ``driver.*`` is user config and always wins over anything here;
this file states *facts about hosts* and ships with the skill.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:  # normal import (utils is a package)
    from .cli_common import skill_dir
    from .unattended import NeedsHuman
except ImportError:  # pragma: no cover - direct script runs with utils/ on path
    from cli_common import skill_dir  # type: ignore
    from unattended import NeedsHuman  # type: ignore


#: Relative to the skill root. Ships inside the skill so a shim can name the
#: instruction core and the dispatcher by path from one installed artifact.
CAPABILITIES_FILE = os.path.join("hosts", "capabilities.yaml")
SCHEMA_FILE = os.path.join("schemas", "host_capabilities.schema.json")

#: The reference host. An omitted ``--host`` reproduces pre-capability-data
#: behavior exactly, which is what keeps the flag strictly additive.
DEFAULT_HOST = "claude-code"

#: Env fallback, for a host that invokes ``multi_llm.py`` directly rather than
#: through a rendered shim. Explicitly *set* by a user or an installer — never
#: detected.
HOST_ENV = "MULTI_LLM_HOST"

#: The closed verb vocabulary, identical in all three places it appears: the
#: wording in ``instructions/*.md``, the fields below, and the three shim slots.
VERBS: Tuple[str, ...] = ("subagents", "ask", "detach")

#: Verb -> the wording the instruction core uses for it. Asserted against the
#: core's own text by ``tests/test_instruction_portability.py``.
VERB_WORDING: Dict[str, str] = {
    "subagents": "spawn subagents",
    "ask": "ask the user",
    "detach": "run detached",
}

#: The profiles the Python-side executor needs from a runner. A runner that can
#: only ``generate`` cannot stand in for a subagent (D3e).
EXECUTOR_PROFILES: Tuple[str, ...] = ("agent-readonly", "agent-write")

#: Every key a consumer indexes on a host entry **without** a ``.get`` fallback —
#: here, in ``utils/host_install.py``, in ``hosts/render_capabilities.py`` and in
#: the executor. It is the schema's own ``definitions.host.required`` list, minus
#: nothing: ``schemas/host_capabilities.schema.json`` requires every field except
#: ``shim_max_lines``, ``headless_invocation`` and ``package``, each of which
#: governs a lint or a generated document rather than a dispatch. (``next_command``
#: decides no dispatch either, but ``utils/next_phase.py`` reads it at run time to
#: build output, so it is required like ``invocation``.) Restated here as a plain tuple
#: because :func:`load` must not need ``jsonschema`` — a dev-only extra — nor a
#: second file present to give a clean error; ``tests/test_host_capabilities.py``
#: asserts the two lists still agree, so the drift is caught at test time and the
#: runtime dependency surface stays at ``pyyaml``.
REQUIRED_HOST_KEYS: Tuple[str, ...] = (
    "arguments",
    "ask",
    "default_subagent_runner",
    "detach",
    "env_guards",
    "install_paths",
    "installable",
    "invocation",
    "max_concurrent_subagents",
    "next_command",
    "multi_turn",
    "native_tool",
    "nested_exec",
    "provenance",
    "reload",
    "runners",
    "session_runner_provider",
    "shim",
    "subagent_tiers",
    "subagents",
    "timeout_ceiling_s",
    "timeout_override",
)

#: The repair line every structural complaint ends on. The data ships *inside* the
#: skill, so a document that fails these checks is not something a user edited
#: into a bad state — it is a partial or corrupt install.
_CORRUPT_INSTALL = (
    "       The capability data ships with the skill and is not user config, so a "
    "malformed\n"
    "       one means a partial or corrupt install; reinstall the skill."
)

_CACHE: Dict[str, Dict[str, Any]] = {}


class UnknownHost(NeedsHuman):
    """An unrecognized ``--host`` id: exit 3, never a silent default."""


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load(base: Optional[str] = None) -> Dict[str, Any]:
    """The parsed capability document, cached per base directory and shape-checked.

    The check is deliberately structural rather than a schema validation: it
    asserts the document is a mapping, that ``hosts`` holds at least one entry,
    and that each entry carries every key in :data:`REQUIRED_HOST_KEYS` — the keys
    consumers index directly. ``schemas/host_capabilities.schema.json`` stays the
    full contract and is enforced by CI; what this adds is a *runtime* floor, so a
    malformed file is one ``NeedsHuman`` naming the file and the missing key at
    load rather than a ``KeyError('max_concurrent_subagents')`` surfacing from
    somewhere mid-dispatch, minutes into a fan-out, with nothing on it to say
    which file was wrong. Running it here rather than in :func:`entry` also means
    a broken *sibling* host is caught by the run that never names it.

    It runs once per base directory: the cache is populated only after the checks
    pass, so ``status`` keeps paying a parse and a handful of set operations
    exactly once and every later call is a dict lookup.
    """
    root = str(base) if base else str(skill_dir())
    cached = _CACHE.get(root)
    if cached is not None:
        return cached
    import yaml

    path = os.path.join(root, CAPABILITIES_FILE)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            document = yaml.safe_load(handle) or {}
    except OSError as exc:
        raise NeedsHuman(
            f"ERROR: host capability data is missing or unreadable: {path}\n"
            f"       ({exc})\n"
            "       The install looks corrupt or partial; reinstall the skill."
        ) from exc
    except yaml.YAMLError as exc:
        # Without this the parser's own exception escapes as an unhandled crash
        # (exit 1, a traceback) rather than as this project's "needs a human"
        # exit 3 — and the traceback names the parser, not the install.
        raise NeedsHuman(
            f"ERROR: host capability data is not valid YAML: {path}\n"
            f"       ({exc})\n"
            f"{_CORRUPT_INSTALL}"
        ) from exc
    _validate_document(document, path)
    _CACHE[root] = document
    return document


def _validate_document(document: Any, path: str) -> None:
    """The runtime floor :func:`load` applies. Raises ``NeedsHuman`` or returns."""
    if not isinstance(document, dict):
        raise NeedsHuman(
            f"ERROR: host capability data is not a mapping: {path}\n"
            f"       (parsed as {type(document).__name__})\n"
            f"{_CORRUPT_INSTALL}"
        )
    hosts = document.get("hosts")
    if not isinstance(hosts, dict) or not hosts:
        raise NeedsHuman(
            f"ERROR: host capability data declares no hosts: {path}\n"
            "       `hosts:` must be a mapping of at least one host id to its "
            "capability entry.\n"
            f"{_CORRUPT_INSTALL}"
        )
    for host_id, host in sorted(hosts.items()):
        if not isinstance(host, dict):
            raise NeedsHuman(
                f"ERROR: host capability entry '{host_id}' is not a mapping: "
                f"{path}\n"
                f"       (parsed as {type(host).__name__})\n"
                f"{_CORRUPT_INSTALL}"
            )
        missing = [key for key in REQUIRED_HOST_KEYS if key not in host]
        if missing:
            raise NeedsHuman(
                f"ERROR: host capability entry '{host_id}' is incomplete: {path}\n"
                f"       Missing: {', '.join(missing)}\n"
                "       Every capability is required — an absent one would be a "
                "silent guess about\n"
                "       what this host can do, which is the whole reason the data "
                "exists.\n"
                f"{_CORRUPT_INSTALL}"
            )


def clear_cache() -> None:
    """Drop the cache (tests that point at a fixture tree)."""
    _CACHE.clear()


def host_ids(base: Optional[str] = None) -> Tuple[str, ...]:
    return tuple(load(base).get("hosts", {}))


def entry(host_id: str, base: Optional[str] = None) -> Dict[str, Any]:
    """One host's capability profile, or exit 3 naming the ids that exist."""
    hosts = load(base).get("hosts", {})
    if host_id not in hosts:
        raise UnknownHost(
            f"ERROR: unknown host '{host_id}'.\n"
            f"       Known hosts: {', '.join(sorted(hosts))}\n"
            "       --host names an entry in hosts/capabilities.yaml; it is baked "
            "into a shim by `install-host`, not guessed at run time."
        )
    return hosts[host_id]


#: The ``next_command`` key a ``None`` route reads: the route the host's
#: ``invocation`` cell documents (plans/next-phase-command.md §2.1, "One route
#: vocabulary").
DEFAULT_ROUTE_KEY = "default"


def next_command_routes(host_id: str, base: Optional[str] = None) -> Tuple[str, ...]:
    """The route keys *host_id*'s ``next_command`` cell carries, in file order."""
    return tuple(entry(host_id, base).get("next_command") or {})


def next_command_template(
    host_id: str, route: Optional[str], base: Optional[str] = None
) -> str:
    """The next-phase command template for *host_id* on *route*.

    ``None`` reads ``default``; a route key the host carries returns its
    template. **It never falls back**: any other route raises ``ValueError``
    naming the host and the route. Falling back is done once, in
    ``utils.next_phase.resolve_route``, which already turns an unset or invalid
    ``MULTI_LLM_ROUTE`` into ``None``; a route that reaches this accessor with no
    key on the host is a caller bug, and a silent default would print a
    plausible wrong spelling. The provenance never gates use: the template is
    display text with no conservative alternative, so a ``documented`` cell is
    returned like a ``verified`` one.
    """
    cell = entry(host_id, base).get("next_command") or {}
    key = DEFAULT_ROUTE_KEY if route is None else route
    template = cell.get(key)
    if not isinstance(template, str) or not template:
        raise ValueError(
            f"host '{host_id}' has no next_command template for route "
            f"'{key}' (it carries: {', '.join(cell) or 'none'})"
        )
    return template


def next_command_prefix(
    host_id: str, route: Optional[str], base: Optional[str] = None
) -> str:
    """The text before ``{args}`` in :func:`next_command_template` — the route's
    invocation prefix (the schema pins every template to end in ``{args}``)."""
    template = next_command_template(host_id, route, base)
    return template[: template.index("{args}")]


def resolve_host_id(
    argv: Optional[Sequence[str]] = None,
    *,
    explicit: Optional[str] = None,
) -> str:
    """``--host`` → ``$MULTI_LLM_HOST`` → :data:`DEFAULT_HOST`.

    Nothing here inspects the environment for *evidence* of a host — an env var a
    user or installer sets is a declaration, a sniffed process tree would be a
    guess (D5b: "Python never sniffs the environment to guess its host").
    """
    if explicit:
        return explicit
    if argv:
        try:
            from .cli_common import flag_value
        except ImportError:  # pragma: no cover
            from cli_common import flag_value  # type: ignore
        found = flag_value(argv, "--host")
        if found:
            return found
    return os.environ.get(HOST_ENV) or DEFAULT_HOST


# ---------------------------------------------------------------------------
# Derived facts consumers ask for
# ---------------------------------------------------------------------------

#: The startup slack a command must leave below a host's ``timeout_ceiling_s``.
#:
#: It lives **here**, beside the ceilings it is subtracted from, rather than in
#: ``run_status`` where it is spent, because it is spent in two unrelated
#: registers: ``status --wait`` clamps its own resolved deadline to
#: ``ceiling - margin`` (``run_status._resolve_wait_timeout``, which re-exports
#: this name), and a Claude Code poll has to give the **tool call around** the
#: command a timeout of ``interval + margin``. Both are "the cap is not the
#: budget; process start, ``load_config``, the checkpoint read and a 5 s re-check
#: grid all come out of it".
#:
#: F6, 2026-09-20: ``run_status``'s own comment claimed the number was "named
#: once here rather than twice so the two cannot drift" while ``30`` was spelled
#: out in six places — this constant's predecessor, the ``native`` *run detached*
#: sentence below, ``SKILL.md``, ``references/host-capabilities.md`` and four
#: instruction cores. The sentence is rendered from the constant now, which
#: carries the two generated copies with it (``SKILL.md`` is byte-compared to it,
#: ``references/host-capabilities.md`` is generated from it), and the four cores
#: are pinned against the constant in ``tests/test_instruction_portability.py``.
WAIT_CAP_MARGIN_S = 30.0


def max_concurrent_subagents(host_id: str, base: Optional[str] = None) -> int:
    """The host-side leg of D3i's three-way minimum."""
    return int(entry(host_id, base)["max_concurrent_subagents"])


def timeout_ceiling_s(host_id: str, base: Optional[str] = None) -> int:
    """How long one *foreground* command may run here before the host kills it.

    ``0`` is not a cap of zero — it is the documented "no cap" value (codex ships
    it, `hosts/capabilities.yaml`), the same falsy special case
    ``host_install.timeout_note`` and ``render_capabilities._timeout_cell``
    already make. Every caller therefore has to test truthiness before
    subtracting anything from it, or a host with no documented cap becomes the
    tightest one in the file.

    The one runtime consumer is ``status --wait``'s clamp: ``capabilities.yaml``'s
    own "not on any agent read path" note names ``multi_llm.py`` as a legitimate
    reader, so resolving the ceiling *here* rather than baking a number into a
    rendered surface is exactly the indirection this module exists for.
    """
    try:
        return int(entry(host_id, base).get("timeout_ceiling_s") or 0)
    except (TypeError, ValueError):  # pragma: no cover - schema keeps this an int
        return 0


def tightest_timeout_ceiling(
    base: Optional[str] = None
) -> Optional[Tuple[str, int]]:
    """``(host_id, ceiling)`` for the smallest **non-zero** cap in the file.

    What an *unrouted* command clamps against. A poll that names no ``--host``
    could be running under any of them, so skipping the clamp entirely would let
    it overshoot some host's cap by accident; the tightest declared cap is the
    only bound that holds whichever host it turns out to be. Hosts declaring
    ``0`` are skipped rather than winning as the minimum, per
    :func:`timeout_ceiling_s`. ``None`` when no host declares one at all.
    """
    capped = [
        (host_id, timeout_ceiling_s(host_id, base))
        for host_id in host_ids(base)
    ]
    live = [(host_id, ceiling) for host_id, ceiling in capped if ceiling]
    if not live:
        return None
    # Ties broken by host id, so the reported host is stable across runs.
    return min(live, key=lambda pair: (pair[1], pair[0]))


def executor_capable_runners(
    host_id: str, base: Optional[str] = None
) -> List[str]:
    """Runners in this host's entry that can actually back the executor (D3e)."""
    runners = entry(host_id, base).get("runners", {})
    return sorted(
        name
        for name, spec in runners.items()
        if set(spec.get("profiles", ())) & set(EXECUTOR_PROFILES)
    )


def require_executor_runner(host_id: str, base: Optional[str] = None) -> None:
    """Refuse ``--exec-subagents`` on a host with no executor-capable runner.

    A flag that silently does nothing is worse than a refusal: the phase would
    stop at a dispatch marker waiting for a subagent nobody is going to start,
    until the host's shell cap kills it. The list comes from the data, so adding a
    runner is a YAML edit rather than a code change.
    """
    if executor_capable_runners(host_id, base):
        return
    host = entry(host_id, base)
    raise NeedsHuman(
        f"ERROR: --exec-subagents is not available on host '{host_id}'.\n"
        "       The executor needs a runner declaring the "
        f"{' or '.join(EXECUTOR_PROFILES)} profile, and this host's entry "
        f"declares none (runners: {', '.join(sorted(host.get('runners', {}))) or 'none'}).\n"
        "       Configure one under `driver.subagent_runner` in providers.yaml, or "
        "drop --exec-subagents and let this host's own subagent mechanism run the "
        "phase."
    )


#: The three lists every ``env_guards`` block declares (D3c/D5b).
ENV_GUARD_LISTS: Tuple[str, ...] = ("guards", "session_scoped", "passthrough")


def env_guards(host_id: str, base: Optional[str] = None) -> Dict[str, List[str]]:
    """This host's declared child-env guards (D3c/D5b), always three lists.

    ``guards`` are the nested-session markers a dispatched runner must not
    inherit, ``session_scoped`` the ids that would make a child join or overwrite
    the parent's session, and ``passthrough`` the names the host *sanctions* for
    the runner (a credential the runner legitimately needs), which therefore
    survive the strip. Literal names only — the schema rejects a ``*``, because a
    prefix sweep would take the runner's own credentials with it.
    """
    declared = entry(host_id, base).get("env_guards") or {}
    return {
        name: [str(value) for value in (declared.get(name) or ())]
        for name in ENV_GUARD_LISTS
    }


#: The three independent ways a host can stop a dispatched runner (D3c), in the
#: order every consumer reports them.
NESTED_EXEC_LEGS: Tuple[str, ...] = ("spawn", "network", "credentials")


def nested_exec(host_id: str, base: Optional[str] = None) -> Dict[str, str]:
    """This host's declared ``nested_exec`` verdict, always the three legs + notes.

    ``spawn`` is "may this host's shell start a third-party agent CLI at all",
    ``network`` is "can that CLI reach its provider API from inside the sandbox",
    ``credentials`` is "can it read its own auth store" — each
    ``allowed | needs-config | denied | unknown``, with ``notes`` naming the flag
    or setting that grants it. A missing or unreadable block reads as ``unknown``
    on every leg rather than as ``allowed``: the executor's preflight probes an
    ``unknown`` leg with a throwaway dispatch (D3c), and defaulting to ``allowed``
    would silently skip exactly that probe.
    """
    declared = entry(host_id, base).get("nested_exec") or {}
    states = {
        leg: str(declared.get(leg) or "unknown") for leg in NESTED_EXEC_LEGS
    }
    states["notes"] = str(declared.get("notes") or "").strip()
    return states


def is_multi_turn(host_id: str, base: Optional[str] = None) -> bool:
    """Does this host leave the driving agent able to act on a command's output?

    ``multi_turn`` is one boolean over two mechanisms — a further tool call
    inside the same invocation, or a conversation the next invocation resumes —
    because every consumer asks the same single question: *after this command
    returns, is an agent still there to read it and do something?* Either
    mechanism answers that yes; a host that answers no ends its invocation with
    the command it ran, so the output is read by a human and by nobody else.
    """
    return bool(entry(host_id, base)["multi_turn"])


def is_free_text_ask(host_id: str, base: Optional[str] = None) -> bool:
    return entry(host_id, base)["ask"] == "free-text"


def ask_class(host_id: str, base: Optional[str] = None) -> str:
    return str(entry(host_id, base)["ask"])


# ---------------------------------------------------------------------------
# The package route's install pin — which version a generated page names
# ---------------------------------------------------------------------------

class PackagePinError(NeedsHuman):
    """``package.version`` / ``package.public_version`` disagree with the
    provenance row, or with each other."""


def _release_precedence(version: str) -> Tuple[Tuple[int, ...], int, Tuple[Any, ...]]:
    """SemVer precedence for the schema's version pattern, as a sortable key.

    Build metadata is ignored, a pre-release sorts below its release, and
    pre-release identifiers compare as SemVer orders them: numeric below
    alphanumeric, and a shorter list below a longer one it prefixes.
    """
    core = version.split("+", 1)[0]
    numbers, _, pre = core.partition("-")
    release = tuple(int(part) for part in numbers.split("."))
    if not pre:
        return (release, 1, ())
    identifiers = tuple(
        (0, int(item), "") if item.isdigit() else (1, 0, item)
        for item in pre.split(".")
    )
    return (release, 0, identifiers)


def package_spec_version(host: Dict[str, Any]) -> Optional[str]:
    """The version a generated install paragraph pins for *host*'s package, or
    ``None`` when the route pins none (``update: reinstall``).

    TWO VERSIONS, BECAUSE THE CANDIDATE IS NOT THE RELEASE. ``package.version``
    copies the shared version, so it moves at every bump, while the published
    package is still the previous version. A paragraph built from it at
    ``verified`` would recommend a spec the registry does not serve yet, from the
    bump through publication and the registry check, and for as long as either
    fails. On this host that failure is silent: the plugin stays listed, the
    exit code is 0, and nothing loads. So:

    * before ``provenance.package`` is ``verified``, the paragraph is the
      "not yet published" one and names the candidate, ``version``;
    * at ``verified`` it is the recommendation and names ``public_version``, the
      last version whose registry record validated, which moves only after
      that check passes.

    The schema pairs ``public_version`` with the provenance row, but no JSON
    Schema keyword compares two versions, so the ordering half is checked here:
    a public pin newer than the candidate means one of them was hand-edited
    past the other. The pairing is re-checked as well, so a caller that never
    ran the schema (the renderer, in a checkout without the dev extra) still
    refuses. Not part of :func:`load`'s runtime floor: ``package`` governs
    generated documentation only, and a malformed one must never be able to
    stop a dispatch.
    """
    package = host.get("package") or {}
    provenance = (host.get("provenance") or {}).get("package", "unknown")
    version = package.get("version")
    public = package.get("public_version")
    pinned = package.get("update") == "pinned-spec"
    if public is None:
        if pinned and provenance == "verified":
            raise PackagePinError(
                f"ERROR: package '{package.get('name')}' is `verified` but has no "
                "`public_version`.\n"
                "       A verified paragraph recommends a spec, and the only "
                "version it may name is the\n"
                "       last one whose registry record validated. Set "
                "`public_version` to that version."
            )
        return version
    if provenance != "verified":
        raise PackagePinError(
            f"ERROR: package '{package.get('name')}' carries `public_version: "
            f"{public}` while its provenance is `{provenance}`.\n"
            "       No registry install has been verified, so there is no public "
            "version to name.\n"
            "       Remove it; it is set in the same edit that promotes "
            "`provenance.package`."
        )
    if not pinned or version is None:
        raise PackagePinError(
            f"ERROR: package '{package.get('name')}' carries `public_version` on "
            f"an `update: {package.get('update')}` route with "
            f"`version: {version}`.\n"
            "       Only a `pinned-spec` route has a pin to recommend."
        )
    if _release_precedence(public) > _release_precedence(version):
        raise PackagePinError(
            f"ERROR: package '{package.get('name')}' has `public_version: "
            f"{public}` newer than `version: {version}`.\n"
            "       `version` is the candidate and follows the shared version; "
            "`public_version` trails it\n"
            "       and moves only after that version's registry record "
            "validates."
        )
    return public


# ---------------------------------------------------------------------------
# Verb resolution — one fixed phrasing per enum value
# ---------------------------------------------------------------------------
# These strings ARE the shim's answer to each capability verb. `install-host`
# fills `{{spawn_subagents}}` / `{{ask_user}}` / `{{run_detached}}` from them at
# the same moment it bakes `{SKILL_DIR}` and `--host <id>`, and the Claude Code
# shim — the one nobody renders — is asserted byte-identical to what they produce
# for the `claude-code` entry. One phrasing per value, no interpolation beyond the
# tool name, so "the reference host cannot drift from the data that governs every
# other host" is a byte comparison rather than a review note.

_SUBAGENTS = {
    "native": (
        "**Spawn subagents** — call your host's own subagent tool `{tool}`: when the "
        "task carries `task.prompt_path`, tell the subagent to read that file in "
        "full — through line `task.prompt_lines`, paging if one read returns fewer "
        "— and follow it verbatim, printing only what it asks; if the file is "
        "absent, or the task has no `prompt_path`, pass `task.prompt` verbatim. "
        "Take the role from `task.subagent_type` when your tool needs one, and "
        "write the JSON it returns to `task.output_path`. Never pass "
        "`--exec-subagents` on this host."
    ),
    "executor": (
        "**Spawn subagents** — run the dispatcher with `--exec-subagents`: it "
        "dispatches every materialized task itself and continues past each marker "
        "in the same process. Never spawn a subagent by hand on this host."
    ),
    "none": (
        "**Spawn subagents** — run the dispatcher with `--exec-subagents`. This "
        "host has no subagent mechanism of its own, so a run that cannot use the "
        "executor is refused rather than degraded."
    ),
}

_ASK = {
    "structured": (
        "**Ask the user** — call your host's own structured question tool "
        "`{tool}`, then copy the selected option's command verbatim. Never compose "
        "a flag from the user's words."
    ),
    "free-text": (
        "**Ask the user** — print the numbered option block exactly as the "
        "dispatcher rendered it and copy the selected option's command verbatim, "
        "and only under `--interactive`. Otherwise the documented `--yes` default "
        "applies and nothing is asked."
    ),
    "none": (
        "**Ask the user** — never. This host has no reliable user channel, so "
        "every gate resolves from its documented `--yes` default and "
        "`--interactive` is exit 3."
    ),
}

# T8 (2026-09-20): the `native` sentence used to stop at the launch, and the
# launch is the only part of this host's loop the agent could get right without
# being told. A native background run writes no `run` record, so `status` can
# never hand it a terminal verdict (`no_run` is not in `TERMINAL_VERDICTS`) — the
# loop is bounded by the background mechanism's own completion signal, and the
# poll in between is a timed progress snapshot rather than a verdict read. Both
# numbers a poll needs are stated here because neither is in `capabilities.yaml`:
# the `--host` the wait clamp reads (with no launcher-printed command there is
# nothing to copy it from, and its absence silently clamps every poll to the
# tightest declared ceiling) and the per-call timeout, which is a tool parameter
# and therefore none of `host_install.TIMEOUT_CHANNELS`.
#
# That second number is interpolated from `WAIT_CAP_MARGIN_S` rather than typed,
# so the margin `status --wait` subtracts from a ceiling and the margin a poll
# adds to its call timeout are the same number by construction (F6, 2026-09-20).
# `SKILL.md` is byte-compared to this sentence and `references/host-capabilities.md`
# is generated from it, so both follow the constant without a second edit.
#
# F-2026-09-21: what it never said is what *unit* that tool parameter takes, and
# on the only host this template renders for it is **milliseconds** (the Bash
# tool's `timeout`: 120000 by default, 600000 at the cap). An agent that read
# the interval-plus-margin figure as seconds and passed `330` got a 0.33 s
# call, killed before `status` could answer — and rule 2 below then told it to
# re-issue with the right call timeout, so the loop span rather than polled.
# The sentence names the unit and one worked value now, both derived from the
# same constant rather than typed: the widest interval it offers is 300 s, so
# the largest number it can ever ask for is 330000, well under the cap. The
# unit is host-specific while this template is keyed by the *resolution*, so
# `tests/test_host_capabilities.py` fails if a second host ever resolves
# *run detached* to `native` — "milliseconds here" would be a guess there.
#
# 2026-09-20: it gained the two things a real run was missing. The **roster** is
# a call of its own, made once between the launch and the loop and never waiting
# — the first poll waits 120-300 s, and a roster that reaches the user three
# minutes after launch is not a roster; the `models:` table is the only thing on
# screen that says which CLI and model each slot runs. And what a poll relays
# gains the `just finished:` line, because `models 4/5 done` names no model.
#
# Both halves were then corrected against the code that emits them (F-2026-09-20).
# The roster call cannot assume a printed table is *this* run's: a phase dir is
# re-used, so on a re-run the predecessor's table is what prints until the write
# that claims the dir drops its `progress` (~0.2 s warm). The discriminator is on
# screen in that window and it is the `progress:` step alone — `fanout` here and
# `complete` for a predecessor that finished — so the sentence names it rather
# than leaving the agent to relay a finished run's roster. The head line's tense
# is NOT the second half of an OR (F-2026-09-21): only `status_file.claim_run`
# writes `"run": None`, so a foreground re-run over a dir an earlier `--detach`
# run used keeps the predecessor's terminal `run` record and `_verdict_text`
# renders its verdict word for the whole fan-out — an OR on that never accepts
# this run's roster at all. And the ABSENCE of `just finished:` is
# not a claim that nothing finished: the line is a difference between two
# readings taken inside one `--wait` call (`run_status._wait_for_terminal` takes
# the baseline, `_attach_finished_during_wait` diffs it), so a model that
# finishes in the gap between polls is already terminal when the next poll takes
# its baseline and no poll ever names it. So the table comparison is per poll and
# not conditional on the line being absent (a model finishing in the gap and a
# second during the wait share one line that names only the second) — copy the
# newly terminal row's spec and state word out of the table, which is a copy and
# not the recount the counts rule forbids.
#
# PD-1 (2026-10-27): the sentence sized every poll's call timeout and never the
# launch's, and on this host the launch is a tool call with a deadline of its
# own. Claude Code's Bash tool stops a `run_in_background` command "after
# reaching its background time limit", and a launch that names no `timeout` gets
# the tool's default: 1800000 in an interactive session, max(600000,
# `BASH_DEFAULT_TIMEOUT_MS`) in a single-shot `claude -p` one (read from 2.1.311's
# bundle; the tool description renders both numbers for the session it is in).
# Measured on 2.1.310: a timeout-less `sleep 700` was stopped at 600.9 s, and a
# live `--review-commits` fan-out launched that way was stopped at 599.7 s with
# one slot still out. The dispatcher's result line read `"exit":143,
# "next":null`, and the host, whose deadline notice from the tool said to "start
# it again with `run_in_background` and a longer `timeout`", improvised a
# `review-code --force` that re-ran both models. The cores' "a detached run is
# not subject to your host's shell-command cap" was true of `--detach` alone.
#
# The launch names the **maximum** rather than a figure sized from the run's
# budget. The host cannot know that budget when it launches (the roster that
# shows each slot's budget prints after the launch); the dispatcher bounds every
# slot itself and exits on its own, so this deadline is a backstop the run never
# means to reach; and a deadline that is too long costs nothing, because the
# completion notification arrives when the process exits. The tool takes the
# number in milliseconds and clamps a background request to its maximum rather
# than refusing it (`min(timeout, max)`, reported as `timeout_clamped`). That
# maximum is 7200000 in the code; a server-side flag may only lower it and only
# `BASH_MAX_TIMEOUT_MS` raises it. And at the maximum the tool's own deadline
# notice reads "do not restart it", which agrees with the sentence's "rather
# than retrying" instead of contradicting it.
#
# Milliseconds, and Claude Code's number alone: safe for the reason the poll's
# worked value is, `tests/test_host_capabilities.py` failing if a second host
# ever resolves *run detached* to `native`.
#
# Fable review, finding 3 (2026-10-27): the maximum is still a ceiling, and a run
# past it was left with "report … rather than retrying" and nothing to offer.
# Probed with no model call, on a copy of the run-1 phase dir the kill left:
# - `status … --view run` reads `running in foreground (2/2 models, no detached
#   run record)` and names no command; its `models:` table calls codex `done`.
# - That `done` slot left no `<model>.json`. A result the provider wrote itself
#   (`source: file`) lands in the phase dir during the slot, but one held for
#   `save_model_result` (`stdout_fallback`, codex's here) is written only after
#   the whole fan-out returns, so a kill loses it. The scope ledger is written at
#   attempt start, so a file result that did land stays reusable.
# - The launch made again without `--force` over a dir holding a result exits 3
#   ("Partial completion detected … Run: --reaggregate"), `next` null. That guard
#   is review-code's alone (and so the commit modes'): review-plan, review-tasks
#   and ask re-run plainly and `[SKIP]` what is there, so the parenthetical names
#   review-code (Fable's second pass, finding 2).
# - With `--force` it resumes: `[SKIP] codex:gpt-6-luna:high - already has
#   results`, then validation as usual. And `--reaggregate` reports with what is
#   there, naming the rest `[MODEL_FAILED] … no result file and no recorded
#   failure`. Both went through the commit front door with the brief path as the
#   range.
# So the sentence names both, offered rather than run, and tells the host to
# say which models really have a file. A composite's own continuation wins:
# its review step now resumes with `--force` over such a dir
# (`improve_workflow.Records.leftover_results`), where it used to loop on the
# guard (Fable's second pass, finding 1).
NATIVE_LAUNCH_TIMEOUT_MS = 7_200_000

_DETACH = {
    "native": (
        f"**Run detached** — use your host's own background mechanism `{{tool}}`, "
        "redirecting stdout and stderr to the phase dir's `orchestrator-run.log` "
        "(`> … 2>&1`, the one dispatcher command that takes a redirect: every "
        "foreground call runs bare), and give that launch call a timeout of its "
        f"own, the longest the parameter takes: {NATIVE_LAUNCH_TIMEOUT_MS} here, "
        f"in milliseconds ({NATIVE_LAUNCH_TIMEOUT_MS // 3_600_000} hours; a "
        "session whose maximum is lower clamps it rather than refusing it). "
        "Without one the mechanism stops the command at its default deadline, "
        "as short as ten minutes, and a fan-out still running then dies "
        "mid-run (exit `143`, `next` `null`). "
        "Never pass `--detach` on this host. Then make one **non-waiting** "
        "`status <plan> <selector> --host <this host's id> --view run --exit-zero` "
        "call — no "
        "`--wait`, no `--timeout`, so it answers in well under a second — and "
        "relay its `progress:` line and `models:` table once: the count is on the "
        "one, and the other's rows are the only thing that says which CLI and "
        "model each of them runs. The run writes that roster a few seconds after "
        "launch, so repeat that one call once if no table printed yet, adding "
        "`--wait --timeout 10` as the wait (never `sleep` before a call: a "
        "call that does not start with `uv` loses its permission rule) — and a "
        "table that *does* print can still be the previous run's, because the "
        "phase dir is re-used and the write that claims it for this fan-out "
        "drops the predecessor's `progress` only about 0.2 s in: a table under "
        "a `progress:` step that is not `fanout` is the last run's, so "
        "make that call again rather than relaying it. That step is the whole "
        "test — a head line reading `finished in foreground (…)` rather than "
        "`running` is what a re-used dir prints all run long once an earlier "
        "`--detach` run left its own terminal `run` record in it, so the tense "
        "names no run. Then poll "
        "while it runs, one "
        "foreground `status <plan> <selector> --host <this host's id> --view run "
        "--wait --timeout <interval> --exit-zero` call per turn at a 120-300 s "
        "interval, "
        "relaying the rendered `progress:` line and, whenever one prints, the "
        "`just finished:` line that names the model that turned terminal during "
        "that wait — verbatim. Its absence claims nothing: that line is a "
        "difference between two readings taken inside one wait, so a model that "
        "finished in the gap between polls is already terminal when the next "
        "poll takes its baseline — so every poll compares its `models:` table "
        "with the previous poll's and names every newly terminal row that line "
        "did not name, copying its spec and state word out "
        "of the row — a copy, never a recount. Nothing else from the "
        "view is relayed mid-run. Spell "
        "`--host` out yourself — no launcher printed a command to copy it from, "
        "and without it the wait is clamped under the tightest ceiling on "
        "record — and give the call itself a timeout of at least the interval "
        f"plus {WAIT_CAP_MARGIN_S:.0f} s, in that parameter's own unit — "
        f"milliseconds here, so {int((300 + WAIT_CAP_MARGIN_S) * 1000)} for a "
        f"300 s interval, not {int(300 + WAIT_CAP_MARGIN_S)}, which is a third "
        "of a second — because this host's default per-call "
        "cap is shorter than the "
        "interval and would otherwise kill every poll from the first. No exit "
        "code from that poll ends the loop except `1`, the unreadable one: "
        "nothing on this host names one invocation, so without `--exit-zero` "
        "`2` is the steady state "
        "and a `0` or a `3` belongs to an earlier run in the same dir and names "
        "no verdict for this one: read the exit code as nothing, relay the "
        "rendered line exactly as on a `2`, and keep polling. Both calls carry "
        "`--exit-zero` so every answer that was read exits `0` and none shows "
        "as an error. The loop ends when "
        "the background mechanism reports "
        "the process exited; read the markers and output paths from "
        "`orchestrator-run.log` then, and report a non-zero exit status with "
        "that path rather than retrying. A stop at the mechanism's time limit "
        "(exit `143`, `next` `null`, `status` still reading `running in "
        "foreground`) names no way forward of its own, so offer the user each "
        "of these and run none yourself: the launch, made again the same way "
        "with `--force` added, which resumes, keeping each model whose result "
        "file is in the phase dir (`[SKIP]`) and running the rest (without "
        "it, review-code and the commit modes refuse a dir holding results, "
        "exit `3`; never `--rerun-all`); and, on a review mode with at least "
        "one such file, "
        "its `--reaggregate`, which reports with those and lists the rest as "
        "failed. Say which models have a file: a `done` row can have none, its "
        "result held in memory for the fan-out's end. Where the mode "
        "instruction names a continuation for a stopped run (a composite's "
        "`[IMPROVE_RERUN]`), offer that instead. The mode instruction names "
        "the selector and the rest of the loop."
    ),
    # R4 (2026-08-21): the previous wording ended "the foreground stays legal
    # for short calls", and codex-apply-executor read that as permission to skip
    # `--detach` entirely — measured as a miss on three consecutive host-lane
    # runs (20260820T093838Z, 20260821T020823Z, 20260821T024227Z), each time
    # leaving no `.status.json` run block for the row to grade. The permission
    # was accurate and is kept, but it is no longer the clause the reader ends
    # on: `--detach` is now stated as the default for every fan-out mode, and
    # the foreground exception is narrowed to the calls it was always meant for.
    "python": (
        "**Run detached** — pass `--detach` (which implies `--yes`) on every "
        "fan-out mode, then poll `status <plan> --view run`. Do this even when "
        "you expect the run to be quick: a fan-out started in the foreground "
        "cannot be handed back to once your turn ends. Only a single-model, "
        "non-fan-out call may stay in the foreground. Never combine `--detach` "
        "with a host background mechanism — pick one."
    ),
    "required": (
        "**Run detached** — pass `--detach` (which implies `--yes`) on every "
        "fan-out mode and poll `status <plan> --view run`. This host caps a single "
        "shell command below a fan-out's runtime, so no foreground fan-out path is "
        "offered."
    ),
}

_TEMPLATES = {"subagents": _SUBAGENTS, "ask": _ASK, "detach": _DETACH}

#: The template slot each verb fills in ``hosts/<host>/shim.md.tmpl`` (D7 owns the
#: templates; the slot names are fixed here so both sides cannot drift).
VERB_SLOTS: Dict[str, str] = {
    "subagents": "{{spawn_subagents}}",
    "ask": "{{ask_user}}",
    "detach": "{{run_detached}}",
}


def verb_sentence(host_id: str, verb: str, base: Optional[str] = None) -> str:
    """The one sentence this host's shim carries for *verb*."""
    if verb not in VERBS:
        raise KeyError(
            f"unknown capability verb {verb!r}; the vocabulary is closed at "
            f"{VERBS}"
        )
    host = entry(host_id, base)
    value = host[verb]
    template = _TEMPLATES[verb][value]
    if "{tool}" not in template:
        return template
    tool = (host.get("native_tool") or {}).get(verb)
    if not tool:
        raise NeedsHuman(
            f"ERROR: host '{host_id}' resolves the *{VERB_WORDING[verb]}* verb to "
            f"'{value}', which names the host's own tool, but its entry carries no "
            f"native_tool.{verb}. A shim cannot be rendered from an incomplete "
            "profile."
        )
    return template.format(tool=tool)


def verb_sentences(host_id: str, base: Optional[str] = None) -> List[str]:
    """All three sentences, in the closed verb order."""
    return [verb_sentence(host_id, verb, base) for verb in VERBS]


def verb_block(host_id: str, base: Optional[str] = None) -> str:
    """The three sentences as the markdown list a shim embeds."""
    return "\n".join(f"- {line}" for line in verb_sentences(host_id, base))


# ---------------------------------------------------------------------------
# Recovery wording — a failed run's instruction goes to whoever can follow it
# ---------------------------------------------------------------------------
# Same fix, two addressees, chosen by ``multi_turn``. The resolution happens
# *here*, in Python, from the ``--host`` id the shim baked into the command that
# is failing — the same rule as the verb sentences, and for the same reason: the
# agent reads a finished sentence, never the matrix. Telling the agent of a host
# with no follow-up turn to "re-invoke to retry" is an instruction nobody in that
# run is able to follow, which is how a failed batch becomes a silently abandoned
# one; naming the human is the honest form of the same fix.

_RETRY_LEAD: Dict[bool, str] = {
    True: (
        "Re-invoke to retry only the failures ({failed}) — completed tasks are "
        "skipped by their result files:"
    ),
    False: (
        "This host ends its run with the command that just failed, so no agent "
        "turn follows this output — a human has to act on it. Re-invoke the "
        "phase to retry only the failures ({failed}); completed tasks are "
        "skipped by their result files:"
    ),
}

#: Printed when the caller has no resolved command to name. The retry *is* the
#: same invocation, so "the same command" is always true, on either host.
_RETRY_FALLBACK = "  (re-run the same command; completed tasks are skipped)"


def retry_instruction(
    host_id: str,
    *,
    failed_ids: str = "",
    retry_command: Optional[str] = None,
    base: Optional[str] = None,
) -> List[str]:
    """The retry block a failed batch prints, addressed to whoever can act.

    Never raises. An unknown host id or unreadable capability data is a broken
    install, and dropping the retry command over it would cost a caller more
    than the wrong addressee does: the fallback is the reference host's answer,
    which is the wording this path printed before the field had a consumer.
    """
    try:
        multi_turn = is_multi_turn(host_id, base)
    except Exception:  # pragma: no cover - unknown host / unreadable data
        multi_turn = True
    lead = _RETRY_LEAD[multi_turn].format(failed=failed_ids or "none recorded")
    return [lead, f"  {retry_command}" if retry_command else _RETRY_FALLBACK]
