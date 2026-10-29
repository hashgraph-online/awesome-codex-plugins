"""Muse Code CLI provider implementation with JSONL event stream parsing."""
import json
import shutil
from typing import Any, Dict, Iterator, List, Optional, Tuple

from ..json_extractor import extract_json_from_text
from .base import (
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    split_reasoning_effort,
)

# Reasoning effort values accepted by `muse exec --reasoning-effort`
# (verified live against Muse Code 0.1.0-R708.1). Unlike most providers here,
# muse HARD-ERRORS on an unrecognised value ("unsupported reasoning effort
# `x`; expected none|minimal|low|medium|high|xhigh|ultra") rather than
# ignoring it, so the whitelist has to match the CLI exactly.
#
# muse is the outbound half of the `ultra` ≡ `max` pair: its rejection text
# above shows it has no `max` at all, so `ultra` is declared as muse's SPELLING
# of the top rung. The ladder therefore renders canonical `max` as `ultra` here,
# where codex — which takes `max` verbatim — accepts `ultra` inbound and emits
# `max`. Same two words, opposite directions, one table each.
EFFORT_LADDER = ReasoningLadder(
    provider="muse",
    rungs=("none", "minimal", "low", "medium", "high", "xhigh"),
    spellings=(("ultra", "max"),),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted


class MuseProvider(LLMProvider):
    """Provider for Meta's Muse Code CLI tool.

    ``muse exec --json`` emits JSONL records on stdout. Each record is an
    envelope — ``{"sequence": N, "record_type": ..., "payload_type": ...,
    "payload": {...}}`` — and only three payload types matter here:

    - ``run.output.delta``  — raw streaming text chunks. These are token-level
      fragments, NOT message boundaries: a single assistant message arrives
      split across many deltas.
    - ``tool.result``       — a completed tool call, which is the only usable
      marker between assistant messages (see parse_output).
    - ``run.terminal.*``    — the closing record, carrying ``terminal``
      (completed/failed), ``reason``, and ``text``.

    Model strings support an optional ``model[:effort]`` suffix (e.g.
    ``muse-spark-1.2:xhigh``), translated to ``--reasoning-effort <effort>``.
    Valid efforts are listed in REASONING_EFFORTS; anything else passes
    through verbatim as the model name. Without a suffix muse does NOT use
    the ``--reasoning-effort`` default advertised in ``--help``; it uses
    ``reasoning_effort`` from the user's ~/.config/muse/settings.json.

    ``--disable-approval`` is mandatory, not a convenience: muse's default
    approval policy is ``on-request``, and a tool call the policy judges risky
    (verified with ``rm -rf``) blocks on a prompt that headless exec can never
    answer — the run writes no further output and burns the entire timeout.

    ``--disable-sandbox`` is its sibling (D6, 2026-09-11). muse's shell
    sandbox is bubblewrap with ``--unshare-net``, and on a stock Ubuntu 24.04
    (``kernel.apparmor_restrict_unprivileged_userns=1``) bwrap cannot start at
    all — every sandboxed write dies on ``bwrap: loopback: Failed RTM_NEWADDR:
    Operation not permitted``, the failure that took codex's reviews, and muse
    ships no Linux self-test to say so beforehand (``muse sandbox`` is
    Windows-only). The earlier argument for leaving the sandbox on — "it
    already permits writes under the workspace root" — is true only where
    bubblewrap works. The flag is to muse's sandbox what
    ``--skip-git-repo-check`` is to codex's trust gate: an explicit headless
    choice over an interactive default. ``--yolo`` is NOT that flag: it also
    grants workspace trust, which the next paragraph leaves to the user.

    Workspace trust is also left at muse's default. An untrusted workspace
    only skips project-local instructions, skills, and hooks — file reads and
    writes still work — so this defers to the user's own ``muse`` trust store
    rather than granting trust from inside a review run.
    """

    # §7.2 — per-adapter pattern overrides, EXTENDING the base sets.
    #
    # muse's failures are structured: exit 1 with stderr carrying only "run
    # ended with Failed", and the real cause on stdout in the
    # `run.terminal.failed` record's `reason` — which is why `describe_failure`
    # exists. Two recorded shapes the base English lists do not carry:
    #
    # * an unfunded account gives `API error 402 … Billing verification failed …
    #   (after 10 provider attempts)`. That is a credit/quota condition, so it
    #   belongs on the rate-limit rung (backoff, budget not consumed) rather
    #   than on the generic transport rung.
    # * `API error 401` is muse's auth spelling; the bare token `401` is not in
    #   the base auth set at all (it is only a *context* word there).
    #
    # MEASURED 2026-08-19, WIDENED 2026-08-20 (C3) — the first two entries below
    # did not fire on the one 401 this repo has actually captured.
    # `tests/fixtures/muse/`'s `auth-error` row is a real 401 from
    # `failserver.py --mode 401`, and muse SWALLOWS the vendor text: the strings
    # `401`, `API error` and `Incorrect API key provided` appear **nowhere** in
    # the 17 KB capture. What muse writes instead is its own gloss, in the
    # `run.terminal.failed` record's `reason` — "your API key from META_API_KEY
    # was rejected — update or unset it" — which matched none of the twelve base
    # patterns, so a rejected muse credential classified as **None** and landed
    # on the transport rung with a full retry budget: the one condition §7.2
    # makes terminal, retried until the slot's budget ran out.
    #
    # The last two entries are that gloss, taken from the committed capture
    # rather than from new bytes, and they are two independent anchors on one
    # sentence — the credential's SOURCE ("your API key from <VAR>") and muse's
    # own remedy ("update or unset it") — so a build that rewords one half is
    # still classified by the other. Both are multi-word, so `matches_any`
    # accepts them without the bare-token context window.
    #
    # `was rejected` — the other half of the wording the fixture README
    # suggested — is deliberately NOT here. C1's `vendor_text` drops muse's two
    # prompt-echoing payloads, but it leaves every `run.output.delta`, so the
    # MODEL's answer text is still in the haystack; "was rejected" is a sentence
    # a code review legitimately writes, and a false auth verdict fails the whole
    # batch. Verified against every row in `tests/fixtures/muse/`: the two
    # patterns below occur in `auth-error` and in nothing else, and no success
    # capture moves.
    #
    # The `api error 401` / `403` entries are NOT removed: they are still what
    # the live 402 shape's sibling statuses spell, and nothing has measured a
    # live 401 against a real Meta endpoint.
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "api error 401",
        "api error 403",
        "api key from",
        "update or unset it",
    )
    rate_limit_patterns = LLMProvider.rate_limit_patterns + (
        "api error 402",
        "billing verification failed",
        "api error 429",
    )

    # A THIRD MEASURED SHAPE, recorded rather than fixed, and it is a base-table
    # ORDERING fact rather than a missing pattern here. muse prefixes every
    # vendor error it does not gloss with `API error <status>: <vendor text>`,
    # and `\bapi error\b` is a member of `base.SERVER_ERROR_MARKERS`, which
    # `classify_streams` consults BEFORE `INVALID_MODEL_MARKERS`. So muse's 404
    # — which is otherwise ideal, keeping the vendor sentence verbatim and
    # NAMING the model ("API error 404: The model `muse-spark-9.9-nonexistent`
    # does not exist or you do not have access to it.") — classifies as
    # `server_error`, a retryable transport category, instead of the terminal
    # `invalid_model` whose fix is a config edit. Pinned by
    # `tests/fixtures/muse/`'s `invalid-model` row, which asserts the
    # classification the code produces today. The 402/429 rungs above are
    # unaffected: rate limits are checked before the server table.

    # §7.6(b), declared 2026-08-20 (C12). Measured, never inferred — every
    # number below is read off a committed capture in `tests/fixtures/muse/`:
    #
    # * `max_requests = 40` — the canonical `truncated` row's own terminal
    #   sentence, `4 failed attempts (40 provider requests) over 12m16s`
    #   (`manifest.yaml`'s `truncated` notes; `truncated.stdout.txt`'s
    #   `run.terminal.failed` reason). muse's ladder is a ladder OF ladders:
    #   ten provider attempts per round (`opening meta model stream attempt
    #   N/10`), rounds repeated until a wall-clock ceiling. The single-round
    #   chain alone is 10 attempts / 30 POSTs / 248 s, identical to two decimals
    #   on the 5xx and the 429 at 0.1.0 (`stdout-error` and `rate-limit`,
    #   `wall_s: 248.16` / `248.18`, `requests: 32`; 250.69 / 249.04 and 31 at
    #   1.4.3, the same ten attempts), with backoff `1s, 2s, 4s, 8s, 16s,
    #   32s, 60s, 60s, 60s` — exponential, capped at 60 s, 243 s of it sleeping
    #   (`README.md`'s "What this set found" item 3).
    #
    # * `max_wall_s = 985.0` — the `truncated` row's whole measured wall at
    #   1.4.3 (985.32 s; 984.33 at 0.1.0). muse states a *12-minute wall-clock
    #   ceiling measured from its first failed attempt*, and at 1.4.3 it words
    #   the same four rounds as "over 16m19s since the first counted provider
    #   request" (0.1.0: "over 12m16s"). This is a policy the CLI enforces on
    #   itself, not a round trip against a stub, which is what makes it
    #   declarable at all (contrast goose, which declares `None`). It was 736
    #   (the 0.1.0 sentence's 12m16s) until 2026-10-08, and that number is a
    #   span *inside* the chain — the ceiling clock does not start until the
    #   first failure, so the opening round sits outside it — not what one
    #   dispatch costs. Declared at 736, rule 4 admitted a second attempt into
    #   the 815 s an 1800 s slot has left after a 985 s chain, a child certain
    #   to be killed part-way through the same chain (review 24, pins #3); at
    #   985 the ladder refuses that retry and says why. The slot that runs is
    #   providers.yaml's `muse.default_timeout`, 1800 s, which holds one whole
    #   chain, so the rich diagnosis is seen; the class's own
    #   `default_timeout` (600) is only the fallback for a config without the
    #   row, and a 600 s slot is refused before the spawn.
    #
    # * `retries_rate_limit = True` — the `rate-limit` row IS the 5xx row's
    #   envelope to two decimal places: muse's ladder does not distinguish a 429
    #   from a 500, and it ran ten attempts over 248 s against a fail-forever
    #   429 with no `Retry-After`. **Read the budget consequence in the right
    #   direction**: declaring this REMOVES the harness's own rate-limit backoff
    #   for muse (§7.5 rule 6(b), `STOP_VENDOR_ALREADY_RETRIED`). A rate-limited
    #   muse slot used to get up to `MAX_RATE_LIMIT_BACKOFFS` further identical
    #   dispatches of a chain the CLI had already run; it now gets none. That is
    #   a SMALLER retry budget, not a larger one — the multiplication rule 6(b)
    #   exists to prevent, not an entitlement to more attempts.
    #
    # `configurable_by` is empty: nothing this adapter emits moves any of the
    # three numbers. `build_command` passes no retry or timeout flag and
    # `get_env` is not overridden, so the ladder above is muse's own, at the
    # configuration this harness actually runs.
    internal_retries = InternalRetryEnvelope(
        max_requests=40,
        max_wall_s=985.0,
        retries_rate_limit=True,
        configurable_by=(),
    )

    #: The build every fixture in ``tests/fixtures/muse/`` was captured from —
    #: the §6 step-5 probe, ``--network none``, ``stub_server.py`` and
    #: ``failserver.py`` both running inside the container, no credential. Ten
    #: of §6.2's twelve rows — plus two extra truncation rows — are raw
    #: ``muse exec --json`` bytes from this build, so it is what the JSONL
    #: envelope shape above is *known* to be true of, not a range to trust.
    #:
    #: ``min_version`` is deliberately left empty rather than pinned to the same
    #: string, and the reason is that this adapter declares no ``version_cmd``:
    #: ``_detect_version`` only compares against a floor when a probe actually
    #: read a version, so a ``min_version`` here would be enforced by nothing
    #: while reading, in every listing, as a gate that exists. Declaring the
    #: probe would take a ``parse_version`` override first — ``muse --version``
    #: prints ``Muse Code 0.1.0 (0.1.0-R708.1)``, two version strings on one
    #: line, and the base parser reads neither of them the way this field
    #: spells it. ``tests/container/cli-versions.lock`` pins the same build.
    #:
    #: **Moved 0.1.0-R708.1 -> 1.4.3-R5018.1 on 2026-10-08**: all twelve rows
    #: re-captured on 1.4.3 by the same rig in the pinned image (``--version``
    #: prints ``Muse Code 1.4.3 (1.4.3-R5018.1)``), with no parser change. The
    #: three payload types this parser reads, the terminal record, the
    #: ``tool.result`` boundary and the 4 x 10 truncation ladder are unchanged.
    #: What moved: 18 requests per call (1 catalog GET, 17 POSTs), no
    #: background reminder fails in a green run any more, stderr now ends a
    #: failure with ``run ended with Failed: <reason>``, a 404 is glossed (``model
    #: `…` does not exist or you lack access``) like the 401 already was, and
    #: the ceiling sentence reports ``over 16m19s since the first counted provider
    #: request`` where 0.1.0 wrote ``over 12m16s``.
    verified_version = "1.4.3-R5018.1"

    #: D6 — muse's shell sandbox is bubblewrap with ``--unshare-net``, and
    #: `build_command` turns it off on every dispatch (``--disable-sandbox``,
    #: see the class docstring). `doctor` therefore runs the bwrap self-test
    #: for this adapter but reports a failure as *bypassed*, never as a check
    #: this adapter fails; `sandbox_probe_command` stays the base ``None``
    #: because there is no sandbox left in the dispatch path to probe, and
    #: ``muse sandbox`` is Windows-only in any case.
    sandbox_mechanism = "bubblewrap"
    sandbox_disabled_by = "--disable-sandbox"

    @property
    def name(self) -> str:
        return "muse"

    @property
    def default_timeout(self) -> int:
        return 600

    def is_available(self) -> bool:
        return shutil.which("muse") is not None

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        # muse exec --json --disable-approval --disable-sandbox --model <model>
        #     [--reasoning-effort <effort>] "<prompt>"
        base_model, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        cmd = [
            "muse", "exec", "--json", "--disable-approval", "--disable-sandbox",
            "--model", base_model,
        ]
        if effort is not None:
            cmd += ["--reasoning-effort", effort]
        cmd.append(prompt)
        return cmd

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """The JSONL stream minus the two payloads that carry our prompt back.

        muse echoes the prompt into a ``prompt`` field on exactly two payload
        types — ``turn.input.user`` (the ``status`` record) and
        ``run.lifecycle.started`` (the ``event`` record) — measured across every
        capture in ``tests/fixtures/muse/``. Today that echo classifies as
        ``None``, which is *one plan word* away from being the harmful case:
        this adapter's ``auth_error_patterns`` already carry ``api error 401``
        and its ``rate_limit_patterns`` carry ``api error 402`` /
        ``billing verification failed``, and both classes are forwarded by
        ``subagent_executor._classify_failed_run`` to fail or back off the whole
        batch. It is also why C1 lands before the auth-pattern widening: a wider
        table on an echoing adapter matches more of *our* wordings, not more of
        the vendor's.

        The reduction drops the ``prompt`` key from those two payloads and
        leaves the records — and every other line — in place, so the sequence
        numbers, the ``run.terminal.*`` record's ``terminal``/``reason``/``text``
        (which is where muse's whole diagnosis lives, including the "your API
        key from META_API_KEY was rejected" gloss and the verbatim ``API error
        404: The model `…` does not exist``) and every ``run.output.delta``
        survive untouched. stderr — muse's ``run ended with Failed`` line — is
        never reduced.
        """
        try:
            if not stdout or '"prompt"' not in stdout:
                return stdout, stderr
            echoing = ("turn.input.user", "run.lifecycle.started")
            lines: List[str] = []
            changed = False
            for line in stdout.split("\n"):
                stripped = line.strip()
                if stripped:
                    try:
                        event = json.loads(stripped)
                    except ValueError:
                        event = None
                    if (
                        isinstance(event, dict)
                        and event.get("payload_type") in echoing
                    ):
                        payload = event.get("payload")
                        if isinstance(payload, dict) and "prompt" in payload:
                            payload.pop("prompt")
                            # Compact separators, because muse's stream is
                            # compact: the default `", "`/`": "` would put bytes
                            # into the line that were never in the capture,
                            # which is the one thing this hook may not do. On a
                            # record with this many keys they also add up — a
                            # short dropped prompt could leave the "reduced"
                            # line LONGER than the original.
                            line = json.dumps(
                                event, ensure_ascii=False, separators=(",", ":")
                            )
                            changed = True
                lines.append(line)
            if not changed:
                return stdout, stderr
            return "\n".join(lines), stderr
        except (AttributeError, TypeError, ValueError):
            return stdout, stderr

    @staticmethod
    def _iter_events(stdout: str) -> Iterator[Dict[str, Any]]:
        """Yield ``(payload_type, payload)``-bearing records of the JSONL stream."""
        for line in stdout.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue
            if isinstance(event, dict) and isinstance(event.get("payload"), dict):
                yield event

    @staticmethod
    def _direct_json(text: str) -> Optional[Dict[str, Any]]:
        """Parse ``text`` as one complete JSON document, or return None."""
        if text.startswith(('[', '{')):
            try:
                return {"success": True, "data": json.loads(text)}
            except json.JSONDecodeError:
                pass
        return None

    def _scan(self, stdout: str) -> Dict[str, Any]:
        """Collect the answer text and terminal state from the event stream.

        ``tail`` holds the deltas emitted after the LAST ``tool.result``, which
        is the closest thing muse gives to "the final assistant message" — see
        parse_output for why that matters.

        The walk is shared by :meth:`parse_output`, :meth:`describe_failure`
        and :meth:`salvage_text`; ``envelope``, ``saw_delta`` and
        ``terminal_text`` are salvage's and nothing else reads them.
        """
        deltas: List[str] = []
        tail: List[str] = []
        terminal: Optional[str] = None
        reason: Optional[str] = None
        terminal_text: Optional[str] = None
        task_failures: List[str] = []
        envelope = False
        saw_delta = False

        for event in self._iter_events(stdout):
            payload_type = event.get("payload_type") or ""
            payload = event["payload"]
            if isinstance(event.get("payload_type"), str):
                envelope = True

            if payload_type == "run.output.delta":
                text = payload.get("text")
                if isinstance(text, str):
                    saw_delta = True
                    deltas.append(text)
                    tail.append(text)
            elif payload_type == "tool.result":
                # A tool call closes the preceding assistant message; anything
                # buffered so far belongs to an earlier turn.
                tail.clear()
            elif payload_type.startswith("run.terminal."):
                terminal = payload.get("terminal")
                if isinstance(payload.get("reason"), str) and payload["reason"]:
                    reason = payload["reason"]
                if isinstance(payload.get("text"), str):
                    terminal_text = payload["text"]
            elif payload_type == "task.lifecycle.failed":
                detail = payload.get("event")
                if isinstance(detail, dict):
                    message = detail.get("reason")
                    if isinstance(message, str) and message:
                        task_failures.append(message)

        return {
            # The terminal record's text is authoritative — the deltas are
            # ephemeral status records that a future build could drop.
            "full": terminal_text if terminal_text is not None else "".join(deltas),
            "tail": "".join(tail),
            "terminal": terminal,
            "reason": reason,
            "task_failures": task_failures,
            "envelope": envelope,
            "saw_delta": saw_delta,
            "terminal_text": terminal_text,
        }

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        """Recover the reason for a non-zero exit from the event stream.

        On a failed run muse writes only "run ended with Failed" to stderr and
        leaves the actual cause in the ``run.terminal.failed`` record on
        stdout. Verified against a live out-of-credits account, which exited 1
        with that stderr and a terminal reason of "API error 402 [...]:
        Billing verification failed. [...] (after 10 provider attempts)".
        """
        scan = self._scan(stdout)
        if scan["reason"]:
            return scan["reason"]
        # No terminal record (killed mid-run, say) — fall back to whatever
        # task-level failures were reported.
        return "; ".join(scan["task_failures"]) or None

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse the JSONL event stream emitted by ``muse exec --json``.

        The terminal record's ``text`` is the concatenation of EVERY assistant
        message in the run, glued with no separator — a run that narrates
        before answering yields "Looks good so far.[{...}]", and one that
        shows a draft yields "Draft: [{...draft...}][{...answer...}]". The
        extractor now takes the LAST balanced structure, i.e. the answer, so
        that shape no longer needs the closing message isolated first — but a
        turn boundary is still what makes an EARLIER turn's text inadmissible
        rather than merely outranked, which is why the tail is isolated below.

        muse publishes no message-boundary event (``run.output.delta`` carries
        token fragments, verified by splitting one message across three SSE
        deltas), but ``tool.result`` reliably separates turns. The deltas after
        the last tool result are therefore tried first, and the full text only
        as a fallback — for single-turn runs the two are identical.

        All of that is now a **committed capture** rather than a description:
        ``tests/fixtures/muse/multi-assistant.stdout.txt`` is raw JSONL from a
        run whose terminal ``text`` reads ``Draft: [{…DRAFT…}][{…S001…}]``.
        Since the extractor took the last-wins rule both routes agree on this
        capture — the whole string and the tail after the last ``tool.result``
        each return the answer — so what the row still exercises is the boundary
        itself, and it is the only capture in the repo that exercises one at
        all, which is why it took a probe-local stub driving a real
        ``read_file`` call to produce (see that directory's README).

        MEASURED 2026-08-19, **FIXED 2026-08-20 (C8)**: a FAILED run whose
        salvaged text happened to parse used to be returned as a success. The
        first branch below fails a non-``completed`` run only ``and not full``,
        so with any text present control fell through to ``_direct_json(tail)``
        and returned before the terminal state was consulted again.
        ``tests/fixtures/muse/truncated-json-answer.stdout.txt`` is the capture:
        exit **1**, ``run.terminal.failed`` reading "model failed after 10
        attempts: stream ended before terminal event", and this method answering
        ``success: True`` with the array. ``llm_client`` was safe by accident (it
        short-circuits on ``returncode != 0`` and never calls this), but
        ``subagent_executor`` was not — it treats the exit code as evidence
        rather than verdict and accepted a schema-valid result from a non-zero
        exit, which is the one way this adapter could hand a fan-out slot a
        fabricated answer. The ``and not full`` conjunct is gone, and the rule
        it leaves behind is **terminal state before salvaged text, in one
        direction only**:

        - ``terminal == "completed"`` — parse, exactly as before;
        - terminal present and NOT ``completed`` — **fail**, whatever text was
          salvaged, carrying muse's own terminal reason as ``error`` and the
          stream as ``raw`` (Lane B's rung split reads ``raw``: text present is
          rung 5 ``unparseable_result``, text absent is rung 4
          ``runner_error``, so the failing branch must never answer
          ``raw: None``);
        - ``terminal is None`` — muse wrote no terminal record at all — parse,
          exactly as before.

        A recorded verdict outranks a guess made from bytes; the *absence* of a
        verdict is not a verdict, which is why the ``None`` half of that
        condition is unchanged and why the clean ``success`` capture still
        parses. The fix is in this adapter and nowhere else:
        ``subagent_executor``'s "exit code is evidence, never the verdict" rule
        is deliberately untouched, because the evidence that condemns this run
        is ``run.terminal.failed`` and its reason sentence — which only this
        adapter parses — not the exit code several CLIs overload.

        Residual limit, now CLOSED: two JSON documents inside the SAME closing
        turn (a draft and an answer with no tool call between them) used to
        resolve to the first, since nothing separates them. The extractor now
        states one rule — the last document wins, at every level — so that shape
        resolves to the ANSWER with no boundary needed (verified against this
        adapter's own ``multi-assistant`` capture: the whole terminal string now
        yields ``id: S001``). What the tail rule below still pins is narrower and
        unchanged: a ``tool.result`` boundary is authoritative rather than
        inferred from document order, so text from an earlier turn is never the
        answer even when it is the only thing that parses. What is left is the
        inverse risk this paragraph used to prefer first-wins for — an answer
        followed by an illustrative snippet — and clause 2 of the rule ("shape
        before position") holds its common form, since a snippet after an array
        answer is usually an object and every array is tried before every
        object. An ARRAY-shaped trailing example would displace the answer; no
        capture in ``tests/fixtures/`` shows that shape, while draft-then-answer
        is captured on this adapter from a real tool loop.
        """
        scan = self._scan(stdout)
        full = scan["full"].strip()
        tail = scan["tail"].strip()

        # Terminal state before salvaged text (C8). No `and not full` here: a
        # recorded non-`completed` terminal fails the run whatever parsed out of
        # the stream, while a MISSING terminal (`None`) still falls through to
        # the parse below. `raw` is the whole stream, never None — Lane B splits
        # rung 5 from rung 4 on exactly that field.
        if scan["terminal"] not in (None, "completed"):
            reason = scan["reason"] or "; ".join(scan["task_failures"])
            error = f"Muse run {scan['terminal']}"
            if reason:
                error = f"{error}: {reason}"
            return {"success": False, "error": error, "raw": stdout, "data": None}

        if not full:
            error = "No output events found in output"
            reason = self.describe_failure(stdout, stderr)
            if reason:
                error = f"Muse reported an error: {reason}"
            return {"success": False, "error": error, "raw": stdout, "data": None}

        # Exact parses first — they are unambiguous — closing message before
        # the whole transcript.
        for candidate in (tail, full):
            if candidate:
                direct = self._direct_json(candidate)
                if direct is not None:
                    return direct

        result: Dict[str, Any] = {}
        for candidate in (tail, full):
            if not candidate:
                continue
            # Try to extract JSON from the text (may be in code blocks)
            result = extract_json_from_text(candidate, prefer_arrays=True)
            if result.get("success"):
                return result

        # Nothing parsed out of the salvaged text of a run that did not reach
        # "completed" — the terminal reason is the real diagnosis, so keep it
        # rather than reporting only "no valid JSON found".
        #
        # C8 made this a BELT, not the braces: since the first branch stopped
        # asking whether text was salvaged, every run with a recorded
        # non-`completed` terminal now returns there carrying the same reason,
        # and this condition can no longer be true. It is kept rather than
        # deleted because it is the reason-preserving rule stated where a reader
        # of the parse path looks for it, and because the only way it comes back
        # to life is somebody reintroducing a carve-out in the branch above —
        # in which case the diagnosis should survive that too. Nothing in
        # `tests/fixtures/muse/` reaches it any more:
        # `truncated-after-deltas`, which did, now fails at the first branch.
        if scan["terminal"] not in (None, "completed") and scan["reason"]:
            result = dict(result)
            result["error"] = "{} (muse run {}: {})".format(
                result.get("error", "Failed to parse response"),
                scan["terminal"], scan["reason"],
            )
        return result

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The closing assistant message's text, for the salvage gate (D4.1/D4.4).

        muse's stdout is an envelope of typed records — the runtime's
        lifecycle, tool calls and their results, reminder observers — and only
        ``run.output.delta`` payloads are the model's words. The answer is the
        text :meth:`parse_output` tries first: ``tail``, the deltas after the
        last ``tool.result`` (:meth:`_scan`). Deltas are token fragments, so a
        run killed mid-answer leaves the answer's first half in ``tail`` — the
        case salvage exists for — and the terminal state is deliberately not
        consulted: ``truncated-json-answer`` exits 1 with ``run.terminal.failed``
        and its deltas still hold a complete array.

        When ``tail`` is empty the last turn wrote nothing. If earlier turns
        did, that is narration before a tool call and is dropped, not used as a
        fallback the way ``parse_output`` falls back to ``full`` (plan D4.2:
        narration can quote an example array). Only a stream with no delta at
        all reads the terminal record's ``text`` — the one source of answer
        text left if a build stops emitting deltas.

        * ``None`` when no line is a muse record (not this adapter's stream);
        * ``""`` when the closing turn holds no text — a verdict, final;
        * otherwise that text.

        Never raises: a failed walk is ``""``, the reading the caller would give
        a raise anyway.
        """
        try:
            scan = self._scan(stdout or "")
            if not scan["envelope"]:
                return None
            if scan["tail"].strip():
                return scan["tail"]
            if scan["saw_delta"]:
                return ""
            return scan["terminal_text"] or ""
        except Exception:  # noqa: BLE001 - the hook must never raise
            return ""
