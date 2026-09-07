---
date: 2026-05-28
topic: ship skill — background, rationale, tooling survey
---

# Ship Skill — Reference

## Purpose and mental model

Shipping is not committing. Committing is one step of shipping.
Ship = the full sequence: validate gates → review → push → optionally tag.
Each step has a fail-fast verdict; the chain stops on first failure.

## Skill relationships

- skills/build/reference/git.md — commit mechanics
- skills/quality/SKILL.md — Big 5 self-review checklist
- /kernel:validate — invokes validator agent (full 9-gate safety chain)
- /kernel:review — invokes reviewer agent (>80% confidence threshold)
- agents/pre-ship.md — composite release gate for tier 2+ work (spawns 4 parallel validators)

## Core principles (the "why" behind the sequence)

1. **Validate before review, review before push, push before tag.** The order is fail-fast.
2. **Push to `main` requires explicit user say-so.** Feature branch push is fine after gates pass.
3. **The release is the artifact, not the intent.** Verify by file/diff, not by what you meant to ship.
4. **Tag only when explicitly releasing.** Casual pushes don't get tags.
5. **Hook carve-outs apply to hooks only.** User and agent commits in this skill go through the full gate chain.

## Local gate equivalents (when /kernel:validate unavailable)

Use the project's nearest configured command first (`package.json` scripts, `Makefile`, `pyproject.toml`, `justfile`).

| Gate | Command |
|---|---|
| Tests | `npm test` / `pytest` / `cargo test` |
| Types | `tsc --noEmit` / `mypy` / `cargo check` |
| Lint | `eslint` / `ruff` / `cargo clippy` |
| Security | `npm audit` / `pip-audit` / project scanner |
| Diff sanity | `git diff --stat {main}..HEAD` — no unrelated changes, no leaked secrets |

## Tag format details

- Semver projects: read version from manifest (`package.json`, `Cargo.toml`, `pyproject.toml`), confirm next version with user.
- Command: `git tag -a v{X.Y.Z} -m "{release notes summary}"` then `git push origin v{X.Y.Z}`.
- Non-versioned projects: timestamp tag if requested, otherwise skip.
- Check before tagging: `git tag -l` to avoid overwriting existing tags.

## Profile-gated post-ship actions

- `github-oss` / `github-production`: post PR or release note via `gh` CLI / GitHub integration hooks.
- `local`: nothing further beyond agentdb checkpoint.

## Why the ask_user gates exist

Three mandatory pause points prevent autonomy overreach:
1. **Preflight ambiguity** — wrong branch or unexpected commit range is a pre-condition failure, not a recoverable error.
2. **Review COMMENT (not REQUEST CHANGES)** — comments are advisory; the human decides if they block.
3. **Push to main** — NEXUS I0.8 is non-negotiable; explicit confirmation is the external hook equivalent for this gate.
