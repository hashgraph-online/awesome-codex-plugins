# Threat checklist: STRIDE plus agent threats

Walk every trust-boundary crossing and every entry point through this list. For each prompt, ask whether an attacker from your capability list can make it happen at this point. Write a threat only when you can describe the abuse path hop by hop.

## STRIDE

**Spoofing (pretending to be someone else)**
- Can a caller reach this point without authenticating, or with a token meant for another service or audience?
- Are identities taken from a client-controlled field (header, body, JWT claim not verified, `X-Forwarded-For`) instead of the verified session?
- Can a webhook be forged because its signature is not checked, or checked with a non-constant-time compare, or the timestamp is not bounded?
- Can an agent act under the user's identity on input the user never saw?

**Tampering (changing data or code without authority)**
- Can the caller change an object they should only read, or change fields (role, owner, price, tenant ID) through mass assignment?
- Is data integrity-checked when it returns from an untrusted store (client storage, cookies, cache, queue)?
- Can a lower-trust party alter build inputs: lockfiles, CI workflow files, scripts invoked by CI, container base images, MCP server config?
- Can retrieved content or a tool result rewrite an agent's plan, memory, or config?

**Repudiation (acting without a trace)**
- Is the security-relevant action logged with actor, target, and outcome, in a log the actor cannot edit?
- For agent actions, does the log record which inputs (prompt sources, tool results) led to the tool call, so an injected action can be traced to its source?

**Information disclosure**
- Can the caller read another user's or tenant's data by changing an ID, path, or filter?
- Do errors, logs, traces, or analytics carry secrets, tokens, PII, or full prompts containing user data?
- Can the model be induced to repeat system prompt contents, other users' data from shared memory, or secrets present in its context?
- Can an agent exfiltrate through a side channel: a URL it fetches, an image it renders in markdown, a link it writes into a ticket?

**Denial of service**
- Is there an unbounded input (size, count, recursion depth, regex backtracking, decompression ratio)?
- Can a caller trigger expensive work (model calls, GPU jobs, fan-out) without a rate or spend limit?
- Can an agent be led into a loop of tool calls with no step or cost cap?

**Elevation of privilege**
- Does any path let a caller reach a capability their role lacks: admin endpoints, internal services via SSRF, the host via command or template injection, code execution via deserialization?
- Does the agent hold credentials broader than the task needs, so any successful injection inherits them?
- Can a PR from a fork run with repository secrets or write tokens?

## Agent-specific threats

**Indirect prompt injection.** Content the model reads (documents, web pages, emails, issues, tool results, MCP tool descriptions) carries instructions that the model follows. Check: which tools are available in the same call that reads untrusted content, and could any of them cause harm if invoked with attacker-chosen arguments?

**Tool misuse through confused deputy.** The model calls a legitimate tool with arguments the attacker chose. Check: does each tool enforce authorization itself, using the end user's identity, or does it trust whatever the model passes?

**Excessive agency.** The agent has tools or scopes it does not need for this task (write access when it only reads, a shell when it only needs a search API). Check: list every tool and scope at each call site and the task that needs it.

**Unvalidated model output as instructions or code.** Model output is executed as SQL, shell, code, config, or a plan another agent runs. Check: is the output parsed against a strict schema, and are values bound as parameters instead of concatenated?

**Memory and cache poisoning.** One session writes content into persistent memory, a vector store, or a shared cache that a later session, possibly another user's, reads as trusted. Check: is memory partitioned by user or tenant, and is stored content marked with its source and trust level?

**MCP server trust.** A third-party MCP server's tool descriptions are read by the model and can carry instructions; its results are untrusted; a server added to config can be swapped or updated upstream. Check: pinned versions or hashes, the credentials each server receives, and whether description changes are reviewed.

**Cross-agent propagation.** One agent's output becomes another's input (planner to executor, summarizer to actor). An injection in the first hop arrives at the second hop looking like trusted internal text. Check: does each hop treat upstream model output with the trust level of the least-trusted content that produced it?

**Data exfiltration through rendering.** The model emits markdown images, links, or HTML that the client renders, sending data to an attacker URL in a query string. Check: does the client render model output, and is outbound fetching from rendered content restricted to an allowlist?

**Spend and resource abuse.** An attacker drives model or tool usage to run up cost or exhaust quota. Check: per-user and per-session caps on tokens, tool calls, and wall time.

**Human-confirmation bypass.** A confirmation prompt exists but shows a summary written by the model, so injected content can misdescribe the action. Check: does the confirmation show the literal action and arguments?

## Supply chain and pipeline

- New or changed dependencies: who publishes them, are they pinned, do they run install scripts?
- CI workflows: which events trigger them, which secrets and token permissions they get, and whether untrusted PR content (titles, branch names, file contents) is interpolated into shell steps.
- Deploy credentials: which jobs hold them, and can a non-main branch reach those jobs?
