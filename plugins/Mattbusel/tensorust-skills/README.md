# Tensorust agent skills

Four agent skills backed by the hosted [Tensorust Ontology MCP server](https://shop.tensorust.com/api/mcp). They give a coding or research agent public-records data it does not have on its own. Free previews need no key.

| Skill | What it does |
|---|---|
| [counterparty-screen](https://github.com/Mattbusel/tensorust-skills/blob/main/skills/counterparty-screen/SKILL.md) | Who owns and controls a US company or home, and whether a vendor or purchase line hits DoD 1260H, Section 889, FCC Covered List, UFLPA or BIOSECURE |
| [bdc-mark-crosscheck](https://github.com/Mattbusel/tensorust-skills/blob/main/skills/bdc-mark-crosscheck/SKILL.md) | What every BDC lender marks a private first-lien loan at, from SEC filings, and where lenders disagree |
| [idr-offer](https://github.com/Mattbusel/tensorust-skills/blob/main/skills/idr-offer/SKILL.md) | No Surprises Act IDR offer bands and arbitrator loss rates from the CMS public use file |
| [llm-api-cost](https://github.com/Mattbusel/tensorust-skills/blob/main/skills/llm-api-cost/SKILL.md) | Dated, source-cited LLM API prices and the cost of a request |

## Install

Claude Code:

```
/plugin marketplace add Mattbusel/tensorust-skills
/plugin install tensorust@tensorust-skills
```

The repo also has an [Agent Plugins](https://agent-plugins.org) manifest (`plugin.json`) for GitHub Copilot. Any other MCP client can use the server in [mcp.json](https://github.com/Mattbusel/tensorust-skills/blob/main/mcp.json): `https://shop.tensorust.com/api/mcp` (streamable HTTP).

## Example

Ask the agent:

```
Screen Hikvision before we buy cameras for a federally funded lab.
```

The counterparty-screen skill calls the MCP tools (`lookup_organization`, `exposure_screen_purchases`) and reports the lists Hikvision is on (1260H, Section 889, FCC Covered List) and what that means for the purchase.

## Docs and license

- Skill files: [skills/](https://github.com/Mattbusel/tensorust-skills/tree/main/skills)
- Full data needs a Tensorust key (`Authorization: Bearer tdk_...`): https://shop.tensorust.com/offers/enterprise-api
- MIT license: [LICENSE](https://github.com/Mattbusel/tensorust-skills/blob/main/LICENSE)
