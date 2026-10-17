# Preference Journal

This is an optional persistence format for teams that want the skill to behave
more like a reusable open-source workflow.

## Files

```text
.writers-loop/
|-- journal.jsonl
|-- prefs.md
`-- styles/
    `-- my-style.md
```

`journal.jsonl` is append-only and durable. `prefs.md` is derived and can be
regenerated. `styles/` contains reviewed style packs only when the user opts
into durable local style storage.

Do not create or update these files unless the user or project has opted into
durable preference storage. Journals may contain sensitive draft text, business
context, or private preferences. For shareable repositories, store summaries and
evidence IDs instead of full private passages when possible.

## Event Shape

```json
{
  "id": "evt-short-id",
  "createdAt": "2026-04-25T14:32:11Z",
  "artifact": "coding-plan",
  "stage": "planning",
  "type": "plan_approved",
  "signal": "positive",
  "appliesTo": "coding-plan/planning",
  "summary": "User approved plan with explicit test gates.",
  "payload": {
    "location": "testStrategy section",
    "changeSize": "sentence | paragraph | section | scene | whole artifact",
    "preference": "short summary of the learned rule, if any"
  }
}
```

## Event Types

Use these portable event names:

- `question_answered`
- `question_skipped`
- `plan_approved`
- `plan_revision_requested`
- `draft_accepted`
- `proposal_applied`
- `proposal_rejected`
- `proposal_adjusted`
- `proposal_undone`
- `manual_rewrite`
- `preference_declared`

## Storage Modes

- `session-only`: keep decisions in the current conversation; do not write files.
- `project-local`: write `.writers-loop/` into the current project.
- `portable`: write redacted summaries suitable for sharing in an open-source repo.
- `style-local`: write reviewed style packs to `.writers-loop/styles/`.

Default to `session-only` unless the user asks for persistence.
Choosing `session-only` for one task is a storage constraint, not a learned
preference. Do not emit a `Learned Preferences` rule from it unless the user
explicitly says to use that storage mode in future work.

Style packs are not preferences. Store them as reviewed style guidance in
`.writers-loop/styles/`; promote style behavior into `prefs.md` only after user
decisions support it.

For any storage-mode request, output:

```text
Storage Decision
- Mode: session-only | project-local | portable | style-local
- Durable files: none | .writers-loop/journal.jsonl | .writers-loop/prefs.md | .writers-loop/styles/[name].md
- File action: I will not create or update `.writers-loop/`, `journal.jsonl`, `prefs.md`, or style packs unless durable storage is explicitly approved
- Project-local storage: yes/no
- Portable/redacted storage: yes/no; redact private passages before sharing
- Privacy note: journals and style packs may reveal sensitive draft text, business context, or private preferences
- Learning status: no reusable preference learned unless reviewed decisions were collected
```

## Journal Tool

Use `scripts/journal.mjs` from the skill directory:

```bash
node scripts/journal.mjs init /path/to/project
node scripts/journal.mjs append /path/to/project '{"type":"plan_approved","signal":"positive","artifact":"coding-plan","stage":"planning","appliesTo":"coding-plan/planning","summary":"User approved exact test gates.","payload":{"preference":"Use exact verification commands in implementation plans"}}'
node scripts/journal.mjs derive /path/to/project
```

The derived `prefs.md` includes only medium and high confidence preferences.
Single events stay in the journal unless they are explicit `preference_declared`
events.
`question_answered`, `question_skipped`, and `draft_accepted` events are retained
as session evidence but are not promoted by the derivation tool.
Use `appliesTo` for the artifact/stage scope. `journal.mjs` also accepts legacy
`scope` fields when reading older journals.

## Derived Preferences

```markdown
# Learned Preferences

## Coding Plan / Planning
### Prefer
- Use exact file paths and verification commands. [confidence: high, evidence: 3]

### Avoid
- Avoid vague "add tests" steps without test names. [confidence: medium, evidence: 2]

## Report / Drafting
### Prefer
- Lead with the recommendation before background. [confidence: high, evidence: 2]
```

## Promotion Rules

Promote to `prefs.md` when:

- The user explicitly declares the rule as a standing preference.
- At least two strong decisions support the same pattern.
- The rule is specific, scoped, and not contradicted by newer evidence.

Keep as low-confidence evidence when:

- Only one decision supports it.
- The scope is unclear.
- It conflicts with a current task requirement.

## Conflict Rules

- Explicit user instruction beats inferred preference.
- Recent repeated evidence beats old evidence.
- Artifact-specific rules beat global rules.
- Strong rejected or undone edits can create `Avoid` rules.
