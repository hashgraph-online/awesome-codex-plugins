---
name: varg-publish-skill
description: >-
  Turn your agent skill into a varg how to listing: reads a skill folder or repo, checks it
  against the varg media skill standard, fills the one card format every listing on varg how to
  (varg.ai/how-to) uses — name, one-line summary, use-when triggers, category, install command,
  a real example of the output — shows it to the person and publishes it for review through the
  varg MCP publish_skill tool (or the API with a varg key). Use when someone says "publish my
  skill", "list this skill on varg", "submit my skill to varg how to", "add my skill to the
  catalog", "how do I get my skill found by agents", or the same in any language. Not for
  finding a skill (use how-to-make-ai-video), not for writing the skill itself, and not for
  contributing to the vargHQ/skills repo (that is a pull request).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai/how-to/publish
compatibility: >-
  Publishes through the varg MCP server (https://mcp.varg.ai/mcp, tools publish_skill and
  my_skills) or, without MCP, POST https://api.varg.ai/v2/skills/submissions with VARG_API_KEY
  (or ~/.varg/credentials). Needs a varg account; publishing is free.
allowed-tools: Bash(curl:*) Read
---

# Publish a skill to varg how to

varg how to (https://varg.ai/how-to) is where AI agents look for video, image and audio skills. Every listing has the
same card, so agents can compare skills at a glance and search finds them by meaning. This skill turns any skill folder
or repo into that card and sends it for review. The varg team approves most skills within a day; then the skill is
searchable by agents (the varg MCP `search_skills`, `varg.ai/how-to/api/search`) and has a page at
`varg.ai/how-to/skills/<slug>`.

**Never publish without the person's OK on the exact card.** Never invent an install command, a feature or an example.

## 0. Gates

- **What is the skill?** A folder with a `SKILL.md` (Agent Skills format), or its repo URL. No SKILL.md → stop: this
  catalog lists agent skills. Offer to help write one first.
- **Where does it live?** The listing links a public https source (GitHub tree URL preferred). Local only → ask the
  person to push it first.
- **How will you send it?** The varg MCP `publish_skill` tool if it is connected (best). Otherwise the API with
  `VARG_API_KEY` (step 6). Neither → tell the person: `claude mcp add --transport http varg https://mcp.varg.ai/mcp`,
  or the form at https://varg.ai/how-to/publish.

## 1. Read the skill

Read `SKILL.md` (frontmatter `name`, `description`, the "Use when" / "NOT for" lines, required keys and tools), the
README, the license, `scripts/` (every script, for step 3) and anything under `assets/` or `examples/` that shows output.

## 2. Is it already listed?

Search with the skill's purpose in one line, through `search_skills` or:

```bash
curl -s "https://api.varg.ai/v2/skills/search?q=<what it makes, URL-encoded>&kind=skill&limit=5"
```

The same skill already listed (same repo, or the same thing under another name) → tell the person and do not publish a
duplicate; an update goes in a message to the varg team (`send_feedback`).

## 3. Check it against the standard

Run the checklist in `references/standard-checklist.md`. Report what fails in plain words. Blocking: secrets in files,
`curl | bash` or install hooks, scripts calling unknown hosts, bundled media without a license, no SKILL.md description.
Everything else (evals, metadata, ≤ 500 lines) is advice: list it, offer to fix it, publish anyway if the person wants.

## 4. Fill the card

Exactly the fields and rules in `references/card.md` — the one format every listing uses:

| Field | Rule (short) |
|---|---|
| `name` | Title Case, ≤ 80 chars, named after the task, from the first fitting name template ("Turn {input} into {output}", "{Task} with {Library}", …) |
| `summary` | One line ≤ 160 chars: what it makes, from what. No "This skill…", no catalog words |
| `source_url` | https repo or tree URL of the skill folder |
| `install` | The exact command from the repo's docs; else `npx skills add <owner>/<repo> --skill <name>` only when the folder sits where that CLI finds it; else leave out |
| `use_when` | 3–6 triggers, from the SKILL.md description, as tasks ("Burning captions into a 9:16 video") |
| `category` | One id from the table in `references/card.md` |
| `tags` | ≤ 12, lowercase: tools, models, formats |
| `media_url` | https link to a real output of this skill (repo asset, the author's post or upload); none → leave out |
| `description` | 2–5 sentences: input → output, how it works, what it needs (keys, tools, cost) |
| `publisher_name` | Who to credit, if not the repo owner |

## 5. Show the card, get the OK

Show it exactly like this and wait for a yes (edits → show again):

```
Name:        <name>
Summary:     <summary>
Source:      <source_url>
Install:     <install or "—">
Use when:    <trigger 1> · <trigger 2> · …
Category:    <category id> (<label>)   Tags: <tags>
Example:     <media_url or "—">
About:       <description>
Standard:    <passes | what is advised>
```

## 6. Publish

With the varg MCP: call `publish_skill` with the card fields. Without it:

```bash
KEY="${VARG_API_KEY:-$(grep -o '"api_key"[^,}]*' ~/.varg/credentials 2>/dev/null | head -1 | cut -d'"' -f4)}"
curl -s -X POST https://api.varg.ai/v2/skills/submissions \
  -H "Authorization: Bearer $KEY" -H 'content-type: application/json' \
  -d '{"name":"…","summary":"…","source_url":"https://…","install":"…","use_when":["…"],"category":"…","tags":["…"],"via":"api"}'
```

`201` with `"moderation": "pending"` = sent. `429` = over the plan's publishing quota (`my_skills` shows it); say when
to try again. `400` lists the field to fix.

## 7. Tell the person what happens next

"Sent for review. The varg team checks it, usually within a day. Ask me 'what's the status of my skills?' (`my_skills`,
or `GET /v2/skills/submissions/my`). Once approved it is searchable by agents and has a page at
varg.ai/how-to/skills/<slug>." A rejection comes with a reason: fix it and publish again.
