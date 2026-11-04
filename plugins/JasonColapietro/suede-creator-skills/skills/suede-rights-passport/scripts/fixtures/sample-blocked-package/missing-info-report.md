
# Missing Info Report

Private draft: unresolved rights and creator questions may be sensitive. Review
before sharing.

## Summary

Missing information must be resolved before Suede can confidently register, license, route royalties for, or expose the work to agent commerce.

## Questions

| Severity | Field | Question | Blocks |
| --- | --- | --- | --- |
| high | `rights.owner_claim` | Who owns the master and publishing rights? | registry, licensing, royalty-routing, agent-commerce |
| high | `credits.contributors` | Who contributed to the work, what were their roles, and are splits confirmed? | royalty-routing, licensing |
| high | `rights.sample_clearance_status` | Are all samples, loops, interpolations, or third-party beats cleared? | licensing, registry |
| medium | `project.release_status` | Has the work already been released, registered, minted, licensed, or sold? | registry, licensing, catalog-discovery |

## Risk Flags

| Severity | Label | Detail | Action |
| --- | --- | --- | --- |
| high | ownership-unconfirmed | Owner claim has not been confirmed by the creator. | Confirm master and publishing ownership before registry, licensing, or royalty routing. |
| high | contributors-unconfirmed | Contributor list and splits are not confirmed. | Collect contributor roles and split confirmations. |
| high | sample-clearance-unconfirmed | Samples or third-party material are indicated, but clearance is not confirmed. | Collect clearance records or remove uncleared material before licensing. |
| medium | stems-not-found | No stems were detected. | Ask whether stems exist or use Suede stem preparation during optimization. |

## Status

Not ready for final Suede intake until high-severity questions are answered.
