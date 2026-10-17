<p align="center">
  <img src="assets/logo.svg" alt="PMC" width="128" />
</p>

<h1 align="center">Give Codex a memory it can use</h1>

<p align="center"><strong>Stop explaining the same project in every task.</strong></p>

<p align="center">PMC turns approved project knowledge into private, portable Markdown inside your Obsidian vault.</p>

---

## The problem PMC solves

Yesterday's Codex task learned why an architecture was chosen, which requirement cannot change, what failed in production, and what should happen next. A new task usually starts without that context.

PMC gives the project a trustworthy place to restart.

| Without PMC | With PMC |
|---|---|
| Re-explain the project repeatedly | Start from a focused Project Home |
| Decisions disappear into old chats | Preserve decisions with rationale and evidence |
| Notes drift away from the code | Surface stale or contradictory knowledge |
| Documentation becomes an unstructured dump | Save only reviewed, durable information |
| Knowledge is trapped in one product | Keep ordinary Markdown you own |

## Your first useful result takes one prompt

> **@PMC set up lasting memory for this project in my Obsidian vault**

PMC guides you through creating or connecting a vault, registers the repository, builds a polished `Project Home.md`, and offers to scan the codebase. The scan can capture:

- what the project does;
- how the repository is organised;
- important run, test, and build commands;
- current status and next actions;
- verified constraints, decisions, discoveries, and procedures.

No terminal commands or configuration syntax are required.

## Work naturally

Use plain requests rather than memorising a command language:

```text
@PMC remember this
@PMC remember the decision we just made
@PMC update the project status
@PMC what do we already know about authentication?
@PMC wrap up this task
@PMC check this project's memory
```

During normal work, PMC notices information likely to matter later and asks one clear question before promoting it:

> **This will matter in future tasks. Add it to the project's Obsidian vault?**

## A useful Obsidian front door

Every configured project receives a scannable Project Home with status, current focus, commands, decisions, risks, next actions, and links to deeper notes. Focused templates cover:

- decisions;
- constraints;
- discoveries;
- procedures;
- debugging lessons;
- current state and handoffs.

## Keep the memory trustworthy

Ask PMC to check the project's memory. It can find broken links, overdue reviews, contradictory decisions, stale status, missing setup knowledge, completed actions still shown as active, and important repository changes not reflected in the vault.

Semantic changes are proposed for review rather than silently rewritten.

## Private by design

- Local Markdown only.
- No PMC account.
- No developer server or telemetry.
- No raw transcript capture.
- No Obsidian community plugin required.
- No durable write without user intent or approval.
- Easy to inspect, edit, sync, version, export, or delete.

## Start here

- [Quickstart](docs/quickstart.md)
- [Complete user guide](docs/user-guide.md)
- [Automatic orientation](docs/automatic-orientation.md)
- [Privacy](docs/privacy.md)
- [Support](docs/support.md)

PMC is MIT licensed. See [LICENSE](LICENSE).
