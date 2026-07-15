# CodeTruss agent plugins

Open integration wrappers that teach Claude Code, Codex, and other Agent Skills
clients to use the local-first CodeTruss CLI as an acceptance gate for
AI-generated changes.

The integrations do not contain an analyzer, upload source code, or call a
CodeTruss service. They invoke the separately installed CLI, keep deterministic
analysis on the developer's machine, and require explicit consent before
installation, provider-backed `--llm` review, authentication, or receipt
`sync`.

## Prerequisites

- Git
- Node.js 20.9 or newer
- CodeTruss CLI v0.2.24 or newer from <https://codetruss.com/cli>

The skill can explain the official installer when the CLI is missing, but it
must not install software without the developer's confirmation.

## Claude Code

```bash
claude plugin marketplace add DeliriumPulse/codetruss-plugins
claude plugin install codetruss@codetruss
```

The owned marketplace is live now. CodeTruss is not currently listed in
Anthropic's reviewed community catalog or its separately curated official
marketplace.

## Codex

```bash
codex plugin marketplace add DeliriumPulse/codetruss-plugins
codex plugin add codetruss@codetruss
```

The owned marketplace is live now. CodeTruss is not currently listed in
OpenAI's public Plugin Directory.

## Agent Skills clients

Install the same canonical skill for both Claude Code and Codex with the public
Agent Skills installer:

```bash
npx --yes skills add DeliriumPulse/codetruss-plugins \
  --skill codetruss --agent claude-code codex -y
```

For an immutable install, pin the current reviewed release:

```bash
npx --yes skills add \
  https://github.com/DeliriumPulse/codetruss-plugins/tree/v0.1.5 \
  --skill codetruss --agent claude-code codex -y
```

The skill is indexed at
<https://skills.sh/DeliriumPulse/codetruss-plugins/codetruss>. Review the skill
before use; it can invoke the separately installed CLI with the agent's local
permissions.

## What the skill does

- proposes a narrow repository allow/deny policy and verification commands;
- runs guided `codetruss setup` only after the developer confirms the boundary,
  hook target, and exact verification-command trust;
- installs and diagnoses the existing Claude Code or Codex lifecycle hook;
- reviews working-tree or staged changes and interprets the resulting receipt;
- treats exit codes 1 and 2 as product verdicts with valid evidence, not generic
  shell failures;
- refuses to weaken policy merely to manufacture a green verdict.

The canonical Agent Skills definition is in `skills/codetruss/`. Platform
packages contain byte-identical copies so each marketplace archive is
self-contained.

## Development

```bash
npm test
claude plugin validate ./plugins/codetruss-claude
python3 /path/to/plugin-creator/scripts/validate_plugin.py ./plugins/codetruss
npm run release:verify
```

`npm test` uses only Node.js built-ins and verifies manifests, marketplace
entries, skill parity, and privacy guardrails.
`npm run release:verify` builds the OpenAI and Claude plugin archives twice
from the committed Git tree and proves their bytes are reproducible.

## Security and support

Read [SECURITY.md](SECURITY.md) before reporting a vulnerability. General
wrapper issues belong in this repository; CLI issues belong in the
[CodeTruss CLI tracker](https://github.com/DeliriumPulse/codetruss-cli/issues).
Never attach third-party source, credentials, or unredacted receipts to a public
issue.

## Licensing boundary

The manifests and skill instructions in this repository are MIT licensed. The
separately installed CodeTruss CLI is free to use under the CodeTruss CLI
Proprietary License and CodeTruss Terms of Service. This repository does not
make the CLI open source and does not redistribute its executable bundle.
