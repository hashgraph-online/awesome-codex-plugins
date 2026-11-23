# REST runner

## Use direct REST through the bundled runner

Substitute `{runner}` with the installed runner path from the host entry. Execute each shown line as one command. Fill each single-quoted slot literally and replace every internal `'` with `'\''`. An empty slot is `''`. Choose `{type}` from the fixed list below. Keep the command under 8,000 characters. Use the staged or local-file path for larger input. No prefix, command chaining or generated shell source.

```bash
bash {runner} probe '{path}'
```

`probe` reports the local type, absolute `PATH:`, and size or entry hints. For a large site near its limits, read the current limits through the same client.

```bash
bash {runner} limits
```

| Input | `{type}` and source | Existing REST operation |
|---|---|---|
| `.html` or `.htm` | `html-file --path` | `POST /api/html` as HTML |
| `.md` or `.markdown` | `html --path` | `POST /api/html` as Markdown |
| Other file | `file --path` | `POST /api/files` as multipart |
| Built folder with HTML | `site-dir --path` | `POST /api/sites` as a verified ZIP |
| Prebuilt site archive | `site-zip --path` | `POST /api/sites` as an inspected ZIP |
| Inline JSON | `json --text` or `json --run` | `POST /api/json` |
| Inline HTML or other text | `html --text` or `html --run` | `POST /api/html`, HTML for a whole document and Markdown otherwise |

The runner preserves non-UTF-8 HTML or Markdown source bytes by routing those files as multipart. UTF-8 HTML requests use the API's `verbatim` option to preserve supplied markup. `{ns}` is a 1–32 character lowercase name using letters, digits and hyphens. An explicit `''` password-file slot selects no password. A chosen password file must be an absolute path to an existing non-symlink regular file. Use the path only. The runner transfers its password through a private header file.

```bash
bash {runner} publish {type} --ns '{ns}' --ttl '{days}' --entry '{entry}' --delivery-mode '{delivery_mode}' --password-file '{password_file}' --path '{path}'
```

```bash
bash {runner} publish {type} --ns '{ns}' --ttl '{days}' --entry '' --delivery-mode '{delivery_mode}' --password-file '{password_file}' --text '{content}'
```

For long text or JSON, prefer an available file source where supported. Otherwise stage chunks at their existing line breaks so joining with one newline reproduces the exact content. Start with an empty run ID, then reuse the returned `RUN:` value. If a chunk cannot preserve the source within the command limit, use a local file or return the artifact.

```bash
bash {runner} stage --run '{run_id}' --text '{chunk}'
```

```bash
bash {runner} publish {type} --ns '{ns}' --ttl '{days}' --entry '' --delivery-mode '{delivery_mode}' --password-file '{password_file}' --run '{run_id}'
```

```bash
bash {runner} cleanup --run '{run_id}'
```

For eligible HTML and sites, append `--state '{state}'` when Page data was requested. The value is one JSON object. `{}` enables private visitor entries by default. For a requested owned hostname, use `--domain '{hostname}'` with existing applicable account owner proof as described in [custom domains](custom-domain.md). The REST runner uses the package's own User-Agent. Use the returned reader link exactly, including its trailing slash. Server notices may explain ineligible options or effective hosting changes. Handle receipt and credential storage through [ownership](ownership.md).

### Check inputs for MCP

```bash
bash {runner} preflight {local_type} --path '{path}'
```

Use `file`, `site-dir` or `site-zip` for `{local_type}`. Append `--entry '{entry}'` for a requested site entry and any actual `--password-file '{password_file}'` or `--owner-token-file '{owner_token_file}'` paths so the check can exclude those sources. For preflight, publish and update, repeat `--exclude-file '{protected_file}'` for other known protected files, using absolute paths. `CHECKED_PATH:` names the private checked snapshot. For a directory, `MCP_FILES_PATH:` names the checked JSON file list when all its files can be represented as text. Use only the checked snapshot or returned JSON with MCP. If the file list is absent, select another authorized path before sending a write. Clean up through `cleanup --run '{run_id}'` after consumption or cancellation.

### Choose proof or update a target

An ordinary create reuses the selected saved owner when exactly one can be resolved. With several owners, append `--owner-target '{saved_publication_url}'` after the owner chooses an exact saved reader or API link. Append `--owner-token-file '{owner_token_file}'` for owner-supplied proof from an absolute owner-only file. Use `--anonymous` for an explicitly fresh unsigned create. If the owner declines workspace history, use `--no-save --receipt-dir '{receipt_directory}'` after agreeing on the [protected file destination](ownership.md#prepare-for-a-new-anonymous-owner). Keep the token itself out of the command.

```bash
bash {runner} update {update_type} --target '{target}' --password-file '' --path '{path}'
```

Use the matching content type and the exact saved reader or official owner API URL. Append `--owner-token-file '{owner_token_file}'` when supplying separate proof for the target. Use `--text` or `--run` in place of `--path` for supported inline or staged input. The empty password-file slot preserves the existing password on replacement. Omit `state` for a content-only edit. For sites, omit `--entry` to retain the authorized metadata's existing entry; send `--entry` only for a requested entry change. An unresolved or missing prior entry stops replacement. The runner sends one owner-authorized PUT and keeps the selected identity. A missing or rejected update does not create a replacement.
