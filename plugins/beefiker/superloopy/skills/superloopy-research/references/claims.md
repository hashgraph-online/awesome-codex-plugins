# Claims

Load this reference for Phase 3 and 3b: whenever a claim is contested, code-shaped, or high-risk, and before writing `claim-ledger.md`.

## Phase 3 - Verify contested claims by running code

Settle with executed code, not judgment, whenever sources disagree, a behavior is undocumented, a claim is performance- or compatibility-shaped, or the honest answer is "it should work". Dispatch one verification worker per claim: write the smallest self-contained script that tests the claim; run it; capture full stdout and stderr; pin runtime and dependency versions. Reply with the exact code, the full output, the environment, and a verdict — CONFIRMED / REFUTED / PARTIAL — grounded in the output. Journal each verdict to `verify-<slug>.md`.

## Phase 3b - Lock non-code claims through a claim ledger

Code settles code-shaped claims (Phase 3). Numeric, market-share, legal, dated, causal, and financial claims cannot be run — so they pass through a **data-flow-lock** instead (verification idea adapted from fivetaku/insane-research, MIT): the synthesis may assert a high-risk non-code claim **only** if it cleared this gate, and the gate's `verified-claims` output is the sole allowlist the synthesis draws from. Skip the gate and there is nothing to synthesize — the lock is self-enforcing.

The claim ledger is orchestrator-owned. Workers only return verified-claim markers as message text, the same channel as EXPAND markers — never a file. A high-risk claim clears the gate to `verified-claims` only when all hold:

- **Two or more independent observations, sitting on different surfaces.** Two pages on one domain count once, and so do two outlets reprinting one announcement — domain independence is necessary but nowhere near sufficient. Independence means the observations were produced by processes that *could* disagree: a rendered page against the machine-readable endpoint behind it, a first-party statement against a repository or registry artifact, marketing copy against the legal instrument it describes, a vendor's figure against a neutral denominator. Agreement between two mirrors of one surface is one observation with a spare URL. (Surface contrast adapted from fivetaku/insane-research; independent-observation grouping from the `ulw-research` skill in code-yeongyu/lazycodex; both MIT.)
- **A neutral denominator for every share, ranking, growth, or adoption number.** Establish the number against a source that is not selling the outcome — a broad public developer survey, a public registry's package or download record, an independent ranking index, a regulator's filing. Vendor-supplied figures may corroborate but never establish.
- **One counter-search** actively looked for a refutation and did not find a stronger one.
- **A primary source** (the standard, filing, dataset, or first-party doc) backs it, not only secondary commentary.
- **Both dates recorded**: `observed` (when you retrieved it) and `as-of` (the date the content itself holds for). Conflating them turns a claim that was right last year into a wrong claim today, and it is the failure the counter-search is worst at catching. A claim whose `as-of` falls outside the Phase 0 as-of window cannot clear silently — either it is re-established inside the window or the synthesis states the vintage.

**Proof is priced.** Before you spend a verification lane, record what being wrong actually costs: a claim that a decision rests on earns code execution or the full gate, and a claim that only adds supporting context can be deferred with a hedge or dropped. Risk tier comes from the consequence of the claim being wrong, not from how interesting it is. This keeps the gate binary — it never softens — while keeping the expensive path scarce, so saturation stays affordable on the claims that matter. Record the decision either way; a deferral you wrote down is a known limit, and one you did not is a hole. (Proof-cost ledger adapted from the `ulw-research` skill in code-yeongyu/lazycodex, MIT.)

Anything that fails goes to an `Unresolved` (insufficient evidence) or `Refuted` (counter-search won) annex — abstention is a correct outcome, not a gap to paper over. Maintain `claim-ledger.md` as a table the validator can read, one row per claim:

```text
| id | claim | risk | cost | observations | counter | primary | observed | as-of | depends-on | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | <assertion> | high | <cost of being wrong> | api: <url> · rendered: <url> | <counter-search result> | <primary source> | 2026-07-29 | 2026-06-01 | none | verified |
```

`observations` holds `surface: url` entries separated by `·`, and the surface labels are what the gate counts — two entries labelled the same surface are one observation. The label vocabulary is closed, because a free-text label lets one observation be renamed into two: `rendered`, `api`, `repo`, `registry`, `standard`, `filing`, `legal`, `dataset`, `survey`, `press`, `community`, `runtime`. Of those, `api`, `repo`, `registry`, `standard`, `filing`, `legal`, `dataset`, and `runtime` come from the system or authority itself rather than from commentary about it, and a high-risk claim needs at least one of them — two outlets and a forum thread agreeing is press repetition, not primary footing. `depends-on` lists the ids this claim rests on, or `none`. `status` is `verified`, `unresolved`, `refuted`, or `deferred`. A claim cannot be `verified` while anything it depends on is unresolved or refuted: dependency is how one collapsed fact takes its downstream claims with it instead of leaving them standing in the synthesis. (Claim dependency adapted from the `ulw-research` skill in code-yeongyu/lazycodex, MIT.) Draw the synthesis only from `verified` rows. Worker reply marker (message text, same channel as EXPAND):

```text
## CLAIMS
- CLAIM: <non-code assertion> - RISK: high|normal - COST: <what a wrong call costs> - OBSERVATIONS: <surface label: url · surface label: url> - COUNTER: <refutation search result> - PRIMARY: <primary source or none> - AS-OF: <date the claim holds for>
```
