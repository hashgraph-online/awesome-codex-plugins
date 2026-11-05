# Metis Check plugin

The Metis verification engine as a plugin for ChatGPT and Codex (one listing in the OpenAI plugin directory). One identifier, or every identifier in one passage, settled at the body that issues it and answered with exactly one of four states: settled true, settled false, not decidable (a person decides) or unreachable (a delay, not evidence). Anything not looked at is reported as not checked, with the reason. Every check ends in a report with a unique id (MC-XXXX-XXXX-XXXX), a public page, a PDF, signed receipts and a recheck button.

The plugin is a thin package. All the work happens on the Metis API:

- MCP endpoint: `https://check-api.metisfoundry.com/mcp/check` (streamable HTTP; `apps/api/app/mcp_remote.py`)
- Tools: `check_identifier`, `check_text`, `get_report` (`apps/api/app/mcp_check.py`)
- Auth: OAuth 2.1 with dynamic client registration (`apps/api/app/mcp_oauth.py`); the consent page takes a Metis sign-in or a live API key with the `mcp:call` scope
- Resource metadata: `https://check-api.metisfoundry.com/.well-known/oauth-protected-resource/mcp/check`

## Package layout

```
plugins/metis-check/
  plugin.json                 manifest: listing fields, review test cases, release notes
  mcp.json                    the server entry and its OAuth block
  skills/metis-check/SKILL.md how to pick a tool and present a result
  skills/setup/SKILL.md       onboarding: connecting, first check, where reports live
  assets/icon.png, logo.png   512 x 512, from the brand kit (see assets/README.txt)
```

The marketplace file for local installs is at the repo root: `.agents/plugins/marketplace.json` (marketplace name `metis-local`).

## Local install in Codex

From the repo root (the folder that holds `.agents/plugins/marketplace.json`):

```
codex plugin marketplace add ./
```

Then in the ChatGPT desktop app (or Codex): run `/plugins`, choose the **Metis (local)** marketplace and install **Metis Check**. Restart the ChatGPT desktop app after the first install so the plugin directory picks the marketplace up.

To enable the plugin for one project, add to that project's `.codex/config.toml` (project config loads only for trusted projects):

```toml
[plugins."metis-check@metis-local"]
enabled = true
```

The key is `<plugin name>@<marketplace name>`.

On install, Connect opens the Metis sign-in page. Sign in, or create a Metis Check account from the link on that page and you return automatically. The tools then run under that account.

## Test prompts

- `Is 10.1038/s41586-020-2649-2 a real DOI?` (one DOI at Crossref; expect settled true)
- `Check the LEI HWUPKR0MPOU8FGXBT394 for Apple Inc.` (GLEIF, with a name compare)
- `Check the citations in this paragraph: Recent work (doi:10.1038/s41586-020-2649-2; PMID 32939066; arXiv:2005.14165) extended the approach. See also 10.1000/not-a-real-doi-9999.` (check_text; expect three settled true, one settled false)
- `Does the citation 410 U.S. 113 exist? It is cited as Roe v. Wade.` (case citation; on an account without case law the reply relays the tool's sentence and names the plans page)
- `Open my Metis Check report MC-7K3F-9Q2M-4XWD` (get_report; use an id the account holds)

What a good reply looks like: it leads with the report headline, lists each identifier with its state in Metis's words and the registry, says what was not checked and why, and gives the report and PDF links. It does not grade the text as a whole and makes no claim stronger than the four states.

## Before submitting

The submission kit is `notes/plugin-submission-kit-2026-10-26.md` (listing copy with character counts, review test cases, reviewer account, commerce declaration, domain verification, a pre-submission grep for banned phrases, and the open questions for review).
