# Core Philosophy

Read at the start of every session. These principles override anything in
the workflow that contradicts them.

- **Correctness within Constraints.** Implement the best possible solution
  within current VEF capabilities. When a feature cannot be fully realized,
  implement the best safe workaround the typed API supports and document the
  limitation in `.claude/tracking/limitations.md`.

- **Incremental Verification.** Test every function immediately after
  implementation. NEVER proceed with failing tests.

- **No Gate Skipping.** The phase gates (the Phase 3 three-agent
  simplification review and the Phase 4 critic checklist review) are
  mandatory. Run them as written even if the user is being terse, even if
  the work feels small, even if it slows iteration. Never offer to skip a
  gate; never call a gate optional. The only escape is the user explicitly
  saying "skip Phase N" by name, in which case do it and note the skip in
  `.claude/tracking/`.

- **Deep Debugging.** When a failure occurs, add diagnostic output to
  understand the "why" before attempting a fix. Always show actual test
  output.

- **Zero Tolerance for Hallucination.** Only report test results you have
  actually observed. Never assume success.

- **Fail Loud, Fail Early.** If any step fails — connectivity, bootstrap,
  build, test, install — stop immediately. Report the exact error and any
  paths or values checked. Do not proceed, do not guess at API signatures,
  do not fabricate values to keep going.

- **Typed C++ API Only.** Locate `vsql.h` and the `vsql/` subdirectory in
  the SDK during Phase 2 bootstrap. All implementation work goes through
  this typed API. If it is not present in the SDK, stop and flag this to
  the user before writing any implementation code. **Never read headers
  under any `abi/` directory** — those are internal server/protocol
  headers, not the extension interface. If you find yourself reading one,
  stop and return to the typed API headers.

- **Preview vs. Stable.** Within the typed API, headers under a `preview/`
  subdirectory are preview capabilities — documented but unstable across
  server builds. Everything else is stable. Design against stable headers
  when possible; note any preview API use in
  `.claude/tracking/limitations.md`.

- **VEF Extensions Only.** This skill builds VEF extensions only. If a
  requested capability is beyond what VEF currently supports, the answer is
  to implement the best workaround the VEF typed API allows, document the
  gap in `.claude/tracking/limitations.md`, and use the Phase 6 call to
  action to direct the user to file a VillageSQL issue or upvote an
  existing one. MySQL plugins (`INSTALL PLUGIN`, MYSQL_PLUGIN ABI) and
  MySQL server components (`INSTALL COMPONENT`, component service
  framework) are never a suggested alternative — they have different build
  systems and ABIs and are outside the scope of this skill entirely.

# Handling Scope Variations

- **Default:** Implement the full standard API.
- **Minimal requests:** Maintain all quality standards and the full
  workflow. Document in README: "Partial implementation. Missing: [list]."
- **PostgreSQL ports:** Implement every function VEF can support. Where VEF
  constraints prevent full compatibility, use the best workaround, document
  each gap in `limitations.md` immediately, and surface all gaps in the
  README.

# Principle: Process, Not API

The SKILL.md and all reference files in this directory encode **process
and principles, not API**. Any specific name appearing in this skill —
struct fields, constants, builder methods, header filenames — is
illustrative only and may be outdated. Always verify against live SDK
headers from Phase 2 bootstrap.

If you're writing code based on a name from this skill rather than a name
from the live headers, stop and re-read the headers.
