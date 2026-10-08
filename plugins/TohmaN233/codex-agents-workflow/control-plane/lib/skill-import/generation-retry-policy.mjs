const SEMANTIC_CODES=new Set([
  'GENERATION_REVIEW_FINDINGS',
  'GENERATION_DETERMINISTIC_AUDIT',
  'AUTHORING_SEMANTIC',
  'EXPANSION_SOURCE_DISPOSITIONS',
  'EXPANSION_REQUIREMENT_COVERAGE',
  'EXPANSION_TOOL_BINDINGS',
  'EXPANSION_OPERATION_MODE',
]);
// One initial semantic plan followed by at most three automatic, patch-only
// repairs.  Explicit human continuations use the same patch contract but are
// outside this automatic budget.
export const MAX_SEMANTIC_REPAIRS=3;
export const MAX_PLANNER_ATTEMPTS=MAX_SEMANTIC_REPAIRS+1;
export const DEFAULT_AGENT_ATTEMPTS=3;
// The persisted node keeps a bounded reserve for explicit user-guided
// continuations after automatic repair is exhausted.
export const MAX_AUTHORING_ATTEMPTS=10;

// These failures concern fields or capabilities owned by the Host. They must
// stop visibly, never be converted into planner feedback, and never spend a
// semantic repair even if their code shares the EXPANSION_ namespace.
const MECHANICAL_CODES=new Set([
  'AUTHORING_DIAGNOSTIC_GAP',
  'AUTHORING_FORMAT',
  'AUTHORING_REPAIR_STATE',
  'AUTHORING_REPAIR_SCOPE',
  'AUTHORING_REVIEW_RESOURCE_LIMIT',
  'DATA_INVALID',
  'GENERATION_PROPOSAL_ENVELOPE',
  'GENERATION_PROPOSAL_JSON',
  'GENERATION_PROPOSAL_CONTRACT',
  'GENERATION_HOST_PROJECTION',
  'EXPANSION_GRAPH_INVALID',
  'ROUTING_CLASSIFICATION',
  'EXPANSION_WRITE_PROVIDER',
  'EXPANSION_THREAD_LIFECYCLE',
]);

export function isGenerationContractFailure(errorOrFeedback){
  const code=errorOrFeedback?.code ?? '';
  return SEMANTIC_CODES.has(code) || MECHANICAL_CODES.has(code) || code.startsWith('EXPANSION_');
}

export function generationRetryClass(errorOrFeedback){
  const code=errorOrFeedback?.code ?? 'GENERATION_UNKNOWN';
  return SEMANTIC_CODES.has(code)?'semantic':'mechanical';
}

export function semanticGenerationRepair(errorOrFeedback){
  return generationRetryClass(errorOrFeedback)==='semantic';
}
