# Suede AI Skills MCP

<a href="https://trendshift.io/repositories/82031?utm_source=trendshift-badge&amp;utm_medium=badge&amp;utm_campaign=badge-trendshift-82031" target="_blank" rel="noopener noreferrer"><img src="https://trendshift.io/api/badge/trendshift/repositories/82031/daily?language=Python" alt="JasonColapietro%2Fsuede-creator-skills | Trendshift" width="250" height="55"/></a>

`suede-skills-mcp.mjs` is a local stdio MCP server for Suede skills.

It gives an agent:

- skill routing: `search_suede_skills` ranks the pack against a task, and
  `plan_suede_workflow` turns a goal into an ordered sequence of skills;
- every skill's instructions, through `get_suede_skill` or the
  `suede://skill/{name}` resource template, with name autocomplete;
- a live A-F page audit: `suede_live_page_audit` fetches a public URL and grades
  what Google and AI answer engines actually receive, with the top fixes;
- copy checks: `suede_copy_check` scores pasted copy against the pack's house
  rules and names each fix;
- public GitHub skill installs, local plugin notes, MCP, and skill-copy install
  options;
- SEO/AEO/AI EO copy audit, A-F visibility and code-grade checklists, and
  multi-lane QA checklists for skill, MCP, docs and public site changes.

For public positioning, launch copy, public explainer language, Suedify
messaging, MCP explanation, social posts, emails, FAQ answers, and evidence
boundaries, use [`PROMO.md`](../PROMO.md).

Run it directly:

```bash
node mcp/suede-skills-mcp.mjs --profile all
```

Profiles:

- `all`: expose the full public catalog.
- Area profiles `workflow`, `creator`, `marketing`, and `consumer` narrow the
  server to the corresponding plugin-bundle context. `artist` remains a legacy
  alias for the creator context.
- Specialty profiles `ship`, `craft`, `found`, `demand`, `revenue`, and
  `position` narrow the server to one catalog specialty.

The server is dependency-free and speaks newline-delimited JSON-RPC over stdio,
protocol versions 2025-11-25, 2025-06-18, 2025-03-26 and 2024-11-05. It supports
`initialize`, `ping`, `tools/list`, `tools/call`, `resources/list`,
`resources/read`, `resources/templates/list`, `prompts/list`, `prompts/get`, and
`completion/complete`.

Current surface: 12 tools (`list_suede_skills`, `list_suede_specialties`,
`search_suede_skills`, `get_suede_skill`, `suede_install_options`,
`suede_copy_seo_audit`, `suede_visibility_grade`, `suede_code_grade`,
`suede_qa_checklist`, `suede_live_page_audit`, `suede_copy_check`,
`plan_suede_workflow`), 7 resources (`suede://catalog`, `suede://specialties`,
`suede://plugins`, `suede://copy-seo-audit`, `suede://visibility-grade`,
`suede://code-grade`, `suede://qa-checklist`), 1 resource template
(`suede://skill/{name}`), and 5 prompts (`suede-copy-seo-audit`,
`suede-plugin-install`, `suede-visibility-grade`, `suede-code-grade`,
`suede-full-qa`). Every tool returns structured content against a published
output schema, with a text fallback.

## Live page audit

`suede_live_page_audit` fetches the page, its `robots.txt`, its sitemap and
`/llms.txt`, then grades four lanes A-F: findability (status, HTTPS, noindex,
Googlebot access, canonical, title, description, sitemap, language, viewport),
AI search readiness (ChatGPT, Perplexity and Claude answer-bot access, H1,
readable text in the served HTML, JSON-LD, H2 sections, FAQ, llms.txt, alt text),
page action (calls to action, the primary action you name, a contact path, HTML
response time) and share preview (Open Graph and X cards). A 4xx or 5xx caps the
overall grade at F; noindex or a Googlebot block caps it at D. Training crawlers
such as GPTBot are reported without a penalty, because blocking them is a policy
choice.

It is the one tool that reaches the network. It follows up to five redirects,
reads at most 2 MB of HTML, and refuses localhost, private and reserved
addresses at every hop. Two environment variables control it:

- `SUEDE_MCP_OFFLINE=1` turns the live audit off, so the server stays fully local.
- `SUEDE_MCP_ALLOW_PRIVATE_HOSTS=1` lets it audit a local dev server.

## Docker

```bash
docker build -t suede-skills-mcp .
docker run -i --rm suede-skills-mcp
```

The image holds `mcp/` and `skills/` only and runs as the unprivileged `node`
user. Pass `-e SUEDE_MCP_OFFLINE=1` to run it without network access.

The plugin manifests (`.mcp.json` for Claude Code, `.codex-plugin/plugin.json`
for Codex) register one server, `suede_skills_mcp`, on the `all` profile, so an
install starts one process and exposes each tool once. The area and specialty
profiles above remain available to anyone who registers the script by hand with
`--profile`. Catalog additions are exposed through
the generic discovery tool and `suede://catalog`; adding a skill does not add a
new tool, resource, or prompt.
