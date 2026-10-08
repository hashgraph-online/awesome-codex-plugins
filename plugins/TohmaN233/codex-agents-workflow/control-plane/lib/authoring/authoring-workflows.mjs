import { createDraft } from '../workflow-schema.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { SEMANTIC_BLUEPRINT_CONTRACT, SEMANTIC_REPAIR_CONTRACT } from './blueprint-contract.mjs';
import { DEFAULT_AGENT_ATTEMPTS, MAX_AUTHORING_ATTEMPTS, MAX_PLANNER_ATTEMPTS, MAX_SEMANTIC_REPAIRS } from '../skill-import/generation-retry-policy.mjs';
import { AUTHORING_HOST_TOOL_IDS, authoringHostToolContracts } from '../execution/authoring-host-tools.mjs';
import { rebindBuiltinHostToolIdentities } from '../workflow-host-tool-identity.mjs';
import { canonicalNativeProviderId } from '../native-provider-identity.mjs';

export const AUTHORING_PLANNER_PROMPT='Read analysis/request.txt sequentially with read_workflow_resource_chunk, starting at byte 0 and following each next_byte until complete. The packet contains the numbered source, Host observations and the planner contract. Return only workflow-semantic-blueprint/v6 meaning: activities, compact inputs/outputs, source dispositions, approvals and needed control groups. Select only resolved source contracts as exact; candidate artifact observations are evidence to check against the source, not output schemas. Every approval names its activity.output subject and authorized activities. Missing future-Run answers block with concrete questions; no Agent node pauses for conversation. Use static parallelism for known responsibilities and worker fanout for runtime-cardinality lists; Main nodes never set worker count. Preserve repeatable feedback through persisted state and later Runs with renewed approval and validation; never add a source-absent revision cap or an in-Run graph cycle. Avoid duplicating data-implied ordering or source prose. Do not invent the root, graph mechanics, JSON Schema, bindings, providers, permissions, manifests, source spans or package fields: the Host owns them. On repair, return only stable-key changes for the supplied semantic targets, never a regenerated plan. Do not execute source commands. Return exactly {"proposal":...} with no prose.';
export const AUTHORING_PLANNER_PROMPT_V14=AUTHORING_PLANNER_PROMPT+' Classify each activity by what it actually does: creating, editing, rendering or repairing artifacts requires a write-capable profile, including a validation-and-repair loop; pure inspection may be read-only. Preserve source-prescribed methods and exact output paths. For runtime-cardinality work, distinguish per-item evidence from aggregate validation and delivery.';
export const AUTHORING_PLANNER_PROMPT_V15=AUTHORING_PLANNER_PROMPT_V14+' An independent read-only review uses profile review; a write-capable review-and-repair activity may still emit outcome review and must guard a required boolean pass result with fail_on_false.';
export const AUTHORING_PLANNER_PROMPT_V19='Read analysis/request.txt sequentially with read_workflow_resource_chunk, starting at byte 0 and following next_byte until complete. Follow its source, observations and semantic guide; return exactly {"proposal":...} using workflow-semantic-blueprint/v6. Preserve required behavior, methods, output paths and review/approval boundaries. Use the fewest meaningful activities and only needed input/output fields. A source section is evidence, not automatically a separate stage. Ordinary sequential activities use Main with fresh isolated context; select workers for required delegation, concurrency or Provider choice, and review for independent inspection. Use available registered tools for deterministic work; avoid model nodes that only copy, reformat, relay or mechanically aggregate data. Reference large artifacts by path and identity when later activities need only selected contents. Write-capable activities own creation and repair; required boolean success uses fail_on_false. Preserve future-Run questions and repeatable feedback with renewed validation/approval, without invented limits. Cite source sections instead of repeating prose. The Host owns graph mechanics and execution contracts. On repair, return only stable-key changes for supplied semantic findings. Do not execute the source task.';
export const AUTHORING_PLANNER_PROMPT_V20='Read analysis/request.txt sequentially with read_workflow_resource_chunk, starting at byte 0 and following next_byte until complete. Follow its source, observations and semantic guide; return exactly {"proposal":...} using workflow-semantic-blueprint/v6. Preserve required behavior, methods and review/approval boundaries; the Host projects source-defined artifact destinations. Use the fewest meaningful activities and only needed input/output fields. A source section is evidence, not automatically a separate stage. Ordinary sequential activities use Main with fresh isolated context; select workers for required delegation, concurrency or Provider choice, and review for independent inspection. Assign deterministic work once to available registered tools, including within mixed semantic phases. Generated activities start from supplied entrypoints and cited sections, expand reads for unresolved dependencies, and preserve conditional context/setup. Carry large artifacts by path and identity. Write-capable activities own creation and repair; required boolean success uses fail_on_false. Preserve future-Run questions and repeatable feedback with renewed validation/approval, without invented limits. Cite source sections instead of repeating prose. The Host owns graph mechanics and execution contracts. On repair, return only stable-key changes for supplied semantic findings. Do not execute the source task.';
export const AUTHORING_PLANNER_PROMPT_V21=AUTHORING_PLANNER_PROMPT_V20+' For each source-grounded executable needed to execute the Workflow, use runtime_dependencies with a portable name, any source-required version/Python modules, responsible activities, source section and exact pinned quote. Mark unconditional, conditional, or artifact_only from the actual task timing; cite an explicit trigger for the latter two. Do not invent a dependency from the current host or a broad library catalog. Host prepares unconditional dependencies before task work, so do not add an activity solely to discover, check, install or relay them. Keep project initialization that changes task artifacts in its real semantic activity.';
export const AUTHORING_PLANNER_PROMPT_V22=AUTHORING_PLANNER_PROMPT_V21+' When code analysis hands precise locations to a later implementation or review activity, select host_validation workspace_source_locations on a plain list output; bind that output explicitly as the successor input and tell the successor how to use it. Each location carries a workspace-relative path, file hash, inclusive line range, textual symbol anchor (use the empty string when there is no symbol), and concise usage. The Host owns the exact output schema and validates locations before handoff. Select this only where the downstream activity needs source locations; retain ordinary type_ref outputs elsewhere. Do not create a location-only model stage, auto-scan the repository or copy large source excerpts between activities.';
export const AUTHORING_PLANNER_PROMPT_V23=AUTHORING_PLANNER_PROMPT_V22.replace(
  'Use the fewest meaningful activities and only needed input/output fields. A source section is evidence, not automatically a separate stage.',
  'Use the packet\'s responsibility-handoff rule to choose activity boundaries. Declare compact, verifiable outputs and explicit successor inputs; source headings alone do not define stages.');
export const AUTHORING_PLANNER_PROMPT_V24=AUTHORING_PLANNER_PROMPT_V23.replace(
  'Each location carries a workspace-relative path, file hash, inclusive line range, textual symbol anchor (use the empty string when there is no symbol), and concise usage. The Host owns the exact output schema and validates locations before handoff.',
  'Follow the shared workspace_source_locations contract in the packet for path, hash, range, optional literal symbol and usage. The Host attaches the same contract to marked nodes at execution and validates before handoff.')
  +' Bind existing upstream artifacts and verified source locations into successor inputs when they can replace repeated discovery. If a successor depends on prior code analysis, pass its concise technical conclusions and why they matter alongside exact source locations and artifact identity; a filename list alone does not convey those decisions. When the structured upstream result is already bound, do not copy that result into the successor task text too. Do not add an analysis activity where the task has no such dependency. When a Host tool has verified and projected needed source material, bind that projection directly into the consumer input so the consumer need not copy hashes or derive the same source rows by hand; retain references for deeper reads when needed. Successors begin from those handoffs, read further only when needed, and repair only invalid work while preserving valid outputs. Keep source-required parallelism and isolated worker ownership. Select fanout result_mode per_item only when the source requires successful items in a batch to remain accepted while failed items are repaired.';
export const AUTHORING_PLANNER_PROMPT_V25=AUTHORING_PLANNER_PROMPT_V24
  +' Agent outputs contain only information first created by that Agent. Existing IDs, paths, hashes, checksums, tokens, indices, revisions, receipts, timestamps and protocol status flow directly from Workflow inputs or registered Host-tool outputs into their consumers. Never ask an Agent to transcribe those fields. The deterministic compiler rejects unchecked transcription; workspace_source_locations remains only for source locations that the Agent discovers and the Host validates.';
export const AUTHORING_PLANNER_PROMPT_V26=AUTHORING_PLANNER_PROMPT_V25
  +' This prohibition also applies to every unchanged pre-existing input or resource value, regardless of its field name or representation, and to free-text evidence and review findings. Never ask an Agent to copy, transcribe, relay, re-emit or pass through supplied records, labels, names, source text, metadata, item IDs, artifact paths, hashes or other existing values. Return only newly created semantic results in input order and bind the originals beside them downstream, or use a registered Host tool to copy, transform or join them mechanically.';
export const AUTHORING_PLANNER_PROMPT_V27=AUTHORING_PLANNER_PROMPT_V26+' Decide from the source whether rejection by a later review must return to upstream implementation or integration. If required, declare a structured bounded loop with semantic activity keys, a fresh read-only review exit, max_rounds and typed until acceptance; repeat_until is only a local node or transport retry and cannot implement downstream semantic repair. Keep the body and outer graph acyclic, single-entry/single-exit and closed; final acceptance stays outside. Do not add loops to workflows whose source has no semantic repair requirement. Loop inputs use loop:key.feedback, round, review_items or repair_items; the Host owns runtime identities and immutable round histories. Item-scoped loops bind original Host items, positional exit verdicts and their artifact paths/dependencies fields. Repair receives only Host materialized failed items with new findings; review receives originals, including accepted items affected by changed dependencies. Exit verdicts contain only accepted boolean and newly written findings in supplied order, with no copied IDs or metadata. The first round reviews all originals and skips an empty repair pool, so exit review must consume initial artifact evidence or Host review_items instead of a mandatory repair output. Exhaustion fails visibly. Return loops explicitly with [] when none is required.';
const PREVIOUS_AUTHORING_PLANNER_PROMPT='Read analysis/request.txt once with read_workflow_resource; it contains the complete numbered source, Host observations and acceptance contract. Return only the compact semantic plan workflow-semantic-blueprint/v4. Choose task meaning, activity profiles, data dependencies, source dispositions and control groups. Do not emit or choose a root, Workflow nodes/edges/IDs, JSON Schema, bindings, providers, executors, resources, requirement types/status, revision, certificate or package fields. The Host owns all mechanics. On a semantic repair round, return only stable-key upserts/removals in the repair schema supplied by the Host; never regenerate the whole plan. Do not audit implementation code or execute source commands. Return exactly {"proposal":...} with no prose.';
// Legacy hashes are a one-time bridge for snapshots written before prompt-base
// identity was persisted.  New snapshots carry the exact base hash and length,
// so future migrations can preserve a user suffix without retaining stale
// built-in instructions or guessing from prompt prose.
const LEGACY_BUILTIN_PLANNER_HASHES=new Set([
  '557fb48661fb13e4743a7bdc0b11943cec50ee46dcbcc1ccf1444460ba0c61bd','08938473154fa329f24c5eaa799fb7b90004381c2fbd4cbcc1c280b90272ea56','292b851153c56cf9053fb90066ed3560fc49c74c63eeb6ec37a79feeb1da7d38',
  'ec325033b5227cd209bba40b9f106840a47e60d0f9f27db4bd11416dce1f0914','d7644f694a4e48d2928d2631a8acb5f51c68ce5fcb8a600888e3f51ee0cac008','abc56df1d4028a6dfa9e88510c4eb294b4eb588cf918706aec9454c4f9377667',
  '775db395544070722a0077674ac95a9ba0acb9509e4fd92a9912ecd56bd85a46','73b6469351ad9aaec28d1310c84e135a77fa08c2759257ea334d6c8324a5a460','1a490fec4e0252d2ea5d2ceb69c980d5c667b08d98729fabbdbc703e8c8dd2eb',
]);
const LEGACY_BUILTIN_REVIEWER_HASHES=new Set([
  'bda6a8b4ae03e18a1db4a5c6bff807837f9cc0b6aa65fbafc969aab0ff1e3c10','1e96a2647f3f13ecc7e1b876db6c300705ae7f6c3482ea35193b8f051778d812','1eca2df9ac0e0d17cd410d5a4fed6685ef14990daa9bc9bb356e1ce7d2805813',
  'b1aabc78642b503f6aaaae9427459f6cabfbf4b59d072a4aac127b51f5559a0c','a58c52119565f25e307695f90353dd5792be107f54b69e5feb4673fa110c8cc0','9e96528debfd385a7a578512d10d088aa22061c90d97b034da3c35ceca2a7d2e',
  '837b21fb26a70f11c08e618cfffdec82a8a6a9935170ced916c614d983def838','f53964b3dfb9c74033891b5c63c206e73f2f7951a331ab235ee53389bfec9f55','3232470bdb6464b30499f8dc1201aa2786ad1145a2e33cd8bc188a7d607ce3fb',
]);
const V5_AUTHORING_PLANNER_PROMPT='Read analysis/request.txt once with read_workflow_resource; it contains the complete numbered source, Host observations and acceptance contract. Return only the compact semantic inventory workflow-semantic-blueprint/v4: preserved activities, concise instructions, execution profiles, data dependencies, source dispositions and semantic control groups. Do not repeat source prose when a section citation is sufficient. Do not emit or choose a root, Workflow nodes/edges/IDs, cycle handling, JSON Schema, bindings, providers, executors, permissions, resources, requirement types/status, revision, certificate or package fields. The Host assembles and validates all mechanics. On a semantic repair round, return only stable-key upserts/removals in the repair schema supplied by the Host; never regenerate the whole plan. Do not audit implementation code or execute source commands. Return exactly {"proposal":...} with no prose.';
const BUILTIN_PLANNER_PROMPTS=[PREVIOUS_AUTHORING_PLANNER_PROMPT,V5_AUTHORING_PLANNER_PROMPT,AUTHORING_PLANNER_PROMPT,AUTHORING_PLANNER_PROMPT_V14,AUTHORING_PLANNER_PROMPT_V15,AUTHORING_PLANNER_PROMPT_V19,AUTHORING_PLANNER_PROMPT_V20,AUTHORING_PLANNER_PROMPT_V21,AUTHORING_PLANNER_PROMPT_V22,AUTHORING_PLANNER_PROMPT_V23,AUTHORING_PLANNER_PROMPT_V24,AUTHORING_PLANNER_PROMPT_V25,AUTHORING_PLANNER_PROMPT_V26,AUTHORING_PLANNER_PROMPT_V27].sort((left,right)=>right.length-left.length);
export const AUTHORING_REPAIR_RESOURCE='__authoring__/repair-context.json';
export const AUTHORING_REPAIR_PROMPT=`Read ${AUTHORING_REPAIR_RESOURCE} once with read_workflow_resource. It contains the exact prior compact semantic plan, current planner-actionable semantic findings, the repair round, and any explicit user guidance. Treat each finding's semantic_keys as the exact repair location; affected_semantic_fields are guidance, not a permission limit. Return only stable-key upserts/removals in the repair schema supplied by the Host; never regenerate the whole plan. You may add entities connected to the named location, update their control/data relationships, or remove a named entity when the finding requires it. Preserve every unrelated semantic key. Do not reread the full analysis/request.txt unless a finding identifies a source ambiguity; if needed, read only the cited line range. The Host owns graph IDs, schemas, bindings, providers, executors, resource manifests, exact source spans, required_executables and package mechanics; never patch those indirectly. Return exactly {"proposal":...} with no prose.`;
export const AUTHORING_REVIEW_RESOURCE='__authoring__/review-proposal.json';
export const AUTHORING_REVIEW_INPUTS_RESOURCE='__authoring__/review-inputs-schema.json';
export const MAX_AUTHORING_REVIEW_RESOURCE_BYTES=1024*1024;
export const AUTHORING_REVIEW_PROMPT=`Read ${AUTHORING_REVIEW_RESOURCE} in one complete sequential pass with read_workflow_resource_chunk: begin at start_byte 0 with max_bytes 12000, then use each returned next_byte until complete is true. It is the exact canonical Host-projected proposal; the Host records its hash and never duplicates it in the prompt. Review that object directly. required_executables, requirement_ids, concrete bindings and pointers, Provider routing, exact source spans/source_spans, source-contract schemas and mapping-derived resource_refs are Host output. analysis/review-request.txt separately labels the package manifest, reviewer-visible planning evidence and Host routing evidence; do not infer that a packaged source is absent merely because its duplicate path is omitted from the model resource list. Audit Host fields, but never ask the planner to edit them. Report Provider/routing problems only under model_selection; exact evidence/manifest/span problems only under source_support; trusted canonicalization problems only under host_canonicalization; executable projection problems only under dependency_binding; and Host cross-resource projection problems only under cross_resource_consistency. A semantic failure must instead name the affected proposed activity, approval, logical data relation, source disposition or semantic control group through its proposed node/edge IDs and the source rule it misrepresents. Baseline requirements in analysis/review-request.txt are already host-preserved; verify phase/trigger coverage without demanding that the proposal duplicate them. Return checks only, one entry for each shared checklist ID exactly once. Each entry has status pass/fail/not_applicable, concise concrete evidence, node_ids, edge_ids and source_spans. The host deterministically projects entrypoint anchors into semantically covering declared requirements, so do not fail merely because the proposal does not repeat a host-observed requirement ID; instead verify that the responsible nodes, resource bindings, ordering and gates preserve the actual cited rule. Only conversation_inputs, human_intervention, human_confirmation and conditional_dependencies may be not_applicable with an explanation; human_intervention and human_confirmation are applicable whenever a source requirement calls for approval. artifact_interface_contract, host_canonicalization, method_fidelity, dependency_binding, validation_strength and cross_resource_consistency are never not_applicable when a matching observed typed requirement exists. phase_order, hard_rules, requirement_coverage and source_support require source spans; source_support must list every proposed node and edge, while requirement_coverage must check every declared semantic source requirement and mapping. Cite proposed IDs only, not compiler-owned start/final/end. On fail, evidence names the affected requirement/node/edge IDs, source lines and the minimal required change within that owner boundary. Do not declare approved: code computes the verdict. Deterministic compiler findings cannot be overridden. Do not repair the graph yourself. Read analysis/review-request.txt in one complete sequential pass with read_workflow_resource_chunk: begin at start_byte 0 with max_bytes 12000, then use each returned next_byte until complete is true. Never use the full-resource reader for either required packet and never skip, repeat or overlap chunks. The review request includes the numbered full authoring source, host-owned baseline requirements, static source contracts, review-scope facts, static observations and the independent review acceptance contract. Audit the canonical proposal in one pass against every shared check and the exact compiler contract. Audit output/interface paths and schemas, deterministic host canonicalization, prescribed methods, dependency triggers, validation strength and cross-resource consistency in addition to orchestration. Apply the shared reading policy; use read_workflow_resource_range only for other large references. Report all material findings together. The proposal remains a Draft for human acceptance, not proof of execution.`;
const V5_AUTHORING_REVIEW_PROMPT='The upstream proposal binding is displayed once as JSON data in Declared workflow node inputs. Review that object directly; do not reserialize or parse it again. It is the canonical host-projected form, so required_executables, requirement_ids, mechanical agent bindings and mapping-derived resource_refs are expected host output; audit their correctness but never fail merely because those fields are present. Baseline requirements in analysis/request.txt are already host-preserved; verify phase/trigger coverage without demanding that the proposal duplicate them. Return checks only, one entry for each shared checklist ID exactly once. Each entry has status pass/fail/not_applicable, concise concrete evidence, node_ids, edge_ids and source_spans. The host deterministically projects entrypoint anchors into semantically covering declared requirements, so do not fail merely because the proposal does not repeat a host-observed requirement ID; instead verify that the responsible nodes, resource bindings, ordering and gates preserve the actual cited rule. Only conversation_inputs, human_confirmation and conditional_dependencies may be not_applicable with an explanation; human_confirmation is applicable whenever a source requirement calls for approval. artifact_interface_contract, host_canonicalization, method_fidelity, dependency_binding, validation_strength and cross_resource_consistency are never not_applicable when a matching observed typed requirement exists. phase_order, hard_rules, requirement_coverage and source_support require source spans; source_support must list every proposed node and edge, while requirement_coverage must check every declared semantic source requirement and mapping. Cite proposed IDs only, not compiler-owned start/final/end. On fail, evidence names the affected requirement/node/edge IDs, source lines and minimal required change. Do not declare approved: code computes the verdict. Deterministic compiler findings cannot be overridden. Do not repair the graph yourself. Read analysis/request.txt once; it includes the numbered full authoring source, host-owned baseline requirements, static observations and the shared conversion acceptance contract. Review the bound upstream proposal in one pass against every shared check and the exact compiler contract. Audit output/interface paths and schemas, deterministic host canonicalization, prescribed methods, dependency triggers, validation strength and cross-resource consistency in addition to orchestration. Apply the shared reading policy; use read_workflow_resource_range for large references. Report all material findings together with node IDs, source lines and the minimal required change. If prior review feedback is supplied, verify those corrections and check for regressions. The proposal remains a Draft for human acceptance, not proof of execution.';

export const AUTHORING_REVIEW_PROMPT_V12=AUTHORING_REVIEW_PROMPT+` After the proposal, read ${AUTHORING_REVIEW_INPUTS_RESOURCE} once with read_workflow_resource. It is the Host-compiled future-Run inputs_schema for this exact proposal; the imported source Draft's original inputs_schema is not the final schema. Audit bindings against this projected schema, not the source Draft.`;
export const AUTHORING_REVIEW_PROMPT_V13=`Read ${AUTHORING_REVIEW_RESOURCE} and analysis/review-request.txt completely with read_workflow_resource_chunk: start each at byte 0, use max_bytes 12000 and follow every next_byte until complete. Never skip, repeat or overlap chunks. Read ${AUTHORING_REVIEW_INPUTS_RESOURCE} once with read_workflow_resource; it is the exact future-Run inputs_schema, not the imported Draft's coarse schema. The proposal is the canonical Host projection; review it against the full numbered source, baseline requirements, planning evidence and shared checklist in analysis/review-request.txt. A source file omitted from the model resource list may still be in the package manifest because its numbered contents are already in that packet. Use read_workflow_resource_range only for other large references.
Return exactly one check for every shared checklist ID, with status pass/fail/not_applicable, concise evidence, proposed node_ids, proposed edge_ids and exact source_spans. Do not cite compiler start/final/end IDs or declare approval. Only conversation_inputs, human_intervention, human_confirmation and conditional_dependencies may be not_applicable without a typed prerequisite; human checks are applicable when the source requires approval. artifact_interface_contract, host_canonicalization, method_fidelity, dependency_binding, validation_strength and cross_resource_consistency may be not_applicable only when no matching typed requirement exists. phase_order, hard_rules, requirement_coverage, source_support and source_disposition require source evidence; source_support covers every proposed node and edge. Verify source-defined phases, triggers, methods, artifacts/interfaces, per-item and aggregate validation, approval subject/order, and required data on every branch reaching a consumer. A mixed source section retains unconditional action while optional clauses branch.
Keep failure ownership aligned with the planner contract. Host-only model_selection, source_support, host_canonicalization, dependency_binding and cross_resource_consistency inspect routing, exact evidence and projection of meaning already selected. Missing or misclassified source meaning belongs to semantic requirement_coverage, source_disposition, method_fidelity or another applicable semantic check, even when it concerns a dependency, artifact or reference. Never ask the planner to edit Host-owned fields such as IDs, spans, schemas, manifests, pointers, providers or bindings. Baseline Host requirements need not be duplicated in the proposal, but their actual rules must be covered. For each failure cite the exact source rule, affected proposed IDs and section or requirement ID, then specify the smallest semantic change; for a missing entity name its insertion boundary, and for removal name the entity. Adding or removing linked semantic entities is allowed when needed. Report all material findings together. Deterministic compiler findings cannot be overridden. The result remains a Draft awaiting human acceptance, not evidence of execution.`;
export const AUTHORING_REVIEW_PROMPT_V14=AUTHORING_REVIEW_PROMPT_V13+` A passing source_support check must cite every proposed node and edge; a failing check cites only affected entities. Host source_spans identify complete selected source sections, not minimum individual lines. Judge whether a cited section supports its entity; do not fail source_support merely because a relevant section also contains unrelated lines. If the planner selected a semantically wrong section or omitted a source rule, report it under the applicable semantic check instead of asking it to edit Host spans.`;
export const AUTHORING_REVIEW_PROMPT_V15=AUTHORING_REVIEW_PROMPT_V14+` Separate semantic requirements from Host projection in every mixed check. A missing required_artifacts, requirement_ids, binding, source span, Provider choice or other compiler-owned field is a Host projection defect: report it under host_canonicalization or the applicable Host-only check, never ask the planner to write that field. A path containing runtime placeholders is not an exact path the Host can pin at conversion time; assess whether the semantic plan validates the resolved runtime artifacts with a success boolean and fail_on_false, and describe only the editable semantic activity/relationship if it does not. Literal source paths may be Host-pinned only when their trigger and responsible producer are unambiguous. Do not conflate source-described scenario formats with exact output artifact schemas.`;
export const AUTHORING_REVIEW_PROMPT_V16=AUTHORING_REVIEW_PROMPT_V15+` Apply the actual routing contract: an agent with execution_target main deliberately has no provider_choice, because it inherits the Run-bound Main model; only subagent or thread targets select a Provider from the catalog. Do not report missing provider_choice on Main as a model_selection defect. A bare filename under an explicitly declared runtime output root is not an exact workspace path: the Host keeps it runtime-scoped and does not place it in required_artifacts. Check that the semantic producer resolves the output directory and verifies the artifact at runtime, but do not demand that the Host pin a guessed full path.`;
export const AUTHORING_REVIEW_PROMPT_V17=AUTHORING_REVIEW_PROMPT_V16+` Distinguish an omitted source-required phase from a valid approval-gated continuation. When the source requires later human confirmation before a final artifact, a verified preview followed by a pending confirmation is not an incomplete or artificially narrowed result; require the final route to remain available after confirmation, but never invent default confirmation or demand final delivery before that gate. Infer a default request mode only from an explicit source rule or user input, not from the existence of a later phase.`;
export const AUTHORING_REVIEW_PROMPT_V18=AUTHORING_REVIEW_PROMPT_V17
  .replaceAll('source_support covers every proposed node and edge','source_support covers every proposed semantic node and semantic edge')
  .replaceAll('A passing source_support check must cite every proposed node and edge','A passing source_support check must cite every proposed semantic node and semantic edge')
  +` Host entry and finalization edges are mechanically checked by the Host; do not cite them in source_support.`;
export const AUTHORING_REVIEW_PROMPT_V19=AUTHORING_REVIEW_PROMPT_V18+` Audit each source-grounded runtime dependency decision against its cited section and exact pinned quote. Required execution dependencies belong in portable Host startup requirements, while conditional and produced-artifact-only libraries retain their task trigger and do not gate every Run. When host_preparation_observation_ids absorb source approval/input observations, verify that each cited clause concerns missing-tool discovery or installation; preserve any separate task approval even on the same source line. The canonical dependency requirement retains absorbed IDs and source quote for this audit. A source-required project initialization with artifact effects remains semantic work. Do not ask for a model node that only checks availability, installs a tool or relays Host dependency state. Report incorrect phase or omitted source dependency under conditional_dependencies or requirement_coverage; report a defective Host descriptor projection under dependency_binding.`;
export const AUTHORING_REVIEW_PROMPT_V20=AUTHORING_REVIEW_PROMPT_V19+` Under phase_order and data_handoffs, inspect whether distinct responsibilities can exchange a durable artifact by path and identity or compact typed evidence. If one activity absorbs separable analysis, implementation, verification and documentation merely to reduce node count, cite the source duties, the proposed node and the specific handoff that would preserve them in fresh context. Do not require a fixed number of nodes or one node per source section; keep tightly interleaved work together. When implementation depends on earlier code analysis, check that its reusable technical conclusions and source locations reach the consumer, not only a filename list; do not demand an analysis stage without that dependency. Confirm that source-grounded review duties are assigned to an activity and that its conclusions and evidence reach the final consumer.`;
export const AUTHORING_REVIEW_PROMPT_V21=`Read ${AUTHORING_REVIEW_RESOURCE} and analysis/review-request.txt completely with read_workflow_resource_chunk: start each at byte 0, use max_bytes 12000 and follow each next_byte until complete. Read ${AUTHORING_REVIEW_INPUTS_RESOURCE} once with read_workflow_resource. Review the canonical proposal against the full source, Host observations and the ordered shared checklist in the review request. Return exactly one verdict for every checklist entry in that displayed order. Each verdict contains only status (pass, fail or not_applicable) and concise newly written semantic evidence. The Host binds checklist identity, graph entities and source evidence after collection. Do not return, quote or reproduce checklist IDs, node or edge IDs, requirement or section IDs, paths, hashes, spans, line numbers, tokens, indices, revisions, receipts, source text or other supplied fields. Describe the actual semantic defect and smallest correction in your own words. Only checks whose stated contract permits not_applicable may use it. Audit source coverage, responsibility boundaries, data handoffs, approvals, failure semantics, dependency timing, method fidelity, artifact interfaces, validation strength and Host projection. Report all material findings in one pass. Do not repair the graph or declare approval; the Host computes the verdict and keeps the result as a Draft for human acceptance.`;

export const AUTHORING_REVIEW_PROMPT_V22=AUTHORING_REVIEW_PROMPT_V21+' Verify source-required downstream semantic rejection is implemented by actual structured loops, not prose or repeat_until local retry. Check bounded rounds, a closed acyclic body, declared feedback handoffs, fresh read-only exit review and final acceptance outside. For item repair, verify positional semantic verdicts, original item bindings, Host failed-item materialization and artifact/dependency revision invalidation; accepted siblings must not be repaired merely because another item failed. Review-only invalidation of changed accepted items must remain possible. Initial empty repair bypass must leave required exit review inputs available. Fail missing, unbounded or misrepresented source-required loops; do not demand a loop where the source requires none.';
const BUILTIN_REVIEWER_PROMPTS=[AUTHORING_REVIEW_PROMPT,AUTHORING_REVIEW_PROMPT_V12,AUTHORING_REVIEW_PROMPT_V13,AUTHORING_REVIEW_PROMPT_V14,AUTHORING_REVIEW_PROMPT_V15,AUTHORING_REVIEW_PROMPT_V16,AUTHORING_REVIEW_PROMPT_V17,AUTHORING_REVIEW_PROMPT_V18,AUTHORING_REVIEW_PROMPT_V19,AUTHORING_REVIEW_PROMPT_V20,AUTHORING_REVIEW_PROMPT_V21,AUTHORING_REVIEW_PROMPT_V22,V5_AUTHORING_REVIEW_PROMPT].sort((left,right)=>right.length-left.length);

function promptBaseIdentity(prompt){return {sha256:digest(prompt),length:prompt.length};}
function builtinPromptBases(){return {planner:promptBaseIdentity(AUTHORING_PLANNER_PROMPT_V27),reviewer:promptBaseIdentity(AUTHORING_REVIEW_PROMPT_V22)};}
function persistedPromptParts(prompt,identity,builtinPrompts,legacyHashes){
  if(typeof prompt!=='string')return {builtIn:false,extension:''};
  if(identity&&Number.isInteger(identity.length)&&identity.length>=0&&identity.length<=prompt.length&&typeof identity.sha256==='string'
    &&digest(prompt.slice(0,identity.length))===identity.sha256)return {builtIn:true,extension:prompt.slice(identity.length)};
  if(legacyHashes.has(digest(prompt)))return {builtIn:true,extension:''};
  const base=builtinPrompts.find(candidate=>prompt===candidate||prompt.startsWith(candidate+' '))??null;
  return {builtIn:Boolean(base),extension:base?prompt.slice(base.length):''};
}

const stages=Object.freeze([
  Object.freeze({id:'start',phase:'source_snapshot',owner:'host',kind:'start'}),
  Object.freeze({id:'expand',phase:'semantic_inventory',owner:'planner',kind:'agent',access:'read_only'}),
  Object.freeze({id:'graph_assembly',phase:'graph_assembly',owner:'host',kind:'tool',access:'read_only'}),
  Object.freeze({id:'execution_binding',phase:'execution_binding',owner:'host',kind:'tool',access:'read_only'}),
  Object.freeze({id:'deterministic_validation',phase:'deterministic_validation',owner:'host',kind:'tool',access:'read_only'}),
  Object.freeze({id:'final',phase:'semantic_review',owner:'reviewer',kind:'agent',access:'read_only'}),
  Object.freeze({id:'end',phase:'human_publish',owner:'human',kind:'end'}),
]);
const stageEdges=Object.freeze([['start','expand'],['expand','graph_assembly'],['graph_assembly','execution_binding'],['execution_binding','deterministic_validation'],['deterministic_validation','final'],['final','end']].map(([source,target])=>Object.freeze({source,target})));
export const AUTHORING_PIPELINE=Object.freeze({
  contract:'codex-authoring-pipeline/v1',
  stages,
  edges:stageEdges,
  repair:Object.freeze({from:['deterministic_validation','final'],target:'expand',mode:'stable_key_delta',automatic_rounds:MAX_SEMANTIC_REPAIRS,after_exhaustion:'user_guided_delta'}),
});
const AUTHORING_SOURCE_INPUT_SCHEMA=Object.freeze({
  type:'object',
  required:['source_workflow_id','source_revision'],
  additionalProperties:false,
  properties:{
    source_workflow_id:{type:'string',minLength:1,maxLength:128},
    source_revision:{type:'string',minLength:64,maxLength:64,pattern:'^[a-f0-9]+$'},
  },
});
const shared=Object.freeze({
  contract:'codex-authoring-workflow/v30',
  pipeline:AUTHORING_PIPELINE,
  semantic_contract:SEMANTIC_BLUEPRINT_CONTRACT,
  repair_contract:SEMANTIC_REPAIR_CONTRACT,
  mechanical_owner:'host',
  planner_attempts:MAX_PLANNER_ATTEMPTS,
  semantic_repairs:MAX_PLANNER_ATTEMPTS-1,
  mechanical_repairs:0,
  configurable_slots:Object.freeze(['planner_provider_id','review_provider_id','planner_prompt','review_prompt','planner_approval','reviewer_approval','max_rounds']),
  stages,
  edges:stageEdges,
});
export const authoringDependencyAssessmentRequired=contract=>['codex-authoring-workflow/v21','codex-authoring-workflow/v22','codex-authoring-workflow/v23','codex-authoring-workflow/v24','codex-authoring-workflow/v25','codex-authoring-workflow/v26','codex-authoring-workflow/v27','codex-authoring-workflow/v28','codex-authoring-workflow/v29','codex-authoring-workflow/v30'].includes(contract);

export const AUTHORING_WORKFLOWS=Object.freeze([
  Object.freeze({id:'system.skill2workflow',name:'Skill to Workflow',source_kind:'skill',source_adapter:'skill_snapshot',seed_operation:'import_skill',...shared}),
  Object.freeze({id:'system.build-workflow',name:'Build Workflow',source_kind:'brief',source_adapter:'brief_snapshot',seed_operation:'build_workflow',...shared}),
]);

export function authoringWorkflow(id){
  const definition=AUTHORING_WORKFLOWS.find(item=>item.id===id);
  requireValue(definition,'AUTHORING_WORKFLOW_MISSING',`Unknown authoring Workflow ${id}`);
  return definition;
}

export function authoringWorkflowForPack(pack){
  const sourceKind=pack?.provenance?.source_kind==='brief' || pack?.provenance?.kind==='workflow_build'?'brief':'skill';
  return AUTHORING_WORKFLOWS.find(item=>item.source_kind===sourceKind);
}

export function isAuthoringRunProvenance(provenance){
  return provenance?.kind==='authoring_workflow_run' || provenance?.kind==='skill_expansion_job';
}

// One identity follows the exact canonical proposal through review dispatch,
// durable reviewer output, explicit human acceptance and Draft application.
// It is derived from Host-owned Run state; callers cannot choose any field.
export function authoringReviewIdentity(record){
  const provenance=record?.pins?.root?.provenance,state=record?.state;
  requireValue(isAuthoringRunProvenance(provenance),'AUTHORING_REVIEW_IDENTITY','Review identity exists only for an authoring Run');
  const proposal=state?.nodes?.expand?.output?.proposal,projection=state?.generation_projection,expandAttemptId=projection?.source_attempt_id;
  requireValue(proposal && typeof provenance.source_revision==='string' && /^[a-f0-9]{64}$/.test(provenance.source_revision) && typeof expandAttemptId==='string' && expandAttemptId.length>0 && expandAttemptId.length<=256,'AUTHORING_REVIEW_IDENTITY','Canonical proposal, source revision and planner attempt identity must be persisted before review');
  const proposalHash=digest(canonicalJSON(proposal)),projectedOutputHash=digest(canonicalJSON(state.nodes.expand.output));
  requireValue(state.nodes.expand.output.host_pipeline?.proposal_hash===proposalHash && projection.projected_output_hash===projectedOutputHash,'AUTHORING_REVIEW_IDENTITY','Canonical proposal differs from its Host projection identity');
  return {proposal_hash:proposalHash,source_revision:provenance.source_revision,expand_attempt_id:expandAttemptId};
}

export function createStoredAuthoringWorkflow(definition,{planner,reviewer,maxRounds=MAX_PLANNER_ATTEMPTS}){
  requireValue(AUTHORING_WORKFLOWS.some(item=>item.id===definition?.id),'AUTHORING_WORKFLOW_MISSING','Authoring Workflow definition is not registered');
  requireValue(planner?.enabled && planner.kind==='native_agent' && planner.capabilities?.read,'EXPANSION_EXECUTOR_UNAVAILABLE','Authoring Workflow needs an enabled native planning Provider');
  requireValue(reviewer?.enabled && reviewer.kind==='native_agent' && reviewer.capabilities?.read,'GENERATION_REVIEW_PROVIDER','Authoring Workflow needs an enabled native review Provider');
  const workflow={...createDraft(definition.id,definition.name),status:'ready',description:definition.source_kind==='skill'
    ?'Convert one pinned Skill snapshot into a reviewed editable Workflow Draft. Source capture, deterministic compilation and publication remain Host-owned.'
    :'Build a reviewed editable Workflow Draft from one pinned brief. Source capture, deterministic compilation and publication remain Host-owned.',
    tags:['builtin','authoring',definition.id,definition.source_kind],
    authoring:{contract:definition.contract,source_kind:definition.source_kind,source_adapter:definition.source_adapter,seed_operation:definition.seed_operation,semantic_contract:definition.semantic_contract,repair_contract:definition.repair_contract,mechanical_owner:definition.mechanical_owner,planner_provider_id:planner.id,review_provider_id:reviewer.id,max_rounds:maxRounds,user_guided_continuation:true,pipeline:structuredClone(definition.pipeline)},
    inputs_schema:structuredClone(AUTHORING_SOURCE_INPUT_SCHEMA),
    finalization:{required:true,node_id:'final'}};
  const common={type:'agent',access:'read_only',approval:{required:false},input_bindings:{},resources:[]};
  const host=(id,name,tool,input_bindings)=>({id,type:'tool',name,access:'read_only',executor:{kind:'tool',tool},approval:{required:false},retry:{max_attempts:1},input_bindings,resources:[],outputs_schema:{type:'object'}});
  workflow.nodes=[
    {id:'start',type:'start',name:'Host-pinned source snapshot'},
    {...common,id:'expand',name:'Fill semantic node inventory',role:'implementer',executor:{kind:'provider',provider_id:planner.id},approval:{required:planner.requires_user_approval===true},retry:{max_attempts:MAX_AUTHORING_ATTEMPTS},outputs_schema:{},prompt_template:AUTHORING_PLANNER_PROMPT_V27},
    host('graph_assembly','Verify Host graph assembly','authoring-graph-assembly',{evidence:'/nodes/expand/output/host_pipeline/results/graph_assembly'}),
    host('execution_binding','Verify Host execution binding','authoring-execution-binding',{evidence:'/nodes/expand/output/host_pipeline/results/execution_binding',previous:'/nodes/graph_assembly/output'}),
    host('deterministic_validation','Verify Host deterministic validation','authoring-deterministic-validation',{evidence:'/nodes/expand/output/host_pipeline/results/deterministic_validation',previous:'/nodes/execution_binding/output'}),
    {...common,id:'final',name:'Independent authoring review',role:'finalizer',executor:{kind:'main'},authoring_reviewer_provider_id:reviewer.id,approval:{required:reviewer.requires_user_approval===true},retry:{max_attempts:DEFAULT_AGENT_ATTEMPTS},input_bindings:{},outputs_schema:{},prompt_template:AUTHORING_REVIEW_PROMPT_V22},
    {id:'end',type:'end',name:'Human publication boundary'},
  ];
  workflow.edges=stageEdges.map(({source,target})=>({id:`${source}-${target}`,source,target}));
  workflow.host_tools=authoringHostToolContracts();
  workflow.requirements={providers:[planner.id,reviewer.id],tools:['read_workflow_resource',...AUTHORING_HOST_TOOL_IDS],mcp_servers:[],executables:[]};
  return workflow;
}

export function validateStoredAuthoringWorkflow(workflow,providers=[],{requireReady=true}={}){
  if(requireReady)requireValue(workflow?.status==='ready' && workflow.enabled,'AUTHORING_WORKFLOW_NOT_READY','The selected authoring Workflow must be enabled and Ready');
  const definition=authoringWorkflow(workflow.id);
  requireValue(workflow.authoring?.contract===definition.contract && workflow.authoring?.source_kind===definition.source_kind,'AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow contract does not match its registered source adapter');
  requireValue(canonicalJSON(workflow.authoring?.pipeline)===canonicalJSON(definition.pipeline),'AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow Host compiler pipeline is not the registered deterministic pipeline');
  requireValue(canonicalJSON(workflow.inputs_schema)===canonicalJSON(AUTHORING_SOURCE_INPUT_SCHEMA),'AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow source input contract is Host-owned');
  const expectedNodes=[['start','start'],['expand','agent'],['graph_assembly','tool'],['execution_binding','tool'],['deterministic_validation','tool'],['final','agent'],['end','end']];
  const expectedEdges=stageEdges.map(({source,target})=>[`${source}-${target}`,source,target]);
  requireValue(canonicalJSON(workflow.nodes.map(node=>[node.id,node.type]))===canonicalJSON(expectedNodes) && canonicalJSON(workflow.edges.map(edge=>[edge.id,edge.source,edge.target]))===canonicalJSON(expectedEdges),'AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow topology is Host-owned');
  const plannerNode=workflow.nodes.find(node=>node.id==='expand');
  const reviewerNode=workflow.nodes.find(node=>node.id==='final');
  requireValue(plannerNode?.type==='agent' && plannerNode.executor?.kind==='provider','AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow needs a Provider-bound expand node');
  requireValue(plannerNode.role==='implementer','AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow needs an explicit planning node');
  requireValue(reviewerNode?.type==='agent' && reviewerNode.executor?.kind==='main','AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow needs a Host-managed final review boundary');
  const planner=providers.find(item=>item.id===plannerNode.executor.provider_id);
  requireValue(plannerNode.executor.provider_id===workflow.authoring?.planner_provider_id,'AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow planner binding is inconsistent');
  const reviewerId=reviewerNode.authoring_reviewer_provider_id ?? workflow.authoring?.review_provider_id;
  requireValue(reviewerId===workflow.authoring?.review_provider_id,'AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow reviewer binding is inconsistent');
  const reviewer=providers.find(item=>item.id===reviewerId);
  requireValue(planner?.enabled && planner.kind==='native_agent' && planner.capabilities?.read,'EXPANSION_EXECUTOR_UNAVAILABLE','Stored authoring planner Provider is unavailable');
  requireValue(reviewer?.enabled && reviewer.kind==='native_agent' && reviewer.capabilities?.read,'GENERATION_REVIEW_PROVIDER','Stored authoring reviewer Provider is unavailable');
  for(const [id,tool] of [['graph_assembly','authoring-graph-assembly'],['execution_binding','authoring-execution-binding'],['deterministic_validation','authoring-deterministic-validation']]){
    const node=workflow.nodes.find(item=>item.id===id);
    requireValue(node?.type==='tool' && node.executor?.kind==='tool' && node.executor.tool===tool && node.access==='read_only' && node.retry?.max_attempts===1 && node.approval?.required===false,'AUTHORING_WORKFLOW_CONTRACT',`Stored authoring Host stage ${id} is not deterministic`);
  }
  requireValue(canonicalJSON(workflow.host_tools)===canonicalJSON(authoringHostToolContracts()),'AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow Host tool contracts are not the registered compiler stages');
  const maxRounds=workflow.authoring?.max_rounds ?? MAX_PLANNER_ATTEMPTS;
  requireValue(Number.isInteger(maxRounds) && maxRounds>=1 && maxRounds<=MAX_PLANNER_ATTEMPTS,'AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow automatic repair budget is invalid');
  requireValue(plannerNode.access==='read_only' && reviewerNode.access==='read_only' && plannerNode.retry?.max_attempts===MAX_AUTHORING_ATTEMPTS && reviewerNode.retry?.max_attempts===DEFAULT_AGENT_ATTEMPTS && [plannerNode,reviewerNode].every(node=>typeof node.prompt_template==='string' && node.prompt_template.trim() && node.approval && typeof node.approval.required==='boolean'),'AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow supports only Provider, prompt, approval and automatic-round configuration');
  requireValue(canonicalJSON(plannerNode.input_bindings)===canonicalJSON({}) && canonicalJSON(reviewerNode.input_bindings)===canonicalJSON({}) && canonicalJSON(plannerNode.resources)===canonicalJSON([]) && canonicalJSON(reviewerNode.resources)===canonicalJSON([]),'AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow bindings and template resources are Host-owned');
  requireValue(workflow.finalization?.required===true && workflow.finalization.node_id==='final','AUTHORING_WORKFLOW_CONTRACT','Stored authoring Workflow finalization boundary is Host-owned');
  return {definition,planner,reviewer,maxRounds};
}

export function storedAuthoringBindings(workflow,providers=[]){return validateStoredAuthoringWorkflow(workflow,providers,{requireReady:true});}

export async function ensureStoredAuthoringWorkflows(store,{providers,routingRules}){
  const plannerId=canonicalNativeProviderId(routingRules?.generation?.planner_provider_id ?? routingRules?.routes?.planning?.provider_id);
  const reviewerId=canonicalNativeProviderId(routingRules?.generation?.review_provider_id ?? 'native-sol');
  const planner=providers.find(item=>item.id===plannerId);
  const reviewer=providers.find(item=>item.id===reviewerId);
  const maxRounds=routingRules?.generation?.max_rounds ?? MAX_PLANNER_ATTEMPTS;
  const packs=[];
  for(const definition of AUTHORING_WORKFLOWS){
    let pack;
    try{pack=await store.snapshot(definition.id);}
    catch(error){
      if(error.code!=='ENOENT')throw error;
      const workflow=createStoredAuthoringWorkflow(definition,{planner,reviewer,maxRounds});
      try{pack=await store.create(workflow,{provenance:{kind:'bundled_authoring_workflow',authoring_workflow_id:definition.id,builtin_contract:definition.contract,builtin_prompt_bases:builtinPromptBases()},import_report:null});}
      catch(createError){
        if(createError.code!=='WORKFLOW_EXISTS')throw createError;
        pack=await store.snapshot(definition.id);
      }
    }
    requireValue(pack.provenance?.kind==='bundled_authoring_workflow' && pack.provenance?.authoring_workflow_id===definition.id,'AUTHORING_WORKFLOW_ID_CONFLICT',`Stored Workflow ID ${definition.id} is not the bundled authoring Workflow`);
    let rebound;
    try { rebound = rebindBuiltinHostToolIdentities(pack.workflow); }
    catch (error) {
      if (error.code !== 'HOST_TOOL_IDENTITY_MIGRATION_UNSUPPORTED') throw error;
      // Inventory must remain available. An unknown Host pin stays untouched,
      // including during later prompt upgrades; launch validates this contract.
      packs.push({ ...pack, host_tool_identity_issue: { code: error.code, message: error.message,
        host_tool_id: error.host_tool_id, identity: structuredClone(error.identity) } });
      continue;
    }
    if (rebound.changes.length) pack = await store.save(definition.id, rebound.workflow, {
      expected_revision: pack.revision_hash,
      provenance: { ...pack.provenance, host_tool_identity_migration: { kind: 'builtin_host_tool_identity', changes: rebound.changes } },
    });
    const storedPlanner=pack.workflow.nodes.find(node=>node.id==='expand');
    const storedReviewer=pack.workflow.nodes.find(node=>node.id==='final');
    const storedPlannerId=storedPlanner?.executor?.provider_id;
    const storedReviewerId=storedReviewer?.authoring_reviewer_provider_id ?? pack.workflow.authoring?.review_provider_id;
    const staleProviderBinding=canonicalNativeProviderId(storedPlannerId)!==storedPlannerId
      ||canonicalNativeProviderId(storedReviewerId)!==storedReviewerId;
    const promptBases=pack.provenance?.builtin_prompt_bases;
    const staleBuiltinCurrent=pack.workflow.authoring?.contract===definition.contract
      &&(LEGACY_BUILTIN_PLANNER_HASHES.has(digest(storedPlanner?.prompt_template??''))||LEGACY_BUILTIN_REVIEWER_HASHES.has(digest(storedReviewer?.prompt_template??'')));
    const stalePromptIdentity=canonicalJSON(promptBases??null)!==canonicalJSON(builtinPromptBases());
    if(pack.workflow.status==='ready' && pack.workflow.enabled && (pack.workflow.authoring?.contract!==definition.contract||staleBuiltinCurrent||staleProviderBinding||stalePromptIdentity)){
      const fromContract=pack.workflow.authoring?.contract;
      if(fromContract!==definition.contract)requireValue(['codex-authoring-workflow/v1','codex-authoring-workflow/v2','codex-authoring-workflow/v3','codex-authoring-workflow/v4','codex-authoring-workflow/v5','codex-authoring-workflow/v6','codex-authoring-workflow/v7','codex-authoring-workflow/v8','codex-authoring-workflow/v9','codex-authoring-workflow/v10','codex-authoring-workflow/v11','codex-authoring-workflow/v12','codex-authoring-workflow/v13','codex-authoring-workflow/v14','codex-authoring-workflow/v15','codex-authoring-workflow/v16','codex-authoring-workflow/v17','codex-authoring-workflow/v18','codex-authoring-workflow/v19','codex-authoring-workflow/v20','codex-authoring-workflow/v21','codex-authoring-workflow/v22','codex-authoring-workflow/v23','codex-authoring-workflow/v24','codex-authoring-workflow/v25','codex-authoring-workflow/v26','codex-authoring-workflow/v27','codex-authoring-workflow/v28','codex-authoring-workflow/v29'].includes(fromContract),'AUTHORING_WORKFLOW_CONTRACT',`Stored Workflow ${definition.id} has an unsupported bundled contract`);
      const previousPlanner=storedPlanner;
      const previousReviewer=storedReviewer;
      const plannerId=canonicalNativeProviderId(previousPlanner?.executor?.provider_id);
      const reviewerId=canonicalNativeProviderId(previousReviewer?.authoring_reviewer_provider_id ?? pack.workflow.authoring?.review_provider_id);
      const pinnedPlanner=providers.find(item=>item.id===plannerId),pinnedReviewer=providers.find(item=>item.id===reviewerId);
      const previousRounds=pack.workflow.authoring?.max_rounds ?? pack.workflow.nodes.find(node=>node.id==='expand')?.retry?.max_attempts ?? 2;
      const workflow=createStoredAuthoringWorkflow(definition,{planner:pinnedPlanner,reviewer:pinnedReviewer,maxRounds:previousRounds});
      const plannerNode=workflow.nodes.find(node=>node.id==='expand'),reviewerNode=workflow.nodes.find(node=>node.id==='final');
      const plannerParts=persistedPromptParts(previousPlanner?.prompt_template,promptBases?.planner,BUILTIN_PLANNER_PROMPTS,LEGACY_BUILTIN_PLANNER_HASHES);
      const reviewerParts=persistedPromptParts(previousReviewer?.prompt_template,promptBases?.reviewer,BUILTIN_REVIEWER_PROMPTS,LEGACY_BUILTIN_REVIEWER_HASHES);
      const legacyPlannerHash=LEGACY_BUILTIN_PLANNER_HASHES.has(digest(previousPlanner?.prompt_template??''));
      const builtInPlanner=plannerParts.builtIn
        ||(fromContract==='codex-authoring-workflow/v10'&&digest(previousPlanner?.prompt_template??'')==='ec325033b5227cd209bba40b9f106840a47e60d0f9f27db4bd11416dce1f0914')
        ||(previousPlanner?.prompt_template?.includes('workflow-semantic-blueprint/v4:')&&previousPlanner.prompt_template.includes('whose Planner and Host responsibilities are explicit'))
        ||(previousPlanner?.prompt_template?.startsWith('Read analysis/request.txt once with read_workflow_resource;')&&previousPlanner.prompt_template.includes('exact static source contracts')&&previousPlanner.prompt_template.includes('whose Planner and Host responsibilities are explicit'))
        ||(previousPlanner?.prompt_template?.startsWith('Read analysis/request.txt in one complete sequential pass with read_workflow_resource_chunk:')&&previousPlanner.prompt_template.includes('exact static source contracts')&&previousPlanner.prompt_template.includes('workflow-semantic-blueprint/v5:'));
      const builtInReviewer=reviewerParts.builtIn||(fromContract==='codex-authoring-workflow/v10'&&digest(previousReviewer?.prompt_template??'')==='bda6a8b4ae03e18a1db4a5c6bff807837f9cc0b6aa65fbafc969aab0ff1e3c10')||(previousReviewer?.prompt_template?.startsWith('The upstream proposal binding is displayed once as JSON data in Declared workflow node inputs.')&&previousReviewer.prompt_template.includes('Report Provider/routing problems only under model_selection'))||(previousReviewer?.prompt_template?.startsWith(`Read ${AUTHORING_REVIEW_RESOURCE} in one complete sequential pass`)&&previousReviewer.prompt_template.includes('Report Provider/routing problems only under model_selection'));
      if(plannerParts.builtIn&&plannerParts.extension&&!legacyPlannerHash)plannerNode.prompt_template=AUTHORING_PLANNER_PROMPT_V27+plannerParts.extension;
      else if(typeof previousPlanner?.prompt_template==='string' && previousPlanner.prompt_template.trim() && !builtInPlanner)plannerNode.prompt_template=previousPlanner.prompt_template;
      if(reviewerParts.builtIn&&reviewerParts.extension)reviewerNode.prompt_template=AUTHORING_REVIEW_PROMPT_V22+reviewerParts.extension;
      else if(typeof previousReviewer?.prompt_template==='string' && previousReviewer.prompt_template.trim() && !builtInReviewer)reviewerNode.prompt_template=previousReviewer.prompt_template;
      if(typeof previousPlanner?.approval?.required==='boolean')plannerNode.approval.required=previousPlanner.approval.required;
      if(typeof previousReviewer?.approval?.required==='boolean')reviewerNode.approval.required=previousReviewer.approval.required;
      const migration=staleBuiltinCurrent
        ?{kind:'bundled_authoring_refresh',contract:definition.contract,from_prompt_sha256:digest(previousPlanner.prompt_template)}
        :staleProviderBinding&&fromContract===definition.contract
          ?{kind:'bundled_authoring_provider_binding',contract:definition.contract,planner_provider_id:plannerId,review_provider_id:reviewerId}
          :fromContract!==definition.contract
            ?{kind:'bundled_authoring_contract',from_contract:fromContract,to_contract:definition.contract}
            :{kind:'bundled_authoring_prompt_identity',contract:definition.contract};
      pack=await store.save(definition.id,workflow,{expected_revision:pack.revision_hash,resources:await store.resources(definition.id,pack.revision_hash),provenance:{...pack.provenance,builtin_contract:definition.contract,builtin_prompt_bases:builtinPromptBases(),migration}});
    }
    packs.push(pack);
  }
  return packs;
}

// The two built-ins are real Workflow constructors, not labels for a service
// state machine. Source-specific resources and Provider slots are materialized
// per Run while the stage topology and authority boundary stay invariant.
export function instantiateAuthoringWorkflow({definition,templateWorkflow,id,sourceName,planner,reviewer,planningResources,plannerResources=Object.keys(planningResources).sort(),reviewResources,plannerSchema,plannerPrompt,reviewSchema,reviewPrompt}){
  requireValue(AUTHORING_WORKFLOWS.some(item=>item.id===definition?.id),'AUTHORING_WORKFLOW_MISSING','Authoring Run needs a registered built-in Workflow');
  requireValue(planner?.kind==='native_agent','EXPANSION_EXECUTOR_UNAVAILABLE','Authoring requires a user-selected native planning Provider');
  const workflow={...structuredClone(templateWorkflow ?? createDraft(id,definition.name)),id,name:`${definition.name}: ${String(sourceName).slice(0,220)}`,revision:1,status:'ready',description:`Read-only ${definition.name} Run. The Host compiles its semantic output and a human explicitly publishes the resulting Draft.`,tags:['internal-authoring',definition.id,definition.source_kind],inputs_schema:{type:'object',required:['task'],additionalProperties:false,properties:{task:{type:'string',minLength:1,maxLength:2000}}},finalization:{required:true,node_id:'final'}};
  const common={type:'agent',access:'read_only',approval:{required:false},retry:{max_attempts:MAX_AUTHORING_ATTEMPTS},input_bindings:{},resources:plannerResources};
  const templatePlanner=workflow.nodes?.find(node=>node.id==='expand');
  const templateReviewer=workflow.nodes?.find(node=>node.id==='final');
  const host=(stage,name,tool,input_bindings)=>({id:stage,type:'tool',name,access:'read_only',executor:{kind:'tool',tool},approval:{required:false},retry:{max_attempts:1},input_bindings,resources:[],outputs_schema:{type:'object'}});
  workflow.nodes=[
    {id:'start',type:'start',name:'Host-pinned source snapshot'},
    {...common,id:'expand',approval:{required:templatePlanner?.approval?.required===true || planner.requires_user_approval===true},role:'implementer',executor:{kind:'provider',provider_id:planner.id},outputs_schema:plannerSchema,prompt_template:templatePlanner?.prompt_template ?? plannerPrompt},
    host('graph_assembly','Verify Host graph assembly','authoring-graph-assembly',{evidence:'/nodes/expand/output/host_pipeline/results/graph_assembly'}),
    host('execution_binding','Verify Host execution binding','authoring-execution-binding',{evidence:'/nodes/expand/output/host_pipeline/results/execution_binding',previous:'/nodes/graph_assembly/output'}),
    host('deterministic_validation','Verify Host deterministic validation','authoring-deterministic-validation',{evidence:'/nodes/expand/output/host_pipeline/results/deterministic_validation',previous:'/nodes/execution_binding/output'}),
    {...common,id:'final',retry:{max_attempts:DEFAULT_AGENT_ATTEMPTS},resources:reviewResources,input_bindings:{},approval:{required:templateReviewer?.approval?.required===true || reviewer?.requires_user_approval===true},role:'finalizer',executor:{kind:'main'},authoring_reviewer_provider_id:reviewer.id,...(reviewSchema?{outputs_schema:reviewSchema}:{}),prompt_template:templateReviewer?.prompt_template ?? reviewPrompt},
    {id:'end',type:'end',name:'Human publication boundary'},
  ];
  workflow.edges=stageEdges.map(({source,target})=>({id:`${source}-${target}`,source,target}));
  workflow.host_tools=authoringHostToolContracts();
  workflow.requirements={providers:[planner.id,reviewer.id],tools:['read_workflow_resource',...AUTHORING_HOST_TOOL_IDS],mcp_servers:[],executables:[]};
  return workflow;
}
