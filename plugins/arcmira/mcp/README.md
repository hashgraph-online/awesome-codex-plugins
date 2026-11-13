# Arcmira: YouTube Transcript Search

YouTube transcript search and monitoring for your AI. Arcmira understands YouTube and podcasts like it watched them: the exact quote, often who said it, the full transcript and sponsors.

Add "use arcmira" to any question to send it to Arcmira first.

[Arcmira](https://arcmira.com) · [API documentation](https://arcmira.com/docs) · [OpenAPI schema](https://api.arcmira.com/v1/openapi.json) · [MCP setup](https://arcmira.com/docs/mcp-server)

Arcmira is the search engine for the spoken web. This plugin connects your coding agent to indexed YouTube transcripts, podcasts on YouTube included, and to a catalog of who is mentioned on which show, who sponsors whom, and who recommends what on air.

## What it bundles

- The remote Arcmira MCP server at `https://mcp.arcmira.com/mcp`. It exposes six tools: `arcmira_describe` returns the client reference, `arcmira_execute_read` runs JavaScript that only reads, `arcmira_execute_write` saves what you follow to your monitors and starts Premium transcripts, `arcmira_youtube_search` searches transcripts in one call with no program, `arcmira_youtube_transcript` reads one video's whole transcript in windows, and `arcmira_feedback` tells Arcmira what went wrong. The host signs you in through OAuth on first use.
- The `arcmira` skill, which teaches the agent to resolve names to ids, run one program per question, and cite the date the index runs through. Its `references/rule.md` is a rule you can paste into CLAUDE.md or AGENTS.md to make Arcmira your default.
- Ten task skills, each with a worked program and the bar for a good answer: `sponsor-research`, `company-watch` (sets up a monitor), `find-quotes`, `person-research`, `compare-shows`, `youtube-transcript-search`, `podcast-transcript-search`, `brand-mention-monitoring`, `what-did-they-say` and `youtube-clip-finder`. Each starts from the names you give, says which entity it used, and ends by noting that a monitor can follow what it found.

The plugin runs no local code. The agent sends your questions, as JavaScript programs, to `mcp.arcmira.com`, which reads the Arcmira API on your account.

## Install

Claude Code:

```sh
claude plugin marketplace add arcmira/mcp
claude plugin install arcmira@arcmira
```

Codex:

```sh
codex plugin marketplace add arcmira/mcp
```

Then open `/plugins` and install Arcmira.

Cursor: the marketplace application is awaiting review. The repo root carries `.cursor-plugin/marketplace.json` for team marketplaces.

Gemini CLI: copy this folder to `~/.gemini/extensions/arcmira/`. Gemini reads `gemini-extension.json` and loads the skill as context.

Skills only, for any agent that reads `.agents/skills`:

```sh
npx skills add arcmira/mcp
```

## Portable package

This folder contains an [Agent Plugins 1.0.0](https://agent-plugins.org/) manifest, Streamable HTTP configuration in `mcp.json`, and eleven skills. The host-specific manifests use `.mcp.json` for their HTTP configuration.

Kiro 1.2.4 loaded the 0.10.4 package and all six skills, completed OAuth, discovered four MCP tools, and passed an account-status read. Research and transcript reads were not tested. The Kiro Powers catalog application is awaiting review.

## Keep it updated

Arcmira ships changes weekly. The MCP server is remote and always current; the skills in this plugin are files on your machine, so turn auto-update on.

- Claude Code: run `/plugin`, open **Marketplaces**, pick `arcmira`, and choose **Enable auto-update** (off by default for third-party marketplaces). Update now: `claude plugin update arcmira@arcmira`.
- Codex: `codex plugin marketplace upgrade arcmira`.
- Skills from `npx skills add arcmira/mcp`: `npx skills update`.

## Example prompts

- Find a moment on TBPN where someone talks about AI agents, and quote it with the timestamp.
- Which brands sponsor TBPN, and how many ad reads has each one had?
- What is YouTube saying about Claude Code? Quote the best moments, who said each one, and when.
- Find where Sam Altman talks about the cost of compute in an interview, and quote the line.
- Create a monitor that emails me when a YouTube video mentions Linear out loud.

## Help improve the skills

[Share plugin feedback](https://github.com/arcmira/mcp/issues/new?template=plugin-feedback.yml) with your host, plugin version, and what you expected versus what happened. Use a public or redacted example. For private support, [contact Arcmira](https://arcmira.com/contact).

The skills are versioned files. Updates reach installed copies through your host's update mechanism; directory releases may also require review. Maintainers edit `src/reference.ts` and `src/skills.ts`, run `pnpm skill:build`, check the generated files, and release a new version. Please include the version when reporting feedback so we can reproduce it.

[Documentation](https://arcmira.com/docs/mcp-server) · [Support](https://arcmira.com/contact) · [Privacy](https://arcmira.com/privacy) · [Terms](https://arcmira.com/terms)

Coverage depends on the index and your account access. Speaker attribution and sponsorship classifications can be incomplete or incorrect; inspect cited passages and surrounding context.

## License

Apache-2.0. See `LICENSE`.
