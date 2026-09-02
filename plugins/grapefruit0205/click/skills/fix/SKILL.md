---
name: fix
description: When explicitly invoked with a software defect or unwanted behavior, translate the natural-language report and repository evidence into one compact repair contract, explain it plainly, then fix it in one approved shot. Never invoke implicitly.
---

# Fix

Use `$fix` only when the user explicitly selects it. Do not infer activation from words such as “bug,” “broken,” or “fix,” and do not promise a native `/fix` command. `$fix` intentionally selects Click's Guarded repair workflow. Read Click's [operating modes](../click/references/modes.md) for the exact arm, bypass, cancel, and resume rules.

Trace the reported symptom to the narrowest owning behavior, relevant state, public contract, and focused evidence. Keep confirmed repository evidence separate from hypotheses. Resolve ordinary repair tactics yourself and expose only consequential assumptions in the contract instead of asking serial implementation questions.

Use Click's shared [contract format and approval lifecycle](../click/references/directive-format.md) and [verification profiles](../click/references/verification-profiles.md). Stage the repair JSON once, keep `plain_language` digest-bound, capture its `contract_id` from `CLICK_CONTRACT_ID`, and present the exact Hook-generated Goal, Changes, Unchanged, and Completion checks projection without independently summarizing it. Keep JSON as optional Technical contract details, ask once, and stop without editing. Only after explicit approval in a later user turn, pass that id—never resend the JSON.

Then follow the shared [anti-loop policy](../click/references/anti-loop-policy.md) and [structured capability protocol](../click/references/capability-protocol.md). Repair continuously inside the approved semantic boundary, collect each assigned completion source once on the final relevant revision, and stop when the repair is proven. Pause only for missing authority, an uncovered irreversible or paid action, or a required change to the approved semantic contract.
