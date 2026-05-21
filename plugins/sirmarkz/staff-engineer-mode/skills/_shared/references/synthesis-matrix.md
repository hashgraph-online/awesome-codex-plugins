# Staff Engineer Mode Synthesis Matrix

This file records the normalized defaults used by the hand-authored skills. It is a navigation aid, not generated source of truth. The `SKILL.md` files carry the authoritative instructions.

| Theme | Normalized Default |
| --- | --- |
| Routing | Select one primary skill by engineering surface, event type, risk, and scope. Ask one question when confidence is low. |
| Architecture and interfaces | Prefer modular boundaries, explicit contracts, and ADRs before adding distributed complexity. |
| Reliability and resilience | Define user-visible reliability, bound failure domains, control dependency amplification, model tail latency, validate correctness properties, and prove recovery with evidence. |
| Delivery and quality | Make builds, config, automation, docs, fleet upgrades, and changes gradual, observable, reversible, tested, reviewed, and migrated with explicit evidence. |
| Operations and observability | Page only on urgent actionable user impact; use telemetry to explain impact and causality. |
| Data and workflows | Start from data semantics and contracts, then choose consistency, workflow, cache, database, pipeline, and ML controls. |
| Security and privacy | Map trust boundaries, cryptographic lifecycle, and data lifecycles to enforceable controls, least privilege, minimization, evidence, and verification. |
| Platform and infrastructure | Encode standards as reusable capabilities with desired state, policy, drift control, and operational responsibility. |
| Client and edge experience | Gate client releases on user-visible runtime quality, segmented telemetry, and rollback or forward-fix paths. |
| AI and experimentation | Gate AI-assisted development, model-backed workflows, and experiments with scoped authority, representative evaluation, metric trust, and reviewable evidence. |

## Cross-Cutting Rules

- Skills must stay technology-agnostic unless explicitly tied to a domain such as frontend, mobile, ML, or LLM applications.
- Vendor and tool references may appear as sources, but defaults must be expressed as capabilities and evidence.
- Competing source practices should be blended into one pragmatic default with explicit exceptions.
- Missing evidence is a blocker, exception, or follow-up route, not an acceptable claim.
