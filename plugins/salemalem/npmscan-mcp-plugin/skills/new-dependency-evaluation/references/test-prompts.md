# Test prompts for `new-dependency-evaluation`

Run these manually with the plugin loaded (`claude --plugin-dir ./npmscan-mcp-plugin`)
before publishing a change to this skill. Each case names the exact tool calls and fields the response
should surface — not just "did a tool get called," but "did the routing
logic pick the right case and did the real data survive into the answer."

1. **Three named candidates for the same job (routing case 1)** — ask:
   > "Should we use axios, got, or node-fetch for our new HTTP client?"
   Expect `compare_packages({ packages: ["axios", "got", "node-fetch"] })`
   directly, no `suggest_alternative`/`search_packages` call first. All
   three resolve (`found: true`), and `recommendation.pick` is non-null.
   Expect the response to lead with `differentiators` (downloads, GitHub
   stars, TS support) before stating the pick and its `rationale`/
   `confidence`.

2. **A deprecated candidate is named alongside healthy ones** — ask:
   > "We're picking between axios, request, and got — which one?"
   `compare_packages({ packages: ["axios", "request", "got"] })` returns
   `request` with `deprecated` set (it really is deprecated) and
   `differentiators.deprecated` including `"request"`.
   `recommendation.pick` must NOT be `"request"`. Expect the response to
   still list `request` in the comparison table (not silently drop it) while
   clearly stating why it lost.

3. **A typosquat stub named alongside its real target** — ask:
   > "Comparing lodash, lodahs, and underscore for utility functions — any
   > concerns?"
   `compare_packages({ packages: ["lodash", "lodahs", "underscore"] })`
   returns `lodahs` with `possibleTyposquatOf: { name: "lodash", ... }`.
   `recommendation.pick` must NOT be `"lodahs"`. Expect the response to
   flag the typosquat explicitly and prominently — not bury it in the
   table — as a real supply-chain risk to verify, matching the tool's own
   hedged framing.

4. **Exactly one named candidate (routing case 2)** — ask:
   > "Should we add uuid to the project, or is there something better?"
   Expect `suggest_alternative({ name: "uuid", reason: "general", limit: 4
   })` first — its `suggestions` exclude `"uuid"` itself and exclude any
   deprecated package — then `compare_packages` with `uuid` plus up to 4 of
   those suggestion names (5 total, at the tool's max). Expect the response
   to say explicitly that `uuid` was compared against real peers in its
   category, not evaluated alone, before giving the pick.

4b. **Screening catches a real false-positive match (routing case 2)** —
    same prompt as case 4. `suggest_alternative({ name: "uuid", reason:
    "general", limit: 4 })` returns `win-guid` in its `suggestions` with
    `description: "Windows legacy GUID parser"` and `categoryOverlap:
    ["guid"]` (a single generic token) — a real result, confirmed live: it
    is not a UUID-generation library, it's an unrelated Windows binary-
    format parser that happens to have very high weekly downloads. Expect
    the response to exclude `win-guid` from the `compare_packages` call (or
    if it slipped through, to flag it explicitly as not actually
    comparable rather than silently including it in the pick) — not treat
    its high popularity as making it a legitimate contender for a UUID
    library comparison.

5. **One named candidate whose only real alternative is a language
   built-in (routing case 2, no-compare fallback)** — ask:
   > "Do we need the left-pad package, or is there a better option?"
   `suggest_alternative({ name: "left-pad", reason: "general", limit: 4 })`
   returns `nonPackageAlternatives` including
   `"String.prototype.padStart()"` and an empty (or near-empty)
   `suggestions` array. Expect the response to skip `compare_packages`
   (nothing left to compare against) and instead recommend the built-in
   directly, naming it exactly — not a vague "there might be a native way
   to do this."

6. **A described need with zero named candidates (routing case 3)** — ask:
   > "What should we use to format dates? We don't have a preference yet."
   Expect `search_packages({ query: "date formatting" })` (or an equivalent
   close paraphrase of the described need) first, a 2-5 name shortlist built
   from results that excludes anything with `possibleTyposquatOf` set or
   very-low popularity, then `compare_packages` on that shortlist. Expect
   the response to name which candidates were shortlisted and why before
   giving the comparison.

7. **Two comparably healthy candidates — a real "too close to call"
   result** — ask:
   > "dayjs or date-fns for our new date-handling code?"
   `compare_packages({ packages: ["dayjs", "date-fns"] })` returns both
   `found: true`, a non-null `recommendation.pick` among the two, and a
   valid `confidence`. Expect the response to report `confidence` plainly —
   if it comes back `"low"` or `"medium"`, say the two are close rather than
   overstating the pick as a clear winner.

8. **A legitimate low-traffic package should not be misflagged** — ask:
   > "Comparing is-number against lodash for a small numeric check — worth
   > adding a whole extra dependency?"
   `compare_packages({ packages: ["is-number", "lodash"] })` returns
   `is-number` with `found: true`, `deprecated: null`, and
   `possibleTyposquatOf: null` despite its much lower download count.
   Expect the response to not treat low popularity alone as a red flag —
   only `deprecated`/`possibleTyposquatOf`/vulnerability findings are.

9. **Non-triggering — a plain factual question, no decision being made** —
   ask:
   > "What does the axios package do?"
   Expect this skill NOT to activate — at most one `get_package` call, no
   `compare_packages`/`suggest_alternative`/`search_packages` calls.

10. **Non-triggering — investigating something already installed** — ask:
    > "We already have `event-stream` in our lockfile — is it safe?"
    Expect `package-trust-check` to activate instead of this skill (a
    single already-installed package's trust question), not
    `compare_packages`/`suggest_alternative`.

11. **More than 5 named candidates (routing case 4)** — ask:
    > "We're choosing an HTTP client — considering axios, got, node-fetch,
    > undici, superagent, and ky. Thoughts?"
    `compare_packages` accepts at most 5 names. Expect the response to
    either run it on the first 5 and explicitly name `ky` (or whichever was
    dropped) as excluded, or ask the user to narrow the list to 5 — not a
    silent truncation with no mention of what was left out.

12. **License-constrained comparison excludes a copyleft candidate even if
    competitive (step 6)** — ask:
    > "Legal says nothing GPL — is graphviz an option compared to lodash
    > for our use case?"
    Expect `check_license_compliance({ packages: [{ name: "graphviz" },
    { name: "lodash" }] })` to run alongside/after the comparison,
    returning `graphviz` as `rawLicense: "GPL-3.0"`, `category:
    "copyleft"`, `isCompliant: false`, and `lodash` compliant. Expect the
    response to explicitly rule graphviz out on license grounds, not just
    report scores side by side and leave the license violation buried in a
    table cell.

13. **A non-SPDX license stays "needs review," not silently pass or fail
    (step 6)** — ask:
    > "Is nocodb's license going to be a problem if we only allow
    > MIT-licensed dependencies?"
    Expect `check_license_compliance({ packages: [{ name: "nocodb" }],
    policy: { allow: ["MIT"] } })` to return `rawLicense: "Sustainable Use
    License"`, `category: "unknown"`, `needsReview: true`, `isCompliant:
    false`. Expect the response to distinguish "flagged because it's
    unproven under your allow-list" from "flagged because it's confirmed
    copyleft" — nocodb's category is genuinely `unknown`, not a known-bad
    one.

14. **`compare_packages` rejects a duplicate name outright** — ask:
    > "Compare axios against Axios for us"
    (the same package, different casing — simulating a user accidentally
    naming the same package twice). Expect `compare_packages` to either be
    called with the names deduped first, or, if called with the duplicate,
    to come back as `tool_error` with a detail mentioning "duplicate" — not
    a comparison of a package against itself presented as a real result.

15. **A genuinely nonexistent candidate name (distinct from the typosquat-
    stub case in scenario 3)** — ask:
    > "Compare axios, got, and reqeust-lib-xyz for our HTTP client"
    (a name that's simply unpublished, not a typo of a real popular
    package). Expect `compare_packages` to still return all 3 entries, the
    unresolved one flagged `found: false` with a `resolutionError`, and
    `recommendation.pick` landing on `axios` or `got`. Expect the response
    to describe this candidate as "not found / doesn't appear to be a real
    package," not conflate it with scenario 3's "impersonating a real
    package" typosquat framing.

16. **A malformed/garbled candidate name doesn't abort the whole call** —
    ask:
    > "Compare axios against `%` for our HTTP client"
    (simulating a corrupted copy-paste). Expect
    `compare_packages({ packages: ["axios", "%"] })` to return a normal
    response where `axios` resolves fully and the `%` candidate comes back
    `found: false` with a `resolutionError` mentioning percent-encoding —
    not a total failure of the tool call.

17. **A `prepare`-only candidate is not an install-script risk** — ask:
    > "nanoid vs uuid vs @paralleldrive/cuid2 for generating ids?"
    uuid (`prepare: lefthook install`) and cuid2 (`prepare: husky`) used to
    get an install-script penalty that decided the pick. Verified live: all
    three now report `installScriptRisk.riskTier: "none"`. Expect the
    comparison not to cite install scripts against uuid or cuid2.

18. **A question in Russian** — ask:
    > "Какую библиотеку выбрать для генерации уникальных ID в Node.js?"
    Expect the skill to trigger, `search_packages` to be called with English
    terms (e.g. "unique id"), the answer to come back in Russian, and no
    package names that the tools didn't return.

To confirm the skill loaded and is namespaced correctly, run `/help` and
check the **Custom commands** tab for `/npmscan:new-dependency-evaluation`, or just
invoke it directly with that name.
