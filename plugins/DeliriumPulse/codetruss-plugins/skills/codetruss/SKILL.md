---
name: codetruss
description: Operate CodeTruss local acceptance gates for coding-agent changes. Use when a developer asks to bind an agent task to allowed or denied files, configure repository verification, install or diagnose Claude Code or Codex hooks, review a working-tree or staged diff before commit, interpret or verify a signed CodeTruss receipt, repair a failed verdict, or explicitly opt into provider-backed review or receipt sync.
---

# CodeTruss

Use the installed `codetruss` CLI as the source of truth. Do not reimplement
scope classification, analyzers, verdict rules, signing, or hook behavior in the
agent.

## Preserve the trust boundary

- Work inside the developer's Git repository and inspect existing policy before
  proposing changes.
- Run `codetruss --version` first. This skill targets v0.2.24 or newer. If the
  CLI is missing or older, explain the prerequisite, then
  obtain explicit consent before downloading or installing software, including an upgrade.
- Offer only the official install paths from `https://codetruss.com/cli`. Let
  the developer inspect a downloaded installer instead of piping it when they
  prefer an inspect-first flow.
- Do not run `--llm`, `codetruss auth login`, or `codetruss sync` unless the
  developer explicitly requests that networked action. Never search for or
  print provider keys.
- Do not broaden `allow`, remove `deny`, add `--no-verify`, or edit a receipt to
  manufacture a green verdict. Fix the change or ask the developer to approve a
  genuine policy change.
- For `codetruss run` and `codetruss review`, treat exit `0` as `PASS`, exit `1`
  as `REVIEW_REQUIRED`, exit `2` as `FAILED`, and exit `3` as a usage or
  environment failure. Exits 1 and 2 still produce receipts; other commands
  may use nonzero exits differently, so read their output.
- Describe a valid signature as post-generation integrity evidence. Do not call
  it trusted execution, proof of authorship, or automatic compliance evidence.

## Set up a repository

1. Confirm the repository root and require a reasonably clean baseline when
   attribution matters.
2. Inspect tracked paths, task context, existing `.codetruss.yml`, package
   scripts, and the repository's normal lint, typecheck, test, or build commands.
3. Propose the smallest useful `allow` globs, appropriate `deny` globs, the
   exact verification commands CodeTruss is expected to detect, and one hook
   target. Keep secrets, generated output, production infrastructure, and
   unrelated migrations denied when appropriate. Show which tracked paths each
   glob matches, and flag empty or overly broad matches. Do not default to `**/*`.
4. Ask the developer to confirm the exact boundary, hook target, verification
   command list, and whether to trust that list for automatic execution.
5. After confirmation, use `codetruss setup` as the single guided setup path,
   with the approved repeated `--allow` and `--deny` values and one
   `--hooks claude|codex|pre-commit|all` value. Prefer its interactive trust
   prompt so the commands it actually prints can be compared with the approved
   list before answering `trust`. Use `--yes` only after every choice is
   explicit and the inspected repository state is unchanged. Include
   `--trust-verify` only after the developer approves the exact detected list,
   so fingerprint trust is completed. Do not replace guided initial setup with
   ad hoc config editing or separate hook installation.
6. Read the setup output and verify the expected policy, hook health, and
   local-only privacy reminder. When commands were detected, require their
   full verification fingerprint and trusted result, then run
   `codetruss verify-policy status` and require exit 0 with the same fingerprint
   and command list. Otherwise confirm that setup reports no detected commands.
   If setup pauses before trust, show the exact commands and fingerprint, obtain
   approval, then rerun the same setup path with `--trust-verify`.
7. Remind Codex users to open `/hooks` and approve the exact repository hook
   definition when setup reports that one-time host trust step.

The CLI's hook installer is idempotent and preserves supported existing hook
configuration. An existing `.codetruss.yml` remains authoritative: if setup
reports a policy mismatch, stop instead of overwriting or weakening it, and
treat any policy change as a separate developer decision. If the developer
approves the exact policy diff, make only that reviewed edit and rerun setup
without conflicting policy flags. A setup hook target installs or checks that
target; it does not remove other existing hooks. Never uninstall another hook
without an explicit removal request. Do not replace the installer with
plugin-bundled hook logic.

## Review changes

1. Use the developer's actual task statement. Ask for it if the intended change
   is unclear; do not invent a permissive task after seeing the diff.
2. Use `codetruss review --task "..."` for current tracked and untracked changes.
   Add `--staged` only when the developer requests the index or a pre-commit
   review.
3. Use repository policy by default. Pass task-specific `--allow`, `--deny`, or
   `--verify` values only when the developer explicitly sets or approves them.
4. Read the receipt ID and explicit reasons. Use
   `codetruss report latest --json` when structured evidence is useful, then run
   `codetruss verify latest` before describing the receipt as valid.
5. Report the verdict, scope exceptions, sensitive surfaces, analyzer findings,
   verification results, evidence limitations, and receipt path. Distinguish a
   policy dispute from a product or shell failure.

For a wrapped agent run, preserve the exact task and policy:

```bash
codetruss run --task "<task>" --allow "<glob>" --verify "<command>" -- <agent-command>
```

Do not stage, commit, reset, clean, or sync as a side effect of review.

## Repair and recheck

- Repair the finding at its source while keeping the approved policy stable.
- Re-run the same review mode and verification commands after the change.
- If the developer intentionally changed a sensitive or denied surface, record
  that decision explicitly; do not silently reclassify it.
- Use `codetruss hooks status <surface>` and
  `codetruss hooks doctor <surface>` for diagnosis. Use
  `codetruss hooks uninstall <surface>` only on an explicit removal request.

Keep the final response compact: verdict first, then actionable reasons, receipt
ID/path, integrity result, and any decision still required from the developer.
