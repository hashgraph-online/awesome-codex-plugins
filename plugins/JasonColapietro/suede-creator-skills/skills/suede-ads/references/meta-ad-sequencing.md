# Meta Ad Sequencing

Use when planning a Meta campaign as an ordered path of ads instead of one
winning ad. Linked from the "Meta in the Andromeda era" section of SKILL.md.

## Plan the path, not one winner

Meta's ranking model reads a person's activity as an ordered timeline of ad
clicks, conversions, and organic engagement (Meta Engineering's posts on its GEM
ads model, November 2025 and October 2026). In practice the second ad someone
sees is judged against the first. So ask what ad 2 says to a person who already
saw ad 1, instead of testing every ad in isolation.

Explicit sequencing in auction campaigns rolled out account by account in early
2026. The setup is narrow, so confirm it in Meta's current help docs before
planning around it:

- Objective: Awareness (Maximize reach) or Engagement (ThruPlay). Sales and
  Leads objectives do not offer it.
- Frequency control set to **Target frequency**, not the default cap.
- **Lifetime budget** at the ad set level, at least 7 days, with Advantage
  campaign budget off.
- At least two ads published in the ad set.

**Fit the sequence to the flight.** Campaign length and the frequency window
cap how many ads fit: a 3-week flight showing one ad every 7 days holds three.
Two or three ads is the usual range, since longer paths shed people.

A typical path runs hook, then problem, then proof (testimonial or case study),
then offer. Each ad assumes the last one landed, so ad 3 does not re-explain the
product.

Target frequency usually costs more per impression than standard delivery.
Judge a sequence on downstream conversions, ideally against a holdout, not on
CPM. On conversion objectives, where sequencing is unavailable, approximate the
path with engagement retargeting: viewers or engagers of the hook ad get the
proof ad, then the offer. Do not quote a conversion multiplier for sequencing
unless the account has measured one.

Sources: sequencing framing from Cody Schneider (October 2026); setup
requirements from Jon Loomer's testing and Meta's documentation as of early 2026.
