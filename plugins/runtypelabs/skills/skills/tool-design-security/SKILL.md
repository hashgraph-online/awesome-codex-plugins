---
name: tool-design-security
description: 'Design tool identity, credential injection, authorization, tenant scope, and audit boundaries.'
user-invocable: true
argument-hint: '[tool or toolkit whose trust boundary to design]'
---

# Tool Security and Context Design

Prompts express intent; code enforces rules. An agent under prompt injection will try
to call the wrong tool with the wrong arguments and will produce a persuasive reason
for doing so. The only defenses that hold are the ones the tool layer enforces without
consulting the model.

## Procedure

1. **Name the principal.** Who is the tool acting as: a user, a service account, an
   organization? Where does that identity come from (session, token, context object)?
2. **Route every credential through injection.** No secret, token, or key is ever a
   model-visible parameter.
3. **Write the permission check in code**, before the operation, for both the action
   ("can this principal delete users") and the target ("this user, in this org").
4. **Declare scopes** per tool and pre-check them.
5. **Fix the boundary**: tenant, root path, allowed hosts, quotas.
6. **Log every invocation** with redacted parameters.
7. **Decide what context to inject** automatically (team, timezone, environment) and
   what the agent must establish itself through an identity anchor.

## Rules with examples

### Secrets never pass through the model (Secret Injection)

Before (the key is in the schema, so it is in the prompt, the trace, and the transcript):

```json
{
  "name": "call_api",
  "parameters": { "apiKey": { "type": "string" }, "endpoint": { "type": "string" } }
}
```

After (the key is resolved from server-side context at execution):

```json
{
  "name": "call_api",
  "parameters": { "endpoint": { "type": "string" } },
  "config": { "headers": { "Authorization": "Bearer {{secret:SERVICE_API_KEY}}" } }
}
```

Store credentials encrypted at rest, resolve them at call time, log the access, and
never log or return the value. If a parameter's only purpose is to carry a credential
or a trust decision, it is not a parameter.

### Access control lives in code (Permission Gate)

Check permissions at the top of execution, on the principal from context, not from any
argument the model supplied. Check the action and the target. Deny with a clear,
class-tagged error that names the required role, and log every denial.

```text
if "admin" not in principal.roles: deny(required="admin")
if target.orgId != principal.orgId: deny(reason="outside your organization")
```

A system prompt that says "never delete users" is a UX hint, not a control. Approval
gates on destructive or costly commands are a backstop for residual risk, not a
substitute for least-privilege tool selection; gate the few dangerous calls, not
everything, or the human learns to rubber-stamp.

### Declare the scopes each tool needs (Scope Declaration)

List the minimum required scopes and any optional ones in the tool definition and in
the description ("Requires `gmail.send`"). Pre-check before the upstream call and return
an `authRequired` error that names the missing scope and how to re-authenticate. Use
the narrowest scope that works; different tools in the same set can require different
scopes.

### Every call is logged (Audit Trail)

Record what (tool name, parameters with secrets and PII redacted), who (principal,
session), when, and the result (success or failure, duration, error class). Set a
retention period. This is how abuse is detected and how "why did the agent do that" is
answered later.

### The agent can ask who it is (Identity Anchor)

Provide a `who_am_i` discovery tool that returns the principal's id, name, roles,
permissions, and team or organization, and either recommend it as the first call in
tool descriptions or run it automatically and inject the result into the system prompt.
Cache it for the session. Downstream tools reference the ids it returns.

### State across calls is explicit (Session Context)

When tools share working state (current project, selected account, scope), store it
server-side against the session, expose tools to set and read it, expire stale sessions,
and echo the active context in results so the agent and the user can see what scope a
call ran in.

### Inject what the agent would not think to ask for (Context Injection)

Timezone, locale, region, and feature flags are supplied from context by default and
may be overridden by explicit parameters. Authorization scope (team, organization,
tenant) is also injected from context, but it is never overridable by the model: a tool
that needs to act on another team resolves that through the permission gate, not through
a parameter. Document what is injected, return the effective values in the response, and
expand machine ids to names where a human will read the result.

### Boundaries are enforced, not described (Context Boundary)

File tools resolve every path against a root and refuse anything outside it. Data tools
carry a tenant scope from context and never accept one from the model. Network tools
check hosts against an allowlist. Quotas and rate limits are applied in the tool layer.
Violations return a clear, logged error.

## Anti-patterns

- `apiKey`, `token`, `tenantId`, or `actAsUserId` as model-visible parameters.
- Authorization decided by reading the agent's stated reason for a call.
- Permission rules that exist only in the system prompt.
- A file tool that joins a user-supplied path without checking it stays under the root.
- Logging full parameters, including the secret that was injected.
- One broad OAuth scope for the whole server because it was easier.

## On Runtype

- **Secrets.** `{{secret:KEY}}` references resolve from the managed secret store at
  execution and are the only credential contract. They are honored in HTTP surfaces
  only: `external` tool `url`, `headers`, `body`, and auth, and the HTTP flow steps
  (`fetch-url`, `api-call`, `wait-until`, `paginate-api`). Never collect secret values
  in chat; hand users the dashboard intake URL from `get_secret_intake_manifest`, and
  create pending secrets with `create_secret` (no `value`) so the reference resolves
  once the owner fills it in.
- **Context injection.** `hiddenParameterNames` on a runtime tool (hidden parameters
  in the SDK) strip auth context and tenant ids from the model-facing schema and
  re-merge them from the execution context.
- **Permission gate.** `config.tools.approval.require` lists the tools that pause for
  a human; `timeout` bounds the wait; `requestReason` asks the model for a
  justification carried as the reserved `_approvalReason` parameter; `choices`
  (`alwaysAllow`, `alwaysDeny`) offers persistent decisions at the prompt. The reason
  is display-only and must never drive the decision. On client-token and Persona
  surfaces the account owner approves, not the end user.
- **Session context.** Durable working state belongs in `save_memory` /
  `recall_memory` (gated by `config.memory.enabled`) or in records, not in an
  ever-growing message array or a hand-rolled session store.
- **Audit.** Every tool call is traced on the run (`trace_execution`,
  `list_logs`), so tools only need to keep secrets out of their parameters and
  results.
- Read `get_platform_documentation(topic="agent-design")` for the approval-gate
  contract and `get_platform_documentation(topic="external-tools")` for the secret
  syntax rules.
