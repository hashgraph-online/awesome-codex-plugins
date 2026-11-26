---
name: knowledge-vault
description: How to USE and keep the knowledge vault — the Obsidian "world map" of how this codebase's modules work and link to each other — as the retrieval layer for every repo it covers. Use this BEFORE any major or cross-module change (query the vault instead of re-exploring the code), whenever you finish ANY meaningful change (a new module, an enhancement, a bug fix that revealed a trap, a new integration, a schema or enum change, a new flag, a client ruling or decision, especially a reversal, a release cut or changelog entry), and whenever you're asked about the vault, the map, "the world", the module docs, or told to update Obsidian or the notes. Updating the vault is part of the definition of done, so a change that ships without its note is incomplete. Also read this before writing any new architecture doc; it probably belongs in the vault, not in docs/.
---

# Knowledge vault

A living map of how this system is built and how the pieces connect: domains, modules, end-to-end flows, integrations, platform conventions and traps, decisions, releases, plus a generated `World.canvas`. It lives in its own git repository outside the code, so one map can cover several repos and every checkout and branch sees the same picture. The hooks and the `vault` CLI find it through the repo's remote or path in `_meta/vault.json`; `VAULT_ROOT` overrides the lookup.

It exists because the knowledge in a codebase lives in places that can't show relationships: a changelog nobody re-reads, a tracker in date order, docs written for an audience, and an agent's private memory. Which module a change ripples into is exactly the thing that is hard to reconstruct from code.

Trust `vault status` and `_meta/Coverage.md` for counts, never a number written in prose.

---

## Finding what's affected (read this half first)

Don't re-read the code per task. Query the map:

```bash
vault find payment capture retry                        # topic → notes
vault find --paths app/Services/PaymentService.php      # file → owning notes
vault find --json order refund                          # for scripting; --limit N too
```

Every hit prints the note's one-liner, its `status` and `updated` (the honesty fields), its path in the vault, and its one-hop links **with the reason each link exists**. That neighbour list is the **blast radius**: the other notes to check when your change ripples. Topic search tiers through names → aliases and flags → tags → full text, and for a full-text hit prints the matching bullet, which in a long note is the retrieval unit.

The workflow:

1. **Before changing an area**, find its note. Inside a covered repo the hooks do this for you: a hint on your prompt, a pointer the first time you edit a documented file. **When a hook surfaces a note, actually read it.** *How it works* and *Gotchas* are where lost hours are recorded. A pointer that says "stub, nothing recorded yet" means the note exists but is thin; you are about to learn what should go in it.
2. **Treat *Connects to* as the impact list.** Each reason tells you whether your change reaches that neighbour.
3. **A file that maps to no note** is a signal in itself. Either it is genuinely new (the trigger table says what to create) or it is an undocumented surface of an existing module (add a *Where it lives* row).
4. **The vault can be wrong.** It records what was true when written. If the code disagrees with a note, the code wins, and fixing the note is part of your change.
5. **After the change**, the write half below applies. Same session, while the reasoning is in your head.

### The hooks

Four hook events run in every repo the vault covers (Claude Code hooks, or the Hermes Agent adapter). All of them advise; none blocks.

- **SessionStart** prints a primer: where the vault is, how to query it, and whether notes need attention.
- **UserPromptSubmit** matches your prompt against note names, aliases and flags and names the notes to read. Once per session it also says "this sounds like a Decision" when a prompt reads like a ruling or a reversal.
- **PreToolUse** points at the owning note before you edit a documented file, or says "stub, nothing recorded yet".
- **Stop** reminds you, when the session changed code but the vault did not move, which notes those files belong to. `VAULT_STOP_NUDGE=quiet` silences it for one shell.
- **SessionStart after a compaction** reminds you to re-query the vault, because the notes you read have just left your context.

---

## The one rule

> **Every `[[link]]` carries a reason.**

```markdown
- [[Invoice]] — an order confirmation bills through `InvoiceService::create()`
```

not

```markdown
- [[Invoice]]
```

A bare link makes the graph a hairball: you can see two things touch but not how. The reason clause makes it a map, and the index turns the reasons into the blast radius beside every search hit. It is also the part that rots first. When the reason stops being true the link is a lie, and that is your signal to fix the note.

If you only do one thing from this skill, do this one.

---

## Trigger table

| What you changed | What to touch |
|---|---|
| **New module** | New note in `2 Modules/` from `_templates/Module.md` + a reasoned link from its `1 Domains/` note |
| **Enhanced an existing module** | That note's *How it works* / *Gotchas*; bump `updated`; promote `depth: stub → full` |
| **Behaviour spanning modules** | A `3 Flows/` note, **and** the reasoned link on *both* module notes |
| **New or changed third party** | `4 Integrations/` |
| **New convention, or a trap that will bite again** | `5 Platform/` |
| **A non-obvious why**: a client ruling, a reversal, a deferred refactor | `6 Decisions/` |
| **Renamed or removed a module** | Rename the note (Obsidian fixes inbound links) or set `status: deprecated`. **Never delete silently** |
| **A release reached the production branch** | `7 Releases/vX.Y.Z.md` + the reconcile sweep below |
| **A domain word got misread, or a new one appeared** | A term note in `9 Glossary/` from `_templates/Term.md`: what the word means *here*, and where it shows up. If a module already carries the name, its *What it is* is the definition instead |

Nothing about the canvas. `vault check --write` regenerates `World.canvas` from the notes.

**Most changes are one module getting better.** That is three edits: amend *How it works*, add a *Gotcha* if you just lost an hour to something, bump `updated`. Sixty seconds. Don't over-build it.

**Find the note before writing one.** `vault find <name>` tells you in a second whether one exists, and aliases count. A new note that duplicates an existing one is worse than no note, because now two things disagree.

---

## Structure

```
<vault>/
├── Home.md            ← entry point, including "Finding things"
├── World.canvas       ← the visual map (generated; never hand-edit)
├── 1 Domains/         ← business areas, grouped the way the product groups them
├── 2 Modules/         ← the citizens of the world
├── 3 Flows/           ← end-to-end journeys
├── 4 Integrations/    ← outside systems
├── 5 Platform/        ← cross-cutting conventions and traps
├── 6 Decisions/       ← why it is this way
├── 7 Releases/        ← which parts of the world moved per version
├── 8 Repos/           ← one orientation note per codebase
├── 9 Glossary/        ← one term note per word this codebase uses in its own way
├── _templates/        ← copy these
└── _meta/             ← Conventions, How to update, vault.json, local.md (optional),
                         Coverage.md, Vault Changelog.md, Attention.md (generated), views/,
                         index.json (generated, gitignored)
```

`_meta/vault.json` names the vault, lists the repos it covers (each with its `remote` or `path`, an optional `root` inside the checkout, the `watched` directories, its `production_ref` and an optional `version_log`), and holds the tuning knobs: `generic_dirs`, `noise_files`, `stop_window_hours` and the `tidy` thresholds. `VAULT_ROOT`, `VAULT_WATCHED`, `VAULT_WINDOW_HOURS` and `VAULT_STOP_NUDGE=quiet` override it for one shell.

---

## Frontmatter

```yaml
---
type: module              # module|domain|flow|integration|platform|decision|release|repo|term|meta
aliases: [Billing, INV]   # optional. Other names THIS note answers to; flat ONE-LINE list
status: shipped           # shipped|in-progress|planned|deprecated (decisions: accepted|open|superseded)
depth: full               # full|stub
repo: api                 # a key from `repos` in vault.json, or both
domain: Billing
since: v1.4.0             # the release it first shipped in, when known. Empty beats a guess
updated: 2025-01-31       # bump EVERY time you touch the note
flags: [FEATURE_X_ENABLED]
tags: [module, domain/billing]
---
```

Flat one-line `key: value` only. The tool and Obsidian's queries read it line-wise; nested YAML parses wrong in both.

**`status: shipped` means the code is on the production branch**, the `production_ref` in `vault.json`. Work that exists only on a staging or feature branch is `in-progress`, however finished it feels. Verify with `git merge-base --is-ancestor <sha> <production_ref>` **plus a content grep**; a commit in the history is not proof the feature is live.

**`status` and `depth` do different jobs.** `status: in-progress` means the code isn't on production yet. `depth: stub` means the note is thin. A shipped module with a stub note is the normal starting state.

**`status` is where honesty lives.** Because the vault is a separate repo you can write about work that is still on a branch. That is allowed, but the note must say `status: in-progress`, or mark the paragraph "(on `develop`, not yet on `main`)", or it claims something false about production. This is the failure mode that makes a whole vault untrustworthy. Take it seriously.

**Aliases** are other names of *this* note, never a related concept, with no `[[`, `]]`, `|` or `#` inside, and may not collide with another note's name or alias. `vault check` enforces this.

---

## Section order

Module and integration notes always use this order, so any two diff cleanly:

1. **What it is** — plain language, two or three sentences a non-engineer can follow
2. **Where it lives** — the paths table
3. **How it works** — in the order the code actually runs
4. **Connects to** — linked, with reasons
5. **Config & flags**
6. **Gotchas**
7. **History**

Don't add sections. If something doesn't fit, it is a *Gotcha* or its own `6 Decisions/` note.

**Paths are code-spans, not links**: `app/Services/PaymentService.php`. The vault points at code.

**The *Where it lives* table is what the hooks run on.** Real files only. First path in a cell fully qualified; siblings may be bare filenames. **Never a container directory** like `app/Services/`; `vault check` rejects it. **Only the owning note cites a file's full path.** Elsewhere write `PaymentService::capture()`, because a full path anywhere in a body also counts as ownership and would point the pre-edit hook at the wrong note.

**Gotchas must be specific.** "Be careful with totals" is worthless. "`Order::total()` returns minor units and the CSV export multiplies by 100 again if you hand it a float" is worth keeping forever.

**History** links the release note when one exists: `- [[v1.4.0]] — capture moved to a queued job`.

---

## Stub → full

Promote the first time you work on a module for real: fill *How it works*, add at least two reasoned links, list the actual gotchas, set `depth: full`, bump `updated`.

**Don't promote by padding.** A stub that is honestly thin beats a full note that is half invented. If you didn't learn enough to fill it, leave it a stub and say so.

---

## Release-cut reconcile

When a version reaches the production branch:

1. `vault release vX.Y.Z` prints the window since the previous release and the owning notes whose files moved. Create `7 Releases/vX.Y.Z.md` from `_templates/Release.md`.
2. List every module note the release touched, each with **what** changed.
3. Sweep for misses: a note whose `updated` predates the previous release but whose files moved in this one was skipped. Fix it now.
4. Record the commands the release needs (migrations, seeders, one-off patches) and the flags it flips.
5. Flip `in-progress` claims the release made true, after verifying each one.

`/lightkeeper:release vX.Y.Z` walks this.

---

## Verify before you finish

```bash
vault check --write
```

Works from any directory. It checks that every `[[link]]` resolves (aliases count); catches duplicate filenames, alias collisions, bare links, container-directory claims and malformed frontmatter; lists orphans and stale notes; regenerates `_meta/Coverage.md`, `_meta/Vault Changelog.md`, `_meta/Attention.md` and `World.canvas`; and rebuilds the search index. It exits non-zero on any problem and must exit 0 before you commit.

Then commit. The vault is its own git repo and needs its own commit:

```bash
git -C <vault> add -A && git commit -m "Payment: capture retries; Gotcha on webhook ordering"
```

Name the notes in the message. `vault log <note>` reads that history back, and `Vault Changelog.md` is built from it. The vault commit is separate from the code commit; whatever rule you follow for committing code still applies to the code repo.

---

## Catching up

If a session shipped code without updating the vault, **don't reconstruct from memory**. Read the changelog entry and the actual diff, then write what the code says. A note written from a hazy recollection is worse than a stub: a stub is honestly thin, a bad note is confidently wrong.

Other people's pushes have no hooks pointed at this vault. For those, use the **vault-sync** skill: `vault sync` reports everything since the last reconciled commit, grouped by owning note.

When the primer or `vault status` says notes need attention, use the **vault-tidy** skill.

---

## Vault vs agent memory

Your agent memory is private to one machine and invisible in Obsidian. **How the system works belongs in the vault**: mechanics, traps, rulings, what connects to what. Every session and every human sees it there. Memory keeps what is about working with this user: preferences, workflow, in-flight session state. When you catch yourself writing an architecture fact into memory, write the vault note instead, or as well.

---

## What does NOT go in the vault

- **Code.** Snippets only where the shape itself is the point.
- **The release log.** The repo's changelog owns release history and deploy commands; `7 Releases/` only records which parts of the world moved.
- **Secrets, credentials, personal data.** No keys or tokens, no real names, emails, phone numbers or account identifiers. The vault syncs to other machines.
- **Task lists.** Those live in your tracker.
- **Docs with an external audience.** Client guides, runbooks and API references stay in the repo's docs folder; the vault links to them.

---

If `_meta/local.md` exists in this vault, read it now and follow it. It holds this vault's own rules, and where they conflict with the generic ones above, local.md wins.
