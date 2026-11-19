# Prompts

Focused requests for the agent. `abliterate prompt TOPIC` prints one; `abliterate review --since BRANCH` prints the review prompt with the base filled in.

### review — Before the push

Use the abliterate-review skill. If the skill is missing, read it with `abliterate skill` or use `npx -y abliterate@latest skill` when registry access is available. Review what this branch would push against {base}, then separately what is staged and what is only on disk. Run the engine for evidence when available, trace each lead in source, and report demonstrated regressions in order of impact. Include the evidence still needed and the test that would catch each regression. Check dependencies the change added and earlier fixes for similar code. Return the review in chat and leave files unchanged.

### design — Before writing the code

Use the abliterate-review skill in design mode. For the proposed feature identify actor, resource, action and trust boundary. Write up to three rules as "given … when … then …", say where each is enforced and how to test it with one allowed and one excluded actor. If behaviour depends on an open decision, present it with an example of its consequence.

### access — Authorization and isolation

Use the abliterate-review skill. Rebuild the actor × action × resource matrix from the policy actually applied. Follow identity from the entry point to the query or job. Include legitimate collaborators on shared resources. Read the authorization check for one allowed and one excluded actor. Propose assertions for the allowed result and for unchanged state after a denied write.

### inputs — From input to point of use

Use the abliterate-review skill. Follow each field whose path changed, even if it existed before. Inspect how the final consumer handles it, for example through bound query parameters, renderer escaping, explicit field selection or an argument list. Cite the line that handles the value and propose test cases for a surname with an apostrophe and a disallowed type where relevant.

### privacy — Exposed data and secrets

Use the abliterate-review skill. Compare what the contract allows with what reaches responses, caches, logs and error messages. A field hidden by the UI can still be in the response. When private data leaves its boundary, cite the selection point and propose a test on the actual content with synthetic values. Never print or try secrets.

### state — Transitions, caches and jobs

Use the abliterate-review skill. Pick a changed transition and the condition that must hold between authorization and effect: a revoked permission, the tenant in a cache key, a repeated request. Check atomicity, invalidation or propagated identity where relevant. Propose a deterministic test with fixtures, without load or traffic against a service.

### delivery — Dependencies and CI

Use the abliterate-review skill. Run `abliterate deps --changed` and review workflow changes. For each new or bumped dependency, confirm only advisories whose vulnerable function the code reaches. For CI, follow what runs, from where, with which permissions and with which untrusted input. Do not install packages to test them and do not attribute a CVE without an applicable advisory.

### variants — Siblings of known bugs

Use the abliterate-variants skill. Starting from {seed}, find code that repeats the vulnerable pattern without the guard the fix introduced. Separate introduced from pre-existing, confirm reachability, and propose one regression test per confirmed variant.

### fix — Correction and regression proof

Use the abliterate-review skill in fix mode, only for the identified finding. Write an isolated test that fails because of the broken rule and note the failure before patching. Fix at the point that governs the operation. Re-run the denied case and one allowed case, checking stored state and output. Report what failed before, what passes after and what remains unverified. Do not revert or stage other changes.
