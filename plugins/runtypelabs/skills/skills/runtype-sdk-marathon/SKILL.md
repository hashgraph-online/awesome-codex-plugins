---
name: runtype-sdk-marathon
description: 'Build source-controlled Runtype workflows with the SDK or CLI: config-as-code deploys from CI (ensure), save-and-run flows (upsert), long-running or multi-session agent runs with Marathon (runtype marathon or runtype agents task), and Marathon playbooks.'
user-invocable: true
argument-hint: '[SDK, CLI, or Marathon task]'
---

# Runtype SDK and Marathon

Use this skill for code-first Runtype workflows, the CLI, and Marathon. Use
`runtype-build-product` when the user designs hosted product resources through MCP.

## SDK guidance

Fetch live docs when available:

- `get_platform_documentation(topic="sdk-reference")`
- `get_platform_documentation(topic="types-flow-steps")`
- `get_platform_documentation(topic="types-entities")`
- `get_platform_documentation(topic="flow-step-types")`

Code-first modes:

- **Stored**: create persistent agents or flows in Runtype.
- **Upsert**: running the code creates the flow if it does not exist and updates it when
  its steps change. It keeps a version of each change by default
  (`createVersionOnChange: false` turns that off). If the flow was last edited in the
  dashboard or through the API, upsert fails unless you set
  `allowOverwriteExternalChanges: true`.
- **Ensure (config-as-code)**: converge a definition from your repo onto Runtype at deploy
  time without running it. Ensure never deletes a resource, and agents, flows, and skills
  keep a version of each change. The SDK has `ensure` for flows, agents, tools, skills,
  evals, products, surfaces, and client tokens; `evals.ensure` replaces the suite's cases.
  The CLI has `runtype agents ensure <file>` for a JSON agent definition; add
  `--expect-no-changes` to fail a CI job on drift.
- **Virtual**: the definition is supplied per execution without creating a saved agent or
  flow. Execution logs, traces, and retention policies still apply, so this is not a
  zero-retention mode.

Use ensure for CI/CD deploys and upsert for save-and-run scripts. Prefer stored, upsert, or
ensure for production workflows, because dashboard inspection, logs, evals, and versioning
are easier. Use virtual for tests, one-offs, or temporary generated flows. For
privacy-sensitive workloads, verify retention separately.

Use local tools when a tool must run in the user's browser or server: pass a map of tool
names to async functions to `runWithLocalTools`. Use hidden parameters when auth context,
tenant IDs, or sensitive request data must not appear in the tool schema the model sees:
list them in the tool's `hiddenParameterNames`, and the runtime fills them from execution
variables. Names that start with `_internal` are never filled; use `{{secret:NAME}}`
references for credentials. The `sdk-reference` topic has the signatures.

## CLI setup

Install or run directly:

```bash
npm install -g @runtypelabs/cli
npx @runtypelabs/cli@latest <command>
```

Check auth before you change it:

```bash
runtype auth status
```

`runtype auth status` checks only the stored login or signup state. Then pick the first
case that applies:

1. `RUNTYPE_API_KEY` is set: run `runtype auth whoami --no-tty` and reuse that account.
   This is also how CLI commands authenticate in CI.
2. A stored account is authenticated: reuse it.
3. A signup is pending: run the `next` command that `auth status` prints.
4. The user needs a new account: run `runtype auth register --email <email>`, then
   `runtype auth verify <code>`.
5. The user wants the browser login flow of `runtype auth login`: the user runs it in their
   own interactive terminal, not in an automated agent's shell.

For existing-account or installation recovery, follow
`https://runtype.ai/.well-known/agent.md`. Never ask for API keys in chat. Have the user
configure credentials privately.

Common commands include `runtype agents list`, `runtype agents ensure`, `runtype dispatch`,
`runtype flows create`, `runtype records create`, `runtype schedules`, `runtype models`,
`runtype batch`, `runtype eval`, `runtype persona`, `runtype products init`, and
`runtype validate-product`. For flags not listed here, run `runtype --help` or
`runtype <command> --help`.

## Marathon

Marathon is a CLI command that runs long research, code-editing, and build tasks across
multiple sessions. It streams progress, carries context from one session to the next,
supports playbooks, and can use sandboxes. `runtype marathon` is an alias for
`runtype agents task`. The `get_platform_documentation` topics do not cover Marathon, so use
`runtype marathon --help` as the flag reference. User docs:
`https://docs.runtype.com/user-guide/agents/marathon-long-running-tasks`.

The first argument is an agent ID or name. If no agent matches, the CLI creates an agent
with that name in the user's account.

```bash
runtype marathon researcher \
  --goal "Research recent AI announcements and summarize them" \
  --tools firecrawl \
  --max-sessions 5 \
  --max-cost 2

runtype marathon "Code Editor" \
  --goal "Refactor the auth module and run tests" \
  --max-cost 10

runtype marathon calculator \
  --goal "Build a calculator in 3D and deploy it publicly" \
  --sandbox daytona
```

Guardrails:

- **Cost and length**: `--max-sessions` defaults to 50 and there is no default budget. For
  unattended runs, always set `--max-cost <usd>` and an explicit `--max-sessions <n>`.
- **Local files**: local file tools such as `read_file`, `write_file`, and
  `list_directory` are on and can read and write anywhere under the current working
  directory. The `--no-local-tools` flag does not currently turn them off, so start
  research-only runs from an empty directory, and never from an untrusted one.
- **Unattended runs**: without a TTY, or with `--json`, the interactive startup screen is
  off. `--json` prints the final result as JSON. Checkpoint pauses auto-continue after
  `--checkpoint-timeout` seconds (default 10). The `--no-checkpoint` flag does not
  currently remove the pauses.

Built-in tools you can enable with `--tools` include `exa`, `firecrawl`, `dalle`,
`openai_web_search`, `anthropic_web_search`, and `google_search`. The CLI validates tool IDs
and model compatibility at startup.

`--sandbox` accepts `daytona`, `runtype-sandbox`, `cloudflare-worker`, or `quickjs`. Only
`daytona` and `runtype-sandbox` can deploy to a public preview URL.

Models: `--model` sets the model for the run, `--planning-model` and `--execution-model`
set it per phase, and `--fallback-model` is used when the primary model fails. Use routed
model IDs such as `claude-sonnet-5` or `claude-haiku-4-5`. For `--max-tokens` and
`--temperature`, a playbook milestone value beats the CLI flag, and the CLI flag beats the
playbook-level default.

To watch a run in the dashboard, add `--track`. Marathon syncs progress to a Runtype record
named after the task.

### Resume or restart a run

Marathon saves local state per task, by default under
`~/.runtype/projects/<hash>/marathons/` (change it with `--state-dir`).

- `--resume "<new instruction>"` continues from saved state, for example after the run hits
  its session or cost cap. The message is optional.
- `--session <name>` resumes a specific session.
- `--fresh` starts a new run and ignores saved state.
- `--name <name>` keeps separate tasks for the same agent apart. It defaults to the agent
  name.

For long runs that hit context limits, adjust `--compact-threshold`,
`--tool-context observation-mask`, or `--offload-threshold`. See `runtype marathon --help`.

## Playbooks

Use a playbook for repeatable multi-phase work such as research, build, verify, and polish.
Load one with `--playbook`:

```bash
runtype marathon researcher \
  --goal "Research the topic, then build a demo" \
  --playbook research-build \
  --max-cost 5
```

`--playbook NAME` accepts a file path, or a name that resolves to
`.runtype/marathons/playbooks/NAME.{yaml,yml,json,ts,mts}`. The CLI checks the current
directory first, then the home directory. The CLI ships no built-in playbooks, so
`research-build` above is a file the user writes.

A playbook has a `name` and a list of `milestones`. Each milestone has a `name`,
`instructions`, and optional `model`, `fallbackModels`, `completionCriteria`, `maxTokens`,
and `temperature`. Top-level fields include `description`, `rules`, `verification`,
`policy`, `fallbackOnEmpty`, `maxTokens`, `temperature`, and `plugins`. Keep `rules`
explicit about file scope, verification, and deployment expectations.

A TypeScript playbook default-exports a config, or a factory that receives
`{ registerWorkflowHook }`. Wrap it in `definePlaybook` from `@runtypelabs/sdk` for types:

```ts
import { definePlaybook } from '@runtypelabs/sdk'

export default definePlaybook({
  name: 'build-only',
  milestones: [
    {
      name: 'build',
      instructions: 'Build the feature described in the goal, then run the tests.',
      canAcceptCompletion: true,
    },
  ],
})
```

TypeScript playbooks and `plugins` modules run as code with the user's privileges when the
playbook loads. Load only playbooks and plugins the user trusts.

If the `runtype` skill is also installed, its references cover working modes in more depth.
Prefer live MCP documentation over local reference files.
