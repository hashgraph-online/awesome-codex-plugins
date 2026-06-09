# SenderKit Email Deliverability Skill

Portable AI-agent instructions for getting transactional email authenticated and landing in the inbox.

This open-source skill lives in the [`senderkit/senderkit-skills`](https://github.com/senderkit/senderkit-skills) GitHub repository under `skills/senderkit-email-deliverability/`. It helps coding assistants diagnose and fix the DNS that controls inbox placement, whether mail is sent directly via SenderKit or routed through a provider such as Resend, SendGrid, Postmark, Mailgun, SES, or SMTP. It works with Codex, Claude, Cursor-style agents, and generic LLM coding assistants that can read local files and run `dig`.

## What it does

- Identifies the sending domain and the records that must exist.
- Diagnoses current SPF, DKIM, DMARC, MX, and alignment with `dig`/`nslookup`.
- Generates the exact DNS records to add (one merged SPF record, DKIM as issued by SenderKit, a DMARC record starting at `p=none`).
- Points to the SenderKit dashboard for issued values (DKIM selector/key, verification token).
- Verifies publication and sets realistic propagation expectations; optional manual validators.

## Contents

```text
senderkit-skills/
|-- LICENSE
`-- skills/
    `-- senderkit-email-deliverability/
        |-- AGENTS.md
        |-- README.md
        |-- SKILL.md
        |-- agents/
        |   `-- openai.yaml
        |-- llms.txt
        `-- references/
            |-- spf-dkim-dmarc.md
            |-- dns-provider-notes.md
            |-- troubleshooting.md
            `-- sources.md
```

## Use with coding agents

Reuse from GitHub:

```bash
git clone https://github.com/senderkit/senderkit-skills.git
```

Codex / OpenAI-compatible skill loaders:

```bash
mkdir -p ~/.codex/skills
cp -R senderkit-skills/skills/senderkit-email-deliverability ~/.codex/skills/senderkit-email-deliverability
```

Prompt:

```text
Use $senderkit-email-deliverability to diagnose and fix SPF, DKIM, and DMARC for my sending domain.
```

Claude / Anthropic-style plugins:

Install the `senderkit` plugin from this repository, or package `skills/senderkit-email-deliverability/` as a standalone skill. `SKILL.md` is the canonical instruction file, and the skill name declared there is `senderkit-email-deliverability`.

Cursor, Windsurf, Aider, Continue, and generic coding agents:

Add `senderkit-skills/skills/senderkit-email-deliverability/` to your repository or agent context and ask the assistant to read `AGENTS.md` or `SKILL.md` before making changes.

## Related skills

- `senderkit-integration` — wire sends into the codebase (From domain, headers).
- `senderkit-mcp-messaging-operations` — send a live test and confirm inbox placement.

## Reuse and distribution

This repository is open source under the MIT license. Reuse the `skills/senderkit-email-deliverability/` directory as the portable skill package, or vendor it into an agent-specific skills folder. Keep `SKILL.md`, `AGENTS.md`, `llms.txt`, `agents/openai.yaml`, and `references/` together, and preserve the MIT license.
