# sealos-skills

Agent plugin for deploying and operating apps on [Sealos Cloud](https://sealos.io),
packaged in the [Agent Plugins](https://agent-plugins.org/) format and as a
[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) profile bundle.
The same `use-sealos` skill is also installable through Codex, Claude Code,
Cursor, Qoder, `skills.sh`, OpenClaw / ClawHub, CodeBuddy, Gemini CLI, Qwen
Code, and generic repo importers.

Say "deploy X to Sealos" (or "帮我把 X 部署到 Sealos") in a compatible agent
and the `use-sealos` skill handles the rest: sign-in, picking the fastest
deploy path, databases, storage, public HTTPS, and post-deploy verification.

## What's inside

```
package.json                        # DeepSeek Harness bundle manifest (`dsh.bundle`)
cordis.patch.yml                    # inserts the skill provider into a dsh profile
index.js                            # registers `use-sealos` on `ctx.skills`
CLAUDE.md                           # context-only hosts (Gemini, Qwen, Amp / Kimi)
gemini-extension.json               # Gemini CLI extension
qwen-extension.json                 # Qwen Code extension
openclaw.plugin.json                # unused on OpenClaw's native package.json path; install plugins/sealos instead
.codex-plugin/plugin.json           # root Codex import manifest
.agents/plugins/marketplace.json    # Codex marketplace entry
.codebuddy-plugin/marketplace.json  # CodeBuddy marketplace
skills/                             # skills.sh entries (symlinks → plugins/sealos/skills/*)
plugins/sealos/
├── .codex-plugin/plugin.json       # Codex marketplace plugin manifest
├── .claude-plugin/plugin.json      # Claude Code manifest
├── .cursor-plugin/plugin.json      # Cursor manifest
├── .qoder-plugin/plugin.json       # Qoder manifest
├── commands/sealos.md              # /sealos for compatible plugin hosts
└── skills/
    ├── use-sealos/
    │   ├── SKILL.md                # intent router + execution rules
    │   ├── references/             # loaded on demand
    │   │   ├── deploy.md           # three deploy paths (store / image / source)
    │   │   ├── build.md            # Dockerfile, linux/amd64 build, registry push
    │   │   ├── databases.md        # KubeBlocks clusters + credentials
    │   │   ├── platform.md         # manifest contract (labels, Ingress, storage, quota)
    │   │   ├── operate.md          # status, logs, debugging, deletion
    │   │   └── recipes.md          # per-app recipes for popular self-hosted software
    │   └── scripts/
    │       ├── sealos-api.py       # auth (OAuth2 device flow) + Template API, stdlib only
    │       └── wait-app.sh         # post-deploy readiness + URL verification
    ├── sealos-deploy/SKILL.md      # Brain managed-mode entry (MCP-gated pipeline)
    └── k8s-kaniko-job/             # sandbox build executor (Kaniko Job → GHCR)
        ├── SKILL.md
        └── scripts/kaniko-build.py
```

## Installation

### Cursor

From a published GitHub repo: **Settings → Plugins**, paste the repository
URL in **Search or Paste Link**, open the Sealos plugin, click **Add to
Cursor**.

For local development, symlink the skill into your personal skills folder:

```bash
ln -sfn "$(pwd)/plugins/sealos/skills/use-sealos" ~/.cursor/skills/use-sealos
```

### Claude Code

```text
claude plugin marketplace add labring/sealos-skills
claude plugin install sealos@sealos-skills
/reload-plugins
```

Use `/sealos` for interactive work. The marketplace also accepts a local
checkout path.

### Codex

```sh
codex plugin marketplace add labring/sealos-skills
codex plugin add sealos@sealos
```

In Codex CLI, invoke `$sealos`; in Codex App, select Sealos under Plugins.
The marketplace source is `.agents/plugins/marketplace.json`; the plugin
manifest is `plugins/sealos/.codex-plugin/plugin.json`. A repository-root
Codex manifest is also included for direct importers.

### Qoder

In Qoder, open the plugin **Marketplace** (Settings → Plugins → Marketplace),
click **+ Create Plugin**, choose **import from a local folder**, and select
`plugins/sealos` from a clone of this repository.

To distribute, zip the contents of `plugins/sealos` (the zip root must
contain `.qoder-plugin/plugin.json`) as `sealos-2.0.0.zip` and share or
publish it through the Qoder marketplace.

Use `/sealos` in Qoder after installation.

### DeepSeek Harness

This repository is a dsh profile bundle. After `npx @deepseek-ai/dsh web` works, install the plugin into the same `web` profile (`pnpm` must be on `PATH`):

```sh
npx @deepseek-ai/dsh plugin --profile web add github:labring/sealos-skills
npx @deepseek-ai/dsh web
```

A local checkout:

```sh
npx @deepseek-ai/dsh plugin --profile web add /path/to/sealos-skills
```

`use-sealos` appears in the session skill catalog. Say "deploy X to Sealos"; the model loads the skill via the `skill` tool, then runs `scripts/sealos-api.py` / `kubectl` through bash.

Login writes `~/.sealos/kubeconfig`; grant the host's required filesystem
access when prompted.

Add the GitHub topic `dsh-plugin` on the public repo so it shows up in the harness plugin index.

### OpenClaw

Install the plugin directory, not the repository root:

```sh
openclaw plugins install /path/to/sealos-skills/plugins/sealos
```

OpenClaw loads it as a Cursor bundle and exposes `use-sealos`. Slash-command
exposure is not claimed. Say "deploy X to Sealos".

Do not install the repo root. OpenClaw sees root `package.json` first, treats
the checkout as a native plugin, and fails because that package has no
`openclaw.extensions`. Root `openclaw.plugin.json` is not used on that path.

### CodeBuddy

```text
/plugin marketplace add labring/sealos-skills
```

Command exposure depends on the CodeBuddy runtime.

### Gemini CLI

Context-only extension. Slash commands are not claimed.

```sh
gemini extensions install https://github.com/labring/sealos-skills
```

Ask Gemini to deploy to Sealos Cloud. It loads `CLAUDE.md`, which points at
`use-sealos`.

### Qwen Code

Context-only extension. Slash commands are not claimed.

```sh
qwen extensions install https://github.com/labring/sealos-skills
```

### skills.sh

```sh
npx skills add labring/sealos-skills
```

The pack installs three skills: `use-sealos` (the interactive entry — say
"deploy X to Sealos"), plus `sealos-deploy` and `k8s-kaniko-job`, which are
inert outside a managed sandbox (see below).

### Brain (managed sandbox)

Brain's GitHub-deploy pipeline installs this pack into a Devbox with
`npx skills add <repo> -y` and drives the `sealos-deploy` skill in managed
mode (`SEALAI_DEPLOY_MODE=managed`, MCP handshake via `template_ready` /
`deployment_completed`, source builds via a `k8s-kaniko-job` Kaniko Job).
Point Brain's `DEPLOY_SKILL_SOURCE` env at this repository. The design and
the full control-plane contract live in `BRAIN-ADAPTATION.md`.

### Amp / Kimi / generic repo importers

Import `https://github.com/labring/sealos-skills.git`. Behavior is
host-dependent. Context is `CLAUDE.md`; the skill lives at `skills/use-sealos`
and `plugins/sealos/skills/use-sealos`.

### First run

Say "deploy X to Sealos". The skill checks credentials
(`sealos-api.py status`) and, if needed, signs you in via OAuth2 device flow —
or paste a kubeconfig from the Sealos web console into `~/.sealos/kubeconfig`.

## Deploy strategy

1. **Template store** — 200+ one-click templates, deployed via the Template
   API (~3 min).
2. **Official Docker image** — a generated template (workloads + KubeBlocks
   databases + Ingress) for self-hosted apps not in the store (~5-10 min).
3. **Source build** — Dockerfile → `docker buildx --platform linux/amd64` →
   registry push → image deploy (for the user's own projects).

All three paths go through the Sealos Template API, so every deployment is
tracked as an instance: visible in the Sealos UI and removable as a unit.

## Requirements

- `kubectl`, `python3` (stdlib only); `docker` + `gh` only for the source path
- A Sealos account — the skill signs in via OAuth2 device flow, or paste a
  kubeconfig from the Sealos web console into `~/.sealos/kubeconfig`

## Development

Scratch clones, test dumps, and other local-only artifacts go in
`validation-assets/` (gitignored).

This 2.0 release replaces the previous eight-skill implementation. The
standalone Canvas, Sealos Desktop app builder, cloud-native readiness,
Dockerfile, and Compose-conversion skills are archived on the
`codex/backup-before-next-20260928` branch. Deployment, database, object
storage, and operations now route through `use-sealos`; Brain's managed
deployment has its own `sealos-deploy` and `k8s-kaniko-job` skills.
