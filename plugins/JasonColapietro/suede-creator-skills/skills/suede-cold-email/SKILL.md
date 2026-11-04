---
name: suede-cold-email
description: "Use when asked \"write a cold email\" or to repair B2B outbound to qualified prospects. Suede AI produces sourced personalization, short subjects, bodies under 75 words, one ask and bounded follow-ups, with current sender-rule checks. NOT FOR: prospect qualification (use suede-prospecting), opted-in lifecycle email (use suede-emails), or broader sales collateral (use suede-sales-enablement)."
metadata:
  display-name: "Suede AI Cold Email Skills"
  version: 2.1.1
---

# Suede AI Cold Email Skills

Use this cold-email playbook to write concise, evidence-grounded outreach that sounds human and respects the recipient.

## Compatibility

Any agent that can read the prospect evidence and product brief; current sender-policy checks need web access. Drafting needs no email account or sending integration.

## Before Writing

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Understand the situation (ask if not provided):

1. **Who are you writing to?** Role, company, why them specifically
2. **What do you want?** The outcome (meeting, reply, intro, demo)
3. **What's the value?** The specific problem you solve for people like them
4. **What's your proof?** A result, case study, or credibility signal
5. **Any research signals?** Funding, hiring, LinkedIn posts, company news, tech stack changes

Work with whatever the user gives you. If they have a strong signal and a clear value prop, that's enough to write. Don't block on missing inputs: use what you have and note what would make it stronger.

---

## Writing Principles

### Write like a peer, not a vendor

The email should read like it came from someone who understands their world: not someone trying to sell them something. Use contractions. Read it aloud. If it sounds like marketing copy, rewrite it.

### Every sentence must earn its place

Cold email is ruthlessly short. If a sentence doesn't move the reader toward replying, cut it. The best cold emails feel like they could have been shorter, not longer.

### Personalization must connect to the problem

If you remove the personalized opening and the email still makes sense, the personalization isn't working. The observation should naturally lead into why you're reaching out.

See [personalization.md](references/personalization.md) for the 4-level system and research signals.

### Lead with their world, not yours

The reader should see their own situation reflected back. "You/your" should dominate over "I/we." Don't open with who you are or what your company does.

### One ask, low friction

Interest-based CTAs ("Worth exploring?" / "Would this be useful?") beat meeting requests. One CTA per email. Make it easy to say yes with a one-line reply.

---

## Voice & Tone

**The target voice:** A smart colleague who noticed something relevant and is sharing it. Conversational but not sloppy. Confident but not pushy.

**Calibrate to the audience:**

- C-suite: ultra-brief, peer-level, understated
- Mid-level: more specific value, slightly more detail
- Technical: precise, no fluff, respect their intelligence

**What it should NOT sound like:**

- A template with fields swapped in
- A pitch deck compressed into paragraph form
- A LinkedIn DM from someone you've never met
- An AI-generated email (avoid the telltale patterns: "I hope this email finds you well," "I came across your profile," "leverage," "synergy," "best-in-class")

---

## Structure

There's no single right structure. Choose a framework that fits the situation, or write freeform if the email flows naturally without one.

**Common shapes that work:**

- **Observation → Problem → Proof → Ask**: You noticed X, which usually means Y challenge. We helped Z with that. Interested?
- **Question → Value → Ask**: Struggling with X? We do Y. Company Z saw [result]. Worth a look?
- **Trigger → Insight → Ask**: Congrats on X. That usually creates Y challenge. We've helped similar companies with that. Curious?
- **Story → Bridge → Ask**: [Similar company] had [problem]. They [solved it this way]. Relevant to you?

For the full catalog of frameworks with examples, see [frameworks.md](references/frameworks.md).

---

## Subject Lines

Short, boring, internal-looking. The subject line's only job is to get the email opened: not to sell.

- 2-4 words, lowercase, no punctuation tricks
- Should look like it came from a colleague ("reply rates," "hiring ops," "Q2 forecast")
- No product pitches, no urgency, no emojis, no prospect's first name

See [subject-lines.md](references/subject-lines.md) for the full data.

---

## Follow-Up Sequences

Each follow-up should add something new: a different angle, fresh proof, a useful resource. "Just checking in" gives the reader no reason to respond.

- 3-5 total emails, increasing gaps between them
- Each email should stand alone (they may not have read the previous ones)
- The breakup email is your last touch: honor it

See [follow-up-sequences.md](references/follow-up-sequences.md) for cadence, angle rotation, and breakup email templates.

---

## Quality Check

Run this pass on the draft before presenting it. Every item resolves to something you can observe in the text, not a feeling about it.

- [ ] "You/your" outnumbers "I/we" in the body
- [ ] Deleting the personalization sentence breaks the sentence that follows it
- [ ] Exactly one ask, answerable with a one-line reply
- [ ] Body is under 75 words
- [ ] Zero strings from What to Avoid appear in the draft: check that list term by term, not by impression
- [ ] Read aloud it uses contractions, and no sentence reads as marketing copy

Any item that fails means rewrite before presenting. Do not hand over a draft with a caveat attached to it.

---

## Output Format

Deliver every email in this shape, with these field labels verbatim.

```
Subject: [2-4 words, lowercase]

Body: (NN words, target under 75)
[the email exactly as it would be pasted into the send tool]

CTA: [the single ask, quoted from the body]

Personalization source: [the specific signal this email traces to (the post, the filing,
the job ad, the release) with enough detail that the user can confirm it is real]
```

`Personalization source:` is required on every email. It is what makes the "do not invent personalization" boundary auditable. If you cannot name a real source, you do not have personalization, and the opening line has to change.

Emit the follow-up table only when the user asked for a sequence rather than a single message:

| # | Send day | New angle it carries | Subject |
|---|---|---|---|
| 1 | 0 | ... | ... |
| 2 | +3 | ... | ... |

3-5 emails total: see [follow-up-sequences.md](references/follow-up-sequences.md) for cadence and angle rotation. Omit the table entirely for a single-message request.

---

## What to Avoid

- Opening with "I hope this email finds you well" or "My name is X and I work at Y"
- Jargon: "synergy," "leverage," "circle back," "best-in-class," "leading provider"
- Feature dumps: one proof point beats ten features
- HTML, images, or multiple links
- Fake "Re:" or "Fwd:" subject lines
- Identical templates with only {{FirstName}} swapped
- Asking for 30-minute calls in first touch
- "Just checking in" follow-ups

---

## Deliverability Gate

Copy that lands in spam earns nothing, and a burned domain takes months to
recover. When the user asks for a sequence or a send plan, state these as
recommendations alongside the copy:

- Send from a secondary domain or subdomain, never the primary domain that
  carries invoices and password resets.
- SPF, DKIM, and DMARC (p=none minimum, aligned) must pass. Gmail treats close
  to 5,000 daily messages to personal accounts as bulk, and Microsoft enforces
  authentication above 5,000 a day; both reject non-compliant mail.
- Keep the spam-complaint rate under 0.1% and never near 0.3%.
- Include a working opt-out and a postal address (CAN-SPAM); honor opt-outs
  fast and permanently.
- Verify addresses first; stop if hard bounces pass 2%.
- Plain text, at most one link, no images or attachments on first touch.

Sources and detail: [benchmarks.md](references/benchmarks.md).

## References

- [benchmarks.md](references/benchmarks.md): directional reply and meeting ranges, deliverability rules with sources, mistakes ranked by damage
- [personalization.md](references/personalization.md): four personalization depths and signal sources
- [subject-lines.md](references/subject-lines.md): subject line defaults and what to avoid
- [follow-up-sequences.md](references/follow-up-sequences.md): cadence, angle rotation, close-out emails
- [frameworks.md](references/frameworks.md): email shapes with examples

Use them to inform the writing, not as a checklist to satisfy.

---

## Boundaries

- Do not invent personalization, mutual connections, customer facts, results, urgency, or prior contact.
- Do not scrape prohibited data, expose sensitive personal information, or advise evasion of consent, spam, or platform rules.
- Do not send, schedule, enroll, or follow up with anyone without explicit authorization for the exact recipients and sequence.
- Do not decide that silence means consent; honor opt-outs and suppression lists before any execution.

## Routing

- Need a qualified prospect list -> use `suede-prospecting`.
- Need lifecycle or nurture email -> use `suede-emails`.
- Need positioning context or collateral -> use `suede-product-marketing` or `suede-sales-enablement`.
- Need CRM stages, lead routing, or suppression operations -> use `suede-revops`.
- Before anything goes to a real recipient -> use `suede-deslop`.
- From those skills, route cold outbound message and follow-up writing back to `suede-cold-email`.

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
