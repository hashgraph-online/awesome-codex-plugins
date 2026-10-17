---
name: ship
description: "Release-gate sequence: validate → review → push → tag. Wraps kernel:git mechanics with the pre-ship safety chain. Triggers: ship, release, push to main, ready to merge, deploy."
allowed-tools: Read, Bash, Task, Edit
kernel:
  kind: operator
  version: 1
  side_effects: writes_remote
  confirmation: on_side_effect
---

<skill id="ship">

## Sequence

1. **Preflight**
   - `git status --porcelain` — clean? If not: ask user to commit, stash, or abandon.
   - `git branch --show-current` — matches intent? Wrong branch → stop.
   - `git log --oneline {main}..HEAD` — commit range matches what you think you're shipping?
   - (gate: any mismatch → AskUserQuestion before continuing)

2. **Validate**
   - Invoke `/kernel:validate` (spawns validator agent, full 9-gate safety chain).
   - If unavailable: run project's nearest configured command (see reference/ship-research.md for equivalents).
   - (gate: any FAIL → stop; report which gate; do NOT push)
   - For plugins that support multiple loaders, validate each loader's schema
     independently and exercise one installed payload per loader. A shared file
     parsing successfully is not proof that its armed behavior is equivalent.
   - Run install, supported upgrade, and documented recovery commands in a
     disposable plugin/cache copy from outside the source checkout. Assert user
     data and user-owned files are unchanged.
   - Put an explicit resource ceiling around heavyweight suites when available;
     a release gate must fail loudly instead of exhausting the host machine.

3. **Review**
   - Tier 1 (1–2 file changes, low risk): self-review via Big 5 from skills/quality/SKILL.md.
   - Tier 2+: invoke `/kernel:review` (spawns reviewer agent, >80% confidence threshold).
   - (gate: REQUEST CHANGES → stop; address feedback; restart from step 2)
   - (gate: COMMENT → AskUserQuestion: "Address now, ship anyway, or hold?")
   - (gate: APPROVE → continue)

4. **Push**
   - Feature branch (`feat/*`, `fix/*`, `chore/*`, etc.): `git push` (or `git push -u origin {branch}` if upstream not set).
   - `main` / `master`: **STOP. AskUserQuestion required.** (NEXUS I0.8)
   - Detached HEAD or unexpected state: stop; investigate.
   - (gate: push rejected / non-fast-forward → surface to user; do NOT force-push)

5. **Version + Tag** *(on a release)*
   - Semver: patch=fix, minor=feature or behavior-preserving refactor, major=breaking. Confirm the number with the user.
   - Bump ALL canonical declarations in one shot: `scripts/bump-version.sh X.Y.Z`
     updates `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
     `governance/kernel.md.tmpl`, regenerates `AGENTS.md` and `CLAUDE.md`, and
     updates `skills/help/SKILL.md`. NEVER hand-edit one location — drift fails
     `test_version_sync_all`.
   - Human-author the release prose the script does NOT touch: the plugin/marketplace `description` highlight + a `CHANGELOG.md` entry (`## [X.Y.Z] - DATE` + Added/Changed/Fixed).
   - (gate: `bash tests/run-tests.sh` green — `test_version_sync_all` confirms no stale version anywhere.)
   - If a native manifest validator rejects required safety metadata, do not
     weaken the safety metadata or hand-author an unvalidated manifest. Keep the
     proven compatibility loader, record the limitation, and defer the native
     manifest until both schemas can be satisfied.
   - Tag (only if user requested a tagged release): `git tag -l` to avoid clobber → `git tag -a v{X.Y.Z} -m "{summary}"` → `git push origin v{X.Y.Z}`.
   - Before upgrading the installed plugin on this machine: `pgrep -fl codex`. The upgrade
     deletes the old cache directory under a live session's feet and every hook in that
     session exits 127 until it restarts. Name the live sessions in the handoff and say
     they need a restart; never report "upgraded" as if it covered them
     (docs/upgrading.md, 2026-08-27).
   - After publishing the GitHub release, install it into Claude's own cache and verify a
     fresh headless Claude process: `scripts/install-release.sh X.Y.Z`. The script updates
     only Claude's marketplace/cache, atomically advances Claude's `current` selector, and
     fails unless both the installed manifest and the fresh process report `X.Y.Z`. Codex
     installation remains a separate operation.

6. **Human pass** *(any user-facing release: app build, deploy, anything a person will touch)*
   - Load `skills/human-pass/SKILL.md` and write the guide for THIS build: literal
     controls, paste-ready inputs, expected outcome per step, worst case first,
     bundled to one sitting with the time cost stated.
   - Hand it over and wait. The build is not shipped, it is awaiting verdict.
   - (gate: no guide, or no recorded verdict → the release is NOT done. Say
     "awaiting your pass on <build>", never "shipped". A green pipeline is not a
     person having used the thing.)
   - Findings come back as prose; YOU convert them into issues, not the human.
   - Record the verdict as a state-change receipt on the release issue, naming
     what it unlocks (next build, submission, deploy promotion).

7. **Checkpoint**
   - `agentdb learn pattern "ship: {branch} {commit_range} {sha_pushed}" "validate=pass review=pass push=ok"`
   - Profile-gated: github-oss/github-production → post PR or release note via gh CLI.

## The verdict is part of done

For anything a person will use, the completion states are ordered: validated,
merged, deployed, **accepted**. CI proves the first three. Only a human who used
the build proves the fourth, and only that one predicts whether the release was
any good: a 15-minute guided pass found five defects that 500+ green tests had
not, because some properties only exist on the far side of a real screen with
real data. Report the state you actually reached, by name.

## Ask-user gates (mandatory pause points)

| Point | Condition | Question |
|---|---|---|
| Preflight | Branch or commit range is ambiguous | "Shipping {N} commits on {branch}. Confirm?" |
| Review | COMMENT verdict | "Review returned {N} comments. Address now, ship anyway, or hold?" |
| Push | Target is main/master | "About to push to main. NEXUS I0.8 requires explicit say-so. Confirm?" |

## Failure modes

1. `validate FAIL` → block; report which gate; do not loop silently
2. `review REQUEST_CHANGES` → block; address comments; restart from step 2
3. `push rejected (non-fast-forward)` → ask user; never auto-rebase or force-push
4. `tag conflict` → check `git tag -l` first; suggest next version; never overwrite existing tag

## Anti-patterns

- `ship_without_validate` — every step depends on the previous; skipping validate skips type/test/security
- `silent_skip_review` — review FAIL with no surfacing to user = trust violation
- `auto_push_to_main` — NEXUS I0.8; main requires explicit user confirmation
- `force_push_on_rejection` — rejection means remote has work you don't; investigate before overwriting
- `tag_without_release_intent` — tags are durable; casual pushes get no tag
- `skip_checkpoint` — shipped-but-unrecorded work breaks retrospective and learning loops

<on_complete>
agentdb write-end '{"skill":"ship","branch":"X","commits":N,"validate":"pass","review":"approve|comment|skip","pushed":true,"tagged":"X.Y.Z|none"}'
</on_complete>

</skill>
