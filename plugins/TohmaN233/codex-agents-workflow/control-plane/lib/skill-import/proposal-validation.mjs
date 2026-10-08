import { sourceRepairLoopIntentFindings } from '../authoring/semantic-loops.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { decodeGeneratedEnvelope, decodeGeneratedProposalDetailed } from './expansion-run.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { projectObservedRequirements } from './source-requirements.mjs';
import { compileExpansion } from './semantic-expander.mjs';
import { sourceSectionInventory, validateSourceDispositions } from './source-dispositions.mjs';
import { applySemanticRepair, canonicalizeSemanticRepair, CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA, INTERNAL_SEMANTIC_BLUEPRINT_SCHEMA, LEGACY_SEMANTIC_BLUEPRINT_CONTRACT, normalizeSemanticBlueprint, PREVIOUS_COMPACT_SEMANTIC_BLUEPRINT_CONTRACT, PREVIOUS_COMPACT_SEMANTIC_BLUEPRINT_SCHEMA, PREVIOUS_FANOUT_SEMANTIC_BLUEPRINT_CONTRACT, PREVIOUS_FANOUT_SEMANTIC_BLUEPRINT_SCHEMA, PREVIOUS_SEMANTIC_BLUEPRINT_CONTRACT, SEMANTIC_BLUEPRINT_CONTRACT, SEMANTIC_BLUEPRINT_SCHEMA, SEMANTIC_REPAIR_CONTRACT, SEMANTIC_REPAIR_SCHEMA } from '../authoring/blueprint-contract.mjs';
import { actionableSemanticError, lowerSemanticBlueprint } from '../authoring/workflow-forge.mjs';
import { validateData } from '../workflow-data-schema.mjs';
import { AUTHORING_PIPELINE, authoringDependencyAssessmentRequired } from '../authoring/authoring-workflows.mjs';

const countsBy=(values,key)=>Object.fromEntries([...new Set(values.map(item=>item?.[key] ?? 'none'))].sort().map(value=>[value,values.filter(item=>(item?.[key] ?? 'none')===value).length]));

// This trace is evidence of the deterministic compiler work actually performed
// between the two model boundaries. It intentionally records bounded summaries
// and hashes, not a second copy of the proposal.
export function authoringPipelineTrace({pack,resources,authoringPlan,proposal,compiled,repairs=[]}){
  const semantic=authoringPlan ?? proposal;
  const graphNodes=proposal.nodes ?? [],graphEdges=proposal.edges ?? [];
  const executableNodes=compiled.workflow.nodes.filter(node=>!['start','final','end'].includes(node.id));
  const validation=compiled.validation;
  const resultById={
    source_snapshot:{source_revision:pack.revision_hash,resource_count:Object.keys(resources).length},
    semantic_inventory:{contract:authoringPlan?.contract ?? 'legacy-proposal',activity_count:authoringPlan?.activities?.length ?? graphNodes.length,source_disposition_count:authoringPlan?.source_dispositions?.length ?? proposal.source_dispositions?.length ?? 0,control_group_counts:{sequence:authoringPlan?.sequences?.length ?? 0,parallel:authoringPlan?.parallels?.length ?? 0,choice:authoringPlan?.choices?.length ?? 0,approval:authoringPlan?.approvals?.length ?? 0,loop:authoringPlan?.loops?.length ?? 0},semantic_hash:digest(canonicalJSON(semantic))},
    graph_assembly:{node_count:graphNodes.length,edge_count:graphEdges.length,loop_count:proposal.loops?.length??0,graph_hash:digest(canonicalJSON({loops:proposal.loops??[],nodes:graphNodes.map(node=>node.id),edges:graphEdges.map(edge=>[edge.source,edge.target,edge.on ?? null,edge.label ?? null])}))},
    execution_binding:{access_counts:countsBy(executableNodes,'access'),executor_counts:countsBy(executableNodes.map(node=>node.executor ?? {}),'kind'),input_binding_count:executableNodes.reduce((total,node)=>total+Object.keys(node.input_bindings ?? {}).length,0),resource_binding_count:executableNodes.reduce((total,node)=>total+(node.resources?.length ?? 0),0),host_projection_count:repairs.length},
    deterministic_validation:{valid:validation.valid,launch_ready:validation.launch_ready,cycle_free:validation.valid,error_codes:validation.errors.map(item=>item.code),blocker_codes:validation.blockers.map(item=>item.code),topological_order:validation.order},
    semantic_review:{status:'pending'},
    human_publish:{status:'pending'},
  };
  const proposalHash=digest(canonicalJSON(proposal));
  const results=Object.fromEntries(['graph_assembly','execution_binding','deterministic_validation'].map(stage=>[stage,{stage,proposal_hash:proposalHash,result:structuredClone(resultById[stage])}]));
  return {contract:AUTHORING_PIPELINE.contract,proposal_hash:proposalHash,results,stages:AUTHORING_PIPELINE.stages.map(stage=>({...structuredClone(stage),status:['semantic_review','human_publish'].includes(stage.phase)?'pending':'succeeded',result:resultById[stage.phase]})),edges:structuredClone(AUTHORING_PIPELINE.edges),repair:structuredClone(AUTHORING_PIPELINE.repair)};
}

function missingContractFields(proposal) {
  const findings=[];
  if (!Object.hasOwn(proposal ?? {},'required_executables')) findings.push({field:'required_executables',reason:'Host executable projection is missing.'});
  for (const node of proposal?.nodes ?? []) if (['agent','tool','human_gate'].includes(node.type)) {
    for (const field of ['input_bindings','resource_refs','requirement_ids']) if (!Object.hasOwn(node,field)) findings.push({node_id:node.id,field,reason:'Current conversion nodes require an explicit host/model projection.'});
  }
  return findings;
}

export function deterministicProposalFindings(proposal,compiled,version,resources={}) {
  const mechanical=[],semantic=sourceRepairLoopIntentFindings(proposal,resources);
  if (version>=6) mechanical.push(...missingContractFields(proposal));
  if (version>=4) {
    semantic.push(...compiled.workflow.import_status.requirement_coverage.filter(item=>item.status==='unsupported'));
    for(const mapping of proposal.requirement_mappings ?? []) if(mapping.rationale?.startsWith('Host-projected to resource-consuming nodes because the planner supplied no semantic mapping')) semantic.push({requirement_id:mapping.requirement_id,status:'fallback_review',reason:'A deterministic source requirement has no planner-supplied semantic mapping.'});
  }
  if (version>=8) semantic.push(...validateSourceDispositions(proposal,resources));
  const nodeKeys=new Map((proposal.nodes??[]).map(node=>[node.id,node.semantic_key??node.id]));
  const requirements=new Map((proposal.source_requirements??[]).map(item=>[item.requirement_id,item]));
  const actionable=semantic.map((finding,index)=>{
    if(Array.isArray(finding?.affected_semantic_fields)&&Array.isArray(finding?.semantic_keys)&&finding.semantic_keys.length)return finding;
    const requirement=requirements.get(finding?.requirement_id),mapping=(proposal.requirement_mappings??[]).find(item=>item.requirement_id===finding?.requirement_id);
    const semanticKeys=[...(finding?.node_ids??[]),...(mapping?.node_ids??[])].map(id=>nodeKeys.get(id)).filter(Boolean);
    if(finding?.requirement_id)semanticKeys.push(finding.requirement_id);
    if(finding?.section_id)semanticKeys.push(finding.section_id,...(finding.activity_keys??[]));
    const sourceSpans=structuredClone(requirement?.source_spans ?? finding?.source_spans ?? []);
    const fields=finding?.section_id?['source_dispositions','activities.source_sections']:['requirement_assignments'];
    const message=finding?.reason ?? `Deterministic semantic check failed for ${finding?.requirement_id ?? finding?.section_id ?? 'the proposal'}.`;
    const stableKeys=[...new Set(semanticKeys)].sort();
    return {...structuredClone(finding),target_id:`planner_deterministic_${String(index+1).padStart(3,'0')}`,owner:'planner',check_ids:[finding?.section_id?'source_disposition':'requirement_coverage'],semantic_keys:stableKeys,affected_semantic_fields:fields,source_spans:sourceSpans,evidence:[message],minimal_change:`Update only ${fields.join(', ')}${stableKeys.length?` for ${stableKeys.join(', ')}`:''}; preserve unrelated semantic keys.`};
  });
  return {mechanical,semantic:actionable};
}

// One deterministic gate shared by pre-review, persisted-artifact recheck and
// final apply.  No caller may maintain a weaker copy of the conversion rules.
export function validateGenerationProposal(output,{pack,resources,provenance,context,previousPlan=null,repairFeedback=null}) {
  const projectedPipeline=output?.host_pipeline??null;
  const envelope=projectedPipeline?{proposal:output.proposal}:output;
  const payload=decodeGeneratedEnvelope(envelope);
  const requireDependencyAssessment=authoringDependencyAssessmentRequired(provenance.authoring_contract);
  const semanticContracts=[SEMANTIC_BLUEPRINT_CONTRACT,PREVIOUS_FANOUT_SEMANTIC_BLUEPRINT_CONTRACT,PREVIOUS_COMPACT_SEMANTIC_BLUEPRINT_CONTRACT,PREVIOUS_SEMANTIC_BLUEPRINT_CONTRACT,LEGACY_SEMANTIC_BLUEPRINT_CONTRACT,SEMANTIC_REPAIR_CONTRACT];
  const decodedResult=semanticContracts.includes(payload?.contract)
    ? (()=>{
      let authoringPlan=null,semantic=payload,repairs=[];
      if(payload.contract===SEMANTIC_REPAIR_CONTRACT){
        const repairPatch=canonicalizeSemanticRepair(payload);
        validateData(repairPatch,SEMANTIC_REPAIR_SCHEMA);
        requireValue(previousPlan?.contract===SEMANTIC_BLUEPRINT_CONTRACT,'AUTHORING_REPAIR_STATE','Semantic repair has no pinned compact blueprint to update');
        const corrections=[];
        authoringPlan=applySemanticRepair(previousPlan,repairPatch,{targets:repairFeedback?.findings,corrections});validateData(authoringPlan,requireDependencyAssessment?CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA:SEMANTIC_BLUEPRINT_SCHEMA);semantic=authoringPlan;
        if(payload.purpose)repairs.push({kind:'host_ignored_repair_purpose'});
        for(const correction of corrections)repairs.push({kind:'host_ignored_out_of_scope_repair_field',...correction});
        repairs.push({kind:'host_semantic_delta_applied'});
      } else if(payload.contract===SEMANTIC_BLUEPRINT_CONTRACT){
        if(requireDependencyAssessment)requireValue(Array.isArray(payload.runtime_dependencies),'GENERATION_DEPENDENCY_ASSESSMENT','Current authoring plans must explicitly decide runtime_dependencies, including []');
        validateData(payload,requireDependencyAssessment?CURRENT_AUTHORING_SEMANTIC_BLUEPRINT_SCHEMA:SEMANTIC_BLUEPRINT_SCHEMA);authoringPlan=structuredClone(payload);
      }
      else if(payload.contract===PREVIOUS_COMPACT_SEMANTIC_BLUEPRINT_CONTRACT){validateData(payload,PREVIOUS_COMPACT_SEMANTIC_BLUEPRINT_SCHEMA);}
      else if(payload.contract===PREVIOUS_FANOUT_SEMANTIC_BLUEPRINT_CONTRACT){validateData(payload,PREVIOUS_FANOUT_SEMANTIC_BLUEPRINT_SCHEMA);}
      if(requireDependencyAssessment&&payload.contract!==SEMANTIC_REPAIR_CONTRACT&&payload.contract!==SEMANTIC_BLUEPRINT_CONTRACT)requireValue(false,'GENERATION_DEPENDENCY_ASSESSMENT','Current authoring plans must use the compact blueprint with an explicit runtime_dependencies decision');
      let normalized,proposal;
      try{
        normalized=normalizeSemanticBlueprint(semantic);validateData(normalized,INTERNAL_SEMANTIC_BLUEPRINT_SCHEMA);
        // Lower from the compact source, not the normalized internal form:
        // source-inventory preflight must see the planner's dispositions and
        // report their semantic defects before graph compilation.
        proposal=lowerSemanticBlueprint(pack,resources,semantic,{...context,routing_rules:provenance.routing_rules,routing_catalog:provenance.routing_catalog});
      }catch(error){throw actionableSemanticError(error,semantic);}
      repairs.push({kind:'host_semantic_blueprint_lowered'});
      if(payload.contract===LEGACY_SEMANTIC_BLUEPRINT_CONTRACT)repairs.push({kind:'host_semantic_blueprint_v2_upgraded'});
      return {proposal,repairs,authoringPlan};
    })()
    : decodeGeneratedProposalDetailed(envelope,provenance.source_revision,{requirePlanningAnalysis:provenance.routing_rules?.selection_mode === 'automatic',requireSourceDispositions:(provenance.review_contract_version ?? 1)>=8,requireRuntimeDependencies:requireDependencyAssessment,sourceInventory:sourceSectionInventory(resources)});
  const decoded=decodedResult.proposal;
  const proposal=projectObservedRequirements(decoded,resources);
  const repairs=[...decodedResult.repairs];
  if (canonicalJSON(decoded)!==canonicalJSON(proposal)) repairs.push({kind:'host_contract_projection',fields:['source_requirements','requirement_mappings','required_executables','input_bindings','resource_refs','requirement_ids']});
  const compiled=compileExpansion(pack,resources,proposal,{...context,routing_rules:provenance.routing_rules,routing_catalog:provenance.routing_catalog});
  if (canonicalJSON(proposal)!==canonicalJSON(compiled.canonical_proposal)) repairs.push({kind:'host_semantic_status_projection',fields:['requirement_mappings','tool_output_schemas']});
  const canonicalProposal=compiled.canonical_proposal;
  const findings=deterministicProposalFindings(canonicalProposal,compiled,provenance.review_contract_version ?? 1,resources);
  requireValue(findings.mechanical.length===0,'GENERATION_HOST_PROJECTION','The Host projection is incomplete and cannot be repaired by another model attempt',{findings:findings.mechanical,validation:compiled.validation});
  requireValue(findings.semantic.length===0,'GENERATION_DETERMINISTIC_AUDIT','The proposal does not satisfy the pinned deterministic conversion contract',{findings:findings.semantic,validation:compiled.validation});
  const authoringPlan=decodedResult.authoringPlan ?? null;
  const pipelineTrace=authoringPipelineTrace({pack,resources,authoringPlan,proposal:canonicalProposal,compiled,repairs});
  if(projectedPipeline){
    const stageIds=['graph_assembly','execution_binding','deterministic_validation'];
    requireValue(projectedPipeline.contract===pipelineTrace.contract && projectedPipeline.proposal_hash===pipelineTrace.proposal_hash && canonicalJSON(Object.keys(projectedPipeline.results??{}).sort())===canonicalJSON(stageIds.slice().sort()) && stageIds.every(stage=>projectedPipeline.results[stage]?.stage===stage && projectedPipeline.results[stage]?.proposal_hash===pipelineTrace.proposal_hash),'GENERATION_PROJECTION_CONFLICT','Persisted Host compiler stage evidence does not match the canonical proposal identity');
  }
  return {decoded,proposal:canonicalProposal,compiled,repairs,authoring_plan:authoringPlan,pipeline_trace:pipelineTrace};
}
