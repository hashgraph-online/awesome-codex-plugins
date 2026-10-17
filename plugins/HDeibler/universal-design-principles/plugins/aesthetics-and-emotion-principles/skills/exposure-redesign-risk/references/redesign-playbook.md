# Redesign playbook

A step-by-step playbook for executing major redesigns while managing exposure-effect risks.

## Phase 1: justify

**Articulate the user benefit.** What specific user problems does the redesign solve? Be concrete. "Modernize the visual design" isn't a user benefit; "make it easier for users to find X" is.

**Quantify if possible.** If the redesign improves measurable outcomes (task completion rate, time-to-value, user satisfaction), articulate the targets.

**Compare against the cost.** The cost includes: the engineering work, the user transition cost, the risk of backlash, the risk of churn. Is the user benefit large enough to justify all of this?

**Get sign-off from key stakeholders.** Including support (who will field user complaints), marketing (who will communicate the change), and leadership (who will hear the complaints).

If the justification isn't strong, reconsider. Many proposed redesigns aren't actually worth the cost.

## Phase 2: design

**Design with the existing user in mind.** Power users have specific workflows they depend on. The new design should serve those workflows, even if it changes how they look.

**Map the changes.** For each change, identify: what users currently do, how the new design changes that, what users will need to learn or unlearn.

**Identify the riskiest changes.** Some changes will trigger more backlash than others. The riskiest changes should be the most justified.

**Plan for migration.** For each change, what's the migration path? Documentation, in-product hints, support resources.

**Test with users.** Before shipping, test the new design with representative users. Both new users (who'll see only the new design) and existing users (who have built-up familiarity).

## Phase 3: communicate (pre-launch)

**Announce in advance.** 30–90 days before launch, depending on scale.

**Multiple channels.** Blog post, email to active users, in-product banner, social media. Different users encounter different channels.

**Be specific about what's changing.** Don't be vague about "improvements." Tell users specifically what will look or work differently.

**Explain the why.** Users tolerate change better when they understand the reasoning. Even users who disagree with the reasoning appreciate that it exists.

**Acknowledge the costs.** "We know change is hard. Here's how we're trying to make it easier." Recognition of user investment in the existing design builds goodwill.

**Open feedback channels.** Make it easy for users to share concerns or questions. Listen and respond.

## Phase 4: gradual rollout

**Start with a small percentage.** 1–10% of users. Watch for issues you didn't anticipate.

**Measure during rollout.** Are users completing tasks? Are they happy? Are support tickets spiking?

**Adjust based on what you learn.** Sometimes rollout reveals issues that need fixing before broader release.

**Increase percentage over time.** 5% → 25% → 50% → 100% over weeks or months.

**Allow users to opt out (where feasible).** A "use old layout" option gives users control during the transition. Plan to remove the option eventually but during transition, it reduces backlash.

## Phase 5: support during transition

**Documentation.** Detailed migration guides for major workflows. "If you used to do X, you now do Y."

**Video tutorials.** Some users learn better from video than text. Both are useful.

**In-product help.** Tooltips, banners, walkthroughs that show users the new patterns.

**Customer support readiness.** Brief support team on the changes; provide them with quick-answers; expect ticket volume to spike.

**Active feedback collection.** Ask users how the transition is going. Use the feedback to refine.

**Transparent fix process.** When users report bugs or unintended consequences, fix them quickly and visibly. Demonstrating responsiveness rebuilds trust.

## Phase 6: post-launch monitoring

**Track key metrics.** User satisfaction, task completion, support ticket volume, churn rate. Compare to pre-launch baselines.

**Listen to ongoing feedback.** Some issues only surface after broader use. Continue collecting feedback for months.

**Plan for follow-up improvements.** No first ship is perfect. Schedule fast-follow improvements based on feedback.

## Phase 7: long-term integration

**Remove transitional fallbacks.** After enough time (3–6 months typically), remove "use old layout" options. The transition period ends.

**Update documentation, marketing, training.** Old screenshots and references should be updated to reflect the new design.

**Capture lessons.** Document what went well and what didn't. Use the learnings for future redesigns.

## Variants for different change sizes

**Small change.** Phases 2 and 7 may be all you need. Communicate briefly; no extensive rollout or transition support needed.

**Medium change.** Skip the gradual rollout if confidence is high. Communicate; ship; support; refine.

**Large change.** Use the full playbook. Don't skip phases.

**Radical change.** Use the full playbook plus: longer transition periods, more communication, more transition support, possibly an extended dual-layout period.

## Anti-patterns

**Skipping the justification phase.** Redesigns that aren't actually justified by user benefit. The team finds out the hard way that change-for-change's-sake doesn't pay back.

**Shipping with no advance communication.** Surprise redesigns trigger maximum backlash.

**Big-bang releases without gradual rollout.** Issues that affect all users at once produce coordinated backlash.

**Ignoring early feedback.** Backlash that gets worse over time often started with early signals that were dismissed.

**Removing the transitional fallback too quickly.** Users still adapting need the option to revert; removing it before they're ready triggers a second wave of backlash.

**Persisting with a redesign users genuinely hate.** Some redesigns are bad. Sometimes the right call is to revert or significantly modify. Distinguish "users resisting change" (will subside) from "users hating the new design" (won't subside).

## A timeline template for major redesigns

- **T-90 days:** justification finalized; communication plan drafted.
- **T-60 days:** initial announcement to users; design finalized.
- **T-30 days:** detailed announcements; migration content published.
- **T-7 days:** final reminder; support team briefed.
- **T-0:** rollout begins (5% of users).
- **T+7 days:** rollout to 25% if metrics look healthy.
- **T+14 days:** rollout to 50%.
- **T+30 days:** rollout to 100%.
- **T+30 to T+180:** transition support active; "old layout" option available.
- **T+180:** transition support reduced; "old layout" option removed.

This is a starting template; calibrate to your product and audience.

## Cross-reference

For onboarding-related exposure design, see `exposure-onboarding`. For the parent principle, see `exposure-effect`.
