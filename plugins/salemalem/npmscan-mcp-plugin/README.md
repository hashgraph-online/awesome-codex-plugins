# NPMScan plugin for Claude Code

A [Claude Code plugin](https://code.claude.com/docs/en/plugins) that gives
Claude read-only npm package and vulnerability lookups, backed by
[npmscan.com](https://npmscan.com)'s free, unauthenticated MCP server.

NPMScan is also officially listed for both ChatGPT and Claude on
[npmscan.com's MCP page](https://npmscan.com/mcp), so users can verify that
this plugin points at the same public service.

## Official listings

- **Claude** (Anthropic's official Claude directory):
  [claude.ai/customize/skills/…/npmscan](https://claude.ai/customize/skills/id/aa8fcafe-0bcd-41b6-9e07-6c7ebbb71153%40anthropic-plugin-directory)
- **ChatGPT** (install npmscan as an app for one-click setup):
  [chatgpt.com/plugins/…/npmscan](https://chatgpt.com/plugins/plugin_asdk_app_6a6a699e6f3481918d5e6034432894f2?q=npm)
- **mcpHQ**: [mcphq.org](https://github.com/mcpHQ/awesome-mcp-servers)
- **TensorBlock MCP Index**: [tensorblock.co/mcp](https://github.com/TensorBlock/awesome-mcp-servers)
- **Awesome Gemini CLI**: [Piebald-AI/awesome-gemini-cli](https://github.com/Piebald-AI/awesome-gemini-cli)
- **Awesome Gemini CLI Extensions**: [Piebald-AI/awesome-gemini-cli-extensions](https://github.com/Piebald-AI/awesome-gemini-cli-extensions)
- **Setup docs for other clients**: [npmscan.com/mcp](https://npmscan.com/mcp)

Pending:

- **Grok Build** (xAI's official plugin marketplace): submitted in
  [xai-org/plugin-marketplace#1506](https://github.com/xai-org/plugin-marketplace/pull/1506),
  awaiting xAI review. See [Using it with Grok Build](#using-it-with-grok-build).
- **GitHub Copilot** (Awesome Copilot marketplace): submitted in
  [github/awesome-copilot#5142](https://github.com/github/awesome-copilot/issues/5142).
- **Gemini CLI** (extension gallery): indexed automatically from this repo. See
  [Using it with Gemini CLI](#using-it-with-gemini-cli).

## What it adds

- **MCP server** (`npmscan`, `https://npmscan.com/api/mcp`) with
  twenty-three tools — see [Tools](#tools) below. Every tool result includes
  an `npmscanUrl` linking back to the full write-up on npmscan.com. No API
  key or auth required — same public data as the website. The server is
  stateless and rate-limited to 30 requests/minute per IP. Every
  vulnerability finding carries `isMalware`, so a confirmed-malicious
  package is reported as malware to remove, never as an ordinary bug.

- **`/npmscan:dependency-audit` skill** — chains `batch_query_vulnerabilities`
  → `get_package`/`get_package_version` → `analyze_transitive_dependencies`
  → the maintainer/provenance/license/remediation/alternative tools into one
  dependency-audit report, instead of leaving that tool sequencing to Claude
  each time. Also handles PR-style before/after diffs via
  `diff_dependencies`, raw `npm audit --json` output via `enrich_npm_audit`,
  and a bare GitHub repo URL via `audit_github_repository`. Triggers
  automatically when you paste a `package.json`/lockfile/SBOM, give a GitHub
  repo URL, or ask to check/audit your dependencies, or invoke it directly.
  See [`skills/dependency-audit/SKILL.md`](skills/dependency-audit/SKILL.md).

- **`/npmscan:package-trust-check` skill** — a deep, single-package
  investigation for "is X safe / was X compromised" questions: a malware
  check (including versions npm has since removed for being malicious),
  maintainer add/remove history (account-takeover patterns),
  publish-provenance cross-checks, and install-script scanning, in one
  report. Triggers
  automatically on a trust question about one named package; not for
  auditing a whole dependency list (that's `dependency-audit`). See
  [`skills/package-trust-check/SKILL.md`](skills/package-trust-check/SKILL.md).

- **`/npmscan:new-dependency-evaluation` skill** — for a forward-looking
  choice about what to *add*, not what's already installed: comparing 2-5
  named candidates ("axios vs got vs node-fetch"), evaluating one candidate
  against its real peers, or shortlisting candidates from a described need.
  Orchestrates `compare_packages`/`suggest_alternative`/`search_packages`
  into a structured side-by-side with a deterministic pick. See
  [`skills/new-dependency-evaluation/SKILL.md`](skills/new-dependency-evaluation/SKILL.md).

- **`/npmscan:incident-response` skill** — turns an existing finding, or
  just a vague symptom description ("npm install did something weird"),
  into concrete `get_remediation_playbook` steps: real incident references,
  severity, and prevention tips, not improvised advice. See
  [`skills/incident-response/SKILL.md`](skills/incident-response/SKILL.md).

- **`/npmscan:ci-pr-gate` skill** — turns a dependency change (a
  before/after snapshot, or one or more named "bump X from A to B"
  upgrades) into one deterministic PASS/WARN/FAIL verdict formatted for a
  CI check or PR-comment bot, applying a fixed policy on top of
  `diff_dependencies`/`simulate_dependency_upgrade` — not a conversational
  report (that's `dependency-audit`'s job). See
  [`skills/ci-pr-gate/SKILL.md`](skills/ci-pr-gate/SKILL.md).

## Tools

NPMScan provides twenty-three tools:

| Tool | Description |
|---|---|
| `search_packages` | Search the npm registry by name or keywords. Each result includes weekly/monthly download counts, dependent-package counts, and rank among npmscan's own top-100k-by-downloads snapshot, so you can tell an established package from an abandoned or squatted one that merely matches the query text — flags `possibleTyposquatOf` when a low-popularity result's name is one typo away from a top-5,000 package. |
| `get_package` | Latest version, install scripts (`preinstall`/`install`/`postinstall`/`prepare`), maintainers, license, recent version history, weekly downloads, GitHub stars, TypeScript support, days since last publish, ecosystem-wide download rank, a 3-month download trend, and an `isLatestVersionVulnerable`/`highestSeverity` verdict (with fixed versions and `isMalware` per finding) — plus a rule-based (not model-generated) maintenance/popularity summary and typosquat flag computed from those numbers. |
| `get_package_version` | Metadata for one exact version plus an OSV.dev check scoped to that version — `isVulnerable`/`highestSeverity` as a direct safe/not-safe answer, with each finding's severity, summary, fixed version and `isMalware`. For checking a version pinned in a lockfile. A version npm has removed but OSV still has advisories for (usually one pulled for being malicious) comes back with `versionExists: false` and those findings, not a bare "not found". |
| `get_maintainer_profile` | Packages an npm username currently maintains via npm's own `maintainer:<username>` search index, plus precomputed download/dependent totals across all of them. Lists the most-downloaded `limit` packages (default 50, max 250); totals still cover every package found. A plain info lookup, not a security check — pair it with `check_maintainer_blast_radius` for the actual compromised-account signal. |
| `query_vulnerabilities` | OSV.dev lookup for known vulnerabilities affecting a package, optionally scoped to a version, with `isVulnerable`/`highestSeverity` as a direct verdict and each finding's severity, summary, fixed version and `isMalware`. For npm it also cross-checks the name/version against the registry: a name or version that isn't on npm still returns its OSV data, with `packageExists: false` and an `existenceCheckNote` — so a typo doesn't read as "clean", and a version removed for malware still shows its findings. Accepts `packageName` as an alias for `name`, and other ecosystems via `ecosystem` (e.g. `"PyPI"`). |
| `batch_query_vulnerabilities` | OSV.dev lookup across a whole dependency inventory at once — pass a flat `packages` list, or paste raw `package.json`/lockfile/CycloneDX JSON/SPDX JSON content via `content` and it parses that for you. Chunks large inventories internally, with severity, summary, CVE aliases, fixed version and `isMalware` per finding. Also reports names/versions that aren't on npm (`unresolvedPackages`/`nonexistentVersions` — never read those as clean), per-package `signals` (deprecated, install scripts, popularity, typosquat), and for lockfiles a `source` check that flags a tarball from an unexpected host or one that is a different package than declared (`identityMismatch`). |
| `get_latest_advisories` | Recently published npm advisories from one of three sources (one per call): `type: "reviewed"` (default) is GitHub's curated, mostly CVE-backed set, filterable by severity, vulnerability category, affected package name, or an exact GHSA/CVE ID; `type: "malware"` is GitHub's own malicious-package advisories; `type: "osv"` is OSV.dev's OpenSSF malicious-packages feed (`MAL-` ids). Cursor-paginated. These are feeds of recent advisories, not a package's full history — to check whether a package is or was malware, use `query_vulnerabilities` and its `isMalware` flags. |
| `get_cve` | NIST NVD lookup for one exact CVE ID (authoritative CVSS score/vector, CWEs, references), or a keyword/severity/CWE/date-range search. Enriched with CISA KEV status (actively exploited in the wild?) and FIRST.org EPSS (30-day exploitation probability). Falls back to the raw MITRE CVE record when NVD has no data yet. Not npm-scoped — NVD covers every ecosystem. |
| `analyze_install_script` | Fetches a package's published tarball and statically scans its `preinstall`/`install`/`postinstall`/`prepare` lifecycle scripts — and the files they reference, pulled from the tarball itself — against npmscan's red-flags rubric (`child_process` use, network calls, sensitive-path/env access, obfuscation, untrusted remote binaries, exfil hosts, eval on decoded strings, CI telemetry) plus a typosquat check. Returns a `totalScore` and `riskTier`. A `prepare`-only package scores 0 unless its command does something alarming, since npm never runs a dependency's `prepare` on install. A heuristic static scan, not proof of malice — it doesn't execute code or check maintainer history. |
| `analyze_transitive_dependencies` | Recursively resolves 1-15 direct/root packages' dependency graphs to a configurable depth (default 2, max 3) and batch-checks every resolved package against OSV.dev — surfaces vulnerabilities buried several levels deep that a flat `batch_query_vulnerabilities` call would miss, with `vulnerablePaths` naming which direct dependency pulled in each vulnerable transitive package. A total-node budget caps runaway graphs, reported via `truncated`/`truncationNote` rather than silently returning a partial scan as complete. |
| `check_package_provenance` | Checks a version's npm/Sigstore publish provenance against reality: flags a non-GitHub-hosted builder or an attested source repo that doesn't match `package.json`'s own `repository` field; flags a package missing provenance while its npm-scope/maintainer peers consistently have it (skipped for versions published before npm provenance existed, 2023-04-19); and diffs the published tarball's install scripts/dependencies against the source repository at the attested commit — the pattern of a stolen-npm-token publish that bypasses CI. For a version npm has removed, the error names any OSV advisories for it. Structural only, not a cryptographic re-verification of the Sigstore bundle. |
| `check_maintainer_changes` | Reconstructs a package's maintainer-add/remove history from the npm packument and flags account-takeover patterns — a new maintainer who published shortly after being added, a sudden full maintainer-list replacement, a long-standing maintainer quietly dropped, or a maintainer change not yet tied to any release. Also cross-checks the declared GitHub repository for transfers/archival. |
| `check_maintainer_blast_radius` | Given an npm username, finds the packages that account currently maintains and flags a tight cluster of packages published within a short rolling window of each other — the compromised-account pattern behind incidents like the 2025 chalk/debug ("qix") compromise and the 2026 keyv/cacheable ("Shai-Hulud") worm. Clusters over a year old count for a quarter, as do clusters at least 30 days old whose versions have no malware advisory, and clusters of near-unused packages don't count. A large total package count alone is never the signal. Lists the most-downloaded `limit` packages (default 50), always including every package in a cluster. |
| `get_remediation_playbook` | Maps a finding's `rule` value from `analyze_install_script`/`check_maintainer_changes`/`check_package_provenance` (or an `id` slug guessed from a plain-language description) to a human-authored incident-response playbook — concrete steps, severity, real-incident references, and prevention tips, not just a link. Includes `compromised-publisher` for when your own npm account or tokens were used to publish malware (token revocation, credential rotation, deprecating the bad versions). Pure local lookup, batches up to 10 rules per call. |
| `check_license_compliance` | Given a package list and an optional allow/deny license policy, classifies each declared SPDX license (permissive/weak-copyleft/copyleft/network-copyleft/proprietary/public-domain/unknown), understands simple SPDX expressions (`OR`/`AND`/`WITH`), and reports a compliance verdict per package. With no policy given, applies a default rule flagging only copyleft/network-copyleft/proprietary. Ambiguous expressions are reported as `needsReview`, not silently guessed at. |
| `diff_dependencies` | Compares two raw snapshots of a `package.json`, `package-lock.json`, `yarn.lock`, or `pnpm-lock.yaml` — e.g. before/after a PR — and reports added/removed/version-bumped packages. For every added or bumped package: a newly introduced `preinstall`/`install`/`postinstall` script (`installScriptIntroduced`; a new `prepare` is listed but never runs on a registry install), `vulnerabilityDelta` (introduced/fixed/still-vulnerable/still-clean), `sourceIntegrityChanged` (same version, different tarball or hash — `changeType: "source-swap"`), and `identityMismatch` (the tarball is a different package or version than declared, with vulnerabilities checked for the real one). Also diffs the project's own root lifecycle scripts and overrides. Ideal for a CI gate reviewing a dependency-changing PR. |
| `prioritize_remediation` | Given a batch of already-flagged vulnerability findings, ranks them by what to actually fix first, into a `remove-now`/`patch-now`/`patch-soon`/`scheduled`/`monitor` tier per finding. Confirmed malware (a `MAL-` id, or an advisory whose OSV record is a malware advisory — looked up automatically) is `remove-now`; CISA KEV status (active exploitation) is `patch-now`; otherwise FIRST.org EPSS (30-day exploitation probability) leads, with severity as a fallback, and an EPSS of 10% or more is at least `patch-soon`. A fix-order ranking across a backlog, not a merge gate. |
| `simulate_dependency_upgrade` | Classifies a specific version jump (e.g. a suggested `fixedVersion`) as safe/low-risk/review-recommended/breaking-change-likely/unknown/do-not-upgrade by semver bump, a newly-deprecated target, a newly-introduced `preinstall`/`install`/`postinstall` script, a tightened Node engine requirement, and a before/after OSV.dev check reporting `vulnerabilityDelta`. `do-not-upgrade` means the target is known malware, or npm no longer lists it while OSV still has advisories for it. Accepts a single `packageName` (or `name`)/`currentVersion`/`targetVersion`, or a `packages` batch of up to 100 upgrades in one call. Doesn't fetch changelogs or diff source — a fast deterministic pre-check. |
| `suggest_alternative` | Suggests better-maintained replacements for a deprecated, vulnerable, abandoned, or suspicious package by combining maintainer-provided deprecation hints, a hand-checked list of known successors for well-known packages (e.g. `request` → got/undici/ky, `colors` → @colors/colors), and deterministic npm search/category ranking — filtering out typosquats, deprecated, vulnerable and unverifiable candidates, and returning plain-language `whySuggested` notes, or a `nonPackageAlternatives` entry when a language built-in supersedes the package entirely. |
| `compare_packages` | Given 2-5 candidate packages for the same job (e.g. "axios vs got vs node-fetch"), fans the same registry/popularity/maintenance/vulnerability enrichment `get_package` computes out across every candidate in parallel, adds a lightweight install-script risk signal (a `prepare`-only candidate isn't penalized) and an install-size rollup (own + transitive), and returns a structured side-by-side plus a deterministic, reasoned pick — never a deprecated or typosquat-flagged candidate. A name that fails to resolve still appears with `found:false` rather than failing the whole call. |
| `audit_github_repository` | Given a GitHub repo URL, fetches its `package.json`/lockfile from the default branch (auto-detecting monorepos via workspace globs) and checks every lockfile entry for known vulnerabilities, then gives up to 100 packages — vulnerable ones first — the license-compliance, install-script and, for up to 5 elevated-risk packages (one slot per package, not per version), ownership-risk checks, in one call, no copy-pasting file contents required. `coverage` and a summary starting `PARTIAL AUDIT` say when not everything got every check. The most expensive tool in the suite; avoid calling it in a tight loop across many repos. |
| `generate_sbom` | Generates a spec-valid CycloneDX or SPDX SBOM from the same `packages`/`content` inputs `batch_query_vulnerabilities` accepts, with npmscan's own vulnerability and license findings embedded in each format's native fields (CycloneDX's top-level `vulnerabilities[]`, SPDX's `externalRefs[]`). Every finding's VEX state is `in_triage` — an honest "OSV/GHSA match found, not manually assessed," never a stronger claim. |
| `enrich_npm_audit` | Ingests raw `npm audit --json` output directly (npm 7+ or legacy npm 6 format) and ranks it with the same CISA KEV + FIRST.org EPSS + severity scoring as `prioritize_remediation`, resolving each finding's GHSA advisory to a CVE alias first (npm audit JSON almost never carries a CVE id on its own). `yarn audit --json`/`pnpm audit --json` are rejected rather than misparsed — use `batch_query_vulnerabilities` with the manifest/lockfile for those. |

## Install

### Option 1: add this repo as a marketplace

```
/plugin marketplace add salemalem/npmscan-mcp-plugin
/plugin install npmscan@npmscan
/reload-plugins
```

### Option 2: point Claude Code at a local checkout

```
claude --plugin-dir ./npmscan-mcp-plugin
```

Useful for testing changes before pushing them.

### Option 3: skip the plugin, add the MCP server directly

If you only want the tools (no bundled skills), you don't need this repo at
all:

```
claude mcp add --transport http npmscan https://npmscan.com/api/mcp
```

or in `.mcp.json` / `~/.claude.json`:

```json
{
  "mcpServers": {
    "npmscan": {
      "type": "http",
      "url": "https://npmscan.com/api/mcp"
    }
  }
}
```

(The `"type": "http"` field is required — Claude Code treats an entry with a
`url` but no `type` as misconfigured and skips it.)

## Try it

```
Does lodash have any known vulnerabilities?
Find npm packages for parsing CSV files
Before I install left-pad, tell me about its maintainers and install scripts.
Is chalk 5.6.1 safe? I heard there was a supply-chain incident.
What changed between these two package-lock.json snapshots?
Should we use axios, got, or node-fetch for our new HTTP client?
Audit https://github.com/expressjs/express for dependency issues.
```

Or paste a `package.json` and ask "audit my dependencies for vulnerabilities."

## Repo layout

```
npmscan-mcp-plugin/
├── .claude-plugin/
│   ├── plugin.json        # plugin manifest
│   └── marketplace.json   # lets this repo be added directly as a marketplace
├── .mcp.json               # bundles the npmscan MCP server
├── README.md
├── CHANGELOG.md            # what changed in each plugin version
├── LICENSE
├── .github/plugin/
│   └── plugin.json         # GitHub Copilot plugin manifest
├── gemini-extension.json   # Gemini CLI extension manifest
├── llms-install.md         # setup steps for Cline's one-click installer
├── assets/logo-400.png     # 400×400 logo for the Cline marketplace
├── assets/screenshot-*.png # Codex listing screenshots (npmscan.com pages)
├── .codex-plugin/
│   └── plugin.json         # Codex plugin manifest (ignored by Claude Code)
├── .agents/plugins/
│   └── marketplace.json    # lets Codex add this repo as a marketplace
├── .codexignore            # paths the plugin scanner skips
├── .plugin-scanner.toml    # HOL plugin-scanner config (see Using it with Codex)
├── SECURITY.md             # how to report a security problem
├── kimi.plugin.json        # Kimi plugin manifest (ignored by Claude Code)
├── icon.png                # Kimi plugin icon (dark tile, npmscan.com branding)
├── locales/                # Kimi interface translations (zh-CN)
│   └── zh-CN.json
├── outreach/               # directory listings: tracker, per-directory notes, scripts
└── skills/                 # shared by both clients; generated, don't edit here (see below)
    ├── dependency-audit/
    │   ├── SKILL.md
    │   └── references/test-prompts.md
    ├── package-trust-check/
    │   ├── SKILL.md
    │   └── references/test-prompts.md
    ├── new-dependency-evaluation/
    │   ├── SKILL.md
    │   └── references/test-prompts.md
    ├── incident-response/
    │   ├── SKILL.md
    │   └── references/test-prompts.md
    └── ci-pr-gate/
        ├── SKILL.md
        └── references/test-prompts.md
```

## Validate and test locally

```bash
claude plugin validate .
claude --plugin-dir .
```

Then in the session, run `/npmscan:dependency-audit`,
`/npmscan:package-trust-check`, `/npmscan:new-dependency-evaluation`,
`/npmscan:incident-response`, or `/npmscan:ci-pr-gate` (or just paste a
`package.json`/name a package and ask) to exercise each skill, and try the
prompts in each skill's `references/test-prompts.md`.

## Submitting to a marketplace

NPMScan is already listed in Anthropic's plugin directory (see
[Official listings](#official-listings)). The values used for that submission form
are in [outreach/targets/claude.md](outreach/targets/claude.md); update them there when the plugin
changes.

- **Self-hosted (this repo)**: nothing further to do — anyone can
  `/plugin marketplace add` this repo directly, as shown above.
- **`claude-plugins-community`**: submit via
  [claude.ai/admin-settings/directory/submissions/plugins/new](https://claude.ai/admin-settings/directory/submissions/plugins/new)
  (Team/Enterprise orgs) or
  [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit)
  (individual authors). Run `claude plugin validate .` first — the review
  pipeline runs the same check.
- **`claude-plugins-official`**: curated directly by Anthropic; there's no
  application form for it.

See Anthropic's [plugin docs](https://code.claude.com/docs/en/plugins) for
the full development and distribution guide.

## Using it with Kimi

This same repo is also a [Kimi plugin](https://moonshotai.github.io/kimi-code/en/customization/plugins.html):
[`kimi.plugin.json`](kimi.plugin.json) declares the same MCP server and
points at the same `skills/` directory. Claude Code ignores that file, and
Kimi prefers it over `.claude-plugin/plugin.json`, so each client reads its
own manifest and both load the same five skills.

- **Kimi Code CLI**: `/plugins install https://github.com/salemalem/npmscan-mcp-plugin`
  (or `/plugins install ./` from a local checkout).
- **Kimi Work**: in the plugin marketplace, click "Custom plugin" and ask
  Plugin Builder to import `https://github.com/salemalem/npmscan-mcp-plugin`.
  It appears under the **Personal** tab; click **+** to install.

The manifest is prepared for the official Kimi marketplace: full
`zh-CN` locale, `brandColor` (#ef4444, npmscan.com's primary red), a dark
rounded-tile `icon.png` built from the site's dark-mode logo, and
`hostKind: hosted`. Kimi's local validation passed with 0 errors / 0
warnings on v3.0.2 (the last version imported into Kimi; see [outreach/targets/kimi.md](outreach/targets/kimi.md)).
Official-marketplace publication goes through a Kimi review step — see
[outreach/targets/kimi.md](outreach/targets/kimi.md) for the status and the application steps.

Test results and marketplace submission steps: [outreach/targets/kimi.md](outreach/targets/kimi.md).

When editing, keep Kimi-only settings inside `kimi.plugin.json`. Don't add
root-level `commands/`, `agents/`, or `hooks/` directories for Kimi, because
Claude Code auto-loads those too.

## Using it with Grok Build

Grok Build reads this repo as-is (`.claude-plugin/plugin.json`, `.mcp.json`
and `skills/`), so it needs no Grok-specific manifest.

- **Status**: submitted to xAI's official marketplace in
  [xai-org/plugin-marketplace#1506](https://github.com/xai-org/plugin-marketplace/pull/1506)
  as a remote source pinned to commit `5cbf977` (v3.1.2). It's waiting for
  xAI to approve the CI run and do a code-owner review. The source stays on
  this personal-account repo rather than the NPMscan org, so the Claude and
  ChatGPT listings don't have to move.
- **After merge**: install with `/marketplace` or
  `grok plugin install npmscan` inside Grok Build.
- **Updating**: Grok Build installs the pinned commit only. To ship a new
  release, open a PR to `xai-org/plugin-marketplace` that bumps the `sha` of
  the `npmscan` entry in `.grok-plugin/marketplace.json`, then run
  `python3 scripts/generate-plugin-index.py`, `scripts/validate-catalog.py`
  and `scripts/generate-plugin-index.py --check` there. The index script
  fetches every plugin in the catalog and takes several minutes.

## Using it with Gemini CLI

This repo is also a [Gemini CLI extension](https://geminicli.com/docs/extensions/):
[`gemini-extension.json`](gemini-extension.json) declares the same MCP server
(`httpUrl`, streamable HTTP), and Gemini CLI loads the same five skills from
`skills/`.

```bash
gemini extensions install https://github.com/salemalem/npmscan-mcp-plugin
```

The install follows `main`, so each push offers installed users an update.
The [extension gallery](https://geminicli.com/extensions/) finds the repo
by its `gemini-cli-extension` GitHub topic and re-crawls it daily; there's
nothing to submit. Check a change with
`gemini extensions validate .` before pushing.

Antigravity CLI users (which replaced Gemini CLI for free and Google AI
Pro/Ultra accounts) can bring the extension over with
`agy plugin import gemini` after installing it in Gemini CLI.

## Using it with Cline

Cline connects to the hosted server directly; there's nothing to build and
no API key:

```bash
cline mcp install npmscan --transport http https://npmscan.com/api/mcp --yes
```

or in `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "npmscan": {
      "type": "streamableHttp",
      "url": "https://npmscan.com/api/mcp"
    }
  }
}
```

[`llms-install.md`](llms-install.md) has the same steps for Cline's one-click
installer. Cline's marketplace logo is
[`assets/logo-400.png`](assets/logo-400.png).

## Using it with Factory (Droid)

Droid installs Claude Code plugins as they are: it translates
`.claude-plugin/` and `.mcp.json` into its own layout when it caches the
plugin. Add this repo as a marketplace, then install the plugin:

```bash
droid plugin marketplace add salemalem/npmscan-mcp-plugin
droid plugin install npmscan@npmscan-mcp-plugin --scope user
```

The marketplace takes its name from the repo (`npmscan-mcp-plugin`), not
from the `name` in `.claude-plugin/marketplace.json`, so the plugin ID is
`npmscan@npmscan-mcp-plugin`. Check it with `droid mcp list`: `npmscan`
should show as `http  connected`, and the five skills come with it.

## Using it with Codex

This repo is also a [Codex plugin](https://developers.openai.com/codex/plugins/build):
[`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) points at the same
`skills/` and the same [`.mcp.json`](.mcp.json), and
[`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) lets
you add the repo as a marketplace:

```bash
codex plugin marketplace add salemalem/npmscan-mcp-plugin
codex plugin add npmscan@npmscan
```

Check it with `codex mcp list`: `npmscan` should show as enabled at
`https://npmscan.com/api/mcp`. The other clients ignore `.codex-plugin/` and
`.agents/`.

Before changing the Codex manifest, run the
[HOL plugin-scanner](https://github.com/hashgraph-online/hol-guard) that
[awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins)
uses (it needs 80 or more with no critical or high findings):

```bash
pipx install --force "plugin-scanner==3.57.0"
plugin-scanner scan . --format text
```

[`.plugin-scanner.toml`](.plugin-scanner.toml) turns off one Kimi rule that
misreads `kimi.plugin.json`
([hol-guard#6032](https://github.com/hashgraph-online/hol-guard/issues/6032)).
Remove it once that's fixed.

## Using it with TRAE

TRAE connects to the hosted server directly. Open this link to add it in one
click (TRAE asks you to confirm):

```
trae://trae.ai-ide/mcp-import?type=http&name=npmscan&config=eyJ1cmwiOiJodHRwczovL25wbXNjYW4uY29tL2FwaS9tY3AifQ%3D%3D
```

Or go to **Settings > MCP > Add > Create Manually** and paste:

```json
{
  "mcpServers": {
    "npmscan": {
      "url": "https://npmscan.com/api/mcp"
    }
  }
}
```

For one project only, put the same JSON in `.trae/mcp.json`. To add the
skills, copy the folders in `skills/` to `~/.trae/skills/` (or
`.trae/skills/` in a project), or zip one skill folder and use **Upload
Skill** in TRAE's marketplace.

## Also available for other AI clients

The same `npmscan` MCP server and the same `dependency-audit` /
`package-trust-check` / `new-dependency-evaluation` / `incident-response` /
`ci-pr-gate` skills are also available in ChatGPT via the official
[npmscan app listing](https://chatgpt.com/plugins/plugin_asdk_app_6a6a699e6f3481918d5e6034432894f2?q=npm)
(submission artifacts live in the main [npmscan](https://npmscan.com) app
repo, under `mcp/`).

**Where to edit the skills:** the main npmscan repo's `mcp/skills/` is the
only source. This repo's `skills/` folder is generated from it by
`npm run sync:plugin-skills` (run in the main repo), which rewrites the few
platform-specific sentences for Claude; `npm run sync:plugin-skills -- --check`
fails when the two have drifted. An edit made directly in this repo's
`skills/` is overwritten by the next sync.

## License

MIT — see [LICENSE](LICENSE).

Made by [BlockHacks.io](https://npmscan.com) — protecting the open source
ecosystem.
