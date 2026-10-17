import {canonicalJSON} from '../workflow-revisions.mjs';

function observation(snapshot,path,side){
  const value=snapshot.get(path)??null;
  return value?.startsWith('metadata:')?{[`${side}_sha256`]:null,[`${side}_metadata_sha256`]:value.slice(9)}:{[`${side}_sha256`]:value};
}

// Preserve the exact evidence before managers release their in-memory snapshots.
// This diagnostic never exempts caches or other writes from the declared scope.
export async function rejectWorkspaceScope({runtime,runId,attemptId,code,changed,outside,before,after,event}) {
  const sample=outside.slice(0,3).join(', ').slice(0,700);
  const violation=Object.assign(new Error(`Changed ${outside.length} path(s) outside declared write scope: ${sample}`),{code});
  const report={schema:'workspace-scope-violation/v1',run_id:runId,attempt_id:attemptId,
    changed_paths:changed,outside_paths:outside,
    changes:changed.map(path=>({path,...observation(before,path,'before'),...observation(after,path,'after'),
      ...(before.unreadablePaths?.has(path)?{before_unreadable:before.unreadablePaths.get(path)}:{}),
      ...(after.unreadablePaths?.has(path)?{after_unreadable:after.unreadablePaths.get(path)}:{})}))};
  try {
    const reference=await runtime.runs.saveArtifact(runId,`scope-${attemptId}`,canonicalJSON(report));
    await event('scope_violation',{...reference,changed_count:changed.length,outside_count:outside.length});
    violation.message+=`; evidence: ${reference.artifact}`;
  } catch(error) {
    throw Object.assign(new AggregateError([violation,error],'Workspace scope violation and evidence persistence failure'),{code});
  }
  throw violation;
}
