---
name: package-trust-check
description: Investigate whether one specific npm package is trustworthy — maintainer/ownership takeover signals, publish-provenance mismatches, and risky install scripts. Use when the user asks if a single named package is safe, compromised, hijacked, suspicious, or "can I trust this" — not for auditing a full package.json/lockfile (see dependency-audit) and not for a plain factual question like "what does X do."
---

# NPMScan package trust check

Use this skill when the user names **one specific package** (optionally a
version) and asks a trust question about it — "is X safe to use," "was X
compromised," "should I be worried about X," "check X's maintainers." This
is a deep, single-package investigation: it runs checks `dependency-audit`
deliberately skips for every package in a batch because they're too
expensive to run at scale.

If the user instead pastes a `package.json`/lockfile/dependency list or asks
to audit multiple packages, use the `dependency-audit` skill instead — don't
run this skill's checks across a whole inventory. If the question is purely
factual with no trust/safety angle ("what does lodash do," "what's the
latest version of express"), just answer directly with `get_package` — don't
invoke the full investigation for that. If the user is instead choosing
between candidates for something not yet installed ("should we add X," "X
vs Y for this job"), that's a forward-looking pick, not a trust
investigation — use the `new-dependency-evaluation` skill.

## Steps

1. Baseline with `get_package` (or `get_package_version` if the user gave an
   exact version). Pull `deprecated`, `maintenanceSummary`,
   `possibleTyposquatOf`, `isLatestVersionVulnerable`/`highestSeverity`,
   `downloadTrend`, and days-since-last-publish. This alone answers a good
   chunk of "should I trust this" and grounds the deeper checks that follow —
   don't skip straight to the maintainer/provenance tools without it. If
   `get_package_version` comes back with `versionExists: false`, that version
   is no longer on npm but OSV still has advisories for it — usually a
   release npm pulled for being malicious (ua-parser-js 0.7.29, debug
   4.4.2). Report its `vulnerabilities` as real; it is not a "not found."
2. Check for malware. Every vulnerability finding carries `isMalware` — true
   for a confirmed-malicious package (an OSV `MAL-*` record, or a GitHub
   advisory with CWE-506 such as ua-parser-js's GHSA-pjwm), not an ordinary
   bug. Read it on the step-1 findings for this version, and call
   `query_vulnerabilities({ name })` with no version to see whether ANY
   release of this package was ever malicious — a past compromise is worth
   naming even when the current version is clean. Any `isMalware: true`
   finding on the version in question is the most severe possible outcome:
   report it plainly as known malware, never as "worth verifying."
   `get_latest_advisories({ type: "malware", affects: name })` (GitHub's
   malware feed) and `({ type: "osv", affects: name })` (OpenSSF's) only
   cover recently published advisories — useful for a brand-new incident
   OSV hasn't indexed yet, but an empty result says nothing about history.
3. Call `check_maintainer_changes({ name })`. It reconstructs maintainer
   add/remove history from the npm packument and flags:
   - a maintainer added recently who then published shortly after (the
     account-takeover pattern behind the Sept 2025 chalk/debug "qix"
     compromise and ua-parser-js),
   - a full sudden replacement of the maintainer list,
   - a long-standing maintainer quietly dropped,
   - a maintainer-list change on npm not yet tied to any release — flag this
     as the *more* urgent case, since access changed hands but nothing has
     shipped with it yet, so there's no version to warn the user off of.
   Also reports GitHub repository transfer/archival — a transfer isn't
   automatically hostile (e.g. jade → pug was a documented rename), say so
   rather than treating every transfer as a red flag. If it flags a newly
   added or fully turned-over maintainer, immediately follow up with
   `check_maintainer_blast_radius({ maintainerUsername })` on that account
   — it lists every other package the same account currently touches and
   flags a tight cluster of packages published within a short window of
   each other, the compromised-account shape behind incidents like the 2025
   chalk/debug ("qix") compromise and the 2026 keyv/cacheable "Shai-Hulud"
   worm. Don't stop at the one named package if the maintainer signal is
   already concerning — a tight cluster across several packages is a
   materially worse finding than a single-package maintainer change, and
   this is a single-package investigation's best chance to catch that
   before the user asks about the next affected package separately. A large
   `totalPackagesFound` alone is not a red flag; only a tight cluster is. A
   cluster note starting "Discounted:" means it's at least 30 days old and
   OSV.dev lists no malware for its versions — a past burst that stayed
   clean, not a current threat; one naming a malware advisory is the
   opposite.
4. Call `check_package_provenance({ name, version })`. Three checks in one
   call: does the Sigstore build attestation's source repo/commit match
   `package.json`'s declared repository; is this version missing provenance
   while its npm-scope or maintainer peers consistently publish with it (a
   real anomaly, not just "no provenance" — a version published before npm
   provenance existed, 2023-04-19, skips this comparison, and `peers.note`
   says so); and does the tarball's actual install scripts/
   dependencies match what's committed at the attested source commit — a
   script or dependency on npm that was never committed in source is the
   stolen-npm-token publish pattern. This is structural verification, not a
   cryptographic re-check of the Sigstore bundle — say so if the user asks
   how deep it goes. For a version npm no longer lists, this tool returns a
   not-found error that names any OSV advisories — use those, don't stop at
   the 404.
5. If `get_package`/`get_package_version` in step 1 showed
   `hasLifecycleScripts`/a `preinstall`/`postinstall`/`prepare` entry, follow
   up with `analyze_install_script({ name, version })`. It fetches the
   published tarball and statically scans the script — and the files it
   references — against npmscan's red-flags rubric (child_process,
   network calls, `.ssh`/`.aws`/`.npmrc`/`*TOKEN`/`*KEY` access,
   obfuscation, remote binaries off untrusted hosts, exfil endpoints,
   eval-on-decoded-content), returning a `totalScore`/`riskTier`. A nonzero
   score isn't automatically malicious — a legitimate binary download (e.g.
   `cypress`) scores nonzero too — so report the actual `findings`, not just
   the score. A `prepare`-only package scores 0 unless its command does
   something alarming: npm never runs a dependency's `prepare` on install.
6. If the combined picture ends up genuinely concerning (a maintainer-
   takeover pattern, a malware finding, a provenance mismatch, a
   `possibleTyposquatOf` hit, or a critical install-script finding), offer — don't force —
   `suggest_alternative({ name, reason })` with `reason` set to whichever of
   `"vulnerable"`/`"abandoned"`/`"typosquat"`/`"general"` best fits, so the
   user has a next step instead of just a warning.
7. Produce one findings report, most-concerning signal first:
   - State the verdict per check plainly (e.g. "no maintainer-change red
     flags in the lookback window," not silence-as-clean).
   - Every finding from `check_maintainer_changes`/`check_package_provenance`
     is a hedged signal meant to prompt verification, not proof — say
     "worth verifying independently," matching the tools' own language,
     especially for anything below their `high`/`critical` tiers.
   - Include the `npmscanUrl` so the user can read the full write-up.
   - If nothing turned up anything but a low/none `riskTier` and no maintainer
     or provenance findings, say so plainly — this skill exists to give
     confident "looks clean" answers as often as it flags real risk.

## Do not

- Do not run this skill's checks across every package in a list — that's
  `dependency-audit`'s job, and `check_maintainer_changes`/
  `check_package_provenance` are deliberately reserved there for
  already-flagged packages only, not a full inventory.
- Do not treat a missing `provenance` field, a repository transfer, or a
  single maintainer addition as confirmed compromise on its own — report
  what the tool actually flagged (or didn't) and let the `riskTier`/points
  speak, don't editorialize past it.
- Do not skip `get_package` and jump straight to the deep checks — the
  baseline (deprecated, popularity/maintenance tiers, typosquat) is cheap
  and often already answers the question.
- Do not invent a replacement package name yourself — let
  `suggest_alternative` return its own `whySuggested`/`nonPackageAlternatives`
  rather than guessing.
- Do not silently skip `analyze_install_script` when lifecycle scripts exist
  just because `check_maintainer_changes`/`check_package_provenance` came
  back clean — a legitimate maintainer can still ship a genuinely risky
  script, and vice versa; report all applicable signals, not just whichever
  ran first.
- Do not skip `check_maintainer_blast_radius` once `check_maintainer_changes`
  flags a newly added or fully turned-over maintainer — that combination is
  exactly when the follow-up matters most, not an optional extra step.
- Do not treat a large `totalPackagesFound` from `check_maintainer_blast_radius`
  as a red flag by itself — many legitimate maintainers publish hundreds of
  packages over a career. Only a tight-cluster finding (several packages'
  latest versions landing within a short window of each other) is the
  actual signal.

- Do not soften an `isMalware: true` finding into a hedged "worth verifying"
  the way a `check_maintainer_changes`/`check_package_provenance` signal is
  — it is a confirmed report of malicious code, not a heuristic.
- Do not treat an empty `get_latest_advisories` malware/osv result as a
  clearance — those feeds only cover recent advisories. The `isMalware`
  flags on the OSV findings are the malware check.
- Do not read a `versionExists: false` result, or a provenance not-found
  error that names advisories, as "the version doesn't exist so it's fine" —
  that is exactly how npm removes malicious releases.
- Do not attempt to install, upgrade, or publish packages yourself; this
  skill only reads data through NPMScan's read-only MCP tools.

## Tools used

`get_package`, `get_package_version`, `query_vulnerabilities`,
`get_latest_advisories`, `check_maintainer_changes`,
`check_maintainer_blast_radius`, `check_package_provenance`,
`analyze_install_script`, `suggest_alternative`
— all provided by the `npmscan` MCP server bundled with this plugin
(`.mcp.json`). See [references/test-prompts.md](references/test-prompts.md)
for prompts to manually verify this skill after installing or editing it.
