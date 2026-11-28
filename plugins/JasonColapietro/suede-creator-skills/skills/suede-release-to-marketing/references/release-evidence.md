# Release ledger and publication checks

| Claim ID | Version and target | Audience and rollout | Evidence and check UTC | What wording is supported? | What stays withheld? |
|---|---|---|---|---|---|
| R01 example | Web 3.14.1 production | Pilot tenant list only | Exact ship revision and pilot path verified | Pilot users can include archived records in exports | All customers can use bulk export |
| R02 example | Desktop branch merged | No release artifact verified | PR merge and a staging test | Change is merged; release not confirmed | Download includes fix |
| R03 example | Mobile 5.1 live | Android initially; iOS pending | Verified Android rollout and docs | Available on Android for eligible devices | Available on all platforms |

Before sharing a draft, review source evidence against each externally visible statement, including titles, image text, link preview text, dates and captions. Check that metric methods are compatible, destinations are public, material restrictions are visible, and a planned entry is not formatted as currently available. A withdrawn or reverted change requires the ledger to identify stale drafts and public assets without editing or contacting anyone automatically.

**Negative fixture:** Revert merges after the release job but before the public announcement. Check the deployed revision or serving artifact before changing public copy. If neither is visible, hold the claim instead of guessing whether the revert shipped.
