# Bead Anatomy — What Makes a Good Bead

## Table of Contents
- [Example Bead](#example-bead)
- [Required Elements](#required-elements)
- [Description Guidelines](#description-guidelines)
- [Anti-Patterns](#anti-patterns)

---

## Example Bead

A well-formed bead looks like:

```
ID: bd-7f3a2c
Title: Implement OAuth2 login flow
Type: feature
Priority: P1
Status: open

Dependencies: [bd-e9b1d4 (User model), bd-c4d5e6 (Session management)]
Blocks: [bd-a1b2c3 (Protected routes), bd-f7g8h9 (User dashboard)]

Description:
Implement OAuth2 login flow supporting Google and GitHub providers.

## Background
This is the primary authentication mechanism for the application.
Users should be able to sign in with existing Google/GitHub accounts
to reduce friction.

## Technical Approach
- Use NextAuth.js for OAuth2 implementation
- Store provider tokens encrypted in Supabase
- Create unified user record on first login
- Handle account linking for multiple providers

## Success Criteria
- User can click "Sign in with Google/GitHub"
- OAuth flow completes and redirects to dashboard
- User record created/updated in database
- Session cookie set correctly
- Logout clears session properly

## Test Plan
- Unit: Token encryption/decryption
- Unit: User record creation
- E2E: Full OAuth flow (mock provider)
- E2E: Account linking scenario

## Considerations
- Handle provider API rate limits
- Graceful degradation if provider is down
- GDPR compliance for EU users
```

---

## Required Elements

| Element | Purpose | Example |
|---------|---------|---------|
| **ID** | Unique identifier | `bd-7f3a2c` |
| **Title** | Clear, actionable | "Implement OAuth2 login flow" |
| **Type** | Categorization | `feature`, `bug`, `task`, `epic` |
| **Priority** | Importance (P0-P4) | `P1` (high) |
| **Status** | Current state | `open`, `in_progress`, `closed` |
| **Dependencies** | What blocks this | List of bead IDs |
| **Description** | Self-contained context | Markdown with sections |

---

## Description Guidelines

### Must Include

| Section | Content |
|---------|---------|
| **Background** | Why this exists, context |
| **Technical Approach** | How to implement |
| **Success Criteria** | How to verify done |
| **Test Plan** | Unit + E2E tests |
| **Considerations** | Edge cases, risks |

### Good Description Properties

1. **Self-contained** — Never need to refer back to original plan
2. **Self-documenting** — Future you can understand it
3. **Verbose** — More detail is better than less
4. **Actionable** — Clear what to do

### Description Checklist

- [ ] Background explains WHY
- [ ] Technical approach explains HOW
- [ ] Success criteria define DONE
- [ ] Test plan ensures QUALITY
- [ ] Considerations prevent SURPRISES

---

## Anti-Patterns

### Too Short

```
# BAD
Title: Fix login
Description: Fix the login bug
```

### Too Vague

```
# BAD
Title: Improve authentication
Description: Make auth better
```

### Missing Dependencies

```
# BAD
Title: Implement protected routes
Description: Add route protection
# No mention of auth dependency!
```

### Oversimplified

```
# BAD (lost complexity)
Title: Add user management
Description: CRUD for users

# GOOD (preserves complexity)
Title: Add user management with role-based access
Description:
## Background
Users need CRUD operations with granular permissions.
Admin users can manage all users; regular users can only
view/edit their own profile.

## Technical Approach
- Implement RBAC middleware
- Create admin-only routes
- Add ownership validation
- Handle permission errors gracefully
...
```

---

## Creating Beads with br

### Basic Creation

```bash
br create "Implement OAuth2 login flow" \
  --type feature \
  --priority 1 \
  --description "$(cat description.md)"
```

### Add Dependencies After

```bash
br dep add bd-7f3a2c bd-e9b1d4  # OAuth depends on User model
br dep add bd-7f3a2c bd-c4d5e6  # OAuth depends on Session mgmt
```

### Add Labels

```bash
br label add bd-7f3a2c auth backend security
```

### View Complete Bead

```bash
br show bd-7f3a2c
# or
br show bd-7f3a2c --json | jq
```

---

## Bead Types

| Type | Use For |
|------|---------|
| `epic` | Large features with many sub-beads |
| `feature` | New functionality |
| `task` | Non-feature work (config, setup) |
| `bug` | Defect fix |
| `chore` | Maintenance, cleanup |

---

## Priority Levels

| Priority | Meaning | When to Use |
|----------|---------|-------------|
| P0 | Critical | Blocking release, security |
| P1 | High | Core feature, important |
| P2 | Medium | Nice to have this sprint |
| P3 | Low | Future work |
| P4 | Backlog | Maybe someday |

---

## Dependency Best Practices

### Do

- Make ALL blocking relationships explicit
- Use bidirectional awareness (A blocks B, B depends on A)
- Keep dependency chains shallow when possible
- Validate no cycles: `br dep cycles`

### Don't

- Create circular dependencies
- Leave implicit dependencies
- Skip dependencies because "it's obvious"
- Create deep chains that serialize all work
