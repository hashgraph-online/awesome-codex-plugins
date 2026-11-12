"""The one failure classifier (§7.2, §7.1.a): the marker tables,
:func:`classify_streams` and :func:`match_streams`.

It reads one captured run, its two streams and its exit code, and names the
failure: a status from :mod:`utils.retry_ladder`'s vocabulary, a ``CATEGORY_*``
name, or ``None``. Both lanes classify through it, by way of an adapter's
``classify_failure``. The default pattern sets ``LLMProvider`` declares live
here (:data:`AUTH_ERROR_PATTERNS`, :data:`RATE_LIMIT_PATTERNS`), so a caller with
no adapter in hand gets the same verdict as one with an adapter.

**Pure.** It imports no provider module and no ``utils`` module but the status
vocabulary (``utils.retry_ladder``) and the process-cache registry
(``utils.process_state``), both standard-library only;
``tests/test_provider_base_moved_names.py`` keeps it so. ``base`` re-exports
every name here for reading (docs/development/providers.md#the-provider-base-modules).
"""

import re
from dataclasses import dataclass
from typing import Any, Collection, Dict, Optional, Pattern, Tuple

# The status vocabulary is the retry ladder's, never a second copy of it (§7.2).
# The dependency runs one way only: this module may import the ladder, and the
# ladder must stay free of provider imports — it reads an adapter's retry
# envelope *structurally*, through a Protocol, for exactly that reason.
from ..process_state import process_cache
from ..retry_ladder import (
    STATUS_AUTH_FAILED,
    STATUS_CONTEXT_LENGTH_EXCEEDED,
    STATUS_RATE_LIMITED,
    STATUS_RUNNER_ERROR,
    STATUS_SPAWN_FAILED,
    STATUS_TIMEOUT,
)


#: Terms that make a *bare* token a real failure signal rather than a
#: coincidence. A one-word pattern ("429", "unauthorized") is required to occur
#: near one of these — outside its own span — because on its own it appears in
#: places that say nothing about the run: opencode prints per-step costs
#: (``"cost":0.0429``), every runner prints token counts (``14290``), and a
#: review answer quotes the plan and diff under review ("the unauthorized branch
#: returns early").
_ERROR_CONTEXT = re.compile(
    r"http|status|code|error|err\b|response|fail|denied|forbidden|reject|"
    r"invalid|expired|exceeded|missing|quota|retry|throttl|too\s*many|rate|"
    r"limit|credential|login|log\s*in|sign\s*in|api[\s_-]*key|401|403|429|529"
)

#: How far either side of a bare-token match :data:`_ERROR_CONTEXT` is looked for.
_CONTEXT_WINDOW = 48

#: Compiled-pattern cache: the classifier runs on every failed dispatch.
_STREAM_PATTERNS: Dict[str, "re.Pattern[str]"] = process_cache(
    "utils.providers.failure_classifier._STREAM_PATTERNS"
)


def stream_pattern(pattern: str) -> "re.Pattern[str]":
    """Compile one classifier substring into a boundary-aware regex.

    A textual pattern keeps a left word boundary while staying a prefix match on
    the right — "rate limit" must still recognize "rate limits" and
    "rate-limited" — and any run of separators inside the pattern matches any run
    of separators in the stream, so one entry covers ``rate limit``,
    ``rate-limit`` and ``ratelimit`` alike. A numeric pattern (an HTTP status
    code) must additionally stand alone as a token, so ``429`` is not found
    inside ``0.0429`` or ``14290``.

    Patterns are matched against a lowercased haystack, so the compiled regex is
    lowercase and carries no ``IGNORECASE`` flag.
    """
    token = (pattern or "").strip().lower()
    cached = _STREAM_PATTERNS.get(token)
    if cached is not None:
        return cached
    if token.isdigit():
        regex = re.compile(rf"(?<![\w.]){token}(?![\w.])")
    else:
        body = re.sub(r"(?:\\?[ _\-])+", r"[\\s_\\-]*", re.escape(token))
        regex = re.compile(rf"(?<![a-z0-9]){body}")
    _STREAM_PATTERNS[token] = regex
    return regex


def _needs_context(token: str) -> bool:
    """Whether ``token`` is too bare to classify a run on its own.

    A multi-word phrase ("not logged in", "too many requests", "quota_exceeded")
    is specific enough to stand alone; a single token ("429", "unauthorized",
    "overloaded") is not, because it occurs inside numbers and inside the prose a
    runner prints about somebody else's code.
    """
    return re.search(r"[\s_\-]", token) is None


def matches_any(patterns: Collection[str], haystack: str) -> bool:
    """Whether any declared classifier pattern really occurs in ``haystack``.

    This is the whole difference between the executor classifying a run and
    guessing at one: the D3k ladder consults
    :meth:`LLMProvider.classify_failure` for a run with no usable result, and a
    bare ``pattern in haystack`` test moves such a run onto a rung with different
    retry rules than the one it belongs on — ``rate_limited`` is retried *without*
    consuming the retry budget, ``auth_failed`` fails the entire batch.
    """
    for pattern in patterns:
        token = (pattern or "").strip().lower()
        if not token:
            continue
        regex = stream_pattern(token)
        bare = _needs_context(token)
        for match in regex.finditer(haystack):
            if not bare:
                return True
            window = "\n".join((
                haystack[max(0, match.start() - _CONTEXT_WINDOW):match.start()],
                haystack[match.end():match.end() + _CONTEXT_WINDOW],
            ))
            if _ERROR_CONTEXT.search(window):
                return True
    return False


#: ``LLMProvider.auth_error_patterns``' default, and the set
#: :func:`classify_streams` and :func:`match_streams` match when their caller
#: names none. An adapter extends the class attribute, never this.
AUTH_ERROR_PATTERNS: Tuple[str, ...] = (
    "not logged in",
    "please log in",
    "please login",
    "authentication required",
    "unauthorized",
    "invalid api key",
    "api key is missing",
    "no credentials",
    "credentials not found",
    "run `login`",
)


#: ``LLMProvider.rate_limit_patterns``' default, read the same way as
#: :data:`AUTH_ERROR_PATTERNS`.
RATE_LIMIT_PATTERNS: Tuple[str, ...] = (
    "429",
    "rate limit",
    "rate_limit",
    "ratelimit",
    "too many requests",
    "quota exceeded",
    "quota_exceeded",
    "insufficient_quota",
    "overloaded",
)


# ---------------------------------------------------------------------------
# The one failure classifier (§7.2, §7.1.a)
#
# Everything below is *new* data for categories the adapter pattern sets never
# covered. The two declared sets — ``auth_error_patterns`` and
# ``rate_limit_patterns`` — and the matcher above are **not** touched: they were
# audited on 2026-08-16 and measured clean (``stream_pattern`` gives a numeric
# token its own boundaries, and a bare token additionally needs an
# ``_ERROR_CONTEXT`` word within 48 characters), with
# ``tests/test_provider_failure_classification.py::TestClassifyFailure`` pinning it. This section adds
# categories beside them, and then makes every other classifier in the tree call
# this one instead of growing its own.
#
# The new tables are **regexes**, not substrings, because §7.2 asks for regexes
# ("maximum context length is N tokens") and because a regex states its own
# boundaries: ``\bthrottl(?:ed|ing)\b`` needs no context window to be safe,
# whereas the bare token ``throttled`` handed to ``matches_any`` would.
# ---------------------------------------------------------------------------

#: Categories the ladder has no status for. They exist so the ``Reason:`` line a
#: user acts on and the retry decision can be read off the *same* verdict —
#: §7.1.a's seven-branch ``elif`` chain is a lookup on these.
CATEGORY_CONNECTION_ERROR = "connection_error"
CATEGORY_SERVER_ERROR = "server_error"
CATEGORY_INVALID_MODEL = "invalid_model"
CATEGORY_PERMISSION_DENIED = "permission_denied"
#: The runner's *own* OS sandbox could not start (D6). Deliberately the same
#: string as ``retry_ladder.STATUS_SANDBOX_UNAVAILABLE`` — like
#: ``CATEGORY_INVALID_MODEL``, an alias for a word already in the vocabulary —
#: so it reaches the ladder under its own name, at rung 1: a property of the
#: machine, not of the turn, and every sibling on that runner fails identically.
CATEGORY_SANDBOX_UNAVAILABLE = "sandbox_unavailable"

#: §7.2's retryable-code allowlist, shared across both harnesses. Auth is
#: deliberately absent (no retry fixes a logged-out CLI) and so is
#: :data:`STATUS_CONTEXT_LENGTH_EXCEEDED`: until §7.6(a) ships a prompt splitter,
#: re-dispatching an oversized prompt unchanged spends budget to reproduce the
#: same error. Open question 13 owns the splitter; this frozenset owns the fact
#: that nothing may retry it in the meantime.
RETRYABLE_FAILURE_CATEGORIES = frozenset({
    STATUS_RATE_LIMITED,
    STATUS_TIMEOUT,
    CATEGORY_CONNECTION_ERROR,
    CATEGORY_SERVER_ERROR,
})

#: A shell reports "could not execute what you asked for" as 127, on every
#: POSIX shell and through every wrapper script. It is the one launch verdict
#: that needs no text at all.
MISSING_BINARY_EXIT_CODE = 127


def _markers(*patterns: str) -> Tuple["Pattern[str]", ...]:
    """Compile one classifier table. Haystacks are lowercased before matching."""
    return tuple(re.compile(p) for p in patterns)


def _matches_marker(markers: Collection["Pattern[str]"], haystack: str) -> bool:
    return any(marker.search(haystack) for marker in markers)


#: Root-cause launch failures, ordered **before** the auth patterns (§7.2). A
#: sandbox that refused the exec, or a shim that could not find the binary,
#: prints text that reads like a permission or credential problem — and reading
#: it as ``auth_failed`` is expensive twice over, because rung 1 fails the whole
#: batch and because the actual fix (install the CLI, grant the exec) is never
#: mentioned. Each tuple is ``(category, markers)`` and the first match wins.
#:
#: The markers are deliberately specific phrases rather than the bare
#: ``'not found'`` Lane A used: that one called **every** provider's failure
#: "cursor-agent command not found", and it swallowed "model not found" too.
#: bubblewrap's own refusals when it cannot start (D6): whole lines, each
#: anchored at a line start on the exact prefix of one measured refusal, so a
#: line that only mentions bubblewrap is never one. The table is consulted
#: **first** of the launch tuple, because the same lines also say "permission
#: denied" / "operation not permitted" and would otherwise land on
#: ``permission_denied`` — a per-task verdict, where this one is fatal to the
#: batch and names a machine repair (``multi_llm.py doctor``). Read on
#: **stderr only** (:data:`STDERR_LAUNCH_FAILURE_MARKERS`), and only the part
#: of it the adapter's :attr:`LLMProvider.LAUNCH_DIAGNOSTICS` says the CLI
#: wrote: a failed run's stdout is often a model's answer, and an answer or a
#: tool's output that quotes these lines must not fail the batch. A vendor
#: refusal that reaches us only on stdout is therefore a bounded retry (one
#: extra dispatch per lane); see docs/development/providers.md#launch-diagnostics.
#: The haystack is lowercased, so the anchors are multiline and the words
#: lowercase. Any other bubblewrap line is no verdict of its own, only
#: :func:`sandbox_hint`'s pointer at ``doctor`` in the failure message.
SANDBOX_MARKERS = _markers(
    # Stock Ubuntu 24.04 (`kernel.apparmor_restrict_unprivileged_userns=1`, no
    # AppArmor profile granting /usr/bin/bwrap `userns`), under --unshare-net:
    # doctor's `BWRAP_SELF_TEST` and the `codex sandbox` probe
    # (`CodexProvider.sandbox_probe_command`), exit 1.
    r"(?m)^bwrap: loopback: failed rtm_newaddr: ",
    # The same host without --unshare-net (docs/hosts.md).
    r"(?m)^bwrap: setting up uid map: ",
    # Docker's default seccomp profile, codex 0.146.0 in the e2e image
    # (2026-08-20, tests/test_container_live_provider.py INNER_USERNS_HISTORY).
    r"(?m)^bwrap: no permissions to create a new namespace\b",
)

#: A non-zero exit from a ``sandbox_probe_command`` that says nothing about the
#: sandbox: the CLI did not understand the probe. Measured on codex — a build
#: without the ``sandbox`` subcommand reads the argv as an interactive prompt
#: and dies on ``Error: stdin is not a terminal``; clap's own refusals are the
#: ``unrecognized subcommand`` / ``unexpected argument`` lines. The preflight
#: records these ``unknown`` and dispatches, exactly like a probe that timed
#: out: refusing a runner because it is *older* than the probe would turn a
#: diagnostic into a version gate the adapter never declared.
SANDBOX_PROBE_INCONCLUSIVE_MARKERS = _markers(
    r"unrecognized subcommand",
    r"unknown subcommand",
    r"unexpected argument",
    r"stdin is not a terminal",
)


def sandbox_probe_inconclusive(text: str) -> bool:
    """Whether a failed sandbox probe's output says the CLI did not run it."""
    return _matches_marker(SANDBOX_PROBE_INCONCLUSIVE_MARKERS, (text or "").lower())


#: A bubblewrap line in any wording: ``bwrap: `` opening a line or a word of
#: it (behind a log prefix, or a path to the binary). Never a verdict: only
#: :data:`SANDBOX_MARKERS`' measured refusals fail the batch.
SANDBOX_HINT_MARKER = re.compile(r"(?im)(?<![\w.-])bwrap: [^\n]*")

#: Longest bubblewrap line :func:`sandbox_hint` quotes.
_SANDBOX_HINT_CHARS = 200


def sandbox_hint(launch_stderr: str) -> Optional[str]:
    """A sentence pointing at ``multi_llm.py doctor`` when stderr carries a
    bubblewrap line, else ``None``.

    For the failure message only, never the verdict: a bubblewrap line that
    is none of :data:`SANDBOX_MARKERS`' measured refusals (another wording, a
    log prefix ahead of it) keeps whatever the tables decided, and the
    message still says the runner's own sandbox may not have started.
    ``launch_stderr`` is the part of stderr the adapter's CLI wrote
    (:meth:`LLMProvider.launch_diagnostics`). The caller redacts.
    See docs/development/providers.md#launch-diagnostics.
    """
    found = SANDBOX_HINT_MARKER.search(launch_stderr or "")
    if found is None:
        return None
    line = found.group(0).strip()[:_SANDBOX_HINT_CHARS]
    return (
        f"stderr carries a bubblewrap line ({line!r}), so the runner's own "
        f"sandbox may not have started; `multi_llm.py doctor` checks it"
    )


LAUNCH_FAILURE_MARKERS: Tuple[Tuple[str, Tuple["Pattern[str]", ...]], ...] = (
    # These two rows are read on stderr only: :data:`STDERR_LAUNCH_FAILURE_MARKERS`
    # below. They stay here for their place in the order (the sandbox first,
    # then a launch refusal, both before a permission denial).
    (CATEGORY_SANDBOX_UNAVAILABLE, ()),
    (STATUS_SPAWN_FAILED, ()),
    (CATEGORY_PERMISSION_DENIED, _markers(
        r"permission denied",
        r"operation not permitted",
        r"\beacces\b",
        r"\beperm\b",
    )),
)

#: ``spawn_failed`` phrases a CLI writes about **its own** invocation: a
#: refused argv or config, read on stderr. Each one is batch-fatal wherever it
#: appears there. omp 18.2.2, both measured on stderr, both exit 1 at **zero
#: requests** because the CLI validates its own argv and its config overlay
#: before it resolves a model: a rejected ``--tools`` name raises
#: ``CliUsageError``, and a ``--config`` path that does not resolve is
#: ``error: Config overlay not found: <abs path>`` in 0.13 s. Neither is a
#: failed *spawn* in the literal sense (the binary ran), but the disposition is
#: the one this rung exists for: a property of the install, identical for every
#: sibling slot on that runner, and no retry can fix it. The alternative was
#: ``None``, which offers a transport retry of a run that cannot change its
#: mind. omp 18.8.3 (measured 2026-10-08, tests/fixtures/omp/invalid-tool)
#: refuses a bad ``--tools`` name, exit 2, with ``Error: Unknown tool in
#: --tools: bogus.`` (``Unknown tools in --tools: a, b.`` for two) opening its
#: stderr, no Bun trace and no ``CliUsageError`` word, so that row is anchored
#: at a line start (review 24, pins #5). Lowercase, like every other row here:
#: :func:`_markers` compiles without ``re.I`` and :func:`classify_streams`
#: lowercases the haystack first.
CLI_REFUSAL_MARKERS = _markers(
    r"\bcliusageerror\b",
    r"config overlay not found",
    r"(?m)^error: unknown tools? in --tools\b",
)

#: ``spawn_failed`` phrases a shell, ``env``, cmd.exe or the kernel writes
#: about **whichever** command it could not run: the CLI itself, or a hook, a
#: wrapper or an MCP server the CLI started, whose refusal lands on the same
#: stderr. :func:`classify_streams` reads them as ``spawn_failed`` like the
#: rows above; both lanes keep that verdict only when the run made no progress
#: (:func:`launch_refusal`,
#: docs/development/delegation.md#read-and-analyze-executor).
SHELL_REFUSAL_MARKERS = _markers(
    r"command not found",
    r"executable file not found",
    r"\bbinary not found\b",
    r"not found in \$?path\b",
    r"is not recognized as an internal or external command",
    r"cannot execute binary file",
    r"\bexec format error\b",
)

#: Launch-failure rows read on **stderr only**, consulted in the place of
#: :data:`LAUNCH_FAILURE_MARKERS`' row of the same category. A phrase a model's
#: answer can quote does not belong in the shared haystack: rung 1 fails the
#: whole batch, and a failed run's stdout is often that answer (a reviewer
#: reading this repo's own omp fixtures quotes the ``--tools`` refusal).
STDERR_LAUNCH_FAILURE_MARKERS: Dict[str, Tuple["Pattern[str]", ...]] = {
    # Batch-fatal like ``spawn_failed`` below, for the same reason
    # (:data:`SANDBOX_MARKERS`).
    CATEGORY_SANDBOX_UNAVAILABLE: SANDBOX_MARKERS,
    # **Every ``spawn_failed`` marker is read here, on stderr, and nowhere
    # else.** The verdict fails the executor's whole batch, so it must come
    # from the launcher or the CLI's own refusal, never from a model's answer
    # or a tool's output the CLI relays on stdout ("command not found" in a
    # review of a plan, a shell tool's ``npx: command not found``), or on
    # stderr (:attr:`LLMProvider.LAUNCH_DIAGNOSTICS`). A shell,
    # ``env`` and cmd.exe all write their refusal on stderr; exit 127 needs no
    # text at all (:data:`MISSING_BINARY_EXIT_CODE`), and an adapter whose CLI
    # refuses on stdout says so in its own ``classify_failure`` (vibe's
    # config refusal, read at the start of stdout). The CLI's own refusals
    # come first, so :func:`match_streams` names one of them when both appear.
    STATUS_SPAWN_FAILED: CLI_REFUSAL_MARKERS + SHELL_REFUSAL_MARKERS,
}

#: Where an adapter's launch diagnostics live: the values of
#: :attr:`LLMProvider.LAUNCH_DIAGNOSTICS`, which decide what text the two
#: batch-fatal rows of :data:`STDERR_LAUNCH_FAILURE_MARKERS` may read.
#: ``stderr``: everything there was written by the CLI, its launcher or the OS.
#: ``none``: stderr also relays a model's or a tool's words, on lines that
#: cannot be told apart from the CLI's own, so no batch-fatal verdict is read
#: from text at all (exit 127 still is) and the run keeps its bounded retry.
#: See docs/development/providers.md#launch-diagnostics.
LAUNCH_DIAGNOSTICS_STDERR = "stderr"
LAUNCH_DIAGNOSTICS_NONE = "none"
LAUNCH_DIAGNOSTICS_VALUES = frozenset({LAUNCH_DIAGNOSTICS_STDERR, LAUNCH_DIAGNOSTICS_NONE})

#: Per-vendor context-overflow shapes (§7.2). These are the *only* thing that
#: may produce :data:`STATUS_CONTEXT_LENGTH_EXCEEDED`, because that status is
#: terminal: a false positive fails a slot that a retry would have completed.
#: Lane A's ``'context' in str(error)`` matched ``context_mode``, "in this
#: context" and any prose quoting a plan's Context section; every regex here
#: carries the numbers or the verb that make it a real overflow report.
CONTEXT_OVERFLOW_MARKERS = _markers(
    # OpenAI: "This model's maximum context length is 128000 tokens. However,
    # your messages resulted in 214537 tokens."
    r"maximum context length",
    r"\bcontext[_ ]length[_ ]exceeded\b",
    r"reduce the length of the messages",
    # Anthropic: "prompt is too long: 248113 tokens > 200000 maximum"
    r"prompt is too long",
    # Gemini: "The input token count (1093122) exceeds the maximum number of
    # tokens allowed (1048576)."
    r"input token count\s*\(?\d+\)?\s*exceeds",
    # The shapes several gateways normalise the three above onto. `effective`
    # is goose 1.53.0's own compaction report (tests/fixtures/goose/
    # context-overflow, measured 2026-10-08): "Failed to compact: the base
    # prompt … exceeds the model's effective context window …", which goose
    # writes as a text part with no error `kind`, so this row is what reaches
    # it. One optional word, so no new prose shape matches.
    r"exceeds the (?:model'?s )?(?:maximum |effective )?context (?:window|length)",
    r"context window (?:of \d+ tokens )?exceeded",
    r"\btoo many tokens\b",
    # Mistral Vibe, measured at 2.24.1: "The conversation context exceeds the
    # model's maximum limit. Use /rewind ...". The row above does not reach it --
    # vibe puts the noun first and calls the bound a "limit" rather than a
    # "window" or a "length" -- and without this the run classifies as
    # transport-shaped and burns the executor's whole bounded-retry path on a
    # condition no retry can fix. "conversation context" is what keeps it off
    # prose: an answer discussing a plan's Context section does not say it.
    r"conversation context exceeds",
    # aider, measured at 0.86.2 on the 2026-08-19 fixture capture: it SWALLOWS
    # litellm's ContextWindowExceededError and prints its own help instead, so
    # not one marker above appears anywhere in the run --
    #     "Model openai/stub-model has hit a token limit!"
    #     "Input tokens: ~103 of 0 -- possibly exhausted context window!"
    # The upstream 400's wording never reaches stdout at all. Without these two
    # the row classified as None, i.e. transport-shaped, and the executor spent
    # its whole bounded-retry budget on the one condition §7.2 calls terminal.
    # Both phrasings are specific enough to stay off prose: an answer discussing
    # token budgets does not say "has hit a token limit" or "exhausted context
    # window", and `_markers` anchors on the error context regardless.
    r"hit a token limit",
    r"exhausted context window",
)

#: Rate-limit shapes the adapters' declared English set does not carry, kept
#: here rather than added to it: a bare ``throttled`` handed to
#: :func:`matches_any` would need an ``_ERROR_CONTEXT`` word within 48
#: characters, and the measured phrasing ("Request was throttled") has none. A
#: regex states its own boundary and needs no window — which is why this is a
#: separate table and not an edit to the audited-clean adapter set.
SHARED_RATE_LIMIT_MARKERS = _markers(
    r"\bthrottl(?:ed|ing)\b",
    r"\bquota[ _-]?limit\b",
    r"\busage limit (?:reached|exceeded)\b",
    # gRPC / Connect-RPC status 8, ``RESOURCE_EXHAUSTED``: "some resource has
    # been exhausted, perhaps a per-user quota". cursor-agent speaks Connect-RPC
    # to its backend and relays the code by name. Measured 2026-09-17 on
    # ``cursor-agent:kimi-k3-high``: three ``Connection lost, reconnecting to
    # https://agentn.global.api5.cursor.sh (attempt N)...`` lines and then
    # ``RetriableError: [resource_exhausted] Error`` on stderr, exit 1, zero
    # bytes on stdout, 23.7 s — and no table above matched a word of it, so the
    # slot was recorded as a bare "exited with code 1" (its ``Connection lost``
    # is not a ``CONNECTION_ERROR_MARKERS`` shape either). The CLI names the
    # error retriable itself; this is the rung that retries.
    r"\bresource[_ ]exhausted\b",
)

#: A wall-clock cutoff, wherever it was imposed. Checked before the connection
#: table on purpose: "connection timed out" is a timeout, and
#: ``validation.py``'s persisted vocabulary has always classified it that way.
TIMEOUT_MARKERS = _markers(
    r"\btimed out\b",
    r"\btime[ _-]?out\b",
    r"deadline exceeded",
    r"\betimedout\b",
)

CONNECTION_ERROR_MARKERS = _markers(
    # **Separable on purpose — this row's widening plus its two fixture re-pins
    # are the whole change, and they land as their own commit**, not folded into
    # the adapter work that found them. Its file list is this row,
    # ``tests/fixtures/cline/manifest.yaml``'s ``zero-body`` row (with the
    # matching item 4 of ``tests/fixtures/cline/README.md``) and
    # ``tests/fixtures/omp/manifest.yaml``'s ``empty`` row — no adapter module,
    # and no other provider's verdict (``"connection was"`` greps to those two
    # fixture trees and this line only; the whole grader run confirms it). It is
    # ``plans/add-omp-provider.md``'s follow-up item 1, deferred there for
    # exactly this reason: re-pinning a committed verdict belongs to whoever
    # reviews that provider, so it is put where they can read it on its own
    # terms. If it is ever squashed into a larger commit, that commit's message
    # names the cline re-pin, because the moved verdict — not the regex — is the
    # part a reviewer has to agree with.
    #
    # ``(?:was )?`` is one word wide, and it is there because two adapters emit
    # the SAME Bun/undici sentence for a server that accepted the request and
    # then closed the socket after ZERO body bytes — "The socket connection was
    # closed unexpectedly …" — which the unwidened row missed for the single
    # reason that it says "connection **was** closed". cline's committed
    # `zero-body` row carries it on stderr with `(ECONNRESET)` appended (exit 1,
    # 3 requests over 7.85 s); omp's `empty` row carries it as a terminal
    # `stopReason: "error"` with **no** `errorStatus` (exit 1, 21 requests over
    # 31.9 s). A dropped socket is exactly what this row means, so the widening
    # is a better reading of the same bytes rather than a behaviour change in
    # either CLI. Taken 2026-09-18, with both fixture manifests re-pinned in the
    # same change: cline `runner_error` → `connection_error` (it had been
    # falling through to `exit_zero_markers`, the rung below this one) and omp
    # `None` → `connection_error`.
    #
    # Measured on those same bytes, what moves downstream is the `Reason:` line
    # — "the runner reported a failure" and "Unknown (see tail output below)"
    # both become "Connection/network error" — and, for omp alone, Lane A's
    # retry decision. Lane A then classified its own `"<cli> exited with code
    # N: <describe_failure>"` string rather than the streams: omp's
    # `describe_failure` quotes the sentence into it, so that slot went from
    # `None` ("never retried") to one transport retry, while cline declares no
    # `describe_failure` at all, so its Lane A string stayed the bare exit line.
    # A non-zero exit now carries the adapter's own verdict to Lane A's ladder
    # (docs/development/delegation.md#read-and-analyze-executor). Lane B is unmoved
    # for both: its re-classification hook only upgrades a slot to auth, rate
    # limit, invalid model or sandbox, and `connection_error` is none of those.
    r"connection (?:was )?(?:refused|reset|closed|aborted|error|failed)",
    r"could not connect",
    r"unable to connect",
    r"failed to connect",
    r"network is unreachable",
    r"no route to host",
    r"temporary failure in name resolution",
    r"name or service not known",
    r"\bgetaddrinfo\b",
    r"\becconnrefused\b",
    r"\benotfound\b",
    r"\bdns\b.*\bfail",
)

SERVER_ERROR_MARKERS = _markers(
    r"\b5\d{2}\b\s*(?:internal|server|bad gateway|service|gateway)",
    r"internal server error",
    r"service unavailable",
    r"bad gateway",
    r"gateway time",
    r"\bupstream error\b",
    r"\bapi error\b",
    r"\bserver error\b",
    # OpenAI's 500 sentence, "The server had an error while processing your
    # request. Sorry about that!", relayed verbatim by kilocode, kimi, opencode,
    # gemini, cline, aider and pi (the `server-error` rows of
    # tests/fixtures/<provider>/manifest.yaml, failserver `--mode 500`). None of
    # the rows above reads it: it never says "server error" or a status beside
    # one. The whole clause, so only that sentence matches.
    r"\bserver had an error while processing your request\b",
    # codex's own gloss of the same 500, which it prints instead of the vendor
    # sentence (tests/fixtures/codex/rows/stdout-error, codex 0.167.0): "We’re
    # currently experiencing high demand, which may cause temporary errors."
    # Read from "currently" on, so either apostrophe matches.
    r"\bcurrently experiencing high demand, which may cause temporary errors\b",
)

#: "The model you named does not exist / is not available to this account."
#: Its own category because the fix is a config edit, never a retry.
INVALID_MODEL_MARKERS = _markers(
    r"model not found",
    r"\bmodel_not_found\b",
    r"invalid model",
    r"unknown model",
    r"\bmodel .{0,40}(?:does not exist|is not available)",
    r"unsupported model",
    # omp 18.2.2, measured pre-flight against its own local catalog:
    # `Model "stub/nonexistent" not found` — exit 1, zero bytes on stdout, zero
    # requests. The existing `model not found` row does not reach it because the
    # quoted selector sits between the two words, and `\bmodel .{0,40}…` wants a
    # different verb. Written with the quotes optional and the gap bounded, so
    # the row is the shape ("model <name> not found") rather than one vendor's
    # punctuation — a cost line or a token count cannot satisfy it.
    r"\bmodel [\"'`]?[\w./:-]{1,60}[\"'`]? not found",
)


def classify_streams(
    stdout: str,
    stderr: str,
    exit_code: int = 0,
    *,
    auth_patterns: Optional[Collection[str]] = None,
    rate_limit_patterns: Optional[Collection[str]] = None,
    exit_zero_markers: Collection["Pattern[str]"] = (),
    launch_stderr: Optional[str] = None,
) -> Optional[str]:
    """Classify one captured run. **The** implementation, for both lanes (§7.2).

    Returns a status from :mod:`utils.retry_ladder`'s vocabulary, one of the
    ``CATEGORY_*`` names above, or ``None`` for "nothing recognized" — which the
    caller must read as *transport-shaped*, never as "fine".

    The order is the whole design, and each step earns its place:

    1. ``exit_code == 127`` — the shell's own "I could not run that".
    2. :data:`LAUNCH_FAILURE_MARKERS` — root cause **before** auth (§7.2), since
       a refused exec prints text that reads like a credential problem. Its
       two batch-fatal rows (a sandbox that cannot start, a launch refusal)
       read stderr alone (:data:`STDERR_LAUNCH_FAILURE_MARKERS`), or
       ``launch_stderr`` when given: the part of stderr the adapter's CLI
       wrote (:meth:`LLMProvider.launch_diagnostics`).
    3. :data:`CONTEXT_OVERFLOW_MARKERS` — terminal and unambiguous, and it must
       not be laundered into a retryable category by a later table.
    4. auth, then rate limit — the existing order, pinned by
       ``TestClassifyFailure::test_auth_wins_over_a_rate_limit_in_the_same_stream``:
       misreading a logged-out CLI as a rate limit retries what cannot be fixed.
    5. timeout, connection, **invalid model, then server** — the rest of the
       allowlist. Invalid-model is consulted **before** server-error, and the
       pair is the one step of this ladder that did not earn its original
       order (C2). ``\\bapi error\\b`` sits in :data:`SERVER_ERROR_MARKERS`,
       so a 404 that correctly *names the model* used to land on
       ``server_error`` — a **retryable** category — and burn the retry budget
       on a terminal condition. A model-named 404 is strictly more specific
       than "api error", so the specific table is asked first. Measured on
       ``claude-code``, ``grok``, ``muse`` and ``vibe``; pinned by
       ``TestClassifyLadderOrder``.
    6. the adapter's own exit-0 marker, last: it says only "this run failed",
       so anything more specific must have had its chance first.

    ``auth_patterns``/``rate_limit_patterns`` default to :class:`LLMProvider`'s
    declared sets, which is what lets a caller with no adapter in hand — Lane A's
    error-line fallback — get the same verdict as one with an adapter. Both are matched through :func:`matches_any`, never as raw
    substrings.
    """
    haystack = f"{stdout or ''}\n{stderr or ''}".lower()

    if exit_code == MISSING_BINARY_EXIT_CODE:
        return STATUS_SPAWN_FAILED

    if not haystack.strip():
        return None

    launch_text = stderr if launch_stderr is None else launch_stderr
    stderr_lower = (launch_text or "").lower()
    for category, markers in LAUNCH_FAILURE_MARKERS:
        if _matches_marker(markers, haystack) or _matches_marker(
            STDERR_LAUNCH_FAILURE_MARKERS.get(category, ()), stderr_lower
        ):
            return category

    if _matches_marker(CONTEXT_OVERFLOW_MARKERS, haystack):
        return STATUS_CONTEXT_LENGTH_EXCEEDED

    auth = (
        AUTH_ERROR_PATTERNS if auth_patterns is None else auth_patterns
    )
    if matches_any(auth, haystack):
        return STATUS_AUTH_FAILED

    rate = (
        RATE_LIMIT_PATTERNS
        if rate_limit_patterns is None
        else rate_limit_patterns
    )
    if matches_any(rate, haystack) or _matches_marker(
        SHARED_RATE_LIMIT_MARKERS, haystack
    ):
        return STATUS_RATE_LIMITED

    if _matches_marker(TIMEOUT_MARKERS, haystack):
        return STATUS_TIMEOUT
    if _matches_marker(CONNECTION_ERROR_MARKERS, haystack):
        return CATEGORY_CONNECTION_ERROR
    if _matches_marker(INVALID_MODEL_MARKERS, haystack):
        return CATEGORY_INVALID_MODEL
    if _matches_marker(SERVER_ERROR_MARKERS, haystack):
        return CATEGORY_SERVER_ERROR

    if _matches_marker(exit_zero_markers, haystack):
        # The exit code carried no verdict (goose, aider, cursor-agent and cline
        # all exit 0 on a provider failure), and the adapter's own marker is the
        # only thing that says this run failed at all.
        return STATUS_RUNNER_ERROR

    return None


@dataclass(frozen=True)
class StreamMatch:
    """Where :func:`match_streams` found the text that decided a verdict.

    ``channel`` is ``"stdout"`` or ``"stderr"`` and ``offset`` indexes that
    channel's own **lowered** text (never the joined haystack). All three are
    ``None`` for the two steps that decide without a pattern: exit 127 and the
    adapter's ``exit_zero_markers``.
    """

    status: str
    pattern: Optional[str] = None
    channel: Optional[str] = None
    offset: Optional[int] = None


def _first_pattern_match(
    patterns: Collection[str], haystack: str
) -> Optional[Tuple[str, int]]:
    """:func:`matches_any`'s walk, returning the pattern and offset it accepted.

    The same order, the same boundary regex and the same bare-token context
    rule; only the return value differs, so the two cannot disagree about
    *whether* a haystack matches.
    """
    for pattern in patterns:
        token = (pattern or "").strip().lower()
        if not token:
            continue
        regex = stream_pattern(token)
        bare = _needs_context(token)
        for match in regex.finditer(haystack):
            if not bare:
                return token, match.start()
            window = "\n".join((
                haystack[max(0, match.start() - _CONTEXT_WINDOW):match.start()],
                haystack[match.end():match.end() + _CONTEXT_WINDOW],
            ))
            if _ERROR_CONTEXT.search(window):
                return token, match.start()
    return None


def _first_marker_match(
    markers: Collection["Pattern[str]"], haystack: str
) -> Optional[Tuple[str, int]]:
    """:func:`_matches_marker`'s walk, returning the regex source and offset."""
    for marker in markers:
        found = marker.search(haystack)
        if found:
            return marker.pattern, found.start()
    return None


def match_streams(
    stdout: str,
    stderr: str,
    exit_code: int = 0,
    *,
    auth_patterns: Optional[Collection[str]] = None,
    rate_limit_patterns: Optional[Collection[str]] = None,
    exit_zero_markers: Collection["Pattern[str]"] = (),
    launch_stderr: Optional[str] = None,
) -> Optional[StreamMatch]:
    """:func:`classify_streams`'s verdict **plus where it matched**. Quote-only.

    Additive beside :func:`classify_streams`, which is untouched: the same
    parameters, the same steps in the same order, and ``match.status`` always
    equals what :func:`classify_streams` returns for the same arguments
    (``tests/test_provider_failure_classification.py::TestMatchStreams`` pins it over every
    ``classify_streams`` case in the suite). What it adds is the pattern that
    fired and its position, so ``attempt_classifier._classify_failed_run`` can
    quote the text that actually decided a verdict instead of a stream tail
    that may not contain it (the b38de8bb run quoted a stderr line with no
    rate limit in it).

    **Nothing classifies through this.** Not Lane A's error-line fallback,
    not any adapter's ``classify_failure`` — the
    verdict is always :func:`classify_streams`' (through
    :meth:`LLMProvider.classify_failure`), and this is re-run afterwards for
    the quote alone. Like :func:`classify_streams` it is adapter-free: it never
    applies :meth:`LLMProvider.vendor_text`; the caller hands it text that is
    already reduced.

    ``offset`` is into the matched channel's own lowered text. The joined
    haystack is ``stdout + "\\n" + stderr``, so an offset below
    ``len(stdout)`` is on stdout and anything past the joiner is rebased onto
    stderr.
    """
    out_lower = (stdout or "").lower()
    haystack = f"{stdout or ''}\n{stderr or ''}".lower()

    if exit_code == MISSING_BINARY_EXIT_CODE:
        return StreamMatch(STATUS_SPAWN_FAILED)

    if not haystack.strip():
        return None

    def _found(status: str, hit: Tuple[str, int]) -> StreamMatch:
        pattern, offset = hit
        if offset < len(out_lower):
            return StreamMatch(status, pattern, "stdout", offset)
        return StreamMatch(
            status, pattern, "stderr", max(0, offset - len(out_lower) - 1)
        )

    # `launch_stderr` blanks, never removes (:meth:`LLMProvider.launch_diagnostics`),
    # so an offset into it is an offset into stderr.
    launch_text = stderr if launch_stderr is None else launch_stderr
    err_lower = (launch_text or "").lower()
    for category, markers in LAUNCH_FAILURE_MARKERS:
        hit = _first_marker_match(markers, haystack)
        if hit is not None:
            return _found(category, hit)
        hit = _first_marker_match(
            STDERR_LAUNCH_FAILURE_MARKERS.get(category, ()), err_lower
        )
        if hit is not None:
            return StreamMatch(category, hit[0], "stderr", hit[1])

    hit = _first_marker_match(CONTEXT_OVERFLOW_MARKERS, haystack)
    if hit is not None:
        return _found(STATUS_CONTEXT_LENGTH_EXCEEDED, hit)

    auth = (
        AUTH_ERROR_PATTERNS if auth_patterns is None else auth_patterns
    )
    hit = _first_pattern_match(auth, haystack)
    if hit is not None:
        return _found(STATUS_AUTH_FAILED, hit)

    rate = (
        RATE_LIMIT_PATTERNS
        if rate_limit_patterns is None
        else rate_limit_patterns
    )
    hit = _first_pattern_match(rate, haystack) or _first_marker_match(
        SHARED_RATE_LIMIT_MARKERS, haystack
    )
    if hit is not None:
        return _found(STATUS_RATE_LIMITED, hit)

    for status, markers in (
        (STATUS_TIMEOUT, TIMEOUT_MARKERS),
        (CATEGORY_CONNECTION_ERROR, CONNECTION_ERROR_MARKERS),
        (CATEGORY_INVALID_MODEL, INVALID_MODEL_MARKERS),
        (CATEGORY_SERVER_ERROR, SERVER_ERROR_MARKERS),
    ):
        hit = _first_marker_match(markers, haystack)
        if hit is not None:
            return _found(status, hit)

    if _matches_marker(exit_zero_markers, haystack):
        return StreamMatch(STATUS_RUNNER_ERROR)

    return None


def exit_zero_failure_category(
    provider: Any, stdout: Optional[str], stderr: Optional[str]
) -> Tuple[bool, Optional[str]]:
    """The adapter's verdict on an exit 0 that left no answer, as
    ``(classified, category)``. **The one gate both lanes read** (the fan-out's
    ``provider_outcome``, the executor's ``_classify_failed_run``).

    ``(False, None)`` unless the adapter declares
    :attr:`LLMProvider.EXIT0_CLASSIFIABLE` ``True``: its answer cannot be told
    apart from its diagnostics, so the run is left unclassified rather than
    read off the model's prose. Otherwise :meth:`LLMProvider.classify_exit_zero`,
    best-effort: an adapter that raises, or answers something other than a
    category name or ``None``, is ``(False, None)`` too. ``None`` from it is a
    verdict, ``(True, None)``. ``spawn_failed`` reads as ``None``: a CLI that
    refused its own invocation never exits 0, so the words came from a tool.
    See docs/development/delegation.md#read-and-analyze-executor.
    """
    if getattr(provider, "EXIT0_CLASSIFIABLE", False) is not True:
        return False, None
    try:
        category = provider.classify_exit_zero(stdout or "", stderr or "")
    except Exception:  # noqa: BLE001 - classification must not break a failure path
        return False, None
    if category is not None and not isinstance(category, str):
        return False, None
    if category == STATUS_SPAWN_FAILED:
        return True, None
    return True, category


def launch_refusal(
    provider: Any, stdout: Optional[str], stderr: Optional[str], exit_code: int
) -> Tuple[Optional[str], str]:
    """The verdict on a non-zero exit the adapter read as ``spawn_failed``,
    as ``(category, the stderr it was read from)``. **Both lanes ask it**
    (the fan-out's ``provider_outcome``, the executor's ``_classify_failed_run``).

    ``spawn_failed`` stops the slot and fails the executor's batch, so it
    stands for exit 127, for an adapter's own refusal shape (vibe's config
    refusal on stdout) and for a CLI's own refusal line
    (:data:`CLI_REFUSAL_MARKERS`). A shell's phrase
    (:data:`SHELL_REFUSAL_MARKERS`) names whichever command could not run,
    which may be a hook's, a wrapper's or an MCP server's on the same stderr;
    it stands only when the run made no progress: nothing on stdout, and
    nothing else the adapter recognises on stderr. Otherwise the verdict is
    the adapter's own reading of the same capture with only the shell
    phrases blanked (spaces of their length, so a 401 or a 429 on the same
    line still decides), and ``None`` (one transport retry) when that is
    nothing. The stderr returned is what the verdict was read from, for its
    quote. See docs/development/delegation.md#read-and-analyze-executor.
    """
    stdout, stderr = stdout or "", stderr or ""
    if exit_code == MISSING_BINARY_EXIT_CODE:
        return STATUS_SPAWN_FAILED, stderr
    # The raw stderr's launch part: `vendor_text` only ever removes from
    # stderr, so a phrase the verdict read there is here too.
    try:
        launch_text = provider.launch_diagnostics(stderr).lower()
    except Exception:  # noqa: BLE001 - the adapter's verdict stands
        return STATUS_SPAWN_FAILED, stderr
    if _matches_marker(CLI_REFUSAL_MARKERS, launch_text):
        return STATUS_SPAWN_FAILED, stderr
    if not _matches_marker(SHELL_REFUSAL_MARKERS, launch_text):
        return STATUS_SPAWN_FAILED, stderr
    # Blank the phrases, never the text around them. The tables match a
    # lowered haystack, so the same rows are applied here without case.
    rest_err = stderr
    for marker in SHELL_REFUSAL_MARKERS:
        rest_err = re.compile(marker.pattern, marker.flags | re.IGNORECASE).sub(
            lambda found: " " * len(found.group(0)), rest_err
        )
    if _matches_marker(SHELL_REFUSAL_MARKERS, rest_err.lower()):
        return STATUS_SPAWN_FAILED, stderr
    try:
        rest = provider.classify_failure(stdout, rest_err, exit_code)
    except Exception:  # noqa: BLE001 - classification must not raise
        rest = None
    if rest == STATUS_SPAWN_FAILED or (rest is not None and not isinstance(rest, str)):
        return STATUS_SPAWN_FAILED, stderr
    # Anything the CLI wrote on stdout, colour included, is progress.
    if stdout.strip() or rest is not None:
        return rest, rest_err
    return STATUS_SPAWN_FAILED, stderr


def context_length_message(model: str) -> str:
    """The §7.6(a) sentence a slot fails with, recorded verbatim in the report.

    Not a placeholder for the splitter: open question 13 owns that design, and
    until it is answered the shipping behaviour is to classify the condition,
    name it, and fail the slot with the two remedies a human can actually apply.
    """
    return (
        f"the prompt exceeded {model or 'this model'}'s context window; narrow "
        f"the plan/diff scope or configure a larger-context model"
    )
