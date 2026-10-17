import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join, resolve } from 'node:path';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import {
  conversionResourceHash,
  conversionWorkflowHash,
  certificateForPublishedWorkflow,
  createConversionCertificate,
  requireCurrentConversionCertificate,
} from '../lib/skill-import/conversion-certificate.mjs';
import { CONVERSION_CONTRACT } from '../lib/skill-import/conversion-contract.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';

const TOOL_ID = 'fixture_host_tool';
const TOOL_NAME = 'fixture-host-tool';
const TOOL_VERSION = '1.0';
const OLD_SHA = digest('historical host implementation');
const CURRENT_SHA = digest('qualified current host implementation');
const SOURCE_REVISION = 'a'.repeat(64);
const SOURCE_HASH = digest('historical source content');
const PROPOSAL_HASH = 'b'.repeat(64);
const OUTPUT = { type: 'object', properties: { result: { type: 'string' } }, required: ['result'], additionalProperties: false };

function hostIdentity(sha256 = OLD_SHA, name = TOOL_NAME, version = TOOL_VERSION) {
  return { name, version, sha256 };
}

function registeredBroker(identity, { qualified = true } = {}) {
  const broker_id = 'legacy-certificate-fixture-broker';
  return {
    identity: structuredClone(identity),
    attestation: {
      qualified,
      cancellable: true,
      effect_observation: true,
      tool_identity: structuredClone(identity),
      broker_id,
      evidence_sha256: digest(canonicalJSON({ broker_id, identity, fixture: true })),
    },
    async execute() { return { exit_code: 0, output: {}, diagnostic: '', effects: { observed: true, changed_paths: [], outside_paths: [], artifacts: [] } }; },
    async cancel() { return { termination_confirmed: true, evidence: [{ kind: 'fixture-stop', sha256: digest('fixture-stop') }], effects: { observed: true, changed_paths: [], outside_paths: [], artifacts: [] } }; },
  };
}

function hostContract(identity = hostIdentity()) {
  return {
    id: TOOL_ID,
    identity: structuredClone(identity),
    argv: ['fixture-tool'],
    input_schema: { type: 'object', additionalProperties: false, properties: {} },
    output_schema: { type: 'object', additionalProperties: false, properties: {} },
    env_allow: [],
    permissions: { network: false, read_paths: [], write_paths: [] },
    output_cap_bytes: 4096,
    deadline_ms: 1000,
    idempotency: { mode: 'safe' },
  };
}

function convertedWorkflow(id, identity = hostIdentity(), status = 'ready') {
  return {
    ...createDraft(id, 'Legacy certificate fixture'),
    status,
    skill_policy: { mode: 'cooperative', implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] },
    requirements: { providers: [], tools: [TOOL_ID], mcp_servers: [], executables: [] },
    host_tools: [hostContract(identity)],
    inputs_schema: { type: 'object', properties: { task: { type: 'string' } }, required: ['task'], additionalProperties: false },
    import_status: {
      mode: 'ai_expanded', source_hash: SOURCE_HASH, source_independent: true, unresolved: [],
      conversion_level: 'fully_compiled', conversion_contract_version: 3, requirement_coverage: [], source_dispositions: [],
    },
    finalization: { required: true, node_id: 'final' },
    nodes: [
      { id: 'start', type: 'start' },
      { id: 'work', type: 'agent', executor: { kind: 'main' }, role: 'implementer', access: 'read_only', approval: { required: false },
        retry: { max_attempts: 1 }, input_bindings: { task: '/inputs/task' }, prompt_template: 'Perform the certified task.', outputs_schema: OUTPUT },
      { id: 'final', type: 'agent', executor: { kind: 'main' }, role: 'finalizer', access: 'read_only', approval: { required: false },
        retry: { max_attempts: 1 }, input_bindings: { result: '/nodes/work/output/result' }, prompt_template: 'Accept the result.', outputs_schema: OUTPUT },
      { id: 'end', type: 'end' },
    ],
    edges: [
      { id: 'start-work', source: 'start', target: 'work' },
      { id: 'work-final', source: 'work', target: 'final' },
      { id: 'final-end', source: 'final', target: 'end' },
    ],
  };
}

function conversionIdentity(review_contract_version = 12) {
  return { source_revision: SOURCE_REVISION, source_hash: SOURCE_HASH, proposal_hash: PROPOSAL_HASH, review_contract_version };
}

function historicalCertificate(workflow, resources = [], review_contract_version = 12) {
  return {
    version: 2,
    review_contract_version,
    source_revision: SOURCE_REVISION,
    source_hash: SOURCE_HASH,
    proposal_hash: PROPOSAL_HASH,
    workflow_hash: conversionWorkflowHash(workflow),
    resources_hash: conversionResourceHash(resources),
  };
}

function convertedReport(workflow, resources = [], review_contract_version = 12) {
  const identity = conversionIdentity(review_contract_version);
  return {
    mode: 'converted',
    expansion: {
      ...identity, status: 'draft', conversion_level: 'fully_compiled', requirement_coverage: [], source_dispositions: [],
      inferred_nodes: 2, inferred_edges: 3, certificate: historicalCertificate(workflow, resources, review_contract_version),
    },
  };
}

function conversionProvenance(review_contract_version = 12, publication = null) {
  return {
    kind: 'workflow_conversion', compiler_version: 5, source_kind: 'skill', source_hash: SOURCE_HASH,
    conversion: { source_revision: SOURCE_REVISION, proposal_hash: PROPOSAL_HASH, review_contract_version },
    ...(publication ? { publication } : {}),
  };
}

async function fixture(t, { registryIdentity = hostIdentity(CURRENT_SHA), qualified = true } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'legacy-conversion-certificate-'));
  const workspace = join(root, 'workspace'); await mkdir(workspace);
  const configPath = join(root, 'control-plane.json');
  const service = new WorkflowService({
    configPath,
    defaultConfigPath: DEFAULT_CONFIG_PATH,
    env: {},
    capabilities: { hostToolRegistry: { [TOOL_ID]: registeredBroker(registryIdentity, { qualified }) } },
  });
  await service.call('migrate_v6', {}, { human: true });
  const { store } = await service.open();
  t.after(async () => {
    await Promise.allSettled([...service.attemptAdmission.drainJobs.values()]);
    assert(resolve(root).startsWith(resolve(tmpdir())));
    await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 });
  });
  return { root, workspace, configPath, service, store };
}

async function seedReadyLegacy(f, id, { certificate, provenance, report, workflow } = {}) {
  const resources = {};
  const draftWorkflow = workflow ?? convertedWorkflow(id, hostIdentity(OLD_SHA), 'draft');
  const import_report = report ?? convertedReport(draftWorkflow, [], 12);
  if (certificate) import_report.expansion.certificate = certificate;
  const created = await f.store.create(draftWorkflow, {
    resources,
    provenance: provenance ?? conversionProvenance(import_report.expansion.certificate.review_contract_version),
    import_report,
  });
  const ready = { ...created.workflow, status: 'ready' };
  const readyProvenance = {
    ...created.provenance,
    publication: { actor: 'user', reviewed_revision: created.revision_hash, at: '2026-09-01T00:00:00.000Z' },
  };
  const pack = await f.store.save(id, ready, { expected_revision: created.revision_hash, provenance: readyProvenance });
  return pack;
}

async function saveBindingRenewalDraft(f, baseline, mutate = workflow => {
  workflow.host_tools[0].identity.sha256 = CURRENT_SHA;
}) {
  const workflow = structuredClone(baseline.workflow);
  workflow.status = 'draft';
  mutate(workflow);
  return f.store.save(workflow.id, workflow, { expected_revision: baseline.revision_hash });
}

test('successive direct v12 publications retain historical conversion identity and pin edited content', async t => {
  const f = await fixture(t);
  const baseline = await seedReadyLegacy(f, 'legacy-certificate-success');
  const baselineCertificate = baseline.import_report.expansion.certificate;
  assert.equal(baseline.workflow.status, 'ready');
  assert.doesNotThrow(() => requireCurrentConversionCertificate(baseline.workflow, baseline.resources, baseline.import_report));
  assert.throws(() => createConversionCertificate(baseline.workflow, baseline.resources, conversionIdentity(12)), { code: 'CONVERSION_REVIEW_CONTRACT_STALE' });

  const draft = await saveBindingRenewalDraft(f, baseline);
  const published = await f.service.call('publish', {
    workflow_id: baseline.workflow.id, expected_revision: draft.revision_hash,
  });

  const renewed = published.import_report.expansion.certificate;
  assert.equal(published.workflow.status, 'ready');
  assert.equal(renewed.review_contract_version, 12, 'publication does not claim v13 AI review');
  assert.deepEqual(renewed, { ...baselineCertificate, workflow_hash: conversionWorkflowHash(published.workflow) });
  assert.equal(renewed.resources_hash, conversionResourceHash(published.resources));
  assert.equal(Object.hasOwn(published.import_report.expansion,'host_binding_renewal'),false);
  assert.deepEqual({...published.provenance.publication,at:null},{kind:'direct_editor_publication',actor:'workflow_controller',
    draft_revision:draft.revision_hash,workflow_hash:conversionWorkflowHash(published.workflow),
    resources_hash:conversionResourceHash(published.resources),at:null});

  const retained = await f.store.snapshot(baseline.workflow.id, baseline.revision_hash);
  assert.equal(retained.workflow.status, 'ready');
  assert.equal(retained.workflow.host_tools[0].identity.sha256, OLD_SHA);
  assert.deepEqual(retained.import_report.expansion.certificate, baselineCertificate);
  assert.notEqual(published.revision_hash, baseline.revision_hash);
  assert.doesNotThrow(() => requireCurrentConversionCertificate(published.workflow, published.resources, published.import_report));

  const secondSha = digest('second qualified host implementation');
  f.service.capabilities.hostToolRegistry[TOOL_ID] = registeredBroker(hostIdentity(secondSha));
  const secondDraft = await saveBindingRenewalDraft(f, published, workflow => { workflow.host_tools[0].identity.sha256 = secondSha; });
  const secondPublished = await f.service.call('publish', {
    workflow_id: baseline.workflow.id, expected_revision: secondDraft.revision_hash,
  });
  assert.equal(secondPublished.import_report.expansion.certificate.review_contract_version, 12);
  assert.equal(secondPublished.provenance.publication.draft_revision,secondDraft.revision_hash);
  assert.equal(Object.hasOwn(secondPublished.provenance,'host_binding_renewal'),false);
  assert.equal((await f.store.snapshot(baseline.workflow.id, published.revision_hash)).revision_hash, published.revision_hash);
  assert.deepEqual((await f.store.snapshot(baseline.workflow.id, published.revision_hash)).import_report.expansion.certificate, published.import_report.expansion.certificate);
  assert.equal((await f.store.snapshot(baseline.workflow.id, baseline.revision_hash)).revision_hash, baseline.revision_hash);
  assert.deepEqual((await f.store.snapshot(baseline.workflow.id, baseline.revision_hash)).import_report.expansion.certificate, baselineCertificate);

  const read = await f.service.call('read', { workflow_id: secondPublished.workflow.id, revision_hash: secondPublished.revision_hash });
  assert.equal(read.validation.valid, true, JSON.stringify(read.validation.errors));
  const run = await f.service.call('start', {
    workflow_id: secondPublished.workflow.id, revision_hash: secondPublished.revision_hash, workspace: f.workspace,
    access: 'read_only', main_actor: 'fixture-controller', inputs: { task: 'Check legacy renewal launch binding' },
  }, { human: true });
  assert.equal(run.workflow_revision, secondPublished.revision_hash);
  assert.equal(run.status, 'running');
});

test('current v13 direct edit keeps its pinned conversion review version', async t => {
  const f = await fixture(t);
  const workflow = convertedWorkflow('current-certificate-review', hostIdentity(CURRENT_SHA), 'ready');
  const resources = {};
  const identity = conversionIdentity(CONVERSION_CONTRACT.version);
  const certificate = createConversionCertificate(workflow, resources, identity);
  const report = convertedReport(workflow, [], CONVERSION_CONTRACT.version);
  report.expansion.certificate = certificate;
  const created = await f.store.create({ ...workflow, status: 'draft' }, { resources, provenance: conversionProvenance(CONVERSION_CONTRACT.version), import_report: report });
  const baseline = await f.store.save(workflow.id, { ...created.workflow, status: 'ready' }, {
    expected_revision: created.revision_hash,
    provenance: conversionProvenance(CONVERSION_CONTRACT.version, { actor: 'user', reviewed_revision: created.revision_hash, at: '2026-09-01T00:00:00.000Z' }),
  });
  const draft = await f.store.save(workflow.id, { ...baseline.workflow, status: 'draft', nodes: baseline.workflow.nodes.map(node => node.id === 'work' ? { ...node, prompt_template: 'Reviewed prompt at contract v13.' } : node) }, { expected_revision: baseline.revision_hash });

  const published = await f.service.call('publish', { workflow_id: workflow.id, expected_revision: draft.revision_hash, reviewed: true }, { human: true });
  assert.equal(published.import_report.expansion.certificate.review_contract_version, CONVERSION_CONTRACT.version);
  assert.equal(published.import_report.expansion.certificate.workflow_hash, conversionWorkflowHash(published.workflow));
  assert.equal(Object.hasOwn(published.import_report.expansion, 'host_binding_renewal'), false);
  assert.equal(Object.hasOwn(published.provenance, 'host_binding_renewal'), false);
});

test('certificate validation rejects corrupted v12 evidence, mismatched source/proposal/resources, and unsupported versions', async t => {
  const workflow = convertedWorkflow('legacy-certificate-integrity', hostIdentity(OLD_SHA), 'ready');
  const resources = {};
  const report = convertedReport(workflow, resources, 12);
  assert.doesNotThrow(() => requireCurrentConversionCertificate(workflow, resources, report));

  const corrupted = structuredClone(report);
  corrupted.expansion.certificate.workflow_hash = 'd'.repeat(64);
  assert.throws(() => requireCurrentConversionCertificate(workflow, resources, corrupted), { code: 'CONVERSION_CERTIFICATE_STALE' });

  for (const field of ['source_revision', 'proposal_hash', 'source_hash']) {
    const mismatched = structuredClone(report);
    mismatched.expansion[field] = digest(`mismatched ${field}`);
    assert.throws(() => requireCurrentConversionCertificate(workflow, resources, mismatched), { code: 'CONVERSION_CERTIFICATE_STALE' }, field);
  }
  for (const field of ['source_revision', 'proposal_hash']) for (const observed of [null, 'malformed-hash']) {
    const malformed = structuredClone(report);
    malformed.expansion[field] = observed;
    malformed.expansion.certificate[field] = observed;
    assert.throws(() => requireCurrentConversionCertificate(workflow, resources, malformed), error => {
      assert.equal(error.code, 'CONVERSION_CERTIFICATE_STALE');
      assert(error.differences?.some(item => item.field === `import_report.expansion.certificate.${field}`
        && item.expected === '64 lowercase hexadecimal characters' && item.observed === observed));
      return true;
    }, `${field} must be a 64-character lowercase hash even when report and certificate match`);
  }
  assert.throws(() => requireCurrentConversionCertificate(workflow, { 'workflow-assets/changed.txt': Buffer.from('changed') }, report), { code: 'CONVERSION_CERTIFICATE_STALE' });

  for (const version of [11, CONVERSION_CONTRACT.version + 1]) {
    const unsupported = convertedReport(workflow, resources, version);
    assert.throws(() => requireCurrentConversionCertificate(workflow, resources, unsupported), { code: 'CONVERSION_REVIEW_CONTRACT_UNSUPPORTED' }, `review contract ${version}`);
  }

  const f = await fixture(t);
  const baseline = await seedReadyLegacy(f, 'legacy-metadata-diagnostics');
  const draft = await saveBindingRenewalDraft(f, baseline);
  const provenanceTamper = structuredClone(draft);
  provenanceTamper.provenance.conversion.source_revision = 'e'.repeat(64);
  assert.throws(() => certificateForPublishedWorkflow(provenanceTamper), error => {
    assert.equal(error.code, 'CONVERSION_IDENTITY_REQUIRED');
    assert(error.differences?.some(item => item.field === 'provenance.conversion.source_revision'));
    return true;
  });
  const futureContractTamper = structuredClone(draft);
  futureContractTamper.import_report.expansion.certificate.review_contract_version = CONVERSION_CONTRACT.version + 1;
  assert.throws(() => certificateForPublishedWorkflow(futureContractTamper), { code: 'CONVERSION_REVIEW_CONTRACT_UNSUPPORTED' });
  const semanticTamper = structuredClone(draft);
  semanticTamper.workflow.nodes.find(node => node.id === 'work').prompt_template = 'Published editor prompt.';
  const republishedReport=certificateForPublishedWorkflow(semanticTamper);
  assert.equal(republishedReport.expansion.certificate.review_contract_version,12);
  assert.equal(republishedReport.expansion.certificate.workflow_hash,conversionWorkflowHash(semanticTamper.workflow));
});

test('edited v12 semantic and resource content publishes directly and pins a model-free start',async t=>{
  const f=await fixture(t);
  const baseline=await seedReadyLegacy(f,'legacy-direct-semantic');
  const draft=await saveBindingRenewalDraft(f,baseline,workflow=>{
    workflow.host_tools[0].identity.sha256=CURRENT_SHA;
    workflow.nodes.find(node=>node.id==='work').prompt_template='Process the edited task.';
    workflow.host_tools[0].argv.push('--edited');
  });
  const resourceEdit=await f.service.call('write_resource',{workflow_id:baseline.workflow.id,expected_revision:draft.revision_hash,
    resource_path:'workflow-assets/edited.txt',text:'Edited resource'});
  const published=await f.service.call('publish',{workflow_id:baseline.workflow.id,expected_revision:resourceEdit.revision_hash});
  assert.equal(published.workflow.status,'ready');
  assert.equal(published.workflow.nodes.find(node=>node.id==='work').prompt_template,'Process the edited task.');
  assert.equal(published.import_report.expansion.certificate.review_contract_version,12);
  assert.equal(published.import_report.expansion.certificate.workflow_hash,conversionWorkflowHash(published.workflow));
  assert.equal(published.import_report.expansion.certificate.resources_hash,conversionResourceHash(published.resources));
  assert.equal(published.provenance.publication.draft_revision,resourceEdit.revision_hash);
  assert.equal(published.provenance.publication.kind,'direct_editor_publication');
  assert.equal(Object.hasOwn(published.import_report.expansion,'host_binding_renewal'),false);
  const run=await f.service.call('start',{workflow_id:baseline.workflow.id,revision_hash:published.revision_hash,
    workspace:f.workspace,access:'read_only',main_actor:'fixture-controller',inputs:{task:'Pinned edited task'}},{human:true});
  assert.equal(run.workflow_revision,published.revision_hash);
  assert.equal(run.status,'running');
  await assert.rejects(f.service.call('publish',{workflow_id:baseline.workflow.id,expected_revision:resourceEdit.revision_hash}),
    {code:'REVISION_CONFLICT'});
});

test('v12 edited Draft needs no prior Ready baseline',async t=>{
  const f=await fixture(t);
  const draftWorkflow=convertedWorkflow('legacy-no-ready-baseline',hostIdentity(CURRENT_SHA),'draft');
  const draft=await f.store.create(draftWorkflow,{resources:{},provenance:conversionProvenance(12),
    import_report:convertedReport(draftWorkflow,{},12)});
  const changed=await f.store.save(draft.workflow.id,{...draft.workflow,
    nodes:draft.workflow.nodes.map(node=>node.id==='work'?{...node,prompt_template:'Edited before first Ready'}:node)},
    {expected_revision:draft.revision_hash});
  const published=await f.service.call('publish',{workflow_id:draft.workflow.id,expected_revision:changed.revision_hash});
  assert.equal(published.workflow.status,'ready');
  assert.equal(published.provenance.publication.draft_revision,changed.revision_hash);
});

test('direct publication still rejects invalid executable bindings and graphs',async t=>{

  await t.test('registered implementation is not qualified', async subtest => {
    const f = await fixture(subtest, { qualified: false });
    const baseline = await seedReadyLegacy(f, 'legacy-unqualified');
    const draft = await saveBindingRenewalDraft(f, baseline);
    await assert.rejects(f.service.call('publish', { workflow_id: baseline.workflow.id, expected_revision: draft.revision_hash }), error => {
      assert.equal(error.code, 'WORKFLOW_NOT_READY');
      assert(error.validation?.errors?.some(issue => issue.code === 'HOST_TOOL_BROKER_UNQUALIFIED' || issue.code === 'HOST_TOOL_BINDING_STALE'));
      return true;
    });
    assert.equal((await f.store.snapshot(baseline.workflow.id)).workflow.status, 'draft');
  });

  await t.test('invalid graph is rejected before publication',async subtest=>{
    const f=await fixture(subtest);
    const baseline=await seedReadyLegacy(f,'legacy-invalid-graph');
    const draft=await saveBindingRenewalDraft(f,baseline,workflow=>{
      workflow.host_tools[0].identity.sha256=CURRENT_SHA;
      workflow.edges=workflow.edges.filter(edge=>edge.id!=='work-final');
    });
    await assert.rejects(f.service.call('publish',{workflow_id:baseline.workflow.id,expected_revision:draft.revision_hash}),
      {code:'WORKFLOW_NOT_READY'});
  });

  await t.test('missing Workflow resource is rejected before publication',async subtest=>{
    const f=await fixture(subtest);
    const baseline=await seedReadyLegacy(f,'legacy-missing-resource');
    const draft=await saveBindingRenewalDraft(f,baseline,workflow=>{
      workflow.host_tools[0].identity.sha256=CURRENT_SHA;
      workflow.nodes.find(node=>node.id==='work').resources=['workflow-assets/missing.txt'];
    });
    await assert.rejects(f.service.call('publish',{workflow_id:baseline.workflow.id,expected_revision:draft.revision_hash}),
      error=>['WORKFLOW_NOT_READY','WORKFLOW_RESOURCE_MISSING'].includes(error.code));
  });

  for (const [field, value] of [['name', 'renamed-host-tool'], ['version', '2.0']]) await t.test(`registered ${field} edit remains executable`, async subtest => {
    const registryIdentity = hostIdentity(CURRENT_SHA, field === 'name' ? value : TOOL_NAME, field === 'version' ? value : TOOL_VERSION);
    const f = await fixture(subtest, { registryIdentity });
    const baseline = await seedReadyLegacy(f, `legacy-${field}-change`);
    const draft = await saveBindingRenewalDraft(f, baseline, workflow => { workflow.host_tools[0].identity = structuredClone(registryIdentity); });
    const published=await f.service.call('publish',{workflow_id:baseline.workflow.id,expected_revision:draft.revision_hash});
    assert.equal(published.workflow.status,'ready');
    assert.equal(published.workflow.host_tools[0].identity[field],value);
  });
});
