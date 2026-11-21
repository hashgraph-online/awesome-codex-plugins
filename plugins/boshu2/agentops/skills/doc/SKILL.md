---
name: doc
description: "Write source-checked docs, READMEs, change descriptions and handoffs. Use when: documenting a change, leaving or resuming a handoff, or drafting a questionnaire for someone else."
practices:
- wiki-knowledge-surface
- code-complete
- pragmatic-programmer
hexagonal_role: supporting
consumes:
- repo-context
produces:
- documentation
- session-handoff
context_rel: []
skill_api_version: 1
user-invocable: true
metadata:
  capabilities: [doc, initialize_missing_docs, write_session_handoff]
  effects: [write_documentation, write_requested_handoff, create_requested_evidence_directory]
  canonical_status: canonical
  disposition: keep_specialist
  tier: product
  dependencies: []
output_contract: requested documentation or handoff with source references, check results and explicit gaps
---
# Doc

Write or update the documentation the caller needs, grounded in the current
repository and its accepted intent. A small explanation needs no interview,
coverage ledger or separate report. Select only the mode relevant to the task.

## Modes

| Need | Scope and reference |
|---|---|
| Explain an API, command, code-map or architecture | Inspect its consumers, source and tests, and write to the existing document owner. A coverage percentage needs a numerator and denominator from one enumerated, checked entity set ([validation techniques](references/validation-rules.md)). How the code works is [Research](../research/SKILL.md)'s repository tracing; Doc writes it down when a document is requested. |
| Create or improve a README | Lead with the user's problem and a working first-use path; preserve useful depth. See [README craft](references/readme-craft.md). |
| Check an advertised install, upgrade or first-success path | Follow the selected package and current instructions in an authorized disposable environment. See [developer journey](references/developer-journey.md). |
| Audit or scaffold OSS documentation | Compare existing docs with the requested pack. Create missing files; revise existing files only within the authorized request. See [OSS pack](references/oss-pack.md). |
| Initialize missing entry documents | Create only explicitly requested missing files; report existing paths as skipped. See [setup examples](references/bootstrap/examples.md). |
| Bring docs current after a change, describe a change for reviewers, or write release notes for a range | Start from the exact diff and its public surface; fix what it proves wrong and ask about judgment calls. See [change-driven docs](references/change-driven-docs.md). |
| Preserve a session for another context, or resume from one | Read [the handoff reference](references/handoff.md) before writing or resuming one. A handoff records only facts you observed: anything else is `unknown` or the caller's unverified claim, and a note saying HOLD or paused is not state. |
| Get facts or decisions only another person holds | Write one [questionnaire](references/questionnaire.md) they can answer alone; the caller sends it. |

These are optional task shapes, not successive phases. Detailed references
supply techniques and formats; they do not add interviews, approval checkpoints,
reports or files beyond the accepted request. Existing authorization to revise
specified documents is sufficient.

`<skill-dir>` is the directory that contains this SKILL.md. Claude Code shows it
as "Base directory for this skill"; Codex lists this skill's SKILL.md path; in
an AgentOps source checkout it is `skills/doc`. Replace `<skill-dir>` with that
absolute path before running a command. The working directory stays the user's
repository. If the host did not show where this skill is installed, use the
directory of the SKILL.md you read. If you cannot determine it, do not guess a
path or run a same-named script from the current repository; say the bundled
script is unavailable and compare the repository's documentation files with the
requested pack by hand.

## Grounded writing

1. Identify the audience, question and existing document owner. Reuse accepted
   intent; ask only for missing content that materially changes the document.
   Name the reader's need: learning from scratch, doing one task, looking up a
   fact, or understanding why. A reference list does not show how to do the
   task it exists for. For a reader who learns from it, explain each idea before
   a section relies on it ([ordering](references/prose-and-report-workmanship.md#order-ideas-for-a-learner)).
2. Read the relevant declarations and verify them against code, configuration,
   command help or executable behavior. Use the caller's domain terminology.
   Take steps in another vendor's interface (menus, settings, where a value
   appears) from its current docs or the caller, or mark them unverified; never guess.
   For a larger surface, retain enough source references to disclose what was
   inspected and what remains unknown; do not imply whole-repository coverage.
3. Make the smallest useful edit. Explain non-obvious rules, ordering and tradeoffs
   when they help the reader; a reference page need not manufacture a lesson.
   Preserve operator policy and history outside the authorized scope. Edit an
   existing document in its own shape, from a fresh read if a person may have
   changed it (their edits win): extend the passage that already says it, under
   any heading, rather than add a duplicate section, and do not reorder or
   restyle it into a template unless asked for a rewrite. When rewriting
   existing prose, keep every fact, number, name, citation and identifier,
   and keep each claim's certainty: "may" does not become "does".
   When condensing (a summary, handoff or release notes), keep every failure,
   caveat, open question and request, and sound no more finished, positive or
   certain than the source; say where it is vague or contradicts itself.
   Leave code blocks, quotes and link targets untouched unless they are the
   thing to fix.
4. Check links, cited commits and paths, leftover drafting scaffold, examples
   and the repository's documentation build or validator ([techniques](references/validation-rules.md)).
   Remove empty claims and redundant prose; [prose guidance](references/prose-and-report-workmanship.md)
   can help when the requested output is substantial.
   A link handed to a reader (in a document, report, handoff or change
   description) must open the exact item it names for that reader. Build
   repository URLs from Git rather than by hand, and point them at a ref that
   already contains the pushed content: a main-branch link to a file that exists
   only on a feature branch is dead. Link the item itself (the pull request, the
   file and line), not its parent page. When no direct link can be verified, say
   where to find the item instead of giving a guessed link.
5. Return changed paths and check results, plus unresolved factual gaps. Write a
   separate report only when the caller requests one or an existing consumer
   requires it.

## Missing-document setup

Create only the requested missing documents, such as `PRODUCT.md`, `GOALS.md`
or `AGENTS.md`; a collision is skipped, not overwritten by setup. Verify the
created paths and report created, skipped and failed writes. Setup does not
install tools, run `ao session bootstrap`, initialize Git or trackers, start a
runtime, add hooks, or infer a repository workflow. AgentOps verdict storage is
created only on explicit request; see [AgentOps internals](references/agentops-internal.md).

## Reference menu

Load these only for the document being written. They supply examples and
techniques under the kernel's accepted scope, not additional workflow gates.

- Writing and checks: [prose workmanship](references/prose-and-report-workmanship.md) (cleanup, learner order, diagrams, one live statement), [validation techniques](references/validation-rules.md).
- After a change: [change-driven docs](references/change-driven-docs.md) for doc drift, reader-need coverage and change descriptions.
- Explicit context configuration: [context routing](references/bootstrap/context-routing.md).
- AgentOps itself (vocabulary, evidence routing, handoff commands): [AgentOps internals](references/agentops-internal.md).
