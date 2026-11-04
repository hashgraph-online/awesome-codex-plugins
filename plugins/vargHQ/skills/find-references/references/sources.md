# The seven sources

In this order. Each one answers a different question; skipping one usually leaves an atom empty.

| # | Source | Question it answers | Atoms | Access | Cost |
|---|---|---|---|---|---|
| 1 | varg how to | What already worked for this format? | style, trend | `curl -s "https://varg.ai/how-to/api/search?q=…"`, the varg how to MCP (`search_how_to`) or `vargai search` | free; keep to a few searches |
| 2 | X, last 7 days | What are people saving this week? | trend | an X MCP or the X API; fallback: web search `site:x.com` | depends on the X access |
| 3 | Refs (refs.video) | How do films like this one cut, pace and look? | trend, style | MCP `https://refs.video/mcp` or `scripts/mcp_call.py` | search free, no key; full cards with a free account; frame sheets and blueprints with Pro |
| 4 | FrameThrower | Which real frames have this light, lens or mood? Which ads and animation? | film, pop culture, style | MCP `https://framethrower.ai/api/mcp`, OAuth sign-in | $2 free credit, then pay per use |
| 5 | Film-Grab, Shot Cafe, Eyecannndy, ShotDeck | The person's own browsing in the best still libraries | film | links in `links.md` only; the agent never fetches them | free, except ShotDeck (subscription) |
| 6 | Pinterest, Are.na | What have people already curated for this look? | style, pop culture | `media-download` (`pinterest.sh`, gallery-dl); Are.na MCP `https://mcp.are.na/mcp` | free |
| 7 | YouTube | Which moments, music videos, trailers and title sequences do people remember? | pop culture, motion | search; yt-dlp for 5-15 s clips (`media-download`'s `video.sh`) | free |

## Why the bot rules matter

From the varg craft review of these sites (2026-10-26):

- **Shot Cafe**: `robots.txt` disallows ClaudeBot; personal, non-commercial terms. Human links to `/tag/<tag>` only.
- **Film-Grab**: the operator rejects AI and bots; "fair dealing" covers non-commercial research. Human search
  links `/?s=<query>` only.
- **Eyecannndy**: Cloudflare answers automation with 403; clips are excerpts of others' work. Human links to
  `/technique/<slug>`; use only slugs that exist, or link the home page and name the technique.
- **ShotDeck, Film Vibes**: subscriber products with login-only search; use restricted to reference, internal or
  non-commercial purposes.

## Queries that work

- Name the feeling, not the subject: "lonely, sodium-lit, wet", not "night market".
- Search by attribute: color, light direction, lens, shot size, decade, film stock, time of day.
- Go to the specific, recognizable edge on purpose: one famous scene, one iconic costume, one named animation
  style. Then borrow its look, not its content.
- On X, rank by bookmarks and read the author's first reply; on Pinterest, use `<film> still`,
  `<director> color palette`, `<decade> film grain`, `<character> cosplay`, `<genre> lighting`.
