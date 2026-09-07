---
name: marketing-site
description: "Honest marketing-site method: audience, offer, proof, objections, privacy, art direction, handoff. Triggers: marketing site, landing page, company website, product website, portfolio, campaign page, client website, conversion, positioning, offer, value proposition, CTA, social proof, testimonial, privacy policy."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
kernel:
  kind: methodology
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="marketing-site">

<purpose>
Turn a product or service into a focused, credible website. The page should help a specific
person understand the offer, trust it, and take the next useful action—without marketing
theater or a generic template wearing different nouns.
</purpose>

<skill_load>skills/frontend/SKILL.md</skill_load>

<inputs>
Recover what the user and repository already supplied before asking questions:

1. Audience: who arrives, what they know, and what situation brought them here.
2. Desired action: install, buy, book, join, contact, learn, or compare.
3. Offer: what changes for the visitor, how it works, and why this option is different.
4. Friction: objections, risks, missing information, switching cost, and alternatives.
5. Proof: product behavior, demo, screenshots, founder expertise, customer evidence, data.
6. Brand and constraints: voice, assets, references, legal/privacy needs, stack, deadline.

Do not force an interview when the brief answers these. Ask only for a missing choice that
would materially change the page; otherwise make a reversible assumption and label it.
</inputs>

<truth-rules>
Never invent customers, testimonials, metrics, guarantees, awards, integrations, press logos,
scarcity, fake urgency, or “trusted by” claims. Placeholder proof must be visibly marked as a
placeholder and cannot ship. Describe capabilities at the strength the evidence supports.
Specific and modest beats impressive and false.
</truth-rules>

<strategy>
Write a one-sentence positioning statement:
“For [audience in situation], [offer] helps [outcome] by [mechanism/difference].”

Then choose a page argument that fits the buying decision. A useful default is:
problem or desire → promise → mechanism → proof → objections → action.
It is a diagnostic spine, not a mandatory section order. A familiar plugin may need one sharp
idea and a demo; an expensive service may need process, proof, risk reduction, and detail.

Give each section one job. Prefer one primary CTA; secondary actions are allowed when they
serve a genuinely different visitor state. CTA copy should name the next step, not “Submit.”
</strategy>

<copy>
- Lead with the visitor's outcome or tension, then make the mechanism concrete.
- Use the user's language and real nouns. Delete adjectives that the page cannot prove.
- Keep the headline, subhead, visual, and CTA mutually reinforcing.
- Answer the strongest objection near the claim that creates it.
- Let product screenshots, examples, demos, and specifics carry more weight than slogans.
- Match detail to consequence: higher price/risk needs more explanation and reassurance.
</copy>

<art-direction>
Use `skills/frontend/SKILL.md`. Derive the visual direction from audience, brand, offer,
content, and references. A provocative page earns its tension through the idea; it does not
need random visual aggression. Preserve an existing design system when present.
</art-direction>

<privacy-and-trust>
The privacy page must describe the actual implementation: what data is collected, why, where
it goes, retention/deletion, cookies or analytics, form/email providers, user choices, contact,
and effective date. If the site collects nothing, say so plainly and still disclose hosting
logs or third parties that may receive technical data. Do not copy a broad boilerplate policy
that claims tools the site does not use. Flag jurisdiction-specific legal review when stakes
require it; do not present generated copy as legal advice.
</privacy-and-trust>

<client-delivery>
For client work, confirm who approves copy/design, who owns supplied assets, the domain and
accounts, analytics/consent choices, editable-source handoff, launch/rollback plan, and who
maintains the site. Keep credentials in the client's account or secure environment—not source.
Read `skills/marketing-site/references/client-delivery.md` for the compact handoff checklist.
</client-delivery>

<verification>
Check the rendered page at target widths and follow every conversion path. Verify all claims
against supplied evidence, every CTA and legal link, keyboard/focus behavior, performance,
metadata/share preview, form success/error states, and the deployed privacy behavior.
</verification>

<output>
State the audience, desired action, positioning, page argument, proof used, art direction,
assumptions/placeholders, privacy reality, and what was actually verified.
</output>

</skill>
