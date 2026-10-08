import { posix } from 'node:path';
import { sourceSectionInventory } from './source-dispositions.mjs';
import { exclusiveConditionFanIn, nearestDataProducerIds, selectedUpstreamBinding } from './fan-in-topology.mjs';
import { authoringSourcePath, SKILL_SOURCE } from './authoring-source.mjs';
import { dependencyExecutables, sourceContractIndex } from './source-contracts.mjs';
import { normalizeExecutableRequirements } from '../runtime-requirements.mjs';
import { isOperationalMemoryArtifactPath } from '../artifact-policy.mjs';

const commandPattern = /(?:^|[\s`"'(])((?:\.\/)?(?:scripts|tools|bin)\/[A-Za-z0-9._/-]+\.(?:py|mjs|cjs|js|sh|ps1|cmd|bat))(?=$|[\s`"',);])/gmi;
const approvalPattern = /(?:\b(?:must|required|before|obtain|explicit|ask(?:\s+the\s+user)?(?:\s+for)?)\b.{0,100}\b(?:approval|approve|confirmation|confirm)\b|\b(?:approval|confirmation)\b.{0,100}\b(?:must|required|before)\b|(?:必须|需要|务必|在.{0,20}之前).{0,40}(?:批准|审批|确认))/i;
const inputPattern = /(?:\b(?:ask|prompt|collect|get|receive)\b.{0,80}\b(?:user|human)\b.{0,80}\b(?:input|answer|choice|feedback|brief|selection)\b|\b(?:user|human)\b.{0,80}\b(?:input|answer|choice|feedback|brief|selection)\b|(?:询问|收集|取得|接收).{0,30}(?:用户|人工).{0,30}(?:输入|回答|选择|反馈|简报))/i;
const artifactPathPattern = /(?:[`'"])?((?:(?:[A-Za-z]:[\\/]|\/)?(?:[A-Za-z0-9._-]+[\\/])*)[A-Za-z0-9_-]+\.(?:json|csv|tsv|txt|md|html|pdf|png|jpg|jpeg|mp4|wav|zip))(?:[`'"])?/gi;
const artifactProductionPattern = /\b(?:write|save|create|produce|emit|return|output|update)\b/i;
const conditionalArtifactPattern = /\b(?:optional(?:ly)?|if|when|unless|only\s+(?:if|when))\b/i;
const negativeArtifactPattern = /\b(?:do\s+not|don't|never|must\s+not|forbid(?:den)?)\b/i;
const artifactClauses = text => text.split(/;\s*|(?<=[.!?])\s+(?=[A-Z])/);
const dynamicOutputRootPattern = /\b(?:all|every)\b.{0,100}\b(?:outputs?|artifacts?|files?)\b.{0,80}\b(?:in|into|under)\s+[`'"]?<[^>]+>[\\/]/i;
const interfacePattern = /\b(?:(?:exact\s+)?(?:keys?|columns?|schema|signature)|return\s+type|output\s+format)\b/i;
const canonicalizationPattern = /(?:YYYY-MM-DDTHH:MM:SSZ|\b(?:round(?:ed)?|truncate(?:d)?|format(?:ted)?)\b.{0,80}\b(?:to|as)\s+(?:exactly\s+)?(?:\d+\s+decimal\s+places?|[A-Za-z0-9_.:+-]+))/i;
const methodPattern = /(?:\bEPSG:\d+\b|\b\d+\s+decimal\s+places?\b|\b(?:must|Must|shall|Shall|required to|Required to)\s+(?:the\s+)?(?:[A-Za-z][\w.-]*(?:\([^)]{0,80}\))?|[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})\b|\buse\s+(?:[A-Za-z][\w.-]*\([^)]{0,80}\)|[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})\b|\b(?:do not|Do not|never|Never)\s+use\b)/;
const methodPreferencePattern = /(?:\b(?:prefer|recommended|trust)\b.{0,160}\b(?:method|test|slope|regression|factor|PCA|analysis|environmental data)\b|\b(?:method|algorithm|workflow)\s*:\s*[^|]{2,200})/i;
// Normative Markdown frequently carries the only exact algorithm contract in a
// code block.  Keep explicit calls, derived-variable formulas, contribution
// formulas and rounding/scaling operations in the deterministic floor instead
// of relying on a planning model to notice them later.
const methodCodePattern = /(?:\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\s*\(|\b(?:FactorAnalyzer|StandardScaler|LinearRegression|RandomForestRegressor|PCA)\s*\(|\b(?:round|floor|ceil)\s*\(|\b(?:contribution\w*|contrib_\w+)\s*=|\[["'][^"']+["']\]\s*=.*(?:\+|-|\*|\/))/;
const dependencyContext = /(?:\b(?:require(?:s|d)?|dependency|install|need(?:s)?|(?:use|with|run)\s+(?:python(?:3)?|node|ffmpeg|ffprobe|git|java|Rscript|codegraph))\b|^\s*(?:(?:\d+[.)]|[-*+])\s*)?`?(?:python(?:3)?|node|ffmpeg|ffprobe|git|java|Rscript|codegraph)\b)/i;
const referencePathPattern = /(?:`|['"])?((?:\.\.\/|\.\/)?(?:[A-Za-z0-9._-]+\/)*[A-Za-z0-9._-]+\.(?:md|json|ya?ml|txt))(?:`|['"])?/gi;
const referenceContext = /\b(?:read|follow|apply|consult|load|use|required)\b|(?:读取|遵循|应用|查阅|加载|使用|必须)/i;
const readinessContext = /\b(?:on\s+(?:the\s+)?PATH|available|installed)\b/i;

const span = (resource, line) => ({ resource, start_line: line, end_line: line });
const safe = value => value.replace(/[^A-Za-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 48) || 'resource';
// Preserve v3 IDs for the primary Skill file so existing imported proposals
// remain addressable; auxiliary resources receive a stable resource component.
const id = (kind, resource, line, suffix = '') => resource === SKILL_SOURCE
  ? `observed_${kind}_${line}${suffix ? '_' + suffix : ''}`
  : `observed_${kind}_${safe(resource)}_${line}${suffix ? '_' + suffix : ''}`;
// Only the Skill entrypoint is unconditional conversion authority.  Imported
// references can be examples, optional method packs, or nested Skills whose
// rules apply only after a source-defined trigger.  Promoting every pinned text
// file into the deterministic floor makes those conditional resources global
// requirements and forces the planner to map documents it was explicitly told
// to read only on demand.  The planner may still declare requirements from any
// pinned reference it actually uses; review validates those cited spans and
// resource bindings.  The host-observed floor is deliberately limited to the
// entrypoint whose instructions are always active.
const textResources = resources => {const path=authoringSourcePath(resources);return [[path,resources[path]]];};

function details(kind, line, match = null) {
  if (kind === 'artifact_path') return { artifact_path: match[1] };
  if (kind === 'artifact_schema') {
    const quoted = [...line.matchAll(/[`'"]([A-Za-z_][A-Za-z0-9_-]{0,127})[`'"]/g)].map(item=>item[1]);
    const tail = line.match(/\b(?:keys?|columns?|fields?)\b\s*(?::|are|include|named)?\s*([^.;]+)/i)?.[1] ?? '';
    const terms = quoted.length ? quoted : [...tail.matchAll(/\b([A-Za-z_][A-Za-z0-9_-]{0,127})\b/g)].map(item=>item[1]).filter(term=>!/^(and|or|the|a|an)$/i.test(term));
    return { interface_terms: [...new Set(terms)].slice(0, 32) };
  }
  if (kind === 'canonicalization') return { rule_text: line.trim().slice(0, 1000) };
  if (kind === 'method_rule') return { rule_text: line.trim().slice(0, 1000) };
  return {};
}

/**
 * Conservative deterministic anchors from the always-active Skill entrypoint.
 * They are a floor, not a natural-language compiler: requirements from an
 * optional or nested reference enter the contract only when the proposal cites
 * that pinned resource and preserves its source-defined trigger.
 */
export function observedSourceRequirements(resources) {
  const requirements = [];
  const contractsByResource=new Map();
  for(const contract of sourceContractIndex(resources).contracts){const entries=contractsByResource.get(contract.resource)??[];entries.push(contract.contract_id);contractsByResource.set(contract.resource,entries);}
  for (const [resource, bytes] of textResources(resources)) {
    const lines = bytes.toString('utf8').split('\n');
    const requiredLines=new Set(sourceSectionInventory(resources).filter(section=>section.authority==='required').flatMap(section=>Array.from({length:section.source_span.end_line-section.source_span.start_line+1},(_,offset)=>section.source_span.start_line+offset)));
    const dynamicOutputRoot=lines.some((text,index)=>requiredLines.has(index+1)&&dynamicOutputRootPattern.test(text));
    let artifactListActive=false,conditionalScope=false;
    for (const [index, text] of lines.entries()) {
      const line = index + 1; const sourceSpans = [span(resource, line)];
      if(!requiredLines.has(line))continue;
      const trimmed=text.trim();
      if(!trimmed){artifactListActive=false;conditionalScope=false;continue;}
      const conditionalHeader=/\b(?:if|when|unless|only\s+(?:if|when))\b.*:\s*$/i.test(text);
      if(conditionalScope && !/^\s+|^\s*[-*+]/.test(text) && !conditionalHeader)conditionalScope=false;
      if (approvalPattern.test(text)) requirements.push({ requirement_id: id('approval', resource, line), requirement_kind: 'approval', source_spans: sourceSpans, trigger: 'source_observed', required_result: 'A human approval gate must complete before the dependent operation.', resource_refs: [resource], details: {} });
      if (inputPattern.test(text)) requirements.push({ requirement_id: id('user_input', resource, line), requirement_kind: 'user_input', source_spans: sourceSpans, trigger: 'source_observed', required_result: 'Required user input must be represented explicitly or declared unsupported.', resource_refs: [resource], details: {} });
      let ordinal = 0;
      for (const match of text.matchAll(commandPattern)) {
        if(/\b(?:never|do\s+not|don't|must\s+not|forbid(?:den)?)\b/i.test(text.slice(0,match.index)))continue;
        ordinal++; const target = match[1].replace(/^\.\//, ''); const targetResource = posix.normalize('source/' + target);
        requirements.push({ requirement_id: id('script', resource, line, String(ordinal)), requirement_kind: 'script_operation', source_spans: sourceSpans, trigger: 'source_observed', required_result: `Execute the pinned script resource ${targetResource} with declared inputs and verified outputs.`, resource_refs: [targetResource], details: {source_contract_ids:[...(contractsByResource.get(targetResource)??[])]} });
      }
      let artifactOrdinal = 0;
      for (const clause of artifactClauses(text)) {
        // Only an unconditioned production clause establishes an unconditional
        // path gate. A later `when` clause on the same line must not promote
        // its file, or an earlier file, by borrowing a verb across clauses.
        if (conditionalScope || conditionalArtifactPattern.test(clause) || negativeArtifactPattern.test(clause) || (!artifactListActive && !artifactProductionPattern.test(clause))) continue;
        for (const artifact of clause.matchAll(artifactPathPattern)) {
          if (isOperationalMemoryArtifactPath(artifact[1], { sourceText: text })) continue;
          const runtimeScoped=dynamicOutputRoot&&!/[\\/]/.test(artifact[1]);
          artifactOrdinal++; requirements.push({ requirement_id: id('artifact_path', resource, line, String(artifactOrdinal)), requirement_kind: 'artifact_path', source_spans: sourceSpans, trigger: runtimeScoped?'runtime_resolved_artifact':'produce_declared_artifact', required_result: runtimeScoped?`Produce ${artifact[1]} under the source-defined runtime output root.`:`Produce the exact artifact path ${artifact[1]}.`, resource_refs: [resource], details: details('artifact_path', clause, artifact) });
        }
      }
      artifactListActive=/\b(?:write|save|create|produce|emit|return|output|update)\b[^\n]*:\s*$/i.test(text) || (artifactListActive && /^\s*[-*+]/.test(text));
      if (interfacePattern.test(text)) requirements.push({ requirement_id: id('artifact_schema', resource, line), requirement_kind: 'artifact_schema', source_spans: sourceSpans, trigger: 'produce_or_validate_interface', required_result: `Preserve this exact interface statement: ${text.trim().slice(0, 1000)}`, resource_refs: [resource], details: details('artifact_schema', text) });
      if (canonicalizationPattern.test(text)) requirements.push({ requirement_id: id('canonicalization', resource, line), requirement_kind: 'canonicalization', source_spans: sourceSpans, trigger: 'before_final_validation', required_result: `Apply this deterministic representation rule without changing semantic content: ${text.trim().slice(0, 1000)}`, resource_refs: [resource], details: details('canonicalization', text) });
      if (methodPattern.test(text) || methodPreferencePattern.test(text) || methodCodePattern.test(text)) requirements.push({ requirement_id: id('method_rule', resource, line), requirement_kind: 'method_rule', source_spans: sourceSpans, trigger: 'perform_prescribed_method', required_result: `Preserve this exact method statement: ${text.trim().slice(0, 1000)}`, resource_refs: [resource], details: details('method_rule', text) });
      const negativeCommand=/\b(?:never|do\s+not|don't|must\s+not|forbid(?:den)?)\b/i.test(text);
      if (!negativeCommand && (dependencyContext.test(text) || dependencyExecutables(text).length)) {
        let dependencyOrdinal = 0;
        for (const name of dependencyExecutables(text)) {
          dependencyOrdinal++;
          // Dependency prose is conditional whenever it contains an explicit
          // conditional cue.  Do not attempt to enumerate the subject
          // (rendering/audio/video/etc.); missing one would incorrectly
          // promote an optional executable into the global preparation gate.
          const conditional = conditionalScope || /\b(?:optional(?:ly)?|if|when|unless|only\s+(?:if|when))\b/i.test(text);
          requirements.push({ requirement_id: id('dependency', resource, line, String(dependencyOrdinal)), requirement_kind: 'dependency', source_spans: sourceSpans, trigger: conditional ? `conditional: ${text.trim().slice(0, 500)}` : 'unconditional_source_dependency', required_result: `${conditional ? 'Conditionally check' : 'Prepare'} executable ${name}.`, resource_refs: [resource], details: { executable: name, phase: conditional ? 'conditional' : 'unconditional' } });
        }
      }
      if(conditionalHeader)conditionalScope=true;
      if (referenceContext.test(text)) {
        let referenceOrdinal=0;
        for (const match of text.matchAll(referencePathPattern)) {
          const relative=posix.normalize(match[1].replace(/^\.\//,'').replace(/^\.\.\//,''));
          const target=relative.startsWith('source/')?relative:`source/${relative}`;
          if (target===resource || !Object.hasOwn(resources,target)) continue;
          referenceOrdinal++;
          const conditional=/\b(?:optional(?:ly)?|if|when|unless|only\s+(?:if|when))\b/i.test(text);
          requirements.push({requirement_id:id('reference',resource,line,String(referenceOrdinal)),requirement_kind:'knowledge',source_spans:sourceSpans,trigger:conditional?`conditional: ${text.trim().slice(0,500)}`:'source_required_reference',required_result:`Read and apply the pinned reference ${target} at its source-defined phase.`,resource_refs:[target],details:{}});
        }
      }
    }
  }
  return requirements;
}

// A current authoring decision may refine a coarse name-only observation from
// the exact same source line. Reconcile that fact by source identity, never by
// executable name alone: another line may independently require the program.
const approvalCue=/(?:\b(?:approval|approve|confirmation|confirm|permission)\b|批准|审批|确认)/gi;
const inputCue=/(?:\b(?:input|answer|choice|feedback)\b|输入|回答|选择|反馈)/gi;
const exactDependencyName=name=>new RegExp(`(?<![A-Za-z0-9_.+-])${name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?![A-Za-z0-9_+-]|\\.[A-Za-z0-9_+-])`,'i');
const dependencyObjectEnd=/^\s*(?:(?:version\s+)?(?:v\d+(?:\.\d+){0,2}|(?:>=|<=|==|>|<)?\s*\d+(?:\.\d+){0,2}))?\s*(?:(?:if\s+(?:it\s+is\s+)?(?:missing|unavailable|not\s+found))|(?:before\s+(?:running|using)\s+it))?\s*[.!?。]?\s*$/i;
// An approval is Host preparation only when the approved action itself is
// installing/downloading this executable. A nearby mention of "missing" or
// "locate" says nothing about the approval's object. A coordinated second
// action makes the single observed approval ambiguous, so retain it for the
// semantic gate instead of silently assigning it to Host setup.
function hostPreparationClause(clause,kind,name){
  const dependency=exactDependencyName(name);
  if(kind==='approval'){
    const action=clause.match(/\b(?:approval|permission|confirmation)\s+(?:to|for)\s+(?:download\s+and\s+install|install|download|installing|downloading)\s+(?:the\s+)?/i);
    if(!action)return false;
    const remainder=clause.slice(action.index+action[0].length);
    const mentioned=remainder.match(dependency);
    if(!mentioned||mentioned.index!==0)return false;
    const tail=remainder.slice(mentioned[0].length);
    return dependencyObjectEnd.test(tail);
  }
  // A location question must name the executable's environment/path as the
  // requested input, not merely mention that executable elsewhere in a task.
  const input=[...clause.matchAll(inputCue)][0];
  if(!input)return false;
  const request=clause.slice(input.index+input[0].length).trim();
  const location='(?:path|location|installation|executable|binary|environment)';
  const locationRequest=request.match(new RegExp(`^(?:(?:for|to|about|on)\\s+)?(?:(?:locate|find|provide|specify|select|choose)\\s+)?(?:the\\s+)?(?:${location}\\b\\s+(?:of|for|to)\\s+${dependency.source}|${dependency.source}\\s+${location}\\b)`,'i'));
  return !!locationRequest&&/^\s*[.!?。]?\s*$/.test(request.slice(locationRequest[0].length));
}
export function hostPreparationObservationEvidence(observation,decision,resources={}){
  if(!['approval','user_input'].includes(observation?.requirement_kind)||decision?.requirement_kind!=='dependency'||decision.details?.phase!=='unconditional')return false;
  const name=decision.details?.executable;
  if(typeof name!=='string'||!name.trim())return false;
  const quote=decision.details?.source_quote,anchor=observation.source_spans?.[0];
  if(typeof quote!=='string'||!quote.trim()||quote.includes('\n')||!anchor||anchor.start_line!==anchor.end_line||!Object.hasOwn(resources,anchor.resource))return false;
  const line=Buffer.from(resources[anchor.resource]).toString('utf8').split('\n')[anchor.start_line-1]??'';
  if(!line.includes(quote)||!(decision.source_spans??[]).some(span=>span.resource===anchor.resource&&span.start_line<=anchor.start_line&&span.end_line>=anchor.end_line))return false;
  const cue=observation.requirement_kind==='approval'?approvalCue:inputCue;
  const count=text=>[...text.matchAll(cue)].length;
  if(count(line)!==1||count(quote)!==1)return false;
  // Observations cover source lines. Inspect the original approval-bearing
  // clause, so a shortened quote cannot hide a second approved task action.
  return line.split(/;\s*|(?<=[.!?。])\s+/).some(clause=>count(clause)===1&&hostPreparationClause(clause,observation.requirement_kind,name));
}
const authoringDependencyQuoteAnchored=(decision,resources)=>{
  const quote=decision.details?.source_quote;
  return typeof quote==='string'&&quote.trim()&&(decision.source_spans??[]).some(span=>{
    if(!Object.hasOwn(resources,span.resource))return false;
    const lines=Buffer.from(resources[span.resource]).toString('utf8').split('\n');
    return lines.slice(span.start_line-1,span.end_line).join('\n').includes(quote);
  });
};
export function reconciledObservedRequirements(observed,proposed=[],resources={}){
  const explicit=(proposed??[]).filter(item=>item?.requirement_kind==='dependency'&&String(item.requirement_id).startsWith('authoring_dependency_')&&authoringDependencyQuoteAnchored(item,resources));
  return observed.filter(item=>{
    if(['approval','user_input'].includes(item.requirement_kind))return !explicit.some(decision=>(decision.details?.host_preparation_observation_ids??[]).includes(item.requirement_id)&&hostPreparationObservationEvidence(item,decision,resources));
    return item.requirement_kind!=='dependency'||!explicit.some(decision=>
      decision.details?.executable===item.details?.executable&&(decision.source_spans??[]).some(source=>(item.source_spans??[]).some(anchor=>source.resource===anchor.resource&&source.start_line<=anchor.end_line&&source.end_line>=anchor.start_line)));
  });
}

// A planner may retain a section that the coarse inventory conservatively
// marked as a reference candidate. Its explicit executable-readiness lines
// then become Host facts, but only at the planner-selected source phase. This
// does not promote the rest of that section's prose into unconditional rules.
function selectedReadinessRequirements(proposal,resources) {
  const source=authoringSourcePath(resources),lines=resources[source].toString('utf8').split('\n');
  const inventory=new Map(sourceSectionInventory(resources).map(section=>[section.section_id,section]));
  const selected=[];
  for(const disposition of proposal.source_dispositions??[]) {
    const section=inventory.get(disposition.section_id);
    if(!section||section.authority==='required'||!['workflow','conditional'].includes(disposition.disposition))continue;
    for(let line=section.source_span.start_line;line<=section.source_span.end_line;line++) {
      const text=lines[line-1]??'';
      if(!readinessContext.test(text)||negativeArtifactPattern.test(text))continue;
      const conditional=disposition.disposition==='conditional'||/\b(?:optional(?:ly)?|if|when|unless|only|first[- ]use)\b/i.test(text);
      let ordinal=0;
      for(const name of dependencyExecutables(text)) {
        ordinal++;
        selected.push({requirement:{requirement_id:id('dependency',source,line,String(ordinal)),requirement_kind:'dependency',source_spans:[span(source,line)],trigger:conditional?`conditional: ${text.trim().slice(0,500)}`:'unconditional_source_dependency',required_result:`${conditional?'Conditionally check':'Prepare'} executable ${name}.`,resource_refs:[source],details:{executable:name,phase:conditional?'conditional':'unconditional'}},node_ids:[...(disposition.node_ids??[])]});
      }
    }
  }
  return selected;
}

/**
 * Fill deterministic format fields that a model should not have to echo.
 * Observed requirements have stable Host IDs in the planning packet. The Host
 * never guesses equivalence from line overlap or vocabulary; a missing mapping
 * remains a real semantic finding for one bounded planner repair.
 */
export function projectObservedRequirements(proposal, resources) {
  const contractProjection = Array.isArray(proposal?.source_requirements) && Array.isArray(proposal?.requirement_mappings);
  const result = structuredClone(proposal);
  result.source_requirements = Array.isArray(result.source_requirements) ? result.source_requirements : [];
  result.requirement_mappings = Array.isArray(result.requirement_mappings) ? result.requirement_mappings : [];
  const selectedReadiness=selectedReadinessRequirements(result,resources);
  const observedBase = [...observedSourceRequirements(resources),...selectedReadiness.map(item=>item.requirement)];
  const observed = reconciledObservedRequirements(observedBase,result.source_requirements,resources);
  const observedIds = new Set(observedBase.map(item => item.requirement_id));
  const retainedIds=new Set(observed.map(item=>item.requirement_id));
  result.requirement_mappings=result.requirement_mappings.filter(item=>!observedIds.has(item.requirement_id)||retainedIds.has(item.requirement_id));
  // Observed entries are host facts, not model-authored proposal fields. Strip
  // any echoed copies and inject the canonical host values below. The model may
  // refer to these stable IDs from mappings and nodes, but cannot mutate their
  // kind, evidence, dependency phase, schema terms, or other typed details.
  result.source_requirements = result.source_requirements.filter(item => !observedIds.has(item?.requirement_id));
  const nodes = new Map((result.nodes ?? []).map(node => [node.id, node]));
  for (const node of result.nodes ?? []) if (['agent','tool','human_gate'].includes(node.type)) {
    // Only legacy proposals without a projection inherit the coarse inputs.
    // An explicit map, including {}, is the activity's complete input contract.
    if (contractProjection && node.type==='agent' && !Object.hasOwn(node,'input_bindings')) {
      const producers=nearestDataProducerIds(result.nodes,result.edges,node.id);
      const bindings={task:'/inputs/task'};
      if(exclusiveConditionFanIn(result.nodes,result.edges,node.id))bindings.upstream_selected=selectedUpstreamBinding(result.nodes,result.edges,node.id);
      else for (const source of producers) bindings[`upstream_${source}`]=`/nodes/${source}/output`;
      node.input_bindings=bindings;
    }
    if (!Object.hasOwn(node,'input_bindings') && node.type==='human_gate') node.input_bindings={};
    if (contractProjection || node.type==='human_gate') node.resource_refs=[...new Set([...(node.source_span?.resource?[node.source_span.resource]:[]),...(node.resource_refs ?? [])])];
    if (contractProjection) {node.requirement_ids=[];node.required_artifacts=[];}
    else if (node.type==='human_gate' && !Object.hasOwn(node,'requirement_ids')) node.requirement_ids=[];
  }
  for (const hostRequirement of observed) result.source_requirements.push(structuredClone(hostRequirement));
  const mappedReadiness=new Set(result.requirement_mappings.map(mapping=>mapping.requirement_id));
  for(const {requirement,node_ids} of selectedReadiness) if(retainedIds.has(requirement.requirement_id)&&!mappedReadiness.has(requirement.requirement_id)) {
    const responsible=[...new Set(node_ids)].filter(id=>['agent','tool'].includes(nodes.get(id)?.type));
    if(!responsible.length)continue;
    result.requirement_mappings.push({requirement_id:requirement.requirement_id,node_ids:responsible,binding_names:[],runtime_guards:[],resource_refs:[...requirement.resource_refs],status:'agent_assisted',rationale:'Host projected an explicit executable-readiness line from a planner-retained source section onto its declared responsible activities.'});
    mappedReadiness.add(requirement.requirement_id);
  }
  // A literal, unconditional path can be assigned mechanically when exactly
  // one write-capable activity cites the source line and explicitly names the
  // same production action and path. Ambiguous or merely mentioned paths stay
  // unassigned for semantic review; the Host never guesses a producer.
  const mappedIds=new Set(result.requirement_mappings.map(mapping=>mapping.requirement_id));
  for (const requirement of observed) if (requirement.requirement_kind==='artifact_path' && !mappedIds.has(requirement.requirement_id)) {
    const path=requirement.details.artifact_path;
    const candidates=(result.nodes??[]).filter(node=>node.type==='agent'&&node.operation_mode==='write'
      &&(node.source_spans??(node.source_span?[node.source_span]:[])).some(candidate=>(requirement.source_spans??[]).some(source=>candidate.resource===source.resource&&candidate.start_line<=source.start_line&&candidate.end_line>=source.end_line))
      &&artifactClauses(node.prompt_template??'').some(clause=>artifactProductionPattern.test(clause)&&!conditionalArtifactPattern.test(clause)&&!negativeArtifactPattern.test(clause)
        &&[...clause.matchAll(artifactPathPattern)].some(match=>match[1]===path)));
    if(candidates.length!==1)continue;
    result.requirement_mappings.push({requirement_id:requirement.requirement_id,node_ids:[candidates[0].id],binding_names:[],runtime_guards:[],resource_refs:[...requirement.resource_refs],status:'agent_assisted',rationale:'Host matched one write activity to the same unconditional source line, explicit production action, and literal artifact path.'});
    mappedIds.add(requirement.requirement_id);
  }
  // A human gate already encodes the approval boundary. Generated mappings
  // often name only that gate even though the compiler contract also needs the
  // immediately authorized operation. Derive this mechanical relationship
  // from the graph instead of asking the model to duplicate topology in two
  // arrays. The host never invents a route: only the gate's explicit success
  // successor is projected, and final/end are not treated as operations.
  const outgoing = new Map();
  for (const edge of result.edges ?? []) if ((edge.on ?? 'success') === 'success') {
    const targets = outgoing.get(edge.source) ?? []; targets.push(edge.target); outgoing.set(edge.source, targets);
  }
  for (const mapping of result.requirement_mappings) {
    if (mapping.status === 'unsupported') continue;
    const requirement = result.source_requirements.find(item => item.requirement_id === mapping.requirement_id);
    if (requirement?.requirement_kind !== 'approval') continue;
    const gateIds = (mapping.node_ids ?? []).filter(id => nodes.get(id)?.type === 'human_gate');
    const hasDependent = (mapping.node_ids ?? []).some(id => nodes.has(id) && nodes.get(id).type !== 'human_gate');
    if (!gateIds.length || hasDependent) continue;
    const dependents = [...new Set(gateIds.flatMap(id => outgoing.get(id) ?? []))]
      .filter(id => nodes.has(id) && !['human_gate','final','end'].includes(nodes.get(id).type));
    if (!dependents.length) continue;
    mapping.node_ids = [...new Set([...(mapping.node_ids ?? []), ...dependents])];
    for (const id of dependents) {
      const node = nodes.get(id);
      node.requirement_ids = [...new Set([...(node.requirement_ids ?? []), mapping.requirement_id])];
    }
  }
  // Mapping binding names may identify either a value produced by a mapped
  // node or a semantic input consumed downstream. For each mapped consumer,
  // derive the latter only when exactly one reachable predecessor exposes that
  // top-level output field. Ambiguous or absent producers remain unbound and
  // fail the compiler check below instead of being guessed by a model.
  const predecessors = new Map((result.nodes ?? []).map(node=>[node.id,[]]));
  for (const edge of result.edges ?? []) if (edge.on!=='failure' && predecessors.has(edge.target) && nodes.has(edge.source)) predecessors.get(edge.target).push(edge.source);
  const ancestors = id => { const seen=new Set(), queue=[...(predecessors.get(id) ?? [])]; while(queue.length){const current=queue.shift();if(seen.has(current))continue;seen.add(current);queue.push(...(predecessors.get(current) ?? []));}return [...seen]; };
  const produces = (node,name) => Object.hasOwn(node?.outputs_schema?.properties ?? {},name) && (node.outputs_schema.required ?? []).includes(name);
  for (const mapping of result.requirement_mappings) for (const name of mapping.binding_names ?? []) for (const id of mapping.node_ids ?? []) {
    const node=nodes.get(id);if(!node || produces(node,name) || Object.hasOwn(node.input_bindings ?? {},name) || !['agent','human_gate','tool'].includes(node.type))continue;
    const producers=ancestors(id).map(candidate=>nodes.get(candidate)).filter(candidate=>produces(candidate,name));
    if(producers.length===1){node.input_bindings ??={};node.input_bindings[name]=`/nodes/${producers[0].id}/output/${name}`;}
  }
  // requirement_ids is a runtime projection of the authoritative mapping, not
  // a second semantic judgment. Fill it for every mapped node so generation
  // cannot fail merely because the same relationship was omitted from one of
  // two redundant fields.
  for (const mapping of result.requirement_mappings) {
    const requirement=result.source_requirements.find(item=>item.requirement_id===mapping.requirement_id);
    if(contractProjection) mapping.resource_refs=[...new Set([...(mapping.resource_refs ?? []),...(requirement?.resource_refs ?? [])])];
    for (const id of mapping.node_ids ?? []) {
    const node = nodes.get(id);
    if (node) {
      node.requirement_ids = [...new Set([...(node.requirement_ids ?? []), mapping.requirement_id])];
      // Mapping resource evidence is the authoritative semantic selection;
      // node.resource_refs is its runtime projection, not a second model field.
      if (contractProjection) node.resource_refs = [...new Set([...(node.resource_refs ?? []), ...(mapping.resource_refs ?? [])])];
      if(contractProjection&&mapping.status!=='unsupported'&&requirement?.requirement_kind==='artifact_path'&&requirement.trigger!=='runtime_resolved_artifact'&&node.type!=='human_gate'){
        node.required_artifacts=[...new Map([...(node.required_artifacts??[]),{requirement_id:requirement.requirement_id,path:requirement.details.artifact_path}].map(item=>[item.requirement_id,item])).values()];
      }
    }
  }
  }
  // `compiled` is a host-verifiable claim, not planner confidence. Requirements
  // whose truth still depends on an Agent following prose are faithfully
  // retained but explicitly agent-assisted. This repair is deterministic and
  // avoids another planner round merely to change a status label.
  const compiledByStructure = (requirement,mapping) => {
    const mapped=(mapping.node_ids ?? []).map(id=>nodes.get(id)).filter(Boolean);
    if (requirement?.requirement_kind==='approval') return mapped.some(node=>node.type==='human_gate') && mapped.some(node=>node.type!=='human_gate');
    if (['script_operation','registered_tool','canonicalization','method_rule','artifact_path'].includes(requirement?.requirement_kind)) return mapped.some(node=>node.type==='tool');
    if (requirement?.requirement_kind==='artifact_schema') {
      if (mapped.some(node=>node.type==='tool')) return true;
      const terms=requirement.details?.interface_terms ?? [];
      const schemaKeys=node=>{const found=new Set();const visit=value=>{if(!value||typeof value!=='object'||Array.isArray(value))return;for(const [key,child] of Object.entries(value.properties ?? {})){found.add(key);visit(child);}if(value.items)visit(value.items);if(value.additionalProperties&&typeof value.additionalProperties==='object')visit(value.additionalProperties);};visit(node.outputs_schema);return found;};
      return terms.length>0 && mapped.some(node=>{const keys=schemaKeys(node);return terms.every(term=>keys.has(term));});
    }
    if (requirement?.requirement_kind==='data_dependency') return (mapping.binding_names ?? []).length>0;
    if (requirement?.requirement_kind==='dependency') return typeof requirement.details?.executable==='string';
    return false;
  };
  for (const mapping of result.requirement_mappings) if (mapping.status==='compiled') {
    const requirement=result.source_requirements.find(item=>item.requirement_id===mapping.requirement_id);
    if (requirement && !compiledByStructure(requirement,mapping)) {
      mapping.status='agent_assisted';
      mapping.rationale=`Host downgraded compiled to agent_assisted because ${requirement.requirement_kind} is enforced only by Agent interpretation. ${mapping.rationale}`.slice(0,2000);
    }
  }
  // Section dispositions and requirement assignments are the authoritative
  // semantic links. Project their Host-owned source coordinates onto the
  // responsible nodes so review sees the same evidence
  // that the coverage table already records. This does not infer new intent.
  const appendSpans=(item,spans)=>{
    if(!item || !spans?.length)return;
    const existing=item.source_spans ?? (item.source_span?[item.source_span]:[]);
    item.source_spans=[...new Map([...existing,...spans].map(span=>[`${span.resource}:${span.start_line}:${span.end_line}`,structuredClone(span)])).values()];
    item.source_span ??= item.source_spans[0];
  };
  const sections=new Map(sourceSectionInventory(resources).map(section=>[section.section_id,section]));
  for(const disposition of result.source_dispositions ?? []) {
    if(disposition.disposition==='omit')continue;
    const section=sections.get(disposition.section_id);
    if(!section)continue;
    for(const id of disposition.node_ids ?? []) {
      const node=nodes.get(id);
      appendSpans(node,[section.source_span]);
      if(node && contractProjection && ['agent','tool','human_gate'].includes(node.type)) node.resource_refs=[...new Set([...(node.resource_refs ?? []),section.source_span.resource])];
    }
  }
  for(const mapping of result.requirement_mappings) {
    const requirement=result.source_requirements.find(item=>item.requirement_id===mapping.requirement_id);
    for(const id of mapping.node_ids ?? [])appendSpans(nodes.get(id),requirement?.source_spans);
  }
  // The executable list is a canonical projection of host-observed dependency
  // facts plus the accepted mapping status. It is not free-form planner output.
  // Unconditional dependencies are source facts, not a reward for choosing the
  // word `compiled`. Deliberately unsupported requirements still block later;
  // every other unconditional dependency remains visible to preparation.
  const mappingById = new Map(result.requirement_mappings.map(item => [item.requirement_id, item]));
  const executableEvidence = new Map(),executableDescriptors=[];
  for (const requirement of result.source_requirements) if (requirement.requirement_kind === 'dependency'
    && requirement.details?.phase === 'unconditional' && mappingById.get(requirement.requirement_id)?.status !== 'unsupported') {
    const name = requirement.details.executable;
    executableDescriptors.push({name,...(requirement.details.version?{version:requirement.details.version}:{}),...(requirement.details.python_modules?{python_modules:requirement.details.python_modules}:{})});
    if (!executableEvidence.has(name)) executableEvidence.set(name,structuredClone(requirement.source_spans[0]));
  }
  if (contractProjection) result.required_executables = normalizeExecutableRequirements(executableDescriptors).map(item=>({...item,confidence:1,source_span:executableEvidence.get(item.name)}));
  return result;
}

export function mergeSourceRequirements(observed, proposed = []) {
  const merged = new Map(observed.map(item => [item.requirement_id, structuredClone(item)]));
  for (const item of proposed) if (!merged.has(item.requirement_id)) merged.set(item.requirement_id, structuredClone(item));
  return [...merged.values()];
}
