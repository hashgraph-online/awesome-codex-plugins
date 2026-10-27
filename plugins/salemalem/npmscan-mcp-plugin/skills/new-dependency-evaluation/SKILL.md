---
name: new-dependency-evaluation
description: Help decide what to add as a NEW npm dependency — comparing 2-5 named candidates for the same job, evaluating one named candidate against its real peers, or shortlisting candidates from a described need, before anything is installed. Use for "which should we use for X," "axios vs got vs node-fetch," "is X a good pick for Y," "what should we use to do Z," "should we add X or is there something better." Not for auditing packages already in the project (see dependency-audit), not for a deep single-package compromise/trust investigation (see package-trust-check), and not for a plain factual question with no choice being made ("what does X do").
---

# NPMScan new dependency evaluation

Use this skill when the user is making a **forward-looking choice** about
what to add to a project — not investigating something already installed.
It orchestrates two tools that already do the hard work individually:
`suggest_alternative` (turns one candidate name into a real shortlist of
peers) and `compare_packages` (fans out enrichment across 2-5 named
candidates and returns a structured side-by-side with a deterministic pick).
This skill's only job is routing to the right combination of the two based
on how many candidates the user actually named, then presenting the result.

If the user instead asks whether a package **already in their project** is
safe to keep, use `package-trust-check` (single package) or `dependency-audit`
(a pasted inventory) — those investigate what's already there; this skill
evaluates what to add next. If the question has no choice or decision angle
at all ("what does X do," "what's the latest version of X"), just answer
directly with `get_package` — don't invoke this skill's tool chain for that.

## Determining what to compare

Count how many named candidates the user actually gave, then route:

1. **2-5 named candidates for the same job** (e.g. "axios vs got vs
   node-fetch," "should we use dayjs or date-fns") — go straight to
   `compare_packages({ packages })`. This is the common case and needs no
   extra tool call first.
2. **Exactly 1 named candidate** ("should we add uuid," "is left-pad a good
   choice," "can we use X for Y") — a single package has nothing to be
   compared against yet. Call `get_package({ name })` for the named
   candidate's own `description` (`suggest_alternative`'s `source` object
   doesn't include one), then `suggest_alternative({ name, reason:
   "general", limit: 4 })` to generate real peers (never invent
   plausible-sounding package names yourself). Screen the suggestions
   against that description per
   [Screening candidates before comparing](#screening-candidates-before-comparing-routing-cases-2-3)
   below, then call `compare_packages` with `[name, ...screened
   suggestions, up to 4]` so the original candidate is scored against real
   competition instead of judged in isolation. If `suggestions` comes back
   with fewer than 1 usable peer after screening (e.g. a built-in
   replacement fully covers the case, like `left-pad` →
   `String.prototype.padStart()`), skip `compare_packages` — there's
   nothing left to compare — and report the `nonPackageAlternatives` plus
   the `get_package` baseline on the named candidate instead.
3. **0 named candidates, just a described need** ("what should we use to
   parse dates," "we need something for HTTP retries") — call
   `search_packages({ query })` using the user's own description as the
   query. Build a 2-5 name shortlist from the results, preferring the
   highest `popularityTier`/`maintenanceTier` matches, skipping any result
   carrying `possibleTyposquatOf`, and screening each result's
   `description` against the user's *stated need* (their own words are the
   comparison anchor here — no extra fetch needed) the same way as case 2
   — then run `compare_packages` on that shortlist. If nothing in the
   search results looks like a real contender (all very-low
   popularity/stale, or nothing actually matches the described need), say
   so rather than forcing a comparison, and ask the user for a starting
   name or two.
4. **More than 5 named candidates** — `compare_packages` caps at 5. Don't
   silently drop candidates without saying so: run it on the first 5 and
   name which were left out, or ask the user to narrow the list if the
   ones dropped seem like they'd matter to the decision.

### Screening candidates before comparing (routing cases 2-3)

`suggest_alternative`'s `categoryOverlap` and `search_packages`'s result
ordering are both keyword/token-overlap signals, not semantic relevance —
and a single shared generic word (e.g. both packages' descriptions mention
"guid") combined with high popularity can rank an unrelated package above
genuinely relevant ones. This was confirmed directly: comparing candidates
for `uuid` (an RFC9562 UUID *generator*, `description: "RFC9562 UUIDs"`)
surfaced `win-guid` (`description: "Windows legacy GUID parser"` — an
unrelated Windows binary-format tool) as the top suggestion, ranked above
the real UUID library `@paralleldrive/cuid2`, purely because `win-guid`
happens to have very high download counts and shares the single word
"guid." Reading the two descriptions side by side makes the mismatch
obvious immediately ("generates RFC-standard UUIDs" vs. "parses legacy
Windows binary GUID structures") in a way `categoryOverlap`'s token count
alone does not catch. So for every candidate before it enters
`compare_packages`:

- Actually read and compare full description text, not just token
  overlap — the source's own `description` (from `get_package` in case 2,
  or the user's stated need in case 3) against the candidate's
  `description`. Ask in plain terms: does this candidate do the same job,
  or does it just share vocabulary with something that does? Drop
  candidates that fail this even if their `categoryOverlap` list looks
  populated — shared words are a hint to go check, not a verdict on their
  own.
- Treat a `categoryOverlap` of exactly one generic word (`"guid"`,
  `"data"`, `"util"`, etc.) as weak supporting evidence at best; two or
  more overlapping tokens, or overlap on a specific/technical term, is
  stronger — but the description comparison above is the actual decision,
  not the token count.
- Don't let a high `weeklyDownloads`/`popularityTier` on its own excuse a
  poor description match — a package can be extremely popular as a
  transitive dependency of something unrelated to the job at hand.

## Steps

1. Route per the table above and make the tool call(s).
2. Read `differentiators` before `recommendation` — it names which
   candidate(s) stand out on downloads, GitHub stars, TypeScript support,
   known vulnerabilities, deprecation, typosquat flag, install-script risk,
   and install-size footprint. This is what makes the comparison legible; don't just report the
   final pick with no supporting detail.
3. Report `recommendation.pick`, `runnerUp`, and `rationale` verbatim —
   don't substitute your own judgment for the deterministic score unless a
   `candidates[]` entry shows something the score can't see (e.g. the user
   already said they need TypeScript-first and two candidates are close).
   Always state `confidence` too — a `"low"` confidence pick between two
   close candidates is a materially different answer than a `"high"`
   confidence one.
4. Surface every `found: false` candidate with its `resolutionError`
   (typo? unpublished? malformed name?) rather than silently dropping it
   from the comparison you present.
5. Note that `installScriptRisk` here is the **lifecycle-scripts-only**
   signal (`scanScope: "lifecycle-scripts-only"`) — it scans the command
   strings, not the tarball. If the recommended pick has a nonzero
   `installScriptRisk.totalScore` and the user is about to actually install
   it, mention that `analyze_install_script` (via `package-trust-check`)
   gives the deeper, tarball-aware scan before they commit — don't run it
   automatically as part of this skill, just point at it. A candidate whose
   only lifecycle script is `prepare` (uuid's `lefthook install`) scores 0:
   npm never runs a dependency's `prepare` on install, so it is not a risk
   to weigh against it.
6. If the user's decision also turns on license policy (they mention a
   license constraint, or ask "which of these is safe to use license-wise"),
   follow up with `check_license_compliance` on the shortlist — it's not
   part of the default flow, only pull it in when license is actually in
   play.
7. Sanity-check `githubStars` against `weeklyDownloads` per candidate:
   `githubStars` is attributed to whatever repository the candidate's own
   `package.json` declares, unverified — a tiny, low-download package
   showing a huge star count (e.g. thousands of stars on a package with
   under a thousand weekly downloads) can mean its declared `repository`
   field points at a different, unrelated project's repo rather than its
   own (confirmed directly: `@aigne/uuid`, ~850 weekly downloads, declares
   `repository: github.com/uuidjs/uuid` — the real `uuid` package's repo,
   not its own — and so inherits that repo's star count). Flag a large
   downloads/stars mismatch like this as worth independent verification
   before adopting the package, rather than reporting the star count at
   face value as a credibility signal; this skill's tools don't run the
   deeper source-attestation check that would confirm or rule this out
   (`check_package_provenance`, via `package-trust-check`).
8. Treat `downloadTrend.changePercent` with caution when
   `weeklyDownloads` is low (roughly under a few thousand) — a small
   absolute change produces a large, noisy percentage (e.g. a candidate
   with 850 weekly downloads showing `"growing"` at 800%+ off a tiny prior
   base is statistical noise, not real momentum). Lead with the absolute
   download figure, not the percentage, for any low-volume candidate.
9. Note that `installSize.transitive.transitiveUnpackedSize` (a rollup
   across the candidate's resolved dependency tree, up to depth 2 / 60
   nodes) is often the more useful figure than the candidate's own
   `unpackedSize` — a small package can still drag in a large tree.

## Output requirements

- Always include each candidate's `npmscanUrl` so the user can read the full
  write-up.
- Present the comparison as a table (or clearly separated per-candidate
  summary) with at minimum: downloads/trend, popularity/maintenance tier,
  deprecated status, latest-version vulnerability status, TypeScript
  support, GitHub stars, and install-script risk tier — then the pick and
  rationale below it, not interleaved.
- When `suggest_alternative` was used to generate the peer set (routing
  case 2), say so explicitly ("compared against N real peers in the same
  category, not just this one package in isolation") so the user
  understands the comparison isn't limited to what they originally named.
- State plainly that this is a point-in-time snapshot (downloads,
  vulnerabilities, and maintenance activity all change) — not a permanent
  verdict, especially if the user's decision is time-sensitive.

## Do not

- Do not invent candidate package names yourself when the user gave 0 or 1
  — `search_packages`/`suggest_alternative` exist specifically so the
  shortlist is real, current registry data instead of names recalled from
  training knowledge that may be renamed, abandoned, or gone since.
- Do not call `compare_packages` with fewer than 2 or more than 5 packages
  — dedupe first (case-insensitive; the tool itself rejects exact
  duplicates with a 400), and route through cases 2-4 above instead of
  forcing a single name through it.
- Do not treat a deprecated or typosquat-flagged candidate as excluded from
  the comparison — `compare_packages` still returns them (with `deprecated`/
  `possibleTyposquatOf` set) so the user can see exactly why they lost; only
  `recommendation.pick` is guaranteed to skip them, not the `candidates`
  list itself.
- Do not silently narrow a >5-candidate list without telling the user which
  names were dropped and why.
- Do not use this skill to re-investigate a package the user already has
  installed and is worried about — that's `package-trust-check` or
  `dependency-audit`; this skill's tools are tuned for choosing among
  healthy-looking options, not for compromise/takeover forensics.
- Do not present `recommendation.pick` as a security clearance — it's a
  weighted popularity/maintenance/vulnerability/typosquat/install-script
  score, not a guarantee the package is free of issues the lighter scan
  can't see.
- Do not pass every `suggest_alternative`/`search_packages` result straight
  into `compare_packages` on the strength of `categoryOverlap` alone — a
  single generic shared token plus high popularity can rank an unrelated
  package first (verified: `win-guid`, a Windows GUID *parser*, outranked
  a real UUID library when comparing alternatives to `uuid`). Read each
  candidate's `description` and drop ones that aren't actually the same
  tool for the job before comparing them.
- Do not report a candidate's `githubStars` as a plain credibility signal
  without checking it against `weeklyDownloads` first — a low-download
  package with implausibly high stars likely has a `repository` field
  pointing at a different project's repo, not evidence of its own
  popularity.
- Do not attempt to install, upgrade, or publish packages yourself; this
  skill only reads data through NPMScan's read-only MCP tools.

## Tools used

`compare_packages`, `suggest_alternative`, `search_packages`, `get_package`
(for the source description in routing case 2), and optionally
`check_license_compliance` — all provided by the `npmscan` MCP server bundled with this plugin
(`.mcp.json`). See [references/test-prompts.md](references/test-prompts.md)
for prompts to manually verify this skill after installing or editing it.
