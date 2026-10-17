---
name: scaling-interaction-assumptions
description: 'Verify and design for user-base scaling — broader audiences, more diverse use cases, more edge cases, behaviors that weren''t anticipated. Use when launching to a new market, scaling from beta to GA, expanding from one team to a company, or any context where the user population is growing or changing. Interaction scaling is often harder than load scaling because it surfaces design assumptions that worked for the original audience but fail for a broader one.'
---

# Scaling — interaction assumptions

The second kind of scaling fallacy: assumptions about how users will behave, what use cases they'll have, what they'll consider acceptable. A design that works for 100 early users — who tend to be sophisticated, motivated, and tolerant of rough edges — frequently fails for 100,000 broad-audience users who lack those qualities.

Interaction scaling is often harder than load scaling because it requires anticipating how a broader, more diverse audience will use the product. Engineers can load-test infrastructure; product designers have to imagine future users.

## Common interaction-scaling failures

**Original audience assumptions don't transfer.** A productivity tool designed for engineers expects technical sophistication; when adopted by non-technical professionals, the assumptions fail.

**Edge cases become common.** A 1-in-1000 case happens 100 times a day at a million users. Designs that assumed "this won't happen often" find that it does.

**Feature discovery breaks down.** Features that were discoverable when the product had 5 of them become invisible when the product has 50. Users miss capabilities or use them wrong.

**Onboarding doesn't scale.** A hands-on onboarding (calling each user, showing them around) works for hundreds; doesn't work for hundreds of thousands.

**Support model doesn't scale.** Founders answering every support email is fine at 10 users; impossible at 10,000.

**Moderation doesn't scale.** Manual content moderation works for small communities; impossible for large ones. Algorithmic moderation has its own issues.

**Cultural and linguistic assumptions don't transfer.** A product designed for one country has assumptions (language, units, formats, cultural conventions) that fail in others.

**Accessibility gaps surface.** A product that "works for our team" may have accessibility gaps that affect the broader audience disproportionately.

**Naming conventions don't scale.** Personal names, address formats, ID systems vary widely; designs based on one convention fail for others.

**Power-user features intimidate novices.** Capabilities that are useful for sophisticated users overwhelm casual users.

## Designing for interaction scale

**Anticipate diversity.** Imagine the full range of users you'll have, not just your current users. New audiences, languages, abilities, technical skill levels.

**Design for the long tail.** Edge cases at scale become routine cases. Test with weird names, unusual addresses, unexpected workflows.

**Build for self-service.** Users who can solve problems themselves don't need support. Documentation, error messages with recovery paths, contextual help.

**Plan for moderation at scale.** What happens when bad-faith users find your product? Spam filtering, abuse reporting, automated detection.

**Internationalize early.** Adding internationalization (translation, locale formatting, right-to-left layouts) after launch is much harder than designing for it from the start.

**Plan for accessibility from the start.** Accessibility built in from the start is cheap; bolted on later is expensive and incomplete.

**Calibrate features to scale.** Features that are appropriate at one scale may be inappropriate at another. Manual review, hand-curation, personal touch — all need to evolve.

**Design for varying technical sophistication.** Unless your audience is uniformly sophisticated, design layers that accommodate different skill levels.

## Worked examples

### A productivity tool designed for engineers

A team builds a document-editing tool initially used by engineers. Heavy use of keyboard shortcuts, technical terminology, and assumed comfort with markdown. Engineers love it.

The product expands to non-technical professionals. They struggle: keyboard shortcuts they don't know exist; terms like "fork" and "branch" mean nothing; markdown is foreign.

The fix: layered control. Engineers keep their keyboard-shortcut workflow; non-technical users get a WYSIWYG mode with simpler vocabulary. Both audiences served.

The lesson: original-audience assumptions need to be questioned as the audience broadens.

### A name field that breaks for international users

A signup form has First Name and Last Name fields, each capped at 30 characters. Works for most US users. Fails for users with long names, multi-component names (Spanish, Korean naming conventions), single-name users (Indonesian convention), users with name characters outside ASCII.

The fix: a single "Full Name" field with generous character limit and Unicode support. Don't impose name structure assumptions.

The lesson: cultural assumptions baked into forms surface as the audience diversifies.

### Manual moderation that doesn't scale

A community platform's founders moderate every post personally for the first year. Quality stays high. As the platform grows past 10,000 users, manual moderation becomes impossible. They try to hire moderators; quality drops; bad-faith content slips through.

The fix: combination of automated detection (machine learning), community moderation (trusted users), and reactive moderation (report-and-review). The previous "manual everything" approach can't scale.

The lesson: processes that depend on human attention per item don't scale; design for scale by automating, distributing, or eliminating.

### A help center that doesn't scale

A startup answers every support email personally, with detailed explanations. Users love the personal touch. As the startup grows, the founders can't keep up; response times balloon to weeks.

The fix: build a help center with searchable articles covering the most-common questions; in-product help that answers questions contextually; automated chatbots for common queries; human support reserved for complex cases.

The lesson: personal touch doesn't scale; self-service does.

### A feature set that overwhelms new users

A product that started with 5 features now has 50. Original users learned the product gradually as features were added; new users see all 50 at once and don't know where to start.

The fix: progressive disclosure (hide advanced features behind "more"); guided onboarding (introduce features one at a time); contextual feature discovery (show users features as they become relevant).

The lesson: the cumulative complexity of growing products needs active management; just adding features creates an unscalable surface.

### A pricing tier that doesn't scale to enterprise

A SaaS product's free tier has no real limits. Individual users use modest resources. An enterprise customer signs up under the free tier and uses 1000x the resources of an individual; the company loses money on them.

The fix: tier-based usage limits that scale with company size; enterprise pricing that reflects actual cost to serve; required contract for usage above thresholds.

The lesson: pricing based on assumptions about user size doesn't scale when user sizes vary widely.

## Anti-patterns

**"Our users are all like us."** Designers assuming the user base looks like themselves. The actual user base is more diverse than the design team.

**Assuming current users predict future users.** Early adopters are a particular kind of person; broad adoption brings different kinds of people.

**Building for the median user only.** The median experience may be fine; the experience for users at the edges (high usage, low usage, unusual workflows, accessibility needs) may be broken.

**Deferring internationalization.** Internationalization is much cheaper to design in from the start than to retrofit after.

**Deferring accessibility.** Same as internationalization — cheaper from the start.

**Manual processes that depend on the team's attention.** Moderation, support, onboarding — all break when scale exceeds team capacity.

**Hand-curation that isn't sustainable.** Editorial models, personal recommendations, custom configurations — all need automation strategies for scale.

## Heuristic checklist

When designing for interaction scale, ask: **What audience am I targeting at scale, vs. now?** If different, design for the future audience too. **What edge cases will become common?** Test the rare cases; they happen frequently at scale. **What assumptions about users have I made that may not survive scale?** List them; verify each. **What processes depend on team attention?** They won't scale; design alternatives. **What's our internationalization and accessibility story?** Both need to be designed in, not bolted on.

## Related sub-skills

- `scaling-fallacy` — parent principle on scale-related assumption failures.
- `scaling-load-assumptions` — sibling skill on load and capacity scaling.
- `weakest-link` — at scale, weak design choices surface.
- `mental-model` — broader audiences bring different mental models.
- `accessibility` — accessibility issues become disproportionately impactful at scale.
- `progressive-disclosure` — depth managed for growing feature sets.

## See also

- `references/audience-scale-checklist.md` — practical checklist for evaluating interaction scaling.
