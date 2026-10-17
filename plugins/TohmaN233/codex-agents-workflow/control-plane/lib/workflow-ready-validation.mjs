import { requireValue } from './workflow-paths.mjs';
import { requireWorkflowResourceClosure } from './workflow-resource-validation.mjs';
import { conversionCertificateRequired, requireCurrentConversionCertificate } from './skill-import/conversion-certificate.mjs';
import { requireDeployableConvertedSnapshot } from './skill-import/conversion-deployment.mjs';
import { canonicalJSON } from './workflow-revisions.mjs';

const privateProvenanceKinds=new Set(['skill_import','workflow_build']);

function requirePrivateAuthoringIdentity(snapshot,previous){
  if(!privateProvenanceKinds.has(previous?.provenance?.kind))return false;
  const priorKind=previous.provenance.kind,currentKind=snapshot.provenance?.kind;
  const expectedMode=priorKind==='skill_import'?'coarse':'authored';
  const previousSourceHash=previous.provenance.source_hash ?? previous.workflow?.import_status?.source_hash
    ?? previous.resources?.find(item=>['source/SKILL.md','source/WORKFLOW.md'].includes(item.path))?.sha256;
  if(currentKind===priorKind){
    requireValue(canonicalJSON(snapshot.provenance)===canonicalJSON(previous.provenance),
      'CONVERSION_IDENTITY_REQUIRED','Private authoring provenance is Host-owned and cannot be edited or erased');
    requireValue([expectedMode,'ai_expanded'].includes(snapshot.workflow?.import_status?.mode)
      && snapshot.workflow.import_status.source_hash===previousSourceHash,
      'CONVERSION_IDENTITY_REQUIRED','Private authoring status cannot erase or replace its source identity');
    return true;
  }
  requireValue(currentKind==='workflow_conversion'
    && snapshot.provenance?.conversion?.source_revision===previous.revision_hash
    && snapshot.workflow?.import_status?.mode==='ai_expanded'
    && snapshot.import_report?.expansion?.certificate,
  'CONVERSION_IDENTITY_REQUIRED','Private authoring state may only cross the certified source-free conversion boundary');
  requireValue(typeof previousSourceHash==='string' && /^[a-f0-9]{64}$/.test(previousSourceHash)
    && snapshot.provenance.source_hash===previousSourceHash && snapshot.workflow.import_status.source_hash===previousSourceHash
    && snapshot.import_report.expansion.source_hash===previousSourceHash,
  'CONVERSION_IDENTITY_REQUIRED','Source-free conversion must retain the prior opaque source content hash');
  requireDeployableConvertedSnapshot(snapshot);
  requireCurrentConversionCertificate(snapshot.workflow,snapshot.resources,snapshot.import_report,{required:true,provenance:snapshot.provenance});
  return true;
}

function requirePreservedConversionIdentity(snapshot, previous) {
  const inherited = conversionCertificateRequired(previous?.workflow, previous?.import_report);
  if (!inherited) return false;
  requireValue(snapshot.workflow?.import_status?.mode === 'ai_expanded' && snapshot.import_report?.expansion,
    'CONVERSION_IDENTITY_REQUIRED','A converted Workflow cannot erase or downgrade its Host-protected conversion identity');
  return true;
}

// This is the single persistence boundary for invariants that depend on the
// complete Pack rather than only on graph shape. It deliberately runs for
// every Store create/save path, including package install, duplicate and
// revision restore.
export function requireWorkflowSnapshotIntegrity(snapshot, { previous = null } = {}) {
  requirePrivateAuthoringIdentity(snapshot,previous);
  const inheritedConversion = requirePreservedConversionIdentity(snapshot, previous);
  const deployedConversion=snapshot.provenance?.kind==='workflow_conversion';
  if(deployedConversion)requireDeployableConvertedSnapshot(snapshot);
  else if(snapshot.workflow?.status==='ready' && (['skill_import','workflow_build'].includes(snapshot.provenance?.kind) || ['coarse','authored','ai_expanded'].includes(snapshot.workflow?.import_status?.mode)))
    requireValue(false,'CONVERTED_DEPLOYMENT_REQUIRED','Private authoring source must cross the source-free deployment boundary before Ready publication');
  if (snapshot.workflow?.status !== 'ready') return true;
  requireWorkflowResourceClosure(snapshot.workflow, snapshot.resources);
  requireCurrentConversionCertificate(snapshot.workflow, snapshot.resources, snapshot.import_report, { required: inheritedConversion,provenance:snapshot.provenance });
  return true;
}
