---
name: tokenchronicle-insights
description: Summarize private TokenChronicle usage reports and memory candidates while preserving source provenance and user approval boundaries.
---

# TokenChronicle Insights

Use only the user's configured TokenChronicle data directory.

Resolve the plugin root and use its exact matching signed executable under
`bin/<platform>/tokenchronicle/` when
present; never download or substitute a binary. If an installed plugin has no matching executable,
report that the platform client has not been published and stop. When a report refresh is needed, run
the matching executable's `memory-daily` command. An unpacked development bundle
may use its bundled Python package, but must select the host's Python launcher and environment syntax;
do not use a Unix `PYTHONPATH=... python3` command unchanged on Windows.

Run the read-only `readiness` command first. If TokenChronicle is not initialized or the first archive
is incomplete, switch to guided setup instead of analyzing an empty default location. If daily
protection is inactive, report that limitation with the analysis date.

1. Read derived reports before opening detailed conversation files.
2. Distinguish observed facts from inferred categories.
3. For work, life, domain, preference, or memory analysis, include source date, project scope, and confidence.
4. Treat personal preferences as candidates until the user approves them.
5. Do not modify Codex memories or upload source conversations.
