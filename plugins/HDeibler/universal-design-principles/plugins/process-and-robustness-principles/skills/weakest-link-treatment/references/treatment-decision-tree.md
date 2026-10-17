# Weakest-link treatment — decision tree

A decision tree for choosing among the five treatment options.

## Step 1: is the weak link necessary?

**No → Eliminate.**
- Remove the feature, field, or step.
- Verify that no important user is dependent on it.
- Document the decision so it isn't reintroduced later.

**Yes → continue to step 2.**

## Step 2: is the weakness primarily about reliability (it works most of the time but fails sometimes)?

**Yes → continue to step 3 (reliability path).**

**No → continue to step 4 (UX path).**

## Step 3 (reliability path): can you add redundancy?

**Yes (multiple equivalent providers exist, redundancy is justified by criticality) → Replicate.**
- Add a redundant provider with automatic failover.
- Implement circuit breakers and graceful degradation.
- Test the failover path regularly.

**No → continue to step 5 (general fix).**

## Step 4 (UX path): is the user's experience the primary concern?

**Yes, and the fix is achievable in the short term → Fix.**
- Redesign the UI/UX.
- Improve clarity, reduce friction, prevent error.
- Test the fix with users.

**Yes, but the fix is long-term → Buffer + Communicate.**
- Improve the user's experience around the weakness (better error messages, clear recovery paths).
- Communicate honestly about the limitation and the plan to address it.
- Schedule the long-term fix.

**No (something else is the concern) → continue to step 5.**

## Step 5 (general fix): can you fix the weak link directly?

**Yes, with reasonable effort → Fix.**
- Direct improvement.
- Verify with metrics post-deployment.

**Yes, but expensive → balance against alternatives.**
- Could buffering achieve most of the benefit at lower cost?
- Could elimination be reconsidered if the value is lower than estimated?
- Could the fix be incrementalized?

**No (genuinely can't fix in available timeline) → Buffer + Communicate.**
- Reduce the impact of the weakness on users.
- Be transparent about the limitation.
- Plan the eventual fix even if it's far off.

## Combining treatments

Most real situations call for combinations:

**Fix + Communicate.** A long fix, with honest communication during the work.

**Fix + Buffer.** Improve the weak link while also improving the surrounding experience.

**Replicate + Buffer.** Add redundancy and also improve degradation behavior.

**Eliminate + Communicate.** Remove a feature, with clear communication about the change.

**Buffer + Replicate + Fix.** A comprehensive treatment for a critical weak link.

The combinations cost more but are sometimes warranted for high-impact weak links.

## Common decision pitfalls

**Defaulting to "fix" without considering eliminate.** Designers often want to improve things rather than remove them. Sometimes elimination is the right answer.

**Defaulting to "communicate" as a substitute for actual treatment.** Posting a status page or warning isn't a treatment if there's no plan to fix or eliminate.

**Choosing "buffer" because "fix" feels too hard.** Sometimes the fix is hard but justified; buffering accumulates technical and design debt.

**Choosing "replicate" without verifying the redundancy works.** Many "fallback" mechanisms have never actually been used; when needed, they fail.

**Choosing one treatment when combination is needed.** The most-impactful weak links often warrant multiple treatments simultaneously.

## Concrete examples

### A confusing form field

- Necessary? Maybe — let's verify the data is used downstream.
- Data isn't used → eliminate. (Removed the field; signup conversion improves.)

### A flaky third-party service

- Necessary? Yes (it provides core functionality).
- Reliability problem? Yes.
- Can add redundancy? Yes (multiple providers exist).
- Treatment: Replicate (with fallback) + Buffer (cache for graceful degradation).

### A feature with a complex bug

- Necessary? Yes.
- UX problem? Yes — users experience data loss occasionally.
- Fix achievable short-term? No (requires rewrite).
- Treatment: Buffer (warn users, add recovery) + Communicate (transparent about the issue) + Fix (long-term, schedule the rewrite).

### A frequently-failing background job

- Necessary? Yes (it processes user uploads).
- Reliability problem? Yes (intermittent failures).
- Can add redundancy? No (it's a bespoke job; no alternative exists).
- Treatment: Fix (improve error handling, add retries) + Buffer (notify users when their upload didn't process; provide retry path).

### A confusing error message that users don't understand

- Necessary? Yes (the underlying error condition is real).
- UX problem? Yes — users don't know how to recover.
- Fix achievable? Yes (rewrite the message and add recovery path).
- Treatment: Fix.

## Cross-reference

For methods of identifying weak links, see `weakest-link-identification`. For the parent principle, see `weakest-link`.
