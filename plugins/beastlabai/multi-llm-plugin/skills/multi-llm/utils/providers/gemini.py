"""Gemini CLI provider implementation."""
import json
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

from ..json_extractor import extract_json_from_text
from .base import (
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
)

#: M12 (§6.1): gemini has no rung on the ladder, and the reason is written down
#: rather than left as an absent constant. gemini-cli exposes **no per-run effort
#: control at all** — no flag, no env var — so there is nothing for a ``:effort``
#: suffix to become and no whitelist that could refuse one. Thinking is a
#: *config* fact here: a custom alias with a ``thinkingConfig`` under
#: ``modelConfigs.customAliases`` in ``~/.gemini/settings.json`` (Gemini 3 takes
#: ``thinkingLevel`` LOW/HIGH, 2.5 a numeric ``thinkingBudget``), listed by alias
#: name in ``providers.yaml``. This adapter therefore declares no
#: ``REASONING_EFFORTS``: an empty whitelist and an absent one behave the same
#: way, and only one of them says why.
EFFORT_LADDER = ReasoningLadder(
    provider="gemini",
    declined=(
        "gemini-cli has no per-run effort control (no flag, no env var); "
        "thinking is configured per alias via modelConfigs.customAliases in "
        "~/.gemini/settings.json"
    ),
)

#: A Node stack frame. **Dropped before any message is built** (C4 rung 4): the
#: frames are per-invocation noise carrying absolute paths into
#: ``node_modules``, and leaving them in would make every assertion on the
#: message unstable while adding nothing a user can act on.
_STACK_FRAME = re.compile(r"^[ \t]+at\s.*$", re.MULTILINE)

#: ``Full report available at: /tmp/mllm-inv/gemini-<hex>/…`` — a **fresh temp
#: path every run**, so it is dropped for the same reason as the stack. The
#: prose that FOLLOWS it is the tier-(ii) diagnosis, which is why this pattern
#: captures the remainder of the line rather than only matching the path.
_FULL_REPORT = re.compile(r"Full report available at:[ \t]*\S+[ \t]*(.*)$", re.MULTILINE)

#: Start-up chatter gemini 0.63.0 writes to stderr on EVERY run, an answered one
#: included (measured 2026-10-08 in the pinned image: 189-266 bytes on
#: `success`, `multi-assistant` and `ephemeral-only`, each 0 bytes at 0.25.2).
#: None of it is about the run's outcome — a terminal without 256 colours, no
#: `rg` on PATH, the CLI's own start-up profiler — so it is **dropped before
#: any tier reads the text**: left in, tier (iii) reported "Warning: 256-color
#: support not detected" as the diagnosis of `exit-zero-failure`, and an
#: all-noise stderr stopped being rung 5's ``None``. Whole lines only, each
#: matched by its own measured opening words.
_STARTUP_NOISE = re.compile(
    r"^(?:Warning: 256-color support not detected\b"
    r"|Ripgrep is not available\b"
    r"|\[STARTUP\] )[^\n]*(?:\n|\Z)",
    re.MULTILINE,
)

#: The head of one ``ApiError: {…}`` blob. The payload is brace-nested, so the
#: object itself is read with :data:`_DECODER` rather than by regex.
_API_ERROR = re.compile(r"ApiError:[ \t]*(?=\{)")

#: The head of gemini's trailing machine-readable envelope,
#: ``{"session_id": …, "error": {"type", "message", "code"}}``.
_ENVELOPE = re.compile(r"\{\s*\"session_id\"")

_DECODER = json.JSONDecoder()

#: gemini's `error.message` is ALWAYS this literal string at 0.25.2 — an
#: upstream stringification bug that destroys the diagnosis in the only
#: structured field the CLI offers. It is never reported as a reason; the
#: envelope contributes its ``code`` and nothing else. (0.63.0 fills the field
#: with the real text; the tiers below still answer every capture without it,
#: so it stays unread rather than becoming a fourth source.)
_DESTROYED_MESSAGE = "[object Object]"

#: One short line. ``rate-limit.stderr.txt`` is **15,013 bytes** and
#: ``server-error.stderr.txt`` **14,191**, and nothing is lost by capping,
#: because the caller keeps the full text: Lane A puts it in
#: ``details["stderr"]`` and in the log file. This hook is the summary, not a
#: second copy.
_MAX_DIAGNOSIS_CHARS = 300


def _one_line(text: str) -> str:
    """Collapse a captured fragment to a single line, whitespace normalized."""
    return " ".join((text or "").split())


def _cap(text: str) -> str:
    """One short line (:data:`_MAX_DIAGNOSIS_CHARS`), with an explicit ellipsis."""
    if len(text) <= _MAX_DIAGNOSIS_CHARS:
        return text
    return text[:_MAX_DIAGNOSIS_CHARS - 1].rstrip() + "…"


def _decode_at(text: str, index: int) -> Optional[Dict[str, Any]]:
    """The JSON object starting at ``index``, or ``None``. Never raises."""
    try:
        value, _ = _DECODER.raw_decode(text, index)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


class GeminiProvider(LLMProvider):

    #: MEASURED FALSE 2026-08-19, closing harness-expansion.md §14.7 gap 5.
    #:
    #: This adapter shipped the default `True` and was the last unmeasured one.
    #: Under its own argv — no `--yolo`, no `--approval-mode` — gemini-cli 0.25.2
    #: advertises nine tools and **`write_file` is not among them** (nor
    #: `replace`, nor `run_shell_command`). Handed a `write_file` functionCall it
    #: answers `Tool "write_file" not found in registry`, writes nothing, and
    #: **exits 0 printing the model's own "JSON written to ..." confirmation as
    #: its answer** — so the fan-out recorded a sentence about a file instead of
    #: the review, with `success: True`. That is a worse failure than the four
    #: argv-restricted adapters, which at least refuse in words.
    #:
    #: The restriction is a DEFAULT, not a flag, so the argv guard in
    #: tests/test_provider_housekeeping.py could not see it; that file now carries
    #: NO_WRITE_TOOL_AT_ALL for exactly this shape. Probe:
    #: plans/harness-expansion/probe-out/gemini/gap5_probe.py.
    #:
    #: RE-MEASURED 2026-10-08 on 0.63.0, same probe, same argv: eight tools now
    #: (``enter_plan_mode``, ``glob``, ``google_web_search``, ``grep_search``,
    #: ``invoke_agent``, ``list_directory``, ``read_file``, ``update_topic``),
    #: still none that writes, and the same exit-0 confirmation — only the error
    #: wording moved (``Tool "write_file" not found. Did you mean one of: …``).
    supports_file_output = False
    """Provider for Gemini CLI tool.

    Output shape on stdout: pretty-printed
    ``{"session_id": …, "response": "<the answer>", "stats": {…}}``.
    :meth:`parse_output` unwraps ``response`` and parses it as JSON, falling back
    to :func:`extract_json_from_text` for JSON embedded in prose.

    Everything below was **measured** by the §6 step-5 probe on 2026-08-19
    against ``gemini 0.25.2`` driven offline at a localhost stub
    (``--network none``, no credential), and re-measured by the same rig on
    2026-10-08 against ``gemini 0.63.0`` (what moved is listed at
    :attr:`verified_version`); the raw captures are
    ``tests/fixtures/gemini/`` and its README carries the full record.

    **stdout is empty on every failure.** 401, 429, 404, 400 context-length,
    5xx-forever, a truncated stream, a zero-byte response and a 200 carrying an
    error object all produce **0 bytes on stdout** and put the whole diagnosis on
    stderr — the exact inverse of the opencode trap. ``parse_output`` used to
    read only ``stdout``, so the operator-facing error for all eight was the
    identical, contentless ``JSON parse error: Expecting value: line 1 column 1
    (char 0)``; ``classify_failure`` did read both streams, which is why four of
    them still landed on a category while the parser said nothing.
    **C4 closed that half** (2026-08-20): :meth:`describe_failure` summarizes the
    stderr envelope for both lanes and :meth:`parse_output` names the same text
    in its error branch, so each of the eight now carries the vendor's own
    sentence. The tiers and the rungs are in :meth:`_diagnose`; the split it
    produces over the nine failure captures is 4 / 4 / 1, pinned by
    ``tests/test_stderr_diagnosis.py``. No classification moved with it —
    ``describe_failure`` is diagnostics, never classification.

    **stderr carries a machine-readable envelope whose message is destroyed.**
    After the JS prose and a Node stack, gemini prints
    ``{"session_id", "error": {"type", "message", "code"}}`` — and ``message`` is
    always the literal string ``[object Object]`` (upstream stringification bug
    at 0.25.2). ``code`` is real, and the **process exit code is that code
    truncated to 8 bits**: 401 → 145, 400 → 144, 500 → 244, and a generic
    ``code: 1`` → 1. An exit code from this CLI is a status, not a category;
    ``!= 0`` is the only safe reading of it.

    **Internal retries are real and expensive.** A fail-forever 429 ran **10
    requests over 243 s** inside one awaited subprocess, and a fail-forever 500
    the same (10 / 232 s); a truncated stream, a 401, a 404 and a 400 are each
    **one** request, terminal. **C12 declared it** (2026-08-20): the envelope is
    now on :attr:`internal_retries` with those measured numbers, which the ladder
    reads structurally. Until then §7.5 rule 6(c) budgeted **one** request for a
    chain that really runs ten, and — the expensive half — rule 6(b) re-dispatched
    a rate-limited slot up to ``MAX_RATE_LIMIT_BACKOFFS`` more times, each one
    re-running a four-minute chain the CLI had already run.

    **``supports_file_output`` is inherited as ``True`` and does not hold.**
    Under the argv this adapter emits — no ``--yolo``, no ``--approval-mode`` —
    gemini declares exactly nine tools to the model (``list_directory``,
    ``read_file``, ``search_file_content``, ``glob``, ``activate_skill``,
    ``save_memory``, ``google_web_search``, ``write_todos``,
    ``delegate_to_agent``) and **``write_file`` is not among them**. Answering a
    ``write_file`` call gets ``Tool "write_file" not found in registry``, the
    file is never created, and gemini **exits 0** printing the model's
    ``JSON written to …`` confirmation as its answer — a success report for a
    write that did not happen. That puts this adapter in the same class as
    ``cursor-agent --mode ask`` and ``aider /ask``, and the fix is the
    declaration (``supports_file_output = False``, so
    ``llm_client.render_output_location`` asks for the array on stdout), never a
    ``--yolo``-class argv bypass. Left unchanged here because the roster in
    ``tests/test_provider_housekeeping.py`` is keyed on restriction-shaped argv
    atoms and gemini's argv carries none — its read-only tool set is the
    *default*. See ``tests/fixtures/gemini/README.md`` for the two probe runs
    that measured it (§14.7 gap 5).
    """

    #: MEASURED FALSE by the same 2026-08-19 probe that measured the missing
    #: write tool (``plans/harness-expansion/probe-out/gemini/gap5_probe.py``;
    #: ``NO_WRITE_TOOL_AT_ALL`` in ``tests/test_provider_housekeeping.py``):
    #: under this argv gemini-cli 0.25.2 advertises nine tools and
    #: ``run_shell_command`` is not among them (0.63.0: eight, still without
    #: it). A default rather than a flag, so an argv that later adds ``--yolo``
    #: or ``--approval-mode`` must re-measure this. ``generate_read_scope``
    #: keeps the ``"cwd"`` default: ``read_file`` is advertised, but nothing
    #: measured its reach outside cwd.
    runs_shell_in_generate = False

    version_cmd = ("gemini", "--version")
    #: 0.25.2 is where every fixture in ``tests/fixtures/gemini/`` was first
    #: captured — the §6 step-5 probe, ``--network none``, the stub and the
    #: failserver both running inside the container, no credential — and, until
    #: the 0.63.0 re-capture below, the only release this parser had been run
    #: against. A pin to re-confirm rather than a range to
    #: trust: nothing older has been measured, and the field the parser reads
    #: (``response``) sits beside a ``stats`` block upstream reshapes freely.
    #: ``tests/container/cli-versions.lock`` pins the same string.
    #:
    #: ``gemini --version`` prints a bare version (``0.63.0``) on stdout, which the base
    #: :meth:`parse_version` reads without an override.
    #: NO FLOOR, deliberately. `min_version` was set to 0.25.2 on 2026-08-19 — the
    #: version the §16 fixtures were captured against — and removed the same day
    #: for the reason §5.4.1(a) of harness-invocation-improvements.md states: a
    #: MEASURED-AT version is an upper bound on the true floor, never the floor.
    #: This is a PRE-EXISTING adapter, so a floor pinned to the release that
    #: happened to be in the image newly refuses installs that worked yesterday,
    #: with exit 3 and no evidence that 0.25.2 is where anything actually broke.
    #: (copilot/kimi/qwen-code/vibe keep theirs because they landed *together
    #: with* their probes; muse, cursor-agent and agy leave it empty for this
    #: same reason.) `verified_version` below is warning-only and carries the
    #: measurement instead.
    #:
    #: 0.63.0 since 2026-10-08 (run 10, #10): every row re-captured on it by the
    #: same rig in the pinned image (cli-versions.lock moved to 0.63.0 the same
    #: day). Every parser verdict and classification is unchanged. What moved:
    #: start-up chatter on stderr on every run (dropped by
    #: :data:`_STARTUP_NOISE`, the one parser change), the envelope's
    #: ``message`` now real text, a 429 exiting 173 (``code`` 429, was 1), a cut
    #: stream / error-on-200 / empty answer retried to 4 requests and a zero-byte
    #: response to 10 (each 1 at 0.25.2), and the tool-registry wording.
    verified_version = "0.63.0"

    # C3 — gemini's measured 401 wording matched NONE of the ten base patterns,
    # so a logged-out gemini classified as `None`, was read as transport-shaped
    # and burned the whole bounded-retry budget on a credential no retry can fix.
    #
    # Measured 2026-08-19 against gemini 0.25.2, failserver `--mode 401`
    # (tests/fixtures/gemini/auth-error.stderr.txt, one request, exit 145):
    #   ApiError: {"error":{"code":401,
    #     "message":"Incorrect API key provided: sk-stub***. You can find your
    #                API key at https://platform.openai.com/account/api-keys.",
    #     "status":"UNAUTHENTICATED"}}
    # Two words away from the base set in two different places: Google's status
    # word is `UNAUTHENTICATED`, which is not the `unauthorized` substring, and
    # the vendor sentence is *Incorrect API key provided*, which is not `invalid
    # api key`. Two patterns, one per wording, the way aider's pair was added.
    #
    # `unauthenticated` is a bare single token, so `matches_any` additionally
    # requires an `_ERROR_CONTEXT` word within 48 characters — satisfied here by
    # the `"status"` key it is the value of, and NOT satisfied by prose that
    # merely uses the word. Neither pattern occurs in any gemini success capture.
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "unauthenticated",
        "incorrect api key",
    )

    #: C12 — MEASURED 2026-08-19, on the fail-forever captures in
    #: ``tests/fixtures/gemini/``; the docstring above measured this chain and
    #: deliberately stopped short of declaring it, which left §7.5 rule 6(c)
    #: budgeting **one** request for a chain that really runs ten.
    #:
    #: ``max_requests=10`` and ``max_wall_s=243.0`` are ``rate-limit`` (10
    #: requests over 243 s, nine ``Attempt N failed with status 429. Retrying
    #: with backoff...`` lines on stderr and a tenth attempt that gives up);
    #: ``server-error`` is the same ladder at 10 / 232 s. The wall is declared
    #: rather than left ``None`` — unlike goose's ~7 s, which is round-trip time
    #: against a stub — because it is **dominated by gemini's own sleeping**, so
    #: it holds against any upstream. ``codex``'s stub-measured ``max_wall_s``
    #: is the precedent.
    #:
    #: **``retries_rate_limit=True`` REMOVES a retry, it does not add one.**
    #: Rule 6(b) gives an adapter that declares it **no** identical rate-limit
    #: re-dispatch (``retry_ladder.STOP_VENDOR_ALREADY_RETRIED``), so a
    #: rate-limited gemini slot that used to spend up to
    #: ``MAX_RATE_LIMIT_BACKOFFS`` further dispatches — each one re-running a
    #: four-minute chain the CLI had already run — now ends after one. That is a
    #: **smaller** retry budget, and it is the point: the multiplication is what
    #: rule 6(b) exists to prevent.
    #:
    #: Re-measured 2026-10-08 on 0.63.0: 429 10 / 232 s, 500 10 / 202 s, and a
    #: zero-byte response, now on the same ladder, 10 / 233 s — every chain
    #: inside the declared 10 / 243 s, so the envelope stands.
    #:
    #: ``configurable_by`` is empty because nothing this adapter sets (it passes
    #: only ``--output-format``, ``--model`` and the prompt) reaches gemini's
    #: backoff ladder, which is compiled into ``@google/gemini-cli-core``.
    internal_retries = InternalRetryEnvelope(
        max_requests=10,
        max_wall_s=243.0,
        retries_rate_limit=True,
        configurable_by=(),
    )

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def default_timeout(self) -> int:
        return 900  # Gemini can be slower

    def is_available(self) -> bool:
        return shutil.which("gemini") is not None

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        # gemini --output-format json --model <model> "<prompt>"
        return ["gemini", "--output-format", "json", "--model", model, prompt]

    #: The three tiers :meth:`_diagnose` can answer from, in precedence order.
    #: Named so a test can grade WHICH rung produced an answer rather than only
    #: the text, and so the split itself (4 / 4 / 1 over the nine failure
    #: captures) is an assertion instead of a claim.
    TIER_API_ERROR = "api-error"
    TIER_POST_PATH_PROSE = "post-path-prose"
    TIER_FIRST_LINE = "first-line"

    def _diagnose(self, stdout: str, stderr: str) -> Optional[Tuple[str, str]]:
        """``(tier, one-line message)`` for a failed gemini run, or ``None``.

        The stderr precedence, in the fixed order every caller inherits.

        1. **Channel.** stderr is the diagnosis, stdout is the answer. ``stdout``
           is accepted and deliberately unread. Eight of gemini's nine failure
           captures are 0 bytes on stdout, so the rung decides nothing for them;
           the ninth is what makes it load-bearing. ``exit-zero-failure`` carries
           **1,590 bytes of stdout** (1,174 at 0.25.2) whose ``response`` is the
           model repeating the prompt's own confirmation sentence *"JSON written
           to …"* for a file that does not exist, and **393 bytes of stderr**
           (193) carrying the real reason — *Error executing tool write_file:
           Tool "write_file" not found* (``… in registry`` at 0.25.2). Reading
           stdout here would report the lie.
        3. **Three tiers within stderr**, which between them cover all nine:

           i.   the **last** ``ApiError: {…}`` blob's ``error.message`` and
                ``error.code`` — the vendor's own sentence, and the reason
                ``rate-limit``'s ten identical retry blobs collapse to one line
                (``auth-error``, ``rate-limit``, ``server-error``,
                ``context-overflow``);
           ii.  failing that, the prose sentence following the ``Full report
                available at: …`` path — ``invalid-model``'s *ModelNotFoundError:
                The model `gemini-2.5-flash…`*, ``truncated`` and
                ``error-envelope``'s *Error: Incomplete JSON segment at the end*,
                ``zero-byte-response``'s *Error: exception TypeError: fetch
                failed sending request*;
           iii. failing both, the first stderr line with the stack stripped,
                verbatim — the only tier that reaches ``exit-zero-failure``,
                which has no ``ApiError`` blob, no ``Full report`` path and no
                trailing envelope at all.

           The trailing ``{"session_id", "error": {…}}`` envelope contributes its
           ``error.code`` only when a tier produced a sentence carrying no status
           of its own; **never** its ``error.message``, which is the literal
           string ``[object Object]`` at 0.25.2.
        4. **Three things are dropped before the message is built**, because all
           are noise that would make any assertion on the message unstable or
           wrong: 0.63.0's start-up chatter (:data:`_STARTUP_NOISE`, dropped
           first, before anything else reads the text), the Node stack
           (:data:`_STACK_FRAME`) and the ``/tmp/mllm-inv/…`` report path
           (:data:`_FULL_REPORT`). What is left is capped to one short line.
        5. **Both channels empty is ``None``**, and so is a stderr holding only
           start-up chatter (``ephemeral-only`` at 0.63.0): the rung is the same
           one pi's three silent rows land on: nothing is
           invented from an exit code — which for this CLI is a status truncated
           to 8 bits (401 → 145) and not a category at all.
        """
        # Start-up chatter is not a diagnosis (0.63.0 writes it on every run),
        # so it goes before rung 5 decides whether stderr said anything at all.
        text = _STARTUP_NOISE.sub("", stderr or "")
        if not text.strip():
            return None

        envelope_code = self._envelope_code(text)
        # Rung 4: the stack goes before anything is read out of the text.
        text = _STACK_FRAME.sub("", text)

        blob = self._last_api_error(text)
        if blob is not None:
            message, code = blob
            line = f"{code}: {message}" if code is not None else message
            return (self.TIER_API_ERROR, _cap(_one_line(line)))

        prose = [found.group(1).strip() for found in _FULL_REPORT.finditer(text)]
        prose = [sentence for sentence in prose if sentence]
        if prose:
            return (
                self.TIER_POST_PATH_PROSE,
                _cap(_one_line(self._with_envelope_code(prose[-1], envelope_code))),
            )

        # Rung 4 again: tier (iii) reads raw lines, so the temp path is stripped
        # rather than merely stepped over.
        for line in _FULL_REPORT.sub(r"\1", text).splitlines():
            if line.strip():
                return (
                    self.TIER_FIRST_LINE,
                    _cap(_one_line(self._with_envelope_code(line, envelope_code))),
                )
        return None

    @staticmethod
    def _last_api_error(text: str) -> Optional[Tuple[str, Optional[Any]]]:
        """Tier (i): ``(message, code)`` of the LAST usable ``ApiError`` blob.

        ``rate-limit`` prints nine identical blobs, one per backoff attempt, and
        ``server-error`` prints ten; taking the last collapses the whole chain to
        the line that ended it. A blob whose message is the destroyed
        ``[object Object]`` string is skipped rather than reported.
        """
        found: Optional[Tuple[str, Optional[Any]]] = None
        for match in _API_ERROR.finditer(text):
            payload = _decode_at(text, match.end())
            if payload is None:
                continue
            error = payload.get("error")
            error = error if isinstance(error, dict) else payload
            message = error.get("message")
            if not isinstance(message, str):
                continue
            message = message.strip()
            if not message or message == _DESTROYED_MESSAGE:
                continue
            code = error.get("code")
            found = (message, code if isinstance(code, (int, str)) else None)
        return found

    @staticmethod
    def _envelope_code(text: str) -> Optional[Any]:
        """The trailing envelope's ``error.code``. Its ``message`` is never read.

        ``code`` is the one real field gemini's machine-readable envelope has —
        it is also what the process exit code is, truncated to 8 bits — while
        ``message`` is always :data:`_DESTROYED_MESSAGE`.
        """
        code = None
        for match in _ENVELOPE.finditer(text):
            payload = _decode_at(text, match.start())
            if payload is None:
                continue
            error = payload.get("error")
            if isinstance(error, dict) and isinstance(error.get("code"), (int, str)):
                code = error["code"]
        return code

    @staticmethod
    def _with_envelope_code(sentence: str, code: Optional[Any]) -> str:
        """Append the envelope's status to a sentence that carries none itself."""
        if code is None:
            return sentence
        if re.search(rf"(?<![\w.]){re.escape(str(code))}(?![\w.])", sentence):
            return sentence
        return f"{sentence} (code {code})"

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        """gemini's half of C4: the vendor's own words instead of an exit code.

        Lane A calls this on every non-zero exit and appends the answer to the
        slot's error; Lane B calls it when ``parse_output`` failed and recovered
        no text. gemini exits non-zero on every failure but ``exit-zero-failure``,
        so this is the path that reaches a user. See :meth:`_diagnose` for the
        precedence, and note the one thing it must never report: ``error.message``
        from the trailing envelope, which is the literal string ``[object
        Object]`` at 0.25.2.

        **Diagnostics, never classification.** Nothing here moves any run's
        ``classify_failure`` verdict. In particular the ``exit-zero-failure``
        markers this method now surfaces (``Error executing tool``, ``not found
        in registry``) are deliberately **not** declared as
        ``exit_zero_failure_markers``: declaring them would move that row's
        classification, which is a separate change with its own row. C4 makes
        the sentence visible; classifying on it is somebody else's task.
        """
        diagnosis = self._diagnose(stdout, stderr)
        return None if diagnosis is None else diagnosis[1]

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Unwrap gemini's stdout envelope, and NAME the stderr on a failure.

        The rig calls this on failure rows regardless of exit code and Lane B
        calls it before anything else, so naming the stderr text in the error
        branch is what makes gemini's eight stdout-silent failure rows
        distinguishable from each other at all — before C4 every one of them
        collapsed to the same contentless ``JSON parse error: Expecting value:
        line 1 column 1 (char 0)``.

        Rung 1 is visible in the shape of this method: stdout is parsed on its
        own and keeps ``raw``/``data``/``success`` byte-for-byte, and stderr
        reaches **only** the ``error`` string. ``exit-zero-failure`` is the row
        that proves it — its ``raw`` still carries the stdout ``response`` (*JSON
        written to …*) while its error now names the tool-registry sentence from
        stderr.
        """
        result = self._parse_stdout(stdout)
        if result.get("success"):
            return result

        detail = self.describe_failure(stdout, stderr)
        if not detail:
            return result
        result = dict(result)
        result["error"] = f"{result.get('error') or 'parse failed'} (stderr: {detail})"
        return result

    def _parse_stdout(self, stdout: str) -> Dict[str, Any]:
        """Today's parser, unchanged — the answer channel, read on its own."""
        try:
            wrapper = json.loads(stdout)
            # Gemini returns: {"session_id": "...", "response": "...", "stats": {...}}
            if isinstance(wrapper, dict) and "response" in wrapper:
                response = wrapper["response"]
                # Try to parse the response as JSON if it looks like JSON
                if isinstance(response, str):
                    response = response.strip()
                    if response.startswith(('[', '{')):
                        try:
                            return {"success": True, "data": json.loads(response)}
                        except json.JSONDecodeError:
                            pass
                    # Apply JSON extraction fallback for non-JSON starting responses
                    return extract_json_from_text(response, prefer_arrays=True)
                return {"success": True, "data": response}
            return {"success": True, "data": wrapper}
        except json.JSONDecodeError as e:
            # Try fallback extraction on raw stdout
            fallback = extract_json_from_text(stdout, prefer_arrays=True)
            if fallback.get("success"):
                return fallback
            return {"success": False, "error": f"JSON parse error: {e}", "raw": stdout, "data": None}
