import { requireValue } from './workflow-paths.mjs';
import { hostCompletionResourcePaths } from './execution/host-completion-resources.mjs';

export function requireWorkflowResourceClosure(workflow, manifest = []) {
  const known=new Set(manifest.map(item=>typeof item==='string'?item:item?.path).filter(path=>typeof path==='string'));
  for(const node of workflow?.nodes ?? []){
    const check=node.completion_contract?.host_check;
    const contract=check ? workflow.host_tools?.find(tool=>tool.id===check.tool) : null;
    const required=[...(node.resources ?? []),...(contract ? hostCompletionResourcePaths(contract,node.resources??[]) : [])];
    const missing=[...new Set(required.filter(path=>!known.has(path)))];
    requireValue(missing.length===0,'WORKFLOW_RESOURCE_MISSING','A node references resources missing from the reviewed Workflow Pack',{node_id:node.id,missing});
  }
  return true;
}
