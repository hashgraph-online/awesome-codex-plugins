---
name: omos-archive
description: "Archive completed OpenSpec changes through the vendored archive workflows, delegating to the bundled $openspec-archive-change skill ($openspec-bulk-archive-change for two or more ids). Invoke via $oh-my-openspec:omos-archive."
---

# omos-archive

Archive completed OpenSpec changes by delegating to the bundled vendored
archive skills — the Codex twin of OpenCode's archive command. Every
instruction line below is rendered from `archiveInstruction` in
`core/prompts.ts`, the same single source the OpenCode command prompts
with; the only transforms are the id-count branches pinned statically
and the skill names in the load lines rendered as `$`-mentions.

Arguments arrive as plain text in the user's message after the
`$oh-my-openspec:omos-archive` mention — there is no argument substitution. Split the
message on whitespace into change ids and follow the branch the id
count selects (the `archiveSkillId` mapping: zero or one id binds the
single-archive skill, two or more bind the bulk one):

- Zero ids —
  Load the `$openspec-archive-change` skill and follow it exactly.
  No change ids given — list active changes, confirm with the user which to archive.
- One id —
  Load the `$openspec-archive-change` skill and follow it exactly.
  Change: <change-id>
- Two or more ids —
  Load the `$openspec-bulk-archive-change` skill and follow it exactly.
  Changes: <id-1>, <id-2>

Follow each branch's steps in order:

Validate first with the openspec_validate tool; stop on INVALID unless the user explicitly overrides.
Use the delegated archive skill for its other checks. These plugin-mandated steps override any conflicting upstream sync or archive choices: do not ask whether to sync, and stop before archiving if required sync is blocked.
Before syncing or archiving, review document-level title headings in every selected change artifact and each main specification affected by its deltas, plus Requirement headings in those specifications. Correct TBD placeholders and technical machine-name titles only when a readable title is clearly supported by the artifact content; preserve readable authored main-spec titles. If a title is ambiguous, ask the user to choose and wait before continuing.
Keep MODIFIED requirement headings verbatim to the baseline merge key; express any requirement rename with exact FROM:/TO: entries under RENAMED Requirements. Do not inspect or edit historical archived changes or their specifications.
Sync the selected change's specification deltas into the main specs before archiving; do not ask whether to sync.
When sync creates a new openspec/specs/<capability>/spec.md, give it a readable top-level title derived from the capability's purpose or meaning. Preserve existing readable authored titles and machine-named capability paths.
If required specification sync is blocked, stop without archiving and report the blocker.
After archiving, validate the resulting specifications. Repair issues that are safely fixable within OpenSpec artifacts, then validate again.
If validation remains INVALID or an issue cannot be safely repaired within OpenSpec artifacts, show the exact findings and proactively offer the user help resolving them. Stop without claiming validation passed.
If safe repairs make validation return VALID, report successful validation and do not offer unresolved-finding recovery.
