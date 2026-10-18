import {requireValue} from '../workflow-paths.mjs';
import {validateData} from '../workflow-data-schema.mjs';
import {semanticResultSchema} from './host-main-automation.mjs';
import {bindingPointers} from '../workflow-bindings.mjs';

function inputBound(binding){
 return bindingPointers(binding).every(pointer=>pointer==='/inputs'||pointer.startsWith('/inputs/'));
}
/** An initial semantic decision may share the caller's start call. Effects,
 * approval, worker dispatch, loops and final acceptance remain later stages. */
export function startupSemanticNode(pack){
 const workflow=pack?.workflow,starts=workflow?.nodes?.filter(node=>node.type==='start')??[];
 const outgoing=starts.length===1?workflow.edges.filter(edge=>edge.source===starts[0].id):[];
 const node=outgoing.length===1?workflow.nodes.find(node=>node.id===outgoing[0].target):null;
 requireValue(workflow?.status==='ready'&&workflow.enabled!==false&&workflow.skill_policy?.mode==='cooperative'
  &&node?.type==='agent'&&node.executor?.kind==='main'&&node.executor.mode==='orchestration'
  &&node.id!==workflow.finalization?.node_id&&node.approval?.required!==true&&!node.fanout
  &&!(node.required_artifacts?.length)&&Object.values(node.input_bindings??{}).every(inputBound)
  &&Object.values(node.completion_contract?.host_check?.input_bindings??{}).every(inputBound)
  &&workflow.edges.filter(edge=>edge.target===node.id).length===1
  &&!(workflow.loops??[]).some(loop=>loop.node_ids?.includes(node.id)),
 'WORKFLOW_STARTUP_NOT_ELIGIBLE','Startup semantics require one input-bound initial current-Main node before effects, approval, fan-out, loops or final acceptance');
 return node;
}

export function startupSemanticContract(pack){
 const node=startupSemanticNode(pack);
 return {workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,prompt:node.prompt_template??'',
  input_bindings:structuredClone(node.input_bindings??{}),response_schema:semanticResultSchema(node),
  resources:(node.resources??[]).map(path=>{
   const resource=pack.resources?.find(item=>item.path===path);
   requireValue(resource,'WORKFLOW_STARTUP_RESOURCE','Initial semantic resource is not pinned: '+path);
   return {path:resource.path,sha256:resource.sha256,bytes:resource.bytes};
  })};
}

export function validateStartupSemanticSubmission(pack,args){
 requireValue(typeof args.revision_hash==='string'&&args.revision_hash===pack.revision_hash,
  'WORKFLOW_STARTUP_REVISION','Use the exact Host-generated startup contract revision; stale or missing pins cannot start a Run');
 const node=startupSemanticNode(pack);validateData(args.initial_output,semanticResultSchema(node));
 return {node_id:node.id,revision_hash:pack.revision_hash};
}
