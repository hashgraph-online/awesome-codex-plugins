# Pattern index

All 54 tool design patterns, grouped by the skill that owns them. Use this to find the
skill for a named pattern.

## tool-design (classification and cross-cutting rules)

| Pattern        | Intent                                                    |
| -------------- | --------------------------------------------------------- |
| Tool           | The atomic callable unit an agent invokes to perform work |
| Query Tool     | Read-only retrieval without side effects                  |
| Command Tool   | Performs actions with side effects                        |
| Discovery Tool | Reveals available operations, schema, or capabilities     |

The three axes (maturity, integration type, access pattern) and the four cross-cutting
concerns (machine experience, tool DAGs, error-guided recovery, security boundaries)
are also covered here.

## tool-design-interface

| Pattern            | Intent                                                     |
| ------------------ | ---------------------------------------------------------- |
| Tool Description   | Descriptions optimized for model comprehension             |
| Constrained Input  | Enums, ranges, and validation limit inputs to valid values |
| Smart Defaults     | Fewer required parameters through sensible defaults        |
| Natural Identifier | Accept human-friendly identifiers, resolve internally      |
| Mutual Exclusivity | Enforce exactly-one-of parameter constraints               |
| Performance Hint   | Guide agents toward efficient usage                        |
| Parameter Coercion | Accept flexible formats, normalize internally              |

## tool-design-output

| Pattern                  | Intent                                                 |
| ------------------------ | ------------------------------------------------------ |
| Response Shaper          | Transform raw responses into agent-friendly shapes     |
| Token-Efficient Response | Minimize size while keeping essential information      |
| Paginated Result         | Cursor-based pagination for large result sets          |
| Progressive Detail       | Summary by default, full detail on request             |
| Next-Action Hint         | Suggest what the agent should do next                  |
| GUI URL                  | Links to view or edit results in a web interface       |
| Partial Success          | Mixed success and failure results for batch operations |
| Resource Reference       | Point to external data by URI instead of embedding it  |
| Canonical Tool Model     | Standard data models across the tool ecosystem         |

## tool-design-errors

| Pattern               | Intent                                                   |
| --------------------- | -------------------------------------------------------- |
| Recovery Guide        | Actionable errors that say how to fix the problem        |
| Error Classification  | Retryable versus permanent versus user input versus auth |
| Confirmation Request  | Ask for clarification when input is ambiguous            |
| Fuzzy Match Threshold | Auto-accept confident matches, confirm uncertain ones    |
| Graceful Degradation  | Partial results when the full operation is not possible  |
| Fallback Tool         | Alternatives when the primary tool is unavailable        |

## tool-design-execution

| Pattern                | Intent                                                 |
| ---------------------- | ------------------------------------------------------ |
| Synchronous Execution  | Immediate request-response execution                   |
| Async Job              | Long-running operations with job ids and polling       |
| Idempotent Operation   | Safe to retry with identical results                   |
| Transactional Boundary | All-or-nothing execution for multi-step operations     |
| Compensation Handler   | Undo completed steps when a multi-step operation fails |
| Timeout Boundary       | Maximum execution time with graceful termination       |

## tool-design-security

| Pattern           | Intent                                                    |
| ----------------- | --------------------------------------------------------- |
| Secret Injection  | Credentials injected at runtime, never through the model  |
| Permission Gate   | Access control enforced in code, not prompts              |
| Scope Declaration | Required OAuth scopes declared per tool                   |
| Audit Trail       | Every invocation logged for security and debugging        |
| Identity Anchor   | Establish user identity and context at session start      |
| Session Context   | State maintained across tool calls in a conversation      |
| Context Injection | Relevant context injected without the agent requesting it |
| Context Boundary  | Scope limits on what tools can access or modify           |

## tool-design-composition

| Pattern              | Intent                                                     |
| -------------------- | ---------------------------------------------------------- |
| Abstraction Ladder   | The same capability at several levels of granularity       |
| Task Bundle          | Several operations combined into one tool                  |
| Batch Operation      | Several items processed in one call                        |
| Operation Mode       | Explore, preview, dry-run, and execute modes               |
| Tool Chain           | Explicit sequences of tool calls for complex workflows     |
| Scatter-Gather Tool  | Fan out to several sources, then combine                   |
| Tool Registry        | A catalog of available tools and capabilities              |
| Schema Explorer      | Structure revealed progressively through layered discovery |
| Dependency Hint      | "Call X before Y" guidance in descriptions                 |
| Capability Matching  | Find tools by intent, not just name                        |
| Health Check         | Verify availability before relying on a tool               |
| Tool Gateway         | One interface to several tool backends                     |
| Tool Adapter         | Legacy APIs wrapped as agent-friendly tools                |
| Canonical Tool Model | Shared data models (also listed under output)              |
| Tool Versioning      | Several tool versions coexisting                           |

## Quick reference by question

| Question                    | Patterns                                                     |
| --------------------------- | ------------------------------------------------------------ |
| What kind of tool?          | Tool, Query, Command, Discovery                              |
| How is it called?           | Description, Constraints, Defaults, Natural Ids, Coercion    |
| How is it found?            | Registry, Schema Explorer, Dependency Hint, Capability Match |
| How does it compose?        | Abstraction Ladder, Bundle, Batch, Mode, Chain, Scatter      |
| How does it execute?        | Sync, Async Job, Idempotent, Transactional, Compensation     |
| What does it return?        | Shaper, Token-Efficient, Paginated, Progressive, Hints       |
| How is context managed?     | Identity, Session, Resource Reference, Injection, Boundary   |
| How does it recover?        | Recovery Guide, Classification, Confirmation, Degradation    |
| How is access controlled?   | Secret Injection, Permission Gate, Scopes, Audit             |
| How does it fit the system? | Gateway, Adapter, Canonical Model, Versioning                |
