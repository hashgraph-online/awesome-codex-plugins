# Evergreen Technical Book Examples

Synthetic examples for splitting technical book content from companion resources.

## Book vs Companion Split

| Content | Put In Book | Put In Companion |
|---------|-------------|------------------|
| Why backups fail | Durable model and failure modes | Current backup tool commands |
| Reverse proxy concept | Request path diagram and tradeoffs | Provider-specific UI screenshots |
| Docker Compose example | Small annotated example | Full maintained compose files |
| Cloud pricing | Cost model and warning signs | Current pricing links and calculator |
| Security checklist | Principles and non-negotiables | Tool-specific hardening commands |

## Weak Treatment

```text
Click Settings, then Advanced, then Security, then Enable New TLS Mode.
```

**Problems**:
- UI path may drift.
- Reader learns little about the decision.
- The book looks stale when labels change.

## Strong Treatment

```text
Enable the setting that forces encrypted browser connections. The exact label varies by provider, so use the companion guide for current screenshots. The important check is that plain HTTP redirects to HTTPS before login.
```

**Why it works**:
- Keeps the durable safety point in the book.
- Points volatile UI detail to an updateable place.
- Gives the reader a verification criterion.

## Companion Resource Plan

| Resource | Purpose | Update Trigger | Owner |
|----------|---------|----------------|-------|
| `/guides/current-compose-files/` | Maintained configs for examples | Image or syntax change | Author |
| `/guides/provider-screenshots/` | Current UI walkthroughs | Provider UI changes | Author or contributor |
| `/checklists/server-launch.md` | Printable launch checklist | New safety requirement | Author |
| GitHub issues | Reader reports of drift | Any bug report | Maintainer |

## Wording For Versioned Examples

```text
This chapter uses Caddy 2.x as the concrete example because its configuration makes the underlying model visible. The pattern is the durable part: one public entry point, explicit hostnames, automatic certificate management, and a route to the private service. Current configs and alternatives live in the companion repository.
```

## Drift Audit Table

| Section | Half-Life | Risk | Move Or Keep |
|---------|-----------|------|--------------|
| "How DNS points to your server" | Durable | Low | Keep in book. |
| "Namecheap UI walkthrough" | Volatile | Medium | Move to companion screenshots. |
| "Use Ubuntu 24.04 LTS" | Semi-durable | Medium | Keep as tested baseline with date. |
| "This service is free" | Volatile | High | Verify before release or remove. |

## Stable Reference Pattern

```text
For current files, open the companion repository and use the folder named after this chapter. Each folder has a last-reviewed date and a short changelog.
```

This is more durable than scattering many deep links throughout a chapter.
