# The Workspace is one system

The Workspace (an instance's loose `_repo` source and its live workflows, tables, agents, forms, apps, configs and event subscriptions) is one product, and the foundation Solutions build on. Every change is a change to that whole system: check what it breaks, what it duplicates, and what it should improve for everyone.

## Find what exists before building

**Rule:** Before adding a workflow, module, table, agent, or event subscription, search for the one that already covers the domain and extend or fix it.

```bash
bifrost files search <domain-term> --source all --include '*.py'
bifrost workflows list
bifrost tables list
bifrost agents list
bifrost events list-sources
```

**Why:** Two workflows for the same job drift apart: one gets the fix, the other keeps the bug, and users can't tell which to use.

## One owner per job

**Rule:** Each recurring job and each reaction to an event has one owning workflow or agent. Before subscribing to an event source or adding a schedule, run `bifrost events list-subscriptions <source>` and make sure nothing already does that work. Prefer reacting to an event over polling for changes.

**Why:** Two handlers for the same event take the same action twice (two tickets, two emails, two updates), and neither knows the other exists.

## Know who depends on what you change

**Rule:** Before changing a shared module, a workflow's parameters or result shape, a table's name or fields, a config key, or an integration mapping, list everything that uses it, then check each one after the change:

- modules: `bifrost files search 'from modules.<name>' --source all`
- workflows: search for the workflow's name and `path::function` (forms, apps, agent tools and other workflows reference it)
- tables and configs: search for the table name or config key
- Solutions that allow outbound access can use Workspace pieces too: include `--source solutions`

**Why:** A changed result shape breaks every app screen and agent tool that reads it, and nothing fails until someone uses it.

## Fix the pattern, not just the instance

**Rule:** When you fix a bug or a security problem, search for the same pattern elsewhere and fix those too, or list them for the person who asked.

**Why:** The same mistake usually exists in every workflow that was copied from the first one.

## Centralize on the second use

**Rule:** The second time logic is needed, move it into a shared module with one owner and switch the first copy to it. Shared modules are the building blocks the rest of the Workspace and Solutions rely on; keep them small, typed, and documented.

**Why:** Copies diverge, and an improvement made in one copy (a timeout, a tenant filter, a retry) never reaches the others.

## Rename and move through the supported path

**Rule:** Search for references first, then use the supported path (`bifrost workflows replace`, checked with `bifrost workflows list-orphaned`; see `../references/workflows.md`). Never re-register a renamed workflow.

**Why:** Re-registering mints a new id, and every form, app, agent and schedule still points at the old one.

## Solutions build on the Workspace

**Rule:** When a Solution needs a Workspace module, workflow, or table, depend on it deliberately (`allow_outbound_access`) instead of copying it in. When Workspace logic grows into something meant to be installed elsewhere, move it into a Solution and point the Workspace at it, rather than keeping two copies. The ownership models are in `../SKILL.md`.

**Why:** A copy inside a Solution stops receiving the Workspace's fixes, and a Workspace fork of a Solution stops receiving the Solution's.

## Checklist

- Searched for existing workflows, modules, tables, agents and subscriptions covering the domain.
- One owner per job and per event reaction; events over polling.
- Every consumer of a changed module, workflow, table, config or mapping listed and checked.
- Same-pattern fixes applied elsewhere or listed.
- Repeated logic moved into a shared module.
- Renames through `workflows replace`; no re-registration.
- Solutions depend on Workspace pieces instead of copying them.
