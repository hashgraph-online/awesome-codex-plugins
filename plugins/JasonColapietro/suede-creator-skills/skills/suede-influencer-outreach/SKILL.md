---
name: suede-influencer-outreach
description: "Use when asked \"pitch this creator\" or to repair an influencer or B2B creator-program first touch. Suede AI grounds one message in a named audience fact, states real compensation and one ask, fits the published contact route and stops the two-follow-up plan at a positive reply. NOT FOR: affiliate mechanics (use suede-referrals), brand partnerships (use suede-co-marketing), cold B2B email (use suede-cold-email), or journalist pitches (use suede-public-relations)."
metadata:
  display-name: "Suede AI Influencer Outreach Skills"
  version: 1.0.0
---

# Suede AI Influencer Outreach Skills

Write the first message a creator actually answers. One vetted creator, one pitch, a short follow-up plan, and a clean handoff the moment they say yes.

## Compatibility

Any agent with a vetted creator, cited audience evidence and approved compensation details. Current contact-route checks need web access; drafts need no sending or social integration.

## Before Writing

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use it for brand, product, voice, and signer, and only ask for what it does not cover.

Collect these, one question per message, multiple choice where it helps. Skip anything already answered.

1. **B2C or B2B?** Product sold to consumers, or to businesses. This sets the framing and the deliverable types.
2. **What does the brand make, and why would this creator's audience care?** One line.
3. **Who is the creator, on which platform, and what is the fit evidence?** A named post, a series, an audience trait, or a media kit. Fit evidence is input from the user or from your own reading of their work. Never invent it.
4. **What is the offer, with the real number?** Flat fee, commission (rate, attribution window, payout schedule), gifted product or access, or a hybrid. This skill states the offer. It does not set or change it.
5. **Rough deliverable and timing.** One line, enough to sketch.
6. **Which contact does the creator publish?** Business email, DM only, or a manager or agent.
7. **Brand voice and signer.** Formal, peer-casual, or playful. A named person signs.
8. **Which ask can the brand honor this week?** Reply for details, a sample or trial on reply, a short call, or an application link.
9. **Deadline and intent.** Is there a launch date to beat? Is this a one-off, or a relationship worth building?

After the answers, say which answer moved which default below. An existing relationship with the creator or their manager, a brand they already recognize, audience data in hand, or nothing to gift all change the order.

---

## Workflow

1. **Ground the fit.** If you can browse, read the creator's two or three most recent posts and confirm the fit evidence yourself. Otherwise ask for the specific post or audience trait the pitch will cite.
2. **Confirm the recipient.** The contact the creator publishes decides it. See [channel-and-manager.md](references/channel-and-manager.md).
3. **Propose two or three angles** with trade-offs and a recommendation, drawn from the ranked menu in [pitch-anatomy.md](references/pitch-anatomy.md). Wait for the user to pick one.
4. **Draft the first touch** per [pitch-anatomy.md](references/pitch-anatomy.md), fitted to the confirmed channel.
5. **Draft the follow-up plan** per [follow-up-cadence.md](references/follow-up-cadence.md).
6. **Edit pass.** Run `suede-deslop` over the pitch and every follow-up. A pitch that reads like a mail merge gets deleted on sight.
7. **Quality check** (below). Redraft until every item passes.
8. **Present** angle, first touch, follow-up plan, and stop rule, then hand over the package in the Output Format.

See [examples.md](references/examples.md) before writing copy.

---

## Angle Menu

Default order, best value per unit of effort first. Delete any angle that is not true of this creator. Never park a false one at the bottom.

1. **They already use or recommend the brand.** The fit is proven by their own behavior.
2. **Something they launched in the last few weeks.** Strong today, stale in a month.
3. **A specific piece of their content.** The strongest cold angle. Takes an hour of watching or reading.
4. **A product of theirs the brand team actually uses.** Rarely true, strong when it is.
5. **A natural fit with their format.** Answers "what would this look like?"
6. **Audience overlap.** Weakest when asserted. Promote it when backed by real data such as a media kit, shared analytics, or a customer-list match.

---

## The Offer, by Compensation Model

- **Commission:** state rate, attribution window, payout schedule, and a rough per-sale figure in message one. Commission puts the risk on the creator, so vague terms read as a lowball.
- **Flat fee:** name the model and confirm a real budget exists. No rate card.
- **Gifted product or access:** say so plainly. Never imply payment.

---

## B2C and B2B

- **B2C:** state the audience-purchase fit. Deliverables skew to posts, videos, and stories. Gifting and commission are common.
- **B2B:** speak to a business problem the creator's audience has, not a product feature. Deliverables skew to newsletter issues, podcast reads, webinars, and articles. Gifts take B2B shapes: platform access, beta invites, conference passes, hosted events. Free access still counts as a material connection.

---

## Quality Check

Every item resolves to something you can see in the text.

**First touch, all ten:**

- [ ] Opens on one verifiable, creator-specific fact framed as audience fit, not flattery
- [ ] Swap test: putting another creator's name in would force a rewrite
- [ ] Compensation model and real number match what the user gave, exactly
- [ ] Exactly one ask, and the user confirmed the brand can honor it
- [ ] Fitted to the confirmed channel: full structure for email, 2 to 4 sentences and no links for a DM, addressed to the manager when one is listed
- [ ] Zero items from What to Avoid appear, checked term by term
- [ ] B2B states the business need; B2C states the audience-purchase fit
- [ ] No contract terms, exclusivity, or disclosure language
- [ ] A named person signs
- [ ] Reads human aloud, with contractions

**Every follow-up:**

- [ ] One or two sentences, nothing from the first touch restated
- [ ] Carries one new small angle that could not go to any other creator unchanged
- [ ] Low pressure: no guilt, no invented deadline
- [ ] Same single ask or an easier one

Any failed item means rewrite before presenting. Do not hand over a draft with a caveat attached.

---

## Output Format

Deliver the package in this shape, with these field labels verbatim.

```
INFLUENCER PITCH PACKAGE: <creator>, <date>

Chosen angle: [the angle, and why it beat the alternatives]

Recipient: [creator direct / manager name] via [email / DM / platform]

Subject: [email only]

Body: (NN words)
[the message exactly as it would be pasted]

CTA: [the single ask, quoted from the body]

Personalization source: [the specific post, series, or data point the opener traces to,
with enough detail that the user can confirm it is real]

Follow-up plan:
| # | Day | Channel | New angle | Message |
|---|-----|---------|-----------|---------|

Stop rule: positive reply -> stop and hand off; silence after the final touch -> close the file

Handoff notes: compensation as stated, deliverable mentioned, CTA promised
```

`Personalization source:` is required. If you cannot name a real source, you do not have personalization, and the opener has to change.

---

## What to Avoid

- Subject lines like "Collab opportunity with [Brand]!" or "Quick question", and any emoji bait
- Generic salutations: "Dear influencer", "Hi there", "To whom it may concern"
- Fabricated familiarity: "I've been following you for a long time" with nothing specific behind it
- Feature dumps where the audience-fit reason belongs
- "Very competitive compensation" or any offer without the number
- Rate cards, multi-item deliverable lists, or full campaign plans in message one
- "Non-negotiable" or any hardball language
- Contract, exclusivity, or disclosure terms before the creator agrees to talk
- More than one ask
- A team alias instead of a named sender
- "Just checking in", "bumping this", "did you see my email?"

---

## Measurement

Benchmark against your own pitch log. The reply-rate figures that circulate for creator outreach trace to vendor self-reports and broken citations, so do not quote them as fact or set them as targets.

Log every pitch: creator, channel, manager involved, angle, sent date, follow-ups used, outcome, days to reply. Track reply rate, positive-reply rate, days to first reply, and which angles led to signed deals. After a dozen pitches, your own numbers by angle and channel are the benchmark.

---

## References

- [pitch-anatomy.md](references/pitch-anatomy.md): subject lines, opener, offer by model, CTA menu, channel fitting
- [channel-and-manager.md](references/channel-and-manager.md): which contact carries the pitch, and manager etiquette
- [follow-up-cadence.md](references/follow-up-cadence.md): three cadences, follow-up copy rules, stop rules
- [examples.md](references/examples.md): a B2C commission pitch, a B2B flat-fee pitch, a follow-up plan, and an annotated pitch that gets deleted

---

## Boundaries

- Do not invent personalization, familiarity, audience data, results, or prior contact.
- Do not send, DM, schedule, or follow up with anyone without explicit authorization for the exact recipient and message.
- Recommend the listed manager over a direct message unless the creator has asked for direct contact. Going around a manager can end the conversation, so say so once. If the user still chooses direct, write it to the DM rules.
- Do not set, raise, or lower the compensation. State what the user gave.
- Do not put disclosure, contract, or exclusivity terms in the cold pitch. Disclosure obligations (FTC 16 CFR Part 255 in the US, ASA and CMA rules in the UK) attach once a material connection exists; route that work to `suede-referrals`.

## Routing

- Recruiting affiliates across a list, or designing commission and payout rules -> use `suede-referrals`.
- Partnering with another brand -> use `suede-co-marketing`.
- Cold email to business prospects -> use `suede-cold-email`.
- Pitching journalists, or booking yourself as a podcast guest -> use `suede-public-relations`.
- Choosing and vetting which creator to pitch happens before this skill. It starts from a creator the user has already picked.
- Before anything goes to a real recipient -> use `suede-deslop`.
- From those skills, route one-to-one creator and influencer pitches back to `suede-influencer-outreach`.

## Attribution

Adapted from the `influencer-outreach` skill in [mbfinotti/partnerships-skills](https://github.com/mbfinotti/partnerships-skills) by Maya-Beth Finotti, MIT licensed. See `NOTICE.md` at the repo root.

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
