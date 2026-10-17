import { canonicalJSON, digest, prepareResources, revisionHash } from './workflow-revisions.mjs';
import { requireValue } from './workflow-paths.mjs';
import { requireWorkflowSnapshotIntegrity } from './workflow-ready-validation.mjs';
import { normalizeExecutableRequirements } from './runtime-requirements.mjs';

export const WORKFLOW_PACKAGE_FORMAT='codex.workflow.package';
export const WORKFLOW_PACKAGE_VERSION=1;
export const WORKFLOW_PACKAGE_API=1;

function payloadOf(pack,resources,packageVersion){
  requireValue(/^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/.test(packageVersion),'WORKFLOW_PACKAGE_SEMVER','Workflow package version must be semantic');
  const objects=Object.entries(resources).sort(([a],[b])=>a<b?-1:a>b?1:0).map(([path,bytes])=>({path,sha256:digest(bytes),bytes:bytes.length,content_base64:Buffer.from(bytes).toString('base64')}));
  return {format:WORKFLOW_PACKAGE_FORMAT,format_version:WORKFLOW_PACKAGE_VERSION,package:{id:pack.workflow.id,version:packageVersion},compatibility:{plugin:'codex-agents-workflow',package_api:WORKFLOW_PACKAGE_API,workflow_schema:pack.workflow.schema_version},dependencies:{providers:[...(pack.workflow.requirements?.providers ?? [])].sort(),tools:[...(pack.workflow.requirements?.tools ?? [])].sort(),mcp_servers:[...(pack.workflow.requirements?.mcp_servers ?? [])].sort(),executables:normalizeExecutableRequirements(pack.workflow.requirements?.executables ?? [])},snapshot:{workflow:structuredClone(pack.workflow),resources:structuredClone(pack.resources),provenance:structuredClone(pack.provenance),import_report:structuredClone(pack.import_report),revision_hash:pack.revision_hash},objects};
}

function requirePublicPackageResources(resources) {
  const privatePaths=Object.keys(resources ?? {}).filter(path=>String(path).replaceAll('\\','/').toLowerCase().startsWith('source/'));
  requireValue(privatePaths.length===0,'WORKFLOW_PACKAGE_AUTHORING_PRIVATE','Private conversion sources cannot be exported or installed as Workflow package resources',{resources:privatePaths});
}

export function exportWorkflowPackage(pack,resources,{packageVersion='1.0.0'}={}){
  requirePublicPackageResources(resources);
  requireWorkflowSnapshotIntegrity({workflow:pack.workflow,resources:pack.resources,provenance:pack.provenance,import_report:pack.import_report});
  const payload=payloadOf(pack,resources,packageVersion);
  return {...payload,package_sha256:digest(canonicalJSON(payload))};
}

export function validateWorkflowPackage(bundle){
  requireValue(bundle && typeof bundle==='object' && !Array.isArray(bundle),'WORKFLOW_PACKAGE','Workflow package must be an object');
  const {package_sha256,...payload}=bundle;
  requireValue(payload.format===WORKFLOW_PACKAGE_FORMAT && payload.format_version===WORKFLOW_PACKAGE_VERSION,'WORKFLOW_PACKAGE_VERSION','Unsupported Workflow package format');
  requireValue(payload.compatibility?.plugin==='codex-agents-workflow' && payload.compatibility.package_api===WORKFLOW_PACKAGE_API && payload.compatibility.workflow_schema===1,'WORKFLOW_PACKAGE_COMPATIBILITY','Workflow package is incompatible with this plugin');
  requireValue(/^[a-f0-9]{64}$/.test(package_sha256) && digest(canonicalJSON(payload))===package_sha256,'WORKFLOW_PACKAGE_INTEGRITY','Workflow package digest differs');
  requireValue(payload.package?.id===payload.snapshot?.workflow?.id && /^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/.test(payload.package?.version ?? ''),'WORKFLOW_PACKAGE_IDENTITY','Workflow package identity is invalid');
  const resources=Object.create(null);
  requireValue(Array.isArray(payload.objects),'WORKFLOW_PACKAGE_OBJECTS','Workflow package objects are missing');
  for(const item of payload.objects){
    requireValue(item && typeof item.path==='string' && typeof item.content_base64==='string' && /^[a-f0-9]{64}$/.test(item.sha256) && Number.isSafeInteger(item.bytes),'WORKFLOW_PACKAGE_OBJECTS','Workflow package object metadata is invalid');
    const bytes=Buffer.from(item.content_base64,'base64');
    requireValue(bytes.length===item.bytes && digest(bytes)===item.sha256 && !Object.hasOwn(resources,item.path),'WORKFLOW_PACKAGE_OBJECTS','Workflow package object identity differs');
    resources[item.path]=bytes;
  }
  const prepared=prepareResources(resources);
  requireValue(canonicalJSON(prepared.manifest)===canonicalJSON(payload.snapshot.resources),'WORKFLOW_PACKAGE_MANIFEST','Workflow package manifest differs from its objects');
  requirePublicPackageResources(resources);
  const snapshot={workflow:payload.snapshot.workflow,resources:payload.snapshot.resources,provenance:payload.snapshot.provenance,import_report:payload.snapshot.import_report};
  const expectedDependencies={providers:[...(snapshot.workflow.requirements?.providers ?? [])].sort(),tools:[...(snapshot.workflow.requirements?.tools ?? [])].sort(),mcp_servers:[...(snapshot.workflow.requirements?.mcp_servers ?? [])].sort(),executables:normalizeExecutableRequirements(snapshot.workflow.requirements?.executables ?? [])};
  requireValue(canonicalJSON(payload.dependencies)===canonicalJSON(expectedDependencies),
    'WORKFLOW_PACKAGE_DEPENDENCIES','Workflow package dependency manifest differs from its Workflow');
  requireValue(revisionHash(snapshot)===payload.snapshot.revision_hash,'WORKFLOW_PACKAGE_REVISION','Workflow package revision identity differs');
  requireWorkflowSnapshotIntegrity(snapshot);
  return {package:structuredClone(payload.package),snapshot:structuredClone(payload.snapshot),resources,package_sha256};
}

export async function installWorkflowPackage(store,bundle,{source=null}={}){
  const checked=validateWorkflowPackage(bundle);
  return store.install(checked.snapshot,{resources:checked.resources,installation:{source,package_version:checked.package.version,
    package_sha256:checked.package_sha256,installed_at:new Date().toISOString()}});
}
