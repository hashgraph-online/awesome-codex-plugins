# Suede Code: Grade-Only Worked Example

One change graded end to end in `--grade-only` mode, showing how the lanes combine into an overall letter and what the required upgrades look like. Illustration only: the rules live in SKILL.md.

**Historical snapshot:** written against an earlier release of this pack, when the grade-only pass shipped as its own skill. File sizes and line numbers below are frozen evidence from that run.

## Worked Example

A real grade, not a fictional one: this is the grade-only pass actually grading a real file from this repo: `mcp/suede-skills-mcp.mjs` (715 lines, the stdio JSON-RPC MCP server this skill pack ships). Read in full, then exercised at runtime (spawned the process, sent real JSON-RPC requests over stdin, read the stdout responses) before scoring. This is what the Output Format block looks like filled in, not a template.

```text
Simple explanation:
This file runs fine and doesn't have any dangerous bugs. It's a small local
tool, not something the public logs into or pays through, so the bar is
lower than an auth or payment file. One small paint-by-numbers gap: one
tool's reply doesn't get its text length capped like all the others do,
but that data comes from a file in this repo, not from a stranger, so it
can't be used to attack anything.

Usual breakdown:
Target: mcp/suede-skills-mcp.mjs (715 lines), suede-creator-skills repo,
branch main, clean working tree.
Change reviewed: full file (no diff, graded as a standing artifact, not a
PR), since the task was to grade a real file rather than a specific change.
Runtime surfaces: local stdio JSON-RPC MCP server. No network listener, no
auth, no payment, no database, no user-facing production route: it talks
to an MCP client over stdin/stdout on the machine that spawns it.

Grades:
Correctness: A
Security and permissions: A
Data and state: A
Suede truth: B
UX and release behavior: A
Tests and verification: B
Deploy readiness: A
Overall: A
Grade cap applied: none, surface is a local stdio MCP server, not
auth/payment/migration/public-API, so no cap lane applies.

Why:
Correctness: A. Traced every JSON-RPC method by hand and confirmed at
runtime: `initialize`, `ping`, `tools/list`, `tools/call`, `resources/list`,
`resources/read`, `prompts/list`, and `prompts/get` all returned the
expected shape. Unknown tool name, unknown resource URI, and unknown skill
name each produced correct, distinct error handling, `get_suede_skill`
with a bad name returns a tool-level `isError: true` result (per MCP spec,
since the tool ran but found nothing), while `resources/read` and
`tools/call` on to a genuinely unregistered name throw a JSON-RPC
`-32602 Unknown resource/tool` error, caught by the outer try/catch at
line 703-713 and serialized correctly. Verified live:
  - `tools/call get_suede_skill {name: "nonexistent-skill"}` ->
    `{"isError":true,"structuredContent":{"found":false}}`
  - `resources/read {uri: "suede://bogus"}` -> JSON-RPC error -32602
  - `tools/call {name: "bogus_tool"}` -> JSON-RPC error -32602
The 1 MiB input-buffer guard (lines 686-690) was exercised directly: sent
a >1 MiB unterminated chunk, confirmed it resets `buffer = ""` and emits
a clean `-32603` error, then confirmed the very next well-formed request
(`ping`) on the same connection still succeeds. No stuck state after the
overflow path.

Security and permissions: A. No secrets, no injected shell/SQL, no auth
surface to bypass (there is no auth: this is a local dev tool spawned by
an MCP client, same trust boundary as the process that starts it). No
user-controlled path construction; `catalogPath` is built from
`__dirname`, not request input. `boundedString` (line 27-30) caps every
tool argument that gets echoed into `structuredContent` at 2000 chars
before it goes back out, which is the right instinct for a JSON-RPC
server that will eventually take arguments from less-trusted callers.

Data and state: A. No database, no migration, no cache. `catalog.json` is
read once at module load (line 22-23) and treated as immutable static
data for the life of the process: no write path exists anywhere in this
file.

Suede truth: B. Minor inconsistency, not a false claim: `get_suede_skill`
(line 496-506) returns the matched skill's `description` and `useWhen`
straight from `catalog.json` into both `content` text and
`structuredContent.skill` without running them through `boundedString`,
while every other tool handler in the same function (lines 507-548) bounds
every argument-derived string it echoes back. Confirmed by reading: the
longest live `catalog.json` description is 1016 chars (suede-campaign-in-a-box),
so nothing is actually breaking today: this is a consistency gap that
would only bite if a future catalog entry grew past a client's tolerance
for an unbounded field, or if catalog.json ever stopped being pure
repo-controlled data. Named as a Required Upgrade below, not a blocker.

UX and release behavior: A. Every JSON-RPC error path returns a properly
shaped `{jsonrpc, id, error: {code, message}}` envelope (lines 671-680);
parse errors on malformed input lines are caught per-line (line 696-702)
without killing the buffer for subsequent valid lines; notifications
(messages with no `id`) are correctly treated as fire-and-forget and
never generate a response (line 707-709), matching JSON-RPC 2.0 spec.

Tests and verification: B. No committed test file or npm test script
exists for this MCP server specifically (`package.json` only lists the
`js-yaml` dependency, no test runner). Correctness here was verified by
manually spawning the process and sending real requests this session, not
by an automated suite that runs in CI. The repo does have
`scripts/validate-skill-pack.mjs` and a manual MCP QA checklist, which
cover catalog/skill-folder alignment but not this file's JSON-RPC
behavior directly. That's a real, bounded gap: not a blocker, since the
runtime behavior checked out clean by hand, but there's no regression net
if a future change breaks `tools/call` error shaping.

Deploy readiness: A. No env vars, no config, no build step: it's a
single `.mjs` file with one dependency (`js-yaml`, used indirectly via
the shared catalog tooling, not by this file itself... actually unused
by this file: confirmed no `js-yaml` import in suede-skills-mcp.mjs
itself, only `fs`, `path`, and `node:url`). Runs directly via
`node mcp/suede-skills-mcp.mjs` with zero setup, which matches what the
install docs describe.

Required upgrades:
1. Route `get_suede_skill`'s `content`/`structuredContent.skill` output
   through `boundedString` (or an equivalent bound on `description` and
   `useWhen`) for consistency with every other tool handler in the file:
   currently harmless since catalog.json is trusted static data, but the
   inconsistency is worth closing before this server's argument surface
   changes.
2. Add a small scripted smoke test (a checked-in version of the manual
   JSON-RPC exercise run for this grade) so `tools/call`, `resources/read`,
   and error-path shaping have a regression net instead of relying on
   manual verification each time.
3. No third required upgrade: nothing else surfaced.

Verification:
Checked: full file read; live process spawn with real JSON-RPC requests
over stdin covering initialize, ping, tools/list, tools/call (success and
two distinct error shapes), resources/list, resources/read (success and
error), prompts/list; 1 MiB buffer-overflow guard exercised directly and
confirmed recovery; catalog.json's longest description measured against
the unbounded echo path; grep confirmed no `js-yaml` import in this file.
Not checked: behavior under a real MCP client (Claude Code, Codex, etc.)
end to end, only raw stdio JSON-RPC was exercised directly; concurrent/
overlapping request handling under load; the `prompts/get` argument-
substitution paths for all five prompts (spot-checked `suede-copy-seo-audit`
only).
Ship gate: ship
```

This is what "genuine" looks like: every claim above ties to either a line
number in the file or a command actually run against it in this session,
not an invented test result or a guessed line number.
