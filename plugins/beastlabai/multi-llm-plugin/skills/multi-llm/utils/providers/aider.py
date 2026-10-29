"""Aider CLI provider implementation with ANSWER-marker text parsing."""
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import yaml

from ..json_extractor import extract_json_from_text
from .base import (
    LLMProvider,
    ReadOnlyInvocationRefused,
    ReasoningLadder,
    StructuredSchema,
    split_reasoning_effort,
)

# Reasoning effort values passed to aider's --reasoning-effort, which is an
# unvalidated pass-through (verified on aider 0.86.2): for openrouter/ models
# aider always accepts it and sends OpenRouter's reasoning.effort param;
# other models warn-and-ignore.
#
# The ladder minus `max`: aider forwards whatever it is given, so the whitelist
# is the harness's own gate rather than the CLI's, and it stops where the
# measurement stopped.
EFFORT_LADDER = ReasoningLadder(
    provider="aider",
    rungs=("none", "minimal", "low", "medium", "high", "xhigh"),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted

# aider prints the model's reply after this marker (with --no-pretty).
# Reasoning models emit an optional "► **THINKING**" block first, which may
# contain draft/decoy JSON — only content after the LAST ANSWER marker is
# the actual reply.
ANSWER_MARKER = "► **ANSWER**"

# Absolute file paths mentioned in the prompt (e.g. the plan file) are
# passed to aider via --read so the model actually sees their contents.
# aider's own file-mention auto-add splits the message on whitespace and
# only matches repo-RELATIVE paths / bare basenames, so the absolute paths
# used by the orchestrator prompts never trigger it.
# Two-branch alternation: Windows drive-letter paths (backslash included in
# the character class so C:\Users\foo\bar.md matches in full) and POSIX
# paths (branch byte-identical to the historical pattern). Known accepted
# limitations: UNC paths (\\server\share\...) and paths containing spaces
# are not matched — extraction is best-effort enrichment behind an
# existence check, so a miss just means no extra --read context.
_ABS_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/][\w.\-/\\]+|/[\w.\-/]+)")
_MAX_READ_FILES = 20

#: The decline supply's length: :meth:`AiderProvider.build_command_for_transport`
#: writes exactly ``"s\n" * AIDER_DECLINE_LINES`` to aider's stdin
#: (plans/ask-answer-recovery-and-false-success.md D4.2, decision 11.3).
#:
#: **Why a count matters.** stdin closes once the supply is written
#: (``communicate(input=…)``), and a prompt that reads EOF takes its default,
#: yes (aider ``io.py:884``). So a run that asks more questions than there are
#: lines silently gets the mention auto-add back (run e4: 3.05 MB). Blank lines
#: are never allowed: an empty answer is also the default.
#:
#: **Why ``s``.** One ``s`` ("Skip all") sets the confirm group's preference,
#: so every later file of the same mention scan is declined without reading a
#: line — measured in T4.2's e5 capture, where two scans of 2 and 8 files read
#: exactly 2 lines — and a one-file scan (no group) still reads it as "no".
#:
#: **The bound, read from aider 0.86.2** (``AiderProvider.verified_version``,
#: the release ``tests/container/cli-versions.lock`` pins). Each prompt reads at
#: most one line, and one ``--message`` run reaches at most 11:
#:
#: - mention scans, one line each: one prompt scan (``base_coder.py:919``) plus
#:   one reply scan per request (``:1561``), and at most 1 + ``max_reflections``
#:   (3) = 4 requests (``:101``, ``:939``) — 5 scans;
#: - ``Try to proceed anyway?``, at most once per request (``:1415``) — 4;
#: - startup: "create a git repo?" (``main.py:122``, non-repo cwd only) and the
#:   OpenRouter login offer (``onboarding.py:93``, no key only) — 2.
#:
#: The gitignore, analytics and URL prompts are off by flag, and the lint, test,
#: shell, create-file and edit prompts do not occur in ``/ask``. While the
#: declines hold nothing is added, so no reflection happens and a real run asks
#: at most 4. 64 is about 6x the worst case, for 128 bytes. A bump that raises
#: ``max_reflections`` or adds a confirm site reachable in ``/ask`` invalidates
#: the bound: re-run the T4.2 probe and recompute it before moving the pin
#: (``tests/test_aider_provider.py`` pins the terms and the version).
AIDER_DECLINE_LINES = 64

#: The one answer the supply carries (see :data:`AIDER_DECLINE_LINES`).
AIDER_DECLINE_ANSWER = "s"

#: The environment variable that turns yes-always on (configargparse's
#: ``auto_env_var_prefix="AIDER_"``, ``args.py:41``). Stripped from the child's
#: environment (:meth:`AiderProvider.get_remove_env`), whatever its value.
AIDER_YES_ALWAYS_ENV = "AIDER_YES_ALWAYS"

#: The values that leave a store_true flag OFF when it comes from a config file
#: or the environment (configargparse ``convert_item_to_command_line_arg``).
#: ``true``/``yes``/``on``/``1`` turn it on and anything else makes aider exit
#: on a parse error, so every value outside this set is refused.
_FALSY_SETTING_VALUES = frozenset({"false", "no", "off", "0"})

#: A ``yes-always`` key in a YAML config file, for a file PyYAML cannot parse
#: (aider would fail on it too, but the refusal must not depend on that).
_CONF_YES_ALWAYS_LINE_RE = re.compile(r"^\s*(?:--)?yes-always\s*:\s*(.*?)\s*$")

#: The environment variable that names one more dotenv file for aider to load
#: (``--env-file``, ``args.py:801``, under the ``AIDER_`` prefix). aider loads
#: that file LAST, with ``override=True`` (``main.py:361-384``), so an
#: ``AIDER_YES_ALWAYS`` in it comes back after the strip. Read, never stripped:
#: it is also where a user keeps the API key the run needs.
AIDER_ENV_FILE_ENV = "AIDER_ENV_FILE"

#: An ``env-file`` key in a YAML config file PyYAML cannot parse (as above).
_CONF_ENV_FILE_LINE_RE = re.compile(r"^\s*(?:--)?env-file\s*:\s*(.*?)\s*$")

# ---------------------------------------------------------------------------
# The shape of aider's plain-text stdout
# (plans/ask-answer-recovery-and-false-success.md D4.1, measured on the ten
# committed 0.86.2 fixture rows, the 2026-09-26 incident and the T4.2 captures).
#
# An ordinary answer has no ANSWER marker (it appears only when a THINKING block
# streamed), so the no-marker branch is where most answers live, and an answer
# may quote anything — `litellm.BadRequestError`, "has hit a token limit!", a
# `Tokens:` line. So which lines are aider's own is decided by STRUCTURE, never
# by searching the whole stdout:
#
#   <prologue: banner lines>  <answer span>  <trailing accounting line> <after>
#
# Only the prologue and what follows the trailing accounting line are aider's
# diagnostics. With no accounting line no request completed, no answer span
# exists, and every line is scanned; line-start anchoring is then the guard.
# ---------------------------------------------------------------------------

#: A banner line. The prologue is the top of the (tolerated-line-free) stdout:
#: leading blank lines, then the contiguous run of lines matching this. The
#: first line that does not match — a blank line included — ends it, and the
#: prefixes are never matched after it, so a ``Model:`` line an answer writes is
#: answer text. Fixture-measured: ``Aider v``, ``Model:``, ``Git repo:``,
#: ``Repo-map:``; ``Added … to the chat`` is in the T4.2 captures; the rest are
#: aider's known output — the two large-repo lines are 0.86.2's
#: ``get_announcements`` (``base_coder.py:255-260``), printed between
#: ``Git repo:`` and ``Repo-map:`` in any repo over 1,000 tracked files, which
#: the incident's was. An unknown startup line ends the prologue early, so the
#: failure mode is banner text kept, never answer text lost.
_BANNER_RE = re.compile(
    r"^(Aider v\d|Main model:|Model:|Weak model:|Editor model:|Git repo:"
    r"|Warning: For large repos, consider using --subtree-only and \.aiderignore$"
    r"|See: https://aider\.chat/docs/faq\.html#can-i-use-aider-in-a-large-mono-repo$"
    r"|Repo-map:|Added .+ to the chat|Initial repo scan)"
)

#: The first banner line: what makes a stdout aider's at all (the hook answers
#: ``""`` without it). aider writes it before its first request, so every
#: capture carries it (the manifest's ``empty`` row).
_AIDER_VERSION_RE = re.compile(r"^Aider v\d")

#: aider's accounting line, printed once per completed request after the reply
#: (``Tokens: 801 sent, 20 received.``, with `` Cost: …`` on the same line in a
#: priced run). The LAST one is the real one: an answer that quotes a ``Tokens:``
#: line, in prose or in a fenced example, always prints before it.
_ACCOUNTING_RE = re.compile(r"^Tokens: .* sent, .* received\.")

#: aider's own context-overflow wording (D4.1), matched against whole
#: diagnostic lines: the pre-request estimate (the incident), and the
#: ``has hit a token limit!`` block aider prints after a request the endpoint
#: rejected for length (the ``context-overflow`` row, which carries no
#: ``litellm.`` text at all).
_OVERFLOW = (
    re.compile(r"^Your estimated chat context of .* exceeds the .* token limit"),
    re.compile(r"^Model .+ has hit a token limit!$"),
    re.compile(r"^(?:Input|Total) tokens: .*possibly exhausted context window!$"),
)

#: The counts, where a source states both (D4.1's precedence). First the
#: endpoint's own 400 body — OpenRouter's wording is the measured one (the
#: incident: "maximum context length is 1048576 tokens. However, you requested
#: about 1083501 tokens"); OpenAI's "resulted in N tokens" reads the same way —
#: then aider's pre-request estimate. aider's ``Input tokens: ~N of M`` lines are
#: never used: aider labels them approximate, and they read ``of 0`` when litellm
#: does not know the model's limit (the ``context-overflow`` row).
_BODY_COUNTS_RE = re.compile(
    r"maximum context length is ([\d,]+) tokens\b.*?"
    r"(?:you requested(?: about)?|resulted in) ([\d,]+) tokens"
)
_ESTIMATE_COUNTS_RE = re.compile(
    r"^Your estimated chat context of ([\d,]+) tokens exceeds the ([\d,]+) token limit"
)

#: A confirmation prompt the D4.2 decline supply answers. aider prints the
#: subject on the line before it (a file name; for ``Try to proceed anyway?`` the
#: last line of its over-limit warning), then this question with no newline, so
#: whatever aider prints next — the answer's first line, when the prompt scan's
#: last prompt read a line — shares the line.
_CONFIRM_PROMPT_RE = re.compile(
    r"^(?:Add file to the chat\?|Try to proceed anyway\?) \(Y\)es/\(N\)o[^\]]*\]: ?"
)

#: What aider appends to a prompt it answers from a confirm group's preference
#: rather than from stdin (``io.py`` ``confirm_ask``: ``user_input(question +
#: preference)``). Measured in T4.2's e5 capture: after one ``s``, every later
#: file of the group prints its prompt followed by ``skip`` and reads nothing.
#: It is aider's echo, not answer text, so it is dropped with its prompt.
_GROUP_PREFERENCE_ECHOES = frozenset({"skip", "all"})


def _drop_confirmation_pairs(lines: Sequence[str]) -> List[str]:
    """Remove the confirmation prompts the D4.2 decline leaves in stdout.

    A pair is the subject line, then an ``Add file to the chat? (Y)es/…]: `` or
    ``Try to proceed anyway? …]: `` line. Both go; any text on the prompt line
    after the question stays, in place, because the answer's first line lands
    there when the prompt that preceded it read a line from stdin. A group
    preference echo (``…]: skip``) is aider's, not the answer's, and goes too.

    **The one copy of the pair rule** (plans/ask-answer-recovery-and-false-
    success.md D4.1 step 1): :meth:`AiderProvider.salvage_text` and
    :meth:`AiderProvider.parse_output` both call this, so the next change to
    aider's prompt wording is one edit.
    """
    kept: List[str] = []
    tails: set = set()
    for line in lines:
        match = _CONFIRM_PROMPT_RE.match(line)
        if match is None:
            kept.append(line)
            continue
        # The subject is the line directly above the prompt — unless that line
        # is text an earlier prompt shared, which is never a subject.
        if kept and len(kept) - 1 not in tails:
            kept.pop()
        tail = line[match.end():]
        if tail.strip() and tail.strip() not in _GROUP_PREFERENCE_ECHOES:
            tails.add(len(kept))
            kept.append(tail)
    return kept


def _prologue_end(lines: Sequence[str]) -> int:
    """Index of the first line after aider's banner block (see :data:`_BANNER_RE`)."""
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    while index < len(lines) and _BANNER_RE.match(lines[index]):
        index += 1
    return index


def _last_accounting_index(lines: Sequence[str]) -> Optional[int]:
    """Index of the trailing accounting line, or ``None`` when no request completed."""
    for index in range(len(lines) - 1, -1, -1):
        if _ACCOUNTING_RE.match(lines[index]):
            return index
    return None


def _join_trimmed(lines: Sequence[str]) -> str:
    """The lines joined, blank lines dropped from both ends and none inside."""
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end])


def _format_count(count: str) -> str:
    return f"{int(count.replace(',', '')):,}"


def _overflow_error(body: Optional["re.Match"], scanned: Sequence[str]) -> str:
    """D4.1's context-overflow wording; the first source stating both counts wins.

    The sentence says "context **window**", one word more than D4.1 spells it,
    because the review lanes classify a failed slot from its ``error`` string
    alone (``review_orchestrator_base``: ``classify_streams(error, "")``). With
    the word, the shared ``exceeds the model's context window`` marker reads it
    as ``context_length_exceeded`` — terminal, with the remedy message — exactly
    as aider's raw overflow block classified before D4.1 replaced the error;
    without it the slot classified as nothing at all.
    """
    counts: Optional[Tuple[str, str]] = None
    if body is not None:
        limit, count = body.groups()
        counts = (count, limit)
    else:
        for line in scanned:
            estimate = _ESTIMATE_COUNTS_RE.match(line)
            if estimate is not None:
                counts = estimate.groups()
                break
    if counts is None:
        return "aider: prompt exceeds the model's context window (token count not reported)"
    return (
        f"aider: prompt exceeds the model's context window "
        f"({_format_count(counts[0])} > {_format_count(counts[1])} tokens)"
    )


# ---------------------------------------------------------------------------
# Inherited auto-approval (D4.2). Taking --yes-always off argv does not make
# aider read the declines: in 0.86.2 `confirm_ask` answers "y" when `io.yes is
# True`, BEFORE it reads stdin (`io.py:866`), and yes-always has three sources
# besides argv. Measured 2026-09-29 (T4.2, s supply): each of the env var, a
# repo-root `.aider.conf.yml`, a `$HOME` one and a repo `.env` re-added uv.lock
# and re-sent 3.05 MB. The env var is stripped (get_remove_env); a FILE cannot
# be overridden from argv (`--yes-always` has no negative form, `args.py:760`,
# and `--config` adds a file rather than replacing these), so it is refused —
# the custom dotenv `AIDER_ENV_FILE` or an `env-file` key names included.
# ---------------------------------------------------------------------------

def _setting_turns_on(value: Any) -> bool:
    """True unless ``value`` leaves yes-always off (see :data:`_FALSY_SETTING_VALUES`)."""
    if value is None:  # a YAML null: configargparse skips the key
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in _FALSY_SETTING_VALUES


def _conf_values(path: Path, option: str, line_re: "re.Pattern[str]") -> List[Any]:
    """Every value an ``.aider.conf.yml`` gives ``option``, else ``[]``.

    ``line_re`` reads the key from a file PyYAML cannot parse.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError:
        return [
            match.group(1).split(" #", 1)[0].strip().strip("'\"")
            for match in map(line_re.match, text.splitlines())
            if match
        ]
    if not isinstance(document, dict):
        return []
    # configargparse's keys for `--<option>`: the bare and the dashed.
    return [document[key] for key in (option, f"--{option}") if key in document]


def _conf_yes_always(path: Path) -> Optional[str]:
    """The ``yes-always`` setting an ``.aider.conf.yml`` turns on, else ``None``."""
    for value in _conf_values(path, "yes-always", _CONF_YES_ALWAYS_LINE_RE):
        if _setting_turns_on(value):
            return f"yes-always: {value}"
    return None


def _conf_env_files(path: Path) -> List[str]:
    """The ``env-file`` values an ``.aider.conf.yml`` sets, as configargparse reads them.

    A scalar is stringified (``YAMLConfigFileParser.parse``); a null is skipped,
    and a list or mapping is not a file name.
    """
    return [
        str(value)
        for value in _conf_values(path, "env-file", _CONF_ENV_FILE_LINE_RE)
        if value is not None and not isinstance(value, (list, dict)) and str(value)
    ]


def _dotenv_yes_always(path: Path) -> Optional[str]:
    """The ``AIDER_YES_ALWAYS`` a ``.env`` sets to anything but a falsy value, else ``None``.

    python-dotenv's reading, as far as this one key needs it: ``export`` is
    optional, a quoted value ends at its closing quote, an unquoted one at an
    inline `` #`` comment, and the last assignment in the file wins.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    found: Optional[str] = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, separator, value = line.partition("=")
        if not separator or key.strip() != AIDER_YES_ALWAYS_ENV:
            continue
        value = value.strip()
        if value[:1] in ("'", '"'):
            closing = value.find(value[0], 1)
            value = value[1:closing] if closing != -1 else value[1:]
        else:
            value = value.split(" #", 1)[0].strip()
        found = value
    if found is not None and _setting_turns_on(found):
        return f"{AIDER_YES_ALWAYS_ENV}={found}"
    return None


def _git_root(start: Path) -> Optional[Path]:
    """The nearest ancestor holding ``.git`` (aider's ``search_parent_directories``)."""
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return directory
    return None


def _inherited_yes_always(cwd: Optional[str]) -> Optional[Tuple[Path, str]]:
    """The first file that turns yes-always on for a child spawned in ``cwd``.

    Reads aider 0.86.2's own search lists, resolved against the spawn cwd
    (``None`` means this process's, which the child inherits) and its git root:
    ``.aider.conf.yml`` in the cwd, the git root and ``$HOME``
    (``main.py:464-477``, all read on every run), and ``.env`` in ``$HOME``, the
    git root and the cwd plus ``~/.aider/oauth-keys.env`` (``main.py:305-384``,
    loaded with ``override=True`` and parsed again, so an ``AIDER_YES_ALWAYS``
    there comes back after the variable was stripped from the environment).
    The same loader also reads the ``--env-file`` aider resolves from
    ``AIDER_ENV_FILE`` or an ``env-file`` key in any of those config files
    (``main.py:501``), relative to the cwd with no ``~`` expansion
    (``Path(fn).resolve()``), and loads it last; every candidate is read.
    Any file that sets it counts, even one a later file overrides: refusing a
    run that would have been safe costs one config edit, and the reverse costs
    a 1M-token request.
    """
    try:
        here = Path(cwd).resolve() if cwd else Path.cwd().resolve()
    except OSError:
        return None
    root = _git_root(here)
    home = Path.home()
    conf_files = [here / ".aider.conf.yml"]
    if root is not None:
        conf_files.append(root / ".aider.conf.yml")
    conf_files.append(home / ".aider.conf.yml")
    dotenv_files = [home / ".env"]
    if root is not None:
        dotenv_files.append(root / ".env")
    dotenv_files += [here / ".env", home / ".aider" / "oauth-keys.env"]
    # configargparse gives the env var precedence over the config files, but a
    # wrong guess at which one wins costs a 1M-token request, so all are read.
    env_file_names = [os.environ.get(AIDER_ENV_FILE_ENV, "")]
    for path in dict.fromkeys(conf_files):
        env_file_names += _conf_env_files(path)
    for name in filter(None, env_file_names):
        try:
            dotenv_files.append((here / name).resolve())
        except (OSError, RuntimeError, ValueError):
            continue
    for path in dict.fromkeys(conf_files):
        setting = _conf_yes_always(path)
        if setting is not None:
            return path, setting
    for path in dict.fromkeys(dotenv_files):
        setting = _dotenv_yes_always(path)
        if setting is not None:
            return path, setting
    return None


class AiderProvider(LLMProvider):
    """Provider for the Aider CLI tool (https://aider.chat/).

    Aider runs one-shot headless via --message with a battery of flags that
    disable interactivity, litter files, update checks, and streaming. The
    prompt is prefixed with "/ask " so aider stays in read-only chat mode:
    in edit mode aider refuses to write any absolute path outside the target
    git repo ("is not in the subpath of ..."), so the orchestrator's
    file-based {output_json_path} can never be written reliably — stdout is
    the ONLY output path for this provider (the file read always misses and
    invoke_with_file_output falls back to stdout).

    Output shape on stdout (stderr only carries a harmless non-terminal
    warning): 4-6 banner lines (Aider version, Model, Git repo, Repo-map),
    then for reasoning models an optional "► **THINKING**" block, then
    "► **ANSWER**", then the reply, then usually a trailing
    "Tokens: ... Cost: ..." line.

    Wrap gotcha: with --no-pretty aider still hard-wraps output at the
    terminal width (~80 columns), inserting literal newlines inside long
    JSON strings, which breaks json.loads (and extract_json_from_text does
    not repair broken strings). get_env() therefore sets COLUMNS=10000,
    which removes the wrapping entirely (verified empirically).

    get_env() also sets BROWSER=true: on rate-limit give-up aider offers to
    open the OpenRouter settings URL, and a confirmation that reads EOF (or
    an inherited yes-always) accepts it, which would launch a real browser;
    BROWSER=true makes Python's webbrowser a no-op.

    Input files: aider's file-mention auto-add only matches repo-relative
    paths / bare basenames, never the absolute paths the orchestrator
    prompts use, so build_command scans the prompt for existing absolute
    file paths (e.g. the plan file) and passes them via --read (read-only
    context files, allowed outside the repo root).

    Declined mentions (plans/ask-answer-recovery-and-false-success.md D4.2,
    measured on 0.86.2): aider scans the prompt AND every reply for
    repo-relative paths and asks "Add file to the chat?" for each. Answered
    "y" — which ``--yes-always`` did, and which EOF on stdin does — it added
    every file the plan named, then every file the reply named, and sent
    1.08M tokens; ``--yes-always`` also answered its own over-limit guard. So
    there is no ``--yes-always``: :meth:`build_command_for_transport` supplies
    ``s`` ("skip all") answers on stdin, and refuses before spawn when an
    ``.aider.conf.yml`` or ``.env`` turns yes-always back on.

    Model names are litellm model specs passed VERBATIM to --model (e.g.
    "openrouter/z-ai/glm-5.2") — no partition/splitting. Auth is env-only:
    openrouter/ models need OPENROUTER_API_KEY in the environment (the
    subprocess inherits it).

    Model strings support an optional ``model[:effort]`` suffix (e.g.
    ``openrouter/z-ai/glm-5.2:high``), translated to
    ``--reasoning-effort <effort>`` right after the --model pair. Valid
    efforts are listed in REASONING_EFFORTS; anything else passes through
    verbatim as the model name (keeping ``:free``-style ids intact).

    Gotcha: aider exits 0 EVEN on auth failure and rate-limit give-up (the
    error text, e.g. "litellm.AuthenticationError ...", goes to stdout,
    usually without an ANSWER marker) — parse_output fails such a run on
    aider's diagnostic lines before it extracts any JSON (D4.1), and treats
    "no JSON extractable" as failure with a stdout snippet as the error.

    File-write emulation quirk: because the orchestrator prompt demands
    file-based output while /ask mode is read-only, some models answer
    with a pseudo write envelope like {"file_path": ..., "content":
    "<the JSON as a string>"} (observed live with kimi-k2.7-code).
    parse_output unwraps that envelope and returns the parsed content.
    """

    #: §9.4: aider has **no standalone prompt element**. The prompt ships inside
    #: `"/ask " + prompt` after `--message` (the prefix is what keeps aider in
    #: read-only chat mode — see the class docstring), so `argv[-1] == prompt`
    #: is false and `cmd[:-1]` would truncate an unrelated flag. Declaring
    #: `None` is why §9.4 could not be an assertion: aider is the counterexample.
    #: An adapter declaring `None` must stay argv-only with no agent profile —
    #: both of those paths drop `argv[-1]` — which aider is and does.
    prompt_argv_index = None

    #: The class docstring's "stdout is the ONLY output path for this provider",
    #: stated as data instead of prose. ``/ask`` keeps aider read-only, and in
    #: edit mode it refuses any absolute path outside the target git repo
    #: anyway, so the file the review prompts name can never be written. Asking
    #: for stdout directly is what removes the pseudo-write envelope some models
    #: answered the impossible instruction with (``{"file_path": …, "content":
    #: "<the JSON as a string>"}``); :meth:`parse_output` still unwraps that
    #: envelope, because a model can invent one from any prompt.
    supports_file_output = False

    #: The ask lane's plan route (plans/ask-answer-recovery-and-false-success.md
    #: D4.2). aider already receives the plan by ``--read`` — every absolute
    #: path its prompt names is attached by :meth:`_extract_read_files` — so an
    #: inlined body only doubled the prompt and fed aider's mention scan, which
    #: auto-added every repo path the plan named (1.08M tokens on 2026-09-26).
    #: ``ask_orchestrator.render_plan_fields`` renders the path block for this
    #: adapter only when this extractor finds the plan path in the complete
    #: rendered prompt, question first — a question naming ``_MAX_READ_FILES``
    #: existing files leaves the plan no slot, and gets the inline block.
    wants_inline_plan = False

    #: The code-review route (plans/ask-answer-recovery-and-false-success.md
    #: D4.2, "What it costs"), read from this adapter's argv: ``/ask`` has no
    #: file tool, so the model sees only what aider attaches — the repo map,
    #: the absolute paths :meth:`_extract_read_files` passes by ``--read``, and
    #: the files a mention scan adds. The decline supply
    #: (:meth:`build_command_for_transport`) now refuses every mention add, and
    #: that scan was how the review-code slot got the changed files the prompt
    #: lists by repo-relative path. ``--read`` cannot stand in either: the path
    #: prompt names ``{diff_dir}``, a directory, which the extractor skips. So
    #: the ``"cwd"`` default would render the path prompt for a lane that can
    #: open neither the diff files nor the code. ``"none"`` sends the slot down
    #: ``render_diff_access``'s inline branch instead — plan, manifest and every
    #: diff in the prompt, under the 96 KB argv-safe cap — or, over the cap or
    #: on partial coverage, to an undispatched ``[REVIEW_UNSUPPORTED]``.
    #: Measured offline (T4.2's review-lane gate: the real orchestrator, aider
    #: 0.86.2, a localhost stub): review-code still reaches every changed line,
    #: as diff hunks in one request, where the pre-T4.2 argv mention-added the
    #: whole changed files. What the slot loses is the text outside the hunks.
    generate_read_scope = "none"

    #: aider's repo-map cache, written at the repo root on every run with the
    #: default map (``repomap.py:35-43``, measured on 0.86.2). The porcelain check
    #: ignores it only beside an aider slot in the same fan-out (D4.3). The
    #: version suffix is measured, never globbed: ``v5`` must be re-measured.
    workspace_caches = (".aider.tags.cache.v4/",)

    version_cmd = ("aider", "--version")
    #: 0.86.2 is where every fixture in ``tests/fixtures/aider/`` was captured —
    #: the §6 step-5 probe, ``--network none``, the stub and the failserver both
    #: running inside the container, no credential — and the release
    #: ``tests/container/cli-versions.lock`` pins. It is a pin to re-confirm
    #: rather than a range to trust: the two things the parser reads are both
    #: aider-internal strings upstream is free to restyle
    #: (``reasoning_tags.REASONING_END``, which is where ``► **ANSWER**`` comes
    #: from, and the ``Tokens:``/``Cost:`` accounting lines the answer is trimmed
    #: of).
    #:
    #: **There is deliberately no ``min_version``.** A draft of this block
    #: declared ``min_version = "0.86.2"`` on the strength of "nothing older has
    #: been run against this parser", which is exactly the error
    #: `harness-invocation-improvements.md` §5.4.1(a) names: a *measured-at*
    #: version is an upper bound on the true floor, never the floor itself, so
    #: adopting it as a floor refuses working installs to buy nothing. aider is a
    #: **pre-existing** adapter — unlike copilot, kimi, qwen-code and vibe, which
    #: landed together with their probes and have no older users to refuse — and
    #: nothing measured says 0.85 fails. ``min_version`` is a hard exit-3 refusal
    #: in ``subagent_executor._detect_version``; ``verified_version`` is a
    #: one-line warning. The capture supports the warning and not the refusal, so
    #: only the warning is declared. ``muse``, ``cursor-agent`` and ``agy``
    #: already leave the floor empty for the mirror-image reason.
    #:
    #: (Today the refusal would not even fire: this adapter declares only the
    #: ``generate`` profile, ``_detect_version`` runs solely inside
    #: ``preflight_runner``, and that raises ``missing_profile`` first. That
    #: makes a wrong floor *latent* rather than harmless — it would go live, with
    #: no measurement behind it, on the day this adapter becomes runner-eligible.)
    #:
    #: ``version_cmd`` stays, because it is the only thing that can ever make
    #: ``verified_version`` speak: with no probe the detected version is
    #: ``unknown`` and both the floor and the warning are skipped. Confirmed
    #: against the pinned binary 2026-08-20 (``docker run --rm --network none
    #: --entrypoint /opt/mllm/real/aider mllm-e2e:local --version``): it prints
    #: exactly ``aider 0.86.2`` on stdout, which the base :meth:`parse_version`
    #: reads without an override.
    verified_version = "0.86.2"

    # §7.2 — the auth override plus the exit-0 sniff, folded out of the class
    # docstring's "Gotcha" and into the classifier so the D3k ladder sees them.
    #
    # Measured on aider 0.86.2, 2026-08-16, `--api-key openrouter=sk-invalid`,
    # exit **0**:
    #   litellm.AuthenticationError: AuthenticationError: OpenrouterException -
    #   {"error":{"message":"Missing Authentication header","code":401}}
    #   The API provider is not able to authenticate you. Check your API key.
    # Not one word of that matches the base auth set — "Check your API key" is
    # not "invalid api key", and `401` is only a context word — so a logged-out
    # aider classified as *nothing* and spent the transport retry budget on it.
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "not able to authenticate",
        "missing authentication header",
    )

    #: The residual marker: any other litellm exception aider prints while still
    #: exiting 0. It says "this run failed" and nothing more, which is exactly
    #: why :func:`classify_streams` consults it last.
    exit_zero_failure_markers = (
        re.compile(r"\blitellm\.\w*error\b"),
        re.compile(r"\blitellm\.exceptions\b"),
    )

    #: litellm's model-cost-map refresh, and the one line of aider's stdout that
    #: must never reach the failure classifier.
    #:
    #: MEASURED on the 2026-08-19 credentialed live row. litellm fetches
    #: ``model_prices_and_context_window.json`` from raw.githubusercontent.com at
    #: IMPORT time — before aider parses a flag, so ``--no-check-update`` and
    #: ``--no-analytics`` cannot reach it — with a 5 s timeout, and on ANY
    #: exception falls back to ``model_prices_and_context_window_backup.json``,
    #: which ships inside the package (1.28 MB, already on disk). The refresh is
    #: therefore best-effort by upstream's own design and its failure is not the
    #: run's failure.
    #:
    #: But aider prints that failure to **stdout** (stderr stays empty) and the
    #: text ends in ``Name or service not known``, which is a literal entry in
    #: :data:`base.CONNECTION_ERROR_MARKERS`. So on any host that cannot reach
    #: raw.githubusercontent.com — an air-gapped build box, a corporate proxy, a
    #: container with an egress allowlist — a *successful* aider run was
    #: classified ``connection_error``: the model answered, the JSON parsed, the
    #: credit was spent, and the D3k ladder took the rung for a transport fault.
    #: Measured exactly that way: exit 0, ``["ok"]`` parsed, $0.00028 charged,
    #: classification ``connection_error``.
    #:
    #: Excised by FILENAME rather than by hostname: the file name is unique to
    #: this fetch, while the host also serves things a real failure could mention.
    _TOLERATED_STDOUT_LINES = (
        re.compile(r"model_prices_and_context_window\.json"),
    )

    @classmethod
    def _drop_tolerated_lines(cls, stream: str) -> str:
        """Remove upstream's best-effort-fetch noise before classification."""
        if not stream:
            return stream
        return "\n".join(
            line for line in stream.splitlines()
            if not any(p.search(line) for p in cls._TOLERATED_STDOUT_LINES)
        )

    #: aider's own **gloss** on a failure — the one line of a failed capture the
    #: RUNNER wrote about the vendor rather than the vendor writing about itself
    #: (C7). It is a fixed sentence rather than upstream text: byte-identical
    #: in the 500-forever and the truncated-stream captures, printed under
    #: litellm's own error line and repeated once per retry attempt.
    #:
    #: MEASURED on the committed 0.86.2 captures. ``overloaded`` is a member of
    #: :data:`base.LLMProvider.rate_limit_patterns`, where it carries Anthropic's
    #: genuine 529, and the rate table is consulted before the timeout,
    #: connection and server tables. So every 5xx and every truncated stream
    #: aider reported classified ``rate_limited``:
    #:
    #:   ``truncated``          rate_limited -> connection_error
    #:   ``exit-zero-failure``  rate_limited -> runner_error
    #:
    #: and no other row in ``tests/fixtures/aider/`` moves — ``rate-limit``
    #: (litellm's own ``RateLimitError`` plus *"has rate limited you"*) still
    #: answers ``rate_limited``, ``auth-error`` still ``auth_failed``.
    #:
    #: **Why the excision is here and not in the shared pattern.** Dropping
    #: ``overloaded`` from :data:`base` would weaken a real signal for every
    #: adapter, which is why §16.4 declined this and why the decline was kept.
    #: C1's rule is what makes the narrow fix legal: the classifier is to read
    #: the text the *vendor* wrote, so a gloss the runner invented is narrowed
    #: where it is written rather than by weakening a table every adapter
    #: inherits.
    #: The vendor's own word survives the excision, which is the whole point:
    #: an Anthropic 529 seen through aider keeps litellm's rendered body
    #: (``{"type":"overloaded_error","message":"Overloaded"}``) on the line
    #: above, and still classifies ``rate_limited`` — measured on that capture.
    #:
    #: **Why exactly this one sentence and not aider's gloss family.** Measured:
    #: excising every ``The API provider …`` line instead turns the ``auth-error``
    #: row from ``auth_failed`` into ``runner_error``, because *"not able to
    #: authenticate"* — this class's own declared auth pattern, above — IS the
    #: 401 gloss and is the only auth wording in that capture. aider's gloss is
    #: load-bearing where the vendor's text is silent and misleading only here,
    #: so the excision names the sentence rather than the shape.
    #:
    #: **The rung moves with the label, and that is the correction, not a side
    #: effect.** ``rate_limited`` is rung 3 — backoff with jitter, at most three,
    #: and it does not consume ``driver.subagent_retries`` (D3i: a 429 is not a
    #: transport failure). §7.1.b's ``_LADDER_STATUS_BY_CATEGORY`` puts
    #: ``connection_error`` and ``server_error`` on rung 4, "which is what makes
    #: a connection error or a 5xx spend ``driver.subagent_retries`` exactly
    #: once". Both rows stay retryable either way; what disappears is §7.6(b)
    #: rule 6b's doubled wait — an executor-level backoff on a slot where aider
    #: had already spent 78 s and 27 HTTP attempts retrying on its own.
    #:
    #: **Residual, recorded rather than fixed here.** ``exit-zero-failure``
    #: lands on ``runner_error`` and not on the more specific ``server_error``,
    #: because :data:`base.SERVER_ERROR_MARKERS` spells the phrase with
    #: separators (``internal server error``) while litellm prints the class name
    #: ``InternalServerError``, and the run carries no bare ``500``. Lane A maps
    #: both to rung 4, so only the ``Reason:`` line differs — and it is right
    #: either way, where today it sends the reader to check a quota during a
    #: server outage. Closing that gap is an edit to a shared table, which is
    #: outside C7's scope by construction.
    _ADAPTER_GLOSS_LINES = (
        re.compile(r"The API provider's servers are down or overloaded"),
    )

    @classmethod
    def _drop_adapter_gloss(cls, stream: str) -> str:
        """Remove aider's own gloss, keeping every word the vendor wrote.

        Degrades to its input rather than to ``""``: an empty haystack
        classifies as ``None`` (:func:`base.classify_streams`), so an excision
        that consumed a whole capture would launder a failure into a
        transport-shaped retry — the same rule :meth:`base.LLMProvider.
        vendor_text` states for the hook this narrowing sits beside.
        """
        if not stream:
            return stream
        narrowed = "\n".join(
            line for line in stream.splitlines()
            if not any(p.search(line) for p in cls._ADAPTER_GLOSS_LINES)
        )
        return narrowed if narrowed.strip() else stream

    def classify_failure(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[str]:
        """As the base, minus two lines aider wrote about something else.

        The adapter supplies the data and ``classify_streams`` owns the rule
        (§7.2), so this override changes neither — it only declines to hand the
        rule two lines that are not evidence about this run. Both reductions are
        removal-only and both degrade to their input, so the order they compose
        in does not matter:

        * litellm's tolerated cost-map refresh line, which upstream has already
          decided is non-fatal (:data:`_TOLERATED_STDOUT_LINES`);
        * aider's own gloss for a server error or a cut stream, which is the
          runner's guess about the vendor rather than the vendor's report of
          itself (:data:`_ADAPTER_GLOSS_LINES`, C7).

        Everything else aider prints, including every genuine ``litellm.*Error``
        and every word the provider itself sent, still reaches the classifier
        unchanged. Both streams are reduced for symmetry with the base contract's
        haystack; measured, aider writes 0 bytes to stderr on all eleven
        captured outcomes, so today only stdout carries either line.
        """
        return super().classify_failure(
            self._drop_adapter_gloss(self._drop_tolerated_lines(stdout)),
            self._drop_adapter_gloss(self._drop_tolerated_lines(stderr)),
            exit_code,
        )

    @property
    def name(self) -> str:
        return "aider"

    @property
    def default_timeout(self) -> int:
        return 600

    def is_available(self) -> bool:
        return shutil.which("aider") is not None

    @staticmethod
    def _extract_read_files(prompt: str) -> List[str]:
        """Existing absolute file paths mentioned in the prompt, deduped.

        These are passed via --read (read-only context; allowed OUTSIDE the
        repo root, unlike editable files). Non-existent paths — notably the
        not-yet-written {output_json_path} — are skipped, as are
        directories and special files (os.devnull is not a regular file).
        """
        found: List[str] = []
        for match in _ABS_PATH_RE.findall(prompt):
            candidate = match.rstrip(".,;:")
            if candidate in found:
                continue
            try:
                if Path(candidate).is_file():
                    found.append(candidate)
            except OSError:
                continue
            if len(found) >= _MAX_READ_FILES:
                break
        return found

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        # aider --model <litellm-model-id> --message "/ask <prompt>" + flags.
        # Every flag is load-bearing: --no-auto-commits (no commits in the
        # target repo), --no-pretty / --no-stream (plain non-ANSI output),
        # --no-check-update / --no-show-release-notes / --no-analytics (no
        # network/update side channels), --no-show-model-warnings /
        # --no-detect-urls / --no-fancy-input (no extra prompts),
        # --no-gitignore (don't touch the target repo's .gitignore),
        # --chat-history-file / --input-history-file os.devnull (no litter
        # files). The "/ask " prefix keeps aider in read-only chat mode (see
        # class docstring). Do NOT pass --no-git: in a git repo aider sends a
        # repo-map; without git the model is blind. Absolute paths mentioned in
        # the prompt (the plan file etc.) are additionally passed via --read,
        # because aider's mention auto-add never matches absolute paths.
        #
        # THIS ARGV ALONE IS NOT THE READ-ONLY INVOCATION
        # (plans/ask-answer-recovery-and-false-success.md D4.2). There is no
        # --yes-always, so aider asks before it adds a file the prompt or a
        # reply names, and the answers are the decline supply
        # build_command_for_transport returns as stdin. Spawned from this argv
        # with stdin at EOF, every prompt takes its default, yes, and the
        # mention auto-add comes back silently (T4.2's run e4: 3.05 MB).
        base_model, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        cmd = [
            "aider",
            "--model",
            base_model,
        ]
        if effort is not None:
            cmd += ["--reasoning-effort", effort]
        cmd += [
            "--message",
            "/ask " + prompt,
            "--no-auto-commits",
            "--no-pretty",
            "--no-stream",
            "--no-check-update",
            "--no-show-model-warnings",
            "--no-analytics",
            "--no-gitignore",
            "--no-show-release-notes",
            "--no-detect-urls",
            "--no-fancy-input",
            "--chat-history-file",
            os.devnull,
            "--input-history-file",
            os.devnull,
        ]
        for path in self._extract_read_files(prompt):
            cmd += ["--read", path]
        return cmd

    def get_env(self, model: str) -> Dict[str, str]:
        # BROWSER=true: neuter webbrowser on rate-limit give-up (see class
        # docstring). COLUMNS=10000: disable the ~80-column hard wrap that
        # inserts literal newlines inside long JSON strings.
        return {"BROWSER": "true", "COLUMNS": "10000"}

    def get_remove_env(self) -> List[str]:
        """``AIDER_YES_ALWAYS``, whatever its value (D4.2).

        An inherited ``AIDER_YES_ALWAYS`` turns yes-always on
        (configargparse's ``AIDER_`` prefix), and then aider answers every
        confirmation "y" without reading the decline supply — measured with
        ``AIDER_YES_ALWAYS=1``: uv.lock re-added, 3.05 MB re-sent. Stripped, the
        same run declines again. A ``.env`` that sets it is refused instead
        (:meth:`build_command_for_transport`), because aider loads that file
        into its own environment after this strip.
        """
        return [AIDER_YES_ALWAYS_ENV]

    def build_command_for_transport(
        self,
        prompt: str,
        model: str,
        transport: str = "argv",
        prompt_file: Optional[str] = None,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
        sandbox_fallback: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> Tuple[List[str], Optional[str]]:
        """The argv, plus the decline supply as the child's stdin (D4.2).

        The read-only invocation is this pair, never :meth:`build_command`'s
        argv alone: with no ``--yes-always``, aider asks before adding each
        file the prompt or a reply names, and ``stdin_text`` answers
        ``"s\\n" * AIDER_DECLINE_LINES``. The argv goes through the base leg
        exactly as the base routes it (so a sandbox-fallback rung would reach
        :meth:`apply_sandbox_fallback`, which aider does not override), and no
        transport is added: ``stdin`` and ``file`` still raise ``ValueError``,
        because a supply-less path would read EOF, and EOF means yes.

        Raises:
            ReadOnlyInvocationRefused: before spawn, when an
                ``.aider.conf.yml`` or a ``.env`` aider loads for this ``cwd``
                turns yes-always on (:func:`_inherited_yes_always`). The error
                names the file. ``invoke_with_provider`` records it as a
                configuration error and never retries it.
        """
        argv, _ = super().build_command_for_transport(
            prompt,
            model,
            transport,
            prompt_file,
            timeout_s=timeout_s,
            schema=schema,
            sandbox_fallback=sandbox_fallback,
            cwd=cwd,
        )
        inherited = _inherited_yes_always(cwd)
        if inherited is not None:
            path, setting = inherited
            raise ReadOnlyInvocationRefused(
                f"aider: yes-always is enabled in {path} ({setting}); the read-only "
                f"lane needs aider to ask so it can decline file adds. Remove the "
                f"setting or set it to false.",
                provider=self.name,
                path=str(path),
            )
        return argv, (AIDER_DECLINE_ANSWER + "\n") * AIDER_DECLINE_LINES

    @staticmethod
    def _unwrap_file_write_envelope(data: Any) -> Any:
        """Unwrap a pseudo file-write envelope emitted in read-only mode.

        The prompt asks the model to WRITE the JSON to a file; /ask mode
        cannot, so some models emulate the write (both shapes observed
        live with kimi-k2.7-code):

        - {"file_path": "...", "content": "<json string>"} — a pseudo
          write-file tool call; parse the content.
        - {"code": "<python that dumps the json>"} — a hallucinated
          code_interpreter call whose source embeds the JSON array as a
          literal; extract it from the code text.

        Return the parsed payload in those cases, the data unchanged
        otherwise.
        """
        if (
            isinstance(data, dict)
            and isinstance(data.get("content"), str)
            and set(data.keys()) <= {"file_path", "path", "filename", "file", "content"}
        ):
            content = data["content"].strip()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                fallback = extract_json_from_text(content, prefer_arrays=True)
                if fallback.get("success"):
                    return fallback["data"]
        if (
            isinstance(data, dict)
            and isinstance(data.get("code"), str)
            and set(data.keys()) <= {"file_path", "path", "filename", "file", "code"}
        ):
            fallback = extract_json_from_text(data["code"], prefer_arrays=True)
            if fallback.get("success"):
                return fallback["data"]
        return data

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse plain-text output from the Aider CLI.

        1. Take the text after the LAST "► **ANSWER**" marker (THINKING
           blocks before it may contain decoy JSON)
        2. Strip trailing "Tokens: ..." / "Cost: ..." accounting lines
        3. Parse the answer as JSON, with fallback extraction for code
           blocks and JSON embedded in prose; unwrap a pseudo file-write
           envelope ({"file_path": ..., "content": "<json>"})
        4. No marker at all -> an exit-0 failure on aider's diagnostic lines
           wins (D4.1, :meth:`_exit_zero_failure`); otherwise fallback
           extraction on the full stdout; nothing extractable -> failure with
           a stdout snippet as the error (aider exits 0 even on auth errors
           and rate-limit give-ups)

        Before any of it, litellm's tolerated cost-map line and the D4.2
        confirmation prompts are removed (:func:`_drop_confirmation_pairs`,
        the one copy of the pair rule the hook shares): the declined prompts
        land in stdout, reply-scan ones after the answer.
        """
        stdout = stdout.strip()
        if not stdout:
            return {"success": False, "error": "Empty output from aider", "raw": stdout, "data": None}
        lines = _drop_confirmation_pairs(self._drop_tolerated_lines(stdout).splitlines())
        text = "\n".join(lines)

        if ANSWER_MARKER in text:
            answer = text.rsplit(ANSWER_MARKER, 1)[1]
            answer = "\n".join(
                line for line in answer.splitlines()
                if not line.strip().startswith(("Tokens:", "Cost:"))
            ).strip()
            if not answer:
                return {"success": False, "error": "Empty answer after ANSWER marker", "raw": stdout, "data": None}
            if answer.startswith(("[", "{")):
                try:
                    data = json.loads(answer)
                except json.JSONDecodeError:
                    pass
                else:
                    return {"success": True, "data": self._unwrap_file_write_envelope(data)}
            result = extract_json_from_text(answer, prefer_arrays=True)
            if result.get("success"):
                result["data"] = self._unwrap_file_write_envelope(result["data"])
                return result
            return {
                "success": False,
                "error": f"No JSON found in aider answer: {answer[:500]}",
                "raw": stdout,
                "data": None,
            }

        # No ANSWER marker (e.g. auth error / rate-limit give-up printed to
        # stdout with exit code 0). An exit-0 failure on a diagnostic line wins
        # BEFORE any JSON is extracted (D4.1): the 2026-09-26 incident's 400
        # body was JSON, so extraction returned it as `success: True`, and a
        # body carrying any array got written as a clean `[]` review.
        failure = self._exit_zero_failure(lines)
        if failure is not None:
            return {"success": False, "error": failure, "raw": stdout, "data": None}
        fallback = extract_json_from_text(text, prefer_arrays=True)
        if fallback.get("success"):
            fallback["data"] = self._unwrap_file_write_envelope(fallback["data"])
            return fallback
        # THE SNIPPET IS TAKEN AFTER THE TOLERATED LINES ARE DROPPED, and that is
        # the difference between a usable diagnosis and 500 characters of noise.
        # Offline, the first ~460 bytes of aider's stdout are litellm's cost-map
        # DNS failure plus the banner, so a failed AUTH run used to report
        # `No JSON found in aider output: HTTPSConnectionPool(host=
        # 'raw.githubusercontent.com'...` and never reached the
        # `litellm.AuthenticationError` further down — measured on the 2026-08-19
        # fixture capture. `_drop_tolerated_lines` already exists for
        # `classify_failure`; the error text needs it for the same reason.
        diagnosis = text.strip() or stdout
        return {
            "success": False,
            "error": f"No JSON found in aider output: {diagnosis[:500]}",
            "raw": stdout,
            "data": None,
        }

    def _exit_zero_failure(self, lines: Sequence[str]) -> Optional[str]:
        """D4.1: the error for an exit-0 failure on aider's diagnostic lines, else ``None``.

        ``lines`` is stdout after :meth:`_drop_tolerated_lines` and
        :func:`_drop_confirmation_pairs`. Only the lines outside the answer
        span are read — the prologue, and everything after the trailing
        accounting line — or every line when no request completed (see the
        module's structure note). Two tests, neither a whole-stdout search:

        - a line that **starts** with ``litellm.`` and matches
          :attr:`exit_zero_failure_markers` once lowercased, as
          ``classify_streams`` matches them (the patterns are lowercase, so
          against raw text they never matched — the survey's correction 4);
        - a whole line in aider's own overflow wording (:data:`_OVERFLOW`).

        A context overflow — either wording, or a litellm line whose body
        states both counts — gets its own sentence (:func:`_overflow_error`);
        any other litellm failure is reported as its own line.
        """
        accounting = _last_accounting_index(lines)
        if accounting is None:
            scanned = list(lines)
        else:
            scanned = list(lines[:_prologue_end(lines)]) + list(lines[accounting + 1:])
        litellm_lines: List[str] = []
        overflow = False
        for line in scanned:
            text = line.rstrip()
            lowered = text.lower()
            if lowered.startswith("litellm.") and any(
                pattern.search(lowered) for pattern in self.exit_zero_failure_markers
            ):
                litellm_lines.append(text)
            if any(pattern.search(text) for pattern in _OVERFLOW):
                overflow = True
        body = next(
            (match for match in map(_BODY_COUNTS_RE.search, litellm_lines) if match),
            None,
        )
        if overflow or body is not None:
            return _overflow_error(body, scanned)
        if litellm_lines:
            return litellm_lines[0][:500]
        return None

    def salvage_text(self, stdout: str) -> Optional[str]:
        """aider's answer text, without its banner, prompts or accounting (D4.1).

        aider's stdout is plain text, but it is not the answer: the prologue,
        the D4.2 confirmation prompts and the trailing accounting line wrap it
        in every run, so the base's "whole stdout" would save aider's banner
        (all ten fixture rows). The reduction, validated by the 2026-09-29
        fixture survey:

        1. drop litellm's tolerated cost-map line, then the confirmation pairs
           (:func:`_drop_confirmation_pairs`, shared with :meth:`parse_output`);
        2. with an ANSWER marker: the text after the last marker, cut at the
           trailing accounting line. Not ``parse_output``'s ``Tokens:``/``Cost:``
           filter, which drops such a line anywhere after the marker and so
           would delete one the answer quotes;
        3. no marker, and D4.1's failure test matches a diagnostic line (never
           inside the answer span): ``""``;
        4. otherwise the text between the prologue and the trailing accounting
           line (to the end when there is none).

        Never ``None``: a stdout with no ``Aider v…`` banner line and no marker
        is ``""``, a final "nothing here", like the other D2.5 hooks. aider
        prints that banner before its first request (the manifest's ``empty``
        row), so a stdout without one comes from a run that never reached a
        model — a startup error, a crash — and ``None`` would hand it whole to
        the generic plain-text rule as if it were the answer.
        """
        if not isinstance(stdout, str) or not stdout.strip():
            return ""
        lines = _drop_confirmation_pairs(self._drop_tolerated_lines(stdout).splitlines())
        has_marker = any(ANSWER_MARKER in line for line in lines)
        if not has_marker and not any(_AIDER_VERSION_RE.match(line) for line in lines):
            return ""
        if has_marker:
            after = "\n".join(lines).rsplit(ANSWER_MARKER, 1)[1].splitlines()
            accounting = _last_accounting_index(after)
            return _join_trimmed(after if accounting is None else after[:accounting])
        if self._exit_zero_failure(lines) is not None:
            return ""
        start = _prologue_end(lines)
        accounting = _last_accounting_index(lines)
        return _join_trimmed(lines[start:] if accounting is None else lines[start:accounting])
