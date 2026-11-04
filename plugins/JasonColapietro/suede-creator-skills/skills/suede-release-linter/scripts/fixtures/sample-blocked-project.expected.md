# Release Lint Report

Private draft: review and redact before publishing, committing, or sharing
outside the intended Suede intake workflow.

## Summary

- Project: unknown
- Artist: unknown
- Source: sample-blocked-project
- Metadata source: metadata.json
- Score: 0
- Status: blocked

## Severity Counts

| Severity | Count |
| --- | ---: |
| Error | 7 |
| Warning | 11 |
| Info | 3 |

## Findings

| Severity | Category | Code | Message | Fix |
| --- | --- | --- | --- | --- |
| error | metadata | `missing-title` | Title is missing. | Add the official public title. |
| error | metadata | `missing-artist` | Artist or creator name is missing. | Add the official artist or creator name. |
| warning | metadata | `missing-release-date` | Release date is missing. | Add release date metadata. |
| warning | metadata | `missing-genre` | Genre is missing. | Add genre metadata. |
| warning | metadata | `missing-language` | Language is missing. | Add language metadata. |
| warning | metadata | `missing-description` | Description is missing. | Add description metadata. |
| warning | metadata | `missing-explicit-status` | Explicit-content status is missing. | Add explicit true/false status. |
| error | media | `missing-primary-media` | No primary audio or video file was found. | Add or identify the final master or primary media file. |
| warning | artwork | `missing-artwork` | No artwork image was found. | Add release artwork before public distribution or catalog publication. |
| info | lyrics | `missing-lyrics` | No lyric or timed-text file was found. | Add lyrics or timed lyrics if the release uses vocals. |
| warning | stems | `missing-stems` | No stems were found. | Add stems or plan stem separation for remix, sync, licensing, or Suede optimization. |
| error | splits | `invalid-master-split-total` | Master splits add to 80, not 100. | Correct master split percentages. |
| error | splits | `invalid-publishing-split-total` | Publishing splits add to 110, not 100. | Correct publishing split percentages. |
| warning | credits | `contributors-unconfirmed` | One or more contributors lack confirmation. | Collect contributor confirmations before royalty routing or licensing. |
| error | rights | `ownership-unconfirmed` | Ownership claim is missing or unconfirmed. | Confirm master and publishing ownership. |
| error | rights | `sample-clearance-missing` | Samples, covers, interpolations, or third-party material are indicated but clearance is not confirmed. | Provide clearance details or remove uncleared material before licensing. |
| warning | rights | `release-history-unknown` | Prior release, registration, minting, or licensing history is unknown. | Confirm whether the work has already been distributed, registered, minted, licensed, or sold. |
| info | rights | `ai-involvement-unstated` | AI involvement is not stated. | State whether generative AI was used for vocals, instrumentation, composition, lyrics, artwork, or post-production (use "none" if not); distributors increasingly require this at delivery. |
| warning | suede | `missing-wallet-or-payment-destination` | No creator wallet or payment destination was provided. | Add a public wallet or payment-routing note if Suede royalty routing or agent commerce is intended. |
| warning | suede | `missing-provenance-notes` | No provenance or creation-history notes were provided. | Add creation history, source notes, or chain-of-custody details. |
| info | suede | `rights-passport-candidate` | Project can be prepared with a Suede Rights Passport after blockers are resolved. | Use suede-rights-passport once error findings are fixed or clearly documented. |

## Asset Inventory

| Category | Count |
| --- | ---: |
| audio | 0 |
| video | 0 |
| artwork | 0 |
| lyrics | 0 |
| stem | 0 |
| document | 2 |
| other | 0 |

## Suede Readiness

Blocked until error findings are resolved.

## Recommended Next Action

Fix error findings before preparing a Suede Rights Passport, registering rights, licensing, or routing royalties.
