"""Cline CLI provider implementation with JSONL event stream parsing."""
import json
import re
import shutil
from typing import Any, Dict, List, NamedTuple, Optional

from ..json_extractor import extract_json_from_text
from .base import (
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    split_reasoning_effort,
)

# Thinking levels accepted by `cline --thinking` (verified on cline 3.0.39).
# Hard-validated by the CLI — invalid values exit 1. Unlike -m, --thinking
# does not mutate ~/.cline.
#
# The ladder without `minimal` and without `max`. Because cline hard-errors
# rather than warning, this set has to match the CLI exactly: a rung it does not
# have is not a degraded run, it is exit 1 before the model is ever reached.
EFFORT_LADDER = ReasoningLadder(
    provider="cline",
    rungs=("none", "low", "medium", "high", "xhigh"),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted


class ClineStreamReading(NamedTuple):
    """What :func:`read_cline_stream` found in one ``cline --json`` stdout."""

    #: The answer text (D2.5's five steps), or ``""`` for "nothing there".
    text: str
    #: The last ``run_result`` event, or ``None`` when the stream has none.
    run_result: Optional[Dict[str, Any]]
    #: Whether the stream says its turn finished: a ``run_result`` exists, or
    #: the last iteration closed with a ``done`` event whose ``reason`` is
    #: ``completed``. ``False`` for a stream cut before either.
    finished: bool


def read_cline_stream(stdout: str) -> ClineStreamReading:
    """The cline answer reducer: one walk of the JSONL event stream.

    The one implementation of plans/ask-answer-recovery-and-false-success.md
    D2.5's cline reducer, factored out of :meth:`ClineProvider.parse_output`
    (D4.4) so that the parser's no-``run_result`` branch and the
    ``salvage_text`` hook read the same text. Validated by the preflight survey
    on all 11 committed rows, the incident's cut tail and synthetic cuts:

    1. Unparsable lines are ignored (a stream cut mid-line ends on a torn one).
    2. With a ``run_result``: the last one's ``text``, stripped; ``""`` when its
       ``finishReason`` is ``error`` (``text`` is then cline's error sentence,
       never an answer).
    3. Otherwise track the **last iteration** (everything since the last
       ``iteration_start``). A ``done`` event with ``reason: "completed"`` and a
       string ``text`` gives that text.
    4. If the last iteration has any ``contentType: "tool"`` event, ``""``: any
       text there is narration between tool calls.
    5. Otherwise the last ``contentType: "text"`` event's ``accumulated``, else
       its ``text``, else ``""``.

    So a stream cut while the model reasoned after its tool calls — the
    2026-09-26 incident's tail — gives ``""``: nothing the model wrote is an
    answer. ``finished`` records whether step 2 or 3 supplied the text, which
    is what the stream says about the turn ending (D3.1). A live answer
    streamed as per-delta text events is unmeasured (only the stub's one-event
    answer is captured); ``accumulated`` is the running total such a stream
    would carry.

    Never raises on any input; a non-string is read as an empty stream.
    """
    run_result: Optional[Dict[str, Any]] = None
    iteration_text: Optional[str] = None
    iteration_tool = False
    done_text: Optional[str] = None
    # Split on "\n" only, as the parser always has: `str.splitlines` also
    # breaks on U+2028/U+2029 and U+0085, which JSON leaves unescaped inside a
    # string, so an answer holding one would tear its own `run_result` line.
    lines = stdout.split("\n") if isinstance(stdout, str) else []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        if kind == "run_result":
            run_result = event
            continue
        if kind != "agent_event":
            continue
        inner = event.get("event")
        if not isinstance(inner, dict):
            continue
        inner_kind = inner.get("type")
        if inner_kind == "iteration_start":
            iteration_text, iteration_tool, done_text = None, False, None
        elif inner_kind in ("content_start", "content_update", "content_end"):
            content_type = inner.get("contentType")
            if content_type == "tool":
                iteration_tool = True
            elif content_type == "text":
                value = inner.get("accumulated")
                if not isinstance(value, str):
                    value = inner.get("text")
                if isinstance(value, str) and value:
                    iteration_text = value
        elif (
            inner_kind == "done"
            and inner.get("reason") == "completed"
            and isinstance(inner.get("text"), str)
        ):
            done_text = inner["text"]

    if run_result is not None:
        if run_result.get("finishReason") == "error":
            return ClineStreamReading("", run_result, True)
        text = run_result.get("text")
        return ClineStreamReading(
            text.strip() if isinstance(text, str) else "", run_result, True
        )
    # A completed `done` ends the turn even when its text is empty; only a
    # non-empty one supplies the answer (the survey's reducer, step 3).
    finished = done_text is not None
    if done_text:
        return ClineStreamReading(done_text.strip(), None, True)
    if iteration_tool:
        return ClineStreamReading("", None, finished)
    return ClineStreamReading((iteration_text or "").strip(), None, finished)


def cline_answer_text(stdout: str) -> str:
    """The reducer's text alone: :func:`read_cline_stream`'s ``text`` (D2.5)."""
    return read_cline_stream(stdout).text


def _unwrap_answer_text(text: str) -> Dict[str, Any]:
    """The answer text to a parse result, as the ``run_result`` branch does."""
    if text.startswith(("[", "{")):
        try:
            return {"success": True, "data": json.loads(text)}
        except json.JSONDecodeError:
            pass
    return extract_json_from_text(text, prefer_arrays=True)


class ClineProvider(LLMProvider):
    """Provider for the Cline CLI tool.

    Cline with --json runs headless and emits JSONL (one JSON object per
    line): hook_event / agent_event lines followed by a final
    {"type": "run_result", "finishReason": ..., "text": ...} line whose
    "text" field holds the model's answer. On success finishReason is
    "completed"; on error finishReason is "error" and "text" carries the
    error message.

    Config model names use the format "<cline-provider>/<model-id>"
    (e.g. "openrouter/z-ai/glm-5.2"): the segment before the first "/"
    maps to -P (the cline backend provider) and the remainder to -m (the
    model id). A name without "/" is passed straight to -m and uses the
    saved default provider.

    Model strings support an optional ``model[:effort]`` suffix (e.g.
    ``openrouter/z-ai/glm-5.2:high``), stripped off the full string BEFORE
    the provider/model split and translated to ``--thinking <effort>``.
    Valid efforts are listed in REASONING_EFFORTS; anything else passes
    through verbatim as the model name (keeping ``:free``-style ids intact).
    """

    version_cmd = ("cline", "--version")
    #: 3.0.55 is where every fixture in ``tests/fixtures/cline/`` was first
    #: captured — the §6 step-5 probe, ``--network none``, the stub and the
    #: failserver both running inside the container, no credential — and 3.0.70
    #: is where they were last re-captured (below, after 3.0.69) and the version
    #: ``tests/container/cli-versions.lock`` pins.
    #:
    #: 3.0.39 is the *other* release this parser has been run against (the ``user
    #: not found`` auth pattern below was measured there), and the gap between
    #: the two is not cosmetic — **the exit code changed inside it**. At 3.0.39 a
    #: provider failure exited **0** (the measurement recorded on
    #: ``exit_zero_failure_markers``); at 3.0.55 every one of nine failure modes
    #: exits **1** (401, 404, 400 context-length, 500-forever, 429-forever, a
    #: truncated body, a zero-byte response, a 200 carrying an error object and
    #: an empty completion — ``tests/fixtures/cline/manifest.yaml`` records the
    #: nine captures and why `exit-zero-failure` is not-applicable there). The
    #: markers stay declared: :func:`base.classify_streams` consults them
    #: regardless of exit code and they are the last-resort verdict on five of
    #: the committed rows. That is what makes ``verified_version`` worth
    #: re-confirming on every bump.
    #:
    #: **What 3.0.39 is not is a ``min_version``.** A draft declared one, and it
    #: would have been `harness-invocation-improvements.md` §5.4.1(a)'s error
    #: with an extra step: 3.0.39 is merely the oldest release anyone happened to
    #: run, which is an upper bound on the true floor, not the floor. Nothing
    #: measured says 3.0.38 fails — and the one behaviour known to differ across
    #: that range is *already handled by declaration* rather than by a version
    #: comparison, since ``exit_zero_failure_markers`` are consulted whatever the
    #: exit code is. cline is a **pre-existing** adapter, so a floor here refuses
    #: installs that were working yesterday to protect against nothing.
    #: ``min_version`` is a hard exit-3 refusal in
    #: ``subagent_executor._detect_version`` and ``verified_version`` is a
    #: one-line warning; the evidence supports the warning only.
    #:
    #: ``version_cmd`` stays, because it is the only thing that can ever make
    #: ``verified_version`` speak: with no probe the detected version is
    #: ``unknown`` and the warning is skipped. Confirmed against the pinned
    #: binary 2026-08-20 (``docker run --rm --network none --entrypoint
    #: /opt/mllm/real/cline mllm-e2e:local --version``): a bare ``3.0.55`` on
    #: stdout, which the base :meth:`parse_version` reads without an override
    #: (a bare ``3.0.70`` the same way on 2026-10-09).
    #: It is the SLOW probe of the set — cline makes ~10 outbound connects on
    #: ``--version`` alone and takes 8.7 s when egress is blackholed — but that
    #: is well inside ``_run_probe``'s 30 s timeout, and it runs at most once per
    #: process.
    #:
    #: **Moved 3.0.55 -> 3.0.69 on 2026-10-08**: all ten captured rows were
    #: re-run on 3.0.69 by the same rig in the pinned image (the synthesized
    #: ``multi-assistant`` row re-derived from the new ``success``), with no
    #: parser change. Still exit 1 on every failure. What moved: the internal
    #: retry ladder (a 500, a 429 and a zero-byte body now take 6 requests over
    #: 63 s, was 3 over ~8 s); a truncated body and a 200 error object now fail
    #: in one request as ``Response stream ended without a finish reason.``
    #: (was ``Model returned empty response`` after three); and stderr lost its
    #: AI SDK deprecation warnings, so a green run's stderr is empty.
    #:
    #: **Moved 3.0.69 -> 3.0.70 on 2026-10-09**, the same way and again with no
    #: parser change: every file is the length 3.0.69 wrote, the lines differing
    #: only in ids, timestamps, ``durationMs`` and the bundle chunk a stack trace
    #: names. 3.0.70's ``--help`` drops ``--retries``' default from 6 to 3, which
    #: does not touch the HTTP retry ladder: it counts the agent loop's
    #: consecutive mistakes, and a 500-forever run made 6 requests over 63.0 s
    #: under ``--retries 1``, ``--retries 6`` and this argv, which passes none.
    #: Measured on 3.0.70 (``tests/fixtures/cline/manifest.yaml``): a 500, a
    #: 429 and a zero-byte body take 6 requests at 0/2/6/14/30/62 s, as on
    #: 3.0.69; a 429's ``Retry-After`` under 60 s is honoured as the gap (59 s:
    #: 6 requests over 295.9 s), and 60 s or more is ignored for that ladder; a
    #: stalled request is ONE request that cline gives up on after 360 s
    #: (``The operation timed out.``, the new ``stall`` row, ``timeout``).
    #: Nothing measured here reaches ``default_timeout``'s 600 s, though a 429
    #: chain ending in a stall (295 + 360 s, inferred) would; ``internal_retries``
    #: below declares what was measured.
    verified_version = "3.0.70"

    #: §7.6(b), declared 2026-10-09 from the 3.0.70 measurements above (until
    #: then undeclared, so §7.5 rule 6(c) assumed one request where cline makes
    #: up to six):
    #:
    #: * ``max_requests=6``: a 500, a 429 and a zero-byte body each take 6
    #:   requests (0/2/6/14/30/62 s), as on 3.0.69; ``--retries`` (default 3 on
    #:   3.0.70, unset by this argv) counts the agent loop's mistakes and does
    #:   not move it (6 requests under ``--retries 1`` and ``--retries 6``).
    #: * ``retries_rate_limit=True``: the 429 row is 6 requests of 429, so rule
    #:   6(b) adds no identical re-dispatch on top of cline's own chain.
    #: * ``max_wall_s=None``: no bound this adapter can state. A ``Retry-After``
    #:   under 60 s is honoured as the gap (59 s: 295.9 s), a stall is one
    #:   request given up after 360 s, and a chain of the two is not measured;
    #:   rule 4 then makes no admission test, as for pi.
    #: * ``configurable_by`` is empty: no flag, env var or setting moving the
    #:   HTTP ladder was found.
    internal_retries = InternalRetryEnvelope(
        max_requests=6,
        max_wall_s=None,
        retries_rate_limit=True,
    )

    # §7.2 — per-adapter pattern overrides, EXTENDING the base sets.
    #
    # Measured on cline 3.0.39, 2026-08-16, with an invalid OPENROUTER_API_KEY:
    # cline **exits 0** and the whole verdict is structured —
    #   {"type":"run_result","finishReason":"error",…,"text":"User not found."}
    #   {"type":"error","message":"User not found."}
    # The message is the upstream provider's rejection and carries no auth word
    # at all, so without this entry a logged-out cline classified as *nothing*
    # and burned the transport retry budget on a condition no retry can fix.
    # Measured again on cline 3.0.55, 2026-08-19 — the §6 step-5 probe,
    # failserver `--mode 401` (`tests/fixtures/cline/auth-error.*`) — and it is
    # a SECOND wording, not the same one: cline exits **1**, makes exactly one
    # request (no retry), and passes the upstream sentence through verbatim into
    # `run_result.text`, the `agent_event` error and the stderr copy:
    #   Incorrect API key provided: sk-stub***. You can find your API key at …
    # cline glosses nothing, so the phrase to match is the provider's. It
    # matched neither `invalid api key` (a different word order, and
    # `stream_pattern` keeps a left word boundary rather than matching
    # substrings) nor `user not found`, so a 401 fell all the way through to
    # `exit_zero_failure_markers` and answered `runner_error` — a RETRYABLE
    # rung, spent on a credential. Checked against every capture in
    # `tests/fixtures/cline/`: the phrase occurs in `auth-error` alone, so no
    # success row's cell moves (C3).
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "user not found",
        "incorrect api key",
    )
    # No rate-limit override: cline's 429 text is the upstream provider's,
    # already covered by the base set, and nothing cline-specific was measured.
    rate_limit_patterns = LLMProvider.rate_limit_patterns

    #: The exit code carries no verdict (above): ``finishReason`` does. Matched
    #: JSON-key-first so a model quoting the phrase in prose cannot trip it.
    exit_zero_failure_markers = (
        re.compile(r'"finishreason"\s*:\s*"error"'),
        re.compile(r'"errorclass"\s*:'),
    )

    @property
    def name(self) -> str:
        return "cline"

    @property
    def default_timeout(self) -> int:
        return 600

    def is_available(self) -> bool:
        return shutil.which("cline") is not None

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        # cline --json [--thinking <effort>] -P <cline-provider> -m <model-id> "<prompt>"
        # --json auto-activates headless mode; auto-approve defaults to on,
        # so file-read tools work unattended. The prompt goes last as a
        # positional argument.
        base_model, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        cmd = ["cline", "--json"]
        if effort is not None:
            cmd += ["--thinking", effort]
        head, _sep, rest = base_model.partition("/")
        if rest:
            cmd += ["-P", head, "-m", rest]
        else:
            cmd += ["-m", base_model]
        cmd.append(prompt)
        return cmd

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse JSONL event stream output from the Cline CLI.

        1. Scan lines for the LAST {"type": "run_result", ...} event
        2. finishReason == "error" -> explicit failure with the error text
        3. Unwrap "text" and parse it as JSON, with fallback extraction for
           code blocks and JSON embedded in prose

        **With no ``run_result``, only the reducer's text is parsed, never the
        raw stream** (plans/ask-answer-recovery-and-false-success.md D4.4).
        The old fallback ran ``extract_json_from_text`` over the whole stream
        and found the event lines themselves: every failure fixture with its
        ``run_result`` removed came back ``success: True`` with the ``error``
        event as ``data``, and the incident's cut tail with a tool call's
        ``input`` list. Now a ``completed`` ``done`` still carries the answer;
        a stream with no answer text is ``success: False``, ``No run_result
        event found in output``.

        Such a stream also says its turn did not finish, unless a completed
        ``done`` closed it, so the result carries ``"incomplete": True`` (D3.1):
        the ask lane then keeps any text as a partial rather than counting it.
        Measured on 3.0.55, cline writes a ``run_result`` on every exit, so
        only a stream cut short (a kill, a crash) reaches this branch.
        """
        reading = read_cline_stream(stdout)
        run_result = reading.run_result

        if run_result is None:
            if reading.text:
                result = dict(_unwrap_answer_text(reading.text))
            else:
                result = {"success": False, "error": "No run_result event found in output", "raw": stdout, "data": None}
            if not reading.finished:
                result["incomplete"] = True
            return result

        text = run_result.get("text")
        text = text.strip() if isinstance(text, str) else ""

        if run_result.get("finishReason") == "error":
            return {"success": False, "error": text or "Cline run failed", "raw": stdout, "data": None}

        if not text:
            return {"success": False, "error": "Empty text response", "raw": stdout, "data": None}

        return _unwrap_answer_text(text)

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The reducer's answer text, never the event stream (D2.5).

        cline's ``--json`` stdout is transport: ``hook_event`` bookkeeping,
        ``reasoning`` and ``tool`` content (a tool's ``input`` is a JSON list),
        usage, and a ``run_result`` whose ``text`` is cline's error sentence
        when ``finishReason`` is ``error``. This returns exactly
        :func:`read_cline_stream`'s text — the one reducer, shared with
        :meth:`parse_output`'s no-``run_result`` branch — so the ask lane's
        ``answer_text`` and the review lanes' salvage read what the parser
        treats as the answer.

        Always a string: ``generate`` always renders ``--json``, so a stdout
        with no answer text in it (empty, prose, a bare JSON value) is a
        transport that carried none, and ``""`` keeps that verdict final rather
        than sending the caller to stderr's diagnostics.
        """
        try:
            return cline_answer_text(stdout)
        except Exception:  # noqa: BLE001 - the hook must never raise
            return ""
