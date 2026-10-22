import { requireValue } from '../workflow-paths.mjs';
import { normalizeExecutableRequirements, normalizeNodeRuntimeRequirements } from '../runtime-requirements.mjs';

export function validateRuntimeActivation(value){
  requireValue(value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===2
    &&Object.keys(value).every(key=>['condition_node_id','branch_label'].includes(key))
    &&typeof value.condition_node_id==='string'&&/^[A-Za-z][A-Za-z0-9_-]{0,127}$/.test(value.condition_node_id)
    &&typeof value.branch_label==='string'&&value.branch_label.trim()&&value.branch_label.length<=256&&!/[\x00-\x1f]/.test(value.branch_label),
    'EXPANSION_RUNTIME_ACTIVATION','Runtime activation needs an exact condition node ID and original branch label');
}

// Only an explicit activation establishes executable authority. Topology must
// prove that no other branch or bypass can enter any mapped consumer.
export function conditionalRuntimeProjection(requirement,mapping,nodes,edges,resources){
  const activation=mapping.runtime_activation;
  if(!activation)return {reason:'typed runtime_activation is missing'};
  validateRuntimeActivation(activation);
  if(requirement.details?.phase!=='conditional')return {reason:'source phase is not conditional execution'};
  const [descriptor]=normalizeExecutableRequirements([{name:requirement.details.executable,
    ...(requirement.details.version?{version:requirement.details.version}:{}),...(requirement.details.python_modules?{python_modules:requirement.details.python_modules}:{})}]);
  const evidence=(requirement.source_spans??[]).map(span=>resources[span.resource]?.toString('utf8').split('\n').slice(span.start_line-1,span.end_line).join('\n')??'').join('\n');
  const token=value=>new RegExp(`(^|[^A-Za-z0-9_.+-])${value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?=$|[^A-Za-z0-9_.+-])`,'i').test(evidence);
  if(!token(descriptor.name))return {reason:'source evidence does not name the typed executable'};
  for(const version of descriptor.version?.match(/\d+(?:\.\d+)*/g)??[]){
    let short=version;while(short.endsWith('.0'))short=short.slice(0,-2);
    if(!token(version)&&!token(short))return {reason:'source evidence does not retain the typed version'};
  }
  if((descriptor.python_modules??[]).some(module=>!token(module)))return {reason:'source evidence does not name the typed Python modules'};
  const condition=nodes.find(node=>node.id===activation.condition_node_id);
  if(condition?.type!=='condition')return {reason:'activation does not name a condition node'};
  const routes=edges.filter(edge=>edge.source===condition.id);
  const selected=edge=>(edge.on??'success')==='success'&&edge.label===activation.branch_label;
  const labels=[...(condition.cases??[]).map(item=>item.label),condition.default_label];
  if(routes.length<2||!labels.includes(activation.branch_label)||!routes.some(selected))return {reason:'activation does not name an existing exclusive branch edge'};
  const reaches=(source,target,blocked)=>{const seen=new Set(),queue=[source];while(queue.length){const id=queue.shift();if(id===blocked||seen.has(id))continue;if(id===target)return true;seen.add(id);queue.push(...edges.filter(edge=>edge.source===id).map(edge=>edge.target));}return false;};
  if(!reaches('start',condition.id))return {reason:'activation condition is not reachable from start'};
  const consumers=(mapping.node_ids??[]).map(id=>nodes.find(node=>node.id===id));
  if(!consumers.length||consumers.some(node=>!node||!['agent','tool','skill_ref','subworkflow'].includes(node.type)))return {reason:'mapping contains a shared router or non-executable consumer'};
  if(consumers.some(node=>reaches('start',node.id,condition.id)
    ||!routes.some(edge=>selected(edge)&&reaches(edge.target,node.id))
    ||routes.some(edge=>!selected(edge)&&reaches(edge.target,node.id))))return {reason:'condition does not exclusively dominate every mapped consumer'};
  return {descriptor,activation:structuredClone(activation),node_ids:consumers.map(node=>node.id)};
}

export function projectedNodeRuntimeRequirements(coverage){
  const scopes=new Map();
  for(const item of coverage){if(item.status!=='compiled'||item.requirement_kind!=='dependency'||item.details?.phase!=='conditional'||!item.runtime_activation)continue;
    for(const nodeId of item.node_ids){const scope=scopes.get(nodeId)??{executables:[],source_requirement_ids:[]};
      scope.executables.push({name:item.details.executable,...(item.details.version?{version:item.details.version}:{}),...(item.details.python_modules?{python_modules:item.details.python_modules}:{})});scope.source_requirement_ids.push(item.requirement_id);scopes.set(nodeId,scope);}
  }
  return [...scopes].map(([node_id,scope])=>({node_id,runtime_requirements:normalizeNodeRuntimeRequirements(scope)}));
}
