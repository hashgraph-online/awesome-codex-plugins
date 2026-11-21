# Standard checklist (before publishing)

The varg media skill standard in full: https://varg.ai/how-to/standard. Check these, in this order.

## Blocking (do not publish until fixed)

- [ ] `SKILL.md` exists with frontmatter `name` and `description`.
- [ ] No secrets: no API keys, tokens or `.env` files in the folder or its git history you can see.
- [ ] Scripts are safe: no `curl | bash`, no install or post-install hooks, network calls only to hosts the skill names
      (model APIs, its own CDN). Read every script.
- [ ] Bundled media has a license (own work, CC, or the vendor's terms). No film stills, no scraped photos of people.
- [ ] The source is public over https.

## Advised (list them, offer to fix, publish if the person wants)

- [ ] `description` is third-person, says what it makes, has "Use when …" triggers and a "Not for …" line.
- [ ] Gates first: what it needs (keys, tools, inputs) and what it asks the person before spending money.
- [ ] `SKILL.md` ≤ 500 lines; long material in `references/`.
- [ ] Cost is stated per run (credits or dollars) when it calls paid models; free/local is said too.
- [ ] Models named by current ids; references by role (identity, product, style, …) with their license.
- [ ] `evals/` with trigger cases (should / should not use) — helps agents pick it.
- [ ] One real example of the output exists somewhere public (it becomes the card's preview).
