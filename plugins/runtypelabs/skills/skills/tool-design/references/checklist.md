# Pre-ship checklist for agent tools

Copy this into a review and mark each row. A row that fails is a finding; the pattern
column names the skill section that explains the fix.

| #   | Check                                                                                  | Pattern (skill)                                        |
| --- | -------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| 1   | Name is verb-object and unambiguous next to every sibling tool                         | Tool (tool-design)                                     |
| 2   | Type is explicit: read-only query, side-effecting command, or discovery                | Query / Command / Discovery Tool (tool-design)         |
| 3   | Description says what, when to use, when not to, what to call first, what it returns   | Tool Description (tool-design-interface)               |
| 4   | Every finite-valued string is an enum; numbers have ranges; formats have patterns      | Constrained Input (tool-design-interface)              |
| 5   | Required parameters are minimal; every optional one has a documented default           | Smart Defaults (tool-design-interface)                 |
| 6   | Human identifiers (email, name, handle) are accepted and resolved internally           | Natural Identifier (tool-design-interface)             |
| 7   | Exactly-one-of rules are documented and enforced at the start of execution             | Mutual Exclusivity (tool-design-interface)             |
| 8   | Cheaper or faster call paths are named in the description                              | Performance Hint (tool-design-interface)               |
| 9   | Common input variations (dates, numeric strings, single vs array) are normalized       | Parameter Coercion (tool-design-interface)             |
| 10  | Prerequisite and follow-up tools are named in the description                          | Dependency Hint (tool-design-composition)              |
| 11  | Result is flat, renamed for clarity, and not the raw upstream payload                  | Response Shaper (tool-design-output)                   |
| 12  | Expensive fields are opt-in; long text is truncated with a marker                      | Token-Efficient Response (tool-design-output)          |
| 13  | Lists are cursor-paginated with explicit `hasMore` and a bounded `limit`               | Paginated Result (tool-design-output)                  |
| 14  | Summary is the default; detail is available on request                                 | Progressive Detail (tool-design-output)                |
| 15  | Result names the suggested next tool and arguments where one exists                    | Next-Action Hint (tool-design-output)                  |
| 16  | Resources with a web UI return view and edit links                                     | GUI URL (tool-design-output)                           |
| 17  | Multi-item results report per-item status, counts, and a retry hint                    | Partial Success (tool-design-output)                   |
| 18  | Large payloads are returned as typed references, not embedded                          | Resource Reference (tool-design-output)                |
| 19  | Field names match the set's canonical model                                            | Canonical Tool Model (tool-design-output)              |
| 20  | Every error carries a class: retryable, permanent, user input, or auth                 | Error Classification (tool-design-errors)              |
| 21  | Every error says what, why, and the exact next call                                    | Recovery Guide (tool-design-errors)                    |
| 22  | Ambiguous matches return candidates and the call to make, never a guess                | Confirmation Request (tool-design-errors)              |
| 23  | Fuzzy resolution has documented accept, confirm, and reject thresholds                 | Fuzzy Match Threshold (tool-design-errors)             |
| 24  | Multi-source tools return what worked and name what failed                             | Graceful Degradation (tool-design-errors)              |
| 25  | Critical capabilities have a fallback order and report when it was used                | Fallback Tool (tool-design-errors)                     |
| 26  | Timeout is explicit and the timeout error names the async alternative if any           | Timeout Boundary (tool-design-execution)               |
| 27  | Work over the sync budget is an async job with status and result tools                 | Async Job (tool-design-execution)                      |
| 28  | Command tools state their idempotency guarantee and how it is keyed                    | Idempotent Operation (tool-design-execution)           |
| 29  | Multi-step commands are transactional or have compensation in reverse order            | Transactional Boundary, Compensation Handler           |
| 30  | No credential, token, or tenant id is a model-visible parameter                        | Secret Injection (tool-design-security)                |
| 31  | Permission checks run in code before the operation, on action and target               | Permission Gate (tool-design-security)                 |
| 32  | Required scopes are declared and pre-checked                                           | Scope Declaration (tool-design-security)               |
| 33  | Invocations are logged with redacted parameters and a result                           | Audit Trail (tool-design-security)                     |
| 34  | The agent can establish who it is acting as                                            | Identity Anchor (tool-design-security)                 |
| 35  | Injected context is documented and echoed; only preferences are model-overridable      | Context Injection (tool-design-security)               |
| 36  | Root paths, tenant scope, and host allowlists are enforced in code                     | Context Boundary (tool-design-security)                |
| 37  | Destructive or costly commands have a preview mode, an approval gate, or both          | Operation Mode, Permission Gate                        |
| 38  | Sequences the agent always runs together are bundled; per-item loops have a batch form | Task Bundle, Batch Operation (tool-design-composition) |
| 39  | The tool count stays within what the model can hold, or discovery tools exist          | Tool Registry, Capability Matching                     |
| 40  | Behavior changes ship as a new version with a migration note, not in place             | Tool Versioning (tool-design-composition)              |

## Checked for you on Runtype

When the tool set is built natively on Runtype, `validate_flow` and
`validate_product` report these rows as stable codes at save time. Fix the code and
the row passes; the remaining rows are still yours to review by hand.

| Row | Code                                  | What fires it                                                                                                                                            |
| --- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `RESERVED_TOOL_NAME`                  | A runtime tool's sanitized name collides with the platform's `runtype_set_state`                                                                         |
| 5   | `OPTIONAL_PARAM_IN_TOOL_TEMPLATE`     | An optional parameter is interpolated into an `external` tool's url, header, or body with no default, so an omitted argument ships a literal placeholder |
| 10  | `TOOL_CALL_STEP_UNKNOWN_CATALOG_TOOL` | A `tool-call` step names a catalog tool id that nothing answers to                                                                                       |
| 11  | `UPSERT_RECORD_SOURCE_NOT_JSON`       | A string-producing step feeds `upsert-record`, which needs a JSON object                                                                                 |
| 17  | `FETCH_CLASS_SWALLOWING_FEED`         | A fetch-class step with unset `errorHandling` feeds a transform or record write, so a dead API reads as an empty result                                  |
| 3   | `TOOL_STRATEGY_REQUIRED_MULTISTEP`    | Forced tool choice on a multi-step prompt, which returns empty output                                                                                    |
| 3   | `TOOL_STRATEGY_NONE_WITH_TOOLS`       | Tools attached but `toolCallStrategy: "none"` forbids calling any of them                                                                                |
| 3   | `PROVIDER_TOOLS_MIXED_OWNERS`         | Provider-native tools from two providers on one step; only the first-listed owner's tools run, the rest go inert                                         |
| 30  | `RUNTIME_TOOLS_INVALID`               | The `runtimeTools` block fails structural validation, including a reserved name                                                                          |

Enforced at runtime rather than at save time: the 30 s tool timeout (row 26), the
50-tool request cap and `tool_search` activation at 20 (row 39), `{{secret:KEY}}`
resolution (row 30), `hiddenParameterNames` (row 35), and approval gates (row 37).
