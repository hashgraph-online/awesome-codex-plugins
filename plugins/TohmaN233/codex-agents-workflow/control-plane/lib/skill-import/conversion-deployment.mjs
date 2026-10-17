import { basename } from 'node:path';
import { authoringSourcePath, SKILL_SOURCE, BRIEF_SOURCE } from './authoring-source.mjs';
import { sourceSectionInventory } from './source-dispositions.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { digest } from '../workflow-revisions.mjs';
import { reconcileImportObservations, sanitizeConversionReviewHistory } from './import-reconciliation.mjs';
import { GENERATION_EXECUTOR_OPTIONS } from '../authoring/generation-executor-policy.mjs';
import { runtimeCallableInterface } from './callable-runtime-interface.mjs';
export { reconcileImportObservations, sanitizeConversionReviewHistory, sanitizeImportObservation } from './import-reconciliation.mjs';

const forbiddenEntrypoints = new Set([SKILL_SOURCE.toLowerCase(), BRIEF_SOURCE.toLowerCase()]);
const forbiddenReportKeys = new Set(['source_path', 'metadata_files', 'resource_inventory', 'canonical_proposal']);

const portablePath = path => String(path).replaceAll('\\', '/');
function assetPath(path) {
  const relative = portablePath(path).replace(/^source\//i, '');
  requireValue(relative && !['skill.md', 'workflow.md'].includes(relative.toLowerCase()),
    'CONVERTED_SOURCE_ENTRYPOINT', 'Source entrypoints cannot become deployable Workflow assets');
  const parts=relative.split('/');
  if(['skill.md','workflow.md'].includes(parts.at(-1).toLowerCase()))parts[parts.length-1]='instructions.md';
  return `workflow-assets/${parts.join('/')}`;
}

function replaceAll(text, replacements, originalSourcePath) {
  let result = String(text ?? '');
  for (const [from, to] of replacements) result = result.split(from).join(to);
  for (const entrypoint of [SKILL_SOURCE, BRIEF_SOURCE]) result = result.split(entrypoint).join('the compiled Workflow contract');
  if (originalSourcePath) result = result.split(originalSourcePath).join('the private authoring source');
  result = result.replace(/pinned source Skill/gi, 'compiled Workflow contract').replace(/original Skill/gi, 'private authoring source');
  return result;
}

function remapValue(value, replacements, originalSourcePath) {
  if (typeof value === 'string') return replaceAll(value, replacements, originalSourcePath);
  if (Array.isArray(value)) return value.map(item => remapValue(item, replacements, originalSourcePath));
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, remapValue(item, replacements, originalSourcePath)]));
}

function evidenceIds(item, inventory) {
  const spans = [item?.origin?.source_span, ...(item?.origin?.source_spans ?? [])].filter(Boolean);
  return [...new Set(inventory.filter(section => spans.some(span => span.resource === section.source_span.resource
    && span.start_line <= section.source_span.end_line && span.end_line >= section.source_span.start_line)).map(section => section.section_id))].sort();
}

function sanitizedCoverage(coverage, replacements, originalSourcePath) {
  return (coverage ?? []).map(item => ({
    requirement_id: item.requirement_id,
    requirement_kind: item.requirement_kind,
    status: item.status,
    reason: item.reason,
    ...(item.details?{details:remapValue(item.details.callable_id?{...item.details,interface:runtimeCallableInterface(item.details.interface)}:item.details,replacements,originalSourcePath)}:{}),
    ...(item.runtime_activation?{runtime_activation:structuredClone(item.runtime_activation)}:{}),
    node_ids: [...(item.node_ids ?? [])],
    binding_names: [...(item.binding_names ?? [])],
    runtime_guards: [...(item.runtime_guards ?? [])],
    resource_refs: [...new Set((item.resource_refs ?? []).filter(path => !forbiddenEntrypoints.has(portablePath(path).toLowerCase())).map(path => replacements.get(path) ?? path))],
  }));
}

function sanitizedDispositions(proposal) {
  return (proposal.source_dispositions ?? []).map(item => ({
    section_id: item.section_id,
    disposition: item.disposition,
    node_ids: [...(item.node_ids ?? [])],
    requirement_ids: [...(item.requirement_ids ?? [])],
    ...(item.trigger ? { trigger: item.trigger } : {}),
    rationale: item.rationale,
  }));
}

/**
 * Lower a reviewed private authoring bundle into the deployable Workflow
 * package. The entrypoint, source paths, raw proposal and source history do not
 * cross this boundary. Only explicitly referenced supporting assets survive,
 * under Workflow-owned logical IDs.
 */
export function compileDeployableConversion({ workflow, proposal, resources, pack, proposalHash, reviewContractVersion }) {
  const entrypoint = authoringSourcePath(resources); const inventory = sourceSectionInventory(resources);
  const sourceHash=pack.provenance?.source_hash ?? workflow.import_status?.source_hash ?? digest(resources[entrypoint]);
  const referenced = new Set((workflow.nodes ?? []).flatMap(node => node.resources ?? []).filter(path => path !== entrypoint));
  const replacements = new Map([...referenced].sort().map(path => [path, assetPath(path)]));
  requireValue(new Set(replacements.values()).size===replacements.size,'CONVERTED_ASSET_COLLISION','Two source assets resolve to the same Workflow-owned path');
  const deployedResources = Object.create(null);
  const originalSourcePath = pack.provenance?.source_path ?? null;
  const privateSourceRoots=originalSourcePath?[portablePath(originalSourcePath).replace(/\/[^/]+$/,'')]:[];
  for (const [source, target] of replacements) {
    requireValue(Buffer.isBuffer(resources[source]), 'CONVERTED_ASSET_MISSING', `Referenced Workflow asset is unavailable: ${source}`);
    const bytes = Buffer.from(resources[source]);
    const text = bytes.toString('utf8');
    requireValue(!bytes.includes(resources[entrypoint]),'CONVERTED_SOURCE_ENTRYPOINT','A supporting asset cannot duplicate the private authoring entrypoint');
    deployedResources[target] = source.toLowerCase().endsWith('.md') && Buffer.from(text,'utf8').equals(bytes)
      ? Buffer.from(replaceAll(text,replacements,pack.provenance?.source_path ?? null),'utf8') : bytes;
  }

  const reconciliation=reconcileImportObservations({workflow,proposal,resources,pack});
  const deployed = remapValue(workflow,replacements,originalSourcePath);
  deployed.skill_policy = { mode: 'cooperative', implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] };
  deployed.host_tools = remapValue(deployed.host_tools ?? [], replacements, originalSourcePath);
  deployed.nodes = workflow.nodes.map(node => {
    const next = remapValue(node,replacements,originalSourcePath);
    next.resources = [...new Set((node.resources ?? []).filter(path => path !== entrypoint).map(path => replacements.get(path) ?? path))];
    if (typeof next.prompt_template === 'string') next.prompt_template = replaceAll(next.prompt_template, replacements, originalSourcePath);
    if (next.id === 'final' && deployed.finalization?.node_id === 'final') {
      next.resources = [];
      next.prompt_template = 'Review the declared upstream result against the user task, this Workflow\'s output contract, produced artifacts and verification evidence. Identify a concrete blocker when evidence is insufficient. Return the declared acceptance result with the supporting evidence.';
    }
    if (next.origin) next.origin = { kind: 'converted', reviewed: true, evidence_ids: evidenceIds(node, inventory) };
    return next;
  });
  deployed.edges = deployed.edges.map(edge => edge.origin
    ? { ...structuredClone(edge), origin: { kind: 'converted', reviewed: true, evidence_ids: evidenceIds(edge, inventory) } }
    : structuredClone(edge));
  deployed.import_status = {
    mode: 'ai_expanded',
    source_hash: sourceHash,
    classification: workflow.import_status?.classification ?? 'workflow',
    unresolved: reconciliation.unresolved,
    source_independent: true,
    conversion_level: workflow.import_status?.conversion_level,
    conversion_contract_version: workflow.import_status?.conversion_contract_version,
    requirement_coverage: sanitizedCoverage(workflow.import_status?.requirement_coverage, replacements, originalSourcePath),
    source_dispositions: sanitizedDispositions(proposal),
  };
  const provenance = {
    kind: 'workflow_conversion', compiler_version: 5,
    source_kind: entrypoint === SKILL_SOURCE ? 'skill' : 'brief',
    source_hash: deployed.import_status.source_hash,
    conversion: { source_revision: pack.revision_hash, proposal_hash: proposalHash, review_contract_version: reviewContractVersion },
  };
  const importReport = {
    mode: 'converted', calls_to_models: 2, scripts_executed: 0,
    reconciliation,
    ...(pack.import_report?.review_history?{review_history:remapValue(sanitizeConversionReviewHistory(pack.import_report.review_history,{resources}),replacements,originalSourcePath)}:{}),
    expansion: {
      source_revision: pack.revision_hash,
      source_hash: deployed.import_status.source_hash,
      proposal_hash: proposalHash,
      status: 'draft',
      conversion_level: deployed.import_status.conversion_level,
      requirement_coverage: structuredClone(deployed.import_status.requirement_coverage),
      source_dispositions: structuredClone(deployed.import_status.source_dispositions),
      inferred_nodes: proposal.nodes.length,
      inferred_edges: proposal.edges.length,
      executor_options:structuredClone(GENERATION_EXECUTOR_OPTIONS),
    },
  };
  const result={ workflow: deployed, resources: deployedResources, provenance, import_report: importReport };
  requireDeployableConvertedSnapshot({...result,resources:Object.keys(deployedResources).map(path=>({path}))},{resourceBytes:deployedResources,privateSourceRoots});
  return result;
}

function containsPrivateRoot(value,roots){
  const normalized=String(value).replaceAll('\\\\','/').replaceAll('\\','/').toLowerCase();
  return roots.some(root=>{
    const path=portablePath(root).replace(/\/+$/,'').toLowerCase();
    if(!path)return false;
    let at=normalized.indexOf(path);
    while(at>=0){const next=normalized[at+path.length];if(next===undefined||next==='/'||!/[a-z0-9_.-]/i.test(next))return true;at=normalized.indexOf(path,at+path.length);}
    return false;
  });
}

function inspect(value, path = '$', findings = [], privateSourceRoots=[]) {
  if (typeof value === 'string') {
    if (/source[\\/](?:[^\\/\s]+[\\/])*(?:SKILL|WORKFLOW)\.md/i.test(value)) findings.push({ path, reason: 'source_entrypoint' });
    if(containsPrivateRoot(value,privateSourceRoots))findings.push({path,reason:'private_source_root'});
    return findings;
  }
  if (Array.isArray(value)) { value.forEach((item, index) => inspect(item, `${path}[${index}]`, findings,privateSourceRoots)); return findings; }
  if (!value || typeof value !== 'object') return findings;
  const privateMetadata=path==='$.workflow'||path==='$.workflow.import_status'||path.startsWith('$.workflow.import_status.')
    ||path==='$.provenance'||path.startsWith('$.provenance.')||path==='$.import_report'||path.startsWith('$.import_report.');
  for (const [key, item] of Object.entries(value)) {
    if (privateMetadata && forbiddenReportKeys.has(key)) findings.push({ path: `${path}.${key}`, reason: 'private_authoring_field' });
    const publicEditPath=key==='path'&&value.code==='RESOURCE_EDIT_REQUIRES_REVIEW'&&typeof item==='string'
      &&/^workflow-assets\/[A-Za-z0-9._/-]+$/.test(item)&&!item.split('/').some(part=>part==='.'||part==='..'||!part);
    if(path.includes('.review_history[')&&path.endsWith('.observation')&&['path','target','source_quote','source_text','replacement'].includes(key)&&!publicEditPath)findings.push({path:`${path}.${key}`,reason:'private_review_observation'});
    if ((key === 'source_span' || key === 'source_spans') && [item].flat().some(span=>span&&typeof span==='object'
      &&typeof span.resource==='string'
      &&Number.isInteger(span.start_line)&&Number.isInteger(span.end_line))) findings.push({ path: `${path}.${key}`, reason: 'source_location' });
    inspect(item, `${path}.${key}`, findings,privateSourceRoots);
  }
  return findings;
}

export function requireDeployableConvertedSnapshot(snapshot,{resourceBytes=snapshot.resourceBytes,privateSourceRoots=snapshot.privateSourceRoots??[]}={}) {
  if (snapshot.workflow?.import_status?.mode !== 'ai_expanded' && snapshot.provenance?.kind !== 'workflow_conversion') return true;
  requireValue(snapshot.provenance?.kind === 'workflow_conversion' && typeof snapshot.provenance.source_hash === 'string'
    && /^[a-f0-9]{64}$/.test(snapshot.provenance.source_hash), 'CONVERTED_PROVENANCE', 'Converted Workflow needs only opaque deployable provenance');
  requireValue(snapshot.workflow.skill_policy?.ambient_allow?.length === 0 && snapshot.workflow.skill_policy?.shadowed_skill_paths?.length === 0
    && snapshot.workflow.skill_policy?.implicit === 'deny', 'CONVERTED_SKILL_ISOLATION', 'Converted Workflow must be independent of source and ambient Skills');
  requireValue(!(snapshot.workflow.nodes ?? []).some(node => node.type === 'skill_ref' || node.skill_ref), 'CONVERTED_SKILL_REFERENCE', 'Converted Workflow cannot retain SkillRef nodes');
  const manifest=Array.isArray(snapshot.resources)?snapshot.resources:Object.keys(snapshot.resources??{}).map(path=>({path}));
  const forbiddenResources = manifest.map(item => item.path).filter(path => portablePath(path).toLowerCase().startsWith('source/')
    || ['skill.md', 'workflow.md'].includes(basename(path).toLowerCase()));
  requireValue(forbiddenResources.length === 0, 'CONVERTED_SOURCE_RESOURCE', 'Converted Workflow package retains private authoring resources', { resources: forbiddenResources });
  const findings = inspect({ workflow: snapshot.workflow, provenance: snapshot.provenance, import_report: snapshot.import_report },'$',[],privateSourceRoots);
  requireValue(findings.length === 0, 'CONVERTED_SOURCE_LEAK', 'Converted Workflow metadata retains private source content or paths', { findings });
  if(resourceBytes){
    requireValue(Object.keys(resourceBytes).length===manifest.length&&manifest.every(item=>Buffer.isBuffer(resourceBytes[item.path])&&(!item.sha256||digest(resourceBytes[item.path])===item.sha256)),
      'CONVERTED_RESOURCE_BYTES','Converted Workflow resource bytes do not match the package manifest');
    const assetFindings=[];
    for(const item of manifest)inspect(resourceBytes[item.path].toString('utf8'),item.path,assetFindings,privateSourceRoots);
    requireValue(assetFindings.length===0,'CONVERTED_ASSET_SOURCE_LEAK','Converted Workflow asset bytes retain private source entrypoints or paths',{findings:assetFindings});
  }
  return true;
}
