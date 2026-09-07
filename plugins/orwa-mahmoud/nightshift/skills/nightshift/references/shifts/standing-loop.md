# Product evolution — open-ended — research the space and improve until quitting time

The flagship shift for spare agent capacity. The product, its users, and its market decide the
work; lint and tests prove each change rather than supplying the roadmap. It may ship a sharp fix
or a substantial feature, but never merges its own branch and never leaves a half-built path.

```text
- [ ] **Product evolution — research, build, and improve until quitting time.**
  - Ending: open-ended — hours and a deadline are required.
  - Isolate first: in repository mode, work on a dedicated nightshift branch named
    `nightshift/<short-purpose>-<YYYY-MM-DD>`, never the default branch. The optional
    `isolated-branch` rule profile makes checkout of `main`/`master`, merge, and push
    mechanical denials when the owner applied it at Setup. In artifact mode do not `git init` the folder;
    keep outputs inside the persistent work target. Never merge,
    push, open a PR, deploy, publish, or mutate an external service unless the owner explicitly
    authorized that exact action. The owner decides what ships in the morning.
  - Understand before inventing: read the product docs, issues, architecture, existing features,
    user-facing flows, and recent history. Write the current promise, audience, strengths, and
    weak spots to product-research.md before selecting work.
  - Research the space when web access is available: find comparable products, competing
    approaches, public user complaints, expectations, and relevant standards. Record dated source
    URLs plus observations in product-research.md. Never send private code, secrets, customer data,
    unpublished plans, or proprietary text to a search service; never copy a competitor's wording,
    assets, or implementation. If browsing is unavailable, say so in the record and continue from
    work-target evidence rather than pretending research happened.
  - Maintain opportunity-map.md. Rank each opportunity by user value, evidence/confidence,
    differentiation, effort, reversibility, and regression risk. Mark it candidate, building,
    shipped, rejected, or parked, with the evidence behind the disposition.
  - Resume before exploring: if opportunity-map.md has a building entry, read its scope,
    acceptance, completed work, decisions, rejected paths, exact next action, and remaining
    verification; continue that opportunity first. Never open a second building opportunity.
  - Each cycle: choose the strongest complete improvement that fits the remaining time. Before
    substantial implementation, make it the single building entry using the shipped structure.
    Small fixes, coherent medium work, and substantial features are all valid. Build end-to-end,
    run the item gate, then commit separately in repository mode or write an artifact receipt under `$NS/receipts/`
    in artifact mode, update the opportunity map, then reassess the product
    before choosing again. Keep the branch buildable after every commit; in artifact mode keep
    outputs reviewable after every receipt.
  - The building entry is the cycle's continuation record. Refresh Current phase, Completed,
    Decisions, Rejected, Next, and Verify remaining after meaningful boundaries — research or
    design concludes, a coherent implementation step lands, a decision closes a path, a commit or
    artifact receipt is written, or verification changes state. Do not rewrite it after every command and do not use the
    snag log as a progress journal.
  - Large is allowed; half-built is not. Start a larger feature only when the problem is supported
    by evidence, it fits the product direction, it has a clean rollback boundary, and it can be
    completed and verified inside the remaining shift. Otherwise leave research, a specification,
    or an isolated prototype and park the production decision.
  - Owner decisions stay owner decisions: park pricing, licensing, branding, privacy/legal policy,
    destructive data migrations, new external services, telemetry, authentication, paid
    dependencies, and architectural commitments. Do not turn an unattended guess into policy.
  - Rotate lenses between cycles: product gaps, observed user-path defects, UX friction, performance,
    contracts between layers, meaningful test gaps, and verified dead code. If the project has a
    UI, walk it live every few cycles through direct interaction with the console open.
  - At every site inspection (the interval in `## Gates`; hourly if none is set), run the project's
    quality tooling in report mode. Treat new findings as evidence for the opportunity map, not as
    a requirement to spend the whole shift polishing lint.
  - Dedupe findings against snag-log.md (ALL seen — fixed and rejected). Park human decisions in
    parking-lot.md and keep working. Log one line per cycle to shift-log.md.
  - Open-ended: the deadline is the ONLY thing that ends this item. An empty cycle means the lens
    was too shallow — research a new user, competitor, subsystem, entry point, or workflow.
  - At quitting time finish the current coherent unit, leave the branch green or the outputs
    reviewable, write a morning
    handoff covering research, opportunities, shipped commits or receipts, parked decisions, and how to review
    or reject the branch or folder. If the current unit must remain unfinished, leave its building entry with
    an exact Next and Verify remaining before the wip commit or artifact receipt and handover, then clock out orderly.
  - Verify: the item gate is green at every commit or artifact receipt; every implemented change traces to evidence in
    product-research.md and a disposition in opportunity-map.md.
```
