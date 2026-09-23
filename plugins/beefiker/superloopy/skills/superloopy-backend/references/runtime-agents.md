# Runtime agents

Treat a model-selected tool call as an untrusted request. Schema validity helps transport; authentication and authorization must still be enforced by the application, gateway, service, and data store.

## Tool contract

Every runtime data tool must define and enforce:

- **Input schema:** typed fields, formats, semantic constraints, and rejected unknown fields.
- **Authorization context:** verified principal, roles or grants, audience, decision source, and policy version; never accept authority supplied by the model.
- **Tenant scope:** trusted derivation and behavior for absent, conflicting, administrator, and service identities.
- **Allowlisted operation:** permitted resources, fields, predicates, transitions, and side-effect class. Deny arbitrary SQL or unrestricted database credentials by default.
- **Result schema:** typed data, provenance, truncation or pagination state, and operation identity.
- **Timeout:** server-enforced deadline plus cancellation behavior.
- **Row, payload, and cost limits:** workload-specific caps, including connections, retries, and total tool calls where relevant.
- **Redaction:** fields suppressed from model context, logs, traces, errors, and evaluation datasets.
- **Audit event:** intent, principal, tenant, policy decision, tool and version, sanitized parameters, result status, operation ID, and trace ID.
- **Idempotency:** stable key, deduplication scope, durable outcome, and reconciliation path for writes.
- **Error shape:** typed invalid, unauthorized, forbidden, conflict, bounded, unavailable, and ambiguous outcomes with retryability stated explicitly.

Default credentials and deployed server capability to read-only and least privilege. Make write capability a separate, narrow operation with explicit policy. Short-lived credentials reduce exposure but do not replace object, operation, field, and tenant checks.

## Keep data from becoming authority

Keep retrieval separate and distinct from action. Retrieved records are untrusted data, including text, metadata, schema comments, search results, stored prompts, errors, and prior tool output. They may inform an answer but cannot widen tenant scope, change policy, choose a more powerful tool, supply credentials, or approve a side effect. Preserve provenance and surface conflicting or low-confidence evidence.

Natural-language data intent can remain ambiguous after a query parses or succeeds on one fixture. For consequential decisions, clarify the interpretation or bind it to a reviewed semantic contract with explicit dimensions, filters, time range, units, and expected postconditions.

## Consequential actions

Require approval before a consequential or production write unless an authorized owner has already approved an equivalently specific policy envelope. The approval must show the actor, tenant, operation, target, material parameters, expected effect, and expiry. Place the approval checkpoint before execution; resumable runtimes must not replay the side effect on resume.

On timeout or disconnect after a write may have started, return an ambiguous error and reconcile by operation ID before any retry. On authorization, tenant, policy, or scope uncertainty, deny. On bounds exhaustion, cancel and request a narrower operation. Record attempted boundary crossings without reproducing sensitive content.
