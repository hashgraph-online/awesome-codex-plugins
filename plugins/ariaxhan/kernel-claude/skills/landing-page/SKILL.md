---
name: landing-page
description: "Explicit landing-page build and deploy operator. Loads marketing and frontend judgment, scaffolds the smallest suitable site, verifies it rendered, deploys to the configured target."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent, WebSearch, WebFetch
disable-model-invocation: true
kernel:
  kind: operator
  version: 2
  side_effects: deploys
  confirmation: on_side_effect
---

<skill id="landing-page">

<purpose>
Build, verify, and optionally deploy a focused landing page. This is the explicit operator;
strategy and aesthetics come from the methodology skills it composes.
</purpose>

<skill_load>
Load `skills/marketing-site/SKILL.md` and `skills/frontend/SKILL.md` before writing.
</skill_load>

<inputs>
Use answers already present in the request/repository. Resolve only what materially changes
the build: audience, desired action, offer/proof, brand/assets, required content/legal pages,
real CTA destination, domain, and deploy target. Never invent brand facts or proof.

For the unresolved inputs, run a structured interview with the AskUserQuestion tool
(batched, up to 4 questions per round, recommended option first where evidence supports
one) instead of guessing or asking loose prose questions. Bounded choices only; positioning
and voice discussions stay prose. The interview method: skills/build/SKILL.md "The
interview".
</inputs>

<scaffold>
- Follow the existing repository and stack first. For a new simple page, prefer static
  HTML/CSS with JavaScript only for real behavior; add a framework only when requirements earn it.
- Build the content argument with `marketing-site`; build the visual system with `frontend`.
- Add only the pages and integrations the brief needs. If forms, analytics, cookies, payments,
  embeds, or accounts touch data, create/update a privacy page that matches the real behavior.
- Keep secrets and deploy credentials out of source.
</scaffold>

<verify-local>
- Render and do visual QA at 375 / 768 / 1440 widths unless the product defines better targets.
- Check hierarchy, realistic content, overflow, keyboard/focus, reduced motion, contrast, images,
  console errors, links, metadata, and CTA/form success plus error paths.
- Confirm the privacy policy matches actual collection and third parties.
- Run the repository's tests/build/lint and fix failures before deployment.
</verify-local>

<deploy>
- Use the project's configured deploy command and provider. If none exists, choose the smallest
  provider-appropriate static deployment; Cloudflare Workers Static Assets is one option, not a
  universal default.
- If the user already named the deploy target and asked to deploy, that counts as confirmation.
  Otherwise surface the resolved account/project/domain before the side effect.
- After deploy, verify the live URL: status 200, headline/content marker, nested assets, legal
  page, and conversion path. Static assets can propagate briefly, so retry a short bounded check
  before diagnosing a successful deploy as broken.
</deploy>

<hard-stops>
- No fabricated proof, shippable placeholders, fake form success, or dead CTA.
- No secrets in committed source.
- No “done” claim based only on source, build, commit, or deploy output; inspect the rendered
  page locally and the served page after deployment.
</hard-stops>

<on_end>
Report the live URL if deployed, target widths and paths checked, claims/proof source, privacy
behavior, and any verification bar not observed.
</on_end>

</skill>
