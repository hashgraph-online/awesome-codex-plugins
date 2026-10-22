import { canonicalJSON } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';

export function authoringCompletionPolicy(preference='automatic') {
  requireValue(['automatic','manual'].includes(preference),'AUTHORING_COMPLETION_POLICY','Authoring completion policy must be automatic or manual');
  return {mode:preference,target:preference==='automatic'?'launch_ready':'draft'};
}

// Missing pins are historical, explicitly human-controlled Runs. Never adopt
// current defaults while recovering an existing Run.
export function automaticAuthoringCompletion(provenance) {
  const policy=provenance?.completion_policy;
  if(policy===undefined)return false;
  requireValue(canonicalJSON(policy)===canonicalJSON(authoringCompletionPolicy(policy?.mode)),
    'AUTHORING_COMPLETION_POLICY','Pinned authoring completion policy is malformed');
  return policy.mode==='automatic';
}
