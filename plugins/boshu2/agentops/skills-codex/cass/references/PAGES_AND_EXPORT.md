# Encrypted Archives & HTML Export

> **One-liner:** `cass export-html` makes one shareable, optionally-password-protected HTML file. `cass pages` makes a fully-encrypted searchable archive that can be hosted on GitHub Pages with no server.

## Contents

- [HTML Export (One Session, Easy)](#html-export-one-session-easy)
- [Pages — Encrypted Searchable Archive](#pages--encrypted-searchable-archive-many-sessions-static-hosting)
- [Disaster Recovery](#disaster-recovery)
- [When to Use Which](#when-to-use-which)
- [Pitfalls](#pitfalls)

---

## HTML Export (One Session, Easy)

```bash
# Plain HTML
cass export-html /path/to/session.jsonl -o /tmp/session.html

# Password-protected (AES-256-GCM, PBKDF2 600k iter)
cass export-html /path/to/session.jsonl -o /tmp/session.html --password "use-strong-passwords"

# Read password from stdin to keep it out of shell history
read -rs PW && cass export-html /path/to/session.jsonl -o /tmp/session.html --password-stdin <<< "$PW"
```

The output is a **single self-contained HTML file**:
- Inlined CSS / JS, opens offline
- Tailwind + Prism enhanced via CDN when online (graceful degrade)
- Markdown rendering, syntax highlighting, role-colored bubbles

Use case: hand a teammate "the conversation that solved X" as one file, no installation needed.

---

## Pages — Encrypted Searchable Archive (Many Sessions, Static Hosting)

```bash
cass pages encrypt ~/.local/share/coding-agent-search/agent_search.db \
  --output /tmp/cass-archive \
  --with-recovery
```

This produces a directory:
```
cass-archive/
├── config.json           # key slots, payload metadata
├── payload/
│   ├── chunk-00000.bin   # AES-256-GCM encrypted, content-addressed
│   ├── chunk-00001.bin
│   └── ...
├── search/               # client-side search index
└── viewer/               # static HTML+JS viewer
```

Drop the whole directory under any static host (GitHub Pages, S3, Netlify). Visitors authenticate in the browser with the password (or recovery key) and get a fully searchable view of the corpus.

### Key Architecture

| Layer | Crypto |
|-------|--------|
| Per-slot KEK from password | Argon2id (64MB, 3 iter, parallelism 4) |
| Per-slot KEK from recovery secret | HKDF-SHA256 |
| Wrapped DEK | AES-256-GCM |
| Payload chunks | AES-256-GCM, per-chunk nonce |

### Multi-Slot Operations

```bash
cass pages key list --archive ./archive
cass pages key add-password --archive ./archive
cass pages key add-recovery --archive ./archive
cass pages key revoke --archive ./archive --slot 1
cass pages key rotate --archive ./archive --keep-recovery
cass pages key show-recovery --archive ./archive --qr   # printable backup
```

Constraints:
- Cannot revoke the only remaining slot
- Cannot revoke the slot you're authenticating with
- Revoked slot IDs are never reused

### Verification

```bash
cass pages verify --archive ./archive --check-integrity
```

Validates that all files in `config.json` exist and SHA-256 hashes match `integrity.json`.

---

## Disaster Recovery

| Scenario | Move |
|----------|------|
| Forgot password, have recovery key | `cass pages decrypt ./archive --recovery` |
| Corrupted `config.json` | Restore from backup (no backup = unrecoverable) |
| Corrupt payload chunks | `cass pages verify --archive ./archive` to identify; restore from backup |
| Need to share access | `cass pages key add-password` (requires existing auth first) |

Full recovery procedures: see source-of-truth at `/dp/coding_agent_session_search/docs/RECOVERY.md`.

---

## When to Use Which

| Goal | Tool |
|------|------|
| Share one conversation | `cass export-html --password` |
| Publish a redacted corpus on GitHub Pages | `cass pages encrypt --with-recovery` |
| Internal team archive | `cass pages` + corp SSO at the storage layer |
| Estate-planning backup of work history | `cass pages` + recovery key in safe deposit box |
| Quick markdown handoff | `cass export FILE --format markdown -o /tmp/x.md` (no encryption) |

---

## Pitfalls

- `cass pages encrypt` indexes the entire DB. For a 4M-message corpus expect 5–15 min and ~1.5x DB size in chunks.
- The static viewer requires JavaScript and ~50ms of in-browser key derivation per session load — slow on low-end devices.
- Recovery keys provide **full access**. Treat them like the password — print + safe deposit box, not in email.
- Never use `--password` with the literal password on the command line in a shared shell — use `--password-stdin` or password manager integration. Shell history leaks.
- `cass export` (markdown/json) is **plaintext**. Use `cass export-html --password` if confidentiality matters.
