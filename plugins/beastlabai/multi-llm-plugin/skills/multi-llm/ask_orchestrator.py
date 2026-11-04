#!/usr/bin/env python3
"""
Ask orchestrator: a lightweight, read-only Q&A side-channel for the multi-llm skill.

Unlike the review/implement orchestrators, this mode does NOT force model output
into a JSON suggestion schema and does NOT group/validate/consolidate. It takes a
plan file plus a free-text question, fans the question out to each configured LLM
with the plan inlined as read-only context, captures each model's raw markdown
answer, and aggregates the answers into a single ``answers.md`` file.

Output layout (per question):
    {plan}/ask/<slug>-<hash8>/
    ├── answers.md            # aggregated markdown answers (regenerated each run)
    ├── answer_<model>.md     # per-model raw markdown answer
    ├── origin_<model>.txt    # how that answer was obtained: file | stdout |
    │                         #   fallback | accepted (one word; D7.1)
    ├── partial_<model>.md    # text a FAILED run left (not counted; only
    │                         #   --accept-partial <model> counts it; D3.2)
    ├── log_<model>.txt       # per-model provider debug log (bounded; never
    │                         #   read back as an answer)
    ├── error_<model>.log     # per-model error log (only on failure)
    └── .status.json          # resume detection + collision/freshness guard

``<model>`` is always ``sanitize_model_name(spec)``, the one stem every file of a
model shares (plans/ask-answer-recovery-and-false-success.md D3.2).

A slot counts as answered only when its run ended by itself at exit 0 with a
finished answer (D3.1): a non-empty answer file (step 1), else the adapter's
reduced answer text (step 2, ``details["answer_text"]``, D2.3). A run that timed
out, exited non-zero or reported an incomplete answer is failed whichever channel
carried its text, and that text is kept as ``partial_<model>.md`` (D3.2, D3.3).

Slug-collision semantics (see ``slugify_question``):
- **Same question text → same slug → same dir → resume** (deliberate sharing):
  existing per-model answers are reused and ``answers.md`` is regenerated.
- **Different question text → different slug → different dir** (no sharing):
  because ``<hash8>`` derives from the full original question, two different
  questions cannot normally share a directory, so there is no silent
  answer-mixing.
- **Astronomically-unlikely hash + prefix collision → suffixed sibling dir**
  (``<slug>-2/``), never a silent overwrite: the verbatim-question guard
  (``.status.json`` ``question`` field) catches a stored question that differs
  byte-for-byte from the current one and routes to a sibling directory instead
  of regenerating another question's ``answers.md``.

No ``state.json`` phase tracking — ask is a read-only side-channel, not a
workflow phase.
"""

import argparse
import asyncio
import contextlib
import hashlib
import json
import os
import shlex
import sys
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.stream_bootstrap import bootstrap_streams
from utils import cli_common
from utils.cli_common import (
    build_parent_parser,
    dispatcher_prefix,
)
from utils.output_handler import get_phase_dir, slugify_question
from utils.prompt_loader import load_prompt
from utils.interactive import resolve_models
from utils import unattended as unattended_mod
from utils.unattended import NeedsHuman
from utils.provider_registry import (
    get_all_model_specs,
    get_provider,
    get_provider_timeout,
    is_model_valid,
    parse_model_spec,
    set_run_anchor,
)
# ``looks_like_ndjson`` lives in ``utils.json_extractor`` (D2.2/T2.3) so
# ``utils.llm_client`` can reach it; re-exported here for this module's callers
# and its tests.
from utils.json_extractor import looks_like_ndjson, sanitize_model_name  # noqa: F401
from utils.llm_client import ERROR_PARSE_ERROR, invoke_with_provider
from utils.git_utils import get_project_root
from utils import process_control
from utils.detach import (
    VERDICT_RUNNING,
    VERDICT_STALE,
    VERDICT_STARTING,
    classify_run,
    lock_path,
    record_output_files,
    report_progress,
)
from utils.progress_tracker import FanoutProgress, PhaseProgress
from utils.readonly_audit import combine_audits
from utils.review_orchestrator_base import (
    backfill_deadline_losses,
    boundaryless_sibling_count,
    bypass_stream_audit_clears,
    bypass_write_not_attributed,
    bypass_write_violation,
    fanout_ignore_prefixes,
    flip_map_entries_to_done,
    maybe_detach,
    # Plan codex-sandbox-unavailable §6 F1 (2026-09-30): a slot on the
    # plugin's own jail runs the mode check and the home check instead of the
    # porcelain check.
    mode_check_applies,
    mode_snapshot,
    porcelain_check_applies,
    porcelain_snapshot,
    print_closing_summary,
    read_plan,
    report_jail_outcome,
    run_incidental_checks,
    run_models_concurrent,
    sandbox_fallback_kwargs,
    sandbox_refusal,
    unexpected_writes,
    update_status,
    write_status,
)

# Prompt template filename
ASK_PROMPT_FILE = "ask.txt"

# Conservatively below Linux MAX_ARG_STRLEN (~128 KB) so the rendered prompt,
# delivered as a single argv element, never fails with E2BIG. Leaves headroom
# for the rest of the template.
MAX_INLINE_PLAN_BYTES = 100 * 1024

# Hard ceiling for the fully-rendered prompt (delivered as one argv element).
# Conservatively below Linux MAX_ARG_STRLEN (~128 KB). The plan-inlining guard
# (MAX_INLINE_PLAN_BYTES) only measures plan_content; this catches the case where
# the question (or other template fields) push the rendered prompt over the argv
# ceiling even when the plan itself is small, which would otherwise fail E2BIG.
MAX_PROMPT_BYTES = 124 * 1024


# ---------------------------------------------------------------------------
# Question input resolution
# ---------------------------------------------------------------------------

def resolve_question(args: argparse.Namespace) -> str:
    """Resolve the verbatim question from exactly one of the mutually-exclusive
    inputs (``--question`` / ``--question-file`` / ``--question-env``).

    The resolved question is the **verbatim original text** — no shell
    processing, no re-quoting, no stripping — so that all three sources yield
    byte-identical results and the slug/hash and stored ``question`` key use the
    exact original string.
    """
    if args.question is not None:
        return args.question
    if args.question_file is not None:
        try:
            with open(args.question_file, "r", encoding="utf-8") as f:
                return f.read()
        except (OSError, IOError) as e:
            print(f"ERROR: could not read --question-file '{args.question_file}': {e}")
            sys.exit(1)
    if args.question_env is not None:
        value = os.environ.get(args.question_env)
        if value is None:
            print(f"ERROR: --question-env '{args.question_env}' is not set in the environment")
            sys.exit(1)
        return value
    # argparse(required=True) on the group guarantees one of the above.
    print("ERROR: no question provided")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Plan helpers
# ---------------------------------------------------------------------------

def compute_plan_hash(plan_content: str) -> str:
    """Return the first 12 hex chars of sha1 over the plan content."""
    return hashlib.sha1(plan_content.encode("utf-8")).hexdigest()[:12]


def build_inline_plan(plan_content: str, plan_path: str) -> Tuple[str, bool]:
    """Return (content_for_prompt, truncated).

    Inlines the full plan when it fits under :data:`MAX_INLINE_PLAN_BYTES`.
    Above the threshold, truncates the inlined copy and appends a clear marker
    pointing at ``plan_path`` (agentic providers can still read the full file
    from disk; the path is always present in the prompt). This is a documented,
    recoverable degradation rather than a hard ``E2BIG`` failure.
    """
    encoded = plan_content.encode("utf-8")
    if len(encoded) <= MAX_INLINE_PLAN_BYTES:
        return plan_content, False
    truncated = encoded[:MAX_INLINE_PLAN_BYTES].decode("utf-8", errors="ignore")
    marker = (
        f"\n\n[... plan truncated at {MAX_INLINE_PLAN_BYTES // 1024} KB; "
        f"read the full plan at {plan_path} ...]\n"
    )
    return truncated + marker, True


# ---------------------------------------------------------------------------
# The two per-model fields of ``prompts/ask.txt``
#
# Same decision as the three JSON review prompts', taken the same way: from the
# adapter's declared
# :attr:`~utils.providers.base.LLMProvider.supports_file_output` rather than from
# a provider name spelled out in this orchestrator
# (:func:`utils.llm_client.render_output_location` is the review-side twin). The
# wording cannot be shared with that function's constants — those ask for a raw
# JSON array and ask mode's answer is markdown — but the roster, the rule and
# the unknown-provider posture are the same one: an adapter this build no longer
# ships renders the file variant, which is what this template did unconditionally
# before the fields existed.
#
# The shipped adapters that declare ``supports_file_output = False`` were being
# told to write a file they can only answer with a refusal sentence. Nothing
# downstream moves: step 2 of ``ask_one`` reads their stdout answer — the
# adapter's reduced ``answer_text``, never the bounded log (plans/ask-answer-
# recovery-and-false-success.md D2.3) — and persists it to ``answer_path``, so
# ``source: "fallback"`` stays the measured outcome, aggregation still reads a
# file, and the origin record says ``stdout``, not a recovery (D7.1).
#
# The stdout variant is the shorter of the two on both fields, deliberately: the
# rendered template is the fixed overhead ``render_prompt_guarded`` subtracts
# from :data:`MAX_PROMPT_BYTES`, so this fix can only grow the question budget,
# never shrink it. ``tests/test_ask.py`` pins that as an assertion.
# ---------------------------------------------------------------------------

#: The read-only bullet for a file-capable adapter. Byte-identical to the text
#: the template carried inline before the field existed.
FILE_READONLY_WRITE_RULE = (
    "Do NOT modify, create, or delete any file except the single answer output\n"
    "  file specified below ({path}). In particular, NEVER edit the plan\n"
    "  file or any other file in the repository."
)

#: The same bullet for an adapter that cannot write: naming an exception for a
#: file the next section has just said not to write would contradict it.
STDOUT_READONLY_WRITE_RULE = (
    "Do NOT modify, create, or delete any file. In particular, NEVER edit the\n"
    "  plan file or any other file in the repository."
)

#: What a file-capable adapter is asked for. Byte-identical to the text the
#: template carried inline before the field existed, so the rendered prompt of
#: every adapter that declares ``supports_file_output`` is unchanged to the
#: character.
FILE_OUTPUT_LOCATION = (
    "## Output Location\n"
    "Write your answer as MARKDOWN (not JSON) to this exact absolute file path:\n"
    "\n"
    "{path}\n"
    "\n"
    "- Write to the path exactly as given above. Do NOT reinterpret, relativize, or\n"
    "  change it. It is an absolute path; write the file there.\n"
    "- Write ONLY your markdown answer to that file (no JSON wrapper, no code-fence\n"
    "  around the whole answer).\n"
    "- ALSO print your full answer to stdout. Stdout is the fallback that is used if\n"
    "  the file write fails, so the two should contain the same answer."
)

#: What an adapter that declares ``supports_file_output = False`` is asked for
#: instead: stdout is the channel it *does* have, it is the one step 2 of
#: ``ask_one`` reads (the reduced ``answer_text``, D2.3), and the answer lands in
#: exactly the same ``answer_<model>.md`` either way. Worded like
#: ``llm_client.STDOUT_OUTPUT_LOCATION``: "refused by the sandbox where one
#: runs", because a codex slot under the D6 fallback (``sandbox_fallback:
#: auto``, the default, 2026-09-17) runs with no sandbox and a write there
#: would succeed — the prompt may not claim otherwise.
STDOUT_OUTPUT_LOCATION = (
    "## Output Location\n"
    "Print your full answer to stdout as your final message, in MARKDOWN (not JSON).\n"
    "Do NOT write it to a file — this is a read-only task, and a file write is\n"
    "refused by the sandbox where one runs. Print the answer itself and nothing\n"
    "else: no JSON wrapper, no code-fence around the whole answer."
)


def render_output_fields(provider_name: Optional[str], output_md_path: str) -> Dict[str, str]:
    """The ``{readonly_write_rule}`` and ``{output_location}`` fields for
    ``provider_name``'s rendered ask prompt.

    ``provider_name`` is the already-resolved first half of the model spec (see
    :func:`~utils.provider_registry.parse_model_spec`); ``None`` — or a name this
    build ships no adapter for — renders the file variant, which is what every
    caller got before these fields existed.
    """
    provider = get_provider(provider_name) if provider_name else None
    if provider is not None and not provider.supports_file_output:
        return {
            "readonly_write_rule": STDOUT_READONLY_WRITE_RULE,
            "output_location": STDOUT_OUTPUT_LOCATION,
        }
    return {
        "readonly_write_rule": FILE_READONLY_WRITE_RULE.format(path=output_md_path),
        "output_location": FILE_OUTPUT_LOCATION.format(path=output_md_path),
    }


# ---------------------------------------------------------------------------
# The two plan fields of ``prompts/ask.txt``
# (plans/ask-answer-recovery-and-false-success.md D4.2)
#
# The same shape as the output fields above, read from the adapter's declared
# :attr:`~utils.providers.base.LLMProvider.wants_inline_plan`. An adapter that
# declares ``False`` passes the plan by another route, so an inlined body only
# duplicates it: aider attaches every absolute path its prompt names as a
# ``--read`` file, and the inlined body also fed aider's mention scan, which
# auto-added every repo path the plan named (1.08M tokens on 2026-09-26).
#
# The route is checked, not assumed: the path block is used only when the
# adapter's own extractor finds ``plan_path`` in the COMPLETE rendered prompt —
# the very string ``build_command`` receives — never in the block alone. A path
# ``_ABS_PATH_RE`` cannot match whole (a space, ``+`` or ``~``) would otherwise
# leave aider with no plan at all, and so would a question that names
# ``_MAX_READ_FILES`` existing absolute paths ahead of the plan block: the
# capped extractor stops before it reaches the plan path, so the block would
# claim an attachment the argv never carries. Either way it falls back to the
# inline block and costs only size.
# ---------------------------------------------------------------------------

#: The ``## Plan File`` body for an adapter that inlines the plan. Byte-identical
#: to the text the template carried inline before the field existed, so every
#: adapter that keeps ``wants_inline_plan = True`` gets the same prompt to the
#: character.
INLINE_PLAN_BLOCK = (
    "The full plan content is inlined below. The plan also lives on disk at this\n"
    "absolute path, which you may read directly for additional context if needed:\n"
    "\n"
    "{plan_path}\n"
    "\n"
    "If the inlined content below appears truncated (you will see a truncation\n"
    "marker), read the full plan from the path above.\n"
    "\n"
    "--- BEGIN PLAN CONTENT (read-only) ---\n"
    "{plan_content}\n"
    "--- END PLAN CONTENT (read-only) ---"
)

#: The template's closing section, byte-identical to the text it replaces. It
#: carries its own heading and leading blank line (the template writes
#: ``{output_location}{plan_size_note}`` on one line, so it also ends the line
#: above), and the empty note the path block pairs with leaves no stray heading
#: or blank line behind.
INLINE_PLAN_SIZE_NOTE = (
    "\n"
    "\n"
    "## Note on plan size\n"
    "The inlined plan content above may have been truncated if the plan is very large\n"
    "(roughly above 100 KB), because the prompt is delivered as a single command-line\n"
    "argument with an OS size limit. When you see a truncation marker, rely on the\n"
    "plan path above to read the remainder from disk."
)

#: The ``## Plan File`` body for an adapter that declares
#: ``wants_inline_plan = False``. It does not say "read it there": aider's
#: ``/ask`` has no file tool. "Above this message" is literal: aider 0.86.2
#: sends ``--read`` files as the ``readonly_files`` chunk, ahead of the current
#: message (``coders/chat_chunks.py:16-24``), so the read-only bullet's "the
#: plan content above" stays true without a change.
PATH_PLAN_BLOCK = (
    "The plan lives on disk at this absolute path: `{plan_path}`.\n"
    "Its full content is attached to this chat as a read-only file, above this message.\n"
    "It is not repeated here."
)


def _plan_route_carries(provider: Any, rendered_prompt: str, plan_path: str) -> bool:
    """True when ``provider``'s own path extractor attaches ``plan_path`` from
    ``rendered_prompt``.

    ``rendered_prompt`` must be the complete prompt, question first, exactly as
    ``build_command`` will receive it: the extractor is capped
    (``_MAX_READ_FILES`` for aider) and scans in order, so whether the plan path
    makes the cut depends on every path named ahead of it, and checking the
    block alone would miss a question that exhausts the cap.

    The extractor is the one ``build_command`` turns into ``--read`` arguments
    (for aider, :meth:`~utils.providers.aider.AiderProvider._extract_read_files`).
    An adapter with no extractor has no route this can see, so it keeps the
    inline block; ``tests/test_provider_housekeeping.py`` fails such a
    declaration by name.
    """
    extract = getattr(provider, "_extract_read_files", None)
    if extract is None:
        return False
    return plan_path in extract(rendered_prompt)


def _inline_plan_fields(plan_path: str, plan_content: str) -> Dict[str, str]:
    """The inline block and size note: every adapter's variant but a path-only
    one's, and a path-only adapter's fallback."""
    return {
        "plan_block": INLINE_PLAN_BLOCK.format(
            plan_path=plan_path, plan_content=plan_content
        ),
        "plan_size_note": INLINE_PLAN_SIZE_NOTE,
    }


def render_plan_fields(
    provider_name: Optional[str],
    plan_path: str,
    plan_content: str,
    render_complete: Callable[[Dict[str, str]], str],
) -> Dict[str, str]:
    """The ``{plan_block}`` and ``{plan_size_note}`` fields for
    ``provider_name``'s rendered ask prompt.

    ``wants_inline_plan = True``, ``None`` or a name this build ships no adapter
    for renders the inline block and size note, which is what every caller got
    before these fields existed. ``False`` renders :data:`PATH_PLAN_BLOCK` and
    an empty note, but only when the adapter's extractor finds ``plan_path`` in
    the complete prompt ``render_complete`` builds from those two fields — the
    string the adapter's ``build_command`` really sees; otherwise the inline
    block is the fallback. Each field is formatted here, before substitution,
    so braces in the plan pass through ``render_prompt``'s ``str.format``
    untouched.
    """
    provider = get_provider(provider_name) if provider_name else None
    if provider is not None and not provider.wants_inline_plan:
        fields = {
            "plan_block": PATH_PLAN_BLOCK.format(plan_path=plan_path),
            "plan_size_note": "",
        }
        if _plan_route_carries(provider, render_complete(fields), plan_path):
            return fields
    return _inline_plan_fields(plan_path, plan_content)


def _render_prompt(
    template: str,
    question: str,
    plan_path: str,
    plan_content: str,
    output_md_path: str,
    provider_name: Optional[str],
    *,
    force_inline_plan: bool = False,
) -> str:
    """:func:`render_prompt`, plus ``force_inline_plan`` for
    :func:`render_prompt_guarded`'s re-budget, which has to measure the inline
    block's overhead for an adapter that would otherwise get the path block."""
    output_fields = render_output_fields(provider_name, output_md_path)

    def render_complete(plan_fields: Dict[str, str]) -> str:
        return template.format(question=question, **plan_fields, **output_fields)

    if force_inline_plan:
        return render_complete(_inline_plan_fields(plan_path, plan_content))
    return render_complete(
        render_plan_fields(provider_name, plan_path, plan_content, render_complete)
    )


def render_prompt(
    template: str,
    question: str,
    plan_path: str,
    plan_content: str,
    output_md_path: str,
    provider_name: Optional[str] = None,
) -> str:
    """Render the ask prompt. Only template literals need ``{{`` escaping;
    substituted values (e.g. plan content with literal braces) pass through
    untouched because ``str.format`` only parses the template's own braces —
    which is also why the four per-model fields are formatted *before* they are
    substituted rather than by this call.

    ``provider_name`` selects the output-channel variant
    (:func:`render_output_fields`) and the plan variant
    (:func:`render_plan_fields`, checked against this complete prompt);
    omitted, the prompt asks for a file and inlines the plan.
    """
    return _render_prompt(
        template, question, plan_path, plan_content, output_md_path, provider_name
    )


def render_prompt_guarded(
    template: str,
    question: str,
    plan_path: str,
    plan_content: str,
    output_md_path: str,
    provider_name: Optional[str] = None,
) -> Tuple[str, bool]:
    """Render the ask prompt and guarantee the result stays under
    :data:`MAX_PROMPT_BYTES` (the single-argv ceiling), returning
    ``(rendered_prompt, prompt_truncated)``.

    :func:`build_inline_plan` only bounds ``plan_content``; a large question (or
    other template fields) can still push the *fully rendered* prompt over
    ``MAX_ARG_STRLEN`` and cause an ``E2BIG`` failure even when the plan is
    small. This measures the rendered prompt and, when oversized, truncates the
    question (the only remaining caller-controlled field) with a clear marker so
    the invocation still runs instead of hard-failing. ``plan_path`` and
    ``output_md_path`` are never truncated — the model needs them intact to read
    the full plan and write its answer.

    ``provider_name`` is threaded through to :func:`render_prompt` so the
    overhead measured here is the overhead of the variant actually dispatched —
    the stdout variant is the shorter of the two, so a read-only adapter's
    question budget can only be larger than a file-capable one's. The same holds
    for the plan: an adapter rendered the path block (D4.2) is measured without
    the inline body, which only grows its budget.

    That route is re-checked on every render against the complete prompt, so a
    kept question that still names enough existing absolute paths to exhaust
    the adapter's attachment cap flips the final render back to the inline
    block — which the path-block budget did not pay for. The second pass
    re-budgets against the inline block's overhead, so the ceiling holds
    whichever variant the final render lands on (the path block is always the
    shorter of the two).
    """
    rendered = render_prompt(
        template, question, plan_path, plan_content, output_md_path, provider_name
    )
    if len(rendered.encode("utf-8")) <= MAX_PROMPT_BYTES:
        return rendered, False

    # The fixed overhead is everything except the question. Compute how many
    # question bytes we can keep so the rendered prompt fits under the ceiling.
    marker = "\n\n[... question truncated to fit the argv size limit ...]"
    for force_inline_plan in (False, True):
        overhead = len(
            _render_prompt(
                template, marker, plan_path, plan_content, output_md_path,
                provider_name, force_inline_plan=force_inline_plan,
            ).encode("utf-8")
        )
        budget = MAX_PROMPT_BYTES - overhead
        if budget < 0:
            budget = 0
        q_bytes = question.encode("utf-8")[:budget]
        truncated_question = q_bytes.decode("utf-8", errors="ignore") + marker
        rendered = render_prompt(
            template, truncated_question, plan_path, plan_content, output_md_path,
            provider_name,
        )
        if len(rendered.encode("utf-8")) <= MAX_PROMPT_BYTES:
            break
    return rendered, True


def renders_inline_plan(
    template: str,
    question: str,
    plan_path: str,
    plan_content: str,
    output_md_path: str,
    provider_name: Optional[str] = None,
) -> bool:
    """True when the prompt :func:`render_prompt_guarded` dispatches to
    ``provider_name`` carries the inline plan block, and so the inlined copy of
    the plan.

    An adapter that inlines (``wants_inline_plan = True``, ``None`` or a name
    with no shipped adapter) always does. A path-only adapter (D4.2) does only
    when :func:`render_plan_fields` fell back to the inline block because its
    route cannot carry this plan path in this prompt, so its final render is
    checked rather than its declaration alone. ``main`` uses this to print the
    plan-truncation warning only when a truncated copy reaches some prompt.
    """
    provider = get_provider(provider_name) if provider_name else None
    if provider is None or provider.wants_inline_plan:
        return True
    rendered, _ = render_prompt_guarded(
        template, question, plan_path, plan_content, output_md_path, provider_name
    )
    return PATH_PLAN_BLOCK.format(plan_path=plan_path) not in rendered


# ---------------------------------------------------------------------------
# Answer capture helpers
# ---------------------------------------------------------------------------

def read_nonempty_answer(path: str) -> Optional[str]:
    """Return the answer file's content if it exists and is readable with
    non-whitespace content, else None.

    This is the single, consistent definition of "a usable answer file" used
    by resume, the live run and the disk scan, so an empty or unreadable file
    never counts as success. It checks content only: whether a file counts is
    decided by how the run that wrote it ended (D3.1, D3.3), because a file cut
    mid-write, an outline or a draft all pass this check. The same definition
    says whether a ``partial_<model>.md`` holds text.
    """
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            if text.strip():
                return text
    except (OSError, IOError):
        return None
    return None


def recover_answer_text(
    result: Dict[str, Any], answer_text: Optional[str] = None
) -> Optional[str]:
    """Recover a usable plain-text answer from a provider result, or None.

    **Once the caller has asked for the answer text, it is the only source**
    (plans/ask-answer-recovery-and-false-success.md D2.3). *answer_text* is
    ``details["answer_text"]`` from ``invoke_with_provider(...,
    want_answer_text=True)``: the adapter's reduced answer (its ``salvage_text``
    hook, else ``generic_answer_text``) taken from the **full** stdout, redacted,
    and capped at 1 MiB with the head kept (D2.2). A non-empty string is the
    answer. An empty one is a final "nothing to recover", and ``None`` comes back
    even when ``data`` or ``raw`` holds a string:

    - both bypass the redaction, the cap and the reducer's ``""`` verdict — pi and
      omp ``setdefault("raw", answer)`` on every clean parse, so reading ``raw``
      first would save their answers unredacted and uncapped;
    - on a failed parse ``raw`` is sometimes the answer and sometimes the whole
      transport, which is how grok's ``{"type":"error",…}`` body was once saved
      as an answer (§3.1).

    ``ask_one`` always asks, and passes the popped key (``""`` for a return that
    ran no child, which carries none).

    **When *answer_text* is ``None``** (a caller that did not ask), the legacy
    order applies: ``data`` when it is a non-empty string, then ``raw`` when it
    is a non-empty string that is not an NDJSON event stream. A ``dict``/``list``
    ``data`` is an extracted JSON fragment and never an answer.

    The per-model debug log is **never** a source (D2.1). Since ``2a44fdd`` it
    keeps only the last 20 lines of each stream, so reading it back as "the full
    stdout" saved 20-line tails as answers — and, because the truncation marker
    heads the kept lines, event streams that the NDJSON guard waved through.
    """
    if answer_text is not None:
        return answer_text if answer_text.strip() else None
    data = result.get("data")
    if isinstance(data, str) and data.strip():
        return data
    raw = result.get("raw")
    if isinstance(raw, str) and raw.strip() and not looks_like_ndjson(raw):
        return raw
    return None


def answer_finished(result: Any) -> bool:
    """D3.1's gate on steps 1 and 2: did the run end by itself at exit 0 with a
    finished answer?

    True for ``success`` True, or for ``error_code == PARSE_ERROR`` — the code
    ``invoke_with_provider`` stamps on *every* exit-0 ``success: False`` that
    carries none, which is how a prose answer with no JSON in it arrives (§3.1),
    so a gate on ``success`` alone would fail every such answer. In both cases the
    adapter must not have reported ``details["incomplete"]``: pi's ``stopReason:
    "length"`` exits 0 with no code on purpose (so the review lanes' file channel
    still looks for a findings file) and its text is a cut answer.

    Everything else — ``TIMEOUT``, ``SUBPROCESS_FAILED`` (a non-zero exit, or an
    adapter-declared hard failure at exit 0), a pre-spawn refusal — goes to step
    3, whatever text either channel carried (D3.3).
    """
    if not isinstance(result, dict):
        return False
    details = result.get("details")
    if (isinstance(details, dict) and details.get("incomplete")) or result.get("incomplete"):
        return False
    return bool(result.get("success")) or result.get("error_code") == ERROR_PARSE_ERROR


# ---------------------------------------------------------------------------
# Per-model files beside the answer: the origin record and the partial
# ---------------------------------------------------------------------------

#: D7.1's four origins — each the whole content of ``origin_<model>.txt``.
#: ``file``: step 1 read the answer file the model wrote. ``stdout``: step 2, for
#: an adapter declaring ``supports_file_output = False``, which the prompt asks
#: for stdout (its designed channel, never a recovery). ``fallback``: step 2 for
#: a file-capable adapter that was asked for the file and did not write it.
#: ``accepted``: ``--accept-partial`` counted a failed run's partial (D3.4).
ORIGIN_FILE = "file"
ORIGIN_STDOUT = "stdout"
ORIGIN_FALLBACK = "fallback"
ORIGIN_ACCEPTED = "accepted"
ORIGINS = (ORIGIN_FILE, ORIGIN_STDOUT, ORIGIN_FALLBACK, ORIGIN_ACCEPTED)

#: The one provenance line ``answers.md`` prints under each answer (D7.1).
#: ``{stem}`` is the model's sanitized file stem.
PROVENANCE_LINES = {
    ORIGIN_FILE: "_answer file written by the model_",
    ORIGIN_STDOUT: "_answered on stdout, as this adapter is asked to_",
    ORIGIN_FALLBACK: "_recovered from the model's stdout (it did not write the answer file)_",
    ORIGIN_ACCEPTED: (
        "_accepted by the operator from a run that failed "
        "(its error is in error_{stem}.log)_"
    ),
}

#: An answer with no record, or with a record holding anything but the four
#: words: a question dir written before D7.1, or a failed record write. Nothing
#: is inferred for it.
PROVENANCE_NOT_RECORDED = "_origin not recorded_"


def answer_file_path(question_dir: str, stem: str) -> str:
    """``answer_<stem>.md`` in the question dir."""
    return os.path.join(question_dir, f"answer_{stem}.md")


def partial_file_path(question_dir: str, stem: str) -> str:
    """``partial_<stem>.md``: the text a failed run left (D3.2).

    The stem is the same ``sanitize_model_name(spec)`` the answer, log and error
    files use, so one model's partial and answer can never get different names,
    and every reader and remover (dispatch, D3.3's move, the failed-model note,
    ``--accept-partial``) finds it through that one stem. ``collect_completed``
    and the resume skip never read this name, so a partial is never counted.
    """
    return os.path.join(question_dir, f"partial_{stem}.md")


def origin_file_path(question_dir: str, stem: str) -> str:
    """``origin_<stem>.txt``: how ``answer_<stem>.md`` was obtained (D7.1).

    Its own file, not ``.status.json``'s ``source``: that field says what *this
    run* did with the slot, and a resumed run rewrites every skipped model as
    ``source: "resume"`` — so an origin read from it would vanish after one
    resume.
    """
    return os.path.join(question_dir, f"origin_{stem}.txt")


def _write_atomically(path: str, text: str) -> None:
    """Write *text* to a temp file beside *path*, then ``os.replace`` it in.

    A reader never sees a half-written record or partial. Raises ``OSError``.
    """
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(
        dir=directory, prefix=f".{os.path.basename(path)}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def answers_on_stdout(provider_name: Optional[str]) -> bool:
    """Whether the ask prompt asks *provider_name* for its answer on stdout.

    The rule :func:`render_output_fields` picks the prompt variant by — the
    adapter's declared ``supports_file_output`` — read here so the origin step 2
    records always matches what the model was asked for (D7.1). ``False`` is
    asked for stdout; ``True``, or a name this build ships no adapter for, is
    asked for the file.
    """
    provider = get_provider(provider_name) if provider_name else None
    return provider is not None and not provider.supports_file_output


def remove_stale(path: str) -> None:
    """Remove a file the coming dispatch supersedes; a failure only warns."""
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"WARNING: could not remove stale {os.path.basename(path)}: {e}")


def write_origin(question_dir: str, model_spec: str, origin: str) -> bool:
    """Record *origin* for *model_spec*'s answer, atomically (D7.1).

    Written on success only, straight after the answer lands. A failed write
    prints a ``WARNING`` and never fails the slot: the answer still counts, and
    ``answers.md`` says its origin was not recorded.
    """
    path = origin_file_path(question_dir, sanitize_model_name(model_spec))
    try:
        _write_atomically(path, origin)
        return True
    except OSError as e:
        print(f"WARNING: could not record the origin of {model_spec}'s answer "
              f"({os.path.basename(path)}): {e}; it will read as not recorded")
        return False


def read_origin(question_dir: str, spec: str) -> Optional[str]:
    """The recorded origin of *spec*'s answer, or ``None`` for no valid record."""
    path = origin_file_path(question_dir, sanitize_model_name(spec))
    try:
        with open(path, "r", encoding="utf-8") as f:
            word = f.read().strip()
    except (OSError, UnicodeDecodeError):
        return None
    return word if word in ORIGINS else None


def provenance_line(question_dir: str, spec: str) -> str:
    """The one line ``answers.md`` prints under *spec*'s answer (D7.1).

    Read from the origin record alone — never from ``.status.json`` — so
    regeneration stays a function of the files on disk, and a resumed answer
    prints the line of the run that produced it.
    """
    origin = read_origin(question_dir, spec)
    if origin is None:
        return PROVENANCE_NOT_RECORDED
    return PROVENANCE_LINES[origin].format(stem=sanitize_model_name(spec))


def write_partial(question_dir: str, model_spec: str, text: str) -> Optional[str]:
    """Keep a failed run's stdout answer text as ``partial_<model>.md`` (D3.2).

    Evidence only: it is not counted, and resume re-asks the model. Returns the
    path, or ``None`` (with a ``WARNING``) when the write failed.
    """
    path = partial_file_path(question_dir, sanitize_model_name(model_spec))
    try:
        _write_atomically(path, text)
        return path
    except OSError as e:
        print(f"WARNING: could not keep {model_spec}'s partial text in "
              f"{os.path.basename(path)}: {e}")
        return None


def set_answer_file_aside(question_dir: str, model_spec: str, answer_path: str) -> bool:
    """Move a failed run's answer file to ``partial_<model>.md`` (D3.3).

    Nothing shows a file from a run that timed out or failed is finished — it can
    be cut mid-write, an outline, or a draft — so it is kept as evidence under a
    name the answer scan never reads. The file takes the partial's name over any
    stdout text the same run left: it is the channel the model was asked for.

    The file is the only copy of that text, so a failed move never deletes it
    (D3.2): its bytes are copied into ``partial_<model>.md``, else into
    ``error_<model>.log``, and the file is removed only once a copy has landed.
    With no copy anywhere it is left in place under a ``WARNING`` naming it.

    Returns whether the answer path no longer holds the file (moved, or copied
    and removed). ``False`` means it is still there, and the caller must keep
    the slot failed although the disk scan would read the file as an answer.
    """
    target = partial_file_path(question_dir, sanitize_model_name(model_spec))
    try:
        os.replace(answer_path, target)
        return True
    except OSError as e:
        print(f"WARNING: could not move {model_spec}'s answer file from a failed "
              f"run to {os.path.basename(target)}: {e}")
    name = os.path.basename(answer_path)
    kept_in = _copy_answer_file_aside(question_dir, model_spec, answer_path, target)
    if kept_in is None:
        print(f"WARNING: {name}, from {model_spec}'s failed run, could not be "
              "copied anywhere either, so it was left in place rather than "
              "deleted: it is the only copy of that text. The slot stays failed; "
              "move the file aside by hand before a resume, which would count it "
              "as an answer.")
        return False
    try:
        os.remove(answer_path)
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"WARNING: copied {name} into {kept_in} but could not remove it: "
              f"{e}. The slot stays failed; remove the file by hand before a "
              "resume, which would count it as an answer.")
        return False
    print(f"  {model_spec}: kept a copy of {name} in {kept_in} and removed it")
    return True


def _copy_answer_file_aside(
    question_dir: str, model_spec: str, answer_path: str, target: str
) -> Optional[str]:
    """Copy a failed run's answer file whose move failed; name where it landed.

    ``partial_<model>.md`` first (atomically, so it is whole or absent), then
    appended to ``error_<model>.log``. ``None`` (with a ``WARNING`` per miss)
    when neither write succeeded, or the file could not be read at all.
    """
    try:
        with open(answer_path, "rb") as f:
            text = f.read().decode("utf-8", errors="replace")
    except OSError as e:
        print(f"WARNING: could not read {os.path.basename(answer_path)} to copy "
              f"it: {e}")
        return None
    try:
        _write_atomically(target, text)
        return os.path.basename(target)
    except OSError as e:
        print(f"WARNING: could not copy it to {os.path.basename(target)} "
              f"either: {e}")
    log = os.path.join(question_dir, f"error_{sanitize_model_name(model_spec)}.log")
    try:
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"\nAnswer file from the failed run "
                    f"({os.path.basename(answer_path)}), kept here because it "
                    f"could not be moved or copied to "
                    f"{os.path.basename(target)}:\n{text}\n")
        return os.path.basename(log)
    except OSError as e:
        print(f"WARNING: could not copy it into {os.path.basename(log)} "
              f"either: {e}")
        return None


def partial_note(spec: str, *, earlier: bool) -> str:
    """The failed-model line's tail naming a kept partial (D3.2, D3.4).

    ``earlier`` names it as an earlier run's: a slot that was never dispatched
    this run (the sandbox refusal) keeps whatever partial the last run left, and
    "always from the model's latest run" still holds because a refused slot is
    not a run.

    The spec is shell-quoted, so the printed command works pasted verbatim for a
    spec holding a space or another shell metacharacter; a plain spec prints
    unchanged.
    """
    stem = sanitize_model_name(spec)
    where = "partial text from an earlier run kept in" if earlier else "partial text kept in"
    return (f" — {where} partial_{stem}.md "
            f"(not counted; --accept-partial {shlex.quote(spec)} counts it)")


def failed_model_line(
    question_dir: str, spec: str, reason: str, earlier: Iterable[str] = ()
) -> str:
    """*reason*, plus :func:`partial_note` when the model has a partial on disk."""
    partial = partial_file_path(question_dir, sanitize_model_name(spec))
    if read_nonempty_answer(partial) is None:
        return reason
    return reason + partial_note(spec, earlier=spec in set(earlier))


def write_error_log(question_dir: str, model_spec: str, error: str, result: Dict[str, Any]) -> str:
    """Write a per-model error log (same convention as ``save_model_result``)."""
    sanitized = sanitize_model_name(model_spec)
    path = os.path.join(question_dir, f"error_{sanitized}.log")
    details = result.get("details", {}) if isinstance(result, dict) else {}
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Model: {model_spec}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Error: {error}\n")
            stderr_text = details.get("stderr") if isinstance(details, dict) else None
            if stderr_text:
                f.write(f"\nstderr:\n{stderr_text}\n")
    except (OSError, IOError):
        pass
    return path


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def demote_headings(text: str) -> str:
    """Shift every ATX markdown heading down one level (outside fenced code
    blocks), capping at level 6.

    Per-model answers commonly contain their own ``#``/``##`` headings. Demoting
    them keeps them strictly *below* the per-model ``# provider:model`` section
    header in ``answers.md`` so it stays unambiguous where one model's answer
    ends and the next begins. Headings inside fenced code blocks (e.g. shell
    comments) are left untouched.
    """
    import re as _re

    out: List[str] = []
    in_fence = False
    fence_marker: Optional[str] = None
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif fence_marker is not None and stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = None
            out.append(line)
            continue
        if not in_fence:
            m = _re.match(r'^(#{1,6})(\s.*)?$', line)
            if m and len(m.group(1)) < 6:
                out.append("#" + line)
                continue
        out.append(line)
    return "\n".join(out)


def collect_completed(
    question_dir: str, model_specs: List[str]
) -> List[Tuple[str, str]]:
    """Read-only scan of ``answer_<model>.md`` files.

    Returns the list of ``(spec, answer_text)`` pairs for models that produced
    a usable (non-empty) answer, in the resolved ``model_specs`` order. This is
    the file-based source of truth for which models succeeded, and lets callers
    derive ``completed`` without writing ``answers.md``.
    """
    sections: List[Tuple[str, str]] = []
    for spec in model_specs:
        sanitized = sanitize_model_name(spec)
        answer_path = os.path.join(question_dir, f"answer_{sanitized}.md")
        text = read_nonempty_answer(answer_path)
        if text is not None:
            sections.append((spec, text.strip()))
    return sections


def write_answers_md(
    question_dir: str,
    question: str,
    plan_path: str,
    model_specs: List[str],
    failed_models: Dict[str, str],
    timestamp: str,
    earlier_partials: Iterable[str] = (),
    withheld: Iterable[str] = (),
) -> Tuple[str, List[str]]:
    """Fully (re)generate ``answers.md`` from all current ``answer_<model>.md``
    files plus the failed-models map.

    Returns (answers_md_path, completed_specs). Section ordering is
    deterministic (the resolved ``model_specs`` order), so repeated
    regeneration over identical inputs is byte-identical. ``completed`` is the
    file-based source of truth for which models succeeded; ``failed_models``
    enumerates the rest.

    Each answer gets exactly one provenance line under its heading, read from
    its ``origin_<model>.txt`` and from nothing else (D7.1). Each failed model
    whose ``partial_<model>.md`` is on disk has the partial and the command that
    counts it named on its line (D3.2); *earlier_partials* are the failed specs
    this run never dispatched, whose partial is therefore an earlier run's.
    *withheld* are failed specs whose answer file from a failed run could not
    be set aside (:func:`set_answer_file_aside`): still on disk, never counted.
    """
    earlier = set(earlier_partials)
    withheld_set = set(withheld)
    sections = [
        (spec, text) for spec, text in collect_completed(question_dir, model_specs)
        if spec not in withheld_set
    ]
    completed: List[str] = [spec for spec, _ in sections]

    lines: List[str] = ["# Multi-LLM Ask", ""]
    lines.append("**Question:**")
    lines.append("")
    for q_line in question.split("\n"):
        lines.append(f"> {q_line}")
    lines.append("")
    lines.append(f"**Plan:** {plan_path}")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Models asked:** {', '.join(model_specs)}")
    lines.append(f"**Answered:** {len(completed)}/{len(model_specs)}")
    lines.append("")

    for spec, text in sections:
        lines.append("---")
        lines.append("")
        lines.append(f"# {spec}")
        lines.append("")
        lines.append(provenance_line(question_dir, spec))
        lines.append("")
        lines.append(demote_headings(text))
        lines.append("")

    if failed_models:
        lines.append("---")
        lines.append("")
        lines.append("## Failed Models")
        lines.append("")
        for spec in model_specs:
            if spec in failed_models:
                line = failed_model_line(
                    question_dir, spec, failed_models[spec], earlier
                )
                lines.append(f"- **{spec}**: {line}")
        lines.append("")

    answers_md = os.path.join(question_dir, "answers.md")
    with open(answers_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return answers_md, completed


# ---------------------------------------------------------------------------
# The closing report's answer counts (D7.2)
# ---------------------------------------------------------------------------

def answer_origins(
    question_dir: str, completed: List[str], produced: Iterable[str]
) -> Dict[str, Any]:
    """Count the answered models by origin record, once, for prose and field.

    ``{"answered", "file", "stdout", "fallback", "accepted", "unrecorded",
    "kept", "warn_all_fallback"}`` — the numbers of the counts line
    (:func:`answer_origins_line`) and the ``[WARN]``'s own predicate, so the
    prose and ``MULTI_LLM_RESULT.answer_origins`` cannot disagree
    (plans/ask-answer-recovery-and-false-success.md D7.2).

    - Counted by origin record (D7.1), never by this run's ``source``, so a
      resume of a run that met the warning's condition warns again.
    - ``kept``: answered models this invocation did not produce — *produced*
      is the set it did (a fan-out slot that returned ``file``/``fallback``, or
      a model ``--accept-partial`` just counted). On a fan-out those are the
      ``resume`` and ``not-dispatched`` slots.
    - ``warn_all_fallback``: at least one answer came from a file-capable
      adapter (origin ``file`` or ``fallback``), every one of those is
      ``fallback``, and no origin is unrecorded. ``stdout`` answers neither fire
      it nor keep it off (a stdout-only roster answers that way on every healthy
      run), ``accepted`` answers are outside the rule (they come from failed
      runs), and a run with no answers never warns.
    """
    produced_set = set(produced)
    counts: Dict[str, Any] = {
        "answered": len(completed),
        ORIGIN_FILE: 0,
        ORIGIN_STDOUT: 0,
        ORIGIN_FALLBACK: 0,
        ORIGIN_ACCEPTED: 0,
        "unrecorded": 0,
        "kept": 0,
    }
    for spec in completed:
        origin = read_origin(question_dir, spec)
        if origin is None:
            counts["unrecorded"] += 1
        else:
            counts[origin] += 1
        if spec not in produced_set:
            counts["kept"] += 1
    file_capable = counts[ORIGIN_FILE] + counts[ORIGIN_FALLBACK]
    counts["warn_all_fallback"] = bool(
        file_capable
        and counts[ORIGIN_FALLBACK] == file_capable
        and counts["unrecorded"] == 0
    )
    return counts


def answer_origins_line(origins: Dict[str, Any]) -> str:
    """The closing report's counts line, from :func:`answer_origins` (D7.2).

    The three origin buckets always print; the accepted and unrecorded buckets
    only when non-zero; together they add up to ``answered``. The ``kept``
    clause appears only when non-zero, so a host can tell how many answers this
    run produced itself.
    """
    parts = [
        f"{origins[ORIGIN_FILE]} from answer files",
        f"{origins[ORIGIN_STDOUT]} on stdout as asked",
        f"{origins[ORIGIN_FALLBACK]} recovered from stdout",
    ]
    if origins[ORIGIN_ACCEPTED]:
        parts.append(f"{origins[ORIGIN_ACCEPTED]} accepted from failed runs")
    if origins["unrecorded"]:
        parts.append(f"{origins['unrecorded']} origin not recorded")
    line = f"answered: {origins['answered']} ({', '.join(parts)}"
    if origins["kept"]:
        line += f"; {origins['kept']} kept from an earlier run"
    return line + ")"


def all_fallback_warning(origins: Dict[str, Any]) -> str:
    """The ``[WARN]`` printed when ``origins["warn_all_fallback"]`` is set."""
    n = origins[ORIGIN_FALLBACK]
    return (
        f"[WARN] none of the {n} answering model(s) asked to write an answer file "
        "wrote it; every one of those answers was recovered from stdout, so the "
        "answer-file channel is not working for this roster "
        "(answer_origins.warn_all_fallback)"
    )


# ---------------------------------------------------------------------------
# Question directory resolution (collision / resume guard)
# ---------------------------------------------------------------------------

def resolve_question_dir(phase_dir: str, slug: str, question: str) -> Tuple[str, bool]:
    """Resolve the per-question output directory, honoring the verbatim-question
    collision guard.

    Returns (dir_path, is_resume).
    - If the slug dir does not exist → fresh dir.
    - If it exists and its stored ``.status.json`` ``question`` byte-for-byte
      equals the current question (or no status is stored) → resume into it.
    - If it exists with a *different* stored question (astronomically-unlikely
      hash+prefix collision) → route to a suffixed sibling (``<slug>-2``, ...),
      never overwriting another question's answers.
    """
    base = os.path.join(phase_dir, slug)
    candidate = base
    n = 1
    while True:
        if not os.path.exists(candidate):
            return candidate, False
        if os.path.isdir(candidate):
            status_path = os.path.join(candidate, ".status.json")
            stored_q: Optional[str] = None
            if os.path.exists(status_path):
                try:
                    with open(status_path, "r", encoding="utf-8") as f:
                        stored_q = json.load(f).get("question")
                except (json.JSONDecodeError, OSError, IOError):
                    stored_q = None
            if stored_q is None or stored_q == question:
                return candidate, True
        # Different question (or a non-dir collision) → try a sibling.
        n += 1
        candidate = f"{base}-{n}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    try:
        available_models = get_all_model_specs()
    except FileNotFoundError:
        available_models = ["(providers.yaml not found - run with --models to specify)"]
    except Exception as e:
        available_models = [f"(config error: {type(e).__name__} - check providers.yaml)"]

    # Printed commands, so resolved from `__file__` and never a skill-dir
    # placeholder (see review_plan_orchestrator.parse_args for why).
    run = dispatcher_prefix()
    parser = argparse.ArgumentParser(
        description="Ask each configured LLM a free-text question about a plan",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[build_parent_parser()],
        epilog=f"""
Available models (provider:model format):
  {', '.join(available_models[:10])}{'...' if len(available_models) > 10 else ''}

Examples:
  {run} \\
    ask plans/my-plan.md "Is the rollback strategy sufficient?"

  # Question passed via a temp file (no question bytes transit the shell):
  {run} \\
    ask plans/my-plan.md --question-file /tmp/q.txt --quick
        """,
    )

    parser.add_argument(
        "--plan-file",
        required=True,
        help="Path to the implementation plan markdown file",
    )

    # The question is supplied via exactly one of three mutually-exclusive,
    # shell-safe mechanisms so user-controlled free text never has to be
    # interpolated into a shell command line.
    qgroup = parser.add_mutually_exclusive_group(required=True)
    qgroup.add_argument(
        "--question",
        default=None,
        help="The question as a single argv value (caller controls quoting)",
    )
    qgroup.add_argument(
        "--question-file",
        default=None,
        help="Read the verbatim question from a file (preferred shell-safe mechanism)",
    )
    qgroup.add_argument(
        "--question-env",
        default=None,
        help="Read the verbatim question from the named environment variable",
    )

    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="List of models in provider:model format (bare names use default provider)",
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Use quick_models from providers.yaml (lightweight)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Override timeout per model in seconds (default: per-provider timeout)",
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=5,
        help="Maximum number of parallel model invocations (default: 5)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass resume guards (e.g. act on a stale-plan warning); already-answered "
             "models are kept and only missing answers re-run. For a full re-ask of every "
             "model, also pass --rerun-all.",
    )
    parser.add_argument(
        "--rerun-all",
        action="store_true",
        help="Re-run every model from scratch, discarding any existing per-model result files "
             "(default: resume — skip models that already have results).",
    )
    # D3.4: the one way a failed run's text is counted. Dispatches nothing.
    parser.add_argument(
        "--accept-partial",
        nargs="+",
        default=None,
        metavar="MODEL",
        help="Count each named model's partial_<model>.md — the text a failed run "
             "left — as its answer, then regenerate answers.md. Dispatches nothing; "
             "refuses (changing nothing) unless every named model has a partial and "
             "no answer, while this question's run is still running, and with "
             "--detach (it runs in the foreground only).",
    )

    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# The closing report, shared by the fan-out and --accept-partial
# ---------------------------------------------------------------------------

class ProviderCall:
    """One slot's ``invoke_with_provider``, on a worker thread the fan-out cannot stop.

    ``ask_one`` hands the call to ``asyncio.to_thread``. The fan-out's deadline
    cancels the coroutine awaiting it, never the thread or the CLI that thread
    waits on, so this records where the call is: one still running must be
    stopped and joined before the closing report moves anything; one that
    finished, or that a worker never picked up, has nothing left to write.
    """

    _PENDING, _RUNNING, _FINISHED, _ABANDONED = "pending", "running", "finished", "abandoned"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = self._PENDING
        self.finished = threading.Event()

    def run(self, func: Any, /, **kwargs: Any) -> Any:
        with self._lock:
            if self._state == self._ABANDONED:
                return None  # abandoned before a worker reached it: never dispatched
            self._state = self._RUNNING
        try:
            return func(**kwargs)
        finally:
            with self._lock:
                self._state = self._FINISHED
            self.finished.set()

    def abandon(self) -> bool:
        """Retire the call; ``True`` when it is still running and must be joined."""
        with self._lock:
            if self._state == self._PENDING:
                self._state = self._ABANDONED
            return self._state == self._RUNNING


async def stop_unreturned_provider_calls(
    provider_calls: Dict[str, ProviderCall], *, poll_s: float = 0.05
) -> List[str]:
    """Stop, then join, every provider call still running after the fan-out.

    Only a slot the deadline cut can leave one (a returned slot awaited its
    call to the end), and its CLI can still create or rewrite
    ``answer_<model>.md``. Left running past :func:`set_aside_unreturned_answers`,
    that file would sit at the canonical path and the next resume would skip
    the model as answered. Every slot has returned or been cancelled by now, so
    every Lane A CLI still in ``process_control.live_cli_registry`` belongs to
    such a call and the whole registry is swept; a stopped CLI returns, and its
    ``invoke_with_provider`` with it. Should a CLI outlive the sweep, its own
    timeout still ends the call, so the join is bounded. Returns the specs
    joined.
    """
    running = [spec for spec, call in provider_calls.items() if call.abandon()]
    if not running:
        return []
    print(f"[DEADLINE] stopping {len(running)} provider call(s) the fan-out's "
          f"deadline cut, before their answer files are set aside: "
          f"{', '.join(running)}")
    process_control.sweep_live_clis("DEADLINE_SWEEP")
    while not all(provider_calls[spec].finished.is_set() for spec in running):
        await asyncio.sleep(poll_s)
    return running


def set_aside_unreturned_answers(
    question_dir: str,
    model_specs: List[str],
    results: Dict[str, Any],
    dispatched: Iterable[str],
    left_in_place: Optional[Set[str]] = None,
) -> List[str]:
    """D3.3 for the slots the fan-out's deadline cut: answer file → partial.

    A slot the deadline cancelled (or one that raised) has no result, so step 1
    never judged its file; the scan would otherwise count it and the reconcile
    step drop its failure. Only a spec ``ask_one`` dispatched this run is
    touched: a spec still queued at the deadline never ran, and the answer an
    earlier run left for it is not this run's to demote (the same rule the
    sandbox refusal follows). Returns the specs whose file moved; a spec whose
    file could not be set aside is added to *left_in_place*, which the caller
    keeps out of the scan.

    The move is made once, so it must follow
    :func:`stop_unreturned_provider_calls`: a cut slot's CLI still running
    after it could create or rewrite the answer file at the canonical path.
    """
    dispatched_set = set(dispatched)
    moved: List[str] = []
    for spec in model_specs:
        if spec in results or spec not in dispatched_set:
            continue
        path = answer_file_path(question_dir, sanitize_model_name(spec))
        if read_nonempty_answer(path) is None:
            continue
        if set_answer_file_aside(question_dir, spec, path):
            moved.append(spec)
        elif left_in_place is not None:
            left_in_place.add(spec)
    return moved


def reconcile_failed_map(
    model_specs: List[str], completed: Iterable[str], failed_models: Dict[str, str]
) -> None:
    """Step 3 of the failed map: reconcile it against the disk scan, in place.

    The scan is this lane's source of truth for "answered". A spec with a file
    is completed whatever its result said; a spec with neither a file nor a
    reason claimed success and wrote nothing, which keeps the sentence that has
    always described it.
    """
    completed_set = set(completed)
    for spec in model_specs:
        if spec in completed_set:
            failed_models.pop(spec, None)
        elif spec not in failed_models:
            failed_models[spec] = "No answer produced (model did not complete)"


def ask_run_state(completed: List[str], failed_models: Dict[str, str]) -> str:
    """The run's ``.status.json`` ``state`` from the disk scan (D7.2's table).

    Every model answered → ``completed``; some → ``partial``; none → ``failed``.
    The mapping is unchanged; D3.1 and D3.3 only change its input, so a run
    whose every slot timed out or failed is ``failed`` (exit 3).
    """
    if completed and not failed_models:
        state = "completed"
    elif completed:
        state = "partial"
    else:
        state = "failed"
    return state


def close_ask_run(
    *,
    question_dir: str,
    question: str,
    plan_path: str,
    model_specs: List[str],
    completed: List[str],
    failed_models: Dict[str, str],
    earlier_partials: Iterable[str],
    answers_md: str,
    state: str,
    produced: Iterable[str],
    unattended: bool,
    retry_flags: List[str],
    progress: Optional[Dict[str, Any]] = None,
) -> int:
    """Record and print the outcome of an ask run; return its exit code.

    ``answer_origins`` (D7.2) is computed once, from the origin records, and is
    what both the counts line and the ``[WARN]`` print from, what goes to
    ``.status.json`` in the same ``update_status`` as ``state`` (so ``detach``'s
    run view and a pinned ``status --view run`` restate it), and what rides the
    live ``MULTI_LLM_RESULT``. It is present on every ask run that reaches this
    point, a zero-answer one included, and never moves the exit code: an
    all-fallback run is still ``done`` or ``partial``, exit 0.

    *progress*, when given, joins that same write: ``--accept-partial`` passes
    the accepted models' rows, so the ``progress`` table never disagrees with
    ``models_completed`` beside it. ``progress`` merges one level deep, so a
    ``models`` key must carry the whole map.
    """
    origins = answer_origins(question_dir, completed, produced)
    updates: Dict[str, Any] = {
        "state": state,
        "models_completed": completed,
        "models_failed": failed_models,
        "answers_md": answers_md,
        "answer_origins": origins,
    }
    if progress:
        updates["progress"] = progress
    update_status(question_dir, updates)
    cli_common.record_answer_origins(origins)

    print("")
    print(f"Ask complete: {len(completed)}/{len(model_specs)} models answered "
          f"({len(failed_models)} failed).")
    earlier = set(earlier_partials)
    for spec, reason in failed_models.items():
        print(f"  - FAILED {spec}: "
              f"{failed_model_line(question_dir, spec, reason, earlier)}")
    print(answer_origins_line(origins))
    if origins["warn_all_fallback"]:
        print(all_fallback_warning(origins))
    # D6 row 3: a partial answer set is usable output — marker + `state:
    # "partial"` + exit 0. Zero answers has nothing to aggregate, so it is exit 3
    # naming the retry command rather than the old bare exit 1.
    row3 = unattended_mod.report_partial_results(
        completed=completed,
        failed=list(failed_models),
        phase_dir=question_dir,
        # D2 row 6: the live question positionally (never a recorded
        # --question), the caller's flags, then the verb.
        retry_command=cli_common.retry_command(
            "ask", plan_path, question, "--force", flags=retry_flags,
        ),
        unattended=unattended,
    )

    # Final stdout line: the answers.md path (so the instruction layer/Claude
    # can report it).
    print(answers_md)
    return row3


def _read_question_status(question_dir: str) -> Dict[str, Any]:
    """The question dir's ``.status.json`` as a dict (``{}`` when unreadable)."""
    try:
        with open(os.path.join(question_dir, ".status.json"), "r", encoding="utf-8") as f:
            status = json.load(f)
    except (OSError, ValueError):
        return {}
    return status if isinstance(status, dict) else {}


# ---------------------------------------------------------------------------
# The question dir's lock: one writer at a time, whatever the lane
# ---------------------------------------------------------------------------

#: The labels a foreground ask and ``--accept-partial`` write into the lock.
#: A detached worker's label carries its ``run_id`` instead (``RunHandle``).
FOREGROUND_ASK_LOCK_LABEL = "ask (foreground)"
ACCEPT_PARTIAL_LOCK_LABEL = "ask --accept-partial"


def take_question_lock(
    question_dir: str, *, label: str
) -> Tuple[Optional[process_control.PhaseLock], Dict[str, Any]]:
    """Take ``{question_dir}/.lock``, non-blocking: ``(lock, {})``, or ``(None, holder)``.

    It is the phase lock ``detach.classify_run`` probes as ``lock_held`` and
    the detached worker holds for its whole run (``RunHandle``). A foreground
    ask writes no ``run`` record, so without this lock nothing a reader can
    check showed it was live: ``classify_run`` answered ``no_run``, or the last
    run's terminal verdict, under a checkpoint reading ``models_running``. So
    a foreground ask holds it for its whole run, and ``--accept-partial`` holds
    it from its first check to its last write. Every writer of a question dir
    then takes the same lock, and none can move a file under another. The OS
    drops it when its holder dies, so a crash never leaves the dir locked.
    ``holder`` is the label the current holder wrote, for the refusal message.
    """
    lock = process_control.PhaseLock(lock_path(question_dir))
    try:
        lock.acquire({
            "holder": label,
            "mode": "ask",
            "pid": os.getpid(),
            "process_start_time": process_control.process_start_time(os.getpid()),
            "acquired_at": datetime.now().isoformat(),
        })
    except process_control.LockUnavailable as exc:
        return None, dict(exc.holder or {})
    return lock, {}


def _lock_holder_text(holder: Dict[str, Any]) -> str:
    """Who holds a question dir's lock, named from its label."""
    if holder.get("run_id"):
        who = f"detached run {holder['run_id']}"
    else:
        who = str(holder.get("holder") or "an unrecorded holder")
    return f"{who}, pid {holder.get('pid') or 'unrecorded'}"


def accept_partials(
    *,
    args: argparse.Namespace,
    question: str,
    plan_path: str,
    question_dir: str,
    is_resume: bool,
) -> int:
    """``--accept-partial <model> [<model> …]``: count failed runs' partials (D3.4).

    Without it every resume re-asks, and pays for, a model whose partial the
    operator has read and found whole. It dispatches nothing and judges nothing
    about why the run failed (a porcelain violation's partial can be accepted
    too; the violation stays in ``error_<model>.log``).

    1. Takes the question dir's lock (:func:`take_question_lock`) and holds it
       to the last write, so no ask of this question, foreground or detached,
       can start while it moves files. It refuses while anyone else holds the
       lock (a foreground ask, a detached worker, another acceptance), and
       while ``detach.classify_run`` reports this question's run as live.
    2. Checks **every** named model first: each must be a model this question
       was last asked (``models_requested``), with a non-empty
       ``partial_<model>.md`` and no usable ``answer_<model>.md``. Any failure
       refuses and changes nothing.
    3. Moves each partial to ``answer_<model>.md`` (``os.replace``) and records
       its origin ``accepted`` (D7.1).
    4. Regenerates ``answers.md`` and runs the closing report from the disk scan,
       with the last run's ``models_failed`` less the accepted models. From then
       on it is an ordinary answer: resume skips it, ``--rerun-all`` replaces it.
    """
    if args.rerun_all:
        return unattended_mod.fail_closed(
            "ERROR: --accept-partial counts a partial the last run left and "
            "dispatches nothing; it cannot be combined with --rerun-all, which "
            "re-asks every model."
        )
    if not is_resume or not os.path.isdir(question_dir):
        return unattended_mod.fail_closed(
            "ERROR: --accept-partial: this question has never been asked about "
            f"this plan, so there is no partial to accept (no {question_dir})."
        )
    lock, holder = take_question_lock(question_dir, label=ACCEPT_PARTIAL_LOCK_LABEL)
    if lock is None:
        return unattended_mod.fail_closed(
            "ERROR: --accept-partial refused: this question's run is still running "
            f"({_lock_holder_text(holder)} holds {lock_path(question_dir)}), and it "
            "may yet write the files a partial is accepted over. Nothing was "
            "changed. Wait for it to finish (or abort it), then accept."
        )
    try:
        return _accept_partials_locked(
            args=args, question=question, plan_path=plan_path,
            question_dir=question_dir,
        )
    finally:
        lock.release()


def _accept_partials_locked(
    *,
    args: argparse.Namespace,
    question: str,
    plan_path: str,
    question_dir: str,
) -> int:
    """The body of :func:`accept_partials`, run only while it holds the lock."""
    # The lock shuts out every writer that takes it. A `run` record that still
    # reads live without holding it is refused as well. `lock_held` is not read
    # here: the lock is this process's own now, so it would always be true.
    view = classify_run(question_dir, close_out=False)
    if view.get("verdict") in (VERDICT_STARTING, VERDICT_RUNNING, VERDICT_STALE):
        return unattended_mod.fail_closed(
            "ERROR: --accept-partial refused: this question's run is still running "
            f"({view.get('verdict')}), and it may yet write the files a partial is "
            "accepted over. Nothing was changed. Wait for it to finish (or abort "
            "it), then accept."
        )

    status = _read_question_status(question_dir)
    roster = [s for s in (status.get("models_requested") or []) if isinstance(s, str)]
    accepted: List[str] = []
    problems: List[str] = []
    for name in args.accept_partial:
        stem = sanitize_model_name(name)
        spec = next((s for s in roster if sanitize_model_name(s) == stem), None)
        if spec is None:
            problems.append(
                f"{name}: not a model this question was last asked "
                f"({', '.join(roster) or 'no run recorded'})"
            )
            continue
        if spec in accepted:
            continue
        if read_nonempty_answer(answer_file_path(question_dir, stem)) is not None:
            problems.append(f"{name}: already has an answer (answer_{stem}.md); "
                            "there is nothing to accept")
            continue
        if read_nonempty_answer(partial_file_path(question_dir, stem)) is None:
            problems.append(f"{name}: no partial text to accept "
                            f"(partial_{stem}.md is missing or empty)")
            continue
        accepted.append(spec)
    if problems:
        return unattended_mod.fail_closed(
            "ERROR: --accept-partial refused; nothing was changed:\n"
            + "\n".join(f"       - {p}" for p in problems)
        )

    moved: List[str] = []
    for spec in accepted:
        stem = sanitize_model_name(spec)
        partial = partial_file_path(question_dir, stem)
        answer = answer_file_path(question_dir, stem)
        try:
            os.replace(partial, answer)
        except OSError as e:
            print(f"ERROR: could not move {os.path.basename(partial)} to "
                  f"{os.path.basename(answer)}: {e}")
            continue
        moved.append(spec)
        write_origin(question_dir, spec, ORIGIN_ACCEPTED)
        print(f"[ACCEPTED] {spec}: partial_{stem}.md -> answer_{stem}.md "
              f"(from a run that failed; its error stays in error_{stem}.log)")

    prior_failed = status.get("models_failed")
    prior_failed = prior_failed if isinstance(prior_failed, dict) else {}
    failed_models: Dict[str, str] = {
        spec: str(reason) for spec, reason in prior_failed.items()
        if spec in roster and spec not in moved
    }
    completed = [spec for spec, _ in collect_completed(question_dir, roster)]
    reconcile_failed_map(roster, completed, failed_models)
    # A slot the last run never dispatched (its progress row reads
    # `not-dispatched`) kept an earlier run's partial.
    progress = status.get("progress") if isinstance(status.get("progress"), dict) else {}
    progress_models = progress.get("models") if isinstance(progress.get("models"), dict) else {}
    earlier_partials = [
        spec for spec in failed_models
        if isinstance(progress_models.get(spec), dict)
        and progress_models[spec].get("source") == "not-dispatched"
    ]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    answers_md, completed = write_answers_md(
        question_dir, question, plan_path, roster, failed_models, timestamp,
        earlier_partials=earlier_partials,
    )
    record_output_files(question_dir, answers=answers_md)
    # The accepted models' progress rows move with the rest of the record: a
    # row left reading `failed` with the old error would contradict
    # `models_completed` and `answers.md` in `status --view run`. The row keeps
    # the timings the last run froze (that slot did end when it ended); only
    # its verdict and provenance move. `accepted` is in neither
    # `RESUME_SOURCES` nor `SKIPPED_SOURCES`, so it renders as plain `done`.
    progress_update: Dict[str, Any] = {}
    if moved and progress:
        models_map = {
            spec: dict(entry) if isinstance(entry, dict) else entry
            for spec, entry in progress_models.items()
        }
        if flip_map_entries_to_done(models_map, moved, source=ORIGIN_ACCEPTED):
            progress_update["models"] = models_map
        # The disk scan, as the fan-out's own closing restatement writes it.
        progress_update["models_succeeded"] = len(completed)
    return close_ask_run(
        question_dir=question_dir,
        question=question,
        plan_path=plan_path,
        model_specs=roster,
        completed=completed,
        failed_models=failed_models,
        earlier_partials=earlier_partials,
        answers_md=answers_md,
        state=ask_run_state(completed, failed_models),
        produced=moved,
        unattended=bool(getattr(args, "yes", False)),
        # The retry of this command is a plain re-ask: a replayed
        # `--accept-partial` would only refuse, its partials being gone.
        retry_flags=[],
        progress=progress_update or None,
    )


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

async def main(argv: Optional[List[str]] = None) -> int:
    # What the run holds for its lifetime (the question dir's lock, on the
    # foreground lane) is released on every way out of it: a return, an
    # exception, or the detach boundary's `sys.exit`.
    with contextlib.ExitStack() as held:
        return await _main(argv, held)


async def _main(argv: Optional[List[str]], held: contextlib.ExitStack) -> int:
    # Line buffering + UTF-8/replace stream encoding (Windows-safe output);
    # see utils/stream_bootstrap.py for the full rationale.
    bootstrap_streams()

    args = parse_args(argv)

    # Resolve the verbatim question and require non-empty content.
    question = resolve_question(args)
    if not question.strip():
        print('ERROR: question is empty. Provide a non-empty question, e.g. '
              '--question "Is the rollback strategy sufficient?"')
        return 1

    # Validate plan file. Use realpath (not abspath) so symlinked plan paths
    # match the canonical path agentic CLIs resolve on disk, consistent with
    # output_md_path and the instruction files.
    plan_path = os.path.realpath(args.plan_file)
    if not os.path.isfile(plan_path):
        print(f"ERROR: Plan file not found: {args.plan_file}")
        print(f"       Resolved path: {plan_path}")
        return 1

    # §9.3.a/b: the anchor capture point — absolute, before anything can chdir
    # and before any provider read that decides routing.
    set_run_anchor(plan_path)

    plan_content = read_plan(plan_path)
    plan_hash = compute_plan_hash(plan_content)

    # D3.4: `--accept-partial` dispatches nothing, so it needs no model
    # resolution (which could itself end the run at D6 row 2) and never reaches
    # the detach boundary: it resolves the question dir exactly as a resume does
    # and works on the files there.
    if args.accept_partial:
        # It runs in the foreground or not at all. Silently dropping a
        # caller's `--detach` (the opencode package plugin composes it onto
        # every launch) would hand back a foreground result with no run banner
        # in place of the detached launch that was asked for. So, like every
        # other flag a mode cannot honour, it is refused here, ahead of
        # `get_phase_dir`'s mkdir, so nothing on disk changes.
        if getattr(args, "detach", False):
            return unattended_mod.fail_closed(
                "ERROR: --accept-partial runs in the foreground only: it "
                "dispatches nothing and finishes in seconds, so it cannot be "
                "combined with --detach, which would launch a background run "
                "that never happens. Nothing was changed. Re-run it without "
                "--detach."
            )
        slug = slugify_question(question)
        phase_dir = str(get_phase_dir(Path(plan_path), "ask"))
        question_dir, is_resume = resolve_question_dir(phase_dir, slug, question)
        return accept_partials(
            args=args,
            question=question,
            plan_path=plan_path,
            question_dir=question_dir,
            is_resume=is_resume,
        )

    # Mutual exclusivity check (mirror review orchestrators).
    if args.quick and args.interactive:
        print("ERROR: --quick and --interactive are mutually exclusive.")
        return 1

    # Resolve models. D6 row 2: `defaults.models` is the auto-selected answer and
    # an unresolvable set is exit 3 — `ask` never renders a picker unattended.
    unattended = bool(getattr(args, "yes", False))
    try:
        model_specs = resolve_models(
            cli_models=args.models,
            interactive=args.interactive,
            quick=args.quick,
            mode="ask",
            anchor=plan_path,  # per-project config discovery follows the plan-derived root
            unattended=unattended,
        )
    except NeedsHuman as e:
        return unattended_mod.fail_closed(e.message, site_id=e.site)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        available = get_all_model_specs(anchor=plan_path)
        print(f"Use --models flag. Available: {', '.join(available[:5])}...")
        return 1

    if not model_specs:
        print("ERROR: No models selected.")
        return 1

    # Model validation = warn-and-proceed (match existing orchestrators).
    invalid_models = [m for m in model_specs if not is_model_valid(m, anchor=plan_path)]
    if invalid_models:
        print(f"WARNING: Unknown models (proceeding anyway): {', '.join(invalid_models)}")
        # Anchored to match the rejection above (§9.3.c).
        available = get_all_model_specs(anchor=plan_path)
        print(f"Available models: {', '.join(available[:10])}...")

    # Compute slug + resolve the per-question directory (collision/resume guard).
    slug = slugify_question(question)
    phase_dir = str(get_phase_dir(Path(plan_path), "ask"))
    question_dir, is_resume = resolve_question_dir(phase_dir, slug, question)
    os.makedirs(question_dir, exist_ok=True)

    # Plan-freshness check on resume (warn only; --force is how to act on it).
    if is_resume:
        status_path = os.path.join(question_dir, ".status.json")
        if os.path.exists(status_path):
            try:
                with open(status_path, "r", encoding="utf-8") as f:
                    prior = json.load(f)
                if prior.get("plan_hash") and prior.get("plan_hash") != plan_hash:
                    print("WARNING: plan file has changed since these answers were "
                          "generated; existing answers may be stale — re-run with "
                          "--rerun-all to refresh every model's answer.")
            except (json.JSONDecodeError, OSError, IOError):
                pass

    template = load_prompt(ASK_PROMPT_FILE)
    inline_plan, truncated = build_inline_plan(plan_content, plan_path)
    # D4.2: a path-only adapter (aider) is handed the whole plan by `--read` and
    # gets no inlined copy, so the warning is printed only when some model's
    # prompt really carries the truncated copy. An aider-only roster would
    # otherwise be told of a truncation that reaches no prompt.
    if truncated and any(
        renders_inline_plan(
            template, question, plan_path, inline_plan,
            os.path.realpath(answer_file_path(question_dir, sanitize_model_name(spec))),
            parse_model_spec(spec, anchor=plan_path)[0],
        )
        for spec in model_specs
    ):
        print(f"WARNING: plan exceeds {MAX_INLINE_PLAN_BYTES // 1024} KB; inlined copy "
              f"truncated (a marker points models at the full plan path).")

    project_root = get_project_root(plan_path) or os.path.dirname(plan_path) or "."
    skip_existing = not args.rerun_all

    print(f"Question slug: {slug}")
    print(f"Output directory: {question_dir}")
    print(f"Models: {', '.join(model_specs)}")
    print(f"Plan: {plan_path} ({len(plan_content)} bytes)")
    if args.rerun_all:
        print("Rerun-all: re-asking all models (ignoring existing answer files)")
    print("")

    # --- the detach boundary -------------------------------------------------
    # `ask` runs live at {plan}/ask/<slug>-<hash8>/, so the run this fork owns is
    # this question's dir — which is also why `status` needs `--question`/`--run-id`
    # to pick one. Everything above (question resolution, the collision/resume
    # guard, model resolution, plan hashing) stays in the foreground.
    detach_outcome = maybe_detach(
        args=args,
        mode="ask",
        phase_dir=question_dir,
        plan_file=plan_path,
        phase="ask",
        ask_slug=slug,
        model_specs=model_specs,
    )
    if detach_outcome is not None:
        sys.exit(detach_outcome)

    # One writer per question dir, whatever the lane. The detached worker took
    # `{question_dir}/.lock` at the boundary just above (`RunHandle`). A
    # foreground ask writes no `run` record, so this lock is its liveness. It is
    # held until `main` returns, and the OS drops it if the process dies. It is
    # what `classify_run` reports as `lock_held`, and what refuses a second ask
    # of this question. `--accept-partial` must take it before it moves a file,
    # so it can never rewrite answers.md under a live fan-out.
    if not getattr(args, "internal_worker", False):
        lock, holder = take_question_lock(question_dir, label=FOREGROUND_ASK_LOCK_LABEL)
        if lock is None:
            return unattended_mod.fail_closed(
                "ERROR: another run is already writing this question's directory "
                f"({_lock_holder_text(holder)} holds {lock_path(question_dir)}).\n"
                "       Two runs must not interleave answer files and .status.json "
                "merges in one question dir. Wait for it to finish (or abort it), "
                "then re-run."
            )
        held.callback(lock.release)

    write_status(question_dir, {
        "phase": "ask",
        "state": "models_running",
        "started_at": datetime.now().isoformat(),
        "models_requested": list(model_specs),
        "question": question,
        "question_slug": slug,
        "plan_hash": plan_hash,
        "answers_md": os.path.join(question_dir, "answers.md"),
        # Drop the predecessor's per-model map with the same move `claim_run`
        # makes on the detached lane, and for the reason spelled out in the
        # review base's copy of this write (F1, 2026-09-20): on the foreground
        # lane nothing else ever drops it, so a re-asked question opened on the
        # last run's rows and `just finished:` could never announce a model that
        # the stale map already called terminal. `report_progress` below rebuilds
        # it.
        "progress": None,
    })
    if unattended and not args.models and not args.quick:
        # D6 row 2, recorded rather than merely applied (see review base).
        unattended_mod.record_resolution(
            question_dir,
            unattended_mod.row(2).site_id,
            "defaults.models: " + ", ".join(model_specs),
        )
    # Counters only, deliberately: the per-model map is written by the tracker's
    # seed inside the fan-out (below), and `progress` merges key by key at its
    # top level, so a `models` key here would only race the seed to write the
    # same thing twice.
    report_progress(
        question_dir, step="fanout",
        models_total=len(model_specs), models_done=0, models_succeeded=0,
    )

    # The fan-out's per-model map, and the [PROGRESS] ticker that narrates it.
    #
    # Built against `question_dir` and **not** the `ask` phase dir the other
    # three modes' pattern would predict: ask's checkpoint lives one level
    # below, at `{plan}/ask/<slug>-<hash8>/.status.json` (see
    # `resolve_question_dir`), because two different questions asked about one
    # plan are two independent runs with two answer sets and two `.status.json`
    # files. A tracker anchored on `{plan}/ask/` would merge both questions'
    # models into a single map — and hand a poller a map it cannot attribute to
    # either question. It is the same fact that makes the Layer 2 poll select by
    # `--question` and never by `--phase ask`.
    #
    # `timeout=args.timeout` mirrors `ask_one`'s own budget rule (the CLI
    # override when given, each provider's configured timeout otherwise), so a
    # queued row renders `0m00s/30m` against the budget the slot will really
    # get rather than a blank denominator.
    #
    # Constructed **above** the two coroutines rather than beside the
    # `run_models_concurrent` call it is passed to, because `ask_one` now takes
    # a transition of its own (the `running` one below) and a closure reading a
    # name defined forty lines further down is a trap the next edit springs.
    #
    # The division of labour with the helper: it seeds the map before the tasks
    # exist, marks the stagger wait, turns every slot terminal from the result
    # `ask_one` (or `skip_existing_answer`) returned, names the deadline as the
    # sweep reason, and cancels *and awaits* the ticker in its `finally` before
    # returning. What it cannot do is say when a slot left the queue for a
    # provider — only the coroutine that dispatches sees that — which is why
    # `ask_one` calls `tracker.running()` itself, exactly as
    # `run_single_model` and `run_single_review` do on the other two lanes.
    tracker = FanoutProgress(
        question_dir, model_specs, anchor=plan_path, timeout=args.timeout,
    )

    # Every spec `ask_one` got past the sandbox gate to dispatch (where it drops
    # the model's stale partial and origin record). Only a dispatched slot can
    # have written this run's answer file or partial, so the closing report
    # reads it twice: D3.3's deadline move touches only these specs' answer
    # files, and a failed spec outside it names its partial as an earlier run's.
    dispatched_specs: Set[str] = set()
    # Failed specs whose answer file could be neither moved nor copied aside,
    # so it is still at its canonical path (`set_answer_file_aside`). The
    # closing report keeps them out of the scan: the slot stays failed.
    answers_left_in_place: Set[str] = set()
    # Each dispatched slot's provider call, so the closing report can stop and
    # join the ones the deadline cut before it sets their answer files aside.
    provider_calls: Dict[str, ProviderCall] = {}

    def skip_existing_answer(model_spec: str, index: int) -> Optional[Dict[str, Any]]:
        # Cheap, synchronous resume check (runs before stagger/semaphores):
        # short-circuit models that already have a non-empty answer so resume
        # stays fast. Returns None when the model must (re)run.
        #
        # The returned dict is also this slot's *progress transition*: the
        # fan-out feeds it to `FanoutProgress.record_result`, which reads
        # `success` and `source` and freezes the entry as `done` /
        # `source: "resume"` with `attempt: 0` and `elapsed_s: 0` — terminal the
        # moment it is seeded, because the answer exists and no attempt is ever
        # dispatched. That is why a skipped model counts on **both** numbers,
        # `models_done` and `models_succeeded`: it has finished its slot *and*
        # it has a usable result, so a resumed run of four models that finds
        # three on disk reads 3/4 at the first poll instead of 0/4. Leaving it
        # `queued` would make the counts and the rendered table lie about a run
        # with nothing left to do, and the write that claims the question dir
        # drops the predecessor's `progress` wholesale, so there is no earlier
        # entry to fall back on. (`claim_run` does that on the detached lane; on
        # the foreground one the launch write above does — F1, 2026-09-20.)
        # There is no separate `skipped` state; the distinction lives in
        # `source`.
        if not skip_existing:
            return None
        sanitized = sanitize_model_name(model_spec)
        answer_path = os.path.realpath(os.path.join(question_dir, f"answer_{sanitized}.md"))
        if read_nonempty_answer(answer_path) is not None:
            print(f"[SKIP] {model_spec} - already has a non-empty answer")
            return {"model": model_spec, "success": True, "error": None, "source": "resume"}
        return None

    async def ask_one(model_spec: str, index: int) -> Dict[str, Any]:
        provider_name, _ = parse_model_spec(model_spec, anchor=plan_path)

        # D6 step 3, the review fan-out's gate on the third lane that reaches
        # `generate`, off the same once-per-run cache. An ask slot reads the
        # plan (or is handed it inline) and answers in prose, so a runner whose
        # sandbox cannot start returns a paragraph about the file it could not
        # open — an answer file, and therefore a success. Refused here, ahead of
        # `--rerun-all`'s delete, because a slot that never runs may not destroy
        # the previous run's answer.
        #
        # The third answer (D6 override, 2026-09-17): `dispatch_unsandboxed`
        # when the probe said `unavailable` AND `providers.<name>.sandbox_fallback`
        # is `auto` (the default; `off` refuses). One `[SANDBOX_BYPASSED]` line,
        # the flag on the invoker, and a porcelain snapshot so a write the model
        # makes can be named.
        sandbox = await asyncio.to_thread(sandbox_refusal, provider_name, project_root)
        if sandbox.refused:
            print(f"[{model_spec}] {sandbox.reason}")
            return {"model": model_spec, "success": False, "error": sandbox.reason,
                    "source": "not-dispatched"}
        tree_before = None
        # Any fallback rung prints its one line: `[SANDBOX_FALLBACK]` for a
        # contained rung, `[SANDBOX_BYPASSED]` for the uncontained one.
        if sandbox.fallback:
            print(f"[{model_spec}] {sandbox.reason}")
        if porcelain_check_applies(sandbox):
            # The roster-aware prefixes (D4.3): the plugin's own trees, plus the
            # workspace caches an adapter in this fan-out declares — aider's
            # `.aider.tags.cache.v4/` is a sibling's cache, never this slot's
            # write, but only while an aider slot is in the same fan-out.
            tree_before = await asyncio.to_thread(
                porcelain_snapshot, project_root,
                ignore_prefixes=fanout_ignore_prefixes(
                    plan_path, project_root, anchor=plan_path
                ),
            )
        # The plugin's own jail (F1 "What it fixes"): no porcelain check, by
        # decision; the mode check's before-snapshot instead.
        mode_before = None
        if mode_check_applies(sandbox):
            mode_before = await asyncio.to_thread(mode_snapshot, project_root)

        sanitized = sanitize_model_name(model_spec)
        # output_md_path MUST be absolute: provider subprocesses run with
        # cwd=project_root, so a relative path could escape the question dir.
        answer_path = os.path.realpath(os.path.join(question_dir, f"answer_{sanitized}.md"))
        log_file = os.path.join(question_dir, f"log_{sanitized}.txt")

        if skip_existing:
            # The pre-stagger skip_predicate already short-circuited models with a
            # usable answer; reaching here means the file is missing/empty, so the
            # model re-runs (warn if a stale empty file is present).
            if os.path.exists(answer_path):
                print(f"WARNING: answer_{sanitized}.md is empty/unreadable; re-running model")
        else:
            # --rerun-all: drop any stale answer so only content written during THIS
            # run can count in steps 1 and 2 below.
            try:
                os.remove(answer_path)
            except FileNotFoundError:
                pass
            except OSError:
                pass
        # On both branches, and only past the sandbox gate (a refused slot is
        # not a run and may not destroy the last run's evidence): from here on
        # an origin record or a partial can only come from THIS dispatch. The
        # stale origin goes so a re-ask that fails leaves no record (D7.1); the
        # stale partial goes so the partial a failed-model line names — and the
        # one `--accept-partial` counts — is always the model's latest run's,
        # and a re-ask that answers leaves none beside its answer (D3.2, D3.4).
        remove_stale(partial_file_path(question_dir, sanitized))
        remove_stale(origin_file_path(question_dir, sanitized))
        dispatched_specs.add(model_spec)

        # provider_name (resolved above) selects the output-channel variant: an
        # adapter declaring supports_file_output = False is asked for stdout
        # rather than for a file it would answer with a refusal sentence.
        prompt, prompt_truncated = render_prompt_guarded(
            template, question, plan_path, inline_plan, answer_path, provider_name
        )
        if prompt_truncated:
            print(f"WARNING: rendered prompt for {model_spec} exceeded "
                  f"{MAX_PROMPT_BYTES // 1024} KB; question truncated to fit the argv "
                  f"size limit (plan path preserved so the model can read the full plan).")
        per_model_timeout = (
            int(args.timeout) if args.timeout is not None
            else get_provider_timeout(provider_name, anchor=plan_path)
        )

        # F1, 2026-09-20: this lane had **no** `running` transition at all, and
        # the omission was justified by an argument about *terminal* transitions
        # — `run_models_concurrent` takes those from the returned result dict,
        # so `ask_one` needs none of its own. `running` is not terminal, and it
        # is the one transition the helper cannot take: it knows a slot left the
        # stagger, never that a provider was actually dispatched. Measured on a
        # 2-model ask fan-out: every line of the whole run read `[PROGRESS] 0/2
        # done (0 ok, 0 failed) | staggering 1 | queued 1` — never a model name,
        # never an elapsed/budget — and `status --view run` showed the index-0
        # model `queued` for its entire 30-minute slot. `attempt=1` because this
        # lane makes exactly one dispatch and has no ladder to count; `timeout_s`
        # is the slot's whole budget, which is the seed's value unless a
        # per-slot override moved it — the one thing the seed could not know.
        tracker.running(model_spec, attempt=1, timeout_s=per_model_timeout)

        call = provider_calls[model_spec] = ProviderCall()
        result = await asyncio.to_thread(
            call.run,
            invoke_with_provider,
            prompt=prompt,
            model_spec=model_spec,
            timeout=per_model_timeout,
            log_file=log_file,
            cwd=project_root,
            anchor=plan_path,
            # D2.2: the adapter's reduced answer text from the FULL stdout,
            # redacted and head-capped at 1 MiB — the only source step 2 reads.
            want_answer_text=True,
            **sandbox_fallback_kwargs(sandbox),
        )
        # Popped at once (D2.2): up to 1 MiB of answer must never ride `details`
        # into a caller that logs it. A return that ran no child carries no key,
        # which reads exactly like "" (D2.3).
        details = result.get("details") if isinstance(result, dict) else None
        answer_text = details.pop("answer_text", "") if isinstance(details, dict) else ""
        if not isinstance(answer_text, str):
            answer_text = ""

        # D6 override: the detective check, ahead of the answer-file policy
        # below — a bypassed slot that changed the working tree is failed by
        # path even when it also left an answer file. The question dir itself
        # is the plugin's own tree and is excluded, and so is the workspace
        # cache of an adapter in this fan-out (`fanout_ignore_prefixes`, D4.3).
        if porcelain_check_applies(sandbox):
            ignore_prefixes = fanout_ignore_prefixes(
                plan_path, project_root, anchor=plan_path
            )
            # Plan §4.3: ask is single-shot, so its one attempt's verdict is
            # the whole window's.
            audits = [(result.get("details") or {}).get("readonly_audit")]
            tracker.record_readonly_audit(
                model_spec, combine_audits(audits).to_dict()
            )
            tree_after = await asyncio.to_thread(
                porcelain_snapshot, project_root, ignore_prefixes=ignore_prefixes
            )
            touched = unexpected_writes(
                tree_before, tree_after, ignore_prefixes=ignore_prefixes,
            )
            if touched and bypass_stream_audit_clears(audits):
                warning = bypass_write_not_attributed(provider_name, touched)
                print(f"[{model_spec}] {warning}")
                tracker.warn(model_spec, warning)
            elif touched:
                siblings = await asyncio.to_thread(
                    boundaryless_sibling_count, model_spec, project_root, plan_path
                )
                violation = bypass_write_violation(
                    provider_name, touched, boundaryless_siblings=siblings
                )
                print(f"[{model_spec}] {violation}")
                write_error_log(question_dir, model_spec, violation, result)
                # `collect_completed` reads the answer files, not this return,
                # so an answer this slot wrote is set aside (never deleted: it
                # is still the operator's evidence) under a name the scan does
                # not read, or the failed slot would be counted as completed.
                if os.path.exists(answer_path):
                    try:
                        os.replace(answer_path, answer_path + ".violated")
                    except OSError:
                        pass
                # The same holds for an answer this slot gave on stdout
                # (D3.2): kept as evidence, or what survives a violation would
                # depend on which channel the model answered on. The slot still
                # fails with its violation; `--accept-partial` can count it.
                if answer_text.strip():
                    write_partial(question_dir, model_spec, answer_text)
                return {"model": model_spec, "success": False,
                        "error": violation, "source": "failed"}

        # The plugin's own jail (F1, 2026-09-30): its `[JAIL_DENIED]` line and
        # in-stream denial count, then the mode check and the home check's
        # verdict — the same fail-closed treatment as the porcelain violation
        # above: the answer is set aside as evidence and never counted.
        report_jail_outcome(model_spec, details, question_dir)
        incidental = await run_incidental_checks(
            sandbox, provider_name=provider_name, display_name=model_spec,
            model_spec=model_spec, project_root=project_root, plan_path=plan_path,
            mode_before=mode_before,
            home_checks=[(details or {}).get("home_check")],
            audits=[(details or {}).get("readonly_audit")],
            tracker=tracker, summary_key=question_dir,
        )
        if incidental is not None:
            write_error_log(question_dir, model_spec, incidental, result)
            if os.path.exists(answer_path):
                try:
                    os.replace(answer_path, answer_path + ".violated")
                except OSError:
                    pass
            if answer_text.strip():
                write_partial(question_dir, model_spec, answer_text)
            return {"model": model_spec, "success": False,
                    "error": incidental, "source": "failed"}

        # Steps 1 and 2 count an answer only from a run that ended by itself at
        # exit 0 with a finished answer (D3.1): success, or the PARSE_ERROR a
        # prose answer with no JSON in it arrives as, and no `incomplete`.
        if answer_finished(result):
            # 1. The answer file the model was asked for. Only here: nothing
            #    shows a file from a timed-out or failed run is finished — it
            #    can be cut mid-write, an outline or a draft (D3.3).
            if read_nonempty_answer(answer_path) is not None:
                write_origin(question_dir, model_spec, ORIGIN_FILE)
                return {"model": model_spec, "success": True, "error": None,
                        "source": "file"}

            # 2. The adapter's reduced answer text (D2.3), persisted so resume
            #    skips this model next time. Success requires the text to land
            #    on disk (success ⟺ non-empty answer file), so aggregation
            #    (file-based) always sees it.
            recovered = recover_answer_text(result, answer_text)
            if recovered is not None:
                try:
                    with open(answer_path, "w", encoding="utf-8") as f:
                        f.write(recovered)
                except (OSError, IOError) as e:
                    error = f"Recovered answer but failed to persist it: {e}"
                    write_error_log(question_dir, model_spec, error, result)
                    return {"model": model_spec, "success": False, "error": error,
                            "source": "failed"}
                # D7.1: `stdout` when this adapter is asked for stdout (the
                # same capability, off the same provider_name, that picked the
                # prompt variant), `fallback` when it was asked for the file
                # and did not write it. `source` stays "fallback" for both, so
                # `.status.json` and its readers see no new value.
                write_origin(
                    question_dir, model_spec,
                    ORIGIN_STDOUT if answers_on_stdout(provider_name) else ORIGIN_FALLBACK,
                )
                return {"model": model_spec, "success": True, "error": None,
                        "source": "fallback"}

        # 3. Failure, with the run's own error: a timeout, a non-zero exit, an
        #    incomplete answer, or a clean run with nothing to recover. Any text
        #    it left is kept as partial evidence (D3.2) — its answer file when
        #    there is one (the file takes the name, D3.3), else a non-empty
        #    stdout answer text — and never counted.
        error = result.get("error") or "No usable answer produced"
        write_error_log(question_dir, model_spec, error, result)
        if read_nonempty_answer(answer_path) is not None:
            if not set_answer_file_aside(question_dir, model_spec, answer_path):
                answers_left_in_place.add(model_spec)
        elif answer_text.strip():
            write_partial(question_dir, model_spec, answer_text)
        return {"model": model_spec, "success": False, "error": error, "source": "failed"}

    results = await run_models_concurrent(
        model_specs, ask_one, args.timeout, args.max_parallel,
        skip_predicate=skip_existing_answer,
        anchor=plan_path,
        tracker=tracker,
    )
    # A slot the deadline cut may still have its CLI running; it is stopped and
    # joined here, ahead of D3.3's one-time move below, which it could otherwise
    # outlive and write its answer file behind.
    await stop_unreturned_provider_calls(provider_calls)

    # T5: the fan-out is not the phase, and a ticker that dies with it leaves
    # the rest of the run silent. `run_models_concurrent` returns the moment the
    # last slot does — having cancelled *and awaited* its own ticker first, so
    # no [PROGRESS] line can interleave with the per-model summary — but ask
    # then rescans the question dir, resolves the failed map and rewrites
    # answers.md, which on a large answer set is the second silence this feature
    # exists to remove. This second ticker is what reports that window — with
    # one line rather than a line per interval, for the reason spelled out under
    # the yield below. It holds
    # no per-model map and writes nothing at all (it re-reads the checkpoint and
    # prints), so the terminal map the sweep froze stays byte-for-byte as it was
    # and a table rendered afterwards still shows each model's real duration
    # rather than a clock that kept running.
    phase_progress = PhaseProgress(question_dir, anchor=plan_path)
    phase_progress.start_ticker()
    # One turn of the loop, so the task actually starts. `start_ticker` only
    # *schedules* it, and everything below this line is synchronous — the answer
    # scan, the failed map and the answers.md rewrite are all plain file I/O —
    # so without a yield here the ticker would never get a turn at all, would be
    # cancelled before its body ever ran, and would print nothing: not its
    # interval lines and not the teardown line that names the terminal step.
    # Given the turn, it reaches its first `await` and the teardown cancel lands
    # there, which is what guarantees that last line. (What this lane gets is
    # therefore that one line and no interval lines at all — ask's post-fan-out
    # window is short and wholly synchronous, so an interval expiring inside it
    # cannot be serviced until it ends. F6, 2026-09-20: the parenthesis here
    # used to say a lane whose post-fan-out work awaits "also gets the interval
    # lines", offered as the contrast that made ask's single line the exception
    # — and on the review lanes' executor path it was false, because their
    # `dispatch_subagent_tasks` blocked the loop for the whole validation
    # window. Those two call sites are `asyncio.to_thread`-awaited now, so the
    # contrast is true as stated; ask has no such call to await.)
    await asyncio.sleep(0)
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # D3.3: the fan-out's deadline is a timeout too. A slot it cancelled
        # never returned from `ask_one`, so step 1 never judged its answer file,
        # and the scan below would count it. Moved to its partial first, the
        # spec stays failed (`DEADLINE_ERROR`, from the backfill below). Its
        # provider call was stopped and joined above, so nothing writes the
        # file after this.
        set_aside_unreturned_answers(
            question_dir, model_specs, results, dispatched_specs,
            left_in_place=answers_left_in_place,
        )

        # Read-only scan to determine which models succeeded, so we can build the
        # failed map before writing answers.md exactly once (no transient on-disk
        # version missing the ## Failed Models section).
        completed = [
            spec for spec, _ in collect_completed(question_dir, model_specs)
            if spec not in answers_left_in_place
        ]
        completed_set = set(completed)

        # Every requested model is either completed (has a usable answer file)
        # or failed, and the map is built in the same three steps the review
        # lanes build theirs — F4, 2026-09-20. It used to be one loop over
        # `model_specs` ending in a bare `or "No answer produced (model did not
        # complete)"`, which made this lane the **third** wording for the one
        # cause the other two name once: a slot the fan-out's deadline
        # cancelled was reported that sentence in `answers.md` and in
        # `models_failed` while the map's own swept entry — written by the same
        # run, one file over — said `no result (cancelled at the fan-out
        # deadline)`. One cause, two labels, and the table and the report
        # disagreeing about a model is precisely what `DEADLINE_ERROR` exists
        # to stop.
        #
        # 1. What the fan-out itself returned: a slot that ran and lost carries
        #    its own reason, which is more informative than any backfill.
        failed_models: Dict[str, str] = {}
        for spec, res in results.items():
            if not isinstance(res, dict) or res.get("success"):
                continue
            failed_models[spec] = res.get("error") or "No usable answer produced"
        # 2. F11's backfill, the same call with the same helper the review base
        #    and review-code make: a spec in neither `results` nor
        #    `failed_models` never returned at all, and it is named
        #    `DEADLINE_ERROR` here and in the map by one pass. The tracker's own
        #    sweep has normally already retired it with that same string (the
        #    transitions are idempotent, so the first writer wins); this is the
        #    belt that catches a fan-out which returned by a path the sweep
        #    missed.
        backfill_deadline_losses(model_specs, results, failed_models, tracker=tracker)
        # 3. Reconcile against the disk scan, which is this lane's source of
        #    truth for "answered" (`collect_completed` reads the answer files,
        #    and `answers.md` and `models_completed` are built from the same
        #    scan). A slot with a file is completed whatever its result said; a
        #    slot with neither a file nor a reason claimed success and wrote
        #    nothing, which is a different cause from the deadline and keeps the
        #    sentence that has always described it.
        reconcile_failed_map(model_specs, completed_set, failed_models)
        # A failed run's answer file that could not be set aside is still on
        # disk under its answer name; the failure line says so (D3.2).
        for spec in answers_left_in_place:
            if spec in failed_models:
                failed_models[spec] += (
                    " — its answer file could not be set aside, so it was left "
                    f"in place as answer_{sanitize_model_name(spec)}.md "
                    "(not counted)"
                )

        # Write answers.md once, with the resolved failed-models section. A
        # failed spec this run never dispatched (a sandbox refusal) kept any
        # partial the last run left, and its line says so (D3.2).
        earlier_partials = [s for s in failed_models if s not in dispatched_specs]
        answers_md, completed = write_answers_md(
            question_dir, question, plan_path, model_specs, failed_models, timestamp,
            earlier_partials=earlier_partials, withheld=answers_left_in_place,
        )

        state = ask_run_state(completed, failed_models)

        # A detached ask hands its answers back through `status`, not through a
        # stdout nobody read (no-op in the foreground).
        record_output_files(question_dir, answers=answers_md)
        # Both counters, and they do not mean the same thing — getting them the
        # wrong way round is exactly the bug the plan's "a live progress line
        # cannot use the second meaning" bullet describes. `models_done` counts
        # **finished slots**, read off the map the fan-out just froze: every slot
        # is terminal by now, so on a lossy run it still reads 4/4 instead of
        # walking backwards to the 3/4 a success count would write at the end of a
        # run whose numerator had already reached 4. `models_succeeded` carries
        # what this restatement has always computed, `len(completed)` — and that
        # number is deliberately the *disk* scan (`collect_completed`), the same
        # source `answers.md` and `models_completed` are built from, so the report,
        # the checkpoint and the progress line cannot disagree about which models
        # answered.
        #
        # Counters only: no `models` key, so `update_status`'s one-level merge
        # leaves the frozen map exactly as the fan-out's sweep wrote it.
        models_done = tracker.counts()[0]
        report_progress(
            question_dir, step="complete", models_total=len(model_specs),
            models_done=models_done, models_succeeded=len(completed),
        )
    finally:
        # Stopped only *after* the terminal `progress.step` is on disk: the
        # ticker's teardown line re-reads the checkpoint, so stopping it any
        # earlier would leave the log's last [PROGRESS] trailing off at
        # `fanout`. Cancel-and-await, so that line lands before the run's own
        # report rather than in the middle of it.
        await phase_progress.stop_ticker()

    # The answers this run produced itself — a slot that returned `file` or
    # `fallback` — so the counts line can say how many were kept from an
    # earlier run instead (the `resume` and `not-dispatched` slots, D7.2).
    produced = {
        spec for spec, res in results.items()
        if isinstance(res, dict) and res.get("success")
        and res.get("source") in ("file", "fallback")
    }
    exit_code = close_ask_run(
        question_dir=question_dir,
        question=question,
        plan_path=plan_path,
        model_specs=model_specs,
        completed=completed,
        failed_models=failed_models,
        earlier_partials=earlier_partials,
        answers_md=answers_md,
        state=state,
        produced=produced,
        unattended=unattended,
        # D2 row 6: the caller's flags.
        retry_flags=cli_common.current_replay_flags(mode="ask"),
    )
    # Plan codex-sandbox-unavailable F1 (2026-09-30): every
    # `[CODEX_HOME_CHECK]` and `[JAIL_DENIED]` line of this run's slots,
    # repeated as its last word — a home change outlives the run.
    print_closing_summary(question_dir)
    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
