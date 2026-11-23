# BrewPage plugin for Codex

<p>
<a href="https://github.com/kochetkov-ma/brewpage-codex-plugin/actions/workflows/hol-plugin-scanner.yml"><img height="18" alt="HOL Plugin Scanner" src="https://github.com/kochetkov-ma/brewpage-codex-plugin/actions/workflows/hol-plugin-scanner.yml/badge.svg"></a>
<a href="https://github.com/kochetkov-ma/brewpage-codex-plugin/blob/main/LICENSE"><img height="18" alt="License MIT" src="https://img.shields.io/badge/license-MIT-green"></a>
</p>

Publish HTML, Markdown, any file or a multi-file static site from Codex to
[brewpage.app](https://brewpage.app) and get an HTTPS link back. Publishing needs
no account and no API key.

BrewPage is a hosted, closed-source service. This plugin (manifest, skill and
scripts) is MIT-licensed.

## What is inside

| Part | Path | What it does |
|------|------|--------------|
| Manifest | `.codex-plugin/plugin.json` | Plugin metadata, skills folder, MCP config, icon |
| Skill | `skills/brewpage-publish/` | Prepares drafts locally and routes authorized publishes and updates through BrewPage MCP or the bundled runner |
| MCP server | `.mcp.json` | The BrewPage remote MCP server, `https://brewpage.app/mcp`, with Streamable HTTP, anonymous access and optional account sign-in |
| Icon | `assets/icon.svg` | BrewPage mark |

The skill is a copy of the MIT-licensed BrewPage publishing skill from
[kochetkov-ma/claude-brewcode](https://github.com/kochetkov-ma/claude-brewcode)
(`openclaw/brewpage-publish`, commit `cc19e2fc02ae4752b32d4e1ada4e275cd810f58b`),
with its User-Agent set to `brewpage-codex/0.2.2`. See [the member inventory](PROVENANCE.json).

For a skill refresh, use `python3 tools/vendor-skill.py vendor --upstream
../claude-brewcode --commit <reviewed-full-commit>` after setting the new version
in `.codex-plugin/plugin.json`. The script copies the OpenClaw skill and records
its source revision, source and installed member hashes, file modes, and versioned
Codex User-Agent in `PROVENANCE.json`. Recheck the refreshed package with
`python3 tools/vendor-skill.py check --upstream ../claude-brewcode`.

## Verification

Codex CLI 0.171.0 verified all twelve skill members in an isolated 0.2.2
candidate install. The [HOL Plugin Scanner run](https://github.com/kochetkov-ma/brewpage-codex-plugin/actions/runs/45058780494)
succeeded on the tree of commit `74b97c9`, with no findings.

## Use it

Ask in natural language:

```
Publish report.html to BrewPage and give me the link
Draft an RSVP form with BrewPage Page data and leave it local
Update the saved BrewPage publication with ./dist
```

The skill uses the available BrewPage MCP tools for supported operations. When a
permitted HTTPS fallback is needed, it can upload local bytes through the bundled
runner. Drafts stay local. For a write, the skill resolves publication and owner
choices before sending anything. See [the skill workflow](skills/brewpage-publish/SKILL.md).

| Content | API |
|---------|-----|
| Text, Markdown, `.md` file | `POST /api/html?format=markdown` |
| Whole HTML document, `.html` file | `POST /api/html?format=html` |
| JSON document | `POST /api/json` |
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
- The runner can save anonymous owner proof in `./brewpage-history.md` with mode
  `0600`. It prints reader-facing results by default. Deliver management links
  and owner keys only through a verified private channel. Signed-in MCP publishes
  use the connected account's publishing access.
- A confirmed publication can still need recovery of its unsaved owner proof.
  Follow the protected recovery steps in the [ownership recipe](skills/brewpage-publish/references/ownership.md).
- Requests go only to `brewpage.app`.

## Requirements

macOS, Linux or WSL with `bash`, `curl`, `jq` and `python3`; sites also need `node`,
`zip` and `unzip`. The scripts use no third-party packages.

## Related

- [brewpage.app](https://brewpage.app): the hosting service; [API guide](https://brewpage.app/api); [OpenAPI docs](https://kochetkov-ma.github.io/brewpage-openapi/)
- [brewpage-openapi](https://github.com/kochetkov-ma/brewpage-openapi): OpenAPI contract and the `brewpage-mcp` MCP server ([npm](https://www.npmjs.com/package/brewpage-mcp))
- [brewpage-action](https://github.com/kochetkov-ma/brewpage-action): GitHub Action that publishes CI artifacts ([Marketplace](https://github.com/marketplace/actions/publish-to-brewpage))
- [brewpage-cookbook](https://github.com/kochetkov-ma/brewpage-cookbook): interactive recipes published on BrewPage
- [brewpage-obsidian](https://github.com/kochetkov-ma/brewpage-obsidian): Obsidian plugin that publishes notes ([Obsidian community](https://community.obsidian.md/plugins/brewpage-publisher))
- [brewpage-browser-extension](https://github.com/kochetkov-ma/brewpage-browser-extension): browser extension that publishes pages, selections and files
- [brewpage-publish-plugins](https://github.com/kochetkov-ma/brewpage-publish-plugins): publishing plugins for AI coding tools and the n8n node ([npm](https://www.npmjs.com/package/n8n-nodes-brewpage))
- [langchain-brewpage](https://github.com/kochetkov-ma/langchain-brewpage): LangChain tools ([PyPI](https://pypi.org/project/langchain-brewpage/))
- [llama-index-tools-brewpage](https://github.com/kochetkov-ma/llama-index-tools-brewpage): LlamaIndex tool spec ([PyPI](https://pypi.org/project/llama-index-tools-brewpage/))
- [OpenAPI contract](https://brewpage.app/api/openapi.json) (JSON)
- [Terms](https://brewpage.app/terms), [Privacy](https://brewpage.app/privacy), [Security policy](SECURITY.md)

Support: [info@brewpage.app](mailto:info@brewpage.app)

## License

MIT, see [LICENSE](LICENSE). The hosted BrewPage service is proprietary.
