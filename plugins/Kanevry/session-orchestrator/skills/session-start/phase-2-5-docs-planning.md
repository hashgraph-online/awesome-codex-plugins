# Phase 2.5: Docs Planning (Docs-Orchestrator Integration)

> Skip this phase if `docs-orchestrator.enabled` config is not `true` (default: `false`).

> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). The Dev audience target listed below resolves to whichever file the repo uses.

## Step 1: Read Docs-Orchestrator Config

Read the three controlling fields from `$CONFIG` using the canonical `jq` accessor pattern:

```bash
DOCS_ENABLED=$(echo "$CONFIG" | jq -r '."docs-orchestrator".enabled // false')
DOCS_AUDIENCES=$(echo "$CONFIG" | jq -r '."docs-orchestrator".audiences // ["user","dev","vault"] | join(",")')
DOCS_MODE=$(echo "$CONFIG" | jq -r '."docs-orchestrator".mode // "warn"')
```

Valid values for `mode`: `warn` | `strict` | `off`. Never use `hard`.

If `DOCS_ENABLED` is not `true`, skip all remaining steps in this phase and proceed directly to Phase 3.

## Step 2: Audience Auto-Detection

Using signals already gathered in Phases 2–5 (git analysis, VCS issues, branch state, SSOT checks), apply the following heuristic to determine which audiences are likely affected. Record each match with its triggering signal for inclusion in the output block.

**User audience** — flag as likely when any of the following are true:
- Affected files include `README.md`, `docs/user/**/*.md`, `docs/getting-started.md`, or `examples/**/*.md`
- Open or recently closed issues reference CLI UX changes, new user-facing commands, or a breaking API change
- New public commands are introduced (e.g. changes to `commands/` directory)
- Install flow or setup instructions are modified

**Dev audience** — flag as likely when any of the following are true:
- Affected files include `CLAUDE.md` (or `AGENTS.md` on Codex CLI), `docs/dev/**/*.md`, or `docs/adr/**/*.md`
- Issues describe an architecture decision, major refactor, new module or subsystem, test-coverage shift, dependency upgrade, or an ADR-worthy choice
- New `.mjs` scripts, skill files (`skills/**`), hook files (`hooks/**`), or agent definitions (`agents/**`) are added or substantially changed

**Vault audience** — flag as likely when ALL of the following are true:
- `vault-integration.enabled: true` is present in `$CONFIG`
- Issues involve project-status change, ownership transition, stack/infra decision, cross-project dependency, migration, or archival event

After detection, intersect the detected set with the audiences listed in `DOCS_AUDIENCES` (the user may have narrowed the allowed set in config). If the intersection is empty, proceed to Step 3 without pre-selecting any option as "Recommended" and add a note that no audiences were auto-detected.

See `skills/docs-orchestrator/audience-mapping.md` for the authoritative audience → file-pattern and trigger table.

## Step 3: Confirm Audiences with User

Present the audience confirmation using the platform-appropriate interaction pattern.

**Claude Code (AskUserQuestion):**

Mark the auto-detected primary audience (or audiences, if multiple) with `(Recommended)`. `multiSelect: true` because a single change commonly touches more than one audience.

```js
AskUserQuestion({
  questions: [{
    question: "Welche Audiences berührt dieser Scope? (Mehrfachauswahl möglich)",
    header: "Audiences",
    multiSelect: true,
    options: [
      {
        label: "Dev (Recommended)",   // add "(Recommended)" to each detected audience
        description: "Architektur-, Modul-, Refactoring-Änderungen. Dann ändern sich CLAUDE.md bzw. AGENTS.md und `docs/dev/**, docs/adr/**` (Handbuch und Entscheidungen)."
      },
      {
        label: "User",
        description: "Öffentlich sichtbare Änderungen. Dann werden README.md und `docs/user/**, examples/**` (was Nutzer davon lesen) nachgezogen."
      },
      {
        label: "Vault",
        description: "Strategische oder Status-Änderungen. Dann wird `<vault>/01-projects/<slug>/context.md, decisions.md, people.md` (die Projektakte dazu) nachgezogen."
      }
    ]
  }]
})
```

**Codex CLI / Cursor IDE fallback (numbered Markdown list):**

```markdown
Auto-detected: [dev]  ← list detected audiences here, or "none" if empty intersection

Welche Audiences berührt dieser Scope? Mehrfachauswahl möglich.

1. **Dev (Recommended)** — Architektur-, Modul-, Refactoring-Änderungen. Dann ändern sich CLAUDE.md bzw. AGENTS.md und `docs/dev/**, docs/adr/**` (Handbuch und Entscheidungen).
2. **User** — öffentlich sichtbare Änderungen. Dann werden README.md und `docs/user/**, examples/**` (was Nutzer davon lesen) nachgezogen.
3. **Vault** — strategische oder Status-Änderungen. Dann wird `<vault>/01-projects/<slug>/context.md, decisions.md, people.md` (die Projektakte dazu) nachgezogen.

Enter one or more numbers (comma-separated), or press Enter to accept the recommended default.
```

Store the confirmed audience list as `CONFIRMED_AUDIENCES`.

## Step 4: Emit Docs Planning Result Block

After the user confirms (or defaults are accepted), emit the following delimited block verbatim into the conversation context. This block is the **contract between Phase 2.5 and session-plan Step 1.8** — session-plan MUST parse it to classify tasks as `Docs` role and route them to the `docs-writer` agent.

```markdown
### Docs Planning Result (Phase 2.5)
Audiences: [<comma-separated confirmed audiences, e.g. dev, user>]
Detected-from: [<comma-separated detection signals, e.g. affected-files, issue-labels>]
Mode: <warn|strict|off>
Docs-tasks-seed:
  - audience: "dev"
    rationale: "<one-line reason derived from detection signal, e.g. 'new skill scaffolded in skills/docs-orchestrator'>"
  - audience: "user"
    rationale: "<one-line reason, or omit entry if audience not confirmed>"
```

Session-plan Step 1.8 identifies this block by the exact heading `### Docs Planning Result (Phase 2.5)` and reads `Audiences:` and `Docs-tasks-seed:` to seed the Docs role task list. **Parse rule for `Docs-tasks-seed:`:** each top-level `- audience:` bullet is exactly one seed task; parse all entries in document order; the following indented `rationale:` key binds to the most recent `- audience:`. If this block is absent (phase was skipped), session-plan MUST NOT create any Docs role tasks.

## Step 5: Non-Overlap Discipline

`docs-orchestrator` MUST NOT write to the following paths — they are owned by sibling skills:

- `<vault>/01-projects/*/_overview.md` — owned by `vault-mirror` (regenerated from JSONL on every session-end)
- `<vault>/03-daily/*` — owned by `daily` (idempotent day-level notes; a second writer would corrupt the file)

See `skills/docs-orchestrator/audience-mapping.md` (Non-Overlap with Sibling Skills table) for the complete ownership list and source-citation rules.

Proceed to Phase 3.
