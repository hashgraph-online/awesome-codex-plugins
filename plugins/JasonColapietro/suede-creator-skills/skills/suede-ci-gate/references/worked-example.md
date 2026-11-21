# Suede CI Gate: Worked Example

One repository taken from a green-looking pipeline that gates nothing to a merge that genuinely cannot land broken. Illustration only: the rules live in SKILL.md.

## Worked Example

Fictional repo `acme-notes`: a single Next.js 14 app at the repo root, npm, no CI yet. This is what Step 0 through Output actually produce.

**Step 0: Detect (inventory)**

- **Apps:** one: repo root has `package.json` with `"next": "14.2.3"`. No monorepo, no `apps/*` split.
- **Package manager:** `package-lock.json` present. No `pnpm-lock.yaml` or `yarn.lock` alongside it: clean.
- **Existing CI:** `.github/workflows/` does not exist. Nothing to extend or duplicate.
- **Runtime version:** `package.json` has `"engines": { "node": ">=20.9.0" }`. No `.nvmrc`. Pin CI to `20.9.0`.
- **Deploy platform:** `vercel.json` present with the standing `ignoreCommand` that kills preview builds (`[ "$VERCEL_ENV" != "production" ] && exit 0 || exit 1`). Previews never build on Vercel: CI is the only pre-merge build signal. Build job is mandatory, not optional.
- **Real scripts:** `package.json` scripts are `build`, `lint` (`next lint`), and `test` (`vitest run`). No `test:run` alias, no separate typecheck script: `tsc --noEmit` is not wired up as its own script, so it's added as a CI step directly.

**Deliverable 1: workflow file** (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      app: ${{ steps.filter.outputs.app }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            app:
              - '**'
              - '!**.md'
              - '.github/workflows/ci.yml'

  app:
    needs: changes
    if: needs.changes.outputs.app == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20.9.0'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npx tsc --noEmit
      - run: npm run test
      - run: npm run build

  ci-success:
    if: always()
    needs: [app]
    runs-on: ubuntu-latest
    steps:
      - name: Gate on all jobs
        run: |
          for r in ${{ join(needs.*.result, ' ') }}; do
            [ "$r" = "success" ] || [ "$r" = "skipped" ] || { echo "blocked by: $r"; exit 1; }
          done
```

One app, so path-filtering exists mainly as the escape hatch (doc-only edits skip the `app` job; workflow-file edits always run it). `ci-success` is still required, not `app` directly: a single-app repo can still deadlock if `app` ever gains its own `paths:` filter later, so the aggregator habit holds even here.

**Deliverable 2: branch-protection settings**

Apply to `main`:

- Require status checks to pass before merging → **`ci-success`** only (not `app`, not `changes`).
- Require branches to be up to date before merging → on.
- Require a pull request before merging → on, 1 approving review.
- Block force pushes → on.
- Block branch deletion → on.
- Include administrators → on (repo has one maintainer today; still worth holding the same rule for future contributors).

```bash
gh api repos/acme/acme-notes/branches/main/protection \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -f 'required_status_checks[strict]=true' \
  -f 'required_status_checks[contexts][]=ci-success' \
  -f 'enforce_admins=true' \
  -f 'required_pull_request_reviews[required_approving_review_count]=1' \
  -F 'restrictions=null' \
  -f 'allow_force_pushes=false' \
  -f 'allow_deletions=false'
```

**Deliverable 3: short report**

> **Repo:** `acme-notes` (single Next.js app, npm, Vercel).
> **Package manager:** npm, one lockfile, `npm ci` matches.
> **CI added:** `.github/workflows/ci.yml`, one path-filtered `app` job (lint, typecheck, test, build) behind a `ci-success` aggregator.
> **Required check:** `ci-success` only.
> **Node pinned:** 20.9.0, from `package.json` `engines` (no `.nvmrc` found).
> **Fix first:** nothing blocking, no dual lockfiles, no existing workflow to reconcile, no runtime mismatch.
> **Note:** Vercel previews are disabled by `ignoreCommand`, so this CI build is the only pre-merge proof the app compiles. Do not treat "Vercel deployed" as a build signal for PRs.
>
> **Simple explanation:** Before any change joins the main project, a robot installs it, checks the code style, checks the types, runs the tests, and builds it. If any step fails, the merge button locks. Nothing reaches the live site without passing through the robot first.
