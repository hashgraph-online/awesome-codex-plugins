---
name: ci-pr-gate
description: Turn a dependency change — a before/after package.json/lockfile snapshot, or one or more named "bump X from A to B" upgrades — into one deterministic PASS/WARN/FAIL verdict formatted for a CI check or PR-comment bot, not a conversational report. Use when the user explicitly wants a mergeable/blocking verdict, a "CI gate," a PR status comment, or asks "should this PR be blocked," "is this safe to merge," "gate this dependency bump." Not for a plain explanation of what changed in a diff (dependency-audit's own snapshot-diff flow already covers that conversationally) and not for a single already-installed package's trust investigation (package-trust-check).
---

# NPMScan CI PR gate

Use this skill only when the user wants a **verdict**, not a report — the
output is meant to be pasted directly into a CI check or a PR comment by a
bot, so it has to resolve to exactly one of PASS / WARN / FAIL every time,
even on partial or ambiguous data. `dependency-audit`'s existing
"Comparing two snapshots" flow already produces a good conversational
explanation of a `diff_dependencies` result for a human reading it in
chat — don't duplicate that here. This skill's only job is applying a fixed,
documented policy on top of the same tool output to produce a scannable
verdict instead, and packaging it for a bot persona: no hedging, no
follow-up questions, no "as an AI" framing, no options to weigh — one
verdict, ranked blocking reasons, done.

If the user wants to investigate whether one already-installed package is
compromised (not a PR's dependency change), use `package-trust-check`. If
they want to know what to actually *do* about a finding, hand off to
`incident-response`.

## Determining input shape

1. **Two full snapshots** (any mix of `package.json`, `package-lock.json`,
   `yarn.lock`, `pnpm-lock.yaml`) pasted as a before/after pair — call
   `diff_dependencies({ before, after })` directly. When the PR changes BOTH
   `package.json` and its lockfile and both pairs were given, diff each pair
   (two calls): `package.json` carries `overridesChanges` and the project's
   own scripts, the lockfile carries the exact versions that will install —
   the override rule below needs both.
2. **One or more named bumps with no full snapshots** — the common
   Renovate/Dependabot PR-title shape ("Bump lodash from 3.10.1 to
   4.17.21," "upgrade minimist to 1.2.6") — call
   `simulate_dependency_upgrade` once. For a single bump use
   `{ packageName, currentVersion, targetVersion }`; for two or more, pass
   them all in one call as `{ packages: [{ packageName, currentVersion,
   targetVersion }, ...] }` (1-100 items) rather than one call per package.
   A batch response puts each package's result under `results[]` and adds
   a `batchSummary` — run every entry in `results[]` through the Gate
   policy below, not just the summary counts; an item with a non-null `fetchError` couldn't be
   resolved at all — list it in the table as unchecked (WARN), never as a
   PASS. If more than 100 bumps were named, run the first 100 and say
   explicitly which were skipped rather than silently dropping them.
3. **Both** (full snapshots plus one or more specific packages the user
   wants a deeper semver/breaking-change read on beyond what a diff
   computes) — run `diff_dependencies` first, then add one
   `simulate_dependency_upgrade` call (batched via `packages` when there's
   more than one) only for the specifically-named packages. Don't run both tools for the same package by default; that's
   redundant.
4. **Nothing parseable** — ask for the before/after content or the exact
   `name@current→target` bump(s). Don't guess a version that wasn't given.

## Steps

1. Route per the table above and make the tool call(s).
2. Collect every vulnerability finding worth ranking from the results:
   any entry with `vulnerabilityDelta` of `"introduced"` or
   `"still-vulnerable"` (from either tool), taking `id`/severity from its
   `vulnerabilities[]` array (diff) or `targetVulnerabilities[]` (simulate —
   per item under `results[]` for a batch call).
   Pass each finding's `id` through as `advisoryId` (the tool looks it up
   and auto-detects malware advisories) and set `findingType: "malware"` on
   every finding whose `isMalware` is true. Deduplicate identical
   `{packageName, cveId}` pairs, then call `prioritize_remediation({
   findings })` once with all of them — even for a single finding, since KEV
   status isn't visible from the raw severity string alone.
3. Apply the [Gate policy](#gate-policy) below to every package checked,
   deterministically. The overall verdict is the worst single-package
   verdict (FAIL beats WARN beats PASS) — one failing package fails the
   whole gate.
4. Produce the [Output contract](#output-contract) below. That is the
   entire response — no preamble, no "let me check that for you," no
   summary paragraph after it.

## Gate policy

Evaluate every rule for every package checked; the highest tier any rule
triggers is that package's verdict.

### FAIL — block the merge

- Any finding — introduced or pre-existing — with `isMalware: true`, or
  that `prioritize_remediation` ranks `tier: "remove-now"`, or that carries
  `findingType: "malware"`, or whose `advisoryId`/finding `id` matches
  `MAL-*`; and any `simulate_dependency_upgrade` result with
  `riskTier: "do-not-upgrade"` (the target is known malware, or npm no
  longer lists it while OSV still has advisories for it — how npm removes
  malicious releases). This is a confirmed
  malicious package, not a vulnerability to schedule — it outranks every
  other rule here, including KEV/EPSS, and applies regardless of whether
  the finding is `"introduced"` or pre-existing `"still-vulnerable"`: a
  malware package already present before this PR is exactly as disqualifying
  as one this PR adds. Check this first, before the severity-based rule
  below, since a malware advisory's own OSV `severity` field can be missing
  or non-CRITICAL even though `tier` correctly comes back `"remove-now"`.
- `installScriptIntroduced === true` on any changed/upgraded package
  (from either tool). This is the same highest-signal field
  `dependency-audit` and `diff_dependencies`'s own description call out —
  a routine-looking bump quietly adding a `postinstall` is the shape of a
  compromised-maintainer attack, and a gate should never let that through
  as a warning. It counts preinstall/install/postinstall only; a new
  `prepare` alone is a WARN (below), not a FAIL.
- `sourceIntegrityChanged === true` on any changed/upgraded package (diff
  only — see `resolvedUrl`/`integrity` on that entry for what changed). This
  means the resolved tarball URL or integrity hash changed while the
  version string stayed IDENTICAL — a same-version tarball swap (a
  compromised registry mirror, or a hand-edited/tampered lockfile) that a
  version-only read of the diff would report as "no change." Treat this at
  least as seriously as `installScriptIntroduced`.
- `identityMismatch === true` on any package (diff) — the lockfile's
  tarball is a different package or version than the entry declares
  (`tarballName`/`tarballVersion` say what really installs).
- `projectLifecycleChanges.introduced` contains `preinstall`, `install` or
  `postinstall` (diff only) — a lifecycle key newly added to the SCANNED
  PROJECT's own root `package.json`, not a dependency's (a newly added root
  `prepare` alone is a WARN below). This runs
  the moment anyone runs `npm install` on the project itself and is
  invisible to every per-package rule above, since it isn't a package being
  added/changed at all — treat a new root lifecycle script exactly like
  `installScriptIntroduced` on a dependency.
- Any `vulnerabilityDelta: "introduced"` finding whose `highestSeverity` /
  vulnerability severity is `CRITICAL` or `HIGH` — **regardless of what
  tier `prioritize_remediation` assigns it.** This was confirmed directly:
  simulating minimist's 1.2.6→1.2.5 downgrade (which reintroduces the real
  CRITICAL CVE-2021-44906) and ranking that finding through
  `prioritize_remediation` returns `tier: "monitor"`, `score: 11.37` —
  because EPSS's 30-day exploitation probability for that CVE is currently
  only 4.6% and it isn't KEV-listed. `prioritize_remediation`'s tier
  answers "what should I work through first across my whole backlog,"
  which is the right question for a fix-priority ranking but the wrong one
  for merge admission control — a PR that actively introduces a CRITICAL
  vulnerability shouldn't pass just because that CVE isn't trending right
  now. So: severity on an *introduced* finding is a hard block on its own;
  `prioritize_remediation`'s tier is what decides WARN-level ordering
  below it, not whether this rule fires at all.
- Any finding — introduced or pre-existing — that `prioritize_remediation`
  ranks `tier: "patch-now"` (CISA KEV-listed, confirmed active
  exploitation). This fires even at MEDIUM/LOW severity, same as that tool
  documents: active exploitation overrides severity.
- An override change that lets a bad version in, per the
  [override rule](#override-changes) below.

### WARN — pass, but flag for human review

- `vulnerabilityDelta: "still-vulnerable"` (pre-existing, not introduced by
  this change) at any severity — real, but not this PR's fault; don't
  block the PR for it, but don't hide it either.
- An introduced finding at MEDIUM/LOW severity, or any finding ranked
  `tier: "patch-soon"`, `"scheduled"`, or `"monitor"` that didn't already
  trigger a FAIL rule above.
- `riskTier: "breaking-change-likely"` or `isBreakingBySemver: true`
  (simulate only) — not a security issue, but a gate consumer needs to
  know a major/breaking bump is riding in.
- `targetDeprecated` set (simulate only — `diff_dependencies` doesn't
  surface a per-package deprecation flag; that's a known gap in this
  skill's coverage for the snapshot-diff path, not something to work
  around with an extra tool call here).
- `engineChange.tightened === true` (simulate only) — the target version
  now requires a newer Node than the current one supports.
- `targetIsPrerelease === true` (simulate only).
- A `prepare` newly present in `installScriptKeysIntroduced` (either tool)
  or `projectLifecycleChanges.introduced` (diff) with no other new lifecycle
  key — npm never runs a dependency's `prepare` on install, but a reviewer
  should still see it; a project's own new `prepare` runs on every local
  `npm install`.
- Any unresolved side: `resolutionNote` set (diff) or
  `currentVersionNote`/`targetVersionNote` or a batch item's `fetchError`
  set (simulate) — e.g. a
  git/workspace/file specifier, or a target range with no satisfying
  published version. Never treat unresolved as PASS; it means the gate
  couldn't actually check anything for that entry.
- `changeType === "downgrade"` (diff) or `direction === "downgrade"`
  (simulate) with no vulnerability reintroduced — still
  worth a reviewer's eyes; a PR that quietly lowers a dependency version
  for no stated reason is unusual enough to flag.
- `projectLifecycleChanges.changed` non-empty (diff only) — an EXISTING root
  lifecycle script's command was modified (not newly added — see the FAIL
  rule above for that case). Could be a legitimate build-tooling update, but
  the project's own install-time command changing is always worth a
  reviewer's eyes.
- Any `overridesChanges` entry the [override rule](#override-changes)
  doesn't escalate to FAIL.

### Override changes

`overridesChanges` (diff of `package.json`, any of introduced/removed/
changed) — `overrides`/`resolutions`/`pnpm.overrides` force a version onto
a transitive dependency, usually to pin past a known vulnerability, so a PR
that removes or changes one can let a vulnerable or malicious version back
in. Decide each entry with these fixed steps, in order, so the verdict
never depends on improvising:

1. Find the version that will now install for that package:
   - **introduced/changed override whose new value is an exact version** —
     that version.
   - **removed override, or a range as the new value** — the package's
     `afterVersion` in the lockfile diff (input shape 1, second call). If no
     lockfile diff is available, the version is unknown.
2. If the version is known, call `query_vulnerabilities({ name, version })`
   once for it (batch several with `batch_query_vulnerabilities`).
3. Verdict:
   - **FAIL** — the version has an `isMalware` finding or a CRITICAL/HIGH
     finding.
   - **WARN** — every other case: only MODERATE/LOW findings, clean, or
     unknown (no lockfile diff, `vulnerabilityCheckFailed`, an error, or a
     rate limit). A clean result is still a WARN — a safety pin was removed
     or changed, and a reviewer should see it.
4. Never PASS an override change, never retry a failed check (one attempt,
   then WARN), and always give the reason: which package, the before →
   after override value, the version that will install, and the finding
   ids — or, when unknown, why (e.g. `overrides.minimist removed; could not
   verify the version now installed (no lockfile diff) — include the
   lockfile to verify`).

### PASS

Every package checked triggered none of the above.

## Output contract

Lead with one machine-parseable line, then a short human-readable body.
Nothing goes above the verdict line.

```
GATE: <PASS|WARN|FAIL>

## Dependency gate — <✅ PASS|⚠️ PASS WITH WARNINGS|❌ FAIL>

Checked N package(s), M flagged.

### Blocking (only when FAIL)
- `pkg@version`: <one-line reason — name the exact CVE/GHSA id if there is
  one> ([npmscanUrl])

### Warnings (omit section if none)
- `pkg@version`: <one-line reason> ([npmscanUrl])

### All packages checked
| Package | Before → After | Verdict | Reason |
|---|---|---|---|
```

- The `GATE:` line's value must match the verdict implied by the rest of
  the response — never let the table show a FAIL-tier row while the top
  line says PASS.
- Every row's "Reason" cites the specific field that triggered it (exact
  CVE/GHSA id and severity, `"isMalware"`, `"do-not-upgrade"`,
  `"installScriptIntroduced"`, `"sourceIntegrityChanged"`,
  `"identityMismatch"`, `"overridesChanges"`, "major semver bump,"
  etc.) — never a bare "flagged," and never fold multiple reasons
  for the same package into a vague summary when the row has more than
  one; list them.
- Keep the table to the packages actually checked — don't restate
  `removed` entries from a `diff_dependencies` result; removing a
  dependency isn't a gate concern.
- A package the tool couldn't resolve still gets its own row with verdict
  WARN and the resolution note as the reason — never drop it from the
  table silently.
- `projectLifecycleChanges`/`overridesChanges` describe the PROJECT itself
  (its root `package.json`), not any one dependency package — they don't
  fit the per-package table naturally. Give each one its own row using
  `(project root)` as the "Package" value and the changed key/override name
  in "Before → After" (e.g. `postinstall: (none) → curl ... | sh`, or
  `overrides.lodash: 4.17.21 → (removed)`), same Verdict/Reason columns as
  every other row — never omit them just because they don't name a
  dependency.

## Do not

- Do not derive the verdict from raw severity strings alone once
  `prioritize_remediation` has run — its `tier` (not the bare severity) is
  what decides WARN-vs-FAIL ordering among findings that didn't already
  hit the severity-based FAIL rule above.
- Do not treat a `prioritize_remediation` tier below `patch-now` as
  license to pass an *introduced* CRITICAL/HIGH finding — see the FAIL
  rule above; that tool's tier is a fix-priority ranking across a whole
  backlog, not a merge-admission signal on its own.
- Do not block a PR for a `still-vulnerable` (pre-existing) finding the PR
  didn't introduce — WARN it, don't FAIL it. The one exception is
  `tier: "remove-now"`/`findingType: "malware"`: FAIL that regardless of
  whether it's introduced or pre-existing, per the Gate policy above — a
  malware package doesn't become acceptable just because this PR isn't the
  one that added it.
- Do not run both `diff_dependencies` and `simulate_dependency_upgrade` on
  the same package in the same request "just in case" — route per the
  input-shape table once.
- Do not call `simulate_dependency_upgrade` once per package when several
  bumps were named — batch them into one call's `packages` array.
- Do not silently cap a >100-package batch of named bumps without saying
  which ones were skipped.
- Do not add a conversational summary, caveats paragraph, or follow-up
  question after the output contract — the structured verdict is the
  entire deliverable. If something is genuinely too ambiguous to gate
  (falls under "nothing parseable" in the input-shape table), say so
  instead of producing a contract with a guessed verdict — don't emit a
  fabricated PASS/WARN/FAIL over data you don't have.
- Do not imply this skill actually posts the comment, sets a commit
  status, or blocks the merge itself — it only produces the text; whatever
  bot or workflow is consuming this response is responsible for the actual
  enforcement action.
- Do not silently drop an unresolved entry into the PASS bucket — every
  unresolved side is a WARN with the resolution note as its reason, per
  the Gate policy above. That includes a batch entry with `fetchError`.
- Do not look anything up beyond what the Gate policy names. An extra
  lookup outside the written rules is what made the same override fixture
  FAIL on one run and WARN on the next; the override rule is the only place
  a follow-up query is part of the policy.
- Do not FAIL a dependency bump whose only new lifecycle key is `prepare`.

## Tools used

`diff_dependencies`, `simulate_dependency_upgrade`, `prioritize_remediation`,
`query_vulnerabilities`/`batch_query_vulnerabilities` (override rule only)
— all provided by the `npmscan` MCP server bundled with this plugin
(`.mcp.json`). See [references/test-prompts.md](references/test-prompts.md)
for prompts to manually verify this skill after installing or editing it.
