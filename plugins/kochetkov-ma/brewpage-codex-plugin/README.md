# BrewPage plugin for Codex

Publish HTML, Markdown, any file or a multi-file static site from Codex to
[brewpage.app](https://brewpage.app) and get an HTTPS link back. Publishing needs
no account and no API key.

BrewPage is a hosted, closed-source service. This plugin (manifest, skill and
scripts) is MIT-licensed.

## What is inside

| Part | Path | What it does |
|------|------|--------------|
| Manifest | `.codex-plugin/plugin.json` | Plugin metadata, skills folder, MCP config, icon |
| Skill | `skills/brewpage-publish/` | Detects the content type, asks for namespace and password, uploads through `scripts/brewpage-run.sh`, returns the link |
| MCP server | `.mcp.json` | The BrewPage remote MCP server, `https://brewpage.app/mcp` (Streamable HTTP, no sign-in) |
| Icon | `assets/icon.svg` | BrewPage mark |

The skill is a copy of the MIT-licensed BrewPage publishing skill from
[kochetkov-ma/claude-brewcode](https://github.com/kochetkov-ma/claude-brewcode)
(`openclaw/brewpage-publish`, commit `9ddf5c045b576a3b6493b37dc1743fa3015b5a22`),
with its User-Agent set to `brewpage-codex/0.1.0`.

## Status

Version 0.1.0. The manifest and bundle pass the HOL Plugin Scanner (see the
workflow in `.github/workflows/`); installation inside Codex has not been tested yet.

## Use it

Ask in natural language:

```
Publish report.html to BrewPage and give me the link
Share this Markdown summary as a BrewPage page that expires in 7 days
Upload the ./dist folder to BrewPage as a site
```

The skill asks for a namespace (`public` lists the page in the gallery; a private
slug, the default, keeps it unlisted) and an optional password file, uploads, and
prints the link. See [the skill workflow](skills/brewpage-publish/SKILL.md).

| Content | API |
|---------|-----|
| Text, Markdown, `.md` file | `POST /api/html?format=markdown` |
| Whole HTML document, `.html` file | `POST /api/html?format=html` |
| Any other file | `POST /api/files` |
| Built static directory or `.zip` | `POST /api/sites` |

## Limits

Pages expire: default 15 days, 1 to 30 days (up to 90 with an optional free profile
at [account.brewpage.app](https://account.brewpage.app)). An HTML or Markdown page
or a file is up to 5 MB; a site is up to 200 files and 20 MB. Current values:
`https://brewpage.app/api/limits`.

## Privacy

- An unlisted link is not private: anyone with the link can open it. Never publish
  secrets, credentials or personal data, and use `public` only for content meant to
  be found.
- Each publish returns an owner token. The skill writes it to
  `./brewpage-history.md` (mode 600, added to `.gitignore`) and never shows it in chat.
- Requests go only to `brewpage.app`.

## Requirements

macOS, Linux or WSL with `bash`, `curl`, `jq` and `python3`; sites also need `node`,
`zip` and `unzip`. The scripts use no third-party packages.

## Links

- [BrewPage API guide](https://brewpage.app/api) and
  [OpenAPI contract](https://brewpage.app/api/openapi.json)
- [Terms](https://brewpage.app/terms), [Privacy](https://brewpage.app/privacy),
  [Security policy](SECURITY.md)

## License

MIT, see [LICENSE](LICENSE). The hosted BrewPage service is proprietary.
