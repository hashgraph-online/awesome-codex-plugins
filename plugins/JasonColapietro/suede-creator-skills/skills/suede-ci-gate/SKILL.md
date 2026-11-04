---
name: suede-ci-gate
description: "Suede AI CI Gate Skills. Use when asked to \"fix a required check stuck pending\" or set up branch protection and path-aware CI, runtime/lockfile pinning and one aggregator gate from the real repository. Returns workflows and settings. NOT FOR: reviewing implementation (suede-code), designing AI evals (suede-ai-eval), or release packaging (suede-launch-packaging)."
metadata:
  display-name: "Suede AI CI Gate Skills"
---

# Suede AI CI Gate Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Requires repository source and workflow access; Git and the project own runtimes for local checks. GitHub Actions/branch-protection read access supports verification; changing protection needs explicit authority.

## Gate policy: advisory, not blocking

Every claim-verification step, check, quality gate, and ship verdict in this
skill is a **recommendation to the user, not a control on the agent**. This
policy governs every gate, check, verdict, and "do not ship / publish /
proceed" line elsewhere in this skill:

- Run every check and report the results honestly. Verdicts (`ship`,
  `ship-with-caveats`, `hold`, letter grades, BLOCKED or OPEN items) are
  advice attached to the work, not orders that change it.
- Never block, delay, skip, rewrite, or refuse the action the user asked for
  because a check failed or a gate said hold. Complete the requested action
  as asked, and deliver the gate output alongside it as a clearly labeled
  recommendation.
- A failed gate changes what you report, never what you do.
- Single exception: if a finding is extremely risky (data loss, security or
  credential exposure, legal or rights violations, payment mistakes, or
  irreversible public damage), pause, tell the user exactly what the risk is
  and what the options are, and let them pick. Their choice is final.


Set up CI and branch protection that actually block a bad merge: in any repo, any stack. The output is a working pipeline plus the exact protection settings, not advice.

**Runs only when asked.** This skill never auto-fires on a commit, push, or other side effect of unrelated work: invoke it explicitly (set up CI, protect main, fix this hanging check).

Run this in whatever folder you point it at. **Detect first, never assume.** Nothing here is hardcoded to a specific project, monorepo layout, or package manager.

## Step 0: Detect (before writing anything)

From the repo root, inventory:

- **Apps:** every top-level dir with a manifest: `package.json`, `requirements.txt` / `pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile`. A repo may hold one app or many; build for what's actually there.
- **Package manager per app:** which lockfile is present: `package-lock.json` (npm), `pnpm-lock.yaml` (pnpm), `yarn.lock` (yarn), `bun.lock` or the older binary `bun.lockb` (bun). Two lockfiles in one app is a bug to fix first (Lane 3).
- **Existing CI:** read `.github/workflows/*`. Do **not** duplicate a job that already exists: extend or reconcile it.
- **Runtime versions:** `.nvmrc`, `package.json` `engines`, `.python-version`, `pytest.ini`/`pyproject`. Pin CI to these; never hardcode a guess.
- **Deploy platform:** `vercel.json` / `.vercel`, `netlify.toml`, a `Dockerfile`. If the platform skips non-prod builds (e.g. Vercel `ignoreCommand` kills previews), CI is the *only* pre-merge build signal: so a build job is mandatory.
- **Real scripts:** read each app's `scripts` / test config and use the real ones (`test`, `test:run`, `lint`, `build`). Don't invent commands.

Do not write a single workflow line until this inventory is complete.

## The gate (the part everyone gets wrong)

Path-filtered jobs **skip** when their paths aren't touched. A skipped job that is a *required* status check leaves the PR pending forever. So never require the path-filtered jobs directly. Instead add one **aggregator** that depends on all of them:

```yaml
  ci-success:
    if: always()
    needs: [<every app job>]
    runs-on: ubuntu-latest
    steps:
      - name: Gate on all jobs
        run: |
          for r in ${{ join(needs.*.result, ' ') }}; do
            [ "$r" = "success" ] || [ "$r" = "skipped" ] || { echo "blocked by: $r"; exit 1; }
          done
```

In branch protection, require **only `ci-success`**: never the individual jobs. This is the single thing that makes "protect main" work with change-based CI.

## Lanes

1. **Path-aware jobs**: one job per app, gated by a `changes` job (`dorny/paths-filter` or native `paths:`). Add an escape hatch so edits to the workflow file itself run everything.
2. **Aggregator gate**: as above. The only required check is `ci-success`.
3. **Lockfile hygiene**: exactly one lockfile per app, and the install command must match it (`npm ci`, `pnpm i --frozen-lockfile`, `yarn --immutable`, `bun install --frozen-lockfile`). Two lockfiles means CI can install a different tree than ships: resolve before wiring CI.
4. **Pin runtimes from the repo**: Node/Python/etc. read from `.nvmrc` / `engines` / `.python-version`, falling back to the platform default. Never a hardcoded guess that drifts from prod.
5. **Don't duplicate existing CI**: if a workflow already covers an app (e.g. a backend test workflow), extend it; never stack a second, weaker job on top.
6. **Least privilege**: `permissions: contents: read` unless a job genuinely needs more.
7. **Build is a gate when previews are off**: if the deploy platform skips non-prod builds, the CI build is your only pre-merge proof the app compiles. Keep it.
8. **Branch protection**: output the exact settings: require `ci-success`, require branches up to date before merge, optional required PR review, block force-push and deletion, optionally include administrators. GitHub offers two mechanisms: classic branch protection and repository rulesets (Settings → Rules → Rulesets), which can target many branches and stack. Match whichever the repo already uses; for a new setup on GitHub, prefer a ruleset with `ci-success` as the required status check.

## Instant-fail patterns (CI that looks green but isn't)

- A required check that is a path-filtered job → deadlocks every unrelated PR. Use the aggregator.
- `npm ci` with no committed lockfile, or a lockfile for a different manager → fails or installs the wrong tree.
- A second job duplicating an existing workflow → wasted minutes and conflicting signal.
- Hardcoded `node-version` / `python-version` that doesn't match the app → green in CI, broken in prod.
- A job whose `paths:` never match → always skipped → a "green" check that tested nothing.

## Red flags: stop

The excuses that precede a broken gate:

- "Just require each job directly": a skipped path-filtered job deadlocks every unrelated PR. The aggregator is the only required check.
- "CI is green": green because it ran, or green because everything skipped? Name what actually executed.
- "One big workflow that builds everything is simpler": it also builds the world on a README typo. Path-filter it.
- "We'll protect main after launch": the riskiest merges happen before launch.
- "The deploy platform builds it anyway": if previews are off, CI is the only pre-merge proof the app compiles.

## Output

1. The workflow file(s) under `.github/workflows/`.
2. The exact branch-protection settings to apply (and the `gh api` calls, if asked).
3. A short report: apps detected, package manager per app, what each job runs, what is required, and anything to fix first (dual lockfiles, duplicate workflows, runtime mismatches).
4. **Readback, once the settings have been applied** (the user applies them, this skill does not): verify rather than assume. `gh api repos/:owner/:repo/branches/main/protection --jq '.required_status_checks.contexts'` must return exactly `["ci-success"]` (any path-filtered job in that list is the deadlock above); for a ruleset, `gh api repos/:owner/:repo/rules/branches/main` must show a `required_status_checks` rule naming only `ci-success`; and `gh run list --branch <pr-branch>` must show `ci-success` actually ran, not skipped. If the settings are not applied yet or the token lacks admin scope, report the gate as **unverified**; never claim protection is live from the settings you emitted.

End with a **Simple explanation (plain, for a 10-year-old)**: one short paragraph, no jargon, saying what the gate now does and what it blocks: e.g. "Before anyone's changes join the main project, a robot builds and tests them. If the robot fails, the merge button locks."

## Worked Example

A full pass on one repository (from a pipeline that looks green but gates nothing
to a merge that cannot land broken) is in `references/worked-example.md`. Read it
when wiring a repo whose existing CI shape you do not recognize.

## Post-Deploy Verification

The after-deploy checks (live URL, critical-path smoke test, regression sweep, rollback readiness, and the verified/watch/rollback verdict) are in `references/post-deploy-verification.md`. Read it only when a production deploy has already landed; this skill's own job ends at the merge gate.

## Boundaries

Generate; don't enforce. This skill writes workflow files and tells you the protection settings: it does **not** push, flip branch protection, or change repo access on its own. Verify the detected stack before applying. Works in any repo: it detects rather than assumes Suede or any specific project.

## Routing

- The gate is failing on real defects → **suede-code** to review and grade the change (`--findings-only` when the caller wants no letter grade)
- The repo ships an MCP server → add a job that runs a full stdio session (`initialize`, `notifications/initialized`, then list and call) and wire it into the aggregator
- AI features need eval jobs in the pipeline → **suede-ai-eval** to design the cases, then wire them in here
- Rollout needs flags, staged lanes, or a rollback tree → **suede-agent-teams**
- Gate holds and the release goes public → **suede-launch-packaging**
