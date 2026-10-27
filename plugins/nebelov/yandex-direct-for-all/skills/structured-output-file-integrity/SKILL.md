---
name: structured-output-file-integrity
description: Use when saving, regenerating, reviewing, or transforming local TSV, CSV, JSONL, or table-shaped outputs where row count, row order, stable ids, headers, or schema must be preserved.
---

# Structured Output File Integrity

Use this skill for local structured files and pasted structured answers that must be saved without silent row loss, re-keying, reordering, schema drift, or invented rows.

This also applies to single JSON deliverables that contain arrays or object
collections, such as role results, scored candidates, media plans, validation
packets, and other schema-bound local artifacts. A JSON file does not become
safe just because it is one document instead of JSONL.

## Core Rule

When the user asks to save, repair, or transform an existing TSV/CSV/JSONL/table output, preserve the declared structure unless the user explicitly authorizes a structural change.

## Required Checks

When extracting a registry or other table from a multi-table document, identify
the intended container by its headings, expected columns and surrounding
context before comparing rows. The first table is not a default semantic match.
Zero or several matching containers means unresolved selection, not an empty
registry. Use a positional table index only after identifying the container,
then perform the key, schema and count checks below.

1. Identify stable row keys before writing: `candidate_id`, `row_id`, `id`, primary key, or a deterministic composite if no single key exists.
   For JSON arrays or object collections, identify the stable object key before
   editing, for example `candidate_code`, `role_id`, `slug`, `rank`, or a
   documented composite. Do not patch by broad text replacement when the same
   wording can occur in another object.
2. Preserve header fields, delimiter, row order, and every stable row key unless the current task explicitly permits changing them.
   Derive validation constraints from the declared format and actual source
   records. Do not reject established representations, such as same-origin
   relative API URLs, merely because a new checker assumed absolute URLs.
3. After writing, compare the source and destination:
   - header equality or documented approved header change;
   - row count;
   - stable row-key set;
   - duplicate key count;
   - order of stable keys when order matters.
   For scripted rewrites, write to a temporary sibling file first. Parse and
   validate its schema and keys before atomically replacing the original, so
   an exception during serialization cannot leave only a header or partial rows.
   When using Python `csv`, set `lineterminator='\n'` if the source uses LF;
   the writer's default CRLF otherwise changes line endings even when parsed
   values match.
   Before reading a TSV/CSV whose fields may contain long source evidence or
   serialized arrays, raise Python's default 131072-byte CSV field limit (for
   example, `csv.field_size_limit(sys.maxsize)`, or the largest supported
   value on that platform). A `field larger than field limit` parser error is
   not evidence of a damaged row; never skip or truncate that row to proceed.
4. Remove tool-wrapper or transcript contamination before saving: shell warnings, truncation notices, command banners, assistant prose, Markdown fences, pasted log headers, and other non-table lines must not be mixed into TSV/CSV/JSONL content. If such lines are present in the source transcript, filter them by schema and stable keys before writing.
5. Do not trust line count alone. A file can have the expected number of lines and still lose one source row, duplicate another, change keys, or include warning/prose lines in place of data.
   Calculate reported CSV/TSV volumes from parsed data records, excluding the
   header. Never use `wc -l` as the delivered record count: it includes the header
   and may count multiline fields as several lines. Describe uniqueness using
   the actual deduplication key, including language or other composite fields.
6. If the output came from a previous assistant answer, reconstruct the source row-key set from that answer or the original source file before saving.
7. If any key is missing, new, duplicated, reordered without approval, or replaced by a non-data line, stop and repair before reporting completion.
8. If a structured source has already been pinned by a passport, checksum, signed decision, or mutation journal, treat those exact bytes as immutable after the external write. Record later owner decisions, application outcomes, and status transitions in a separate decision or result artifact. Before editing such a source, check whether any existing passport or completed write references its digest; editing the pinned source would invalidate the audit chain.

For JSON object collections, after each write parse the file and compare the
target object and its siblings separately. Confirm the intended object changed,
unrelated sibling objects kept their key sets and substantive fields, object
count and ordering are still correct, ranking or shortlist counters still match
the collection, and every declared schema or media-format constraint still
passes. A parser pass alone is not enough if the wrong object was edited.

## Dictionary Matching and Reference Labels

Before building a reference set for classification, inspect actual dictionary values and their relationships, not just column names. A field named "brand attribute" can contain generic product descriptions and need not require a named brand. Do not mark such fields missing solely because another field is absent. Do not add properties from a dictionary label that the source does not establish. If several labels remain valid, record ambiguity or explicit acceptable alternatives before model evaluation. Freeze the reference before model calls; record later adjudication separately, and distinguish exact label agreement from factual correctness.

## Compact model classification transport

When a large row set is classified through a model, a compact batch response may use short batch-local codes instead of repeating long source phrases and global identifiers. Keep an immutable map from each code to the original stable row key and source text outside the model response. Rejoin only through that map, then verify one verdict per assigned row, no unknown or duplicate codes, original order when required, and explicit preservation of uncertain or abstained results. A shorter response reduces transport size; it does not establish semantic accuracy.

## Control Character Checks

For JavaScript builders in directories with spaces or non-ASCII names, convert `import.meta.url` or a relative file URL with `fileURLToPath` from `node:url` before using filesystem APIs. `new URL(...).pathname` remains percent-encoded and is not a valid local filesystem path for those directories. Verify the resolved input path exists before authoring.

When transforming TSV, CSV, JSONL, or pasted table output, inspect invisible control characters after writing. This includes carriage returns inside fields, mixed CRLF/LF drift, embedded tabs in TSV fields, null bytes, ANSI escapes, and other non-printing characters that can shift columns without changing visible row counts.

For TSV/CSV, run a parser-level check as well as a text-level scan. If a field append or merge introduces hidden `\r` characters, extra delimiters, or multiline field drift that was not explicitly allowed, block closeout and regenerate from the structured source rather than hand-editing visible rows only.

For JSONL, read records by actual newline boundaries (`for line in file` or an explicit `split('\n')` on a complete string). Do not use Python `str.splitlines()` to address JSONL rows: it also splits Unicode line-separator characters such as U+2028 that can occur legally inside a JSON string. Before batch writes, parse and count every selected record; if a transport tool truncates a batch, reduce only that batch size and resume from the first unconfirmed row.

## Reporting

Report the human-readable file path, row count, key field used, and whether the key-set comparison passed. Do not dump large table contents to chat.
