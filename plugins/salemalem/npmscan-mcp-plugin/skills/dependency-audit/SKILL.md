---
name: dependency-audit
description: Audit a project's npm dependencies for known vulnerabilities and risky install scripts before installing, upgrading, or shipping. Use when the user pastes or attaches a package.json/lockfile, lists dependencies, or asks to check/audit/scan their packages for security issues — including comparing two snapshots (a PR diff) or checking license compliance.
---

# NPMScan dependency audit

Use this skill when the user wants a security check across multiple npm
packages at once (a `package.json`, a lockfile, or a plain list of
`name@version` pairs) — not for a question about a single package. A plain
factual single-package question ("what does X do") you can answer directly
with `get_package` or `query_vulnerabilities`; a single-package
*trust* question ("is X safe," "was X compromised/hijacked") should use the
`package-trust-check` skill instead, which runs the deeper
maintainer-history and publish-provenance checks this skill deliberately
reserves for already-flagged packages only. A forward-looking question about
what to *add* rather than what's already installed ("should we add X," "X
vs Y vs Z for this job," "what should we use to do X") should use the
`new-dependency-evaluation` skill instead — it orchestrates
`compare_packages`/`suggest_alternative` for exactly that decision, which
this skill's per-inventory vulnerability/license flow isn't built for.

## Input

Accept dependency name+version pairs from:
- Pasted `package.json` contents (use `dependencies`; only include
  `devDependencies` if the user asks to include dev dependencies — say
  explicitly which set you audited).
- Pasted lockfile contents (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`).
- Pasted CycloneDX JSON or SPDX JSON SBOM contents.
- A plain list the user typed, e.g. "lodash 4.17.15, express 4.17.1".
- Raw `npm audit --json` output (npm 7+'s `{vulnerabilities: {...}}` format,
  or legacy npm 6's `{advisories: {...}}`) — do NOT re-parse this by hand
  into a `packages` list for `batch_query_vulnerabilities`. Call
  `enrich_npm_audit({ content })` directly instead: it parses the report
  itself, resolves each finding's GHSA advisory to a CVE alias via OSV
  (npm audit JSON almost never carries a CVE id on its own), and returns the
  same remove-now/patch-now/patch-soon/scheduled/monitor ranking as step 9
  below in one call — this replaces steps 1, 3, and 9 for the findings it covers, though
  steps 4-8 (install scripts, maintainer/provenance checks, license
  compliance) still need the package names it flagged run through those
  tools separately, since npm audit's own JSON has no license/maintainer/
  install-script data. `yarn audit --json`/`pnpm audit --json` are not
  supported — treat those like a lockfile paste (step 1) instead.
- A GitHub repository URL (e.g. "audit https://github.com/owner/repo") — do
  NOT ask the user to paste `package.json`/lockfile contents in this case.
  Call `audit_github_repository({ url })` directly instead: it fetches the
  manifest/lockfile from the repo's default branch itself and runs steps 3,
  4, 6, and 8 below (vulnerability, install-script signal, license
  compliance, and — for whatever it flagged as critical/high severity, a
  possible typosquat, or deprecated — the `check_maintainer_changes`/
  `check_package_provenance` ownership checks too, up to 5 packages per call
  — one slot per package, so several versions of one package share its
  result — prioritized the same way step 6 already ranks them) in one call, replacing
  that part of the flow below. Read `coverage` and the summary first: every
  lockfile entry is checked for vulnerabilities, but only 100 packages
  (vulnerable ones first) get the license/install-script detail, and a
  summary starting `PARTIAL AUDIT` means not everything was covered — say
  so; never call a repo "clean" when `coverage.complete` is false.
  `vulnerablePackageCount` covers the whole lockfile; vulnerable packages
  past the 100-package detail cap are in `overflowVulnerablePackages`.
  Check `ownershipCheckNote` for any flagged
  package past that 5-package cap and call the two ownership tools on those
  directly. Still follow up per-package with `analyze_install_script` (for a
  package the tool's lighter `installScriptScanScope:
  "lifecycle-scripts-only"` signal flagged but didn't deep-scan — check
  `deepScanNote`) and `suggest_alternative` the same way you would from the
  pasted-content flow.

A non-npm list (a Python `requirements.txt`, a `Cargo.toml`, ...) can't go
through this flow — every audit tool here is npm-only. Say so, then check
each `name==version` with `query_vulnerabilities({ name, version,
ecosystem })` (`"PyPI"`, `"crates.io"`, ...), and label the result as a
per-package lookup, not a full audit.

If the user instead pastes **two** snapshots and asks what changed (a PR,
before/after, "did this upgrade introduce anything") — see
[Comparing two snapshots](#comparing-two-snapshots-pr-review) below instead
of the single-inventory flow.

If the message contains no parseable package list at all, ask the user to
paste their `package.json` or lockfile — or give a GitHub repo URL — rather
than guessing at what to audit.

## Steps

1. Prefer passing the raw pasted inventory straight to
   `batch_query_vulnerabilities` via its `content` input when the user gave a
   `package.json`, lockfile, CycloneDX JSON, or SPDX JSON document. Only
   manually build a `packages` array when the user gave a plain dependency
   list instead.
2. For raw `package.json` content, set `includeDevDependencies: true` only if
   the user explicitly asked to include dev dependencies; otherwise the tool
   defaults to production-ish dependencies only. Be explicit in the answer
   about what set you audited. For `yarn.lock`, note that the file itself
   cannot distinguish production from dev dependencies, so the tool will scan
   every resolved package and emit a warning about that.
3. Call `batch_query_vulnerabilities` once with the parsed/raw input. The tool
   now chunks large inventories internally — do not re-chunk the request in
   the skill layer unless the client's own request-size limit forces it.
   Each finding already includes severity, a summary, CVE aliases, and the
   fixed version — do not call `query_vulnerabilities` again per flagged
   package just to re-fetch detail you already have. The only exception:
   if the result has an `enrichmentNote` (a very large audit crossed the
   enrichment cap, or some advisory details couldn't be fetched), the
   vulnerabilities it names are ID-only — their severity and malware status
   are unverified, so don't call those packages safe or non-malicious; call
   `query_vulnerabilities` on those *specific* packages for full detail. Each result also carries `signals` (`deprecated`,
   `hasInstallScripts`, `popularityTier`/`maintenanceTier`,
   `possibleTyposquatOf`) directly — a clean `vulnerabilityCount: 0` with a
   flagged `signals` entry is NOT clean, and `signals` is `null` (not "the
   package is fine") for a `not-scanned` git/file/workspace entry, so don't
   read that null as reassurance either. When `content` was a lockfile, each
   result also carries `source` (`resolvedUrl`/`integrity` and
   `nonRegistryHost`/`identityMismatch`): `identityMismatch: true` means the
   resolved tarball doesn't actually match the declared package/version —
   the vulnerability count above was computed for the DECLARED package, not
   whatever the tarball actually is, so treat this as its own critical
   finding, separate from and on top of any CVE result. See the tool's own
   `warnings` array for anything flagged this way. For a hand-typed
   dependency list or raw `package.json` content (names never resolved
   against a registry, unlike a real lockfile/SBOM), also check the result's
   `unresolvedPackages`/`existenceCheckNote`: a name that doesn't exist on
   npm shows `vulnerabilityCount: 0` exactly like a genuinely clean package,
   and that field is what tells the two apart — report an unresolved name as
   its own finding (typo? never published?), never as "no known
   vulnerabilities." Every finding also carries `isMalware` — true for a
   confirmed-malicious package (an OSV `MAL-*` record, or a GitHub advisory
   with CWE-506), not an ordinary bug. An `isMalware` finding is the
   headline of the report: the package must be removed, not patched.
4. For every package the batch call flags, use `signals` from step 3 first
   — it already gives you `deprecated`/`maintenanceSummary`-equivalent data,
   `hasInstallScripts`, and `possibleTyposquatOf` for the specific requested
   version with no extra call. Only follow up with `get_package` (or
   `get_package_version` when an exact version was provided) for what
   `signals` does NOT cover: license, and a closer look at maintainers.
   Treat install scripts as a separate risk signal from known CVEs, not
   something to fold into the same score. If the user wants to know what a
   flagged install script actually *does* rather than just that one exists,
   follow up with `analyze_install_script` — it fetches the published
   tarball and statically scans the script and the files it references
   against npmscan's red-flags rubric, returning a `totalScore`/`riskTier`.
   `signals.hasInstallScripts` covers preinstall/install/postinstall only — a
   dependency's `prepare` never runs on a registry install. Also surface
   `signals.deprecated` (and `maintenanceSummary`, when you did call
   `get_package`) — a deprecated or abandoned dependency is a real finding,
   not just a CVE footnote. If `signals.possibleTyposquatOf` is set, this package's name is one typo
   away from a much more popular one — flag it prominently as a
   supply-chain risk to verify, not as confirmed malice.
5. If the user wants coverage beyond the direct dependencies you were given
   (asks about "transitive"/"indirect" risk, or the inventory is small — up
   to 15 root packages), call `analyze_transitive_dependencies` instead of, or
   in addition to, step 3. It walks each root's own dependency tree (default
   depth 2, capped at 3) and returns `vulnerablePaths` naming which direct
   dependency actually pulled in each vulnerable transitive package —
   `batch_query_vulnerabilities` alone only ever checks the exact packages
   listed. It has no `content` shortcut, so build the `packages` array by
   hand from the parsed inventory.
6. For a package that's flagged as critical/high severity, deprecated, a
   possible typosquat, or that the user specifically calls suspicious, add
   the two ownership/supply-chain checks — don't run these for every clean
   package in a large audit, they're expensive and only useful signal on
   elevated-risk packages:
   - `check_maintainer_changes` — reconstructs maintainer-add/remove history
     from the npm packument and flags account-takeover patterns (a new
     maintainer who published shortly after being added, a sudden full
     maintainer-list replacement, a long-standing maintainer quietly
     dropped) plus GitHub repo transfers/archival. If it flags a newly added
     or fully turned-over maintainer, follow up with
     `check_maintainer_blast_radius({ maintainerUsername })` on that
     account — it lists every other package the same account currently
     touches and flags a tight cluster of packages published within a short
     window of each other, the compromised-account shape behind the 2025
     chalk/debug ("qix") incident (~18 packages within ~2 hours). A large
     total package count alone is not a red flag; only a tight cluster is.
     A cluster note starting "Discounted:" means it's at least 30 days old
     and OSV.dev lists no malware for its versions — report it as a past
     burst that stayed clean, not a current threat.
   - `check_package_provenance` — checks npm's Sigstore publish provenance
     against reality: does the attested source repo/commit match
     `package.json`'s declared repository, is this package missing
     provenance while its npm-scope/maintainer peers consistently have it,
     and does the tarball's install scripts/dependencies match what's
     actually committed at the attested source commit (a mismatch here is
     the stolen-npm-token publish pattern). Structural only, not a
     cryptographic re-verification. A version published before npm
     provenance existed (2023-04-19) skips the peer comparison.
7. Only call `get_latest_advisories` if the user separately asks for
   broader npm-ecosystem context — it is not part of the default flow, and
   it is NOT the malware check: its `malware`/`osv` feeds only list recently
   published advisories. Malware detection is the `isMalware` flag on the
   findings from step 3.
8. If the user asks about license policy/compliance (or pastes an
   allow/deny list), call `check_license_compliance` with the same parsed
   package list. With no `policy` given it applies the default enterprise
   rule (copyleft/network-copyleft/proprietary = violation); pass
   `policy: { allow, deny }` when the user states their own rule. Report
   `needsReview` licenses (unrecognized/mixed SPDX expressions) separately
   from confirmed violations — don't silently treat "unknown" as compliant.
9. Once you have the full set of flagged CVE/GHSA findings (from step 3
   and/or 5), and there is more than a couple of them, call
   `prioritize_remediation` with one `{packageName, cveId, severity,
   currentVersion, fixedVersion, advisoryId, findingType}` entry per finding
   to get a remove-now / patch-now / patch-soon / scheduled / monitor tier
   per finding (a confirmed-malware finding forces `remove-now` ahead of
   everything else — pass each finding's `id` through as `advisoryId`, which
   the tool looks up to detect malware advisories itself, and set
   `findingType: "malware"` for every finding whose `isMalware` was true;
   CISA KEV status overrides everything else after that; EPSS exploitation
   probability is the primary ranking signal otherwise, and an EPSS of 10%+
   always ranks at least `patch-soon`; severity is the fallback). If
   `malwareCheckFailedAdvisoryIds` is non-empty, say those findings' malware
   status is unknown. Lead the
   summary report with this ranking instead of a flat severity list — it
   answers "what do I fix first," which is usually what the user actually
   needs from an audit with more than a few findings. Treat any `remove-now`
   finding as the headline of the report, ahead of the ranked table, not
   just its top row.
10. For any package that ends up flagged as deprecated, vulnerable at its
    latest version, abandoned/stale, or a confirmed typosquat, offer (don't
    force) a replacement: `suggest_alternative` combines the maintainer's own
    deprecation hints with category-matched search results and returns
    plain-language `whySuggested` notes per candidate, or a
    `nonPackageAlternatives` entry when a language built-in supersedes the
    package entirely. Call it when the user asks what to use instead, or
    proactively name it as available in the summary rather than always
    running it unasked for every flagged package.
11. Produce one summary report: a table of package → flagged issue(s) (CVE/
    GHSA id + severity + fixed version, "risky install script", "deprecated/
    unmaintained", "possible typosquat", "maintainer/provenance anomaly",
    and/or "license violation") → the `npmscanUrl` from that tool's result →
    a one-line recommendation (upgrade to the fixed version, patch, replace,
    or no action needed). If `prioritize_remediation` ran, order the table by
    its tier/rank instead of by package name.

## Comparing two snapshots (PR review)

When the user gives a **before** and **after** snapshot (any mix of
`package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`) and asks
what changed, call `diff_dependencies({ before, after })` directly — this
replaces the batch-query flow above, it doesn't precede it.

- Lead with `installScriptIntroduced` findings — a routine-looking version
  bump that quietly adds a postinstall script is the shape of a
  compromised-maintainer supply-chain attack, and is the single highest-
  signal field this tool returns. It counts preinstall/install/postinstall
  only; a newly added `prepare` shows up in `installScriptKeysIntroduced`
  but never runs on a registry install, so mention it without alarm.
- Check `sourceIntegrityChanged` on every changed package too, right
  alongside `installScriptIntroduced` — it catches a DIFFERENT attack shape:
  a lockfile entry whose resolved tarball URL or integrity hash changed
  while the version string stayed IDENTICAL (a compromised registry mirror,
  or a hand-edited lockfile), which a version-only read of the diff would
  report as "no change" (`changeType: "source-swap"`). See `resolvedUrl`/
  `integrity` on the entry for what actually changed. If `identityMismatch`
  is true, the tarball is a different package or version than declared —
  `tarballName`/`tarballVersion` say what really installs, and the
  vulnerability fields describe that. Report it as a headline finding.
- Check `projectLifecycleChanges` (the SCANNED PROJECT's own root
  preinstall/install/postinstall/prepare scripts) and `overridesChanges`
  (`overrides`/`resolutions`/`pnpm.overrides`) even when the dependency list
  itself shows nothing — a PR that only adds a root postinstall or quietly
  removes a security override changes neither `added`/`removed`/`changed`,
  and is exactly the kind of change a diff review exists to catch. Both are
  counted in `flaggedCount`; don't report "no changes" on a diff that only
  flagged one of these.
- Report `vulnerabilityDelta` per changed package (introduced / fixed /
  still-vulnerable / still-clean), not just a final isVulnerable flag — the
  direction of the change is the point of a diff.
- Note the detected `beforeFormat`/`afterFormat` and any `comparisonNote`
  when the two snapshots are different formats (e.g. a range in
  `package.json` resolved against a pinned lockfile version).
- yarn.lock has no direct/transitive distinction, so a diff against a
  yarn.lock covers every resolved package in the file, not just direct
  dependencies — say so if relevant to what changed.

If the user instead wants a machine-parseable PASS/WARN/FAIL merge
verdict — for a CI check or a PR-comment bot, not a conversational
explanation — use the `ci-pr-gate` skill instead; it applies a fixed policy
on top of the same `diff_dependencies`/`simulate_dependency_upgrade` output.

## Output requirements

- Always include the `npmscanUrl` for every flagged package so the user can
  read the full write-up on npmscan.com.
- Keep known-vulnerability, install-script, maintenance/deprecation,
  typosquat, maintainer/provenance, and license risk visually separate — a
  package with no CVEs but a `postinstall` script (or a `possibleTyposquatOf`
  flag) is not "clean."
- When a CVE has a `fixedVersion`, name it directly in the recommendation
  ("upgrade to X.Y.Z") rather than a generic "upgrade the package."
- State which set was audited (e.g. "checked 24 production dependencies,
  skipped devDependencies").
- If the input was an SBOM, state that non-npm entries (if any) were skipped
  and surface the tool's warning/ignored-count metadata when relevant.

## Do not

- Do not guess a version that wasn't provided — call `batch_query_vulnerabilities`
  without a version rather than inventing one.
- Do not fabricate CVE/GHSA ids, severities, or fixed versions beyond what
  the tools returned.
- Do not silently drop non-npm SBOM entries — say they were skipped because
  npmscan's vulnerability pipeline is npm-only.
- Do not treat `possibleTyposquatOf` as proof of malice — it's a rule-based
  heuristic (name similarity + low popularity), not a verdict. Report it as
  "worth verifying," matching the tool's own hedged language.
- Do not run `check_maintainer_changes`/`check_package_provenance` across an
  entire large inventory by default — reserve them for flagged/suspicious
  packages or an explicit request, they're per-package deep checks, not a
  batch scan.
- Do not treat a missing `provenance` or a repository transfer as confirmed
  compromise on its own — both tools return hedged findings meant to prompt
  verification, not a verdict.
- Do not treat a large `totalPackagesFound` from `check_maintainer_blast_radius`
  as a red flag by itself — many legitimate maintainers publish hundreds of
  packages over a career. Only a `tight-publish-cluster` finding (several
  packages' latest versions landing within a short window of each other) is
  the actual signal.
- Do not invent a replacement package name — `suggest_alternative` already
  distinguishes maintainer-named replacements from category-matched guesses
  and reports `nonPackageAlternatives` when no package is the right answer;
  don't override that with your own guess.
- Do not read `source.identityMismatch: true` as a minor detail folded into
  the vulnerability count — it means the vulnerabilityCount/signals reported
  for that package were computed for the DECLARED name/version, not
  whatever the resolved tarball actually is. Report it as its own headline
  finding, not a footnote.
- Do not read a name in `unresolvedPackages` (from a hand-typed list or raw
  `package.json` audit) as clean just because its `vulnerabilityCount` is 0 —
  it means the name wasn't found on the npm registry at all, not that it has
  no known vulnerabilities. This check doesn't run for a real lockfile/SBOM
  input, since those names were already registry-resolved when generated.
- Do not call an `audit_github_repository` result clean when
  `coverage.complete` is false or the summary starts `PARTIAL AUDIT`.
- Do not skip `projectLifecycleChanges`/`overridesChanges` when reporting a
  `diff_dependencies` result just because the dependency list itself shows
  no changes — a PR that only touches the project's own root scripts or an
  override is a real, flaggable change with nothing in `added`/`removed`/
  `changed` to hint at it.

- Do not attempt to install, upgrade, or publish packages yourself; this
  skill only reads data through NPMScan's read-only MCP tools.

## Tools used

`batch_query_vulnerabilities`, `get_package`, `get_package_version`,
`analyze_install_script`, `analyze_transitive_dependencies`,
`check_maintainer_changes`, `check_maintainer_blast_radius`,
`check_package_provenance`,
`check_license_compliance`, `diff_dependencies`, `prioritize_remediation`,
`enrich_npm_audit`,
`suggest_alternative`, `get_latest_advisories`, `audit_github_repository` — all provided by the `npmscan` MCP server bundled with this plugin
(`.mcp.json`). See [references/test-prompts.md](references/test-prompts.md)
for prompts to manually verify this skill after installing or editing it.
