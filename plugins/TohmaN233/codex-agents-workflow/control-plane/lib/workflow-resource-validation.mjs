import { requireValue } from './workflow-paths.mjs';

export function requireWorkflowResourceClosure(workflow, manifest = []) {
  const known=new Set(manifest.map(item=>typeof item==='string'?item:item?.path).filter(path=>typeof path==='string'));
  for(const node of workflow?.nodes ?? []){
    const missing=(node.resources ?? []).filter(path=>!known.has(path));
    requireValue(missing.length===0,'WORKFLOW_RESOURCE_MISSING','A node references resources missing from the reviewed Workflow Pack',{node_id:node.id,missing});
  }
  return true;
}
