# sync. skills

[![skills.sh](https://skills.sh/b/synchronicity-labs/skills)](https://skills.sh/synchronicity-labs/skills)

Agent skills for [sync. labs](https://sync.so): lipsync videos, make photos and AI characters talk, translate and dub, fix spoken words, localize whole campaigns, run lipsync in bulk, and build sync. into your own apps. They work with Claude Code, Codex, Cursor, Gemini CLI, Hermes and any agent that reads [Agent Skills](https://agentskills.io).

## Install

**Any agent** ([skills.sh](https://skills.sh)):

```bash
npx skills add synchronicity-labs/skills
```

Add `--skill lipsync` to install one skill, or `--agent claude-code` to pick the agent.

**Claude Code plugin**, which installs the skills and connects the sync. MCP server in one step:

```text
/plugin marketplace add synchronicity-labs/skills
/plugin install sync@sync
```

Then run `/mcp`, select `sync` and sign in with your sync. account.

**Gemini CLI** extension, with the same skills and MCP server:

```bash
gemini extensions install https://github.com/synchronicity-labs/skills
```

Then run `/mcp auth sync` and sign in with your sync. account.

**Cursor and Codex** read the plugin manifests in `.cursor-plugin/` and `.codex-plugin/`. **Kiro** and other clients that read [Agent Plugins](https://agent-plugins.org) use the root `plugin.json` and `mcp.json`.

### Connect sync.

The skills use the hosted sync. MCP server at `https://mcp.sync.so/mcp`, where you sign in with your sync. account and have no key to copy. The `setup` skill walks any agent through connecting. For scripts, CI and the `sync-api` skill, set an [API key](https://sync.so/settings/api-keys) as `SYNC_API_KEY` instead.

## Skills

| Skill | What it does | Try |
| --- | --- | --- |
| [setup](skills/setup) ([guide](docs/setup.md)) | Connects sync. to your agent, checks your account and gets you to a first video. | "Set up sync." |
| [lipsync](skills/lipsync) ([guide](docs/lipsync.md)) | Lip-syncs a video to new audio or a typed script. | "Lipsync ./talk.mp4 to ./new-take.wav" |
| [talking-photo](skills/talking-photo) ([guide](docs/talking-photo.md)) | Makes a photo, portrait or character talk. | "Make this headshot say: welcome to the team" |
| [ai-video-to-talking](skills/ai-video-to-talking) ([guide](docs/ai-video-to-talking.md)) | Gives dialogue to AI-generated clips from Veo, Kling, Sora and others, including multi-shot scenes. | "My Veo clip has no dialogue. Make her say this line." |
| [translate-and-dub](skills/translate-and-dub) ([guide](docs/translate-and-dub.md)) | Dubs a video into other languages with matching lips. | "Dub this YouTube video into Spanish" |
| [edit-dialogue](skills/edit-dialogue) ([guide](docs/edit-dialogue.md)) | Changes or removes a few spoken words in the speaker's own voice. | "Change the price I say to $49" |
| [localize-campaign](skills/localize-campaign) ([guide](docs/localize-campaign.md)) | Localizes a set of videos across markets: plan, pilot, run, review sheet. | "Make these three ads in Spanish, German and Japanese" |
| [batch-lipsync](skills/batch-lipsync) ([guide](docs/batch-lipsync.md)) | Lip-syncs every row of a CSV or folder within your plan's limits, with safe resume. | "Lipsync each row of leads.csv onto presenter.mp4" |
| [troubleshoot](skills/troubleshoot) ([guide](docs/troubleshoot.md)) | Finds why a job failed, stalled or was rejected, resumes it without paying twice, and can report the problem to sync. | "My lipsync failed, why?" |
| [sync-api](skills/sync-api) ([guide](docs/sync-api.md)) | Builds sync. into apps with the REST API or the Python and TypeScript SDKs: uploads, idempotency, webhooks, errors. | "Add sync. lipsync to my Next.js app" |

Every skill quotes the cost before starting paid work and waits for your approval. Each one has a guide in [`docs/`](docs) with example prompts and common questions. The same guides, with Spanish, French, Brazilian Portuguese and German translations in [`docs/i18n/`](docs/i18n), are published at [sync.so/docs](https://sync.so/docs/plugins-and-extensions/agent-skills/overview) whenever this repo changes.

## Repository layout

```text
skills/<name>/SKILL.md       one skill per folder; references/ and scripts/ load on demand
docs/<name>.md               a guide per skill for people, plus overview.md; published on sync.so/docs
docs/i18n/<locale>/          translations of every guide (es, fr, pt-BR, de)
shared/                      reference files copied into the skills that use them
.claude-plugin/              Claude Code plugin and marketplace manifests
.codex-plugin/, .cursor-plugin/
plugin.json, mcp.json        Agent Plugins manifest (Kiro and other clients)
gemini-extension.json        Gemini CLI extension, with GEMINI.md as its context
.mcp.json                    the hosted sync. MCP server
evals/                       `claude plugin eval` suite with MCP mocks
catalog.json                 generated list of skills that Studio and the docs read
scripts/                     validate.py, sync_shared.py, build_catalog.py
tests/                       tests for bundled scripts
```

## Contributing

See [AGENTS.md](AGENTS.md) for the rules. In short:

1. Edit a skill, or a file in `shared/`. Then run `python3 scripts/sync_shared.py` so every copy matches.
2. If you changed a guide in `docs/`, update its four translations in `docs/i18n/` and their `source-sha256` (see [AGENTS.md](AGENTS.md#docs-pages)).
3. Check it: `python3 scripts/validate.py`, `python3 -m unittest discover -s tests`, and `claude plugin validate .`.
4. Run the evals for what you changed: `claude plugin eval . --case '<skill>-*'`. See [evals/README.md](evals/README.md).

When the MCP server's tools change, refresh `evals/mocks/sync/_tools.json` (see `evals/README.md`). The validator then flags any tool name a skill mentions that no longer exists.

## Support, privacy and security

- Support: https://support.sync.so or support@sync.so
- Contact: hello@sync.so
- Privacy policy: https://sync.so/privacy
- Terms of service: https://sync.so/terms
- Security: report vulnerabilities as described in [SECURITY.md](SECURITY.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
