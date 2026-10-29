#!/usr/bin/env python3
"""The five materialized-subagent prompt generators (D2i).

One module owns prompt assembly for every subagent kind the orchestrators
delegate: ``validation``/``revalidation``, ``consolidation``, ``salvage``,
``human_decision_judge`` and ``task_generation``. Before this module the
prompts lived in instruction markdown, so only a Claude Code agent reading that
markdown could assemble them; materializing them here is what makes one task
file executable by a native-subagent host *and* by a Python executor with
byte-identical prompt text.

Two properties are load-bearing and enforced by tests:

* **Every generator is pure.** No file or network I/O, no clock, no config
  lookup, no environment read — callers read files and pass records in. Identical
  inputs therefore render byte-identical prompt text, which is what makes
  per-kind golden prompt fixtures and the result-contract equivalence diff
  possible at all.
* **No generator interpolates a path the runner may be unable to open.** Under
  ``context_mode: inline`` every input travels inside the prompt as text: the
  plan excerpt, the suggestion records, the salvage request's ``raw_output``, the
  judge's criteria. ``plan_file``, ``grouped_file`` and ``output_path`` are
  provenance and invoker plumbing, never subagent instructions — a headless
  ``claude -p`` / ``codex exec`` invocation is not guaranteed a workspace-read
  tool, and a prompt full of unreadable paths degrades into a confidently empty
  answer rather than an error. There are two named exceptions, both
  ``context_mode: workspace-read``: ``task_generation``, whose context is the
  repository and which names exactly one path, the pinned repo root; and a
  validation/revalidation task, which names at most one path per document
  whose context exceeded the inline limit, each a hash-bound snapshot of that
  document (``context_sources``; ``plans/validation-context-by-path-and-codex-0156-fallout.md``
  §2.3). Every runner able to execute a validation task (``agent-readonly``)
  declares ``supports_workspace_reads``, which a test pins; the excerpt stays
  inline either way.

Every generator also ends the same way: the callee **prints** its result and the
invoker persists it (the D3a print/persist contract). No prompt tells a subagent
to write a file.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Sequence

try:  # Python 3.8+: TypedDict lives in typing
    from typing import TypedDict
except ImportError:  # pragma: no cover
    TypedDict = dict  # type: ignore[misc,assignment]

__all__ = [
    "ContextSource",
    "HUMAN_DECISION_JUDGE_RULES",
    "TASK_AUTHORING_RULES",
    "REFERENCE_SECTIONS",
    "build_validation_prompt",
    "code_review_validation_guidance",
    "build_consolidation_prompt",
    "build_salvage_prompt",
    "build_human_decision_judge_prompt",
    "build_task_generation_prompt",
    "build_schema_repair_prompt",
    "build_nothing_changed_resend_prompt",
    "NOTHING_CHANGED_RESEND_HEADING",
    "SCHEMA_REPAIR_EXAMPLES",
    "SCHEMA_REPAIR_SHAPES",
    "SCHEMA_REPAIR_TOP_KEYS",
    "TASK_GENERATION_REPLY_SHAPE",
    "APPLY_REPORT_KINDS",
    "APPLY_REPORT_REPLY_SHAPE",
    "WRITE_REPORT_REPAIR_KINDS",
    "WRITE_REPORT_REPLY_SHAPE",
    "render_reference_section",
    "reference_section_targets",
]


def _json_block(value: Any) -> str:
    """Deterministic JSON rendering for embedding in a prompt.

    ``sort_keys`` is deliberate: two callers that build the same record with
    keys inserted in a different order must still render the same prompt.
    """
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)


# ===========================================================================
# validation / revalidation
# ===========================================================================

#: The reply shape every validation/revalidation batch must print.
#:
#: ``group_index`` is shown as an unfillable placeholder rather than a literal
#: ``0`` on purpose: with a numeric example there, models copy the example
#: instead of echoing the group's own value (18 of 32 verdicts in one run, 41 of
#: 46 in another, echoed 0,1,2,3…). The hash join absorbs it —
#: ``merge_batched_validation_results`` routes by ``group_hash`` and only counts
#: the mismatch — but the cheaper fix is a template with no number to copy. A
#: model that copies the placeholder *text* is tolerated too: the merge coerces a
#: non-integer echo to "matches nothing" rather than crashing.
#:
#: ``metadata`` comes first and ``groups`` last (fix round 24). With ``groups``
#: first, Claude Code's Sonnet validators kept writing
#: ``{"groups":[{…},"metadata":{…}}`` — the ``]`` dropped at the one place the
#: array is followed by another key (3 of 14 batches on 2026-10-01, again on
#: 10-04 and 10-07, one-group batches included), while the judge's reply, whose
#: array is its last key, has not shown it. Key order means nothing to any
#: reader of the reply; a reply that still breaks is re-asked once
#: (``util check-reply``), never repaired.
#:
#: Fix round 26 (live run 11, Claude Code review-plan batch 5): a Sonnet
#: validator printed its object with two hashes swapped, then "Wait, the
#: hashes above are swapped relative to the groups; corrected reply:" and a
#: second object. The native file did not parse and the batch was re-asked.
#: The contract now says to check the hashes before printing and to print the
#: object once, and rule 2 says a neighbouring group's hash moves the verdict
#: (only a hash foreign to the batch is discarded). A reply holding several
#: objects is still re-asked, never cut down to one (``util check-reply``
#: names it).
_VALIDATION_REPLY_CONTRACT = '''## Reply

Print ONE JSON object and nothing else — no prose, no markdown fences, no
explanation. Do not write any file; whoever invoked you persists your reply.
Your reply is parsed as-is, and a reply that does not parse is thrown away:
the first character is `{` and the last is the `}` that closes it. Keep every
`reason` to one short line with no raw double quotes or line breaks inside it.
`metadata` comes first and `groups` last, so the reply ends with the last
result's `}`, the `]` that closes `groups` and the `}` that closes the object:
`}]}`. Re-read the object once for balanced brackets before you finish.
Settle every verdict, and check each result's `group_hash` against its group
above, before you print anything, then print the object once: a reply that
adds a correction, a note or a second object after the first does not parse.

{
  "metadata": {"model": "<the model you are>", "timestamp": "<ISO 8601>", "schema_version": "2.1"},
  "groups": [
    {"group_index": <the group's group_index value>, "group_hash": "<copy the group_hash of the group verbatim>", "status": "valid|invalid|needs-human-decision", "reason": "<one brief sentence>", "confidence": 0.0}
  ]
}

Rules:
1. Output EXACTLY one result per requested group — no more, no fewer.
2. Each group above carries its own `group_index` — echo that group's
   `group_index` value back into its result, and copy its `group_hash` value
   verbatim too. The `group_index` you echo is advisory; the hash is what the
   results are joined on, so a wrong hash discards the result, and the hash
   of another group in this batch puts your verdict on that group.
3. Confidence is a number between 0.0 and 1.0.
4. Be conservative: when you cannot decide from the context given, answer
   "needs-human-decision" rather than guessing.
'''


#: Appended to every plan validation (context label "Plan content"). The plan
#: reviewers are told task decomposition is out of scope (prompts/plan_review.txt);
#: this is the same rule for a finding that got through anyway. Without it the
#: 2026-10-01 racing-game run validated "the plan has no task breakdown" as valid
#: on all three hosts (HIGH on one), apply-suggestions wrote a task list into the
#: plan, and generate-tasks then wrote a second, diverging one.
#:
#: The last sentence keeps the rule from swallowing a real sequencing gap: "the
#: plan never says the data migration must precede the schema switch" reads as
#: "missing implementation order" to a literal validator, yet it is a constraint
#: of the design (adversarial review, 2026-10-02).
PLAN_VALIDATION_SCOPE_GUIDANCE = '''Scope: a plan is a design document. Breaking it into implementation tasks, with
ids, dependencies and an order, is a later phase (task generation). A finding
whose only complaint is that the plan has no task breakdown, task list,
implementation order, dependency graph or milestones is "invalid": not
applicable to a plan review. A finding that names a concrete design gap which
would block writing those tasks is judged on that gap. A missing ordering
constraint between parts of the design (a data migration that must precede the
schema switch) is a design gap, judged on its merits.'''


#: Extra guidance for code-review validation, phrased in **capability-neutral**
#: terms. It refers only to the `file`/`line_range` values already embedded in the
#: issue records — never to a task's `plan_file`, `grouped_file` or `output_path`
#: — and it conditions every workspace action on the runner actually having one, so
#: the same prompt is correct for an agentic runner and for a headless one.
CODE_REVIEW_VALIDATION_GUIDANCE = '''Each issue record carries `file` and `line_range` when the finding has a
location.

- If you can read the repository, open those locations and compare what the code
  actually does against what the issue claims. Keep the effort bounded: at most 5
  files per group (prefer explicitly named files, then the narrowest line ranges,
  breaking ties by importance HIGH > MEDIUM > LOW), and at most ~200 lines around
  each referenced range.
- If you cannot read the repository, judge from the records and the context above
  alone.
- When an issue has no `file`/`line_range`, try the description plus the context
  above; if the missing location makes the claim unverifiable, answer
  "needs-human-decision" and say that the location metadata was absent.'''


#: :data:`CODE_REVIEW_VALIDATION_GUIDANCE` for a review pinned to a commit
#: (``review-code --head-ref``, a commit brief; plans/review-commits.md §2.5).
#: The same bounds and the same capability-neutral shape, but a location is
#: read at the head commit, never in the working tree, which may hold other
#: bytes: the excerpts above were read there too. ``{head}`` is the head
#: commit's 12-character prefix and ``{change}`` the range as a user reads it.
_PINNED_CODE_REVIEW_VALIDATION_GUIDANCE = '''Each issue record carries `file` and `line_range` when the finding has a
location. The change under review is `{change}`: it ends at commit `{head}`, not
at the working tree, and every line number in the records and in the context
above is a line of the file as that commit (or, for a file the range removed,
its base) holds it.

- If you can read the repository, read those locations at commit `{head}` as the
  rule below says, never from the working tree, and compare what the code
  actually does against what the issue claims. Keep the effort bounded: at most
  5 files per group (prefer explicitly named files, then the narrowest line
  ranges, breaking ties by importance HIGH > MEDIUM > LOW), and at most ~200
  lines around each referenced range.
- If you cannot read the repository, judge from the records and the context above
  alone.
- When an issue has no `file`/`line_range`, try the description plus the context
  above; if the missing location makes the claim unverifiable, answer
  "needs-human-decision" and say that the location metadata was absent.

Wherever this prompt says to open the repository, read it, or check a claim
against existing code, it means reading it at commit `{head}`:

{read_rule}'''


def code_review_validation_guidance(
    *,
    read_rule: Optional[str] = None,
    head: Optional[str] = None,
    change: Optional[str] = None,
    plan_snapshot: Optional[str] = None,
    plan_sha256: Optional[str] = None,
) -> str:
    """The code-review validation guidance, pinned to a commit when asked.

    Pure, like every generator here: the caller renders *read_rule*
    (``utils.commit_range.pinned_head_read_rule``, which already ends with the
    §2.6 trust sentence) and passes the head commit and the range's display
    spelling (*change*). With neither, and no *plan_snapshot*, this returns
    :data:`CODE_REVIEW_VALIDATION_GUIDANCE` unchanged, so an unpinned review's
    prompts and goldens do not move. Both validation legs (Lane B's executor
    and a host's native subagents) run the same materialized prompt, so this
    one text reaches both, and the revalidation tasks of a pinned run too
    (``utils.validation.pinned_validation_guidance``).

    *plan_snapshot* is a commit review's frozen context plan
    (``commit_range.plan_snapshot``, repository-relative, §2.4 "The context
    plan is frozen"): the guidance names that copy, never the user's file,
    which may have changed since the review began.
    """
    if read_rule and head:
        text = _PINNED_CODE_REVIEW_VALIDATION_GUIDANCE.format(
            head=head[:12], change=change or head[:12], read_rule=read_rule.strip(),
        )
    else:
        text = CODE_REVIEW_VALIDATION_GUIDANCE
    if plan_snapshot:
        digest = f" (sha256 `{plan_sha256[:12]}`)" if plan_sha256 else ""
        text += (
            "\n\nThe review was also checked against a context plan. Its frozen "
            f"copy is `{plan_snapshot}`{digest}, relative to the repository root: "
            "read that file for any claim about the context plan, never the "
            "plan's original path, which may have changed since the review."
        )
    return text


class ContextSource(TypedDict, total=False):
    """One context document of a validation round (§2.3 step 7).

    ``mode`` is ``inline`` (fits, no path), ``path`` (over the limit; the
    excerpt stays and ``abs_path`` names the hash-bound snapshot of the whole
    document) or ``truncated`` (over the limit, nothing readable). Only a
    ``path`` source reaches the prompt as a path.
    """

    label: str
    kind: str
    path: Optional[str]
    abs_path: Optional[str]
    sha256: Optional[str]
    bytes: int
    chars_shown: int
    truncated: bool
    mode: str


#: How a ``path`` source's document is named in the prompt.
_FILE_HEADING = {"plan": "Plan file", "tasks": "Tasks file"}
_FILE_NOUN = {"plan": "plan", "tasks": "tasks file"}


def _file_sections(sources: Sequence[Dict[str, Any]]) -> str:
    """The ``## Plan file`` / ``## Tasks file`` sections, in ask.txt's wording."""
    blocks = []
    for source in sources:
        label = str(source.get("label") or "plan")
        heading = _FILE_HEADING.get(label, f"{label.capitalize()} file")
        noun = _FILE_NOUN.get(label, label)
        blocks.append(
            f"## {heading}\n\n"
            f"The {noun} under review is on disk at this absolute path, which "
            f"you may read directly:\n\n"
            f"{source.get('abs_path') or source.get('path')}\n\n"
            f"The context below carries only an excerpt of it (its first "
            f"{source.get('chars_shown')} characters; the file is "
            f"{source.get('bytes')} bytes) and ends in a truncation marker. "
            f"Read the full {noun} from the path above.\n"
        )
    return "\n".join(blocks) + "\n"


def _documents_phrase(sources: Sequence[Dict[str, Any]]) -> str:
    nouns = [_FILE_NOUN.get(str(s.get("label")), str(s.get("label"))) for s in sources]
    if len(nouns) == 1:
        return f"the {nouns[0]}"
    return "the " + " and the ".join(nouns)


def _task_section(
    count: int,
    sources: Optional[Sequence[Dict[str, Any]]],
    inline_blocks: int = 0,
) -> str:
    """The ``## Task`` sentences; the path variant when any source is by path.

    The path variant is scoped per document: only the documents in
    ``sources`` (the ``mode: path`` ones) are judged against their file.
    ``inline_blocks`` counts the context blocks whose document is *not* named
    by path (inline, or cut with no file); each of those stays complete as
    shown and is the text a claim about that document is judged against, so
    a mixed round never judges a task-list omission against the plan file.
    """
    if not sources:
        return f'''## Task

For each of the {count} suggestion groups above, decide:
- "valid": the issue is real and should be addressed
- "invalid": a false positive — incorrect or not applicable
- "needs-human-decision": cannot be determined from the context above and
  requires human judgment

Compare each group against the context above to verify it. Judge only the
groups listed above; ignore anything else.

When a suggestion claims something about existing code — a function name, a
line number, current behaviour — and you can read the repository you are
running in, open it and check the claim before answering; do not rely on the
context above alone when the code itself is one read away. Reserve
"needs-human-decision" for genuine judgment calls (a product or design
trade-off), never for a claim you could have checked but did not look at. If
you cannot read the repository, judge from the records and the context above
alone.

Do not probe system paths, services or databases (anything outside the
repository, a database client, a service status): the repository and the
context above are the evidence.

A claim that the plan or the tasks omit something — "the plan does not specify
X", "the tasks never say to reset X" — is judged against the plan or tasks text
above, not against the working tree: the plan is what an implementer follows,
and a partially implemented tree is exactly the situation this review exists
for. Code that already does X does not make such a claim invalid; it makes it
valid — document or decide it — and the reason should say that the code already
does X. Where the artifact under review is a diff or a code change rather than a
plan, that change is the text such a claim is judged against.'''
    docs = _documents_phrase(sources)
    headings = " / ".join(
        f"`## {_FILE_HEADING.get(str(s.get('label')), 'File')}`" for s in sources
    )
    verb = "is" if len(sources) == 1 else "are"
    if inline_blocks:
        inline_scope = (
            "\n\nEvery other context block is not named by path: judge it as it is"
            "\nshown, since it is the authority for the document it carries. A file"
            "\nnamed above never settles a claim about a document it does not hold."
        )
        inline_rule = (
            "\nA claim about a document that is not named by path is judged against"
            "\nthat document's own context block."
        )
    else:
        inline_scope = ""
        inline_rule = ""
    return f'''## Task

For each of the {count} suggestion groups above, decide:
- "valid": the issue is real and should be addressed
- "invalid": a false positive — incorrect or not applicable
- "needs-human-decision": a genuine judgment call (a product or design
  trade-off) that the full documents cannot settle. It is never the answer for
  a section an excerpt cut or dropped: read the file instead.

{docs[0].upper() + docs[1:]} {verb} named by path under {headings} above. A
file named there is the whole document; its excerpt in the context block is a
convenience copy of its head, authoritative only for the sections it shows in
full. For a document named by path, read the file in full and compare each
group against it. Judge only the groups listed above; ignore anything
else.{inline_scope}

When a suggestion claims something about existing code — a function name, a
line number, current behaviour — and you can read the repository you are
running in, open it and check the claim before answering. Reserve
"needs-human-decision" for genuine judgment calls, never for a claim you could
have checked but did not look at.

Do not probe system paths, services or databases (anything outside the
repository, a database client, a service status): the repository and the
documents named above are the evidence.

A claim that the plan or the tasks omit something — "the plan does not specify
X", "the tasks never say to reset X" — and any claim that something is never
defined, never reset or never tested, or that two sections disagree, is judged
against the document it is about. For a document named by path it is judged
against the full file named above for that document, not against its
excerpt.{inline_rule}
No such claim is judged against the working tree: the plan is what an
implementer follows, and a partially implemented tree is exactly the situation
this review exists for. Code that already does X does not make such a claim
invalid; it makes it valid — document or decide it — and the reason should say
that the code already does X. Where the artifact under review is a diff or a
code change rather than a plan, that change is the text such a claim is judged
against.

Insufficient context is explicit. If reading a file named above fails, comes
back incomplete, or you cannot reach it, do not guess from its excerpt: answer
"needs-human-decision" with a reason that starts `insufficient-context:` and
names the sections you could not read.'''


def build_validation_prompt(
    *,
    plan_excerpt: str,
    suggestion_records: Sequence[Dict[str, Any]],
    kind: str = "validation",
    context_label: str = "Plan content",
    secondary_excerpt: str = "",
    secondary_label: str = "",
    extra_instructions: str = "",
    context_sources: Optional[List[ContextSource]] = None,
) -> str:
    """Render the prompt for one validation or revalidation batch.

    Args:
        plan_excerpt: The one shared context excerpt for this phase, already
            truncated by the caller (excerpted once per phase and reused across
            batches, so batches never re-truncate and prompts stay
            deterministic).
        suggestion_records: This batch's suggestion records — the values, not a
            path to them. Each record carries at least ``group_hash``, ``theme``
            and its ``suggestions``.
        kind: ``"validation"`` or ``"revalidation"``; only the framing sentence
            differs.
        context_label: What the embedded context is (``"Plan content"``,
            ``"Tasks file"``, ``"Diff"``, …).
        secondary_excerpt: An optional **second** context block, for a phase
            whose suggestions are about one document but are judged against two
            — review-tasks embeds the plan *and* the task list the suggestions
            name. Excerpted by the caller like the first, and rendered as its
            own ``## Context (…)`` section so the two are never read as one.
        secondary_label: What that second block is; required whenever
            ``secondary_excerpt`` is given.
        extra_instructions: Optional phase-specific guidance appended before the
            reply contract (e.g. :data:`CODE_REVIEW_VALIDATION_GUIDANCE`). Must be
            capability-neutral and must not name a task's path fields.
        context_sources: The round's context source records (§2.3 step 7).
            Only a ``mode: path`` source is rendered: its document gets a
            ``## Plan file`` / ``## Tasks file`` section naming the snapshot
            by absolute path above the context blocks, and the ``## Task``
            sentences that judge against "the context above" switch to the path
            variant, scoped per document (a file named by path is read in
            full and its excerpt is authoritative only for what it shows; a
            context block not named by path stays complete as shown; an
            omission claim is judged against the document it is about; an
            unreadable file is an explicit ``insufficient-context:``
            answer). With no ``path`` source the
            prompt is byte-identical to what it was.

    Returns:
        The complete prompt text.
    """
    if kind == "revalidation":
        opening = (
            "You are re-validating review suggestions that a previous "
            "validation pass could not classify."
        )
    else:
        opening = "You are validating review suggestions for accuracy."

    if secondary_excerpt and not secondary_label:
        raise ValueError(
            "secondary_excerpt needs a secondary_label: an unlabelled second "
            "'## Context ()' block is exactly the ambiguity two context "
            "sections exist to remove."
        )
    secondary = (
        f"\n## Context ({secondary_label})\n\n{secondary_excerpt}\n"
        if secondary_excerpt
        else ""
    )
    count = len(suggestion_records)
    # The default label is the plan review's; code review passes extra
    # instructions of its own and review-tasks labels its two contexts.
    if context_label == "Plan content" and not extra_instructions.strip():
        extra_instructions = PLAN_VALIDATION_SCOPE_GUIDANCE
    guidance = f"\n{extra_instructions.strip()}\n" if extra_instructions.strip() else ""
    by_path = [
        dict(source) for source in (context_sources or [])
        if isinstance(source, dict) and source.get("mode") == "path"
    ]
    files = _file_sections(by_path) if by_path else ""
    # Context blocks whose document is not named by path (inline, or cut with
    # no readable file): the path variant keeps each one its own authority.
    blocks = 1 + (1 if secondary_excerpt else 0)
    inline_blocks = max(0, blocks - len(by_path))
    return f'''{opening}

{files}## Context ({context_label})

{plan_excerpt}
{secondary}
## Suggestion groups to validate ({count})

{_json_block(list(suggestion_records))}

{_task_section(count, by_path, inline_blocks)}
{guidance}
{_VALIDATION_REPLY_CONTRACT}'''


# ===========================================================================
# consolidation
# ===========================================================================

#: Filled into the ``{OUTPUT_SCHEMA}`` slot of
#: ``prompts/consolidate_suggestions.txt``. Mirrors
#: ``schemas/consolidation_batch.schema.json``, which the reaggregation step
#: validates each ``consolidation_batch_N.json`` against.
CONSOLIDATION_OUTPUT_SCHEMA = '''{
  "verification": "passed",
  "clusters": [
    {
      "title": "<new synthesized title, max 120 characters>",
      "description": "<synthesized description preserving nuance from every underlying suggestion>",
      "importance": "HIGH|MEDIUM|LOW",
      "type": "addition|modification|deletion|clarification",
      "underlying_group_ids": ["<group_id>", "<group_id>"],
      "underlying_group_indices": [0, 1],
      "reasoning": "<1-2 sentences on why these belong together>"
    }
  ],
  "singletons": [
    {
      "group_id": "<group_id>",
      "group_index": 0,
      "reasoning": "<1-2 sentences on why this group stands alone>"
    }
  ]
}'''

CONSOLIDATION_EXAMPLE_INPUT = '''[
  {"index": 0, "group_id": "aaaa000000000000", "theme": "Add retry to the upload call", "importance": "MEDIUM", "type": "addition", "suggestions": [{"title": "Retry uploads", "description": "The upload call has no retry, so a transient 503 loses the file."}]},
  {"index": 1, "group_id": "bbbb000000000000", "theme": "Uploads need backoff on transient failures", "importance": "HIGH", "type": "modification", "suggestions": [{"title": "Exponential backoff for uploads", "description": "Wrap the upload in exponential backoff; a bare retry loop will hammer the service."}]},
  {"index": 2, "group_id": "cccc000000000000", "theme": "Document the config file location", "importance": "LOW", "type": "clarification", "suggestions": [{"title": "Say where config lives", "description": "The plan never states which directory the config file is read from."}]}
]'''

CONSOLIDATION_EXAMPLE_OUTPUT = '''{
  "verification": "passed",
  "clusters": [
    {
      "title": "Make uploads resilient to transient failures with bounded exponential backoff",
      "description": "The upload call currently has no retry at all, so a transient 503 loses the file; and a bare retry loop would hammer the service, so the retry must use bounded exponential backoff rather than immediate repetition.",
      "importance": "HIGH",
      "type": "modification",
      "underlying_group_ids": ["aaaa000000000000", "bbbb000000000000"],
      "underlying_group_indices": [0, 1],
      "reasoning": "Both address the same underlying concern — upload failures on transient errors — one naming the missing retry and the other the backoff policy it needs."
    }
  ],
  "singletons": [
    {
      "group_id": "cccc000000000000",
      "group_index": 2,
      "reasoning": "Documentation of the config location is unrelated to upload reliability."
    }
  ]
}'''

CONSOLIDATION_NON_OVERLAP_CONSTRAINTS = '''- Every input group appears EXACTLY ONCE across `clusters[].underlying_group_ids` and `singletons[].group_id`. Never in two clusters, never in both a cluster and singletons, never omitted.
- `underlying_group_ids` and `underlying_group_indices` must have the same length and must correspond element-by-element.
- A cluster contains at least 2 groups. A single group is a singleton, not a one-element cluster.
- Copy `group_id` and `index` values verbatim from the input. Never invent, renumber or reformat them.
- Set `"verification": "passed"` only after you have checked the three rules above against your own output. If you cannot satisfy them, return every group as a singleton instead of guessing.'''


def build_consolidation_prompt(
    *,
    template: str,
    group_records: Sequence[Dict[str, Any]],
) -> str:
    """Render the prompt for one consolidation batch.

    Args:
        template: The text of ``prompts/consolidate_suggestions.txt``. Passed in
            rather than loaded so this function stays pure.
        group_records: This batch's group records — the values, not a path.

    Returns:
        The filled template plus the print-only reply contract.
    """
    filled = (
        template
        .replace("{GROUPS_JSON}", _json_block(list(group_records)))
        .replace("{GROUP_COUNT}", str(len(group_records)))
        .replace("{OUTPUT_SCHEMA}", CONSOLIDATION_OUTPUT_SCHEMA)
        .replace("{EXAMPLE_INPUT}", CONSOLIDATION_EXAMPLE_INPUT)
        .replace("{EXAMPLE_OUTPUT}", CONSOLIDATION_EXAMPLE_OUTPUT)
        .replace("{NON_OVERLAP_CONSTRAINTS}", CONSOLIDATION_NON_OVERLAP_CONSTRAINTS)
    )
    return filled.rstrip("\n") + '''

## Reply

Print ONLY the JSON object described above — no prose, no markdown fences, no
explanation. Do not write any file; whoever invoked you persists your reply.
'''


# ===========================================================================
# salvage
# ===========================================================================

def build_salvage_prompt(salvage_request: Dict[str, Any]) -> str:
    """Render the prompt for one salvage request.

    Salvage repairs an unparseable *model review* from the fan-out, never a
    failed subagent task, so it carries no batch context: its entire state is
    the salvage-request record the orchestrator already wrote. The record's
    ``raw_output``, ``expected_type`` and ``expected_schema`` travel as values,
    not as a path — and are never truncated, since truncation salvages half an
    array.

    Two steps that used to live in this prompt are invoker duties now: the
    pre-write backup runs on the invoker side immediately before it persists the
    output, and deleting the salvage request is the orchestrator's job after
    reaggregation. What is left is extraction alone, which is why salvage no
    longer needs workspace access.

    **"Nothing recoverable" is a sentinel object, never an empty array.** A
    salvage task's ``output_name`` *is* the model's own result path, so an empty
    array printed here would be persisted over that path and reaggregation would
    read it as "this model reviewed the input and found nothing" — a model that
    never produced a parseable word becomes a phantom participant, and finding
    priority is scored partly by how many models flagged something. So the
    fallback is ``{"salvage_failed": true, "reason": ...}``, which
    ``subagent_executor`` recognises as a failed, never-retried outcome that
    writes nothing and carries the subagent's own reason into
    ``subagent_batch_report.json``. A bare empty array stays legal *as a
    recovery* — it is what a model whose reply really was an empty review
    produced — which is exactly why the negative needs a shape of its own.

    Args:
        salvage_request: The salvage-request record (``model``, ``phase``,
            ``raw_output``, ``expected_type``, ``expected_schema``, …).

    Returns:
        The complete prompt text.
    """
    model = salvage_request.get("model", "unknown")
    phase = salvage_request.get("phase", "unknown")
    expected_type = salvage_request.get("expected_type", "array")
    expected_schema = salvage_request.get("expected_schema", {})
    raw_output = salvage_request.get("raw_output", "")

    return f'''You are a JSON extraction specialist. Recover the valid JSON {expected_type}
from one model's malformed output.

The output below came from model `{model}` during the `{phase}` phase. It was
supposed to be a JSON {expected_type} and could not be parsed.

## Expected shape

{_json_block(expected_schema)}

## Raw output to salvage

<<<RAW_OUTPUT
{raw_output}
RAW_OUTPUT

## Task

1. Find the JSON {expected_type} inside the raw output above. If several
   complete ones are present, use the last complete one.
2. Repair only mechanical syntax damage — trailing commas, unterminated
   strings, stray prose before or after the {expected_type}, markdown fences.
3. Drop any entry that is missing a required field from the expected shape
   rather than inventing values for it.
4. Never add, rewrite or summarize content. You are recovering what the model
   already produced, not authoring it.

## Reply

Print ONLY the extracted JSON {expected_type} and nothing else — no prose, no
markdown fences, no explanation. Do not write any file; whoever invoked you
persists your reply.

If the raw output holds nothing recoverable at all, print exactly this object
instead — never an empty {expected_type}, which is indistinguishable from a
review that ran and genuinely found nothing:

{{"salvage_failed": true, "reason": "<what the raw output actually was>"}}

The reason is one short factual clause naming what the raw output turned out to
be — an authentication error, a stack trace, a truncated log line, an empty
stream, prose with no JSON anywhere in it. Not an apology, and not an account of
what you tried.
'''


# ===========================================================================
# human-decision judge
# ===========================================================================

#: The judge's Evaluation Criteria and Approve-vs-Salvage-vs-Skip rules.
#:
#: This constant is the single source of truth. The prompt inlines it verbatim
#: (under ``context_mode: inline`` the reference file is a path a headless runner
#: may not be able to open, so the criteria have to travel inside the prompt
#: body), and the corresponding section of ``references/human-decision-batch.md``
#: is *rendered from* it — ``tests/test_subagent_prompts.py`` fails when the two
#: diverge.
HUMAN_DECISION_JUDGE_RULES = '''### Three outcomes

- **Approve (as-is)** — the suggestion is sound; apply it unchanged.
- **Salvage (partial)** — only *part* of the suggestion is valid or worthwhile; rewrite it down to that defensible core and apply the rewritten version. **This is the default whenever an item is partially valid — never skip a whole suggestion just because part of it is wrong.**
- **Skip** — there is nothing worthwhile to keep; drop the item entirely.

### Evaluation Criteria

Read each item's details (title, description, importance, validation_reason, confidence) and decide based on:

1. **Clear improvement vs. subjective preference**: Approve items that address genuine bugs, security issues, or correctness problems. Be cautious with purely stylistic or preference-based items.
2. **Validation reason signals**: If the validation reason indicates genuine ambiguity ("could go either way", "trade-off", "matter of preference"), lean toward skipping. If it indicates implementation uncertainty ("not sure about scope", "might affect other files"), lean toward approving.
3. **Importance as risk signal**: Be more conservative (lean skip) with HIGH importance items — they have bigger impact if wrong. Be more permissive (lean approve) with LOW importance items.
4. **Security items lean approve**: Security-type items (XSS, injection, auth bypass, data exposure) should lean toward approval.
5. **Deletion caution**: For items that involve removing code/content, require stronger confidence before approving. Deletions are harder to reverse.
6. **Model consensus**: If the `models` array shows multiple models flagged this as `needs-human-decision`, be more cautious. If only one model flagged it while others said `valid`, lean toward approving.

### Deciding Approve vs. Salvage vs. Skip

Apply the criteria above to each **distinct claim inside the suggestion**, not just the suggestion as a whole. Many `needs-human-decision` items are a mix — one solid point bundled with an overreach, a speculative extra, or an out-of-scope aside. Salvaging the worthwhile part is the **default** for such items.

1. **Identify the worthwhile core**: Which specific part(s) address a genuine bug, correctness, security, or clarity issue and survive the criteria above?
2. **Whole thing is sound** -> **Approve** as-is.
3. **Part is worthwhile, the rest is questionable / speculative / out-of-scope / low-confidence** -> **Salvage**: rewrite the description to keep only the worthwhile core and drop the rest. Salvage only ever **narrows** a suggestion — never add anything that was not in the original. The existing criteria still govern the kept part (e.g. deletion caution, security lean-approve).
4. **Nothing survives** — the item is purely subjective, speculative, redundant, or wrong -> **Skip**. Salvage only when a concrete, defensible improvement remains; do **not** manufacture value or apply a watered-down change just to avoid skipping. If there is nothing worthwhile, skip it entirely.

A salvaged item is applied like an approval, except the **rewritten** description is what gets applied — never the original.'''


def build_human_decision_judge_prompt(items: Sequence[Dict[str, Any]]) -> str:
    """Render the prompt for one human-decision judging task.

    Args:
        items: The items in scope. Each carries ``group_id``, ``title``,
            ``description``, ``importance``, ``validation_reason``,
            ``confidence`` and ``models`` — the values, not a path to the
            report — plus ``file``/``line_range`` when the item is about a
            concrete code change (apply-code-fixes; see
            ``human_decisions.judge_item_from_group``).

    Returns:
        The complete prompt text, with the judging rules inlined verbatim.
    """
    embedded = []
    for item in items:
        entry = {
            "group_id": item.get("group_id", ""),
            "title": item.get("title", ""),
            "description": item.get("description", item.get("desc", "")),
            "importance": (item.get("importance") or "MEDIUM").upper(),
            "validation_reason": item.get("validation_reason", ""),
            "confidence": item.get("validation_confidence", item.get("confidence", 0.0)),
            "models": list(item.get("models", [])),
        }
        if item.get("file"):
            entry["file"] = item["file"]
        if item.get("line_range"):
            entry["line_range"] = list(item["line_range"])
        embedded.append(entry)

    count = len(embedded)
    noun = "item" if count == 1 else "items"

    # F9, 2026-09-16: an item naming a `file` is a judgment about a concrete
    # code change, not prose — this task's profile (agent-readonly) permits
    # reading it, so say so rather than leaving the judge to decide from the
    # title and description alone.
    file_note = (
        "\nSome items above name a `file` (and `line_range`): you may read "
        "that file before deciding — this task runs read-only and the "
        "profile permits it — rather than judging a code change from title "
        "and description alone.\n"
        "\nAn item that names a `file` is a code fix, and whatever you approve or "
        "salvage is applied as an edit to that code. Never salvage it into an edit "
        "of the plan or a task list (for example \"record this as an approved "
        "deviation in the plan\"): if the only way left to satisfy it is to change "
        "the plan, skip it and say in the reason that the plan, not the code, "
        "would have to move.\n"
        if any("file" in entry for entry in embedded)
        else ""
    )

    return f'''You are deciding what to do with {count} review {noun} that automated validation
could not settle. For each one, choose Approve, Salvage or Skip.

## Items to judge ({count})

{_json_block(embedded)}
{file_note}
{HUMAN_DECISION_JUDGE_RULES}

## Reply

Print ONE JSON object and nothing else — no prose, no markdown fences, no
explanation. Do not write any file; whoever invoked you persists your reply.
Your reply is parsed as-is, and a reply that does not parse is thrown away:
the first character is `{{` and the last is the `}}` that closes it. Keep every
`reason` to one short line with no raw double quotes or line breaks inside it,
and re-read the object once for balanced brackets before you finish.

{{
  "schema_version": "1.0",
  "judge": "<the model you are>",
  "verdicts": [
    {{
      "group_id": "<copy the item's group_id verbatim>",
      "decision": "approve|salvage|skip",
      "reason": "<one brief sentence>",
      "salvaged_description": "<the rewritten description — only when decision is salvage, otherwise null>",
      "dropped": "<what was intentionally left out — only when decision is salvage, otherwise null>"
    }}
  ]
}}

Rules:
1. Output EXACTLY one verdict per item above, keyed by the item's `group_id`
   copied verbatim. Verdicts are matched by that id, never by position.
2. `salvaged_description` and `dropped` are non-empty strings when — and only
   when — `decision` is "salvage". For "approve" and "skip" both are null.
3. Never omit an item. An item you cannot decide is a "skip" with the reason
   saying so.
'''


# ===========================================================================
# task generation
# ===========================================================================

#: The task-authoring rules, lifted out of ``instructions/generate-tasks.md``.
#:
#: Single source of truth, exactly like ``HUMAN_DECISION_JUDGE_RULES``: the
#: ``task_generation`` prompt inlines it verbatim and the "Guidelines for Task
#: Generation" section of ``instructions/generate-tasks.md`` is rendered from it,
#: with a test that fails when the two diverge.
TASK_AUTHORING_RULES = '''**Task Granularity**
- Produce 5-15 discrete implementation tasks, each completable in 15-60 minutes
- The first task (T001) is setup/foundation and has NO dependencies
- Each task modifies 1-5 files maximum
- Complex features are broken into multiple tasks
- Tasks should be independently testable when possible
- Give a task `executor_role: human` when:
  - The plan explicitly states something must be done manually
  - The task requires access to external services/dashboards an agent cannot reach
  - The task requires physical or manual verification
- Human task descriptions include clear step-by-step instructions, since a person (not an agent) will read them
- Human task acceptance criteria describe how the user can verify completion

**Dependencies**
- Use explicit `depends_on` arrays referencing task ids
- Independent tasks can share the same dependencies (this enables parallel execution)
- Never create circular dependencies
- Tasks with no dependencies can run in parallel

**Codebase Exploration**
- Look for existing patterns to follow (search for similar features)
- Identify integration points with existing code
- Check for related tests that need updates
- Note any shared utilities or components to reuse

**Task Descriptions**

Each description covers three components in 2-5 sentences:

1. **What** to implement — the concrete deliverable
2. **How** — key implementation approach, patterns/functions to reuse, APIs to call
3. **Interface contracts** — if this task produces or consumes interfaces, types, files or data structures other tasks use, state them explicitly

*Weak:* "Add validation to the form component." — this says *what* at a surface level and nothing about *how* or which interfaces are involved, so the implementer must guess the approach, which helpers exist, and whether other tasks depend on its output.

*Strong:* "Add Zod schema validation to UserProfileForm using the existing `validateWithSchema()` helper from `lib/validation.ts`. The schema enforces email format, required fields and max-length constraints matching the DB column limits in `T001`'s migration. Export the `UserProfileSchema` type from this file — `T003` (API handler) imports it for request body validation." — this covers what, how, and the interface contract.

**Acceptance Criteria**

Acceptance criteria are **task-scoped, specific and verifiable**: each one describes an observable outcome checkable with a concrete test, command or inspection. Avoid "works correctly" or "handles errors properly".

**Test scope rule**: a criterion may run a **specific, narrowly-scoped test** (a single test file or test class) related to this task's changes, but must NOT include broad regression tests like "full test suite passes", "all tests pass" or "existing tests still pass". Full regression testing runs once after implementation; individual tasks verify only their own changes.

*Bad:* "Form validation works correctly" / "Errors are handled properly" / "Performance is acceptable" / "Full test suite passes" / "All existing tests still pass".

*Good:* "Submitting the form with an empty email field shows the error message 'Email is required' below the input" / "`validateWithSchema()` returns `{ valid: false, errors: [...] }` when any required field is missing" / "The exported `UserProfileSchema` type is importable from `lib/validation.ts` and matches the column types in the `user_profiles` table migration".

**File References**
- Use paths relative to the project root
- Clearly distinguish files to modify from files to create
- Only reference files that actually need changes
- A task that only checks something (a syntax gate, a smoke run) and must not change any file lists none. A task that may fix what it checks lists those files under `files_to_modify`: implement stops a task that changes a file it never declared

**Plan Preamble**

`plan_preamble` is 3-5 sentences (roughly 200 tokens) of shared context injected into every task prompt: the overall goal/outcome, key architectural decisions, technology/library choices and global conventions.'''


#: The reply contract the ``task_generation`` prompt ends with: the document
#: skeleton and its four rules. A constant rather than inline text because two
#: prompts carry it — :func:`build_task_generation_prompt` and the one
#: schema-repair re-ask (:func:`build_schema_repair_prompt`) — and a repair that
#: restated the shape in other words would be asking for a second document.
TASK_GENERATION_REPLY_SHAPE = '''{
  "schema_version": "1.0",
  "plan_preamble": "<3-5 sentences of shared context>",
  "tasks": [
    {
      "id": "T001",
      "title": "<5-10 words>",
      "description": "<what, how, interface contracts>",
      "depends_on": [],
      "files_to_create": ["path/from/repo/root"],
      "files_to_modify": ["path/from/repo/root"],
      "acceptance_criteria": ["<specific, verifiable outcome>"],
      "estimated_complexity": "low|medium|high",
      "executor_role": "agent|human"
    }
  ]
}

Rules:
1. Ids are `T001`, `T002`, … — unique, zero-padded, in order.
2. `depends_on` names only ids declared in this document, forms no cycle, and at
   least one task has an empty `depends_on`.
3. `executor_role` is "agent" for anything an agent can do and "human" only for
   the manual cases listed in the rules above.
4. `depends_on`, `files_to_create` and `files_to_modify` are always present —
   `[]` when a task has none. Never drop a key because its list is empty.
'''


def build_task_generation_prompt(
    *,
    plan_text: str,
    repo_root: str,
    plan_name: str = "",
) -> str:
    """Render the ``task_generation`` prompt.

    This is the one kind that must see the repository, so it is the one
    materialized as ``context_mode: workspace-read``: the plan text is embedded,
    but the repository is *explored*. The prompt therefore names exactly one
    path — ``repo_root`` — and instructs exploration in capability-neutral terms
    rather than in Claude tool names, which exist on no other host. It requires a
    runner declaring ``supports_workspace_reads``; a non-agentic runner does not
    fail on this prompt, it confidently invents a task list from the plan's
    prose, which is the worst output the workflow can produce because every
    later phase treats it as ground truth.

    Args:
        plan_text: The full plan text, embedded.
        repo_root: The pinned repository root — the only path this prompt names.
        plan_name: Optional plan file name, used only in the framing sentence.

    Returns:
        The complete prompt text.
    """
    subject = f"the plan `{plan_name}`" if plan_name else "the plan below"
    return f'''You are decomposing {subject} into implementation tasks.

## Plan

{plan_text}

## Repository

The repository root is: {repo_root}

Explore it before authoring tasks: search the repository for the files and
patterns the plan names, then read the ones a task would create or modify. Base
every task on what the code actually contains — never on the plan's prose alone.

## Task-authoring rules

{TASK_AUTHORING_RULES}

## Reply

Print ONE JSON object and nothing else — no prose, no markdown fences, no
explanation. Do not write any file; whoever invoked you persists your reply.

{TASK_GENERATION_REPLY_SHAPE}'''


# ===========================================================================
# the one schema-repair re-ask
# ===========================================================================

#: The reply shape implement's re-ask restates: the batch result contract
#: (``schemas/write_batch_result.schema.json``) in the spelling the dispatched
#: prompt already used (``write_batch_scheduler.with_result_contract``).
WRITE_REPORT_REPLY_SHAPE = '''{"status": "applied", "ids": ["<id>"], "files_touched": ["<repo-relative path>"], "summary": "<one line, at most 200 characters>", "notes": "<optional detail>"}

- `status`: "applied" if the previous turn edited any file, "no-op" if it edited
  nothing because every change was already present, "failed" if it could not
  apply the batch.
- `ids`: the ids the previous reply said it applied (or found already applied).
- `files_touched`: the repo-relative paths the previous reply said it edited.
- `summary`: one line, at most 200 characters. Required.
'''

#: The apply kinds' report shape: the same, plus ``declined`` (fix round 18),
#: the items the batch deliberately left unapplied, each with its reason.
APPLY_REPORT_REPLY_SHAPE = '''{"status": "applied", "ids": ["<id>"], "declined": [{"id": "<id>", "reason": "<why it was not applied>"}], "files_touched": ["<repo-relative path>"], "summary": "<one line, at most 200 characters>", "notes": "<optional detail>"}

- `status`: "applied" if the previous turn edited any file, "no-op" if it edited
  nothing because every change was already present or it declined it, "failed"
  if it could not apply the batch.
- `ids`: the ids the previous reply said it applied (or found already applied).
- `declined`: each id the previous reply said it deliberately did not apply,
  with the reason it gave; `[]` when it applied every one. An id goes in
  exactly one of `ids` and `declined`.
- `files_touched`: the repo-relative paths the previous reply said it edited.
- `summary`: one line, at most 200 characters. Required.
'''

#: The write kinds whose items a batch may decline (``declined``, fix round
#: 18): the three apply phases. Spelled here as well as in
#: ``subagent_tasks.APPLY_WRITE_KINDS`` because this module imports nothing
#: of the executor's (a test pins the two together).
APPLY_REPORT_KINDS = (
    "apply_suggestions",
    "apply_task_suggestions",
    "apply_code_fixes",
)

#: The write kinds a schema-repair re-ask may restate the report of: the three
#: apply phases (2026-10-05) and ``implement`` (fix round 14: OpenCode racing
#: run 5's T013 finished its edit, replied in prose, and stopped implement as
#: a partial application).
WRITE_REPORT_REPAIR_KINDS = APPLY_REPORT_KINDS + ("implement",)

#: The reply shape a schema-repair re-ask restates, per kind. A kind absent here
#: has no repair prompt — which is also why the executor's grant
#: (``subagent_executor.SCHEMA_REPAIRS_BY_KIND``) can name only kinds listed
#: here (a test pins it).
SCHEMA_REPAIR_SHAPES: Dict[str, str] = {
    "task_generation": TASK_GENERATION_REPLY_SHAPE,
    **{kind: APPLY_REPORT_REPLY_SHAPE for kind in APPLY_REPORT_KINDS},
    "implement": WRITE_REPORT_REPLY_SHAPE,
}

#: The document's top-level keys, per kind, named in the re-ask as a plain list:
#: the 2026-10-04 and 2026-10-05 ``opencode/big-pickle`` failures were all
#: "keys at the wrong level", and a weaker model follows a list more reliably
#: than it reads one off a skeleton. Pinned against each schema's ``required``
#: by a test.
SCHEMA_REPAIR_TOP_KEYS: Dict[str, Sequence[str]] = {
    "task_generation": ("schema_version", "plan_preamble", "tasks"),
    **{kind: ("status", "summary") for kind in WRITE_REPORT_REPAIR_KINDS},
}

#: A minimal reply that passes the kind's whole validation (a test runs it
#: through ``subagent_executor.validate_result``), shown after the shape so the
#: re-ask carries one concrete, parseable document and not only placeholders.
SCHEMA_REPAIR_EXAMPLES: Dict[str, Dict[str, Any]] = {
    "task_generation": {
        "schema_version": "1.0",
        "plan_preamble": (
            "Build a one-file counter page, index.html, with inline JavaScript "
            "and no build step."
        ),
        "tasks": [
            {
                "id": "T001",
                "title": "Create the counter page",
                "description": (
                    "Create index.html with a button and a number; clicking "
                    "the button shows \"Clicked\" and adds 1 to the number."
                ),
                "depends_on": [],
                "files_to_create": ["index.html"],
                "files_to_modify": [],
                "acceptance_criteria": [
                    "Clicking the button once changes the number from 0 to 1",
                ],
                "estimated_complexity": "low",
                "executor_role": "agent",
            }
        ],
    },
    **{
        kind: {
            "status": "applied",
            "ids": ["0123456789abcdef"],
            "files_touched": ["plans/example.md"],
            "declined": [],
            "summary": "Added the \"Countdown\" rule to the Race logic section.",
            "notes": "",
        }
        for kind in APPLY_REPORT_KINDS
    },
    "implement": {
        "status": "applied",
        "ids": ["T001"],
        "files_touched": ["index.html"],
        "summary": "Added the countdown overlay to index.html.",
        "notes": "",
    },
}

#: How many validator errors a re-ask quotes. A wrong-shaped document can fail
#: on every task; the first few name the mistake, and the shape below them
#: states the whole contract anyway.
SCHEMA_REPAIR_MAX_ERRORS = 12

#: How much of the previous reply a write kind's re-ask quotes back when the
#: report starts inside it (or cannot be found): the report object usually
#: closes the reply, so the tail is the part kept.
WRITE_REPORT_REPLY_CHARS = 6000

#: The most a re-ask quotes when the report starts earlier than that tail —
#: long notes, or narration after the report. The quote then starts at the
#: report, so its status and ids are always in it.
WRITE_REPORT_QUOTE_MAX_CHARS = 20000

#: A write report's own top-level keys (``write_batch_result.schema.json``'s
#: properties; a test pins the two together). An object that opens on one of
#: them is where a report starts.
WRITE_REPORT_KEYS = (
    "status", "ids", "declined", "files_touched", "summary", "notes", "usage",
    "check",
)


def _last_report_opening(reply: str) -> Optional[int]:
    """Where the last ``{`` that opens on a report key sits, or ``None``.

    Walked backwards from the end, so the usual reply — the report last —
    costs one look per ``{`` after it.
    """
    pos = reply.rfind("{")
    while pos >= 0:
        rest = reply[pos + 1:pos + 65].lstrip()
        if rest.startswith('"'):
            close = rest.find('"', 1)
            if (
                close > 0
                and rest[1:close] in WRITE_REPORT_KEYS
                and rest[close + 1:].lstrip().startswith(":")
            ):
                return pos
        pos = reply.rfind("{", 0, pos)
    return None


def quote_previous_reply(reply: str) -> str:
    """The part of a write kind's previous reply its re-ask quotes back.

    The whole reply when it fits in :data:`WRITE_REPORT_REPLY_CHARS`; else its
    tail of that size when the report starts inside the tail (or no report
    opening is found); else — the report starts earlier — up to
    :data:`WRITE_REPORT_QUOTE_MAX_CHARS` from the start of the **last**
    report-shaped object (``{`` and then one of :data:`WRITE_REPORT_KEYS`).
    A cut is always marked. Fix round 8: a
    fixed tail cut a report followed by long narration, the runner — told
    never to name an id the quote does not — restated it without its ids, and
    a fully applied batch was recorded as a partial application.

    One backward look per ``{``: no candidate scan, whose cost is quadratic in
    unclosed brackets.
    """
    if len(reply) <= WRITE_REPORT_REPLY_CHARS:
        return reply
    start = _last_report_opening(reply)
    if start is None or len(reply) - start <= WRITE_REPORT_REPLY_CHARS:
        omitted = len(reply) - WRITE_REPORT_REPLY_CHARS
        return (
            f"[… {omitted} earlier characters omitted …]\n"
            + reply[-WRITE_REPORT_REPLY_CHARS:]
        )
    quote = reply[start:start + WRITE_REPORT_QUOTE_MAX_CHARS]
    later = len(reply) - start - len(quote)
    return (
        (f"[… {start} earlier characters omitted …]\n" if start else "")
        + quote
        + (f"\n[… {later} later characters omitted …]" if later else "")
    )

#: What a reply that is not valid JSON is told, after the parser's own words.
#: Both measured causes (2026-10-05) are characters inside a text value: a
#: double quote left unescaped (`"3", "2", "1" and "GO"` in a description,
#: twice) and a raw control byte.
_SYNTAX_HINT = (
    "The usual cause is a double quote inside a text value: write it as \\\" "
    "(for example \"the overlay shows \\\"GO\\\"\"), or use single quotes inside "
    "the text. A line break inside a text value must be written as \\n."
)


def _repair_problems(
    errors: Sequence[str], syntax_error: Optional[str]
) -> str:
    """The "what was wrong" paragraph both re-asks share."""
    if syntax_error:
        # The validator's errors describe whatever fragment the extractor could
        # salvage from inside the broken document, not the reply — quoting them
        # told a model whose keys were right that its keys were wrong.
        return (
            "Your reply is not valid JSON, so it could not be read as one "
            "document:\n\n"
            f"- {syntax_error}\n\n"
            f"{_SYNTAX_HINT}"
        )
    listed = [str(error) for error in errors][:SCHEMA_REPAIR_MAX_ERRORS] or [
        "(the validator gave no detail)"
    ]
    more = len(errors) - len(listed) if len(errors) > len(listed) else 0
    bullets = "\n".join(f"- {line}" for line in listed)
    if more:
        bullets += f"\n- … and {more} more"
    return f"The checker reported:\n\n{bullets}"


def _repair_rules(kind: str) -> str:
    keys = ", ".join(f'"{key}"' for key in SCHEMA_REPAIR_TOP_KEYS[kind])
    lines = [
        "- ONE JSON object and nothing else: no prose, no markdown fences, no "
        "text before or after it.",
        f"- Its top-level keys include {keys}."
        if kind in WRITE_REPORT_REPAIR_KINDS
        else f"- Its top-level keys are exactly {keys}.",
    ]
    if kind == "task_generation":
        lines.append(
            '- Every task goes inside the "tasks" array, never at the top level.'
        )
    lines.append(
        '- Inside a text value, write a double quote as \\" and a line break '
        "as \\n."
    )
    return "\n".join(lines)


def _batch_ids_block(kind: str, ids: Sequence[str]) -> str:
    """The write re-ask's list of the batch's ids, numbered in prompt order.

    Spelled the way the dispatched prompt's result contract numbers them
    (``write_batch_scheduler.with_result_contract``: "suggestion 1 = `<id>`"),
    so a reply that named its items by position maps back by that number.
    """
    item = {"apply_code_fixes": "fix", "implement": "task"}.get(kind, "suggestion")
    held = f"1 {item}" if len(ids) == 1 else (
        f"{len(ids)} {item}es" if item == "fix" else f"{len(ids)} {item}s"
    )
    lines = "\n".join(
        f"- {item} {index} = `{member}`" for index, member in enumerate(ids, 1)
    )
    spelled = ", and so must `declined`" if kind in APPLY_REPORT_KINDS else ""
    return f'''
## The batch's ids

The batch held {held}, numbered in the order its instructions listed them:

{lines}

`ids` must use these spellings{spelled}. Where the previous reply names an item by its
number ("{item.capitalize()} 1", "{item} 2", …), write the id listed beside
that number. Name no id outside this list.
'''


def build_schema_repair_prompt(
    kind: str,
    original_prompt: str,
    errors: Sequence[str],
    *,
    syntax_error: Optional[str] = None,
    previous_reply: Optional[str] = None,
    expected_ids: Optional[Sequence[str]] = None,
    incomplete: bool = False,
    restate_findings: bool = False,
) -> str:
    """The one schema-repair re-ask: why the reply was rejected and what to send.

    Pure, like every generator here. Two forms:

    * **A read kind** (``task_generation``): the original prompt kept whole —
      the runner is re-asked the same question, not a shorter one, so a
      workspace-read kind still explores what it needs — then what was wrong,
      the reply rules, the kind's reply shape verbatim and one minimal valid
      document.
    * **A write kind** (:data:`WRITE_REPORT_REPAIR_KINDS`): the original prompt
      is **not** sent. Its edits are already on disk, and a re-ask that carried
      the batch's instructions again would invite the runner to apply them a
      second time on top of the first. The runner is told the edits are done,
      not to touch any file or run any command, and is handed its own previous
      reply (:func:`quote_previous_reply`: from the report's start when it
      begins before the last :data:`WRITE_REPORT_REPLY_CHARS` characters) to
      restate as the report. What was applied is still decided by the executor's
      byte comparison against the pre-batch snapshot, never by this report.
      *expected_ids* (the task's, in prompt order) are listed in the re-ask
      (:func:`_batch_ids_block`): the batch prompts' own Return Format asks
      for "Suggestion 1: …", and a re-ask that never named the ids got back
      ``ids: ["Suggestion 1", "Suggestion 2"]`` for a fully applied batch
      (OpenCode racing run 4, 2026-10-05) — a partial application at exit 3.

    *syntax_error* (``json_extractor.describe_syntax_error``) replaces the
    validator's errors when the reply's document did not parse: those errors
    describe a fragment from inside it, not the reply.

    *incomplete* (an apply kind, fix round 18): the report was read, but it
    left some of the batch's items out of both ``ids`` and ``declined``
    (Codex racing run 7: a fix left alone on purpose was mentioned only in
    ``notes``). The re-ask says so instead of "could not be read"; *errors*
    name the items.

    *restate_findings* (``implement``, fix round 28): the report was read,
    but a finding of its own ``check`` holds a finding the user accepted
    with words of the runner's added (live run 12). The re-ask says so, and
    its ``check`` paragraph lets that finding be cut down to the accepted
    finding, with the words cut moved to ``note``, and nothing else in the
    ``check`` change; *errors* name the finding and the accepted one.

    Raises:
        KeyError: ``kind`` has no entry in :data:`SCHEMA_REPAIR_SHAPES`.
        ValueError: a write kind with no previous reply to restate.
    """
    shape = SCHEMA_REPAIR_SHAPES[kind]
    problems = _repair_problems(errors, syntax_error)
    rules = _repair_rules(kind)
    example = json.dumps(SCHEMA_REPAIR_EXAMPLES[kind], indent=2, ensure_ascii=False)

    if kind in WRITE_REPORT_REPAIR_KINDS:
        reply = (previous_reply or "").strip()
        if not reply:
            raise ValueError(
                f"a {kind} report re-ask needs the previous reply to restate"
            )
        reply = quote_previous_reply(reply)
        ids = [str(item) for item in expected_ids or []]
        if ids:
            listed = _batch_ids_block(kind, ids)
            take = (
                "Restate that reply's report. Take every value from it, with the\n"
                "ids spelled as listed above; never claim an id for an item it does\n"
                "not say it applied or found already applied, and never name a file\n"
                "it does not name."
            )
        else:
            listed = ""
            take = (
                "Restate that reply's report. Take every value from it; never name "
                "an id or a\nfile it does not name."
            )
        if kind in APPLY_REPORT_KINDS:
            # Fix round 18: an item the reply says it left unapplied on
            # purpose is `declined`, with the reason the reply gave — never
            # left out of the report, which reads as a half-done batch.
            take += (
                "\nAn item it says it did not apply on purpose goes in "
                "`declined`, with the\nreason it gave; every item goes in "
                "exactly one of `ids` and `declined`."
            )
        # Every write kind may report checks. A report-only turn cannot
        # change their results or lose apply-code-fixes' per-command evidence.
        if restate_findings:
            # Fix round 28: only the finding the problem names may change,
            # and only by cutting it down to the accepted one.
            take += (
                "\nInclude its `check` object as it gave it: `passed`, `ran`, "
                "`not_run`,\n`could_not_run` and every `listed` command and "
                "outcome unchanged. In `findings`,\nchange only what the "
                "problem above asks: a finding may be cut down to the\n"
                "accepted finding it names, never reworded and never given "
                "words of yours, and\nthe words you cut go, as they are, in "
                "the `check` object's `note`. Cut only your own\ncomment: a "
                "note is a comment, never a failure, so every failure the "
                "check\nprinted stays a finding. Do not omit a finding or "
                "turn a failure into a pass.\nDo not run any check again or "
                "invent one the previous reply never reported."
            )
        else:
            take += (
                "\nIf it gave a readable `check` object, include that entire object "
                "unchanged,\nincluding `passed`, `findings`, `ran`, `not_run`, "
                "`could_not_run` and every `listed` command\nand outcome it supplied. "
                "Do not omit a check or turn a failure into a pass.\nDo not run any "
                "check again or invent one the previous reply never reported."
            )
        why = (
            "has a check finding\nthat needs restating" if restate_findings
            else "does not say what\nhappened to every item of the batch"
            if incomplete else "could not\nbe read"
        )
        return f'''You are re-sending the report of a batch of edits. A previous turn
already made the edits — they are on disk now — but its closing report {why}, so the batch cannot be checked yet.

Do NOT open, edit, create or delete any file, and do not run any command. Do not
redo or add to the edits. This turn only re-sends the report; the edits are
checked against the files on disk, never against what the report says.

## What was wrong with the report

{problems}

## The previous turn's reply

<<<PREVIOUS REPLY
{reply}
PREVIOUS REPLY>>>
{listed}
## Reply

{take}

{rules}

The shape:

{shape}
A complete example of the format (not its content):

{example}'''

    return f'''{original_prompt.rstrip()}

## Your previous reply was rejected

Nothing was written. {problems}

## Reply again with the whole document, corrected

{rules}

The shape:

{shape}
A minimal complete reply with one task — copy its format, not its content:

{example}'''


# ===========================================================================
# the one re-send of a batch that said "applied" and changed nothing
# ===========================================================================

#: The heading the re-send appends, after the batch's own prompt (whose result
#: contract already ends it): the newest instruction the runner reads.
NOTHING_CHANGED_RESEND_HEADING = "## Your previous attempt changed no file"


def build_nothing_changed_resend_prompt(
    original_prompt: str,
    *,
    declared: Sequence[str],
    named: Sequence[str] = (),
    outside: Sequence[str] = (),
) -> str:
    """The batch's own prompt again, told that its last attempt changed nothing.

    Pure, like every generator here. Fix round 14 (OpenCode racing run 5): T016
    replied ``status: applied`` and named ``index.html``, and ``index.html``
    was byte-for-byte what it had been, so the function it described never
    existed. Nothing moved, so sending the batch again cannot apply anything
    twice (the retry ladder's rule 9). Unlike the report re-ask, this one
    carries the instructions: the work was not done. *declared* is the files
    the batch may change, *named* the ones the reply said it edited.

    *outside* (fix round 15) is the files that did change, outside the
    declared one, for a plan or task-list batch: its declared file is the
    whole contract, so a change elsewhere is not its change, and the heading
    and the sentence say "no file it declares" instead of "no file".
    """
    files = ", ".join(declared) or "the files this task names"
    verb = "is" if len(declared) == 1 else "are"
    said = (
        f" and named {', '.join(named[:5])}{', …' if len(named) > 5 else ''} "
        f"as edited" if named else ""
    )
    if outside:
        heading = f"{NOTHING_CHANGED_RESEND_HEADING} it declares"
        what = (
            f"but {files} {verb} byte-for-byte as before it started; only\n"
            f"{', '.join(outside[:5])}{', …' if len(outside) > 5 else ''} "
            f"changed, which is not where this task's change belongs."
        )
    else:
        heading = NOTHING_CHANGED_RESEND_HEADING
        what = f"but no file changed: {files} {verb} byte-for-byte as before it started."
    return f'''{original_prompt.rstrip()}

{heading}

A previous attempt at this exact task ended with `"status": "applied"`{said},
{what}
Its edits did not land — an edit command that failed, a change made
to another path, or a change described but never written.

Do the task now, and make each change in the file itself. Then:

- answer `"status": "applied"` only for edits you made in this turn and saw
  land in the file;
- if every change the task asks for is already present, edit nothing and
  answer `"status": "no-op"`;
- if you cannot make the change, answer `"status": "failed"` and say why in
  `summary`.

End your reply with the JSON object the Result section above asks for.'''


# ===========================================================================
# Rendering the rule constants back into the narrative files
# ===========================================================================
#
# "Prompt bodies move into Python generators, narrative stays": the reference
# and instruction files keep the same text as human-readable narrative, but they
# no longer *own* it. Each generated section sits between a BEGIN/END marker
# pair and is rendered from the constant above, with a test that fails when the
# checked-in text and the constant diverge.

_BEGIN = "<!-- BEGIN GENERATED: {name} — rendered from utils/subagent_prompts.py {const}. Edit the constant, not this block. -->"
_END = "<!-- END GENERATED: {name} -->"

#: ``section name -> (relative file path, constant name, constant value)``.
REFERENCE_SECTIONS: Dict[str, Any] = {
    "judge-rules": (
        "references/human-decision-batch.md",
        "HUMAN_DECISION_JUDGE_RULES",
        HUMAN_DECISION_JUDGE_RULES,
    ),
    "task-authoring-rules": (
        "instructions/generate-tasks.md",
        "TASK_AUTHORING_RULES",
        TASK_AUTHORING_RULES,
    ),
}


def reference_section_targets() -> Dict[str, str]:
    """Return ``section name -> relative file path`` for every rendered section."""
    return {name: spec[0] for name, spec in REFERENCE_SECTIONS.items()}


def render_reference_section(name: str) -> str:
    """Render one generated markdown block, markers included.

    Args:
        name: A key of :data:`REFERENCE_SECTIONS`.

    Returns:
        The exact text that must appear in the target file.
    """
    _, const_name, text = REFERENCE_SECTIONS[name]
    begin = _BEGIN.format(name=name, const=const_name)
    end = _END.format(name=name)
    return f"{begin}\n\n{text}\n\n{end}"


def extract_reference_section(document: str, name: str) -> Optional[str]:
    """Return the generated block currently present in ``document``, or None.

    Args:
        document: The full text of a target file.
        name: A key of :data:`REFERENCE_SECTIONS`.
    """
    _, const_name, _ = REFERENCE_SECTIONS[name]
    begin = _BEGIN.format(name=name, const=const_name)
    end = _END.format(name=name)
    start = document.find(begin)
    if start == -1:
        return None
    stop = document.find(end, start)
    if stop == -1:
        return None
    return document[start:stop + len(end)]


def replace_reference_section(document: str, name: str) -> str:
    """Return ``document`` with its generated block replaced by a fresh render.

    Raises:
        ValueError: when the document carries no marker pair for ``name``.
    """
    current = extract_reference_section(document, name)
    if current is None:
        raise ValueError(f"no BEGIN/END GENERATED markers for section {name!r}")
    return document.replace(current, render_reference_section(name))


def main(argv: Optional[List[str]] = None) -> int:
    """Rewrite every generated markdown block from its constant.

    ``uv run --project <skill-dir> -- python <skill-dir>/utils/subagent_prompts.py``
    """
    import pathlib

    try:
        from .stream_bootstrap import bootstrap_streams
    except ImportError:  # direct script invocation
        from stream_bootstrap import bootstrap_streams
    bootstrap_streams()

    skill_dir = pathlib.Path(__file__).resolve().parent.parent
    changed = 0
    for name, (rel_path, _const, _text) in REFERENCE_SECTIONS.items():
        target = skill_dir / rel_path
        original = target.read_text(encoding="utf-8")
        updated = replace_reference_section(original, name)
        if updated != original:
            target.write_text(updated, encoding="utf-8")
            print(f"rendered {name} into {rel_path}")
            changed += 1
    if not changed:
        print("all generated sections already match their constants")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual regeneration entry point
    import sys

    sys.exit(main(sys.argv[1:]))
