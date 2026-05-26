# Library Update Ratchet

Use this reference for dependency update sessions where multiple packages might move.

## Update Loop

1. Snapshot manifest and lockfile hashes.
2. Research release notes for the target package or family.
3. Move one package or tightly-coupled family at a time.
4. Run the smallest meaningful test after each move.
5. Keep the update only when tests pass and behavior risk is understood.
6. Record incompatible versions as follow-up issues with exact failure output.

## Batch Rules

| Update | Batch? | Reason |
|---|---|---|
| Patch-only, same ecosystem | yes | Low-risk maintenance signal. |
| Minor version, same library family | maybe | Keep together when APIs are coupled. |
| Major version | no | Needs migration proof and rollback. |
| Security fix | no for critical | Keep evidence tight and fast. |

## Report Fields

- Package and old/new version.
- Release-note risk.
- Commands run.
- Files changed.
- Rollback command or restore point.

---

**Source:** Adapted from an external skill corpus / `library-updater`. Pattern-only, no verbatim text.
