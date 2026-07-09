---
name: lvtd-skills-router
description: Use when the user is unsure which LVTD skill or marketplace plugin fits their problem, asks what skill to use, describes a cross-domain workflow, or needs help choosing among installed or source LVTD skills.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Skills Router
  category: Productivity
  tags: skills,router,workflow,agents
---

# LVTD Skills Router

Use this skill to choose the smallest useful set of LVTD skills for the user's
problem. Route by domain, outcome, and evidence needed. Prefer one primary
skill; add secondary skills only when they cover a separate concern in the same
workflow.

## Source Of Truth

When working inside this repository, do not hand-maintain a static catalog in
this skill. Use generated metadata:

1. Run `npm run build:registry` if `dist/registry.json` is missing or stale.
2. Read `dist/registry.json`.
3. Use each skill's `name`, `description`, `category`, `tags`, and
   `hosts.codex.plugin` or `hosts.claudeCode.plugin`.
4. Treat skills without a `hosts.*.plugin` value as direct-install skills.

When the generated registry is not available, inspect source frontmatter in
`skills/*/SKILL.md` and plugin grouping rules in `scripts/marketplace-utils.mjs`.
When using an installed plugin outside this repository, route from the installed
skills and plugin metadata available in the current client.

## Routing Workflow

1. Restate the user's concrete task in one phrase.
2. Search skill names, descriptions, tags, and plugin names for that task.
3. Choose the most specific matching skill whose description directly covers the
   current request.
4. If several skills match, prefer the one closest to the user's actual work:
   implementation over strategy, diagnosis over broad planning, framework-specific
   over framework-neutral when the framework is known.
5. Name the marketplace plugin only when the user asks what to install or when
   the matching skill is unavailable in the current client.
6. Continue with the selected skill when the user asked for work, not just advice.

## Useful Registry Queries

List current marketplace plugins and included skills:

```bash
node --input-type=module -e '
import { readFile } from "node:fs/promises";
const registry = JSON.parse(await readFile("dist/registry.json", "utf8"));
const plugins = new Map();
const direct = [];
for (const skill of registry.skills) {
  const plugin = skill.hosts?.codex?.plugin || skill.hosts?.claudeCode?.plugin;
  if (!plugin) {
    direct.push(skill.name);
    continue;
  }
  plugins.set(plugin, [...(plugins.get(plugin) || []), skill.name]);
}
for (const [plugin, skills] of [...plugins.entries()].sort()) {
  console.log(`${plugin}: ${skills.sort().join(", ")}`);
}
if (direct.length) {
  console.log(`direct-install: ${direct.sort().join(", ")}`);
}
'
```

Find candidate skills by keyword:

```bash
node --input-type=module -e '
import { readFile } from "node:fs/promises";
const query = process.argv.slice(1).join(" ").toLowerCase();
const registry = JSON.parse(await readFile("dist/registry.json", "utf8"));
for (const skill of registry.skills) {
  const haystack = [
    skill.name,
    skill.displayName,
    skill.description,
    skill.category,
    ...(skill.tags || []),
  ].join(" ").toLowerCase();
  if (haystack.includes(query)) {
    const plugin = skill.hosts?.codex?.plugin || "direct-install";
    console.log(`${skill.name} (${plugin}) - ${skill.description}`);
  }
}
' "calibredb"
```

## Tie-Breakers

- Django-specific htmx work: choose `django-htmx`; use `htmx-*` skills for
  framework-neutral patterns or deeper htmx mechanics.
- Rust game work: choose `rust-game-*` or Bevy/bracket/roguelike skills before
  general Rust skills when the request is explicitly game-related.
- SEO channel tests from *Traction*: choose `traction-seo-content`; broader SEO
  strategy, roadmap, technical SEO, or link-building work belongs in `seo`.
- Experiment design, analysis, platform strategy, or long-term measurement:
  choose `practical-ab-testing`; growth channel tests belong in `traction`.
- Developer documentation research, planning, drafting, samples, diagrams,
  information architecture, or maintenance belongs in `developer-docs`.
- Product page, pricing page, launch page, social preview, or shareability audit:
  choose `make-product-viral`.
- Calibre library CLI work: choose `calibredb`.
- Test suite architecture outside a framework-specific skill: choose the
  framework-neutral `tdd` plugin skills.

## Avoid

- Do not load every candidate skill just to browse. Route from metadata first.
- Do not continue routing once a specific skill clearly fits.
- Do not copy plugin names or skill lists into this file unless they are durable
  tie-breakers. Generated registry data is the catalog source of truth.
