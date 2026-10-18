import { dirname, posix } from 'node:path';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { analyzeSkillDependencies } from './dependency-reader.mjs';
import { parseSkill } from './skill-reader.mjs';
import { proveSelectionFixture, proveRejectingFetchFixture } from './credential-fixtures.mjs';

const resourceOf=issue=>typeof issue.path==='string' ? (issue.path.startsWith('source/')?issue.path:'source/'+issue.path) : null;
const matchKey=issue=>canonicalJSON(Object.fromEntries(['code','path','line','target','field','replacement'].filter(key=>issue[key]!==undefined).map(key=>[key,issue[key]])));
const occurrenceHash=(issue,resources,ordinal)=>digest(canonicalJSON({observation:issue,resource_sha256:resources[resourceOf(issue)]?digest(resources[resourceOf(issue)]):null,ordinal}));

function commandEvidence(issue,resource,resources,nodes,scan){
  const text=resources[resource].toString('utf8'),line=text.split('\n')[issue.line-1]??'';
  if(/^\s*\/\//.test(line)||/^\s*banner:\s*\{\s*js:\s*['"]\/\//.test(line))return {reason:'command_comment_or_banner'};
  if(/(?:^|\/)package-lock\.json$/i.test(resource)){
    const metadata=JSON.parse(text);
    if(Object.values(metadata.packages??{}).some(pkg=>Object.values(pkg.bin??{}).includes(issue.target)))return {reason:'dependency_package_bin_metadata'};
  }
  let root=posix.dirname(resource);
  while(root!=='source'&&!resources[root+'/package.json']){const parent=posix.dirname(root);if(parent===root)break;root=parent;}
  const candidates=[posix.normalize(posix.join(posix.dirname(resource),issue.target??'')),root+'/'+issue.target,'source/'+issue.target];
  if(/\.json$/i.test(resource)){
    const metadata=JSON.parse(text);
    const record=metadata.files?.find(item=>item.path===issue.target&&/^[a-f0-9]{64}$/.test(item.sha256??''));
    if(record)for(const [path,bytes] of Object.entries(resources))if(path.endsWith('/'+issue.target)&&digest(bytes)===record.sha256)candidates.push(path);
  }
  for(const target of candidates){if(!resources[target])continue;
    const bound=nodes.filter(node=>(node.resources??[]).includes(resource)&&(node.resources??[]).includes(target)).map(node=>node.id);
    if(bound.length)return {reason:'bound_resource_reference',node_ids:bound,dependency_sha256:[digest(resources[target])]};
  }
  return null;
}

// Public diagnostics retain opaque occurrence identity and resource pins, never
// original paths, source excerpts or credential values. Identical observations
// use their occurrence ordinal rather than collapsing into one code-only issue.
export function sanitizeImportObservation(issue,{resources={},ordinal=0,reason='unresolved_import_observation'}={}) {
  const resource=resourceOf(issue);
  const existing=issue.occurrence_id??issue.id;
  return {code:issue.code,origin:['observed','declared','compiled','inferred'].includes(issue.origin)?issue.origin:'observed',occurrence_id:/^[a-f0-9]{64}$/.test(existing??'')?existing:occurrenceHash(issue,resources,ordinal),
    ...(resources[resource]?{resource_sha256:digest(resources[resource])}:/^[a-f0-9]{64}$/.test(issue.resource_sha256??'')?{resource_sha256:issue.resource_sha256}:{}),reason};
}

export function sanitizeConversionReviewHistory(history,{resources={}}={}) {
  return (history??[]).map(entry=>({...entry,decisions:(entry.decisions??[]).map((decision,ordinal)=>{
    if(!decision.observation)return {...decision};
    const observation=sanitizeImportObservation(decision.observation,{resources,ordinal,reason:'explicit_review_decision'});
    return {...decision,observation};
  })}));
}

export function reconcileImportObservations({workflow,proposal,resources,pack}) {
  let metadata=pack.provenance?.source_metadata??{};
  if(!Object.keys(metadata).length&&resources['source/SKILL.md']){
    // Synthetic compiler fixtures may use a plain source. Actual Skill imports
    // were parsed and pinned by readSkillSnapshot before this boundary.
    if(/^\uFEFF?---\r?\n/.test(resources['source/SKILL.md'].toString('utf8')))metadata=parseSkill(resources['source/SKILL.md'].toString('utf8')).metadata;
  }
  const snapshot={files:resources,metadata,root:pack.provenance?.source_path?dirname(pack.provenance.source_path):null,
    source_path:pack.provenance?.source_path,inventory:pack.import_report?.resource_inventory??[],problems:pack.import_report?.problems??[]};
  const scan=analyzeSkillDependencies(snapshot);
  const fresh=new Map(scan.unresolved.map(issue=>[matchKey(issue),issue]));
  const inherited=workflow.import_status?.unresolved??[];
  const occurrences=[...inherited,...scan.unresolved.filter(issue=>!inherited.some(old=>matchKey(old)===matchKey(issue)))];
  const referenced=new Set((workflow.nodes??[]).flatMap(node=>node.resources??[]));
  const evidence=[],unresolved=[];
  occurrences.forEach((issue,ordinal)=>{
    const resource=resourceOf(issue),bytes=resources[resource],current=fresh.get(matchKey(issue));
    let reason=null,dependency_sha256=[],node_ids=[];
    if(bytes&&issue.origin!=='declared'&&issue.code==='UNRESOLVED_LOCAL_REFERENCE'
      &&scan.references.some(item=>item.path===resource&&item.line===issue.line&&item.target===issue.target&&item.kind==='artifact_template'))reason='artifact_template_reference';
    else if(issue.code==='CREDENTIAL_REDACTED'){
      let proof=(current??issue).synthetic_evidence;
      if(proof?.kind==='selection_assertion')proof=bytes&&proof.resource_sha256===digest(bytes)?proveSelectionFixture(resources,resource,issue.replacement):null;
      else if(proof?.kind==='rejecting_fetch_fixture')proof=bytes&&proof.resource_sha256===digest(bytes)?proveRejectingFetchFixture(resources,resource,issue.replacement):null;
      if(bytes&&proof?.version===1&&proof.literal_length===1&&['selection_assertion','rejecting_fetch_fixture'].includes(proof.kind)
        &&proof.resource_sha256===digest(bytes)&&typeof issue.replacement==='string'&&bytes.includes(Buffer.from('['+issue.replacement+']')))
        {reason='redacted_synthetic_fixture';dependency_sha256=proof.dependency_sha256??[];}
    } else if(bytes&&issue.code==='SOURCE_LINKED_PATH'&&current?.synthetic_evidence?.kind==='pure_path_classifier_assertion'
      &&current.synthetic_evidence.resource_sha256===digest(bytes)){reason='pure_path_classifier_fixture';dependency_sha256=current.synthetic_evidence.dependency_sha256;}
    else if(bytes&&!current&&['UNRESOLVED_LOCAL_REFERENCE','INVALID_REFERENCE','UNRESOLVED_COMMAND_REFERENCE'].includes(issue.code)){
      if(issue.code==='UNRESOLVED_COMMAND_REFERENCE'){
        const proof=commandEvidence(issue,resource,resources,workflow.nodes??[],scan);
        if(proof){reason=proof.reason;node_ids=proof.node_ids??[];dependency_sha256=proof.dependency_sha256??[];}
      } else if(!/\.(?:md|markdown)$/i.test(resource))reason='non_markdown_syntax';
      else {
        const reference=scan.references.find(item=>item.path===resource&&item.line===issue.line&&item.target===issue.target&&item.present);
        if(reference&&referenced.has(reference.resolved)){
          node_ids=(workflow.nodes??[]).filter(node=>(node.resources??[]).includes(resource)&&(node.resources??[]).includes(reference.resolved)).map(node=>node.id);
          if(node_ids.length){reason='bound_resource_reference';dependency_sha256=[digest(resources[reference.resolved])];}
        }
      }
    } else if(bytes&&!current&&issue.code==='SOURCE_LINKED_PATH'
      &&scan.observations.some(item=>item.path===resource&&item.code==='RUNTIME_PATH_REFERENCE'))reason='platform_runtime_discovery_default';
    const diagnostic=sanitizeImportObservation(issue,{resources,ordinal,reason:reason??'unresolved_import_observation'});
    evidence.push({...diagnostic,resolution:reason?'reconciled':'unresolved',...(node_ids.length?{node_ids}: {}),...(dependency_sha256.length?{dependency_sha256}: {})});
    if(!reason)unresolved.push(diagnostic);
  });
  return {version:1,unresolved,evidence,scan_sha256:digest(canonicalJSON({requirements:scan.requirements,references:scan.references,unresolved:scan.unresolved})),
    proposal_sha256:digest(canonicalJSON(proposal)),resources_sha256:digest(canonicalJSON(Object.entries(resources).sort(([a],[b])=>a.localeCompare(b)).map(([path,bytes])=>({path,sha256:digest(bytes)}))))};
}
