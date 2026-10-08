import { sourceRepairLoopIntentFindings } from '../authoring/semantic-loops.mjs';
import { CONVERSION_CONTRACT, HOST_OWNED_REVIEW_IDS } from './conversion-contract.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { projectObservedRequirements } from './source-requirements.mjs';
import { sourceSectionInventory, validateSourceDispositions } from './source-dispositions.mjs';
import { SEMANTIC_BLUEPRINT_SCHEMA } from '../authoring/blueprint-contract.mjs';

export const REVIEW_IDS = CONVERSION_CONTRACT.checks.map(check=>check.id);
const V2_REVIEW_IDS = ['parallelism','agent_ownership','human_intervention','model_selection','phase_order','hard_rules','data_handoffs','failure_semantics','conversation_inputs','human_confirmation','conditional_dependencies','portable_artifact','source_support','review_scope'];
const V3_REVIEW_IDS = ['parallelism','agent_ownership','human_intervention','model_selection','phase_order','hard_rules','requirement_coverage','data_handoffs','failure_semantics','conversation_inputs','human_confirmation','conditional_dependencies','portable_artifact','source_support','review_scope'];
const V4_REVIEW_IDS = ['parallelism','agent_ownership','human_intervention','model_selection','phase_order','hard_rules','requirement_coverage','data_handoffs','failure_semantics','conversation_inputs','human_confirmation','conditional_dependencies','portable_artifact','source_support','review_scope','artifact_interface_contract','method_fidelity','dependency_binding','validation_strength','cross_resource_consistency'];
const V5_TO_V7_REVIEW_IDS = [...V4_REVIEW_IDS.slice(0,16),'host_canonicalization',...V4_REVIEW_IDS.slice(16)];
export function reviewIds(version = CONVERSION_CONTRACT.version) {
  requireValue(Number.isInteger(version) && version>=2 && version<=CONVERSION_CONTRACT.version,'GENERATION_REVIEW_VERSION','Unsupported generation review contract version');
  if (version === 2) return V2_REVIEW_IDS;
  if (version === 3) return V3_REVIEW_IDS;
  if (version === 4) return V4_REVIEW_IDS;
  if ([5,6,7].includes(version)) return V5_TO_V7_REVIEW_IDS;
  return REVIEW_IDS;
}
const strings = {type:'array',maxItems:800,items:{type:'string',minLength:1,maxLength:128}};
export function reviewSchema(version = CONVERSION_CONTRACT.version) { const ids=reviewIds(version); return version>=14
  ? {type:'object',required:['checks'],additionalProperties:false,properties:{checks:{type:'array',minItems:ids.length,maxItems:ids.length,items:{
    type:'object',required:['status','evidence'],additionalProperties:false,properties:{
      status:{type:'string',enum:['pass','fail','not_applicable']},evidence:{type:'string',minLength:1,maxLength:4000},
    },
  }}}}
  : {type:'object',required:['checks'],additionalProperties:false,properties:{checks:{type:'array',minItems:ids.length,maxItems:ids.length,items:{
  type:'object',required:['id','status','evidence','node_ids','edge_ids','source_spans'],additionalProperties:false,properties:{
    id:{type:'string',enum:ids},status:{type:'string',enum:['pass','fail','not_applicable']},evidence:{type:'string',minLength:1,maxLength:4000},
    node_ids:strings,edge_ids:strings,source_spans:{type:'array',maxItems:200,items:{type:'object',required:['resource','start_line','end_line'],additionalProperties:false,properties:{resource:{type:'string',minLength:1,maxLength:1024},start_line:{type:'integer',minimum:1},end_line:{type:'integer',minimum:1}}}},
  },
}}}}; }
// These checks audit fields that the canonical proposal receives from the
// Host.  A failed check remains a release blocker, but sending it to the
// semantic planner cannot repair it and only burns another model attempt.
export { HOST_OWNED_REVIEW_IDS };
const hostOwnedReviewIds = new Set(HOST_OWNED_REVIEW_IDS);
function findingCheckId(finding) { return /^\[([^\]]+)\]/.exec(finding)?.[1] ?? null; }
// Mixed checks can mention a Host field to *exclude* it as the proposed fix.
// Ownership follows the check ID or an explicit assertion that a projected
// field itself is defective, never a bare substring in explanatory prose.
const assertedHostProjection = text => /^(?:\[[^\]]+\]\s*)?(?:The\s+)?Host-projected\s+(?:required_artifacts|requirement_ids|input_bindings|resource_refs|source_spans|provider_choice|execution_target)\b/i.test(text)
  || /^(?:\[[^\]]+\]\s*)?Host projection defect:/i.test(text);
const hostOwnedFinding = finding => hostOwnedReviewIds.has(findingCheckId(finding)) || assertedHostProjection(finding);
const hostOwnedRow = row => hostOwnedReviewIds.has(row.id) || assertedHostProjection(row.evidence);
export function routeReviewFindings(findings) {
  const semantic_findings=[],host_findings=[];
  for (const finding of findings) (hostOwnedFinding(finding)?host_findings:semantic_findings).push(finding);
  return {semantic_findings,host_findings};
}

// Field paths are reviewer guidance and a static contract-coherence check,
// not a second permission system. Stable semantic keys bound the repair.
const editableFields=Object.freeze({
  parallelism:['sequences','parallels','activities.inputs','activities.fanout'],agent_ownership:['activities.profile','activities.fanout'],human_intervention:['approvals','activities.inputs'],phase_order:['activities','sequences','choices','activities.inputs','activities.outputs'],hard_rules:['activities.instructions','activities.source_sections','activities.contract_refs'],requirement_coverage:['source_dispositions','requirement_assignments'],data_handoffs:['activities.inputs','activities.outputs','activities.fanout','approvals.subject'],failure_semantics:['loops','activities.on_missing','activities.outcome','activities.fail_on_false','activities.repeat_until','activities.instructions','activities.outputs'],conversation_inputs:['activities.inputs','activities.on_missing'],human_confirmation:['approvals.subject','approvals.before'],conditional_dependencies:['activities.contract_refs','choices'],portable_artifact:['activities.outputs','activities.contract_refs'],review_scope:['activities.profile'],artifact_interface_contract:['activities.contract_refs','activities.outputs.contract_ref'],method_fidelity:['activities.instructions','activities.contract_refs'],validation_strength:['loops','activities.outputs.contract_ref','activities.fail_on_false','activities.repeat_until','activities.fanout'],source_disposition:['source_dispositions'],
});
function schemaHasPath(path){
  let schema=SEMANTIC_BLUEPRINT_SCHEMA;
  for(const part of path.split('.')){
    if(schema?.type==='array')schema=schema.items;
    schema=schema?.properties?.[part];
    if(!schema)return false;
  }
  return true;
}
for(const id of REVIEW_IDS){
  if(hostOwnedReviewIds.has(id))continue;
  const fields=editableFields[id];
  if(!fields?.length||fields.some(field=>!schemaHasPath(field)))throw new Error(`Review check ${id} has no expressible semantic repair path`);
}
function repairTargets(rows,proposal,owner,resources){
  const nodeKeys=new Map((proposal.nodes??[]).map(node=>[node.id,node.semantic_key??node.id])),edges=new Map((proposal.edges??[]).map(edge=>[edge.id,edge])),groups=new Map();
  const sections=sourceSectionInventory(resources);
  const mentions=(evidence,id)=>new RegExp(`(?:^|[^A-Za-z0-9_-])${id}(?=$|[^A-Za-z0-9_-])`).test(evidence??'');
  const overlaps=(left,right)=>left.resource===right.resource&&left.start_line<=right.end_line&&right.start_line<=left.end_line;
  for(const row of rows){
    const citedNodeIds=(row.node_ids??[]).filter(id=>mentions(row.evidence,id));
    const citedEdgeIds=(row.edge_ids??[]).filter(id=>mentions(row.evidence,id));
    const targetEdgeIds=citedNodeIds.length?citedEdgeIds:citedEdgeIds.length?citedEdgeIds:row.edge_ids??[];
    const edgeKeys=targetEdgeIds.flatMap(id=>{const edge=edges.get(id);return edge?[nodeKeys.get(edge.source),nodeKeys.get(edge.target)]:[];});
    const graphKeys=[...(citedNodeIds.length?citedNodeIds:row.node_ids??[]).map(id=>nodeKeys.get(id)),...edgeKeys].filter(Boolean);
    const locateSection=row.id==='source_disposition'||graphKeys.length===0;
    const citedSections=sections.filter(section=>mentions(row.evidence,section.section_id));
    const requirements=proposal.source_requirements??[],citedRequirements=requirements.filter(requirement=>mentions(row.evidence,requirement.requirement_id));
    const locateRequirement=row.id==='requirement_coverage'||citedRequirements.length>0;
    const sourceKeys=(row.source_spans??[]).flatMap(span=>[
      ...(locateSection?(citedSections.length?citedSections:sections.filter(section=>overlaps(section.source_span,span))).map(section=>section.section_id):[]),
      ...(locateRequirement?(citedRequirements.length?citedRequirements:requirements.filter(requirement=>(requirement.source_spans??[]).some(source=>overlaps(source,span)))).map(requirement=>requirement.requirement_id):[]),
    ]);
    const semantic_keys=[...new Set([...graphKeys,...sourceKeys])].sort(),fields=[...(editableFields[row.id]??[])];
    if((row.edge_ids??[]).length)fields.push('activities.inputs','sequences','parallels','choices','approvals.before');
    const spanKey=JSON.stringify(row.source_spans??[]),key=JSON.stringify([owner,semantic_keys,spanKey]);
    const current=groups.get(key)??{owner,check_ids:[],semantic_keys,affected_semantic_fields:[],source_spans:structuredClone(row.source_spans??[]),evidence:[],minimal_change:''};
    current.check_ids.push(row.id);current.affected_semantic_fields.push(...fields);current.evidence.push(row.evidence);groups.set(key,current);
  }
  return [...groups.values()].map((item,index)=>({...item,target_id:`${owner}_repair_${String(index+1).padStart(3,'0')}`,check_ids:[...new Set(item.check_ids)],affected_semantic_fields:[...new Set(item.affected_semantic_fields)],evidence:[...new Set(item.evidence)],minimal_change:`At semantic key(s) ${item.semantic_keys.join(', ')||'<unlocalized>'}: ${[...new Set(item.evidence)].join(' | ')}. Add or remove linked semantic entities when required; field paths are guidance, not an edit ban.`}));
}

function deterministicRepairTarget(finding,proposal,index){
  const id=findingCheckId(finding),fields=[...(editableFields[id]??[])],nodeKeys=new Map((proposal.nodes??[]).map(node=>[node.id,node.semantic_key??node.id]));
  const keys=[],source_spans=[];
  for(const [nodeId,key] of nodeKeys)if(finding.includes(nodeId))keys.push(key);
  for(const requirement of proposal.source_requirements??[])if(finding.includes(requirement.requirement_id)){keys.push(requirement.requirement_id);source_spans.push(...(requirement.source_spans??[]));fields.push('requirement_assignments');const mapping=(proposal.requirement_mappings??[]).find(item=>item.requirement_id===requirement.requirement_id);for(const nodeId of mapping?.node_ids??[])if(nodeKeys.has(nodeId))keys.push(nodeKeys.get(nodeId));}
  for(const disposition of proposal.source_dispositions??[])if(finding.includes(disposition.section_id)){keys.push(disposition.section_id);fields.push('source_dispositions');}
  return {target_id:`planner_repair_${String(index+1).padStart(3,'0')}`,owner:'planner',check_ids:id?[id]:[],semantic_keys:[...new Set(keys)].sort(),affected_semantic_fields:[...new Set(fields)],source_spans:[...new Map(source_spans.map(span=>[JSON.stringify(span),span])).values()],evidence:[finding],minimal_change:finding};
}

// Portable-artifact evidence can legitimately be a graph-only portability
// conclusion when the source declares no path contract. Drop a bad optional
// citation there instead of retrying the whole review merely to repair a line
// number. Every other check remains fail-closed on malformed source evidence;
// mandatory checks also fail below if no valid span remains.
const OPTIONAL_SOURCE_EVIDENCE = new Set(['portable_artifact']);
export function normalizeReviewEvidence(value, resources, proposal=null) {
  if (!value || typeof value!=='object' || !Array.isArray(value.checks)) return value;
  const normalized=structuredClone(value);
  const knownEdges=new Set((proposal?.edges??[]).map(edge=>edge.id));
  for(const row of normalized.checks)if(Array.isArray(row?.edge_ids))row.edge_ids=[...new Set(row.edge_ids.map(id=>{
    // Reviewers sometimes abbreviate the Host's edge_001 as e001. This is
    // an exact, reversible spelling normalization, not evidence fabrication:
    // unknown or ambiguous IDs still fail the checklist contract below.
    const alias=/^e(\d+)$/.exec(id);
    const canonical=alias?`edge_${alias[1]}`:id;
    return alias&&knownEdges.has(canonical)?canonical:id;
  }))];
  for (const row of normalized.checks) if (OPTIONAL_SOURCE_EVIDENCE.has(row?.id) && Array.isArray(row.source_spans)) row.source_spans=row.source_spans.filter(span=>{
    const bytes=span && Object.hasOwn(resources,span.resource) ? resources[span.resource] : null;
    return Boolean(bytes && Object.keys(span).length===3 && Number.isInteger(span.start_line) && Number.isInteger(span.end_line)
      && span.start_line>=1 && span.end_line>=span.start_line && span.end_line<=bytes.toString('utf8').split('\n').length);
  });
  return normalized;
}

function projectOrderedReviewEvidence(value,resources,proposal,version){
  const ids=reviewIds(version);
  requireValue(value&&Object.keys(value).length===1&&Array.isArray(value.checks)&&value.checks.length===ids.length,
    'GENERATION_CHECKLIST_INVALID','Return one semantic verdict for every checklist entry in Host order');
  const spans=[...new Map(sourceSectionInventory(resources).map(item=>[JSON.stringify(item.source_span),item.source_span])).values()];
  requireValue(spans.length<=200,'GENERATION_CHECKLIST_INVALID','Host source evidence exceeds the review protocol limit');
  const nodeIds=(proposal.nodes??[]).map(node=>node.id),edgeIds=(proposal.edges??[]).map(edge=>edge.id);
  return {checks:value.checks.map((row,index)=>{
    requireValue(row&&Object.keys(row).length===2&&['pass','fail','not_applicable'].includes(row.status)&&
      typeof row.evidence==='string'&&row.evidence.trim()&&row.evidence.length<=4000,
    'GENERATION_CHECKLIST_INVALID',`Invalid semantic verdict at Host checklist position ${index}`);
    return {id:ids[index],status:row.status,evidence:row.evidence,node_ids:[...nodeIds],edge_ids:[...edgeIds],source_spans:structuredClone(spans)};
  })};
}

function deterministicFindings(proposal, resources, version) {
  const requirements = proposal.source_requirements ?? [];
  const nodes = new Map((proposal.nodes ?? []).map(node => [node.id, node]));
  const mappings = new Map((proposal.requirement_mappings ?? []).map(mapping => [mapping.requirement_id, mapping]));
  const findings = sourceRepairLoopIntentFindings(proposal,resources).map(item=>`[failure_semantics] ${item.message}`);
  for (const requirement of requirements) {
    const mapping = mappings.get(requirement.requirement_id);
    if (!mapping) { findings.push(`[requirement_coverage] ${requirement.requirement_id} has no mapping.`); continue; }
    const mapped = (mapping.node_ids ?? []).map(id => nodes.get(id)).filter(Boolean);
    if ((mapping.node_ids ?? []).length !== mapped.length) findings.push(`[requirement_coverage] ${requirement.requirement_id} maps an unknown node.`);
    if (mapping.status === 'unsupported') findings.push(`[requirement_coverage] ${requirement.requirement_id} remains unsupported and cannot pass the v4 conversion gate.`);
    if (mapping.status === 'agent_assisted' && mapping.rationale?.startsWith('Host-projected to resource-consuming nodes because the planner supplied no semantic mapping')) findings.push(`[requirement_coverage] ${requirement.requirement_id} was routed to review without a planner-supplied semantic mapping.`);
    if (mapping.status === 'compiled') {
      if (!mapped.length || mapped.some(node => !(node.requirement_ids ?? []).includes(requirement.requirement_id))) findings.push(`[host_canonicalization] ${requirement.requirement_id} is compiled without explicit node requirement_ids.`);
      if (!(mapping.binding_names ?? []).every(name => mapped.some(node => Object.hasOwn(node.input_bindings ?? {}, name) || Object.hasOwn(node.outputs_schema?.properties ?? {},name)))) findings.push(`[data_handoffs] ${requirement.requirement_id} names a binding absent from mapped inputs and outputs.`);
      if (requirement.requirement_kind === 'artifact_path' && !mapped.some(node => node.type === 'tool' || (node.type === 'agent' && node.operation_mode === 'write'))) findings.push(`[artifact_interface_contract] ${requirement.requirement_id} has no concrete write producer.`);
      if (requirement.requirement_kind === 'canonicalization' && !mapped.some(node => node.type === 'tool')) findings.push(`[host_canonicalization] ${requirement.requirement_id} is marked compiled without a pre-authorized host-tool node.`);
      if (requirement.requirement_kind === 'method_rule' && !mapped.some(node => node.type === 'tool' || (node.resource_refs ?? []).some(ref => (requirement.resource_refs ?? []).includes(ref)))) findings.push(`[method_fidelity] ${requirement.requirement_id} does not project its pinned method reference.`);
      if (requirement.requirement_kind === 'dependency' && !requirement.details?.executable) findings.push(`[dependency_binding] ${requirement.requirement_id} has no typed executable.`);
    }
  }
  if (version >= 8) for (const finding of validateSourceDispositions(proposal,resources)) findings.push(`[source_disposition] ${finding.section_id ?? 'source'}: ${finding.reason}`);
  return findings;
}

// Model review is evidence gathering.  Deterministic coverage is merged below,
// so an all-pass model result can never override a missing contract.
export function evaluateReview(value, proposal, resources, {version = CONVERSION_CONTRACT.version} = {}) {
  value = version>=14?projectOrderedReviewEvidence(value,resources,proposal,version):normalizeReviewEvidence(value,resources,proposal);
  if(version>=8)proposal = projectObservedRequirements(proposal, resources);
  const ids=reviewIds(version);
  const check=(condition,message)=>requireValue(condition,'GENERATION_CHECKLIST_INVALID',message);
  check(value && Object.keys(value).length===1 && Array.isArray(value.checks) && value.checks.length===ids.length,version>=14?'Return exactly one verdict for every Host-ordered checklist entry; no self-declared approved field':'Return every checklist ID exactly once; no self-declared approved field');
  const nodes=new Set(proposal.nodes.map(n=>n.id));const edges=new Set(proposal.edges.map(e=>e.id));const seen=new Set();
  const sourceRequirements=proposal.source_requirements ?? [];const mappings=proposal.requirement_mappings ?? [];
  const approvalRequired=sourceRequirements.some(item=>item.requirement_kind==='approval');
  for(const row of value.checks){
    check(row && ids.includes(row.id) && !seen.has(row.id),'Unknown or duplicate checklist ID');seen.add(row.id);
    check(Object.keys(row).length===6 && ['pass','fail','not_applicable'].includes(row.status) && typeof row.evidence==='string' && row.evidence.trim() && row.evidence.length<=4000,`Invalid result/evidence for ${row.id}`);
    for(const [field,known] of [['node_ids',nodes],['edge_ids',edges]])check(Array.isArray(row[field]) && row[field].length<=800 && new Set(row[field]).size===row[field].length && row[field].every(id=>known.has(id)),`Invalid ${field} in ${row.id}`);
    check(Array.isArray(row.source_spans) && row.source_spans.length<=200,`Missing source spans in ${row.id}`);
    for(const span of row.source_spans){const bytes=span && Object.hasOwn(resources,span.resource)?resources[span.resource]:null;
      check(bytes && Object.keys(span).length===3 && Number.isInteger(span.start_line) && Number.isInteger(span.end_line) && span.start_line>=1 && span.end_line>=span.start_line && span.end_line<=bytes.toString('utf8').split('\n').length,`Invalid source evidence in ${row.id}`);
    }
    const typedChecks = {artifact_interface_contract:['artifact_path','artifact_schema'],host_canonicalization:['canonicalization'],method_fidelity:['method_rule'],dependency_binding:['dependency'],validation_strength:['artifact_path','artifact_schema','canonicalization','method_rule','dependency'],cross_resource_consistency:['artifact_path','artifact_schema','canonicalization','method_rule','dependency']};
    if(row.status==='not_applicable') {
      const kinds=typedChecks[row.id]??[];
      const hasTyped=sourceRequirements.some(item=>kinds.includes(item.requirement_kind));
      check((['conversation_inputs','human_intervention','human_confirmation','conditional_dependencies'].includes(row.id) && !(['human_intervention','human_confirmation'].includes(row.id) && approvalRequired)) || (version >= 4 && Object.hasOwn(typedChecks,row.id) && !hasTyped),`Rule ${row.id} cannot be marked not applicable`);
    }
    if(['phase_order','hard_rules','requirement_coverage','source_support','source_disposition'].includes(row.id))check(row.source_spans.length>0,`Rule ${row.id} needs source evidence`);
    if(row.id==='source_support' && row.status==='pass'){
      const semanticEdges=proposal.edges.filter(edge=>nodes.has(edge.source)&&nodes.has(edge.target));
      check([...nodes].every(id=>row.node_ids.includes(id)) && semanticEdges.every(edge=>row.edge_ids.includes(edge.id)),'A passing source-support review must cover every semantic node and edge');
    }
  }
  const failedRows=value.checks.filter(c=>c.status==='fail'),findings=[...(version >= 4 ? deterministicFindings(proposal,resources,version) : []),...failedRows.map(c=>`[${c.id}] ${c.evidence}`)];
  if(approvalRequired && !proposal.nodes.some(node=>node.type==='human_gate'))findings.push('[requirement_coverage] A source approval requirement has no human_gate.');
  const mapped=new Set(mappings.map(item=>item.requirement_id));
  if(version<4)for(const requirement of sourceRequirements)if(!mapped.has(requirement.requirement_id))findings.push(`[requirement_coverage] ${requirement.requirement_id} has no mapping.`);
  const routed=routeReviewFindings(findings),semanticRows=failedRows.filter(row=>!hostOwnedRow(row)),hostRows=failedRows.filter(hostOwnedRow);
  const semantic_repair_targets=repairTargets(semanticRows,proposal,'planner',resources),host_repair_targets=repairTargets(hostRows,proposal,'host',resources);
  for(const finding of routed.semantic_findings.filter(item=>!failedRows.some(row=>`[${row.id}] ${row.evidence}`===item)))semantic_repair_targets.push(deterministicRepairTarget(finding,proposal,semantic_repair_targets.length));
  return {approved:findings.length===0,findings,...routed,semantic_repair_targets,host_repair_targets,checks:value.checks};
}
