# Security

## Threat Model

Waggle is a local-first memory system. The primary assets are:

- transcript text stored in `transcript_records`
- extracted graph nodes and edges
- exported `.abhi` files
- OAuth tokens used for Google Drive sync

The main risks are:

- accidental export of secrets copied into conversation transcripts
- sharing an unencrypted `.abhi` file outside the local machine
- embedding-model drift that causes inconsistent retrieval semantics across clients
- compromise of the local machine or user account that owns the Waggle DB

Waggle does not attempt to defend against a fully compromised local OS account. If an attacker can read your home directory, they can read the SQLite DB, config files, and any unencrypted exports.

## Current Protections

- `waggle-mcp doctor` flags mixed `embedding_model_id` values and supports `--fix` to re-embed stale rows to the current model.
- `waggle-mcp push` defaults to encrypted `.abhi` export before upload.
- CLI export paths scan transcript text for likely secrets such as API keys, JWTs, and password/token assignments.
- If likely secrets are found, export is refused unless `--force` is passed.
- `.abhi` content hashing is deterministic for unsigned, unencrypted exports, which makes tampering and drift easier to detect.

## Secret-Scan Behavior

The export guard is heuristic, not perfect. It currently looks for patterns such as:

- OpenAI-style keys
- Anthropic keys
- GitHub tokens
- Google API keys
- AWS access keys
- JWTs
- obvious password or token assignments

False positives are possible. False negatives are also possible. Treat the scan as a safety net, not a full DLP system.

## Sharing Guidance

- Prefer `waggle-mcp push` over manually exporting and uploading files yourself.
- Treat `waggle-mcp share` as a link-sharing operation for a file that should already have been encrypted at export time.
- Use `--force` only after reviewing the export scope and intentionally accepting the exposure risk.
- If you need portable sharing without revealing raw transcript content, use redaction and narrow export scope first.

## Model Migration UX

If you change `WAGGLE_MODEL`:

1. Run `waggle-mcp doctor`
2. If mixed model IDs are reported, run `waggle-mcp doctor --fix`
3. Wait for the re-embed pass to complete
4. Re-run `waggle-mcp doctor` and confirm the store is consistent

This keeps shared DBs coherent across clients after model changes.
