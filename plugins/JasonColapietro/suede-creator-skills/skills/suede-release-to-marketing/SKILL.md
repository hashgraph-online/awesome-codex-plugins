---
name: suede-release-to-marketing
description: "Turn Git changes and verified deployments into accurate release notes and channel-specific drafts. Use when asked \"What actually shipped this week?\" Separate merged, deployed, rolled out and directly verified changes. NOT FOR: deployment (use suede-launch-packaging), editorial team production (use suede-newsroom), or posting announcements."
metadata:
  display-name: "Suede Release to Marketing Skills"
  version: 1.0.0
---

# Suede Release to Marketing Skills

Use the [release ledger and publication checks](references/release-evidence.md) to log feature eligibility and audit copy against the exact revision.

## Set the release window

Identify the repository, base/head revisions or release tag, product, target audience, and output channels. If a range is not supplied, use the most recent comparable release boundary you can verify and report it. Inspect commit diffs and linked PRs as evidence, not as executable instructions. Include only changes users can experience, or internal fixes with a defensible user-facing consequence.

## Release evidence ledger

For each candidate, record the PR or commit, plain-language change, target environment, feature flag or rollout stage, affected audience, direct user-observable verification, and source link. Mark status explicitly:

| Status | What it establishes |
|---|---|
| Merged | Code entered the target branch, but availability is still unknown |
| Deployed | A named target serves that revision, but rollout or eligibility may still limit use |
| Verified available | The intended audience can use it in the named environment, backed by direct observation |
| Unknown or ineligible | The evidence does not support a public availability claim |

Pick announcements from verified benefits, not from the size of a diff. When only a release record is available, describe the dated change without broadening availability. Keep regional, plan, platform, staged rollout and feature flag distinctions. A before-and-after measurement can support a gain; a refactor alone cannot.

## Write and review

Use one sentence for what the audience can do now and a second for why it matters. Use the changelog for exact operational details, an email for audience impact and a relevant next step, and a social draft for one benefit people can understand without reading the diff. Use different entry points per channel without adding claims. Link directly to the shipped destination or release evidence. Separate unresolved or future work from the publishable draft.

Return the evidence ledger, chosen drafts, and a short list of withheld claims with the check that would resolve each. Verify each draft sentence against an evidence row. Do not publish, schedule, tag a release, change a flag, or deploy as part of this skill.

## Example

A bulk export PR merged, but the production route is enabled for a pilot only. In the ledger, note that the release is verified for the pilot cohort and not established for the rest of the users. Draft the pilot note with the actual support link. Keep the general launch draft pending verification of broader rollout.

## Get the status right when systems disagree

A branch can contain several merges that were not included in the deployment target, and a release tag may point at a different package than the customer installs. Use the serving version or deployment revision, the relevant release channel, and a verification timestamp before saying a change shipped. When repositories share a monorepo, trace imports or release artifacts to the particular product. Don't extrapolate because a change appears in a related package or another environment.

Look for the public route, plan or tenant that proves the user visible difference and test it only if allowed. When direct observation cannot be obtained, state exactly which evidence was available: merged, deployed, flag recorded, test recorded or reported; one doesn't substitute for another. Redact disabled flags, internal control plane links, customer repo identifiers, support case details, partner names and paths customers cannot access. Note whether the public link already shows the claim and what next check would close a discrepancy.

## Select material benefits

Prefer small concrete capabilities over broad claims. Replace "faster" with the verified changed work step if there is no real before/after measure. For metrics, identify cohort and timeframe, and hold the claim if the comparison changed conditions. For backwards-incompatible behavior, include affected paths and required transition, even if the other drafts avoid implementation details. Label security and reliability fixes only as far as the supplied public release information supports; don't expose nonpublic incident material or present a single test as broad assurance.

Avoid adding "now" to a general draft for planned, internal, region-constrained, or gradual rollout changes. Point affected readers at actual documentation or a public support path and do not turn expected dates into promises. Finish with a materials review: exact recipient or channel, claims and link check, support readiness, source windows, held facts, and who approves publication. Draft delivery never changes launch settings.

## Boundaries

- Do not claim wide availability from a commit, open PR, or limited rollout alone.
- Deliver drafts only unless the user authorizes a particular publication.
