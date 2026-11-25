# lookup: does the Bot API or Telegram.WebApp have it

**When:** does the Bot API have X, a method's parameters, since which version, a Mini App API
question, is the skill up to date.

## Read

`references/api-catalog.md` (tools and the area → reference map), Rich Messages and the
capability matrix `references/telegram-capabilities.md`, per-version items
`references/bot-api-coverage.md`, version gates `references/ui-changelog.md`, sources and dates
`references/official-sources.md`, SDK support `references/sdk-compatibility.md`, Mini App API
`references/mini-apps/webapp-api.md`.

## Steps

1. `tgui.py lookup show <Symbol>` / `lookup search <words>` / `lookup since <version>` /
   `lookup accepts <Type>`; Mini Apps: `tgui.py webapp show|search <name>`.
2. Answer with the symbol, its fields, the version it appeared in and the catalog date. If the
   catalog has no such thing, say "Bot API <version> has no such method or field".
3. Through MCP (`tgui.py mcp`, see `references/api-catalog.md`): `telegram_api_lookup`,
   `webapp_lookup`, `validate_request`, `check_rich_html`, `knowledge_search` (15 tools in all,
   listed in `references/api-catalog.md`).
4. "Is the skill up to date": `tgui.py doctor` (copies, versions, catalog age). Refreshing the
   catalog needs the network (`tgui.py sync bot-api`): only when the user agrees.

## Without scripts

Search `data/bot-api/catalog.json` for the name; quote the description and the fetch date from
its `meta`.

## Done

An answer from the catalog with the version and date, or an explicit "not in the API".
