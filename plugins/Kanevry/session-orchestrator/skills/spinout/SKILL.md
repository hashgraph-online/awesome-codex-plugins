---
name: spinout
user-invocable: true
model: sonnet
description: Use when extracting a project into its own repo — a venture spinout (e.g. a product leaving its incubator repo) or a sanitized content-snapshot fork. Guided 5-step runbook: target sphere + path, confidentiality/sanitize check, copy + fresh git init, SNAPSHOT-FREEZE marker in the source repo, remotes + registration. Trigger on 'spin out X', 'extract this into its own repo', 'fork X sanitized'.
---

# spinout — Guided Project-Extraction Runbook

## Status: Deliberately Not Scripted

This is a 5-phase interactive runbook, not a CLI wrapper. Automate only after 2-3 hand-runs have stabilized the pattern — spinout is a low-frequency, high-stakes operation (new remote, fresh history, a frozen marker left behind in the source repo), and premature scripting bakes wrong defaults (wrong sphere, wrong sanitize scope, wrong remote layout) into something expensive to undo. See #730 / H2.

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion before proceeding. If the gate is OPEN, continue to Phase 1.

## Phase 1: Target + Sphere (AUQ)

Ask via `AskUserQuestion` (per `.claude/rules/ask-via-tool.md` AUQ-001):
- **Destination path** — where the new repo will live on disk.
- **Sphere** — which account/host the new repo belongs to. Sphere conventions are **host-local**, not hardcoded here: read the operator's global `CLAUDE.md` (e.g. `~/.claude/CLAUDE.md`) for the "Verzeichnis = Account" mapping (private vs. org vs. ventures trees, or whatever the host documents) and offer those as options.
- **Extraction type** — `venture-spinout` (a product leaving its incubator repo, gets a live remote and its own backlog) or `sanitized-snapshot` (a frozen, sanitized fork of content/code with no independent forward development expected).

Do not proceed to Phase 2 without explicit confirmation of all three.

## Phase 2: Confidentiality / Sanitize Check (HARD-GATE)

<HARD-GATE>
No copy happens until this checklist is confirmed by the operator. Do not rationalize past it because "it's all internal anyway."
</HARD-GATE>

Checklist:
- **Secrets/tokens** — run gitleaks (or the repo's existing pre-commit scanner) over the target sub-path before copying.
- **Live-infra references** — hostnames, internal URLs, deploy targets that should not leak into a spun-out repo.
- **Internal-only docs** — anything under a private-only doc tree that should not travel.
- **PII** — names, emails, customer data in fixtures or sample content.

**Inertness declaration pattern:** infra-coupled scripts that will simply run empty in the new repo without their source tokens/infra (not broken, just inert there) get TABULATED in the FORK-NOTES (Phase 4) rather than silently deleted — deletion loses information a future maintainer needs; the table makes the inertness an explicit, reviewable fact.

## Phase 3: Copy + Fresh git init

- Directory copy of the target sub-path — deliberately **not** `git subtree split` or `git filter-repo`. No shared history travels with the spinout by design; the new repo starts clean.
- Exclude build/dependency artifacts the same way a worktree would (`node_modules`, `dist`, `.git`, lockfile-derived caches).
- `git init` fresh in the destination.
- Add a provenance header to the new repo's `README.md` / `CLAUDE.md` (or `AGENTS.md` on Codex CLI): source repo, source path, extraction date, extraction type.

## Phase 4: SNAPSHOT-FREEZE Marker in the Source Repo

Write a `FORK-NOTES.md` (or `SNAPSHOT.md`) at the **original location** in the source repo — the copy left behind, not the new repo. Contents:
- Provenance: source path, spinout date, "frozen — SSOT moved to `<new-repo>`".
- Remote map: where the new repo now lives (sphere + URL).
- Inertness table from Phase 2 (script → why it's inert here, not broken).

The corpus left behind at the original location is FROZEN from this point — cross-reference `.claude/rules/development.md` § Corpus Freeze Marker for the convention.

## Phase 5: Remotes + Registration (AUQ)

Confirm each write via `AskUserQuestion` before executing:
- Create the new repo's remote(s) per sphere (push-URL discipline — any helper remote used only for cross-host fetch should have push `DISABLED` where that pattern applies).
- Register the new repo in the vault/portfolio index if one exists.
- Optionally seed an initial issue backlog in the new repo.

## Anti-Patterns

- Scripting this runbook before the pattern has stabilized over 2-3 hand-runs.
- Skipping the Phase 2 sanitize gate "because it's internal anyway."
- Carrying shared git history into the spinout (`subtree`/`filter-repo`) — the new repo starts clean by design.
- Continuing to develop the source copy after Phase 4 instead of treating it as frozen.

## See Also

- `commands/spinout.md` — slash-command entry point.
- `skills/_shared/bootstrap-gate.md` — Phase 0 gate contract.
- `.claude/rules/ask-via-tool.md` — AUQ-001 (every user decision goes through the tool, not prose).
- `.claude/rules/parallel-sessions.md` § PSA-003 — destructive-action safeguards apply to any write in Phase 3/4/5.
