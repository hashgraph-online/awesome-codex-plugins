import { authoringReviewIdentity, isAuthoringRunProvenance } from '../authoring/authoring-workflows.mjs';
import { canonicalJSON } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { validateGenerationProposal } from './proposal-validation.mjs';
import { evaluateReview } from './review-checklist.mjs';

// One side-effect-free acceptance gate is shared by every human entry point.
// It binds the stored reviewer artifact to the current canonical proposal and
// re-evaluates the checklist before any terminal state or receipt is written.
export async function validateAuthoringAcceptance(runtime,record,attempt){
  const provenance=record.pins.root.provenance;
  requireValue(isAuthoringRunProvenance(provenance),'AUTHORING_HUMAN_ACCEPTANCE_REQUIRED','Acceptance applies only to one pinned authoring Run');
  const expected=authoringReviewIdentity(record);
  const proposed={proposal_hash:attempt?.result_proposal?.proposal_hash,source_revision:attempt?.result_proposal?.source_revision,expand_attempt_id:attempt?.result_proposal?.expand_attempt_id};
  requireValue(attempt?.result_proposal?.sha256&&canonicalJSON(proposed)===canonicalJSON(expected)
    &&canonicalJSON(attempt.dispatch?.receipt?.authoring_review_context)===canonicalJSON(expected),
  'AUTHORING_REVIEW_IDENTITY','Human acceptance has no reviewer result for the current canonical proposal');
  const completion=await runtime.runs.readExecutorResult(record.state.run_id,attempt.id,attempt.result_proposal.sha256);
  const pack=await runtime.workflows.snapshot(provenance.source_workflow_id,provenance.source_revision);
  const resources=await runtime.workflows.resources(provenance.source_workflow_id,provenance.source_revision);
  const validated=validateGenerationProposal(record.state.nodes.expand.output,{pack,resources,provenance,context:runtime.context,previousPlan:record.state.generation_repair?.previous_proposal ?? null,repairFeedback:record.state.generation_repair?.feedback ?? null});
  const review=Number.isInteger(provenance.review_contract_version)&&provenance.review_contract_version>=2
    ? evaluateReview(completion.structured_output,validated.proposal,resources,{version:provenance.review_contract_version})
    : completion.structured_output;
  requireValue(review?.approved===true&&Array.isArray(review.findings)&&review.findings.length===0,'GENERATION_REVIEW_BLOCKED','Every required review check must pass before acceptance');
  return {expected,completion,review,validated};
}
