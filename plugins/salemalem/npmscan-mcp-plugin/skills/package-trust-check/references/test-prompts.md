# Test prompts for `package-trust-check`

Run these manually with the plugin loaded (`claude --plugin-dir ./npmscan-mcp-plugin`)
before publishing a change to this skill. Each case names an exact package/version and the exact fields the
response should surface — not just "did a tool get called," but "did the
right version and finding survive into the answer."

1. **The chalk/debug "qix" compromise — now outside the lookback window,
   correctly distinguished from "never happened"** — ask:
   > "Is chalk safe? I heard there was a supply-chain incident."
   Verified live (re-check before reusing, since the tool's 180-day
   lookback window moves forward every day this incident recedes further
   into the past): `check_maintainer_changes({ name: "chalk" })` now
   returns `findings: []`, `riskTier: "none"`, with `history.changes`
   showing the real record — `qix` was added as a maintainer in 2016
   (version 1.1.2) and REMOVED on 2025-09-08 (version 5.6.2, access
   revoked after the compromise was discovered) — but that removal is now
   well outside the 180-day window, so nothing in it is flagged today.
   Expect the response to explicitly distinguish "yes, chalk really was
   compromised via a maintainer account in Sept 2025 — this is public
   record" from "the tool's live check comes back clean today specifically
   because that event is now outside its lookback window, not because it
   never happened" — the same shape as case 2 below, not a vague "chalk had
   some issue once" or a false claim that nothing was ever flagged.

2. **event-stream, asked about the actual malicious 2018 version** — ask:
   > "Was event-stream 3.3.6 compromised? Is it still a risk today?"
   `check_maintainer_changes({ name: "event-stream" })` returns
   `changes: []` with `note: "No maintainer changes within the lookback
   window"` (`riskTier: "none"`) — the real 2018 flatmap-stream incident
   predates the tool's lookback window. Expect the response to explicitly
   distinguish "yes, 3.3.6 was the historically compromised version" (this
   is public record) from "the tool's live maintainer-history check comes
   back clean today because that event is outside the lookback window" —
   not silence on the historical fact, and not a false "still flagged."

3. **Non-triggering, purely factual** — ask:
   > "What does the lodash package do?"
   Expect this skill NOT to activate — at most one `get_package` call, no
   `check_maintainer_changes`/`check_package_provenance`/
   `analyze_install_script` calls.

4. **Non-triggering, multi-package** — paste a `package.json` containing
   `{ "minimist": "1.2.5", "is-number": "7.0.0" }` and ask:
   > "Audit these dependencies for vulnerabilities."
   Expect `dependency-audit` to activate instead of this skill — no
   per-package `check_maintainer_changes`/`check_package_provenance` calls
   across the list, just `batch_query_vulnerabilities` flagging minimist
   1.2.5 (GHSA-xvch-5gv4-984h, CRITICAL, fixed in 1.2.6).

5. **jade → pug: a real transfer, not a takeover** — ask:
   > "jade's GitHub repo now points somewhere else. Was it hijacked?"
   `check_maintainer_changes({ name: "jade" })` returns
   `declaredRepository: "https://github.com/jadejs/jade"`,
   `currentFullName: "pugjs/pug"`, `transferred: true`, finding
   `repository-transferred` (10 points, `riskTier: "low"`). Expect the
   response to name both the old and new repo explicitly and state this is
   a documented rebrand/transfer (jade → pug), not evidence of a hostile
   takeover — while still suggesting the user confirm the new owner
   independently, matching the tool's own hedge.

6. **@npmcli/arborist: a real, specific peer-provenance anomaly** — ask:
   > "Does @npmcli/arborist look legit? Check its publish provenance."
   `check_package_provenance({ name: "@npmcli/arborist" })` returns
   `provenance.hasProvenance: false` while
   `peers: { orgKind: "scope", orgIdentifier: "@npmcli", peersChecked: 8,
   peersWithProvenance: 8, peerProvenanceRate: 1 }`, finding
   `no-provenance-org-norm` (15 points, `riskTier: "moderate"`). Verified
   live — re-check these numbers before reusing them, since peer provenance
   adoption within a scope shifts as more packages publish with
   `--provenance` over time. Expect the response to cite the exact numbers
   (8 of 8 / 100% of @npmcli-scoped siblings publish with provenance, this
   one doesn't) rather than a vague "provenance is missing" — missing
   provenance alone isn't the finding, the peer-norm mismatch is.

7. **lodash: missing provenance with no anomaly** — ask:
   > "lodash shows no npm provenance badge. Is that suspicious?"
   `check_package_provenance({ name: "lodash" })` returns
   `provenance.hasProvenance: false`,
   `peers: { orgKind: "maintainer", orgIdentifier: "jdalton", peersChecked:
   8, peersWithProvenance: 0, peerProvenanceRate: 0 }`, `findings: []`,
   `riskTier: "none"`. Verified live. Expect the response to explain lodash
   predates provenance and so do its maintainer's other packages — no
   anomaly — rather than flagging the missing badge on its own.

8. **semver 7.6.3: a clean, well-formed provenance result** — ask:
   > "Check semver 7.6.3's publish provenance."
   `check_package_provenance({ name: "semver", version: "7.6.3" })` returns
   `sourceRepository`/`declaredRepository` both
   `https://github.com/npm/node-semver`, `repositoryMatchesBuild: true`,
   `sourceDiff: { addedInstallScripts: [], addedDependencies: [] }`,
   `findings: []`, `totalScore: 0`. Expect a plain "matches, zero findings"
   verdict, not hedged language reserved for an actual anomaly.

9. **cypress: a real, legitimate but nonzero-scoring postinstall** — ask:
   > "Is cypress's install process doing anything risky?"
   `get_package({ name: "cypress" })` shows
   `postinstall: "node dist/index.js --exec install"`, then
   `analyze_install_script({ name: "cypress" })` returns findings
   `lifecycle-present` (3 pts) + `child-process` (4 pts, from a
   `require('child_process')` in the scanned `dist/index.js`),
   `totalScore: 7`, `riskTier: "moderate"`. Verified live — the exact
   postinstall command/score can shift release to release; re-check before
   treating these numbers as fixed. Expect the response to name the
   finding (cypress spawns a child process during install as part of
   installing its platform binary) and explicitly say this reflects a
   real, expected step — not malicious behavior — matching the tool's own
   framing.

10. **node-sass: deprecated, with a named replacement offered** — ask:
    > "Can I still trust node-sass?"
    `get_package({ name: "node-sass" })` shows
    `deprecated: "node-sass is deprecated. Please use dart-sass instead."`
    Expect the response to report the deprecation, then offer
    `suggest_alternative({ name: "node-sass", reason: "deprecated" })`,
    which returns `sass` and `sass-embedded` with `whySuggested: "Named
    directly in node-sass's own deprecation notice; actively maintained."`
    — the exact replacement names should appear in the answer, not a
    generic "consider migrating away."

11. **An empty malware feed is not a clearance** — ask:
    > "Is lodash safe to use?"
    `get_latest_advisories({ type: "malware" | "osv", affects: "lodash" })`
    returns nothing, and those feeds only list recent advisories anyway.
    Expect the response to rely on the `isMalware` flags of the OSV findings
    instead, and to still run the maintainer/provenance/install-script
    checks — never "not in the malware feed, so it's safe."

12. **A long-standing maintainer quietly dropped, not a full turnover** —
    ask:
    > "A package's maintainer list dropped someone who had been publishing
    > releases for over a year, while the remaining maintainers stayed the
    > same and kept publishing normally. Is that on its own something to
    > worry about?"
    Expect the model to describe this as the `maintainer-removed-recently`
    finding — a lower-severity signal than a full turnover (the underlying
    rule scores it well below the high/critical tier a full replacement
    gets) — and to recommend the same verification posture as other
    maintainer-change findings, not silence and not alarm-level either.
    **Note:** this is a synthetic-fixture-only pattern (no live package in
    the repo's own tests exhibits it) — treat this as testing the skill's
    grasp of the rule's meaning and relative severity, not a live tool-call
    verification.

13. **A full maintainer-list replacement, contrasted against chalk's
    single addition** — ask:
    > "How would you tell the difference between chalk's situation (one
    > new maintainer added) and a case where every single maintainer on a
    > package was replaced at once?"
    Expect the response to correctly describe `full-maintainer-turnover`
    as the more severe finding — it stacks with `maintainer-added-recently`
    to a `critical` tier when the replacement team also publishes the next
    release themselves — not treat "a maintainer changed" as a single
    undifferentiated risk level regardless of how much of the list turned
    over. **Note:** same synthetic-fixture caveat as case 12 — no live
    package in the repo's tests exhibits a full turnover.

14. **Pending maintainer change vs. dormant package — the two ends of the
    "access changed, nothing shipped" case** — ask two variants of "a
    maintainer was just added to a package's npm listing, but no release
    has shipped with them yet — how urgent is that?": once assuming the
    package released something recently (expect this framed as urgent —
    access already changed, and there's no version yet to warn users off
    of, so the risk is live right now) and once assuming the package
    hasn't shipped in years (expect the response to note this falls
    outside the tool's lookback window given the package's dormancy, and
    to describe it as a much lower-urgency case rather than applying the
    same urgency framing regardless of activity). **Note:**
    synthetic-fixture-only, same caveat as cases 12-13.

15. **A version npm removed for malware** — ask:
    > "Is ua-parser-js 0.7.29 safe?"
    Verified live: `get_package_version` returns `versionExists: false` with
    GHSA-pjwm-rvh2-c87w (`isMalware: true`), and
    `check_package_provenance`'s not-found error names that advisory as
    KNOWN MALWARE. Expect a plain "this was a malicious release, removed
    from npm" verdict naming the advisory — not "that version doesn't
    exist," and not a hedged "worth verifying."

16. **A deprecated package and what to use instead** — ask:
    > "Is request safe to use, and what should I replace it with?"
    Expect: request reported as deprecated; `check_package_provenance` with
    no "peers have provenance" finding (2.88.2 was published in 2020,
    before npm provenance existed); `suggest_alternative` offering real
    HTTP clients (got, undici, ky, axios, node-fetch) — not niche matches
    like gaxios.

17. **A factual question with a false premise — no investigation** — ask:
    > "What's the latest version of lodash? I heard it has a critical RCE."
    Expect no trust-check sweep: `get_package` (and at most
    `query_vulnerabilities`) answers the version, and the premise is
    corrected with the real advisories and severities rather than repeated.

To confirm the skill loaded and is namespaced correctly, run `/help` and
check the **Custom commands** tab for `/npmscan:package-trust-check`, or just
invoke it directly with that name.
