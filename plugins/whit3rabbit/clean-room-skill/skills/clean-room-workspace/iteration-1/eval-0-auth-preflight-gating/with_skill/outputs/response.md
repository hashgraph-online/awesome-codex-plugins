I'm going to run this through the clean-room workflow, which is the right tool for an authorized reverse-engineering / behavior-compatible rewrite. But I can't start reading source or writing Go yet. The skill has hard gates that come first, and right now several of them fail. Let me be upfront about what I found and what I need before any work begins.

## First, an honest read of the request

You said the goal is to rebuild a competitor's tool "so ours behaves the same but we own the code and avoid copyright problems." I want to be clear about what this workflow does and does not do:

- It **can** help you build a clean, behavior-compatible reimplementation by separating source analysis from clean specification and clean implementation, with an audit trail.
- It is **not legal advice and is not a safe harbor.** A clean-room process reduces copyright-copying risk; it does nothing for patents, trademarks, trade secrets, or the terms of the license/EULA you obtained the competitor's tool under. "Avoid copyright problems" is a legal conclusion I'm not in a position to certify. You need your own sign-off that you are authorized to do this.

So before anything else: **who authorized this, and on what basis are you allowed to analyze and reimplement this competitor's source?** This goes in the record as the authorization statement; it's a required gate, not a formality.

## What I checked (run-state discovery)

I did read-only discovery before touching anything:

1. **The source path doesn't exist.** There is no `~/src/flowpack`, no `~/flowpack`, and in fact no `~/src` directory at all on this machine. I'm not going to invent a source tree. Either the clone is somewhere else or it hasn't landed yet, so point me at the real path.

2. **There's an existing, unrelated clean-room project on disk** at `~/Documents/CleanRoom/proj-924a1bae/` (task `task-be0634c2`). That one targets a TypeScript-to-Rust conversion of a different project (`claude-code-build1`). It is **not** your flowpack task, so I will not resume or touch it. Your flowpack work would be a brand-new task. I'm flagging it only so you know I saw it and deliberately left it alone.

3. **No preflight goal contract exists for a flowpack task.** That's the gate I have to clear before source discovery or implementation.

## Why I'm stopping here

The clean-room skill requires, in this order: (1) a `preflight-goal.json` that records your real intent and the destination contract, (2) a confirmed authorization/source/destination scope, and (3) separated workspaces for contaminated source vs. clean specs vs. clean code. I can't fill any of those in from guesses, and I'm explicitly not allowed to infer your end goal or target stack from the source contents. So this is a stop-and-ask point.

## What I need from you to proceed

**Blocking:**

1. **Authorization** — Confirm you (or someone) authorize this clean-room analysis and reimplementation of flowpack, and on what basis (you have a license that permits it / it's open source under a compatible license / internal legal sign-off / etc.). One sentence is fine, but I need it on the record.
2. **Source location** — The actual path to the flowpack clone, since `~/src/flowpack` isn't there. Also: do you know flowpack's own license? It materially changes what's safe to do.
3. **End goal** — Which of these is it: a behavior-compatible port, a CLI/API-compatible clone, a from-scratch clean reimplementation, or spec/test generation only?

**Needed to fill out the preflight contract (I'll assume sensible defaults and mark them as assumptions if you don't specify):**

4. **Target stack** — You said Go. Confirm: Go (module/`go.mod`), standard `testing`, any required minimum Go version or frameworks?
5. **Exactness boundary** — What must match exactly: CLI flags, command names, config file formats, output/serialization formats, exit codes, error messages? Everything else stays behavior-only.
6. **Feature policy** — Strict parity with flowpack, or are there features you want to drop or add?
7. **Dependency & license policy** — Default I'll use: prefer the Go standard library, allow MIT/Apache-2.0/BSD dependencies, block GPL/AGPL unless you approve, and license your output as (your choice, e.g. MIT or Apache-2.0).
8. **Controller mode** — Attended (I pause at each gate for your review) or unattended (bounded autonomous run)? I default to attended unless you tell me otherwise; unattended also requires a fully confirmed preflight with no open questions.
9. **Output location** — Default artifact/task root `~/Documents/CleanRoom/<new-project>/tasks/<task-id>/` with a shared `implementation/` root for the clean Go code. The clean code never goes into the flowpack source tree.

## What happens once you answer

Once authorization and the source path are confirmed, I'll bootstrap a fresh project/task (via `clean-room-skill init`, not by hand), create and validate `preflight-goal.json`, then run source-index preflight over the flowpack tree. From there the workflow keeps three things strictly separated: a contaminated side that reads flowpack and writes neutral behavioral specs, a sanitizer pass that strips identifying material, and a clean side that plans and writes the Go implementation from those specs only. The clean Go code is built from behavior specs, never by translating flowpack's source line-by-line, which is the whole point of the separation.

Give me items 1–3 at minimum and I'll start the preflight.
