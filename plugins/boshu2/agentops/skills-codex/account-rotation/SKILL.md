---
name: account-rotation
description: Switch coding-agent accounts on a usage/rate
---
<!-- TOC: Quick Start | Why the Route Exists | claude-acct (Mac+Claude) | caam (everything else) | Capture Discipline | Live-Session Caveat | Swarm Lanes -->

# account-rotation — switch coding-agent accounts on a rate limit

> **The moment:** you hit a usage limit on a Claude Max / Codex Pro / Gemini
> subscription and want to keep working on a fresh account, or you're spreading
> swarm lanes across accounts for parallel quota. **The tool depends on the host**
> — because the credential *layer* differs by OS+agent. This skill routes; the
> tools do the swap.

## Quick Start — route first

```
macOS + Claude            → claude-acct  (Keychain layer)
macOS + Codex/Gemini      → caam         (file layer)
Linux / WSL  + anything   → caam         (file layer)
```

## Why the route exists (the load-bearing fact)

caam swaps the auth **file** (`~/.codex/.credentials.json`, codex/gemini auth
files). Correct for file-based auth — **Codex, Gemini, and Claude-on-Linux.** But
current **Codex on macOS stores its token in the login Keychain** (`security`
service `Codex-credentials`) and *ignores* that file. So `caam activate`/`next`
for Claude on Mac are **no-ops** — they swap a file Claude doesn't read. That one
exception is the whole reason this router exists.

## macOS + Claude → `claude-acct` (Keychain swap)

A full Claude account on Mac = **two pieces**, both swapped together: the Keychain
**token** + the `~/.codex.json` **`.oauthAccount`** identity block (`claude auth
status` reads the email from the latter; a token-only swap leaves the identity
pinned to the last login → "only the current account works"). `claude-acct` swaps
both via `security add/delete-generic-password -A` (`-A` = no GUI prompt, so
headless workers don't stall) + a JSON splice of `.oauthAccount`.

```bash
claude-acct list                 # captured accounts → real email each maps to
claude-acct current              # which account a NEW claude starts on
claude-acct use <name>           # swap (token + identity)
claude-acct login <name> [email] # one-time capture (see Capture Discipline)
```
Tool: `dotfiles/bin/claude-acct`.

## macOS+Codex/Gemini & all Linux/WSL → `caam` (file swap)

caam is the adopted file-based rotator and is correct here. It self-documents
(there is intentionally no caam skill — the CLI is the doc):

```bash
caam status <tool>            # vault + health
caam next <tool>              # rotate to next non-cooldown account
caam use <tool> <profile>
caam --help                   # full surface
```
On bushido (Ubuntu) this is the **only** rotator you need — file-based auth means
caam's swap actually takes.

## Capture Discipline (the two traps — apply to both tools)

1. **Distinct token bytes ≠ distinct accounts.** OAuth re-issues a fresh token
   each login, so N logins to the *same* account produce N different hashes.
   Verify by **account email**, not token hash. (`claude-acct` warns on collision.)
2. **The browser captures whichever account the provider is signed into.** Email
   login-hints are ignored when a session exists. **Log out (or use a
   Private/Incognito window) before each capture login**, or it re-grabs the
   current account.

## Live-Session Caveat

A running agent process holds its token in memory; rotation changes what a **new**
process picks up, not the live session. To move the session you're in: rotate,
then **relaunch** the CLI. Exactly right for spawning swarm lanes.

## Swarm Lanes (the real unlock)

Parallel quota = put each lane on a different account **before** launching it:

```bash
# Mac (Claude)
claude-acct use acct-a && <spawn lane A>;  claude-acct use acct-b && <spawn lane B>
# Linux / Codex
caam use codex acct-a   && <spawn lane A>;  caam next codex      && <spawn lane B>
```
A dispatcher's limit-hit hook calls `claude-acct use` on Mac / `caam next` on
Linux, then re-dispatches the lane's work.

## Navi-rotate (the cross-model helper rotates a peer — trilateral)

In the trilateral (2 Claude builders + 1 Codex **Navi**), the Navi runs on a
DIFFERENT runtime/account, so it is UNAFFECTED by a builder's Claude rate limit —
making it the right agent to rotate a limited builder. `navi-rotate`
(`dotfiles/bin/navi-rotate`) wraps `claude-acct` with rotation-order + peer-relaunch
signaling, so the move is one repeatable command:

```bash
navi-rotate <peer-tmux-session> [--to <account>] [--dry-run]
# Navi: next account (claude-acct list order) -> claude-acct use <next>
#       -> am + atm signal the peer to relaunch.
```

Per the **Live-Session Caveat**: the swap lands on the peer's NEXT launch, not its
live session — continuity rides the durable substrate (worktree + bead + handoff),
so the peer resumes from its last bead on the fresh account. This is the repeatable,
cross-model-driven form of the dispatcher limit-hit hook above. Routed correctly:
the swap is always `claude-acct` for Mac+Claude (NEVER caam).
