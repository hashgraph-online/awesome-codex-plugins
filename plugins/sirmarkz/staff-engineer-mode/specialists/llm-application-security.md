---
name: llm-application-security
description: "Use when LLM prompts, retrieval, tools, model output, or generated actions cross security boundaries"
---

# LLM Application Security

## Iron Law

```
NO LLM TOOL OR DATA ACCESS WITHOUT A BOUNDARY MAP, LEAST PRIVILEGE, ABUSE-CASE EVALS, AUDIT, AND OUTPUT HANDLING
```

If the model can cause an action, that action needs an explicit boundary, least-privilege scoping, abuse-case tests (prompt injection, exfiltration, jailbreak, unsafe action), an audit trail, and contextual handling of the output before any sink consumes it. "Evals" here are adversarial cases, not happy-path quality checks.

## Overview

LLM applications move untrusted text across tool, data, and decision boundaries.

**Core principle:** treat prompts, retrieved content, tool outputs, and model responses as untrusted inputs; constrain what the application can do with them.

## When To Use

- The user is designing or building LLM prompt, retrieval, tool, output, action, or data flows that cross security boundaries.
- The user asks about prompt injection, tool permissions, retrieval boundaries, insecure output handling, sensitive prompt/response handling, agent actions, model/prompt/retrieval supply chain, emergency stop, or LLM eval security checks.
- An LLM can retrieve private data, call tools, write files, send messages, execute actions, or influence decisions.
- The system mixes instructions, user input, retrieved content, and tool output.
- A launch needs security tests for AI workflow behavior.

## When Not To Use

- The request is broad AI strategy, model strategy, or ethics work outside engineering controls.
- The work is classical ML evaluation or drift; use `ml-reliability-and-evaluation` instead.
- The request is general application threat modeling without LLM-specific boundaries; use `secure-sdlc-and-threat-modeling` instead.
- The issue is generic artifact provenance with no model/prompt/tool supply chain concern; use `software-supply-chain-security` instead.
- The main work is personal-data lifecycle, retention, deletion, export, or prompt/response storage controls; use `privacy-and-data-lifecycle` instead unless LLM prompt, retrieval, tool, or output boundaries dominate.
- The main work is tenant boundary enforcement outside LLM retrieval/session context; use `tenant-isolation` instead.
- The main work is generic source, build, artifact, or model provenance with no prompt, tool, retrieval, or dataset workflow boundary; use `software-supply-chain-security` instead.
- The main work is rollout, rollback, staged exposure, or release sequencing for a model-backed change; use `progressive-delivery` instead unless the emergency stop is an LLM-specific control gap.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Intended use, affected user groups, misuse context, unacceptable harms or unsafe actions, and human escalation or override expectations.
- LLM workflow, actors, prompts, system instructions, retrieved data, tools, actions, and output sinks.
- Trust boundaries among user input, developer instructions, retrieved documents, model output, tool results, and external systems.
- Data classification, tenant boundaries, permissions, secrets, and privacy constraints.
- Tool capabilities, scopes, rate limits, user confirmations, side effects, and activity logs.
- Input and output validation needs: length, file type, links, hidden/control characters, rendered content, feedback forms, and downstream consumers.
- Eval set: prompt injection, data exfiltration, unsafe actions, over-permission, output injection, and regression cases.
- Red-team scope: attacker goals, prohibited actions, data and tool boundaries, safety constraints, success criteria, finding severity, and retest path.
- Logging, redaction, prompt/response storage, retention, human access, and incident response expectations.
- Model chains, nested prompts, loop limits, retrieval fanout, token/cost ceilings, and downstream systems that consume model output.
- Model, prompt, retrieval corpus, index, dataset, and tool-policy provenance, rollback targets, and emergency disable paths.

## Workflow

1. **Frame impact and misuse.** State intended use, affected user groups, unacceptable harms or unsafe actions, misuse context, and where human escalation or override must exist.
2. **Map boundaries.** Identify every place untrusted text can influence prompts, retrieval, tool calls, code paths, messages, or stored state.
3. **Constrain tools.** Give tools minimum permissions, explicit schemas, rate limits, loop/depth limits, side-effect boundaries, and confirmation checks for high-risk actions.
4. **Protect retrieval.** Enforce tenant/data permissions before retrieval and again before answer/action use.
5. **Treat output as untrusted by sink.** Commands need allowlisted operations and dry-run/confirmation where risky; queries need parameterization and scoped credentials; rendered text needs contextual encoding; structured tool inputs need schema validation; documents/messages need destination policy checks; downstream prompts need boundary markers and instruction-isolation.
6. **Validate inputs and feedback.** Bound length and tokens, validate uploaded files by content and declared type, normalize or reject hidden/control characters, set an explicit link/URL policy, redact or block sensitive data by purpose, and apply the same controls to free-form feedback.
7. **Separate instructions from data.** Do not let retrieved or user content override developer/system policy. Use structural boundaries, markers, and deterministic checks as defense in depth, not as guarantees.
8. **Protect stored prompts and responses.** Classify prompts and outputs, minimize retention, restrict human access by need, encrypt with accountable key responsibility, and audit access.
9. **Protect session isolation.** Keep user sessions, conversation state, retrieved context, and mutable objects scoped per user/request; test race conditions that could leak history across users or tenants.
10. **Plan emergency stop and rollback.** Define independent disable or rollback paths for prompt templates, tool permissions, model/config, retrieval corpus, index, and training or fine-tuning inputs.
11. **Scope model chains.** When one model output feeds another model or agent, give each step separate permissions, retrieval boundary, audit trail, and injection eval.
12. **Evaluate adversarially.** Test prompt injection, tool misuse, data leakage, refusal bypass, unsafe output, dependency substitution, recursive tool loops, retrieval amplification, and regression cases with a repeatable adversarial corpus; for high-impact workflows, run a scoped red-team pass with severity triage and retest criteria.
13. **Audit decisions.** Log prompts, retrieval identifiers, tool calls, user confirmations, denials, and outcomes with privacy-preserving redaction, retention, and replay-for-investigation rules.
14. **Control supply chain.** Track prompts, tools, models, datasets, retrieval corpora, indexes, and deployment artifacts as versioned inputs with version, source, eval result, integrity checks, rollback target, and retirement date. Treat executable or code-loading model artifacts as unsafe unless isolated, allowlisted, and justified.

## Synthesized Default

Use least-privilege tools, permission-checked retrieval, input validation, untrusted-output handling, sensitive-data controls, session isolation, adversarial eval checks, audit logs, emergency rollback, and versioned AI workflow inputs. Test the workflow against realistic attacker goals, then make deterministic application controls decide what is allowed.



## Phase Behavior

- Ideation: identify risks, defaults, unknowns, options, and the next decision before code exists.
- Design: shape the target artifact, tradeoffs, checks, and details to gather.
- Development: guide sequencing, code boundaries, checks, and acceptance criteria.
- Testing: define release-blocking tests, evals, fixtures, and failure probes.
- Release: define rollout, observability, abort, rollback, and readiness details.
- Maintenance: define owners, drift checks, cleanup triggers, and refresh cadence.
- Existing artifact: use current code, docs, telemetry, incidents, or diffs as context for the next engineering decision; do not wait for a finished artifact before guiding design, build, release, or operation.
- Missing details: state assumptions and say what to check next instead of blocking lifecycle guidance.

## Exceptions

- Read-only summarization with public data can use lighter tool controls, but output handling and injection tests still matter.
- Human confirmation can mitigate high-impact actions, but confirmation UI must show trustworthy context and not model-manipulated summaries only.
- Some logs must be minimized or redacted for privacy; keep enough traceability to investigate unsafe actions.
- Classifiers or model judges can help detect attacks, but they are defense in depth and must not be the only enforcement boundary.
- Broad AI strategy questions are out of scope unless tied to deployable engineering controls.

## Response Quality Bar

- Lead with the LLM threat model, tool-permission decision, eval check, or blocker list requested.
- For short design or pre-launch answers, include a compact release-check list: prompt-injection mitigation plus verification; tool inventory plus per-tool authorization; sink-specific output validation before execution, querying, rendering, messaging, or downstream prompting; sensitive-info controls plus monitoring; adversarial abuse cases with pass/fail criteria; and audit logs for model invocations, tool calls, denials, user confirmations, and retention.
- Cover prompt/retrieval/tool/output boundaries, least privilege, tenant/data isolation, input and output validation, unsafe-action controls, sensitive-data handling, adversarial evals, logging, emergency rollback, and supply-chain records before optional AI-security breadth.
- Make recommendations actionable with permission scopes, deterministic control points, eval cases, confirmation checks, stop criteria, and regression checks where relevant.
- Name the details to inspect, such as retrieval IDs, tool scopes, action sinks, prompt versions, model versions, eval results, audit logs, and redaction rules; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside deployable LLM application controls. Route privacy lifecycle, tenant isolation, rollout sequencing, and generic supply-chain trust away unless prompt, retrieval, tool, or output boundaries are the dominant risk.
- Be concise: avoid generic prompt-injection background and prefer compact boundary maps, permission matrices, and eval tables.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- LLM threat model and trust-boundary map.
- Intended-use, affected-user, misuse, unacceptable-harm, and escalation or override context.
- Prompt, retrieval, tool, and output permission matrix.
- Tool confirmation, rate-limit, and audit requirements.
- Retrieval data-boundary and tenant-isolation checks.
- Input, feedback, and output validation table for text, files, links, rendered content, and downstream sinks.
- Output sink handling table for commands, queries, rendered content, structured tool inputs, documents/messages, and downstream prompts.
- Adversarial eval and regression plan.
- Red-team plan or explicit rationale for not running one.
- Prompt/response storage, access, retention, logging, and privacy requirements.
- Emergency stop and rollback plan for prompt, model/config, retrieval corpus/index, tool permissions, and training or fine-tuning inputs.
- Session isolation and cross-user leakage test plan.
- Model/prompt/tool/data supply-chain record with artifact ID, version, source, integrity checks, eval result, rollback target, and retire-by date.

## Checks Before Moving On

- `boundary_map`: prompt, user input, retrieved data, tool output, model output, and action sinks are mapped.
- `impact_context`: intended use, affected user groups, unacceptable harms or unsafe actions, misuse context, and escalation or override expectations are stated where relevant.
- `least_privilege`: tools and retrieval are scoped by user, tenant, action, and side effect.
- `input_validation`: prompt, feedback, file, link, hidden/control-character, and size/token controls are defined before model use.
- `output_handling`: model output is validated, encoded, or constrained before use in sensitive sinks.
- `adversarial_check`: prompt injection, leakage, unsafe-action, and regression tests exist.
- `red_team_scope`: high-impact workflows have a scoped red-team plan, finding severity, and retest path, or an explicit risk-based skip.
- `sensitive_data_control`: prompt/response storage, redaction, retention, and human access rules are defined.
- `rollback_control`: prompt, model/config, retrieval, tool-permission, and training/fine-tuning inputs can be disabled or rolled back independently.
- `activity_log_check`: tool calls, user confirmations, retrieval IDs, and outcomes are linked without leaking sensitive data.

## Red Flags - Stop And Rework

- Retrieved documents can override system instructions.
- The model can call broad tools with production privileges.
- Model output is executed, queried, rendered, or sent without validation.
- User input can include unbounded content, hidden instructions, unchecked links, or unchecked files.
- Prompts and responses are stored broadly or exposed to human roles without purpose, retention, and access controls.
- Prompt templates, retrieval corpora, indexes, tool permissions, or model configuration cannot be rolled back independently.
- Shared conversation or retrieval state can leak between users, tenants, or requests.
- Eval set only tests happy-path answer quality.
- Logs capture secrets or private prompts without redaction.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Trusting the model to follow policy | Enforce policy in deterministic application controls. |
| Permission-checking after retrieval only | Check before retrieval and before action/use. |
| Treating prompts as config only | Version prompts as behavior-changing artifacts with release checks. |
| Treating guardrails as guarantees | Combine model-facing mitigations with deterministic application enforcement. |
| Ignoring prompt storage | Prompts and responses need classification, retention, access, and audit controls. |
| Evaluating model, not workflow | Test tool use, retrieval, output sinks, and confirmation paths. |
