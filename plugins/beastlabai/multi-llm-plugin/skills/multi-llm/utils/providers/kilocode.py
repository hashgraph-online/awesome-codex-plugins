"""Kilo Code CLI provider implementation."""
import json
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

from ..json_extractor import _ANSI_ESCAPE
from .base import (
    CATEGORY_CONNECTION_ERROR,
    CATEGORY_INVALID_MODEL,
    CATEGORY_SERVER_ERROR,
    LAUNCH_DIAGNOSTICS_NONE,
    REASONING_LADDER,
    STATUS_RATE_LIMITED,
    STATUS_RUNNER_ERROR,
    STATUS_TIMEOUT,
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    split_reasoning_effort,
)
from .parse_kit import answer_from_text

# Reasoning variant names accepted by `kilocode run --variant` (verified on
# kilocode 7.4.1). Variants are model-specific: effort words for
# OpenAI-family/glm models, "thinking"/"instant" for kimi/minimax; unknown
# variants are silently ignored by the CLI.
#
# `thinking`/`instant` are the second axis, not two more rungs — they select a
# MODE, so they are declared as `variants` and pass through without ever being
# compared to (or coerced onto) a rung.
#
# No `model_caps` here on purpose. kilocode's per-model narrowing is *captured*
# rather than hand-written — `tests/fixtures/kilocode/model_variants.json`, from
# `kilocode models <backend> --verbose` — and `tests/test_provider_kilocode.py` already
# grades every configured spec against it. Restating a slice of that capture
# here would give the same fact two owners and one of them no refresh command.
EFFORT_LADDER = ReasoningLadder(
    provider="kilocode",
    rungs=REASONING_LADDER,
    variants=("instant", "thinking"),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted

#: The two names the Kilo Code CLI installs under, in preference order. Upstream
#: ships both spellings; this adapter used to know only the first, so on a
#: machine where the binary landed as `kilo` the provider was not merely degraded
#: — `is_available()` said False and it was invisible to the fan-out. Order is
#: load-bearing: where both resolve, `kilocode` wins, which is what keeps today's
#: argv byte-identical everywhere the canonical name is installed (the container
#: image installs `@kilocode/cli` as `binary: kilocode`).
BINARY_NAMES = ("kilocode", "kilo")

#: What `build_command` emits when neither name resolves. `is_available()` is
#: False in that case, so the provider is filtered out of the fan-out before any
#: spawn and this value never reaches a subprocess — but `build_command` is still
#: called on a binary-free host by the argv-contract tests, the housekeeping
#: `MODELS` table and `seed_expected_argv.py`, all of which pin the canonical
#: spelling. Falling back to it is what makes the change a pure no-op wherever a
#: `kilo`-only install is not in play.
CANONICAL_BINARY = BINARY_NAMES[0]


def _resolve_binary() -> str:
    """The Kilo Code binary name to place at ``argv[0]``.

    Returns the first of :data:`BINARY_NAMES` that ``shutil.which`` resolves, so
    the argv names a binary that is really there rather than a literal this
    module hardcoded. With neither installed it returns
    :data:`CANONICAL_BINARY` — see that constant for why the nothing-installed
    case has a value at all.
    """
    for name in BINARY_NAMES:
        if shutil.which(name) is not None:
            return name
    return CANONICAL_BINARY


# ---------------------------------------------------------------------------
# The stderr diagnosis (`describe_failure`)
# ---------------------------------------------------------------------------
#
# The defect this closes, verbatim from a `review-code` fan-out against an
# account the configured key no longer belonged to: the CLI painted
# `\x1b[91m\x1b[1mError: \x1b[0mUser not found.` onto stderr, exited 1, and the
# operator-visible line read `kilocode exited with code 1`. That line sent the
# reader looking for a JSON or parse problem when the fix was `kilocode` auth.
# `base.LLMProvider.describe_failure` is this codebase's designated place to
# name a failure, and its contract says neither caller prints raw stderr of its
# own — Lane A (`llm_client`) builds `f"{provider} exited with code {n}"` and
# appends only this hook's answer, Lane B (`subagent_executor`) folds it into
# the rung-4 message — so the repair belongs in the adapter and nowhere else.
# `plans/reaggregate-identity-and-salvage-gating.md` residual item 4 carries the
# incident; `tests/test_stderr_diagnosis.py` carries the captured bytes.


#: The ANSI/OSC pattern is **imported, not retyped**, and the direction of the
#: import is the whole argument: ``utils.json_extractor`` sits BELOW the provider
#: layer — this module already reads ``extract_json_from_text`` out of it — so
#: depending on it downward costs nothing and closes no cycle. The copy in
#: ``providers/cursor_agent`` exists because that module needs no extractor at
#: all, and the one *in* ``json_extractor`` exists because it may not import
#: upward into ``providers/``; neither reason applies here, and its own comment
#: names this adapter's dead-account payload as the bytes it was written for. A
#: third spelling of one rule is what that would be. The name is module-private
#: by convention rather than by boundary (``utils/run_status`` reads
#: ``cli_common._modes`` the same way), and it is a strict superset of the
#: narrower SGR pattern :meth:`KiloCodeProvider.parse_output` used to inline, so
#: routing both readers through it removes a second, weaker notion of "ANSI"
#: from this file rather than adding one.
def _strip_ansi(text: str) -> str:
    """``text`` with the colour the CLI paints its own output in removed."""
    return _ANSI_ESCAPE.sub("", text or "")


#: How kilocode frames a failure it reports itself: bold red ``Error: ``, then a
#: reset flush against the cause, opening a stderr line. Every failure row of
#: tests/fixtures/kilocode/manifest.yaml (7.8.27) prints it, the 401, 429 and 500
#: rows included, and nothing else on stderr opens with it: the run banner and
#: the tool trace (``ESC[0m→ ESC[0mRead <the file it opened>``, the
#: ``multi-assistant`` row) open on a bare reset. :func:`_error_lines` reads
#: the lines that open with it (behind any resets) when stderr is painted.
_PAINTED_ERROR = "\x1b[91m\x1b[1mError: \x1b[0m"

#: Resets ahead of the paint on the same line (``ESC[0m``, ``ESC[m``): the
#: same framing.
_LEADING_RESETS = re.compile(r"(?:\x1b\[0?m)*")

#: The cause OpenRouter's gateway gives for an upstream refusal, with the
#: refusal's JSON body on the lines after it.
_PROVIDER_RETURNED_ERROR = "Error: Provider returned error"

#: Most lines a refusal's JSON body after ``Provider returned error`` may span.
_BODY_MAX_LINES = 64


def _own_error_line(line: str) -> bool:
    """Whether *line* opens on :data:`_PAINTED_ERROR`, behind any resets."""
    return line.startswith(_PAINTED_ERROR, _LEADING_RESETS.match(line).end())


def _error_lines(stderr: str) -> str:
    """The stderr lines kilocode paints as its own ``Error:``, colour off.

    A reset ahead of the paint is the same framing; an unpainted line (a
    tool's output, a wrapped continuation, any line of an uncoloured run) is
    not kilocode's, and the banner (``> code``) and the tool trace (``→``)
    never open so.
    """
    return "\n".join(
        _strip_ansi(line) for line in (stderr or "").split("\n") if _own_error_line(line)
    )


def _body_error_code(lines: List[str], start: int) -> Optional[str]:
    """The ``error.code`` (or top-level ``code``) of the JSON object opening
    ``lines[start]``, within :data:`_BODY_MAX_LINES`; ``None`` without one."""
    rest = _strip_ansi("\n".join(lines[start:start + _BODY_MAX_LINES]))
    opening = rest.lstrip(" \t\r\n")
    if not opening.startswith("{"):
        return None
    try:
        body, _ = json.JSONDecoder().raw_decode(rest, len(rest) - len(opening))
    except (ValueError, RecursionError):
        return None
    if not isinstance(body, dict):
        return None
    error = body.get("error") if isinstance(body.get("error"), dict) else body
    code = error.get("code")
    return None if isinstance(code, bool) or code is None else str(code).strip()


def _gateway_rate_limited(stderr: str) -> bool:
    """Whether a painted ``Error: Provider returned error`` is followed by a
    JSON body whose code is 429. Read as the structured code only: nothing
    in the body (its message, its metadata) reaches a text table."""
    lines = (stderr or "").split("\n")
    return any(
        _own_error_line(line)
        and _strip_ansi(line).rstrip() == _PROVIDER_RETURNED_ERROR
        and _body_error_code(lines, index + 1) == "429"
        for index, line in enumerate(lines)
    )


#: The verdicts the tables rank below a rate limit, which kilocode's
#: structured 429 outranks (:meth:`KiloCodeProvider.classify_failure`).
_BELOW_RATE_LIMIT = frozenset({
    None, STATUS_TIMEOUT, STATUS_RUNNER_ERROR, CATEGORY_CONNECTION_ERROR,
    CATEGORY_INVALID_MODEL, CATEGORY_SERVER_ERROR,
})


def _one_line(text: str) -> str:
    """Collapse a captured fragment to a single line, whitespace normalized."""
    return " ".join((text or "").split())


#: One short line, the same number ``providers/pi`` and ``providers/gemini``
#: chose and for the same stated reason: the caller keeps the full text — Lane A
#: in ``details["stderr"]`` and in the log file it names one line earlier — so
#: this hook is the SUMMARY and never a second copy of the stream. kilocode's
#: committed capture is 75 bytes of stderr that reduce to a 22-character
#: sentence, so nothing measured is cut here; the cap exists so a future release
#: that starts printing a retry chain or a help footer cannot turn the operator's
#: error line into a screenful.
_MAX_DIAGNOSIS_CHARS = 300


def _cap(text: str) -> str:
    """One short line (:data:`_MAX_DIAGNOSIS_CHARS`), with an explicit ellipsis."""
    if len(text) <= _MAX_DIAGNOSIS_CHARS:
        return text
    return text[:_MAX_DIAGNOSIS_CHARS - 1].rstrip() + "…"


#: kilocode's run header — ``> code · moonshotai/kimi-k3`` in the capture, the
#: mode and the resolved model echoed back. It is printed by a run that succeeds
#: as readily as by one that dies, so it is chrome and never a diagnosis, and it
#: is dropped for the reason ``providers/gemini`` drops its Node stack and its
#: ``/tmp/mllm-inv/…`` report path (C4 rung 4): per-invocation noise that would
#: make every assertion on the message unstable while telling a reader nothing
#: they can act on.
#:
#: **Why ``^>`` and not the exact banner.** Matching ``> code · <model>`` would
#: pin the diagnosis to today's display string — the separator, the mode word and
#: a model name that changes per slot — so the first release that reworded the
#: header would either report the header as the failure (when it is the only line
#: left) or, worse, keep passing while quietly grading a different line. ``>`` is
#: the CLI's own quoting prefix for what it echoes back, which is the *shape* of
#: the thing being dropped rather than one rendering of it. Widening further —
#: dropping every line without an error label, say — would delete the fallback
#: tier's whole job, which is to speak for a failure whose wording nobody here
#: has seen.
_BANNER_LINE = re.compile(r"^>\s")

#: The label kilocode paints in bold red ahead of the cause: ``Error: User not
#: found.`` once the escapes are off.
#:
#: **Two calibration decisions, both against over-fitting in one direction and
#: guesswork in the other.** It is not widened to ``fatal``/``failed``: this is
#: the only label this repo has captured from this CLI, an unmeasured synonym is
#: a guess dressed as a parser, and the fallback tier already answers every line
#: the label misses. And it is *searched with no boundary at its head* rather
#: than anchored, because whatever the CLI prints ahead of the label sits flush
#: against it — this very payload after a round-trip through a log that dropped
#: its ESC bytes arrives as ``[91m[1mError: [0mUser not found.`` (the shape
#: ``tests/test_json_extractor.py`` pins for the salvage gate), and both an
#: anchor and a leading ``\b`` lose it to the content-free ``[0m`` residue on the
#: line above. The price is that a word *ending* in "error" followed by a colon
#: would also match, and it is the right price: both tiers report a verbatim
#: stderr line, so the looseness can only ever choose a different true line, it
#: can never invent one.
_ERROR_LABEL = re.compile(r"error\s*:", re.IGNORECASE)


class KiloCodeProvider(LLMProvider):
    """Provider for Kilo Code CLI tool.

    Kilo Code uses `run --auto` for non-interactive mode with plain text output.
    The --json flag is avoided because it streams every reasoning token as a
    full-content-so-far JSON line, producing massive output (~2.6MB for ~50KB
    of actual content). Model selection is via `-m provider/model` flag.

    Model strings support an optional ``model[:effort]`` suffix (e.g.
    ``openai-native/gpt-5.5:high``), translated to ``--variant <effort>``.
    Valid efforts are listed in REASONING_EFFORTS; anything else passes
    through verbatim as the model name (keeping ``:free``-style ids intact).

    The CLI ships under **two** binary names, ``kilocode`` and ``kilo``
    (:data:`BINARY_NAMES`). Both ``is_available()`` and ``build_command`` go
    through :func:`_resolve_binary`, so a ``kilo``-only install is a working
    provider rather than an invisible one, and ``argv[0]`` always names a binary
    the resolver actually found.

    **The diagnosis is on stderr, in colour, and it used to be thrown away.**
    A failing run writes a painted ``Error: <cause>`` line to stderr under its
    own run banner and exits non-zero; stdout is the answer channel and is empty
    on the one failure this repo has captured. With no
    :meth:`describe_failure` the whole of that reached the operator as
    ``kilocode exited with code 1`` — measured on a dead account, whose real
    stderr was ``Error: User not found.`` and whose fix was provider auth rather
    than the JSON repair the bare exit code sent its reader after. The override
    puts the CLI's own sentence into both lanes' error strings; the precedence
    is in :meth:`_diagnose`, and the captured bytes are pinned in
    ``tests/test_stderr_diagnosis.py`` beside ``pi``'s and ``gemini``'s.
    """

    #: stdout **is** the model's reply — plain text, never a transport — and the
    #: diagnosis is stderr (:meth:`_diagnose`, rung 1). So the ask lane's
    #: answer-text reducer returns a direct JSON, array or NDJSON answer whole
    #: instead of reading it as an envelope (plans/ask-answer-recovery-and-false-
    #: success.md D2.2). A flag rather than a :meth:`salvage_text` override: the
    #: hook also feeds the review lanes' salvage, and kilocode has no captures to
    #: label that change against.
    answer_framing = "plain"

    #: :attr:`~.base.LLMProvider.EXIT0_CLASSIFIABLE`, reviewed: kilocode's
    #: stdout is the model's answer as plain text, so nothing on it can be told
    #: apart from what kilocode wrote.
    EXIT0_CLASSIFIABLE = False

    #: :attr:`~.base.LLMProvider.LAUNCH_DIAGNOSTICS`, from the captures: ``kilocode run``
    #: prints its banner and its tool trace on stderr (tests/test_container_live_provider.py
    #: ``MODEL_ECHO_ON_STDERR``), the trace naming what the model chose to read or run; no
    #: capture shows the trace's format or where a tool's output ends, so none of stderr is
    #: read for a batch-fatal verdict.
    LAUNCH_DIAGNOSTICS = LAUNCH_DIAGNOSTICS_NONE

    #: :attr:`~.base.LLMProvider.internal_retries`, from the captures
    #: (tests/fixtures/kilocode/manifest.yaml, 7.8.27): against a fail-forever
    #: stub, kilocode ran the same chain of 6 requests on a 429 (70.48 s), a
    #: 500 (78.18 s) and a reset connection (68 s) before printing its error, so
    #: ``retries_rate_limit`` is ``True`` and the retry ladder sends no identical
    #: re-dispatch of a rate-limited slot (docs/development/providers.md). Neither bound is proven:
    #: ``max_requests`` is ``None`` because a run makes one request per model
    #: turn (2 on ``multi-assistant``, 3 on ``context-overflow``) and each turn
    #: may run its own chain, and ``max_wall_s`` is ``None`` because the observed
    #: walls are a stub's, not a worst case. ``configurable_by`` is empty: the
    #: argv carries no retry or timeout flag and the adapter sets no env.
    internal_retries = InternalRetryEnvelope(
        max_requests=None,
        max_wall_s=None,
        retries_rate_limit=True,
        configurable_by=(),
    )

    #: OpenAI's 401 sentence, relayed verbatim on stderr
    #: (tests/fixtures/kilocode/rows/auth-error, 7.8.27): ``Error: Incorrect API
    #: key provided: sk-…``. No base pattern reads it; cline and gemini declare
    #: the same wording. The whole clause, so a line that only mentions an API
    #: key does not match. ``User not found.`` stays out (:meth:`describe_failure`).
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "incorrect api key provided",
    )

    @property
    def name(self) -> str:
        return "kilocode"

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """What kilocode itself reported: none of stdout, and only the stderr
        lines it paints as its own ``Error:``, colour off (:func:`_error_lines`).

        stdout is the model's answer and nothing else (:attr:`answer_framing`),
        so a failed run's partial answer quoting ``Incorrect API key provided``
        or a rate limit is dropped whole. stderr also carries the run banner and
        the tool trace, which names what the model chose to read or run
        (``→ Read docs/<any name>.md``), so a line is kept only when it opens on
        :data:`_PAINTED_ERROR`, the framing of every captured failure (a reset
        ahead of it allowed). The paint comes off the kept line because its
        reset sits flush against the cause's first word, where a pattern's left
        word boundary (:func:`~.failure_classifier.stream_pattern`) cannot see
        one. Anything else, a wrapped cause's continuation line and every line
        of an uncoloured run included, gives no verdict: text nobody can
        attribute is one bounded retry, never a stop.

        It feeds the classification and its quote (the base docstring names the
        two appliers), never the stored streams or :meth:`describe_failure`.
        """
        try:
            return "", _error_lines(stderr)
        except Exception:  # noqa: BLE001 - a failed reduction returns its input
            return stdout, stderr

    def classify_failure(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[str]:
        """The base rule over :meth:`vendor_text`, then the gateway's 429.

        ``Error: Provider returned error`` names no cause; the JSON body on
        the lines after it does, as a structured code. A painted one with
        code 429 is ``rate_limited``, in a rate limit's place in the tables'
        order (a context overflow or a login notice still wins). The body's
        message and metadata never reach a table, so nothing quoted in them
        decides (docs/development/providers.md#reading-a-capture).
        """
        verdict = super().classify_failure(stdout, stderr, exit_code)
        if verdict in _BELOW_RATE_LIMIT and _gateway_rate_limited(stderr):
            return STATUS_RATE_LIMITED
        return verdict

    def is_available(self) -> bool:
        return any(shutil.which(name) is not None for name in BINARY_NAMES)

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        binary = _resolve_binary()
        base_model, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        if effort is not None:
            return [binary, "run", "--auto", "-m", base_model, "--variant", effort, prompt]
        return [binary, "run", "--auto", "-m", model, prompt]

    #: The two tiers :meth:`_diagnose` can answer from, in precedence order.
    #: Named — rather than left as an unlabelled branch — so a test can grade
    #: WHICH tier produced an answer and not only the text, exactly as
    #: ``providers/pi``'s two and ``providers/gemini``'s three are graded in
    #: ``tests/test_stderr_diagnosis.py``.
    TIER_ERROR_LINE = "error-line"
    TIER_FIRST_LINE = "first-line"

    def _diagnose(self, stdout: str, stderr: str) -> Optional[Tuple[str, str]]:
        """``(tier, one-line message)`` for a failed kilocode run, or ``None``.

        The stderr precedence, in the fixed order both lanes inherit — the same
        five rungs ``providers/pi`` and ``providers/gemini`` are written against,
        so a reader who has read one has read this one:

        1. **Channel.** stderr is the diagnosis, stdout is the answer.
           ``stdout`` is accepted and deliberately unread. It is the stream
           :meth:`parse_output` reads the model's reply out of, and gemini's
           ``exit-zero-failure`` capture is the standing proof of what reading it
           here would cost: 1,174 bytes of a model confidently confirming a write
           that never happened, ready to be reported as the reason the run died.
        2. **Rung 4 first — the paint and the chrome come off.** kilocode colours
           its own output, so :func:`_strip_ansi` runs before any line is looked
           at (an ``\\x1b[91m\\x1b[1m`` prefix is otherwise part of the "first
           character" of every line), and :data:`_BANNER_LINE` drops the run
           header. Blank lines go with them: after the escapes are removed the
           capture's ``\\x1b[0m``-only lines are empty strings.
        3. **Two tiers over what is left**:

           i.  the **last** line carrying kilocode's own :data:`_ERROR_LABEL` —
               ``Error: User not found.`` on the dead-account capture. *Last*
               rather than first for the reason gemini takes the last of its ten
               identical ``ApiError`` blobs: where a CLI retries, it is the line
               that ended the run that a reader needs, and where it does not
               (every capture here) last and first are the same line;
           ii. failing that, the **first** line still standing, verbatim — the
               tier gemini also falls back to. First rather than last, because a
               CLI that adds anything after its error line adds a hint, a
               "run `kilocode login`" footer or a stack, and reporting the
               footer instead of the failure is precisely the diagnosis step
               this hook exists to give back.

        4. The result is collapsed to one line and capped
           (:data:`_MAX_DIAGNOSIS_CHARS`).
        5. **Nothing on stderr is ``None``.** A run whose stderr is empty, or
           holds only the banner, gets no editorial: nothing is invented from an
           exit code, which is the rung pi's three silent captures land on. The
           banner-only case is why that rung is a rule here rather than a
           formality — echoing ``> code · <model>`` back as a failure reason
           would read like a diagnosis and be none.
        """
        lines = [_one_line(line) for line in _strip_ansi(stderr).splitlines()]
        lines = [line for line in lines if line and not _BANNER_LINE.match(line)]
        if not lines:
            return None

        for line in reversed(lines):
            if _ERROR_LABEL.search(line):
                return (self.TIER_ERROR_LINE, _cap(line))
        return (self.TIER_FIRST_LINE, _cap(lines[0]))

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        """kilocode's operator-visible line: the CLI's words, not its exit code.

        Lane A (``llm_client``) calls this on every non-zero exit and appends the
        answer to ``kilocode exited with code <n>``; Lane B
        (``subagent_executor``) calls it when :meth:`parse_output` failed and
        recovered no text — which is every failure where kilocode wrote nothing
        to stdout. On the dead-account capture the two together turn
        ``kilocode exited with code 1`` into
        ``kilocode exited with code 1: Error: User not found.``.

        :meth:`parse_output`'s error branch is deliberately **not** given a
        matching clause. ``pi`` and ``gemini`` grew one because the §6.2 fixture
        rig grades that string against a committed manifest; kilocode ships no
        manifest and no capture pairs, both lanes already reach this hook, and
        naming the stderr there as well would move the ``error`` string every
        existing kilocode parse test asserts on for nothing. The only thing that
        method loses in this change is its private, narrower ANSI regex — see
        its docstring.

        **Diagnostics, never classification.** Nothing here moves any run's
        :meth:`classify_failure` verdict — that reads only kilocode's painted
        ``Error:`` lines (:meth:`vendor_text`) through the declared pattern
        tables and never consults this method. In particular
        ``User not found.`` is *not* added to ``auth_error_patterns`` by this
        change: ``providers/cline`` declares that wording because it measured it,
        and declaring it here would move this capture's category from ``None`` to
        ``auth_failed`` (and append a ``[needs-auth]`` tag to the line above).
        That is a separate change with its own measurement; this one makes the
        sentence visible.
        """
        diagnosis = self._diagnose(stdout, stderr)
        return None if diagnosis is None else diagnosis[1]

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse output from Kilo Code CLI.

        Strips ANSI escape codes from plain text output, then attempts
        JSON extraction from code blocks or embedded JSON in text.

        The strip goes through :func:`_strip_ansi` — the one rule this file has
        — rather than the narrower SGR-only ``re.sub`` inlined here before
        :meth:`describe_failure` existed. Two notions of "ANSI" in one adapter is
        the drift worth removing, and the shared pattern is a strict superset of
        the old one (it adds ``?``-parameterized CSI sequences and the OSC form),
        so no stream that parsed before parses differently now.
        """
        return answer_from_text(_strip_ansi(stdout), empty_error="Empty output")
