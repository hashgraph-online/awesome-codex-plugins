import { authoringReviewIdentity, isAuthoringRunProvenance } from '../authoring/authoring-workflows.mjs';
import { canonicalJSON } from '../workflow-revisions.mjs';
import { validateWorkflowGraph } from '../workflow-validator.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { validateGenerationProposal } from './proposal-validation.mjs';
import { evaluateReview } from './review-checklist.mjs';
import { compileDeployableConversion, requireDeployableConvertedSnapshot } from './conversion-deployment.mjs';

// Inspection never claims a node, adopts authority, collects a session or
// advances the authoring pipeline. Durable evidence survives a Workbench reload.
export async function readAuthoringPreview(runtime, record, { store, context }) {
  const { state, pins } = record, provenance = pins.root.provenance;
  requireValue(isAuthoringRunProvenance(provenance), 'GENERATION_RUN', 'Preview requires a pinned authoring Run');
  const source = { workflow_id: provenance.source_workflow_id, expected_revision: provenance.source_revision };
  const base = { run_id: state.run_id, status: state.status, sequence: record.sequence, source, read_only: true,
    completion_policy: structuredClone(provenance.completion_policy ?? {mode:'manual',target:'draft'}) };
  const final = state.nodes.final, attempt = final?.attempts.find(item => item.id === final.active_attempt_id);
  if (!attempt?.result_proposal) {
    if (state.generation_repair?.awaiting_user_input) return { ...base, phase: 'user_input_required', feedback: state.generation_repair.feedback };
    return { ...base, phase: 'attention', error: state.error ?? { code: 'AUTHORING_PREVIEW_PENDING', message: 'The existing authoring Run has not saved its final review yet. Open its details to continue.' } };
  }
  const expected = authoringReviewIdentity(record);
  const proposed = { proposal_hash: attempt.result_proposal.proposal_hash, source_revision: attempt.result_proposal.source_revision, expand_attempt_id: attempt.result_proposal.expand_attempt_id };
  requireValue(canonicalJSON(proposed) === canonicalJSON(expected) && canonicalJSON(attempt.dispatch?.receipt?.authoring_review_context) === canonicalJSON(expected),
    'AUTHORING_REVIEW_IDENTITY', 'Saved reviewer evidence does not identify the current canonical proposal');
  const completion = await runtime.runs.readExecutorResult(state.run_id, attempt.id, attempt.result_proposal.sha256);
  requireValue(completion?.status === 'succeeded' && completion.structured_output, 'AUTHORING_PREVIEW_RESULT', 'Saved reviewer artifact is not a successful structured result');
  const pack = await store.snapshot(source.workflow_id, source.expected_revision);
  const resources = await store.resources(source.workflow_id, source.expected_revision);
  const validated = validateGenerationProposal(state.nodes.expand.output, { pack, resources, provenance, context,
    previousPlan: state.generation_repair?.previous_proposal ?? null, repairFeedback: state.generation_repair?.feedback ?? null });
  requireValue(validated.compiled.proposal_hash === expected.proposal_hash, 'AUTHORING_REVIEW_IDENTITY', 'Current compiler output differs from the saved reviewed proposal');
  const review = evaluateReview(completion.structured_output, validated.proposal, resources, { version: provenance.review_contract_version });
  const deployed = compileDeployableConversion({ workflow: validated.compiled.workflow, proposal: validated.proposal, resources, pack,
    proposalHash: expected.proposal_hash, reviewContractVersion: provenance.review_contract_version });
  requireDeployableConvertedSnapshot({ ...deployed, resources: Object.keys(deployed.resources).map(path => ({ path })),resourceBytes:deployed.resources });
  return { ...base, phase: 'review_required', proposal: validated.proposal, workflow: deployed.workflow, validation: validateWorkflowGraph(deployed.workflow,context),
    review: { ...completion, structured_output: review }, preview_identity: { ...expected, final_attempt_id: attempt.id, review_result_sha256: attempt.result_proposal.sha256 } };
}

export async function discoverAuthoringPreview(runtime, args, dependencies) {
  requireValue(typeof args.workflow_id === 'string' && /^[a-f0-9]{64}$/.test(args.revision_hash), 'AUTHORING_PREVIEW_SOURCE', 'Discovery needs the exact source Workflow and revision');
  await dependencies.store.snapshot(args.workflow_id, args.revision_hash);
  const records = [];
  for (const item of await runtime.runs.list()) {
    if (['failed', 'cancelled'].includes(item.status)) continue;
    const record = await runtime.runs.read(item.run_id), provenance = record.pins.root.provenance;
    if (isAuthoringRunProvenance(provenance) && provenance.source_workflow_id === args.workflow_id && provenance.source_revision === args.revision_hash) records.push(record);
  }
  const candidates = records.map(({ state, sequence }) => ({ run_id: state.run_id, status: state.status, sequence, updated_at: state.updated_at }));
  const selected = args.run_id ? records.find(record => record.state.run_id === args.run_id) : records.length === 1 ? records[0] : null;
  requireValue(!args.run_id || selected, 'AUTHORING_PREVIEW_SOURCE', 'Selected authoring Run does not belong to this exact source revision');
  return { candidates, preview: selected ? await readAuthoringPreview(runtime, selected, dependencies) : null };
}
