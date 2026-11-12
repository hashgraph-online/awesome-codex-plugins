"""The prompt blocks a review slot's rendered prompt carries about its channels.

Three blocks, each rendered from the adapter's own declarations rather than
from a provider name branched on in an orchestrator
(docs/development/providers.md#provider-output-channels):

* ``{output_location}`` (:func:`render_output_location`): write the JSON to a
  file, or return it on stdout, from ``supports_file_output``;
* ``{diff_access}`` (:func:`render_diff_access`): how a code-review lane reaches
  the change (paths, the bounded inline payload, or unsupported), from
  ``generate_read_scope`` and ``runs_shell_in_generate``
  (docs/development/review-results.md);
* ``{working_limits}`` (:func:`render_working_limits`): the slot's real
  deadline and what it must not run.

Nothing here spawns a process. The strings are prompt text that
``tests/test_review_prompt_rules.py`` and the golden container turns pin byte
for byte. :mod:`utils.llm_client` re-exports every name here for reading only.
"""

import os
import re
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence, Union

from .provider_registry import parse_model_spec, get_provider
from .commit_range import pinned_head_read_rule
from .git_utils import is_empty_tree_id


# ---------------------------------------------------------------------------
# The ``{output_location}`` block the three review prompts end with
# ---------------------------------------------------------------------------

#: What a file-capable adapter is asked for. Byte-identical to the text
#: ``prompts/{code,plan,task}_review.txt`` carried inline before the placeholder
#: existed, so the rendered prompt of every adapter that declares
#: ``supports_file_output`` is unchanged to the character — the golden container
#: turns under ``tests/golden/container_turns/`` are captured from those bytes.
FILE_OUTPUT_LOCATION = (
    "CRITICAL: Write your JSON output to this file: {path}\n"
    "Do NOT print JSON to stdout. Write ONLY the JSON array to the specified "
    "file path.\n"
    'After writing, confirm by printing: "JSON written to {path}"\n'
    "\n"
    "The file must contain ONLY valid JSON - no markdown, no code blocks, no "
    "explanation. Just the raw JSON array."
)

#: What an adapter that declares ``supports_file_output = False`` is asked for
#: instead. Two adapters run their CLI in a read-only chat mode on purpose
#: (cursor ``--mode ask``, aider ``/ask``), and the file instruction is one they
#: can only answer with a refusal sentence. Stdout is the channel they *do*
#: have, it is the one ``invoke_with_file_output`` already falls back to, and
#: the parsed array lands in exactly the same per-model result file either way —
#: ``save_model_result`` writes it from the returned data, not from the model's
#: own file.
#:
#: "Refused by the sandbox where one runs", not "will be refused": until D6's
#: fallback (2026-09-17) every adapter on this roster really did refuse the
#: write — a chat mode, a zero tool budget, a missing tool, or codex's own
#: bubblewrap. A codex slot dispatched under the fallback (``sandbox_fallback:
#: auto``, the default) runs with no sandbox at all, so a write there would
#: *succeed*, and a prompt
#: that promised otherwise would be lying to the model about the one thing it
#: is being asked not to do. The instruction is the same either way (return the
#: array on stdout); only the claim about what happens on disobedience moved.
STDOUT_OUTPUT_LOCATION = (
    "CRITICAL: Return your JSON output on stdout as your final message. Do NOT "
    "write it to a file — this is a read-only task, and a file write is "
    "refused by the sandbox where one runs.\n"
    "Your final message must be ONLY the raw JSON array - no markdown, no code "
    "blocks, no explanation, no preamble and no closing remarks."
)


def render_output_location(
    output_json_path: Union[str, Path],
    model_spec: str,
    anchor: Optional[Union[str, Path]] = None,
) -> str:
    """The ``{output_location}`` block for ``model_spec``'s rendered prompt.

    One decision, taken from the adapter's declared
    :attr:`~utils.providers.base.LLMProvider.supports_file_output` rather than
    from a provider name spelled out in an orchestrator: the caller that renders
    a prompt does not need to know *which* CLIs refuse to write, only that this
    one does. An unknown provider (a config naming an adapter this build no
    longer ships) renders the file block, which is what every caller did before
    this function existed.

    ``anchor`` is the run's plan path (§9.3.c): a bare, prefix-less spec resolves
    its ``default_provider`` against the plan-derived project config, so the
    block matches the binary that will actually be spawned.
    """
    provider_name, _ = parse_model_spec(model_spec, anchor=anchor)
    provider = get_provider(provider_name)
    if provider is not None and not provider.supports_file_output:
        return STDOUT_OUTPUT_LOCATION
    return FILE_OUTPUT_LOCATION.format(path=output_json_path)


# ---------------------------------------------------------------------------
# The ``{diff_access}`` block of the code-review prompt
# ---------------------------------------------------------------------------
#
# Measured on the 2026-09-25 review run (plan: review-run-scope-salvage-and-
# failure-visibility §2.1): the code-review prompt only told reviewers to run
# `git diff`, and the two cursor-agent lanes run `--mode ask`, which has no
# shell — kimi returned `[]` having never seen a diff, and grok reported a test
# failure it could not have run. The orchestrator now writes the scope manifest
# and one diff per file into the phase dir before dispatch, and this block tells
# each lane how to reach them, rendered from the adapter's two `generate`
# declarations (`generate_read_scope`, `runs_shell_in_generate`) so the
# orchestrator never names a provider. It is the ONLY block of the prompt that
# may grant a shell command, and only its `True` text does.

#: The one size cap decision 11.4 keeps. It bounds only the INLINE branch — a
#: lane that cannot open the phase dir gets the plan, the manifest and every
#: diff in the prompt itself — and it is physical, not a guess at a context
#: window: an argv lane's whole prompt is one argument, Linux caps one argument
#: at ``MAX_ARG_STRLEN`` (131072 bytes), and 96 KB leaves room for the template.
INLINE_DIFF_CAP_BYTES = 96 * 1024

#: The same physical limit applied to the WHOLE rendered prompt of an inline
#: slot, not only its ``{diff_access}`` block: the template around that block
#: also carries the implementation record (up to 20 000 chars, UTF-8 widens it),
#: the file list and the working limits, so a block under
#: :data:`INLINE_DIFF_CAP_BYTES` can still sit in a prompt past
#: ``MAX_ARG_STRLEN`` and die as an ``E2BIG`` spawn failure. 4 KB under the
#: kernel's number, for its NUL and an adapter's own wrapping of the prompt
#: argument (aider's ``/ask `` prefix) — the ceiling ``ask_orchestrator``'s
#: ``MAX_PROMPT_BYTES`` uses for the same reason. Measured with
#: :func:`argv_prompt_bytes`.
INLINE_PROMPT_CAP_BYTES = 124 * 1024

#: The values ``LLMProvider.generate_read_scope`` may take.
GENERATE_READ_SCOPES = ("none", "cwd", "any")

#: What the inline branch calls the manifest block. A lane on that branch
#: cannot open the file, so this is the name a truncated file-list notice can
#: point it at ("the ``review-scope.md`` block below") instead of a path.
INLINE_MANIFEST_LABEL = "review-scope.md"

#: What the inline branch calls a commit review's frozen context plan
#: (``commit_range.plan_snapshot``, plans/review-commits.md §2.4): the
#: snapshot's own file name (``commit_brief.CONTEXT_PLAN_SNAPSHOT``), so the
#: commit template's ``{plan_block}`` can point an inline lane at the block.
INLINE_CONTEXT_PLAN_LABEL = "context-plan.md"

#: Shared by the three path texts. Deliberately names no command: only the
#: ``True`` text may.
_MANIFEST_SENTENCE = (
    "The scope manifest at {scope_file} lists every in-scope file with its "
    "status, and names each file's diff file (relative to the manifest) and "
    "its size."
)

#: ``runs_shell_in_generate is True`` — a shell runs, measured. Carries the
#: guidance ``prompts/code_review.txt`` used to hold in its static text, now an
#: optional cross-check rather than the only way to see the change.
DIFF_ACCESS_SHELL_TEXT = (
    "The diff files in {diff_dir} are the authoritative record of the change. "
    + _MANIFEST_SENTENCE
    + " Read the manifest first, then each entry's diff file, with your file "
    "tools.\n"
    "\n"
    "You can also run shell commands. `git diff {base_ref}`, `git show` and "
    "`git log` are an optional cross-check of the diff files, never a "
    "replacement for reading them:\n"
    "1. **All changes at once:** `git diff {base_ref} -- <file1> <file2> ...`\n"
    "2. **One file's changes:** `git diff {base_ref} -- path/to/file`\n"
    "3. **A file's current content:** `cat path/to/file`, or your file-read "
    "tool\n"
    "\n"
    "`git diff {base_ref} -- <path>` is required for any file the manifest "
    "marks `omitted`: it has no diff file, so that command's output is the only "
    "record of its change you can review."
)

#: ``runs_shell_in_generate is False`` — no shell, measured. The first
#: paragraph is plan D2.3's text, word for word.
DIFF_ACCESS_NO_SHELL_TEXT = (
    "You cannot run shell commands. The diff is at {diff_dir}; read it with "
    "your file tools. Do not claim a test passes or fails, because you cannot "
    "run it.\n"
    "\n"
    + _MANIFEST_SENTENCE
    + " The diff files are the authoritative record of the change: read the "
    "manifest first, then each entry's diff file."
)

#: ``runs_shell_in_generate is None`` — not measured. It neither grants nor
#: denies a shell; the first paragraph is plan D2.3's text, word for word.
DIFF_ACCESS_UNMEASURED_TEXT = (
    "The diff files at {diff_dir} are the authoritative record of the change; "
    "read them with your file tools. Do not claim a test passes or fails unless "
    "you actually ran it and saw the result.\n"
    "\n"
    + _MANIFEST_SENTENCE
    + " Read the manifest first, then each entry's diff file."
)

#: What each state adds when ``write_review_diff``'s coverage is ``partial``
#: (git produced no diff for some in-scope path). ``False`` and ``None`` are
#: plan D2.3's text, word for word. ``None``'s names ``git diff`` only as the
#: command the MANIFEST gives, conditionally — it grants nothing.
DIFF_ACCESS_SHELL_PARTIAL = (
    "Diff coverage for this change is partial: git produced no diff file for "
    "the files the manifest marks `omitted`. Run `git diff {base_ref} -- "
    "<path>` for each of them and review it from that output; if the command "
    "fails, list the file as not reviewed. Do not review their current "
    "contents as if they were the change."
)
DIFF_ACCESS_NO_SHELL_PARTIAL = (
    "Files the manifest marks `omitted` have no diff you can read. List them as "
    "not reviewed. Do not review their current contents as if they were the "
    "change."
)
DIFF_ACCESS_UNMEASURED_PARTIAL = (
    "Files the manifest marks `omitted` have no diff file. If you can run the "
    "`git diff` command the manifest gives for one, review it from that output; "
    "otherwise list it as not reviewed. Do not review their current contents as "
    "if they were the change."
)

# A review pinned to a commit (``--head-ref``: a direct two-commit run, or a
# commit brief; plans/review-commits.md §2.5). The change is `git diff <base>
# <head>`, so the working tree is never the reviewed content, for any file, and
# nothing below says it is: the shell text's third command reads a file at the
# head commit (`git show`), never with `cat`. The block opens by naming the
# change as `<base7>..<head7>`, says it ends at the head commit and not at the
# working tree, names the files that changed on disk since that commit, and
# closes with the pinned-head read rule (with the §2.6 trust sentence), so
# `code_review.txt`'s fixed "everything since it" is corrected on a direct run.
# `{sides}` is `<base> <head>` as git takes them, `{head}` the head commit's
# 12-character prefix.

#: ``runs_shell_in_generate is True`` on a pinned review.
DIFF_ACCESS_PINNED_SHELL_TEXT = (
    "The diff files in {diff_dir} are the authoritative record of the change. "
    + _MANIFEST_SENTENCE
    + " Read the manifest first, then each entry's diff file, with your file "
    "tools.\n"
    "\n"
    "You can also run shell commands. `git diff {sides}`, `git show` and "
    "`git log` are an optional cross-check of the diff files, never a "
    "replacement for reading them:\n"
    "1. **All changes at once:** `git diff {sides} -- <file1> <file2> ...`\n"
    "2. **One file's changes:** `git diff {sides} -- path/to/file`\n"
    "3. **A file as the head commit holds it:** `git show {head}:path/to/file`\n"
    "\n"
    "`git diff {sides} -- <path>` is required for any file the manifest "
    "marks `omitted`: it has no diff file, so that command's output is the only "
    "record of its change you can review."
)

#: The shell state's partial-coverage sentence on a pinned review.
DIFF_ACCESS_PINNED_SHELL_PARTIAL = (
    "Diff coverage for this change is partial: git produced no diff file for "
    "the files the manifest marks `omitted`. Run `git diff {sides} -- "
    "<path>` for each of them and review it from that output; if the command "
    "fails, list the file as not reviewed. Do not review their working-tree "
    "contents as if they were the change."
)

#: What a lane with no shell (or an unmeasured one) is told on a pinned review:
#: the read rule's commands need a shell, and its alternative is never the disk.
DIFF_ACCESS_PINNED_NO_SHELL_NOTE = (
    "Without a shell you cannot run the commands below: review from the diff "
    "files and the manifest alone, and read no other file from the working "
    "tree, which may not hold the reviewed code."
)

#: How many changed-on-disk files the opening names before "… and <k> more"
#: (the `[SCOPE_DRIFT]` line names the same ten).
_PINNED_DRIFT_NAMED = 10


def _pinned_opening(
    base_ref: str, head: str, *, root: bool, drifted: Sequence[str],
) -> str:
    """The pinned block's first paragraph: which change, where it ends, what
    drifted. Built by concatenation, never ``str.format``: a drifted path may
    hold braces."""
    h7, h12 = head[:7], head[:12]
    if root:
        text = (
            f"The change under review is `root..{h7}`: every commit up to and "
            f"including `{h7}`, as `git diff {base_ref} {h12}` (the empty tree "
            f"against that commit). It ends at commit `{h7}`, not at the working "
            f"tree. The range starts at the repository's first commit, so the "
            f"diff shows each whole file as new."
        )
    else:
        text = (
            f"The change under review is `{base_ref[:7]}..{h7}`: the net diff "
            f"`git diff {base_ref[:12]} {h12}`, ending at commit `{h7}`, not at "
            f"the working tree."
        )
    names = [str(path) for path in drifted if path]
    if names:
        shown = ", ".join(f"`{name}`" for name in names[:_PINNED_DRIFT_NAMED])
        if len(names) > _PINNED_DRIFT_NAMED:
            shown += f" … and {len(names) - _PINNED_DRIFT_NAMED} more"
        text += (
            f" {len(names)} reviewed file(s) have changed since `{h7}` and "
            f"differ on disk from it, so their working-tree copies are not the "
            f"reviewed code: {shown}."
        )
    return text


def _pinned_rule(base_ref: str, head: str, *, root: bool) -> str:
    """``commit_range.pinned_head_read_rule`` for this pair."""

    return pinned_head_read_rule(None if root else base_ref, head)


def _is_root_base(base_ref: str, cwd: Union[str, Path]) -> bool:
    """Whether *base_ref* is the repository's empty-tree id (a root range)."""

    return bool(base_ref) and is_empty_tree_id(base_ref, str(cwd))

#: The inline branch's opening, by read scope. It names no path: the lane
#: cannot open the phase dir, so every block below is labelled with the name
#: the manifest uses for it, never an address.
_INLINE_HEAD_BY_SCOPE = {
    "none": "You cannot open files in this review, so everything you need is "
    "inline below:",
    "cwd": "The review's artifacts sit outside the directory you can read, so "
    "everything you need is inline below:",
}
_INLINE_HEAD_TAIL_REST = (
    " the scope manifest (`" + INLINE_MANIFEST_LABEL + "`) and one "
    "diff per in-scope source and test file. The diffs are the authoritative "
    "record of the change. Each block is labelled with the name the manifest "
    "uses for it; the labels are names, not files you can open."
)
_INLINE_HEAD_TAIL = " the plan," + _INLINE_HEAD_TAIL_REST
#: The same tail when a commit review has a context plan: its frozen snapshot
#: is one more block, right after the plan's.
_INLINE_HEAD_TAIL_CONTEXT_PLAN = (
    " the plan, the context plan's frozen snapshot (`"
    + INLINE_CONTEXT_PLAN_LABEL + "`)," + _INLINE_HEAD_TAIL_REST
)

#: The inline branch's shell sentence, by ``runs_shell_in_generate``. Only the
#: ``True`` one names a command, as on the path branch.
_INLINE_SHELL_BY_STATE = {
    True: (
        "You can also run shell commands. `git diff {base_ref}`, `git show` and "
        "`git log` are an optional cross-check of the inline diffs, never a "
        "replacement for reading them."
    ),
    False: (
        "You cannot run shell commands. Do not claim a test passes or fails, "
        "because you cannot run it."
    ),
    None: (
        "Do not claim a test passes or fails unless you actually ran it and saw "
        "the result."
    ),
}

#: A diff file name as ``write_review_diff`` writes it (``<n>-<slug>.diff``),
#: as the manifest cites it (relative to itself, under ``diff/``).
_MANIFEST_DIFF_REF_RE = re.compile(r"\bdiff/(\d+-[A-Za-z0-9._-]+\.diff)")


class DiffAccess(NamedTuple):
    """What :func:`render_diff_access` decided for one code-review slot."""

    #: ``"paths"`` (the lane reads the artifacts by absolute path),
    #: ``"inline"`` (they are in :attr:`text`) or ``"unsupported"`` (the slot
    #: must not be dispatched; :attr:`reason` says why).
    mode: str
    #: The rendered ``{diff_access}`` block; ``""`` when unsupported.
    text: str
    #: The adapter's ``generate_read_scope`` (``"cwd"`` for an unknown adapter).
    read_scope: str
    #: The adapter's ``runs_shell_in_generate`` (``None`` for an unknown one).
    #: Not spelled ``shell``: a ``shell: <value>`` line is the identity-text
    #: shape ``redact.redact_text`` redacts (``tests/test_redaction.py``'s
    #: source-tree tripwire).
    runs_shell: Optional[bool]
    #: UTF-8 size of the inline block measured against
    #: :data:`INLINE_DIFF_CAP_BYTES`; ``0`` on the path branch.
    inline_bytes: int
    #: Why the slot is unsupported; ``""`` otherwise.
    reason: str


def _lies_within(path: Union[str, Path], root: Union[str, Path]) -> bool:
    """True when ``path`` resolves to ``root`` or somewhere beneath it."""
    try:
        resolved = os.path.realpath(str(path))
        base = os.path.realpath(str(root))
        return os.path.commonpath([resolved, base]) == base
    except (OSError, ValueError):  # ValueError: different drives on Windows
        return False


def _read_inline_text(path: Union[str, Path]) -> Optional[str]:
    """``path``'s text, or ``None`` when it cannot be read. Never raises."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return None


def _inline_block(label: str, body: str) -> str:
    """One labelled block of the inline payload.

    Delimited rather than fenced: a plan or a diff routinely carries its own
    triple-backtick fences, which would close a fence early.
    """
    content = body.rstrip("\n")
    return f"===== BEGIN {label} =====\n{content}\n===== END {label} ====="


def _render_inline_diff_access(
    *,
    read_scope: str,
    runs_shell: Optional[bool],
    scope_file: str,
    diff_dir: str,
    plan_path: str,
    base_ref: str,
    partial: bool,
    head_ref: Optional[str] = None,
    pinned_opening: str = "",
    pinned_rule: str = "",
    context_plan_path: Optional[str] = None,
) -> DiffAccess:
    """The bounded inline branch, or an explicit unsupported outcome.

    The payload is the plan, the whole manifest and every file in ``diff_dir``
    except ``.gitignore``, in name order (``<n>`` is zero-padded, so name order
    is review order). It is offered only when ALL of it fits
    :data:`INLINE_DIFF_CAP_BYTES` and the coverage is complete: a partial
    inline review would read as a review of the whole change. A missing
    manifest, plan or cited diff file is a reason, never an exception.

    With *context_plan_path* (a commit review's frozen context plan,
    plans/review-commits.md §2.4) the snapshot's text is one more block, the
    :data:`INLINE_CONTEXT_PLAN_LABEL` one right after the plan, and it counts
    against the cap like the rest: a lane that cannot open the snapshot is
    shown it, or is not dispatched at all, never left to judge the range
    without it. An unreadable snapshot is a reason too.

    On a pinned review (*head_ref*) the block opens with *pinned_opening*, its
    shell sentence names ``git diff <base> <head>``, and *pinned_rule* follows
    the shell sentence, ahead of the payload; all of it counts against the cap.
    """
    reasons: List[str] = []
    blocks: List[str] = []

    plan_text = _read_inline_text(plan_path)
    if plan_text is None:
        reasons.append(f"plan file not readable: {plan_path}")
    else:
        blocks.append(_inline_block("plan", plan_text))

    if context_plan_path is not None:
        context_text = _read_inline_text(context_plan_path)
        if context_text is None:
            reasons.append(f"context plan snapshot not readable: {context_plan_path}")
        else:
            blocks.append(_inline_block(INLINE_CONTEXT_PLAN_LABEL, context_text))

    manifest = _read_inline_text(scope_file)
    if manifest is None:
        reasons.append(f"scope manifest not readable: {scope_file}")
    else:
        blocks.append(_inline_block(INLINE_MANIFEST_LABEL, manifest))

    try:
        names = sorted(
            entry.name
            for entry in os.scandir(diff_dir)
            if entry.is_file() and entry.name != ".gitignore"
        )
    except OSError:
        names = []
    unreadable: List[str] = []
    for name in names:
        body = _read_inline_text(os.path.join(diff_dir, name))
        if body is None:
            unreadable.append(name)
            continue
        blocks.append(_inline_block(f"diff/{name}", body))
    if unreadable:
        reasons.append(f"diff files not readable: {', '.join(unreadable)}")
    if manifest is not None:
        cited = set(_MANIFEST_DIFF_REF_RE.findall(manifest))
        absent = sorted(cited - set(names))
        if absent:
            reasons.append(
                f"the manifest names {len(absent)} diff file(s) that do not "
                f"exist: {', '.join(absent[:3])}"
                + (f" (+{len(absent) - 3} more)" if len(absent) > 3 else "")
            )

    if partial:
        reasons.append("diff coverage is partial")

    head = _INLINE_HEAD_BY_SCOPE.get(read_scope, _INLINE_HEAD_BY_SCOPE["none"])
    head += (
        _INLINE_HEAD_TAIL if context_plan_path is None else _INLINE_HEAD_TAIL_CONTEXT_PLAN
    )
    shell_sentence = _INLINE_SHELL_BY_STATE.get(runs_shell, _INLINE_SHELL_BY_STATE[None])
    if head_ref is None:
        text = "\n\n".join(
            [head, shell_sentence.format(base_ref=base_ref)] + blocks
        )
    else:
        sentence = shell_sentence.format(base_ref=f"{base_ref} {head_ref}")
        if runs_shell is not True:
            sentence += " " + DIFF_ACCESS_PINNED_NO_SHELL_NOTE
        text = "\n\n".join(
            [pinned_opening, head, sentence, pinned_rule] + blocks
        )
    size = len(text.encode("utf-8"))
    if size > INLINE_DIFF_CAP_BYTES:
        reasons.append(
            f"inline context {size} B exceeds the {INLINE_DIFF_CAP_BYTES} B cap"
        )

    if reasons:
        return DiffAccess("unsupported", "", read_scope, runs_shell, size, "; ".join(reasons))
    return DiffAccess("inline", text, read_scope, runs_shell, size, "")


def render_diff_access(
    model_spec: str,
    scope_file: Union[str, Path],
    diff_dir: Union[str, Path],
    phase_dir: Union[str, Path],
    cwd: Union[str, Path],
    *,
    base_ref: str,
    coverage: str,
    plan_path: Union[str, Path],
    anchor: Optional[Union[str, Path]] = None,
    head_ref: Optional[str] = None,
    drifted: Sequence[str] = (),
    context_plan_path: Optional[Union[str, Path]] = None,
) -> DiffAccess:
    """Decide how ``model_spec``'s lane reaches the change, and render the block.

    ``scope_file`` is ``code-review/review-scope.md``, ``diff_dir`` is
    ``code-review/diff/``, ``phase_dir`` is the code-review phase dir and
    ``cwd`` is the directory the lane runs in (the repo root), all absolute.
    ``coverage`` is ``write_review_diff``'s ``"complete"`` or ``"partial"``;
    anything but ``"complete"`` is treated as partial, the conservative reading.

    The adapter is resolved exactly as :func:`render_output_location` resolves
    it (``anchor`` is the run's plan path). An unknown adapter reads as
    ``generate_read_scope="cwd"``, ``runs_shell_in_generate=None`` — the base
    defaults, which assert nothing about a shell.

    * **Usable file reads** — ``"any"``, or ``"cwd"`` with ``phase_dir``
      resolving inside ``cwd`` — give ``mode="paths"``: one of three texts
      chosen by ``runs_shell_in_generate``, each naming both absolute paths and
      calling the diff files the authoritative record, plus that state's
      partial-coverage sentence when coverage is partial.
    * **No usable reads** — ``"none"``, or ``"cwd"`` with the phase dir outside
      the repo — give the bounded inline branch, whatever the shell state:
      ``mode="inline"`` when coverage is complete and the whole block fits
      :data:`INLINE_DIFF_CAP_BYTES`, otherwise ``mode="unsupported"`` with an
      empty ``text`` and the reason, so the caller dispatches nothing.

    ``head_ref`` pins the review to a commit (``review-code --head-ref``, a
    commit brief; plans/review-commits.md §2.5): ``base_ref`` is then the base
    commit, or the empty-tree id on a root range. The block opens by naming
    the change as ``<base7>..<head7>`` ending at the head commit, not at the
    working tree, and names *drifted* (the reviewed files that differ on disk
    from it) as changed since that commit; every command reads ``git diff
    <base> <head>`` and a file's content through ``git show <head>:<path>``;
    nothing says the disk is the reviewed content; and the pinned-head read
    rule closes it. ``None`` renders today's text byte for byte.

    ``context_plan_path`` is a commit review's frozen context-plan snapshot
    (``commit_range.plan_snapshot``, plans/review-commits.md §2.4), absolute.
    The paths branch leaves it to the prompt's ``{plan_block}``, which names
    it; the inline branch carries its text as one more block, counted against
    the cap, so an inline lane checks the range against the same plan every
    other reviewer reads, or is not dispatched (too large, or unreadable).

    Never raises for a missing manifest, diff, plan or snapshot file.
    """
    provider_name, _ = parse_model_spec(model_spec, anchor=anchor)
    provider = get_provider(provider_name)
    read_scope = (
        getattr(provider, "generate_read_scope", "cwd") if provider is not None else "cwd"
    )
    shell = (
        getattr(provider, "runs_shell_in_generate", None)
        if provider is not None
        else None
    )
    partial = coverage != "complete"
    scope_file = os.path.abspath(str(scope_file))
    diff_dir = os.path.abspath(str(diff_dir))
    # An empty base ref (no resolvable ref, e.g. an initial commit) fails the
    # whole diff set, so coverage is partial; the command text still has to
    # read as a command with a slot in it rather than `git diff  -- <path>`.
    ref = base_ref or "<base_ref>"
    context_plan = (
        os.path.abspath(str(context_plan_path)) if context_plan_path is not None else None
    )

    reads = read_scope == "any" or (
        read_scope == "cwd" and _lies_within(phase_dir, cwd)
    )
    if head_ref is not None:
        return _render_pinned_diff_access(
            reads=reads,
            read_scope=read_scope,
            runs_shell=shell,
            partial=partial,
            scope_file=scope_file,
            diff_dir=diff_dir,
            plan_path=str(plan_path),
            base_ref=ref,
            head_ref=head_ref,
            drifted=drifted,
            root=_is_root_base(base_ref, cwd),
            context_plan_path=context_plan,
        )
    if not reads:
        return _render_inline_diff_access(
            read_scope=read_scope,
            runs_shell=shell,
            scope_file=scope_file,
            diff_dir=diff_dir,
            plan_path=str(plan_path),
            base_ref=ref,
            partial=partial,
            context_plan_path=context_plan,
        )

    if shell is True:
        text, extra = DIFF_ACCESS_SHELL_TEXT, DIFF_ACCESS_SHELL_PARTIAL
    elif shell is False:
        text, extra = DIFF_ACCESS_NO_SHELL_TEXT, DIFF_ACCESS_NO_SHELL_PARTIAL
    else:
        text, extra = DIFF_ACCESS_UNMEASURED_TEXT, DIFF_ACCESS_UNMEASURED_PARTIAL
    if partial:
        text = text + "\n\n" + extra
    rendered = text.format(scope_file=scope_file, diff_dir=diff_dir, base_ref=ref)
    return DiffAccess("paths", rendered, read_scope, shell, 0, "")


def _render_pinned_diff_access(
    *,
    reads: bool,
    read_scope: str,
    runs_shell: Optional[bool],
    partial: bool,
    scope_file: str,
    diff_dir: str,
    plan_path: str,
    base_ref: str,
    head_ref: str,
    drifted: Sequence[str],
    root: bool,
    context_plan_path: Optional[str] = None,
) -> DiffAccess:
    """:func:`render_diff_access` for a review pinned to *head_ref*.

    The same branch decision (paths, inline or unsupported) and the same
    per-state texts, with the head commit as the new side: the opening names
    the change and the drifted files, the body's commands take ``<base>
    <head>``, and the pinned-head read rule follows. Only the template parts
    go through ``str.format``; the opening and the rule are concatenated, as
    paths and commit text may hold braces.
    """
    opening = _pinned_opening(base_ref, head_ref, root=root, drifted=drifted)
    rule = _pinned_rule(base_ref, head_ref, root=root)
    if not reads:
        return _render_inline_diff_access(
            read_scope=read_scope,
            runs_shell=runs_shell,
            scope_file=scope_file,
            diff_dir=diff_dir,
            plan_path=plan_path,
            base_ref=base_ref,
            partial=partial,
            head_ref=head_ref,
            pinned_opening=opening,
            pinned_rule=rule,
            context_plan_path=context_plan_path,
        )
    if runs_shell is True:
        text, extra = DIFF_ACCESS_PINNED_SHELL_TEXT, DIFF_ACCESS_PINNED_SHELL_PARTIAL
    elif runs_shell is False:
        text, extra = DIFF_ACCESS_NO_SHELL_TEXT, DIFF_ACCESS_NO_SHELL_PARTIAL
    else:
        text, extra = DIFF_ACCESS_UNMEASURED_TEXT, DIFF_ACCESS_UNMEASURED_PARTIAL
    if partial:
        text = text + "\n\n" + extra
    body = text.format(
        scope_file=scope_file, diff_dir=diff_dir, base_ref=base_ref,
        sides=f"{base_ref} {head_ref}", head=head_ref[:12],
    )
    parts = [opening, body]
    if runs_shell is not True:
        parts.append(DIFF_ACCESS_PINNED_NO_SHELL_NOTE)
    parts.append(rule)
    return DiffAccess("paths", "\n\n".join(parts), read_scope, runs_shell, 0, "")


#: The ``{working_limits}`` block the review templates carry just above their
#: output sections (plan: review-run-scope-salvage-and-failure-visibility D3.2).
#: Measured on the 2026-09-25 review run: a pi code-review slot with a 1200 s
#: budget started ``timeout 1700 python -m pytest tests`` and was killed
#: mid-suite, having written nothing — nothing in the prompt told it how long it
#: had or that the suite was off limits. So the block states the real number of minutes and
#: forbids long commands, while still allowing ONE narrowly scoped test file
#: (decision 11.7, the same allowance ``prompts/implementation_task.txt`` makes).
#:
#: It deliberately names no shell command: it reaches every Lane A lane,
#: cursor-agent and claude-code included, which have no shell, so a "use
#: ``git diff``" line here would grant what ``{diff_access}`` denies in the same
#: prompt. The test-claim line is here rather than only in ``{diff_access}``
#: because the false HIGH finding in that run's evidence was a model asserting
#: a test result it had not run, and every lane can make that claim. Advisory
#: text only — what bounds a model that ignores it is the slot's kill.
WORKING_LIMITS_BLOCK = (
    "## Working limits\n"
    "- This review is stopped after about {minutes}. Anything unfinished at "
    "that point is lost, so write your answer well before then.\n"
    "- Do NOT run the project's test suite, builds, linters, installers, or any "
    "other long-running command. This is a read-only review. If a finding "
    "depends on a test's result, you may run that ONE narrowly scoped test "
    "file, and only if you can run commands at all.\n"
    "- Do NOT modify, create or delete any file except the output file named "
    "below.\n"
    "- Do NOT claim that a test passes or fails unless you ran it during this "
    "review and saw its result. Say what a test covers, not what it would "
    "report."
)


def render_working_limits(timeout_s: Union[int, float]) -> str:
    """The ``{working_limits}`` block for an attempt with ``timeout_s`` seconds.

    ``timeout_s`` must be the budget THIS attempt is really spawned with — the
    ``timeout`` handed to :func:`invoke_with_file_output`, or the ladder's slice
    on the review-plan/review-tasks fan-out — because the number is the point:
    the incident's model chose ``timeout 1700`` inside a 1200 s slot. Minutes are
    floored (never promise time the kill will not honour) and never below 1, so
    a sub-minute slot still reads as a deadline rather than "about 0 minutes".
    """
    minutes = max(1, int(timeout_s // 60))
    unit = "minute" if minutes == 1 else "minutes"
    return WORKING_LIMITS_BLOCK.format(minutes=f"{minutes} {unit}")
