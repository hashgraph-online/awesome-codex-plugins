# QuestionPunk plugin

Create saved survey drafts, refine questions, review studies and analyze authorized research results from Codex. The skills are in `skills/`.

## Before you sign in

The plugin declares one server in `mcp.json`, `questionpunk-start` (https://mcp.questionpunk.com/start). It asks for no sign-in and has one tool, which turns a survey Codex drafted into a link that opens it in QuestionPunk as a guest draft. It saves and reads nothing.

## Connect your account

Add QuestionPunk's hosted server and sign in with your own QuestionPunk account:

```sh
codex mcp add questionpunk --url https://app.questionpunk.com/api/v1
codex mcp login questionpunk
```

Then start a new Codex chat. The skills can now save drafts to your account, edit and publish studies, and read results.

The account server is added this way rather than declared in the plugin because Codex shows the model only part of a plugin server's tools: with QuestionPunk's 70 tools, a plugin-declared server lost the account, survey and template tools (Codex CLI 0.169, November 2026). The same server added with `codex mcp add` shows all of them.

Install instructions, permissions and support are in the [repository README](https://github.com/questionpunk/codex-plugin#readme).

## Connection for this build

MCP endpoint: https://app.questionpunk.com/api/v1

QuestionPunk: https://app.questionpunk.com
