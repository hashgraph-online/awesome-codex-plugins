import { canonicalJSON, digest, prepareResources } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { CONVERSION_CONTRACT } from './conversion-contract.mjs';

const PINNED_REVIEW_CONTRACTS=new Set([12,13,14,CONVERSION_CONTRACT.version]);
const LEGACY_REVIEW_CONTRACT=12;
const same=(left,right)=>left===undefined||right===undefined?left===right:canonicalJSON(left)===canonicalJSON(right);
const mismatch=(field,expected,observed)=>({field,expected,observed});
function requirePinnedReviewContract(version){
  requireValue(PINNED_REVIEW_CONTRACTS.has(version),'CONVERSION_REVIEW_CONTRACT_UNSUPPORTED',
    'Converted Workflow uses an unsupported pinned review contract',
    {field:'import_report.expansion.certificate.review_contract_version',observed:version,supported:[...PINNED_REVIEW_CONTRACTS].sort((a,b)=>a-b),current:CONVERSION_CONTRACT.version});
}

function semanticWorkflow(workflow) {
  const {
    revision: _revision,
    status: _status,
    enabled: _enabled,
    id: _id,
    name: _name,
    description: _description,
    tags: _tags,
    ...semantic
  } = structuredClone(workflow);
  // Only the generated reminder for per-item inference confirmation is review
  // metadata.  Conversion level, dependency observations and every other
  // import blocker stay certificate-bound and cannot be cleared by editing a
  // Draft.
  if (semantic.import_status?.unresolved) semantic.import_status.unresolved=semantic.import_status.unresolved.filter(issue=>issue.code!=='AI_INFERENCES_REQUIRE_REVIEW');
  for (const kind of ['nodes', 'edges']) for (const item of semantic[kind] ?? []) {
    if (!item.origin) continue;
    delete item.origin.reviewed;
    delete item.origin.review;
  }
  return semantic;
}

function manifestOf(resources) {
  if (Array.isArray(resources)) return structuredClone(resources);
  return prepareResources(resources ?? {}).manifest;
}

export function conversionWorkflowHash(workflow) {
  return digest(canonicalJSON(semanticWorkflow(workflow)));
}

export function conversionResourceHash(resources) {
  return digest(canonicalJSON(manifestOf(resources)));
}

export function conversionCertificateRequired(workflow, importReport) {
  return workflow?.import_status?.mode === 'ai_expanded' || Boolean(importReport?.expansion);
}

export function createConversionCertificate(workflow, resources, { source_revision, source_hash, proposal_hash, review_contract_version }) {
  requireValue(review_contract_version===CONVERSION_CONTRACT.version,'CONVERSION_REVIEW_CONTRACT_STALE','A current conversion certificate requires the current review contract');
  requireValue(typeof source_hash==='string' && /^[a-f0-9]{64}$/.test(source_hash),'CONVERSION_SOURCE_HASH','A deployable conversion certificate requires the opaque source content hash');
  return {
    version: 2,
    review_contract_version,
    source_revision,
    source_hash,
    proposal_hash,
    workflow_hash: conversionWorkflowHash(workflow),
    resources_hash: conversionResourceHash(resources),
  };
}

export function requireCurrentConversionCertificate(workflow, resources, importReport, { required = false, provenance = null } = {}) {
  if (!required && !conversionCertificateRequired(workflow, importReport)) return null;
  requireValue(workflow?.import_status?.mode === 'ai_expanded' && importReport?.expansion,
    'CONVERSION_IDENTITY_REQUIRED','A converted Workflow cannot erase or downgrade its Host-protected conversion identity');
  const certificate=importReport?.expansion?.certificate;
  requireValue(certificate && certificate.version===2,'CONVERSION_CERTIFICATE_REQUIRED','AI-expanded Workflow must be revalidated at the deployable package boundary before Ready publication');
  requirePinnedReviewContract(certificate.review_contract_version);
  const differences=[
    ['workflow_hash',conversionWorkflowHash(workflow),certificate.workflow_hash],
    ['resources_hash',conversionResourceHash(resources),certificate.resources_hash],
    ['source_revision',importReport.expansion.source_revision,certificate.source_revision],
    ['proposal_hash',importReport.expansion.proposal_hash,certificate.proposal_hash],
    ['source_hash',importReport.expansion.source_hash,certificate.source_hash],
  ].filter(([,expected,observed])=>expected!==observed).map(([field,expected,observed])=>mismatch(`import_report.expansion.certificate.${field}`,expected,observed));
  if(!/^[a-f0-9]{64}$/.test(certificate.source_hash))differences.push(mismatch('import_report.expansion.certificate.source_hash','64 lowercase hexadecimal characters',certificate.source_hash));
  if(certificate.review_contract_version===LEGACY_REVIEW_CONTRACT)for(const field of ['source_revision','proposal_hash']){
    if(!/^[a-f0-9]{64}$/.test(certificate[field]))
      differences.push(mismatch(`import_report.expansion.certificate.${field}`,'64 lowercase hexadecimal characters',certificate[field]));
  }
  requireValue(differences.length===0,'CONVERSION_CERTIFICATE_STALE','AI-expanded Workflow differs from its pinned conversion certificate',{review_contract_version:certificate.review_contract_version,differences});
  if(certificate.review_contract_version===LEGACY_REVIEW_CONTRACT&&provenance)
    requireAcceptedConversionIdentity({workflow,resources,import_report:importReport,provenance},certificate);
  return structuredClone(certificate);
}

function requireAcceptedConversionIdentity(pack,certificate){
  const expansion=pack.import_report?.expansion,provenance=pack.provenance,status=pack.workflow?.import_status;
  const identityDifferences=[
    ['provenance.kind','workflow_conversion',provenance?.kind],
    ['provenance.source_hash',certificate.source_hash,provenance?.source_hash],
    ['provenance.conversion.source_revision',certificate.source_revision,provenance?.conversion?.source_revision],
    ['provenance.conversion.proposal_hash',certificate.proposal_hash,provenance?.conversion?.proposal_hash],
    ['provenance.conversion.review_contract_version',certificate.review_contract_version,provenance?.conversion?.review_contract_version],
    ['workflow.import_status.mode','ai_expanded',status?.mode],
    ['workflow.import_status.source_hash',certificate.source_hash,status?.source_hash],
    ['import_report.expansion.source_revision',certificate.source_revision,expansion?.source_revision],
    ['import_report.expansion.source_hash',certificate.source_hash,expansion?.source_hash],
    ['import_report.expansion.proposal_hash',certificate.proposal_hash,expansion?.proposal_hash],
  ].filter(([,expected,observed])=>expected!==observed).map(([field,expected,observed])=>mismatch(field,expected,observed));
  requireValue(identityDifferences.length===0,'CONVERSION_IDENTITY_REQUIRED',
    'Edited Workflow must retain its accepted conversion source and proposal identity',{differences:identityDifferences});
  const classificationDifferences=[
    ['workflow.import_status.source_independent',true,status?.source_independent],
    ['workflow.import_status.conversion_contract_version',3,status?.conversion_contract_version],
    ['workflow.import_status.conversion_level',expansion?.conversion_level,status?.conversion_level],
  ].filter(([,expected,observed])=>expected!==observed).map(([field,expected,observed])=>mismatch(field,expected,observed));
  if(!same(status?.requirement_coverage,expansion?.requirement_coverage))classificationDifferences.push({field:'workflow.import_status.requirement_coverage'});
  if(!same(status?.source_dispositions,expansion?.source_dispositions))classificationDifferences.push({field:'workflow.import_status.source_dispositions'});
  requireValue(classificationDifferences.length===0,'CONVERSION_IDENTITY_REQUIRED',
    'Edited Workflow cannot rewrite its accepted conversion classification or requirement evidence',
    {differences:classificationDifferences});
}

// Direct publication binds the edited Pack's actual content to its original
// conversion identity. Source identity and conversion level remain protected.
// The editor may, however, change the graph's requirement-node assignments or
// source dispositions; publication records those reviewed graph edits as the
// new accepted classification before sealing the new content hash.
export function certificateForPublishedWorkflow(pack) {
  if (!conversionCertificateRequired(pack.workflow, pack.import_report)) return pack.import_report;
  const certificate=pack.import_report?.expansion?.certificate;
  requireValue(certificate?.version===2,'CONVERSION_CERTIFICATE_REQUIRED','Converted Workflow needs its source conversion certificate before publication');
  requirePinnedReviewContract(certificate.review_contract_version);
  const report=structuredClone(pack.import_report);
  report.expansion.requirement_coverage=structuredClone(pack.workflow.import_status.requirement_coverage);
  report.expansion.source_dispositions=structuredClone(pack.workflow.import_status.source_dispositions);
  requireAcceptedConversionIdentity({...pack,import_report:report},certificate);
  report.expansion.certificate={...certificate,
    workflow_hash:conversionWorkflowHash(pack.workflow),resources_hash:conversionResourceHash(pack.resources)};
  delete report.expansion.host_binding_renewal;
  requireCurrentConversionCertificate(pack.workflow,pack.resources,report,{required:true,provenance:pack.provenance});
  return report;
}
