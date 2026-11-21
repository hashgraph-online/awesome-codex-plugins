# qURL plugin for Codex

Share an app running on your machine privately, straight from Codex, with
qURL: no deploy, no account, no API key, no signup. Install it as the
[repository README](../../README.md) says.

## What it adds

| Skill | How it runs | What it does |
|---|---|---|
| `qurl:qurl` | Codex uses it on its own whenever you want to share, publish or open something with qURL. You can also type `$qurl:qurl`. | The qURL agent skill. |
| `qurl:share` | Only when you type `$qurl:share [who]` | Share the app you're working on privately: email invitations, email sign-in, review, approved passkeys or a contract. Asks who it's for. |
| `qurl:approve` | Only when you type `$qurl:approve [who or what] [CRID]` | Decide a waiting request: a verified email (review), a passkey's approval details, a contract entitlement from your backend, or a six-digit code. Never by name. |
| `qurl:access` | Only when you type `$qurl:access [change] [CRID]` | See who is invited and who has access; invite more addresses, resend, remove someone, or change the mode. |

`share`, `approve` and `access` are Codex's equivalent of slash commands: their
`agents/openai.yaml` sets `allow_implicit_invocation: false`, so the model is
never offered them on its own and they add nothing to a session's context
until you type them. They require qURL CLI 3.4.1 or newer, because an older
CLI publishes a resource that anyone with its address can open, and their
rules hold whatever the skill says.

### Private access modes

| Mode | Who can open it |
|---|---|
| `invite_only` | Only the email addresses you invite. Strangers can't ask. |
| `email_capture` | Anyone who verifies an email address; you receive each one. |
| `review` | People verify an email and ask; you approve each one. |
| `keys` | Passkeys you approve one by one. |
| `contract` | People your own backend entitles (a purchase, a subscription). |

Email verification proves control of a mailbox, not who someone is. The modes
need a `qurl` CLI whose `qurl publish --help` lists `--access`, and a qURL
service with private access turned on. Where either is missing, Codex says so
and shares nothing; it never falls back to a public share or six-digit codes.

The plugin has no MCP server. The skill already drives the `qurl` CLI, which
needs no account; a bundled server (`@layervai/qurl-mcp`) would start a Node
process through `npx` in every Codex session, shared or not, to reach the same
CLI.

## Keeping the bundled skill current (maintainers)

`skills/qurl/SKILL.md` is a copy of the skill served at
<https://layerv.ai/skills/qurl/SKILL.md>, with the reviewed `scripts/directory-skill.patch` applied. The patch removes
runtime instruction downloads for directory compliance. The served file is the
source of truth: never edit the copy here. The `Check plugins` workflow
compares the two every day and on every PR, and fails while they differ. To
update it:

1. Copy the served file and policy reference, apply `scripts/directory-skill.patch`
   in a temporary directory, then copy both patched files into the plugin:

   ```bash
   source_dir="$(mktemp -d)"
   mkdir -p "$source_dir/references"
   curl -fsSL https://layerv.ai/skills/qurl/SKILL.md -o "$source_dir/SKILL.md"
   curl -fsSL https://layerv.ai/skills/qurl/references/access-policies.md -o "$source_dir/references/access-policies.md"
   git -C "$source_dir" apply < scripts/directory-skill.patch &&
     cp "$source_dir/SKILL.md" plugins/qurl/skills/qurl/SKILL.md &&
     cp "$source_dir/references/access-policies.md" plugins/qurl/skills/qurl/references/access-policies.md
   ```

2. Raise `version` in `plugin.json` in the same PR. People get the new files
   when they run `codex plugin marketplace upgrade layerv`; the version is how
   they, and `codex plugin list`, tell one copy from another. Use a patch
   version for a new copy of the skill or a wording change, a minor version
   for a new command, and a major version when a command is removed or
   renamed. The version lives only in `plugin.json`, never in the marketplace
   entry.
3. If the skill's rules changed, check that `skills/share`,
   `skills/approve` and `skills/access` still agree with them.
4. Run the checks the workflow runs:

   ```bash
   python3 scripts/check_manifests.py .
   python3 scripts/check_codex_install.py . -- npx -y @openai/codex@0.162.1
   ```

Raise the version for any other change to the plugin's files too.

## Requirements and data handling

Sharing a local app requires local command execution on the computer running
that app. The plugin installs the qURL CLI from LayerV's official GitHub
release when needed. The computer and app must stay running while shared.
A cloud session cannot reach an app on your computer through this plugin alone.

The main skill and its private policy reference are bundled. Updates to those instructions arrive through plugin releases; the installed
plugin does not download behavioral instructions at runtime. CLI setup
downloads the official installer from `raw.githubusercontent.com/layervai/`
and release binaries and checksums from `github.com/layervai/qurl-integrations`.

The CLI creates a device identity on the publisher computer. It sends resource
and access-management requests to LayerV. Email modes send the recipient email
addresses the publisher supplies; verification and access records are processed
by LayerV. Email capture and review disclose the consumer's verified email to
the publisher. Public app names must contain no secrets or recipient details.
Access records, including verified email addresses and enrolled invitations,
can be retained longer than 30 days; they have no fixed automatic deletion
deadline. Expiry of access does not mean deletion of its records.
Access links and invitation tokens are credentials; do not put them in public
messages or logs. The plugin has no MCP server.

Read LayerV's [privacy policy](https://layerv.ai/privacy) and
[terms](https://layerv.ai/terms). For support, use
[LayerV support](https://layerv.ai/contact).
