# Verification efficiency options

These options change presentation or the bounded order of already requested checks. They never create approval, execution, reuse, receipt, or completion authority.

## Reporting v1

Omitting `reporting` keeps raw streaming. The equivalent default is:

```json
{
  "version": 1,
  "format": "raw",
  "max_bytes": 65536,
  "context": {"enabled": false, "max_files": 2, "max_lines": 120}
}
```

Use `format: "actionable"` only when a compact unittest/pytest diagnosis is wanted. Click drains stdout and stderr from the original execution once, retains at most the configured 4–128 KiB per stream, and reports truncation or parser uncertainty. It does not alter argv or rerun the check. Local detail is owner-readable, expires after 24 hours, and is bounded by 128 files and 8 MiB. Context candidates come only from safe workspace-relative file/line output and still require a separate normal inspect claim; the runner does not read them automatically.

## Failure collection v1

Omitting `failure_collection` preserves fail-fast. The equivalent default is:

```json
{
  "version": 1,
  "mode": "off",
  "independent_sources": [],
  "max_extra_sources": 0,
  "max_extra_failures": 0,
  "start_window_ms": 0
}
```

`mode: "bounded"` requires at least two distinct evidence IDs that are also present in the submitted checks. The caller must know those sources are execution-independent. Allowed limits are one to three extra sources, one to three extra failures, and a 1–30000 ms window for starting the next source. The window is not a timeout for a command already running.

Click continues only after a supported parser classifies a real test failure. A failure inside one source stops the rest of that source. Cancellation, test setup/import/runtime error, unknown output, claim/state drift, protected Git change, environment change, executable change, or budget expiry prevents another source from starting. Every additional source boundary rechecks the current bindings. Automatic shard IDs are not inferred to be independent; if expansion changes the explicitly named identities, Click falls back to fail-fast.

After a repair, resubmit the original parent verification request. A previously passing sibling is reused only if the existing exact, dependency, or precommitted safe-change rules requalify it under the current conditions.

## Dashboard and whole-task evaluation

The dashboard keeps `절감 시간` (time saved from applicable prior successful check durations), `토큰 절감률` (token savings rate), and `전체 작업 효과` (whole-task effect) separate. The latter two accept only the allowlisted `click-task-efficiency-public` v1 format. Missing equivalent task boundaries or complete usage stays unmeasured; test time and output length are never converted to token savings.

Public screens and exports contain token ratios only. Raw usage, absolute token counts, logs, code, commands, paths, environment values, contracts, and credentials remain outside the public presentation. B0→B2 and N→B2, first use and prepared repeat, Evidence and Guarded, and different scenarios stay separate. Multiple scopes require an explicit selection.

For the full measurement and export contract in the source repository, see `VERIFICATION_EFFICIENCY.md`.
