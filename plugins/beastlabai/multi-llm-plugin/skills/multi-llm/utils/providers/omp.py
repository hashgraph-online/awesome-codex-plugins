"""oh-my-pi (``omp``) CLI provider implementation.

omp is argv-compatible with ``pi`` on the one-shot **text** surface — the exact
argv the pi adapter renders, with ``pi`` replaced by ``omp``, returns the same
answer — but this adapter does not run that surface. It renders ``--mode json``
and reads the JSONL event stream, because text mode loses every reason omp was
added: per-record usage, a clean stdout/stderr split, the in-stream error
taxonomy, the tool-approval denials and the exit-0 abort. In text mode the
exit-0 abort of :func:`_max_time_value`'s deadline is byte-identical to a silent
400; in json mode it is a ``toolUse``-final stream this parser names.

The measured surface this file is written against is
``plans/add-omp-provider.md`` §1, at omp 18.2.2. Two things there are load
bearing enough to restate:

* **The stream's shape, not the exit code, decides success.** ``--max-time``
  firing inside a tool call exits **0** with an unfinished stream, and the
  empty-stop retry gives up after four cycles at exit **0** — four assistant
  ``message_end``s carrying ``stopReason: "stop"`` and empty content, then an
  ``auto_retry_end`` naming the reason. :meth:`parse_output` reads the terminal
  assistant ``message_end`` and never the return code, which it is not given
  anyway.
* **A denied tool call poisons the answer that follows it.** Under a narrower
  approval mode than the one this adapter pins, omp denied ``bash`` three times
  and the model then answered ``git version 2.43.0`` — the output of a command
  it never ran. A reviewer that invents ``git diff`` output is a wrong review
  that looks right, so :meth:`parse_output` fails any run containing a
  denial-marked tool result *whatever the final message says*.

Tool policy is pinned on argv and never inherited: ``--approval-mode yolo``
bounded by an explicit ``--tools`` allow-list. omp's own factory default **is**
``yolo`` over every tool, so there is no safe default to fall back on and the
explicit flag is what makes both the default and the user's ``config.yml``
irrelevant. The bypass is declared (``read_only_modes.omp.bypass_exception`` in
``providers.yaml``, ``yolo`` in ``tests/test_read_only_modes.py``'s
``NEGATIVE_VALUE_TOKENS``) and was accepted by the repository owner on
2026-09-17 for the ``generate`` profile only.

Auth is omp's own ``$env`` chain, in the order omp reads it: the process env,
then a ``.env`` in the run's cwd, then ``~/.omp/agent/.env``, then ``~/.omp/.env``
/ ``~/.env``. There is no login state and no keyring, and no auth-status
subcommand exists — see :attr:`OmpProvider.auth_check`. The first leg is the
one this adapter is responsible for: :meth:`OmpProvider.get_env` re-emits
``OPENROUTER_API_KEY`` explicitly so it survives a filtered run, because
nothing in omp's allowlist profile admits it.
"""
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import (
    PROFILE_GENERATE,
    CATEGORY_PERMISSION_DENIED,
    CATEGORY_SERVER_ERROR,
    STATUS_AUTH_FAILED,
    STATUS_RATE_LIMITED,
    STATUS_TIMEOUT,
    USAGE_FULL,
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    VERSION_TOO_LOW,
    split_reasoning_effort,
)
from .pi import parse_answer_text
from .pi_family_stream import (
    _ASSISTANT_MESSAGE_REQUIRED_KEYS,  # noqa: F401 - re-exported; the docstrings cite it
    StreamDialect,
    _answer_text,
    _assistant_ends,
    _cap,
    _events,
    _first_line,
    _one_line,
    _result_text,
    _retry_give_up,
    _stream_version,
    _tool_ends,
    _unclosed_container,
    assistant_text_of_stream,
    shape_fault,
    sum_usage,
    unrecognized_stop_reason,
    version_clause,
    warn_stream_version,
)

# --------------------------------------------------------------------------- #
# Terminal codes. Imported by name from the runner rather than re-spelled: the
# whole point of `parse_output` setting one is that `invoke_with_file_output`
# reads the *same* constants when it decides whether a written findings file may
# still be recovered beside a failed parse.
# --------------------------------------------------------------------------- #
try:  # pragma: no cover - import shim mirrors the rest of utils/
    from ..llm_client import ERROR_SUBPROCESS_FAILED, ERROR_TIMEOUT
except ImportError:  # pragma: no cover - direct-script import shim
    ERROR_SUBPROCESS_FAILED = "SUBPROCESS_FAILED"
    ERROR_TIMEOUT = "TIMEOUT"


#: The overlay every dispatch loads with ``--config``, resolved **absolutely**.
#:
#: ``parents[2]`` is the skill root (``utils/providers/omp.py`` → ``utils`` →
#: the skill), which resolves identically under the plugin cache, ``link-skill.sh``,
#: the opencode package and the container image — provided the file is on the
#: packaging allowlist, which is not automatic: ``tests/container/context_manifest.txt``
#: and the repo-root ``.dockerignore`` name it, and ``packaging/common/payload.py``
#: carries it on ``REQUIRED_INVENTORY`` so a short payload fails the build rather
#: than shipping a skill whose every omp dispatch dies at launch.
OVERLAY_PATH = Path(__file__).resolve().parents[2] / "assets" / "omp" / "overlay.yml"

#: Thinking levels accepted by ``omp --thinking``. The same seven rungs as pi,
#: with ``off`` in ``none``'s place — omp spells the bottom rung ``off``.
#:
#: omp does **not validate** this flag: ``none`` and ``ultra`` are accepted
#: silently and ignored, so this whitelist is the only guard there is. The
#: ``:effort`` suffix is stripped from the model before ``--model`` and rendered
#: as ``--thinking``, which also keeps omp's own native ``:level`` parsing out of
#: the picture.
#:
#: omp's eighth level ``auto`` is deliberately **not** a rung: it is not a
#: canonical effort. Because omp parses a ``:level`` suffix on ``--model``
#: natively, ``omp:<model>:auto`` still works — the suffix is not recognised
#: here, so it passes through as part of the model string and omp reads it.
EFFORT_LADDER = ReasoningLadder(
    provider="omp",
    rungs=("minimal", "low", "medium", "high", "xhigh", "max"),
    spellings=(("off", "none"),),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted

#: The tool allow-list ``--approval-mode yolo`` is bounded by (§2.3 rule 3).
#:
#: Tools outside it are **absent** rather than denied, which is the shape that
#: produced an honest refusal in the measurement ("file-writing tools are
#: unavailable", and no file appeared) instead of the fabrication a denial tier
#: produced. It excludes ``task`` (sub-agent fan-out — a cost multiplier the
#: harness cannot see), ``web_search`` and ``hub`` (egress), ``eval``, ``lsp``,
#: ``todo``, ``ast_edit`` and the ``goal``/``*_experiment``/``update_notes``
#: bench tools.
#:
#: **``find`` was on this list until 18.2.9 and is gone because the NAME changed
#: meaning, not because a capability was dropped.** At 18.2.2 ``find`` was an
#: alias of ``glob`` — the same schema, ``approval: "read"`` — so the rendered
#: request carried six tool schemas under seven names and naming it bought
#: nothing but a guard against a release that split the two apart. That release
#: arrived. At 18.2.9 ``find`` is its own tool (``FindTool``: *"Semantic grep:
#: find files and line ranges by describing what they do"*, still
#: ``approval: "read"``), gated behind the setting ``find.enabled``, whose
#: shipped default is ``false`` — so the name is not in the registry ``--tools``
#: validates against, and every dispatch died at ``CliUsageError: Unknown tool
#: in --tools: find`` before the run began. The globbing the alias stood for is
#: ``glob``'s and is still here, so **nothing narrowed**; the semantic search the
#: name now denotes is a capability this adapter never granted and is
#: model-backed (upstream: *"judged by the judge model role"*), which puts it
#: with ``task`` — an unbounded per-dispatch cost the harness cannot see. It is
#: dropped rather than re-enabled from the overlay.
#:
#: ``ast_edit`` is the other 18.2.9 arrival — write-class, and default **on**
#: (``astEdit.enabled: true``) — and it stays out for the reason every
#: write-class tool beyond ``edit``/``write`` does: this list is the whole bound
#: on ``yolo``, so a tool nobody measured is a tool nobody declared.
#:
#: The accepted vocabulary at 18.2.9, swept **name by name** (the "Valid tools:"
#: list in the error is incomplete and varies between runs — never parse it):
#: ``read bash edit write grep glob search lsp task todo web_search hub eval
#: ast_edit goal init_experiment run_experiment log_experiment update_notes``,
#: where ``search`` is the alias of ``grep`` that replaced ``find``'s alias of
#: ``glob``.
#:
#: **``--tools`` is validated before model resolution, at zero spend**, so an
#: unknown name is 0 B stdout / zero requests with the refusal on stderr — exit 1
#: and a ``CliUsageError`` Bun trace at 18.2.2, exit 2 and a plain ``Error:
#: Unknown tool in --tools: <name>.`` at 18.8.3 (the first on
#: ``LAUNCH_FAILURE_MARKERS``' ``spawn_failed`` row, the second on
#: ``STDERR_LAUNCH_FAILURE_MARKERS``', read on stderr only) — ``spawn_failed`` (D3k rung 1: fails the whole batch, never
#: retried), the right disposition for a property of the *install*, but one that
#: reads like a containment breach when it is an argv fault and the run never
#: started. ``tests/test_omp_containment.py``'s
#: ``TestTheAllowListIsWhatTheInstalledBinaryAccepts`` puts every name through
#: that same free pre-flight against the installed binary, so the next rename is
#: a red test naming the tool rather than a dead dispatch naming nothing.
OMP_TOOLS = ("read", "grep", "glob", "bash", "edit", "write")

#: The environment variable omp's own ``$env`` chain reads its credential from,
#: and therefore the one name this adapter passes through rather than relabels.
#:
#: It is worth a constant because it is the thing that makes omp different from
#: its siblings here: kimi, qwen and copilot carry the same OpenRouter key past
#: the env filter under **their own** prefixed spelling
#: (``KIMI_MODEL_API_KEY``, ``COPILOT_PROVIDER_API_KEY``), so for them
#: ``OPENROUTER_API_KEY`` really is a foreign credential the filter should drop.
#: omp reads it under its real name, so for omp it is not foreign at all — which
#: is the carve-out ``tests/test_env_allowlist.py`` names by this constant.
OMP_CREDENTIAL_ENV = "OPENROUTER_API_KEY"

#: The approval mode, as an **argv token** so ``tests/test_read_only_modes.py``'s
#: scan can see it. Never put in the overlay (invisible to the guard), and
#: ``--auto-approve`` is never used.
OMP_APPROVAL_MODE = "yolo"

#: The ``session.version`` this parser was written against.
#:
#: A different value is **not** a refusal — a bump with the fields intact reads
#: fine and refusing it would fail every dispatch on a benign release — but it
#: is WARNed once per process and quoted in every shape error below, so a drift
#: is never reported as garbage.
OMP_STREAM_VERSION = 3

#: What every assistant ``message_end`` must carry before anything reads it is
#: ``pi_family_stream._ASSISTANT_MESSAGE_REQUIRED_KEYS``, imported above. A
#: release that renames one of those fails by name at the first parse.

#: The closed ``stopReason`` set, all four observed at 18.2.2. Anything else
#: fails closed (§2.6 step 4): an unobserved enum may be a cut (``maxTokens``), a
#: refusal or a rename, and the parser cannot tell which.
_KNOWN_STOP_REASONS = ("stop", "toolUse", "error", "aborted")

#: omp's words for the shared pi-family reader (``pi_family_stream``). Every
#: sentence the reader builds for omp reads "omp 18.2.2" and version 3 from here,
#: so they stay byte-identical to the ones this module built before the lift.
#: ``compaction_event`` is omp's spelling, ``auto_compaction_end``; its usage leg
#: stays **off**: T7.15 measured (container, omp 18.2.11,
#: ``tests/fixtures/omp/compaction-summarized``) that a compaction which really
#: summarizes carries no ``usage`` in ``result`` — see :meth:`OmpProvider.parse_usage`.
OMP_DIALECT = StreamDialect(
    product="omp",
    verified_version="18.8.3",
    stream_version=OMP_STREAM_VERSION,
    stop_reasons=_KNOWN_STOP_REASONS,
    compaction_event="auto_compaction_end",
    compaction_usage=False,
)

#: The headless approval denial, verbatim. Matched on a tool **result's** text
#: only, never on assistant text — the model may quote it.
_APPROVAL_DENIAL_MARKERS = ("requires approval but no interactive UI available",)

#: Foreign vendor keys stripped from every dispatch (§2.10 rule 2).
#:
#: The first two are measured: with either of them in the process env a run with
#: no ``--model`` picked ``google/gemini-3.1-pro-preview`` and spun on a real
#: 429. This adapter always passes ``--model openrouter/…`` so the *provider* is
#: fixed, but the key *source* can still be shadowed, and "adapter wins, ambient
#: loses, no fallback" is the same rule copilot, kimi, qwen and vibe follow.
#:
#: ``OPENROUTER_API_KEY`` is deliberately **not** here: it is what
#: :meth:`OmpProvider.get_env` injects, and an adapter that strips what it
#: injects is a bug ``test_nothing_the_adapter_injects_is_also_stripped`` catches.
_STRIPPED_VENDOR_VARS: Tuple[str, ...] = (
    # The two MEASURED re-selecting the provider: with either of these in the
    # process env a run with no --model picked google/gemini-3.1-pro-preview and
    # spun on a real 429.
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    # The rest is upstream's own `docs/environment-variables.md` §1 "Core provider
    # credentials" table, transcribed whole and minus OPENROUTER_API_KEY. It is a
    # transcription rather than a judgement call on purpose: every name in that
    # table is a credential that authorises or selects one of omp's built-in model
    # providers, this adapter pins `--model openrouter/…` on every dispatch and
    # needs none of them, and a list assembled by picking the "important" ones
    # would be a list nobody can check against the document it came from.
    "AIAND_API_KEY", "AI_GATEWAY_API_KEY", "AIMLAPI_API_KEY",
    "ALIBABA_CODING_PLAN_API_KEY", "ALIBABA_TOKEN_PLAN_API_KEY",
    "ANTHROPIC_API_KEY", "ANTHROPIC_FOUNDRY_API_KEY", "ANTHROPIC_OAUTH_TOKEN",
    "BAILIAN_TOKEN_PLAN_API_KEY", "BASETEN_API_KEY", "CEREBRAS_API_KEY",
    "CHARM_HYPER_API_KEY", "CLINE_API_KEY", "CLOUDFLARE_ACCOUNT_ID",
    "CLOUDFLARE_AI_GATEWAY_API_KEY", "CLOUDFLARE_GATEWAY_ID",
    "COMMAND_CODE_API_KEY", "COREWEAVE_API_KEY", "CURSOR_ACCESS_TOKEN",
    "DEEPINFRA_API_KEY", "DEEPSEEK_API_KEY", "DEVIN_API_KEY",
    "FIREPASS_API_KEY", "FIREWORKS_API_KEY", "GITLAB_TOKEN", "GMI_API_KEY",
    "GOOGLE_API_KEY", "GROQ_API_KEY", "HF_TOKEN", "HUGGINGFACE_HUB_TOKEN",
    "KILO_API_KEY", "LITELLM_API_KEY", "LLAMA_CPP_API_KEY",
    "LM_STUDIO_API_KEY", "MINIMAX_API_KEY", "MINIMAX_CODE_API_KEY",
    "MINIMAX_CODE_CN_API_KEY", "MISTRAL_API_KEY", "MODEL_API_KEY",
    "MOONSHOT_API_KEY", "NANO_GPT_API_KEY", "NOVITA_API_KEY", "NVIDIA_API_KEY",
    "OLLAMA_API_KEY", "OLLAMA_CLOUD_API_KEY", "OPENAI_CODEX_OAUTH_TOKEN",
    "OPENCODE_API_KEY", "QIANFAN_API_KEY", "QWEN_OAUTH_TOKEN",
    "QWEN_PORTAL_API_KEY", "SAKANA_API_KEY", "SILICONFLOW_API_KEY",
    "SILICONFLOW_CN_API_KEY", "SYNTHETIC_API_KEY", "TOGETHER_API_KEY",
    "UMANS_AI_CODING_PLAN_API_KEY", "VENICE_API_KEY", "VLLM_API_KEY",
    "WAFER_SERVERLESS_API_KEY", "XAI_API_KEY", "XAI_OAUTH_TOKEN",
    "XIAOMI_API_KEY", "XIAOMI_TOKEN_PLAN_AMS_API_KEY",
    "XIAOMI_TOKEN_PLAN_CN_API_KEY", "XIAOMI_TOKEN_PLAN_SGP_API_KEY",
    "YOLO_AUTO_API_KEY", "ZAI_API_KEY", "ZENMUX_API_KEY", "ZHIPU_API_KEY",
)

#: What ``build_command`` must be able to show the installed omp accepts before
#: it renders anything (§2.11).
#:
#: This is the gate's **load-bearing** form, not the optional one, because none
#: of these has a safe degraded argv: without ``--mode`` the parser reads a text
#: stream; without ``--tools`` or ``--approval-mode`` the run inherits omp's
#: factory ``yolo`` over *every* tool; without ``--config`` the retry floor is
#: unbounded. ``-p`` is confirmed through ``--print``, the long spelling on the
#: same help line (``-p, --print``), because the shared token regex reads long
#: options only; the argv keeps ``-p``.
#:
#: ``--thinking``, ``--max-time`` and ``--cwd`` are appended by
#: :meth:`OmpProvider.build_command` only when the call actually renders them,
#: so an omitted flag is never probed.
OMP_REQUIRED_FLAGS: Tuple[str, ...] = (
    "--print",
    "--no-session",
    "--mode",
    "--config",
    "--approval-mode",
    "--tools",
    "--cwd",
    "--model",
)

#: What omp needs, after ``--max-time`` fires, to write the ``aborted``
#: ``message_end`` + ``agent_end`` and exit before the parent's
#: ``subprocess.run(timeout=…)`` kills it.
#:
#: **The overshoot is measured, on the production (Responses) path, and it is
#: 0.72 s worst case.** ``--max-time`` INTERRUPTS whatever omp is doing rather
#: than waiting it out — that was the open question, and the answer closes it in
#: all three shapes a deadline can land in. Spawn-to-exit wall clock minus the
#: ``--max-time`` value, against a fail-forever loopback stub: 0.17 s cut in the
#: middle of a 20 s retry backoff sleep (N = 5, 10, 30, 45 — constant, so the
#: sleep is abandoned, not slept out); 0.16–0.17 s cut with a request in flight
#: against a server taking 60 s to answer; 0.19 s cut inside a running ``bash``
#: tool child (the §1.5 ``toolUse`` shape, exit 0). Four concurrent dispatches
#: move it to 0.18–0.21 s. The one outlier is a **cold HOME**: a first run that
#: extracts the 346 MB of natives overshoots by **0.72 s**, and that is the
#: number this constant has to cover.
#:
#: 5 s is therefore kept rather than re-pinned: it is ~7× the worst measurement
#: and ~25× the steady state, and unlike qwen's 30 s it idles nothing that
#: matters — the only slices it costs are ``timeout_s ≤ 5``, where the flag is
#: omitted (see :func:`max_time_value`) and where no omp dispatch could have
#: finished anyway. ``tests/test_providers.py`` pins this value as a literal
#: alongside the renderings it produces (``1200 → "1195"``, ``25 → "20"``), so
#: the constant and that table move together or not at all.
OMP_SHUTDOWN_MARGIN_S = 5

#: The smallest ``--max-time`` omp accepts, **measured**: ``--max-time 1`` and
#: ``--max-time 3`` both ran and both cut cleanly.
#:
#: qwen's ``MIN_INNER_TIMEOUT_S = 60`` is a guard against a binary that *rejects*
#: sub-second values and it is deliberately not copied: it has nothing to guard
#: here, and copying it would render ``--max-time 60`` into a 40 s slice and turn
#: a clean ``aborted`` into a SIGTERM.
OMP_MIN_MAX_TIME_S = 1

#: The three Bun shapes a pre-flight stderr wraps its one real sentence in.
#:
#: **Measured, and the reason this is three patterns rather than one.** A draft
#: dropped only the trace frames, which is the shape that *follows* the
#: diagnosis. What precedes it is worse: Bun prints a **source-context prelude**
#: — six numbered lines of the minified binary's own source, then a caret column
#: — and it comes first, so pi's 300-character cap spent its whole budget on
#: ``466349 | ` + `Use /login, set an API key…`` and ellipsed away the actual
#: ``error: No API key found for openrouter.`` The two rows that carry it
#: (``auth-error-preflight``, ``invalid-tool``) are exactly the two whose
#: diagnosis a user needs, so the prelude is dropped by name:
#:
#: * ``466354 |       const n = await …`` — a line number, a pipe, source;
#: * ``                       ^`` — the caret column under it;
#: * ``      at #xo (/$bunfs/root/omp-linux-x64:466354:15)`` — the frames, whose
#:   offsets are inside the single-file binary and mean nothing outside it.
_BUN_NOISE = re.compile(
    r"^\s*\d+\s*\|"            # a numbered source line from the prelude
    r"|^\s*\^\s*$"             # the caret column under it
    r"|^\s+at\s+\S"            # a stack frame
)


class OmpFlagsUnconfirmed(RuntimeError):
    """The installed omp could not be shown to accept every flag this argv needs.

    Raised **before any argv exists**, from :meth:`OmpProvider.build_command`,
    which is called outside every caller's ``try`` on purpose: it propagates
    through ``invoke_with_file_output`` and out of ``run_single_model``'s ladder
    loop into its per-model ``except``, which records it as that slot's error and
    returns. ``ladder.record`` is never reached — no retry, by construction — and
    the other slots of the fan-out are unaffected.

    It borrows the ``version-too-low`` word, as cursor's does, so the slot's
    error and a doctor row for a genuinely-below-floor build say the same thing.
    The claim it makes is the stronger one, though: it refuses by the **name of
    the flag** the build lacks rather than by a number, and a number would only
    ever be an upper bound on the floor.
    """

    def __init__(self, missing: Tuple[str, ...], binary: str) -> None:
        self.missing = tuple(missing)
        self.binary = binary
        self.state = VERSION_TOO_LOW
        super().__init__(
            f"omp slot refused ({VERSION_TOO_LOW}): {binary} does not list "
            f"{', '.join(self.missing)} in its --help, and multi-llm will not run "
            "omp without them (--mode json is the stream this parser reads; "
            "--approval-mode + --tools are what stop omp's factory `yolo` from "
            "running every tool it has; --config carries the retry bound; --cwd "
            "stops the silent relocation to /tmp). "
            "Upgrade omp, or drop omp from --models."
        )


def max_time_value(timeout_s: Optional[int]) -> Optional[str]:
    """Render ``--max-time`` for an outer deadline of ``timeout_s``.

    qwen's **formula**, never qwen's helper: outer deadline minus a shutdown
    margin, ``None`` in ⇒ ``None`` out so the flag is absent rather than
    defaulted. The two constants and the warning text are omp's own.

    The undersized case is an **omission**, not qwen's clamp-and-render. When
    ``timeout_s <= OMP_SHUTDOWN_MARGIN_S`` — which the retry ladder produces
    legitimately, since a retry's ``timeout_s`` is the slot's *remaining* wall
    clock down to a 1.0 s floor — no value both leaves the margin and is one omp
    accepts. Clamping would put a ``--max-time`` larger than the outer deadline
    on argv, which is a token that cannot do its job; refusing would turn the
    ladder's own short slices into failed slots, because a ``build_command``
    raise escapes as the slot's error with no retry. So the flag is dropped, the
    argv is byte-identical to the ``timeout_s=None`` rendering, and the parent's
    ``subprocess.run`` deadline is the only bound — a run that hits it is a bare
    ``TIMEOUT`` rather than omp's own ``aborted``. One WARNING names omp and both
    numbers.

    A slice merely too short for omp's 12-request 429 chain is **not** undersized
    and nothing is omitted on its account: ``--max-time`` bounds the dispatch, it
    does not promise the chain fits, and the slot had no time for the chain
    whichever way it ended.
    """
    if timeout_s is None:
        return None
    outer = int(timeout_s)
    inner = outer - OMP_SHUTDOWN_MARGIN_S
    if inner < OMP_MIN_MAX_TIME_S:
        print(
            f"WARNING: omp timeout of {outer}s leaves nothing above the "
            f"{OMP_SHUTDOWN_MARGIN_S}s shutdown margin; --max-time omitted, the "
            f"{outer}s deadline is the harness's.",
            file=sys.stderr,
        )
        return None
    return str(inner)


# --------------------------------------------------------------------------- #
# The stream reader. One implementation, read by `parse_output`,
# `describe_failure`, `classify_failure` and `parse_usage` alike — so the
# report's `Reason:` line and the log's error string cannot drift apart. The
# event-level reader (`_events`, `_assistant_ends`, `_tool_ends`, the shape
# check, `sum_usage`, …) is `pi_family_stream`'s, shared with pi and run here
# under `OMP_DIALECT`; what follows is what only omp has (the approval denial,
# the Bun stderr, `errorStatus`, the ladder names) and omp's thin wrappers.
# --------------------------------------------------------------------------- #

def _version_clause(version: Optional[int]) -> str:
    """The parenthetical every shape error carries, naming what the parser knows."""
    return version_clause(version, OMP_DIALECT)


def _warn_stream_version(version: Optional[int]) -> None:
    """One WARN per process for a ``session.version`` that is not the measured 3."""
    warn_stream_version(version, OMP_DIALECT)


def _denied(events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The first approval-denied ``tool_execution_end``, or ``None``.

    **Ordinary tool errors are not denials.** An ``isError: true`` result whose
    text is the command's own failure (``fatal: bad revision``, a ``read`` of a
    missing path) is the model's to recover from, and a later successful call
    plus a ``stop`` is a success. The marker tuple is the whole distinction.
    """
    for event in events:
        if not event.get("isError"):
            continue
        text = _result_text(event)
        if any(marker in text for marker in _APPROVAL_DENIAL_MARKERS):
            return event
    return None


def _shape_fault(
    messages: List[Dict[str, Any]], version: Optional[int]
) -> Optional[str]:
    """The first assistant ``message_end`` missing a required key, as a sentence.

    Checked **by name, before anything reads the stream**, because nothing else
    guards the JSONL surface: the help-text gate covers the argv, and a daily
    release can change the event shape under an unchanged help text with no
    marker at all. The check is the shared reader's, in omp's words.
    """
    return shape_fault(messages, version, dialect=OMP_DIALECT)


def _error_sentence(message: Dict[str, Any]) -> str:
    """``"<status> <message>"`` for an ``error``/``aborted`` terminal message."""
    status = message.get("errorStatus")
    detail = _one_line(str(message.get("errorMessage") or ""))
    if status is not None and detail and not detail.startswith(str(status)):
        return f"{status} {detail}"
    return detail or (f"{status}" if status is not None else "")


def _tool_name(event: Optional[Dict[str, Any]]) -> str:
    if not event:
        return "?"
    return str(event.get("toolName") or "?")


def stderr_diagnosis(stderr: str) -> str:
    """omp's pre-flight stderr, collapsed to one reportable line.

    Two reductions, both measured: a leading ``Working...`` line is dropped (it
    is text mode's spinner and precedes the diagnosis there), every
    :data:`_BUN_NOISE` line is dropped — the source-context prelude *before* the
    diagnosis as well as the stack frames after it — and what is left is
    collapsed and capped at pi's ``_MAX_DIAGNOSIS_CHARS``.

    The prelude is the half that has to go first. It is six numbered lines of
    the minified binary's own source and it precedes the sentence, so without
    this the cap ellipses away the one line a user acts on.

    There is no vendor-JSON tier: omp writes no ``NNN: {json}`` prefix, so pi's
    second rung has nothing to parse here and this is pi's verbatim tier only.
    """
    kept = []
    for line in (stderr or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "Working...":
            continue
        if _BUN_NOISE.match(line):
            continue
        kept.append(stripped)
    return _cap(_one_line(" ".join(kept)))


def _named_for_the_ladder(token: str, sentence: str) -> str:
    """``sentence`` with ``token`` in front of it, unless it already says it.

    **Lane A classifies the error string, not the streams.** Its file-output
    lane reaches for ``classify_streams(str(result.get("error", "")), "")``
    (``utils/review_orchestrator_base.py``) — that composed sentence is the only
    thing it is handed — and never :meth:`OmpProvider.classify_failure`, whose
    callers are ``_format_failure_details`` and the Lane B executor. So a
    structural verdict reaches Lane A's ladder only insofar as this sentence
    carries a word the shared marker tables recognise, and three of the four
    structural shapes carried none:

    * the ``toolUse``-final deadline. ``Command aborted`` is deliberately not a
      marker — a tool error the model *recovered* from contains it — so "run
      ended inside a tool call: bash: Command aborted" classified ``None``, and
      ``None`` is never retried, while the ``aborted`` half of the very same
      ``--max-time`` says "Deadline exceeded" in omp's own words and takes
      rung 2. One deadline, two behaviours on one ladder.
    * the step-3 denial, ``None`` as well: the same *outcome* as
      ``permission_denied`` — never retried — but reported under "Unknown".
    * the 5xx ``error``. Its body says ``The server had an error`` and
      ``(type=server_error)``, and neither is a :data:`SERVER_ERROR_MARKERS`
      row: ``\\bserver error\\b`` wants a space where the type name has an
      underscore, and the ``\\b5\\d{2}\\b\\s*(?:internal|server|…)`` row wants
      one of its words straight after the code.

    Naming the verdict here rather than widening those shared tables keeps the
    word where the shape is known *structurally*, so no other adapter's stream
    is reclassified by one vendor's punctuation. The ``in`` test keeps omp's own
    wording wherever it already carries the word: ``aborted``'s measured
    "Deadline exceeded" is returned untouched.

    The auth (401/403) and rate-limit (429) shapes are deliberately **not**
    named, because they are not the same problem. Both measured bodies already
    carry the tables' own words ("Incorrect API key provided", "Rate limit
    reached"), and the one shape the shared defaults miss — OpenRouter's ``401
    User not found.`` — is missed because Lane A calls ``classify_streams``
    with no adapter in hand and so never sees omp's declared
    :attr:`~OmpProvider.auth_error_patterns`. That gap belongs where the
    patterns are passed and every adapter shares it; closing it here would move
    one vendor's slot from a single dispatch to fatal-to-the-batch on the
    strength of a prefix rather than of the declaration.
    """
    if not sentence:
        return token
    if token.lower() in sentence.lower():
        return sentence
    return f"{token}: {sentence}"


def _tool_use_diagnostics(events: List[Dict[str, Any]]) -> Tuple[str, str]:
    """``(tool name, first line of its result)`` for a ``toolUse``-final stream.

    The last errored ``tool_execution_end``, else the last one. The result line
    is diagnostics only and must never be composed into a classifier-facing
    error string (see :func:`terminal_verdict`).
    """
    tools = _tool_ends(events)
    errored = [e for e in tools if e.get("isError")]
    tool = errored[-1] if errored else (tools[-1] if tools else None)
    detail = _first_line(_result_text(tool)) if tool else ""
    return _tool_name(tool), detail


def terminal_verdict(stdout: str, stderr: str) -> Optional[str]:
    """What the **stream** says went wrong, or ``None``.

    One reader, called by :meth:`OmpProvider.parse_output` and
    :meth:`OmpProvider.describe_failure` alike, so the report's ``Reason:`` line
    and the log's error string cannot say different things about the same bytes.

    ``None`` means the stream carries no verdict: a clean ``stop``, a stdout that
    is not JSONL at all, an empty stdout. stderr is deliberately **not** read
    here — precedence is the caller's to apply, and composing the two channels is
    what ``_DESCRIBE_FAILURE_CHANNELS``' ``STDOUT_ELSE_STDERR`` contract forbids.

    Three of these sentences go out with the shared tables' own word for their
    shape in front of them (:func:`_named_for_the_ladder`), because Lane A
    classifies this *string* and not the streams: an unnamed verdict reaches its
    ladder as ``None`` — "never retried" — however confidently
    :meth:`OmpProvider.classify_failure` read the same bytes.
    """
    events, _junk = _events(stdout)
    if not events:
        return None

    version = _stream_version(events)
    messages = _assistant_ends(events)

    fault = _shape_fault(messages, version)
    if fault is not None:
        return fault

    denial = _denied(_tool_ends(events))
    if denial is not None:
        # The tool's *name* only, as on the toolUse deadline below: the result
        # line is tool-channel text, and this sentence is what Lane A classifies.
        # It travels as parse_output's diagnostic `tool_result` field instead.
        return _named_for_the_ladder(
            "Permission denied",
            f"tool {_tool_name(denial)} was denied approval; the answer that "
            "followed is not trusted",
        )

    if not messages:
        last = events[-1]
        kind = str(last.get("type") or "?")
        message = last.get("message")
        if isinstance(message, dict) and message.get("role"):
            kind = f"{kind}/{message['role']}"
        return (
            f"run ended before any assistant message (last event: {kind}, "
            f"{len(events)} events)"
        )

    final = messages[-1]
    reason = final.get("stopReason")
    if reason == "stop":
        # A `stop` whose content holds no text is not an answer, and omp says so
        # in its own words one event later. MEASURED at 18.2.2: a truncated
        # stream and a 200-with-an-error-body both end in four empty `stop`s and
        # then `{"type": "auto_retry_end", "success": false, "finalError":
        # "Assistant returned empty stop after retry cap; …"}` — a **fifth**
        # event type beyond the thirteen §1.2 lists, and the only place the run
        # says why it produced nothing. Exit code is 0, so without this the
        # shape reports a contentless `Empty output` while the diagnosis sits
        # unread two lines down. A `stop` that *did* carry text is still a
        # success and never reaches here.
        if _answer_text(final).strip():
            return None
        return _retry_give_up(events)
    if reason in ("error", "aborted"):
        sentence = _error_sentence(final) or f"omp reported stopReason {reason!r}"
        if reason == "aborted":
            return _named_for_the_ladder("Deadline exceeded", sentence)
        status = final.get("errorStatus")
        if isinstance(status, int) and 500 <= status < 600:
            return _named_for_the_ladder("Server error", sentence)
        return sentence
    if reason == "toolUse":
        # The tool's *name* only. Its result is content the run read (a file, a
        # command's output), never omp's verdict, and Lane A classifies this
        # sentence through the shared tables: a read that quoted "rate limit
        # exceeded" or "invalid api key" would turn this deadline into
        # rate_limited/auth_failed. The result text travels separately, as
        # parse_output's diagnostic `tool_result` field (_tool_use_diagnostics).
        name, _detail = _tool_use_diagnostics(events)
        return _named_for_the_ladder(
            "Deadline exceeded", f"run ended inside a tool call: {name}"
        )

    return unrecognized_stop_reason(final, version, OMP_DIALECT)


def _never_started(stdout: str) -> bool:
    """True when the stream is a pre-flight corpse: a header, and no run.

    MEASURED at 18.2.2 (``tests/fixtures/omp/auth-error-preflight``): a missing
    key exits 1 in 0.34 s at zero requests, but **not** over an empty stdout —
    omp flushes the ``session`` header (178 bytes, one JSON line) before it
    resolves the credential, and the diagnosis that names the problem (``error:
    No API key found for openrouter.``) is on stderr. So stdout is non-empty and
    yet says nothing: :func:`terminal_verdict` can only offer its
    no-assistant-message fallback there, which reports the *shape* of the stream
    and not the failure.

    That fallback is an answer for a run that **started** and was cut —
    ``ephemeral-only`` is exit 137 over ``session``/``agent_start``/``turn_start``
    and the user message, and "run ended before any assistant message (last
    event: message_end/user, 5 events)" is the whole of what is known about it.
    It is not an answer for a run that never began, which is why the boundary
    here is ``agent_start``: with it absent the agent loop never ran, nothing was
    sent and no model was reached, so the stream is *silent* for
    ``STDOUT_ELSE_STDERR``'s purposes and stderr's diagnosis is the answer.

    Only :meth:`OmpProvider.describe_failure` reads this. :meth:`parse_output`
    keeps the sentence and appends ``; stderr: …`` to it, which is what the
    fixture's ``error_contains`` grades and where both halves are wanted.
    """
    events, _junk = _events(stdout)
    if not events:
        return False
    if any(str(event.get("type")) == "agent_start" for event in events):
        return False
    return not _assistant_ends(events)


class OmpProvider(LLMProvider):
    """Provider for the oh-my-pi coding agent CLI (https://github.com/can1357/oh-my-pi).

    ``omp --no-session -p --mode json`` runs one-shot headless and writes a JSONL
    event stream to stdout, one event per line, with **zero bytes on stderr** on
    success and on API failure alike. Pre-flight faults — a bad model, a missing
    key, a rejected ``--tools`` name, a missing overlay — are the exception: they
    exit 1 with 0 bytes on stdout and a plain-text diagnosis on stderr, at zero
    spend. That asymmetry is why ``_DESCRIBE_FAILURE_CHANNELS["omp"]`` is
    ``STDOUT_ELSE_STDERR`` (precedence) and not ``STDOUT_THEN_STDERR``
    (enrichment).

    **This class does not subclass** :class:`~utils.providers.pi.PiProvider`.
    The two share exactly one thing — the JSON-answer extraction, lifted into
    pi's module-level :func:`~utils.providers.pi.parse_answer_text` and called
    from here — and diverge on everything else: the channel model, the failure
    taxonomy, the tool policy, the transports and usage.

    Model names are omp model selectors passed **verbatim** to ``--model``
    (``openrouter/openai/gpt-5.6-luna``). ``omp models openrouter --json`` lists
    the catalog locally, and its ``selector`` field — not its ``id`` — is the
    spelling to use. An optional ``model[:effort]`` suffix is translated to
    ``--thinking``; anything not in :data:`REASONING_EFFORTS` passes through as
    part of the model name, which keeps ``:free`` ids, bedrock ``…-v1:0`` version
    suffixes and omp's own ``:auto`` intact.

    **The fan-out default transport is stdin**, not argv, and the reason is in
    the harness rather than the adapter: ``invoke_with_file_output`` — the
    function every Lane A review phase goes through — takes no transport argument
    and forwards none, so an adapter default of ``argv`` would leave every review
    prompt on the path measured failing (200 KB on argv is ``E2BIG`` from the
    kernel before omp starts, while the same prompt over stdin is answered in one
    call).

    The SIGKILL hazard, pinned here so nobody shortens the escalation for omp:
    on SIGTERM omp exits in 0.06 s and reaps its own tool children within 1 s; on
    SIGKILL it exits in 0.015 s and **orphans** them, because tool children run
    ``setsid`` in their own process group and a group kill never reaches them.
    The harness's SIGTERM → 10 s → SIGKILL escalation is what makes that safe.
    """

    # ── identity ─────────────────────────────────────────────────────────
    version_cmd = ("omp", "--version")

    #: 18.8.3 is where every captured fixture in ``tests/fixtures/omp/`` was last
    #: captured (first on 18.2.2) and what ``tests/container/cli-versions.lock``
    #: pins. ``omp --version`` prints a bare ``omp/18.8.3`` on stdout, which the
    #: base :meth:`parse_version` reads without an override.
    #:
    #: **Moved 18.2.2 -> 18.8.3 on 2026-10-08**: every captured row re-run on the
    #: host (and ``compaction-summarized`` in the pinned image) by the same three
    #: vehicles, the five composed rows re-derived from the new ``success``. The
    #: JSONL shape held (``agent_end`` gained ``yielded``, nothing the parser
    #: reads moved) and every class held. What moved: ``invalid-tool`` is exit 2
    #: with a plain ``Error: Unknown tool in --tools: …`` and no ``CliUsageError``
    #: word, which the shared launch-failure table now names
    #: (``base.LAUNCH_FAILURE_MARKERS``); ``invalid-model``'s hint names no path;
    #: and the completions client's retry counts (``rate-limit`` 16 → 12,
    #: ``empty`` 21 → 12, ``truncated`` 20 → 12). The Responses chain production
    #: dispatches on is still 6 requests, so :attr:`internal_retries` holds.
    #:
    #: **There is deliberately no ``min_version``.** A measured-at version is an
    #: upper bound on the true floor, never the floor, and the upstream release
    #: notes going back thirty releases mention every gated flag without dating
    #: its introduction — so a number here would be invented. What this adapter
    #: needs is not a version but five flags, and :data:`OMP_REQUIRED_FLAGS`
    #: refuses by the name of the one a build lacks. ``flags_verified_at_floor``
    #: stays empty for the same reason: an exemption requires a declared floor to
    #: have been verified at.
    verified_version = "18.8.3"

    #: The release cadence is roughly daily (18.1.21 → 18.2.2 took three days),
    #: so no ceiling is declared: the drift signals are ``cli-surface.yaml``'s
    #: help sha for the argv surface and :func:`terminal_verdict`'s shape checks
    #: for the JSONL surface, and neither is a version number.
    max_version_exclusive = ""

    #: **omp has no auth-status subcommand**, measured on ``omp --help`` at
    #: 18.2.2, so no probe is declared and none is owed. The three
    #: credential-adjacent commands it does have are each disqualified for the
    #: probe's job: ``omp token <provider>`` *prints the credential*, so a probe
    #: whose success output is the secret would put the key into the captured
    #: streams the doctor row records; ``omp usage`` is a live usage-limit
    #: snapshot over the network for OAuth accounts (a network fact, not a
    #: credential read); and ``omp auth-broker status`` reports the
    #: credential-vault daemon, not whether an OpenRouter key resolves.
    #:
    #: The auth row therefore reads ``unprobed`` on ``doctor`` and ``unknown`` in
    #: the executor preflight — pi's standing state, and by design: a missing key
    #: surfaces one dispatch later as the pre-flight ``No API key found for
    #: openrouter.`` row (exit 1, 0 B stdout, zero requests), which classifies
    #: ``auth_failed`` and lands on D3k rung 1 without a retry.
    auth_check: Tuple[str, ...] = ()

    #: Login is the TUI's ``/login`` and ``auth-broker login`` for OAuth
    #: providers, neither of which applies to an API-key provider. A fix is owed
    #: only where a probe is declared, and none is.
    login_cmd = ""

    #: The local catalog (``omp models openrouter --json``) is a
    #: ``describe_unlisted_model`` follow-up, not a status readout, so nothing is
    #: spawned for the status row.
    setup_probe: Tuple[str, ...] = ()

    install_hint = (
        "Download the omp-linux-x64 asset from "
        "https://github.com/can1357/oh-my-pi/releases, verify it against that "
        "release's SHA256SUMS.txt, chmod +x it and put it on PATH as `omp` "
        "(the @oh-my-pi/pi-coding-agent package needs Bun and does not run "
        "under node)."
    )

    auth_hint = (
        "OPENROUTER_API_KEY, resolved through omp's own $env chain: process env "
        "(passed through explicitly by this adapter), then a .env in the run's "
        "directory, then ~/.omp/agent/.env, then ~/.omp/.env or ~/.env. No login "
        "state and no keyring, and omp has no auth-status subcommand, so an "
        "unprobed row is not a fault."
    )

    # ── declarations ─────────────────────────────────────────────────────
    usage_support = USAGE_FULL

    #: Lane A's review prompts write their findings to ``{output_json_path}``,
    #: and the argv really carries ``write`` and ``edit``: under
    #: ``--approval-mode yolo`` with this allow-list both created and edited
    #: files in the measurement. The declaration is that fact, not an inference.
    supports_file_output = True

    #: TRUE, from its argv: every ``generate`` dispatch renders
    #: ``--approval-mode yolo --tools read,grep,glob,bash,edit,write``
    #: (:data:`OMP_TOOLS`, :data:`OMP_APPROVAL_MODE`), and ``bash`` is on the
    #: allow-list precisely because the code-review lane shells out to ``git
    #: diff`` — under any narrower approval mode ``bash`` is denied headless.
    #: ``tests/test_provider_housekeeping.py``'s ``SHELL_EVIDENCE`` row reads
    #: ``bash`` out of the rendered ``--tools`` value, so dropping it from the
    #: list turns that test red until this moves too.
    runs_shell_in_generate = True

    #: The first adapter whose fan-out default is not argv (§2.5). ``argv`` stays
    #: supported for a caller that asks for it and renders ``-- <prompt>`` last.
    prompt_transport = "stdin"
    supported_prompt_transports: Tuple[str, ...] = ("argv", "stdin")
    prompt_argv_index = -1

    #: omp has no ``--json-schema``; the phase runs its prompt-level JSON path.
    structured_output_support = False

    #: Measured at the configuration this adapter runs (i.e. **with** the
    #: overlay's ``retry.enabled: false``), never omp's default — and now
    #: measured on **both** of omp's client paths, which is what the number
    #: below is about.
    #:
    #: ``max_requests`` is the chain **one failing model call** runs, and it is
    #: **6**, the chain of the **Responses API** path — the one production runs.
    #: The built-in ``openrouter`` provider speaks ``GET /api/v1/models`` and then
    #: ``POST /api/v1/responses`` (``PI_OPENROUTER_RESPONSES`` unset), and every
    #: assistant message it produces carries ``"api":"openrouter"``, which is how
    #: the three ``rate-limit-*`` fixture rows prove in their own bytes which
    #: client they came from. Against a fail-forever loopback stub reached by
    #: overriding that provider's ``baseUrl``, the chain is exactly six requests
    #: whatever the status: a **500** runs 6 in 16.0 s on the fetch wrapper's own
    #: ``500·2ⁿ`` ladder (gaps 0.5, 1, 2, 4, 8 s) and a **429** runs 6 in 100.5 s,
    #: sleeping before each retry the 20 s it reads out of the response **body**
    #: ("Please try again in 20s.", no ``Retry-After`` header anywhere). Six is
    #: the HTTP fetch wrapper's ``maxAttempts: 6`` and nothing else.
    #:
    #: **The completions client is the contrast, not the declaration.** A
    #: ``models.yml`` provider with ``api: openai-completions`` doubles that
    #: chain, because the provider's ``withReplaySafeStreamRetry``
    #: (``maxProviderErrorRetries: 1``) wraps the completions client and does not
    #: wrap the Responses one: a 500 runs **12** in ~32 s, and a 429 ran **16**
    #: in 201 s at 18.2.2 — five 20 s body-parsed sleeps and then the ``500·2ⁿ``
    #: ladder, gaps 20, 20, 20, 20, 20, 0.5, 20, 8.5, 11.5, 8.5, 11.5, 8.5, 11.5,
    #: 8.5, 11.5 — and runs **12** in 201 s at 18.8.3 (the body's 20 s on both
    #: legs, gaps 20 ×5, 0.5, 20 ×5). Those are the numbers the ``rate-limit`` and
    #: ``stdout-error`` fixture rows carry, and 16 is what this field declared
    #: before the production path was measured. They describe a client nothing this adapter dispatches on;
    #: they are kept here because a model spec pointed at a user's own
    #: ``openai-completions`` provider would run them.
    #:
    #: A dispatch's own total is ``6 + (successful calls before it)``, because omp
    #: makes one model call per tool turn and the number of turns is the model's —
    #: the same per-step reading kimi gives its own loop cap. Measured, not
    #: inferred: the ``rate-limit-multi-turn`` row is one successful call that
    #: returns a tool call plus a second call 429'd forever, and its request log
    #: holds **7**. Nothing this adapter sets bounds the turn count; ``--max-time``
    #: bounds the dispatch, and it is what stops a 429'd run in a real slot (at
    #: the shipped 1200 s default, ``--max-time 1195``) — the 100.5 s and 220.5 s
    #: rows were captured with the flag omitted, so that the chain, not the
    #: deadline, was the measurement.
    #:
    #: ``max_wall_s`` stays ``None``, and the production-path measurement is now
    #: the reason rather than the absence of one. The contract is "the worst-case
    #: wall clock **one dispatch** may burn inside the child", and the same
    #: six-request chain measures 100.5 s against an instant stub and **220.5 s**
    #: against one that takes 20 s to answer each 429 — identical request count,
    #: a wall that is just ``backoff + requests × latency`` and therefore a
    #: property of the upstream, not of omp. Nothing was found that omp enforces
    #: on *itself* (muse's 12-minute ceiling is that kind of number); the only ceiling is
    #: ``--max-time``, which this adapter renders from ``timeout_s`` and which is
    #: therefore the slot's number, not the envelope's. Declaring an observed
    #: total would let rule 4 admit an attempt with 101 s left and then watch a
    #: real chain be killed mid-way — the exact outcome rule 4 exists to prevent.
    #:
    #: ``retries_rate_limit`` is ``True`` because omp already makes six attempts
    #: against a 429 on its own (twelve on the completions client at 18.8.3,
    #: sixteen at 18.2.2), so rule 6(b)
    #: withholds the harness's identical re-dispatch; ``configurable_by`` is empty
    #: because those attempts are hard-coded and nothing reachable from here
    #: changes them — the overlay's ``retry.enabled: false`` removes only the
    #: unbounded layer above them.
    internal_retries = InternalRetryEnvelope(
        max_requests=6,
        max_wall_s=None,
        retries_rate_limit=True,
        configurable_by=(),
    )

    #: ``User not found`` is OpenRouter's 401 wording as omp relays it; ``No API
    #: key found for`` is omp's own pre-flight line, which arrives on stderr with
    #: an empty stdout at zero spend.
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "User not found",
        "No API key found for",
    )

    #: Success is structural (:meth:`parse_output`); no regex decides it.
    #: ``Command aborted`` is deliberately **not** a marker — a successful run can
    #: contain it in a tool result the model recovered from.
    exit_zero_failure_markers: Tuple[Any, ...] = ()

    @property
    def name(self) -> str:
        return "omp"

    @property
    def default_timeout(self) -> int:
        return 600

    def is_available(self) -> bool:
        return shutil.which("omp") is not None

    # ── argv ─────────────────────────────────────────────────────────────
    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
        cwd: Optional[str] = None,
    ) -> List[str]:
        """Render the ``generate`` argv, flag order fixed.

        ``omp --no-session -p --mode json --config <overlay> --approval-mode yolo
        --tools <allow-list> [--thinking L] [--max-time N] --cwd <dir> --model M
        -- <prompt>``

        The order is fixed as written so ``expected_argv.yaml``,
        ``cli-surface.yaml`` and the unit test agree on one rendering. ``--``
        ends flag parsing, which is what makes a prompt beginning with ``-``
        safe as a positional — and, measured at 18.2.2, what makes a prompt
        beginning with ``@`` literal text rather than a file reference. The
        stdin transport drops both trailing tokens.

        ``--cwd`` is rendered on **every** dispatch rather than only when the
        spawn cwd is the user's home, so one argv covers the case and the golden
        files see one shape. It is not a tidiness flag: launched from ``$HOME``
        without it omp silently relocates to ``/tmp`` — nothing on either channel
        says so — and a reviewer that moved to ``/tmp`` reads none of the repo's
        files, has an empty ``git diff``, writes ``{output_json_path}`` into
        ``/tmp``, and still exits 0 with a plausible-looking answer. The obvious
        alternative is worse: ``--allow-home`` keeps the cwd *and* auto-mounts the
        MCP servers from ``~/.cursor/mcp.json``, so it is never rendered on any
        profile.

        Raises:
            OmpFlagsUnconfirmed: when omp is installed but its ``--help`` does
                not list every flag this argv needs. Raised before any argv
                exists — a refusal never returns a partial command.
        """
        base_model, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        max_time = max_time_value(timeout_s)

        # The gate reads the flags THIS call will emit, before anything is
        # assembled. One help spawn per process (the shared reader is memoised on
        # the binary and help argv); an unresolvable binary reports nothing
        # missing, which is `is_available()`'s refusal to make and what lets the
        # read-only scan render an argv without a probe.
        emitted = list(OMP_REQUIRED_FLAGS)
        if effort is not None:
            emitted.append("--thinking")
        if max_time is not None:
            emitted.append("--max-time")
        missing = self.missing_flags(emitted)
        if missing:
            raise OmpFlagsUnconfirmed(missing, self.gate_binary(runnable=True) or "omp")

        cmd = [
            "omp", "--no-session", "-p",
            "--mode", "json",
            "--config", str(OVERLAY_PATH),
            "--approval-mode", OMP_APPROVAL_MODE,
            "--tools", ",".join(OMP_TOOLS),
        ]
        if effort is not None:
            cmd += ["--thinking", effort]
        if max_time is not None:
            cmd += ["--max-time", max_time]
        cmd += ["--cwd", cwd or os.getcwd()]
        cmd += ["--model", base_model, "--", prompt]
        return cmd

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
        """Deliver the prompt on stdin (the default) or on argv.

        The two renderings differ by exactly the trailing ``["--", prompt]``, so
        the stdin argv is ``build_command(…)[:-2]``. That ``[:-2]`` is omp's own
        override and not the base helper's ``[:-1]``: dropping only the prompt
        would leave a bare ``--`` on argv.

        Never both: a prompt given on argv *and* on stdin becomes two user
        messages. The caller writes the prompt and closes the pipe, which is the
        EOF omp needs — an inherited non-EOF pipe blocks it forever at startup
        phase ``readPipedInput``.
        """
        argv = self.build_command(
            prompt, model, timeout_s=timeout_s, schema=schema, cwd=cwd
        )
        if transport == "stdin":
            return argv[:-2], prompt
        if transport == "argv":
            # No `@` refusal here, and the measurement that retired it is the
            # reason — measured at 18.2.2 in both directions: after `--`,
            # `@atfile.txt` arrives at the model as that literal text and the
            # file is NOT read; the same prompt without `--` inlines the file's
            # contents into the user message as `<file name="…">…</file>`. So
            # the trailing `["--", prompt]` `build_command` always renders is
            # what makes an `@`-prefixed prompt safe on argv, and a refusal here
            # would only fail a legitimate prompt for a hazard the argv already
            # closes. That makes `--` load-bearing rather than tidiness: drop it
            # and every prompt beginning with `@` silently becomes a file read,
            # with the model answering about bytes nobody asked it to read.
            return argv, None
        raise ValueError(
            f"omp does not support the {transport!r} prompt transport "
            f"(supported: {', '.join(self.supported_prompt_transports)})"
        )

    # ── parsing ──────────────────────────────────────────────────────────
    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Read the JSONL stream. **Success is never read off the exit code.**

        Five steps, in order:

        1. **Empty stdout.** Which silence it is comes from stderr, never from an
           exit code this method is not given. Every 0-byte stdout *measured* at
           18.2.2 is a pre-flight fault that put its diagnosis on stderr
           (``invalid-model``, ``invalid-tool``), so that sentence is named
           verbatim. The empty-stop exhaustion is **not** one of them, whatever
           §1.9 predicted: in ``--mode json`` the retry cap is FOUR cycles with
           the stream written in full — four assistant ``message_end``s carrying
           ``stopReason: "stop"`` and ``content: []``, then ``auto_retry_end``
           with ``finalError`` — so ``truncated`` and ``error-envelope`` reach
           step 4's empty-``stop`` branch and are reported ``Empty output (…)``
           with omp's own sentence, never this one. What is left here is a run
           silent on *both* channels, which no capture produces: it gets the bare
           ``Empty output`` with no ``(stderr: …)`` clause, which classifies as
           transport-shaped and may be re-dispatched — right for a provider-side
           refusal and wrong for a CLI/argv fault. An empty stdout is never on
           its own evidence of a launch fault.
        2. **Shape.** Every assistant ``message_end`` must carry
           :data:`_ASSISTANT_MESSAGE_REQUIRED_KEYS`. One that does not fails by
           name with a hard code, and step 4 is never reached.
        3. **Approval denials fail the run before the final message is read**,
           whatever that message says. A ``stop`` carrying a well-formed findings
           array after a denied ``git diff`` is exactly the fabricated review the
           tool policy exists to prevent, and a parser that read only the final
           message would accept it.
        4. **The last assistant ``message_end``**, branched on a *closed*
           ``stopReason`` set. An unobserved enum fails closed rather than being
           handed to :func:`parse_answer_text` — and so does a ``stop`` whose
           answer opens a JSON document and never closes it
           (:func:`_unclosed_container`), because that function's fallback scans
           for *balanced* substrings and a cut findings array still holds plenty
           of those.
        5. Nothing reads the return code.

        **Why this sets ``error_code`` itself**, which no shipped adapter does:
        ``invoke_with_file_output`` treats a bare ``PARSE_ERROR`` as "the command
        ran, the model may still have written the file" and goes on to read
        ``{output_json_path}``. Lane A's review prompts write their findings
        *before* the model's later tool calls, so a run whose findings file was
        written and whose ``git diff`` was then cut by ``--max-time`` — exit 0,
        ``toolUse``-final — would be a failed parse followed by a recovered file,
        reported as success with a cut-off review passed downstream as complete.
        The three in-stream terminal shapes and the denial therefore carry a code
        from the hard tuple, so the file is neither read nor reported.
        """
        raw = stdout or ""
        if not raw.strip():
            diagnosis = stderr_diagnosis(stderr)
            error = f"Empty output (stderr: {diagnosis})" if diagnosis else "Empty output"
            return {"success": False, "error": error, "raw": "", "data": None}

        events, junk = _events(raw)
        version = _stream_version(events)
        _warn_stream_version(version)
        messages = _assistant_ends(events)

        def with_junk(sentence: Optional[str]) -> Optional[str]:
            """Name the first non-JSON stdout line on the reader's sentences.

            `_events` keeps the lines it could not parse, and a banner — an
            update notice, a deprecation warning, a runtime's own chatter —
            arrives as exactly one of them beside an otherwise well-formed
            stream. Naming it only when there was no assistant message is the
            case that needs it least: there the stream already failed loudly.
            The sentences that go out with a hard `error_code` are the ones a
            reader has to act on, so the banner rides along with each of them,
            and a future line nobody has seen yet is visible in the reported
            error rather than dropped on the floor.
            """
            if sentence and junk:
                return f"{sentence}; non-JSON output: {_first_line(junk[0])}"
            return sentence

        # Every sentence below comes from :func:`terminal_verdict` and never
        # from a second copy of the read. What this method adds is the
        # `error_code` — which the verdict does not carry, because the code is a
        # statement about whether a findings file beside the stream may be
        # recovered and `describe_failure` is only ever diagnostics.
        if _shape_fault(messages, version) is not None:
            return {
                "success": False,
                "error": with_junk(terminal_verdict(raw, "")),
                "error_code": ERROR_SUBPROCESS_FAILED,
                "raw": raw,
                "data": None,
            }

        denial = _denied(_tool_ends(events))
        if denial is not None:
            out = {
                "success": False,
                "error": with_junk(terminal_verdict(raw, "")),
                "error_code": ERROR_SUBPROCESS_FAILED,
                "raw": raw,
                "data": None,
            }
            # Diagnostics beside the error, never inside it (terminal_verdict).
            out["tool_name"] = _tool_name(denial)
            detail = _first_line(_result_text(denial))
            if detail:
                out["tool_result"] = detail
            return out

        if not messages:
            sentence = with_junk(
                terminal_verdict(raw, "")
                or (
                    "run ended before any assistant message (last event: none, "
                    f"{len(events)} events)"
                )
            )
            diagnosis = stderr_diagnosis(stderr)
            if diagnosis:
                sentence = f"{sentence}; stderr: {diagnosis}"
            # No `error_code`: the model produced nothing, and a file it did not
            # write cannot be recovered — so `PARSE_ERROR` is correct and the
            # file channel is welcome to look.
            return {"success": False, "error": sentence, "raw": raw, "data": None}

        final = messages[-1]
        reason = final.get("stopReason")

        if reason == "stop":
            answer = _answer_text(final)
            if not answer.strip():
                # `Empty output` on its own, unless omp's own retry gave up and
                # said why (`auto_retry_end.finalError`). That sentence comes
                # from :func:`terminal_verdict` like every other one here and
                # not from a second call to :func:`_retry_give_up` underneath
                # it: this is the branch `truncated` and `error-envelope` both
                # land on — the four-cycle empty-stop cap, exit 0, Lane A's
                # production parser — so a private read is exactly where the
                # report and the log would drift apart without anything
                # noticing. Only the wrapping is this method's own. Still no
                # `error_code`: the model produced nothing, and a file it did
                # not write cannot be recovered, so the file channel is welcome
                # to look.
                gave_up = terminal_verdict(raw, "")
                return {
                    "success": False,
                    "error": (
                        f"Empty output ({gave_up})" if gave_up else "Empty output"
                    ),
                    "raw": answer,
                    "data": None,
                }
            cut = _unclosed_container(answer)
            if cut is not None:
                # **A cut document is never handed to the extractor.**
                # `parse_answer_text` falls back from a failed `json.loads` to
                # `extract_json_from_text`, which ranks the *balanced* substrings
                # it finds and returns the last one — so an answer that opened a
                # findings array and stopped mid-record still offers it every
                # complete bracket pair nested inside the records that did
                # arrive. Reproduced against a `stop` carrying one whole finding
                # and half of the next: `success: True`, `data: [10, 15]`, the
                # first finding's `line_range` returned as the review. §6.2's
                # `truncated` row exists for exactly this shape — no half-parsed
                # object is ever the answer — so the outer container is judged
                # before any substring is extracted.
                #
                # No `error_code`, for the same reason the empty stop above
                # carries none: this says nothing about a findings file the
                # model may have written whole before the stream was cut, so the
                # file channel is welcome to look.
                closing = "]" if cut == "[" else "}"
                return {
                    "success": False,
                    "error": (
                        f"Truncated output (the answer opens a JSON document "
                        f"with '{cut}' and never closes it: no matching "
                        f"'{closing}' in {len(answer)} characters)"
                    ),
                    "raw": answer,
                    "data": None,
                }
            result = dict(parse_answer_text(answer))
            # **`raw` carries the answer on every outcome, success included.**
            # A successful extraction returns `{"success": True, "data": …}`
            # and nothing else, so the model's own words were dropped the
            # moment its answer happened to contain a JSON document — and the
            # `ask` lane reads exactly this pair: `recover_answer_text` refuses
            # a `dict`/`list` `data` (an erroneously-extracted fragment out of a
            # prose answer that merely quoted an example), falls back to `raw`,
            # and with `raw` absent falls back again to the per-model log's
            # captured stdout — which for this adapter is the JSONL event
            # stream, rejected by `looks_like_ndjson`. A perfectly good markdown
            # answer with one fenced JSON example in it therefore recovered as
            # nothing at all. `setdefault`, because the failure paths inside
            # `parse_answer_text` already set it to this same text.
            result.setdefault("raw", answer)
            return result

        if reason in ("error", "aborted"):
            return {
                "success": False,
                "error": with_junk(terminal_verdict(raw, "")),
                "error_code": (
                    ERROR_TIMEOUT if reason == "aborted" else ERROR_SUBPROCESS_FAILED
                ),
                "raw": raw,
                "data": None,
            }

        if reason == "toolUse":
            out = {
                "success": False,
                "error": with_junk(terminal_verdict(raw, "")),
                "error_code": ERROR_TIMEOUT,
                "raw": raw,
                "data": None,
            }
            # Diagnostics beside the error, never inside it: the error string is
            # what Lane A classifies (see `terminal_verdict`).
            name, detail = _tool_use_diagnostics(events)
            out["tool_name"] = name
            if detail:
                out["tool_result"] = detail
            return out

        return {
            "success": False,
            "error": with_junk(terminal_verdict(raw, "")),
            "error_code": ERROR_SUBPROCESS_FAILED,
            "raw": raw,
            "data": None,
        }

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        """omp's only voice on the exit-1 paths, with **precedence**, not enrichment.

        ``invoke_with_provider`` calls this once, inside the ``returncode != 0``
        branch, and Lane A reaches :meth:`parse_output` only on exit 0 — so every
        in-stream failure that exits 1 (an ``error`` carrying 401/429/500/400,
        an ``aborted`` deadline) is recovered *here* or nowhere. A hook that read
        only stderr would render all of them as a bare ``omp exited with code 1``
        over a zero-byte stderr.

        ``_DESCRIBE_FAILURE_CHANNELS["omp"]`` is ``STDOUT_ELSE_STDERR``, and the
        one consequence the hook must honour is that **when stdout answers,
        stderr may not change the text**. So the two channels are never composed:
        the stream's verdict alone, else the pre-flight stderr diagnosis, else
        ``None``.

        The question that leaves is *when stdout has answered*, and non-empty is
        not the test. A pre-flight failure flushes the ``session`` header and
        dies (:func:`_never_started`), so the stream exists but knows nothing —
        and taking :func:`terminal_verdict`'s no-assistant-message fallback as an
        answer there is what would report a missing key as "run ended before any
        assistant message (last event: session, 1 events)" on the exit-1 path
        that is the only path Lane A has, with ``error: No API key found for
        openrouter.`` sitting unread one channel over. A stream that never
        started is therefore silent here, and stderr answers alone.

        That is also the one place this string deliberately differs from
        :meth:`parse_output`'s — which keeps the fallback and appends
        ``; stderr: …`` to it, where both halves are wanted and where
        ``error_contains`` grades them.

        **Diagnostics first — but the words are load-bearing.** Nothing here
        chooses a category; Lane A, however, classifies the string this sentence
        is composed into (``omp exited with code 1: <this>``) rather than the
        streams, so :func:`_named_for_the_ladder` puts the shared tables' own
        word in front of the denial, the deadline and the 5xx ``error``. The
        verdict is still :meth:`classify_failure`'s; this only keeps it from
        being lost in transit.
        """
        if _never_started(stdout):
            return stderr_diagnosis(stderr) or None
        verdict = terminal_verdict(stdout, stderr)
        if verdict:
            return verdict
        diagnosis = stderr_diagnosis(stderr)
        return diagnosis or None

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """The terminal message's own words, and **nothing earlier**.

        Dropping the user-role events and ``agent_end`` (which repeats the whole
        conversation, our prompt included) is necessary — otherwise every marker
        table runs against ``prompts/plan_review.txt`` — but it is not
        sufficient. A tool result is our own data handed back to us: a reviewer
        that ``read``s a plan quoting ``401 User not found.`` carries every auth
        marker inside a ``tool_execution_end``, and under ``classify_streams``'s
        fixed order (auth before rate limit before timeout) that quoted 401 would
        outrank the real 429 that ended the run — ``auth_failed``, no retry, the
        whole batch failed on a marker the vendor never emitted.

        So the reduction keeps exactly what omp itself wrote as a verdict: the
        terminal message's ``errorMessage`` when its ``stopReason`` is ``error``,
        ``aborted`` or an unrecognized enum (a vendor sentence is the vendor's
        whatever the enum), and **nothing** on a ``stop`` or a ``toolUse``-final
        stream, both of which are decided structurally in
        :meth:`classify_failure`. ``""`` there is the accurate reduction of "omp
        reported no error", not a swallowed one — the contract's "never ``''``"
        clause is about a *failed* parse, and on a failed parse (a banner, a
        non-JSONL stdout) this returns its input unchanged, as required.

        stderr is passed through untouched: the pre-flight failures are plain
        text there over a 0-byte stdout, and ``Model "…" not found``, ``No API
        key found for`` and ``CliUsageError`` (18.2.2) / ``Unknown tool in
        --tools`` (18.8.3) reach their tables exactly as before.

        Tool results and earlier assistant turns are **retained for diagnostics,
        not classification**: ``_attach_stdout_excerpt`` puts the raw stdout on
        ``details.stdout_excerpt``, ``_save_log`` writes it in full, and
        ``_format_failure_details``' stdout tail is cut from the raw stream. This
        hook is applied inside :meth:`classify_failure` (to classify) and, for
        the failure reason's quote only, by the executor's
        ``_classify_failed_run`` (see the base docstring); neither writes the
        reduced text anywhere a human reads instead of the raw stream, so
        narrowing it removes no byte from anything a human reads.
        """
        events, _junk = _events(stdout)
        if not events:
            return stdout, stderr
        messages = _assistant_ends(events)
        if not messages:
            return "", stderr
        final = messages[-1]
        reason = final.get("stopReason")
        if reason in ("stop", "toolUse"):
            return "", stderr
        return _one_line(str(final.get("errorMessage") or "")), stderr

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The last assistant message's answer text, never the event stream.

        omp's JSONL is a transport: every assistant ``message_end`` carries a
        ``content`` array, and a ``--max-time`` cut leaves an exit-0
        ``toolUse``/``aborted`` stream whose ``thinking``/``toolCall`` parts the
        salvage gate would otherwise accept as findings. The reader is pi's
        (:func:`~utils.providers.pi_family_stream.assistant_text_of_stream`),
        under :data:`OMP_DIALECT`; ``None`` for a non-empty stdout that is not
        an omp stream at all keeps the caller's old input. An empty or
        whitespace-only stdout is ``""``, a final verdict: ``--mode json`` is a
        required flag, so no bytes means the transport carried nothing
        (``invalid-model``, a slot killed before omp printed), and stderr's
        diagnostics must not reach the gate in its place.
        """
        return assistant_text_of_stream(stdout, OMP_DIALECT)

    def classify_failure(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[str]:
        """Structural first, the declared tables second.

        ``Command aborted`` is deliberately not a marker, so ``classify_streams``
        alone would answer ``None`` for the ``toolUse``-final shape — rendered
        ``Reason: Unknown`` and offered a transport retry the ladder then
        declines for lack of time. And the stub's 500 sentence matches no shared
        server-error marker, so the ``stdout-error`` row would classify ``None``
        too. Both are read here instead, off the parsed **stdout** — the raw
        JSONL, not the reduced haystack :meth:`vendor_text` builds for the
        fall-through.

        The order matters: a denial before a deadline, so a run that was both
        denied and cut is reported as the non-retryable half. ``permission_denied``
        then reaches a ladder **under its own name**:
        ``_LADDER_STATUS_BY_CATEGORY`` (in ``utils/review_orchestrator_base.py``)
        translates only ``connection_error`` and ``server_error`` into a ladder
        status, and everything it does not map falls through
        :meth:`RetryLadder.record`'s last branch to ``retry=False,
        "permission_denied is never retried"``. One dispatch, then the slot ends —
        which is right, because no retry fixes a policy failure. That pair is
        cited rather than ``RETRYABLE_FAILURE_CATEGORIES`` on purpose: the
        frozenset has had no live consumer since the guard that read it was
        deleted (the comment above ``_LADDER_STATUS_BY_CATEGORY`` records the
        deletion), so naming it would send a reader to a constant that decides
        nothing.

        **Which ladder reads this method, and which reads the sentence.** The
        Lane B executor and ``_format_failure_details`` call it. Lane A's
        file-output lane does not: it classifies ``str(result["error"])``
        through ``classify_streams``, so what reaches that ladder is whatever
        :func:`terminal_verdict` wrote. :func:`_named_for_the_ladder` is what
        keeps the two agreeing — the denial, the ``toolUse``/``aborted``
        deadline and the 5xx ``error`` each carry the shared tables' own word in
        the sentence, so Lane A lands on the same rung off the string that this
        method reaches off the stream. Without it the exit-0 cut review
        classified ``None`` (never retried) while the ``aborted`` half of the
        same ``--max-time`` took rung 2, and the 500's structural
        ``server_error`` never became the transport retry it names.

        Anything the structural read has no branch for — including an
        unrecognized ``stopReason`` — falls through to the declared tables over
        :meth:`vendor_text`, which on a parsed stream is the terminal message's
        own sentence plus stderr and nothing earlier. A bare rename answers
        ``None``, transport-shaped; the ladder's bounded transport retries then
        end the slot with the same named error, which is accepted over inventing
        a new non-retryable category for a shape nobody has seen.
        """
        events, _junk = _events(stdout)
        if events:
            messages = _assistant_ends(events)
            if _denied(_tool_ends(events)) is not None:
                return CATEGORY_PERMISSION_DENIED
            if messages:
                final = messages[-1]
                reason = final.get("stopReason")
                if reason == "aborted" or reason == "toolUse":
                    return STATUS_TIMEOUT
                if reason == "error":
                    status = final.get("errorStatus")
                    if isinstance(status, int):
                        if status in (401, 403):
                            return STATUS_AUTH_FAILED
                        if status == 429:
                            return STATUS_RATE_LIMITED
                        if 500 <= status < 600:
                            return CATEGORY_SERVER_ERROR
        return super().classify_failure(stdout, stderr, exit_code)

    def parse_usage(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """Sum ``usage`` over every assistant ``message_end`` — one per API call.

        A run with tool calls has one assistant message per call, so a multi-turn
        review reports the whole dispatch rather than its last turn. An absent
        block leaves the key **absent**, never 0: a zero would average into
        per-phase totals and read as a free run.

        ``cost_usd`` is priced from omp's own model catalog, not read back from
        the vendor — it is an estimate, and every renderer labels it "est.".

        **An overflowed run under-counts by its summarization calls.** MEASURED
        (T7.15, 2026-09-25, container omp 18.2.11,
        ``tests/fixtures/omp/compaction-summarized``): after a 400 context-length
        omp tries ``shake`` (drops tool output, no model call) and, when that
        finds nothing, ``context-full`` — which made **two** summarization
        requests (``max_tokens`` 8192 and 512) whose usage omp drops:
        ``auto_compaction_end.result`` is ``{summary, shortSummary,
        firstKeptEntryId, tokensBefore, details}`` and no assistant
        ``message_end`` carries them. So that row reports 8 requests' worth of
        work minus 2 (here 1800 input / 80 output tokens short). Nothing else is
        missing, so ``USAGE_FULL`` stands, and :data:`OMP_DIALECT` keeps its
        compaction leg off — there is no ``result.usage`` to add. (pi's
        ``compaction_end.result.usage`` does exist and pi's dialect counts it.)
        """
        events, _junk = _events(stdout)
        if not events:
            return None
        return sum_usage(events, OMP_DIALECT)

    # ── environment ──────────────────────────────────────────────────────
    def get_env(self, model: str) -> Dict[str, str]:
        """``OMP_SKIP_SETUP`` plus the OpenRouter key, re-emitted **conditionally**.

        The setup wizard is skipped in print mode anyway; the pin makes that not
        depend on omp.

        The credential is the part that matters. Under ``env_allowlist: on``
        nothing in omp's profile admits ``OPENROUTER_API_KEY`` — the allowlist
        requires a credential to start with the adapter's own prefix, and omp's
        prefix family is ``PI_``/``OMP_`` — so the one auth source measured as
        "the env alone works" would be silently dropped and omp would fall
        through its ``$env`` chain to a file, or exit 1. Re-emitting it here is
        the route kimi, qwen and copilot already take to carry the OpenRouter key
        past the filter; omp's own spelling happens to be the variable's real
        name. ``build_child_env`` applies this delta **after** the allowlist, so
        the value survives ``on``; under ``off`` it overwrites the inherited
        value with itself.

        **Conditional, not ``os.environ.get(name, "")``.** An injected empty
        string would be *present and wrong* to omp's chain and would shadow the
        ``~/.omp/agent/.env`` source a user with no exported key relies on.
        """
        env = {"OMP_SKIP_SETUP": "1"}
        key = os.environ.get(OMP_CREDENTIAL_ENV)
        if key:
            env[OMP_CREDENTIAL_ENV] = key
        return env

    def resolve_env(
        self,
        model: str,
        profile: str = PROFILE_GENERATE,
        *,
        credential_helper: Optional[str] = None,
        base_env: Optional[Any] = None,
        anchor: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> Dict[str, str]:
        """:meth:`get_env`, but sourcing the credential from ``base_env``.

        ``get_env`` takes no environment and therefore has to read
        ``os.environ`` — which is what every adapter that re-emits a credential
        does, and what is correct at the one production call site, where
        ``base_env`` is ``None`` and ``os.environ`` *is* the source. It is not
        correct for a caller that composes a child env from a source of its own
        (the container wrapper, a test): reading the process environment there
        would carry a value the child was never going to inherit, or miss one it
        was. This override is the only hook that sees both, so the pass-through
        is a pass-through of the composed source when there is one.
        """
        env = super().resolve_env(
            model, profile, credential_helper=credential_helper,
            base_env=base_env, anchor=anchor, cwd=cwd,
        )
        if base_env is not None:
            key = (base_env or {}).get(OMP_CREDENTIAL_ENV)
            if key:
                env[OMP_CREDENTIAL_ENV] = key
            else:
                env.pop(OMP_CREDENTIAL_ENV, None)
        return env

    def get_remove_env(
        self,
        anchor: Optional[str] = None,
        base_env: Optional[Any] = None,
    ) -> List[str]:
        """Strip the foreign vendor keys — "adapter wins, ambient loses".

        This is what closes the measured hazard on a **default** install, not the
        env allowlist: that ships ``off`` (``ENV_ALLOWLIST_DEFAULT``) and is a
        second layer only for a user who turns it on. With the filter off
        ``build_child_env`` is the source environment plus this adapter's delta
        minus these removals, so without this list a stray ``GEMINI_API_KEY``
        reaches omp on every dispatch.
        """
        return list(_STRIPPED_VENDOR_VARS)
