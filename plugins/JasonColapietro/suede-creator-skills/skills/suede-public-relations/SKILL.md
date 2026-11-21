---
name: suede-public-relations
description: "Build earned-media angles, sourced media lists, journalist and podcast pitches, reporter replies, and press kits with consistent entity facts. Use when asked to \"draft a journalist pitch\", assess newsjacking, or prepare third-party coverage for search and AI citations. Returns review-ready drafts and measurement steps. NOT FOR: directory submissions (use suede-directory-submissions), release packaging (use suede-launch-packaging), social posts (use suede-social), or sending without approval."
metadata:
  display-name: "Suede AI Public Relations Skills"
  version: 2.0.0
---

# Suede AI Public Relations Skills

## Compatibility

Drafts from supplied evidence; live journalist, outlet, request, and policy checks need web access. Email and media-database integrations are optional and separately authorized.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

Suede AI Public Relations turns verified milestones, evidence, and timely angles
into respectful earned-media briefs for journalists, podcasts, and newsletters.
Coverage now does two jobs: it reaches readers, and it becomes the third-party
evidence search engines and AI assistants cite when buyers ask about the
category. This skill optimizes story fit and source usefulness without treating
a drafted pitch as sent or coverage as earned.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

---

## Core Philosophy

PR is not a substitute for distribution. Treat it as a channel hypothesis whose
value must be measured against the current audience, story, and sales motion.

- **Do not assume a placement drives or cannot drive conversion.** Track referral
  behavior, brand search, citations, and sales influence for this campaign.
- **Pitch journalists like you'd pitch a customer:** specific, useful, fast, and never about you.
- **The story is not your product. The story is the trend, the data, the conflict, or the human.** Your product is the evidence.
- **Test speed against relevance and accuracy.** Use the story's observed
  coverage curve and deadline; never trade verification for haste.

### When PR is worth it

- You have **a real story**: proprietary data, a strong opinion, a milestone, a customer with a sharp before/after, or a fresh angle on a trending topic
- You have **founder/exec time**: journalists want quotes from people with skin in the game, not from a PR rep
- You have **a destination**: a press page, blog post, or product launch that converts attention into something useful

### When to skip PR (for now)

- Pre-launch with no story beyond "we exist"
- No one on the team can sustain the approved, measured test window
- You don't have a clear ICP: journalists ask "who reads my piece because of this?" and if you can't answer, neither can they

---

## The PR Mix

Four possible modes. Select only those supported by the story, audience,
capacity, and current source access.

| Mode | What it is | Effort | Speed to coverage |
|------|------------|--------|-------------------|
| **Reactive (newsjacking)** | Inject your POV into trending news | Low–medium | Hours to days |
| **Proactive (pitching)** | Build a media list, draft original-story pitches | Measure current capacity | Set from story flow and response data |
| **Inbound (press requests)** | Respond to journalist queries on HARO/Qwoted/Featured | Low | Days to weeks |
| **Owned (press page + media kit)** | Make it easy for journalists to find you | One-time setup | N/A |

**For the reactive newsjacking workflow**: see [references/newsjacking.md](references/newsjacking.md)

**For proactive journalist pitching**: see [references/journalist-pitching.md](references/journalist-pitching.md)

**For inbound press-request platforms (HARO, Qwoted, etc.)**: see [references/press-platforms.md](references/press-platforms.md)

**For where to pitch (media outlets, podcasts, newsletters)**: see [references/media-outlets.md](references/media-outlets.md). For startup/SaaS/AI directories, use the separate `suede-directory-submissions` skill: different intent, different list.

---

## PR as Citation and Entity Building

AI assistants answer category questions mostly from third-party sources. Muck Rack's Generative Pulse study (May 2026, more than 25 million links cited by ChatGPT, Claude, and Gemini) classified about 84% of cited links as earned media rather than brand-owned or paid content, found about 27% were journalism, and found 57% of dated journalism citations were less than a year old. Source: [Muck Rack, What Is AI Reading? (May 2026)](https://media.muckrack.com/documents/What_Is_AI_Reading__May_2026.pdf). Treat the exact shares as one vendor's measurement; the direction is consistent across its reports.

What that changes:

- **Pick outlets AI tools already cite for your category.** Before building the list, ask the main assistants the buyer's top category questions and note which publications, newsletters, and review sites they cite. Those outlets move up a tier.
- **Make every placement quotable.** Original data, a clear named spokesperson, the exact company and product names, and one sentence that defines what you do. Ask for the company name to be spelled the same way it appears on your site.
- **Keep the entity consistent.** Company name, founder name and title, one-line description, founding date, and headquarters should match across the press page, the site's Organization and Person schema (with sameAs links to the same profiles), directories, and every pitch. Mismatches split credit between versions of you.
- **Refresh matters.** Citations skew to recent coverage, so a steady cadence of smaller, accurate placements beats one big hit per year.
- **Close the loop.** Track AI citations on a fixed question set before and after a campaign, alongside brand search and referral visits.

On-site fixes (extractable answers, schema, AI-bot access) go to `suede-ai-seo` and `suede-seo-audit`. Suede AI's SEO, AEO, and GEO services (https://suedeai.agency) run earned media and AI visibility as one program when the user wants it done for them.

---

## Owned: Press Page + Media Kit

Build this when verified newsroom assets and a maintained press contact would
reduce friction for the current media motion; measure usage rather than assuming
ROI.

**Press page (`/press` or `/newsroom`) should include:**
- One-paragraph company description (copy/paste ready)
- Founder bios with headshots (high-res, downloadable)
- Logo pack (SVG + PNG, light + dark, with usage guidelines)
- Product screenshots (high-res)
- Recent coverage list (social proof for the next journalist)
- Founding date, employee count, funding (if disclosed)
- A current press contact path in the format the intended outlets accept
- Recent press releases / announcements
- The same entity facts used in Organization and Person schema on the site, with links to the official social and directory profiles

State a response expectation only if the team has approved and staffed it. Use
the team's real service level rather than a universal 24-hour promise.

---

## Quick Reference: Pitch Quality Bar

Before presenting any draft for send approval, resolve these checks:

- [ ] Does a bounded recent sample show that this journalist covers the beat?
- [ ] Is there a clear news hook: something that just happened or is about to?
- [ ] Could this journalist write a complete story from this email alone? (Data, quotes, customer name, contact.)
- [ ] Is the subject line specific enough to predict the article's headline?
- [ ] Is the pitch within the outlet's published word or character limit, or,
      if the outlet publishes none, under 200 words unless the user set another limit?
- [ ] Are the company name, product name, and spokesperson title spelled exactly as on the site and press page?
- [ ] Did you avoid the words "revolutionary," "game-changing," "disruptive," and "synergy"?
- [ ] Is the ask clear? (Interview? Embargo? Exclusive? Quote?)

**Pass rule:** any unchecked box blocks the draft from being presented for send
approval. Fix it or, if it cannot be resolved (for example, no recent sample is
available to confirm the beat), name the box as unresolved in the handover below
rather than checking it.

### Send-approval handover (the one gate in this skill)

Every workflow in this skill and its references ends here. Contacting a
journalist is unrecallable, so nothing leaves as a draft-plus-send. At the
handover:

1. **Stop.** The work is complete; the output is a draft and nothing has been sent.
2. **Name the four variables, one line each:** recipient (person and outlet),
   channel (email, platform form, DM), visible sending identity, and the exact
   message to be sent.
3. **State cost and timing** if either applies (platform fee, embargo time).
4. **Offer three options:** approve as written / revise (name what changes) / drop.
5. **Wait for the user's explicit pick.** Approval for one recipient never
   transfers to another, and any edit to the message re-opens this gate.

---

## Measurement

What to track:

| Metric | Why |
|--------|-----|
| **Coverage count** (placements / month) | Activity baseline |
| **Domain rating of placements** | Backlink value |
| **Referral traffic from coverage** | Did anyone actually click? |
| **Brand search lift** | Did people search you after reading? |
| **AI citation share** on a fixed question set (Google AI Overviews and AI Mode, ChatGPT, Claude, Perplexity) | Whether coverage turned into answers buyers see |
| **Sales conversations citing the article** | One revenue-influence signal to reconcile with attribution limits |

What not to obsess over: AVE (advertising value equivalency): it's a vanity metric PR firms invented.

---

## Common Workflows

### "Help me newsjack [trending story]"
Go to [newsjacking.md](references/newsjacking.md), run the scoring rubric, draft
a bounded set of evidence-backed angles, and return a recommended draft for
review. Do not pitch or publish.

### "Find journalists who cover [beat]"
Go to [journalist-pitching.md](references/journalist-pitching.md), use the
discovery checklist, and first discover whether an authorized browser or
research connector is callable. If not, work from user-supplied article URLs,
exports, or a manual research worksheet. Build a sourced, scored list without
claiming any profile or article was reviewed unless it actually was.

### "What's worth pitching this week?"
Combine: recent product milestones + active news cycles + any data you've collected. Score each potential story by the quality bar above.

### "Respond to this HARO query"
Go to [press-platforms.md](references/press-platforms.md), use the response
template, follow current outlet limits, and keep the result draft-only.

### "Build my press page"
Use the checklist above. Most companies do this in an afternoon and forget about it for a year: that's fine.

## Boundaries

- Do not contact journalists, submit reporter responses, publish press
  releases, or represent that a draft has been sent without explicit approval
  and a confirmed recipient.
- Do not fabricate claims, data, quotes, customers, credentials, urgency, or
  coverage; separate verified facts from proposed angles.
- Do not impersonate a source, promise exclusivity, or decide legal disclosure,
  embargo, or crisis-response policy.

## Routing

- Use `suede-launch-packaging` to coordinate a broader product launch.
- Use `suede-directory-submissions` for directory and catalog listings.
- Use `suede-social` for approved social distribution and engagement.
- Use `suede-copy` to polish a verified press-page or announcement draft.
- Use `suede-co-marketing` when the announcement is a joint launch with a partner.
