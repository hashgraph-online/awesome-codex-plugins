# Reuse, compose and extend the example library

Use this when building a new bot feature, choosing examples, or adding a scenario
the library does not cover. Small wording fixes do not need this workflow.

## Find before writing

1. Resolve the **skill root** (the folder containing this SKILL.md) and the **user's
   project root** separately. Never assume the current directory is the skill root.
2. Search `recipes/use-cases.json`, or run from the skill root:
   `python scripts/example_library.py --query "event waitlist" --json`.
   Search supports EN/RU intent words and `--context private|group|channel|inline|business|mini-app`.
   It is a deterministic substring search, not semantic search; try synonyms on a miss.
3. Read the returned recipe's state map, failure paths and evidence, then the relevant
   functions/tests. `recipes/manifest.json` names executable files; `use-cases.json`
   groups products; `registry.json` tracks API changelog coverage. They are different indexes.
4. Identify the missing behavior. Choose **reuse** (same invariant), **compose** (several
   known flows) or **extend** (a new invariant). Explain the choice in one short paragraph.
   Do not add features just because a catalog row mentions them.

## What to reuse

| Need | Existing implementation | Adaptation boundary |
|---|---|---|
| Versioned private menus, Back, owner checks | `examples/python/tgkit/flows.py` / `examples/ts/usecases/flows.ts` | Use the host project's equivalent if present; preserve handler contracts. |
| Buttons, callback byte limit and i18n | `btn`, `kb`, `pack`, `I18n` in `flows.py` | Preserve routing and translate product copy. |
| Domain models for intake, events, jobs, queues | `examples/python/tgkit/journeys.py` | Teaching models, single process; production needs transactional persistence. |
| Private callback panel for those models | `examples/python/tgkit/journey_panel.py` | Optional example adapter, not a new mandatory framework. |
| Single-operation streaming, Stop | R01 and R27 | Preserve terminal-state races when porting SDKs. |
| Shared vs personal group content | R04, R28, R46 | Do not port a private panel to a shared message verbatim. |
| Offline transport and failure simulation | `examples/python/tgkit/transport.py` | Keep FakeTransport in tests; live transport is a separate integration. |
| Widgets | `examples/widgets/_kit/` and R50–R56 | Check current production contexts and keep a text fallback. |

Read functions before importing them: these are examples, not a versioned package API.
`OnceStore`, `Scheduler`, `ScreenFlow` sessions and R80–R87 records use process memory;
they do not provide crash recovery, distributed locks or network exactly-once delivery.
For durable business operations, commit state and an outbox intent together, enforce
unique business IDs, and reconcile unknown delivery outcomes. Do not cache success before
an external call has actually completed.

## Extend inside the user's project

Implement the new flow in the user's repository, following its architecture; keep the
installed library unchanged. Copy only the helpers the project lacks and keep the MIT
attribution on copied source. In another language, port the **behavior and failure tests**
with native types/SDK calls; R80–R87 exist only in Python.

A new vertical often needs composition: recruitment = search + lead intake + private file
job + status card; a café = menu/order + booking + reminders; paid community = payment
entitlement + membership lifecycle. Verify cross-flow ownership, identifiers and cancellation
instead of connecting examples only by button labels. Keep backend seams explicit (CRM,
calendar, file worker, payment provider, moderation executor): a fake response is never
production-ready.

## Evidence levels

- **Documented:** behavior described; nothing executable proved.
- **Offline model/contract:** deterministic tests and captured JSON pass.
- **Live API:** calls accepted by a dedicated test bot, with dated evidence.
- **Client verified:** named client/version/context inspected with dated evidence.

Record an unresolved gap in the catalog instead of inventing support.
