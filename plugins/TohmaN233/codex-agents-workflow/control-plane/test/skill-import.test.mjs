import test from 'node:test';
import assert from 'node:assert/strict';
import { randomBytes } from 'node:crypto';
import { mkdtemp, mkdir, writeFile, readFile, rm, symlink } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join } from 'node:path';
import { readSkillSnapshot, parseSkill, redactKnownCredentials } from '../lib/skill-import/skill-reader.mjs';
import { compileCoarseSkill, importCoarseSkill, verifyCoarseRelocation } from '../lib/skill-import/coarse-compiler.mjs';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { validateWorkflowGraph } from '../lib/workflow-validator.mjs';
import { digest, canonicalJSON, prepareResources } from '../lib/workflow-revisions.mjs';
import { SkillInventory } from '../lib/skill-import/inventory.mjs';
import { expansionPacket, applyExpansion, compileExpansion, compileRequirementCoverage, EXPANSION_CONTRACT } from '../lib/skill-import/semantic-expander.mjs';
import { importReviewPacket, reviewImportedDraft } from '../lib/skill-import/review-import.mjs';
import { discoverCodexSkills } from '../lib/skill-import/codex-inventory.mjs';
import { discoverFolderSkills } from '../lib/skill-import/folder-inventory.mjs';
import { defaultRoutingRules } from '../lib/skill-import/routing-rules.mjs';
import { AUTHORING_RUNTIME_ENVELOPE_SCHEMA, decodeGeneratedProposal, decodeGeneratedProposalDetailed, EXPANSION_PROPOSAL_SCHEMA, expansionRunPack } from '../lib/skill-import/expansion-run.mjs';
import { managedNativeResultSchema } from '../lib/execution/host-main-automation.mjs';
import { analyzeSkillDependencies } from '../lib/skill-import/dependency-reader.mjs';
import { HostToolRunner } from '../lib/execution/host-tool-runner.mjs';
import { evaluateReview, REVIEW_IDS } from '../lib/skill-import/review-checklist.mjs';
import { skillSourceStatus } from '../lib/skill-import/source-status.mjs';
import { observedSourceRequirements, projectObservedRequirements } from '../lib/skill-import/source-requirements.mjs';
import { validateData } from '../lib/workflow-data-schema.mjs';
import { sourceSectionInventory, validateSourceDispositions } from '../lib/skill-import/source-dispositions.mjs';
import { CONVERSION_CONTRACT } from '../lib/skill-import/conversion-contract.mjs';
import { compileDeployableConversion, requireDeployableConvertedSnapshot } from '../lib/skill-import/conversion-deployment.mjs';
import { AUTHORING_NODE_PROMPT_MAX_LENGTH } from '../lib/authoring/blueprint-contract.mjs';
import { createConversionCertificate, requireCurrentConversionCertificate } from '../lib/skill-import/conversion-certificate.mjs';
import { exclusiveConditionFanIn } from '../lib/skill-import/fan-in-topology.mjs';
import { dependencyExecutables } from '../lib/skill-import/source-contracts.mjs';
import { resolveBindings } from '../lib/workflow-bindings.mjs';

const roleProfiles=[
  {id:'builtin-role-bounded-code-change',revision_hash:'1'.repeat(64),role:'implementer',access:'bounded_write',instructions:'Implement the bounded task.'},
  {id:'builtin-role-judgment-heavy-change',revision_hash:'2'.repeat(64),role:'implementer',access:'bounded_write',instructions:'Implement the complex task.'},
  {id:'builtin-role-cross-review',revision_hash:'3'.repeat(64),role:'reviewer',access:'read_only',instructions:'Review independently.'},
  {id:'builtin-role-repository-analysis',revision_hash:'4'.repeat(64),role:'implementer',access:'read_only',instructions:'Analyze the repository.'},
  {id:'builtin-role-review-and-repair',revision_hash:'5'.repeat(64),role:'reviewer',access:'bounded_write',instructions:'Review and repair bounded defects.'},
];

test('source requirement projection preserves explicit field and zero-input contracts on repeated calls', () => {
  const resources={'source/SKILL.md':Buffer.from('# Workflow\nProduce a summary and consume that summary.')};
  const proposal={source_requirements:[],requirement_mappings:[],nodes:[
    {id:'producer',type:'agent',input_bindings:{},resource_refs:[],outputs_schema:{type:'object',properties:{summary:{type:'string'},evidence:{type:'string'}},required:['summary','evidence']}},
    {id:'consumer',type:'agent',input_bindings:{summary:'/nodes/producer/output/summary'},resource_refs:[]},
  ],edges:[{source:'producer',target:'consumer'}]};
  const once=projectObservedRequirements(proposal,resources),twice=projectObservedRequirements(once,resources);
  assert.deepEqual(once.nodes[0].input_bindings,{});
  assert.deepEqual(once.nodes[1].input_bindings,proposal.nodes[1].input_bindings);
  assert.deepEqual(twice,once);
  const input=resolveBindings(twice.nodes[1].input_bindings,{inputs:{task:'user task'},nodes:{producer:{output:{summary:'tiny summary',evidence:'X'.repeat(100000)}}}});
  assert.equal(Buffer.byteLength(JSON.stringify(input)),26);
  assert.throws(()=>resolveBindings(twice.nodes[1].input_bindings,{nodes:{producer:{output:{evidence:'present'}}}}),{code:'BINDING_MISSING'});
  const legacy=structuredClone(proposal);delete legacy.nodes[1].input_bindings;
  assert.deepEqual(projectObservedRequirements(legacy,resources).nodes[1].input_bindings,{task:'/inputs/task',upstream_producer:'/nodes/producer/output'});
});

test('compiled agent prompt rejects overflow after Host-required artifact paths are appended', async t => {
  const f=await fixture(t,'Write results/final_report.md with the result.');
  const provider={id:'chosen',enabled:true,capabilities:{read:true,write:true}};
  const pack=await importCoarseSkill(f.store,f.source,{id:'prompt-limit',providerId:provider.id});
  const resources=await f.store.resources('prompt-limit');
  const artifact=observedSourceRequirements(resources).find(item=>item.requirement_kind==='artifact_path');
  assert.equal(artifact?.details?.artifact_path,'results/final_report.md');
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:9,end_line:9}};
  const prompt='X'.repeat(AUTHORING_NODE_PROMPT_MAX_LENGTH-20);
  const proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[{requirement_id:artifact.requirement_id,node_ids:['work'],binding_names:[],runtime_guards:[],resource_refs:[...artifact.resource_refs],status:'agent_assisted',rationale:'Writing the exact source artifact is this activity responsibility.'}],nodes:[{id:'work',type:'agent',prompt_template:prompt,operation_mode:'write',...origin}],edges:[{id:'start-work',source:'start',target:'work',...origin},{id:'work-final',source:'work',target:'final',...origin}]};
  assert.throws(()=>compileExpansion(pack,resources,proposal,{providers:[provider]}),error=>error.code==='AUTHORING_PROMPT_LIMIT'&&error.activity_key==='work'&&error.prompt_chars>AUTHORING_NODE_PROMPT_MAX_LENGTH);
});

test('parallel aggregates consume declared fields from every concrete branch and may use a registered tool', async t => {
  const f=await fixture(t,'Run both independent checks and combine their summaries.');
  const provider={id:'chosen',enabled:true,capabilities:{read:true}};
  const pack=await importCoarseSkill(f.store,f.source,{id:'field-aggregate',providerId:provider.id});
  const resources=await f.store.resources('field-aggregate');
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:9,end_line:9}};
  const output={type:'object',properties:{summary:{type:'string'},evidence:{type:'string'}},required:['summary','evidence']};
  const bindings={left_summary:'/nodes/left/output/summary',right_summary:'/nodes/right/output/summary'};
  const contract={id:'combine_summaries',identity:{name:'combine_summaries',version:'1',sha256:'a'.repeat(64)},argv:['combine_summaries'],input_schema:{type:'object',additionalProperties:false,properties:{left_summary:{type:'string'},right_summary:{type:'string'}},required:['left_summary','right_summary']},output_schema:{type:'object',properties:{summary:{type:'string'}},required:['summary']},env_allow:[],permissions:{network:false,read_paths:[],write_paths:[]},output_cap_bytes:4096,deadline_ms:1000,idempotency:{mode:'safe'}};
  const proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],nodes:[
    {id:'fork',type:'parallel',join_id:'joined',failure_policy:'fail_fast',...origin},
    ...['left','right'].map(id=>({id,type:'agent',prompt_template:'Return the check summary and evidence.',input_bindings:{},outputs_schema:output,...origin})),
    {id:'joined',type:'join',parallel_id:'fork',...origin},
    {id:'aggregate',type:'agent',prompt_template:'Combine the two summaries.',input_bindings:bindings,outputs_schema:contract.output_schema,...origin},
  ],edges:[['a','start','fork'],['b','fork','left','left'],['c','fork','right','right'],['d','left','joined'],['e','right','joined'],['f','joined','aggregate'],['g','aggregate','final']].map(([id,source,target,label])=>({id,source,target,...(label?{label}:{}),...origin}))};
  const context={providers:[provider],host_tools:[contract.id],host_tool_contracts:[contract]};
  for(const type of ['agent','tool']) {
    const candidate=structuredClone(proposal);
    if(type==='tool')candidate.nodes[4]={id:'aggregate',type,tool:contract.id,input_bindings:bindings,...origin};
    const compiled=compileExpansion(pack,resources,candidate,context);
    assert.deepEqual(compiled.workflow.nodes.find(node=>node.id==='aggregate').input_bindings,bindings);
    assert.deepEqual(compiled.workflow.nodes.find(node=>node.id==='left').input_bindings,{});
    assert.equal(compiled.workflow.nodes.find(node=>node.id==='left').retry.max_attempts,3);
    const explicitRetry=structuredClone(candidate);explicitRetry.nodes.find(node=>node.id==='left').retry_max_attempts=1;
    assert.equal(compileExpansion(pack,resources,explicitRetry,context).workflow.nodes.find(node=>node.id==='left').retry.max_attempts,1);
    assert.deepEqual(compiled.workflow.nodes.find(node=>node.id==='final').input_bindings,{task:'/inputs/task',upstream_result:'/nodes/aggregate/output'});
    assert.deepEqual(compileExpansion(pack,resources,compiled.canonical_proposal,context).canonical_proposal,compiled.canonical_proposal);
  }
  for(const input_bindings of [{left_summary:bindings.left_summary},{selected:{coalesce:Object.values(bindings)}}]) {
    const omitted=structuredClone(proposal);omitted.nodes[4].input_bindings=input_bindings;
    assert.throws(()=>compileExpansion(pack,resources,omitted,context),{code:'EXPANSION_AGGREGATE_BINDING'});
  }
});

test('dependency scanning distinguishes shell-local colors from external environment reads', () => {
  const snapshot={root:'/synthetic/source',metadata:{},problems:[],inventory:[],files:{
    'source/setup.sh':Buffer.from('N="reset"; G="green"\necho "${G}+${N} ${REMOTE_TOKEN}"'),
    'source/template.js':Buffer.from('const text = `${N}`; const key = process.env.API_KEY;'),
  }};
  const analysis=analyzeSkillDependencies(snapshot);
  assert.deepEqual(analysis.requirements.environment,[]);
  assert.deepEqual(analysis.observed_dependencies.filter(item=>item.kind==='environment').map(item=>item.name).sort(),['API_KEY','REMOTE_TOKEN']);
});

test('source dependency parsing ignores program names inside quoted command arguments',()=>{
  assert.deepEqual(dependencyExecutables('python -c "print(\'ffmpeg\')"'),['python']);
  assert.deepEqual(dependencyExecutables('ffmpeg -i input.mp4 output.mp4 | ffprobe output.mp4'),['ffmpeg','ffprobe']);
  const resources={'source/SKILL.md':Buffer.from('# Skill\n\n## Workflow\n\nRun `python -c "print(\'ffmpeg\')"`.')};
  assert.deepEqual(observedSourceRequirements(resources).filter(item=>item.requirement_kind==='dependency').map(item=>item.details.executable),['python']);
});

test('allowed tools and optional script resources remain policy/observations rather than unconditional requirements', () => {
  const snapshot={root:'/synthetic/source',metadata:{'allowed-tools':'Bash(git:*) Read'},problems:[],inventory:[],files:{
    'source/SKILL.md':Buffer.from('Optionally upload with `python scripts/upload.py input.json`.\n'),
    'source/scripts/upload.py':Buffer.from('import os\nkey = os.environ["UPLOAD_TOKEN"]\n'),
  }};
  const analysis=analyzeSkillDependencies(snapshot);
  assert.deepEqual(analysis.requirements.tools,['read_workflow_resource']);
  assert.deepEqual(analysis.requirements.executables,[]);
  assert.deepEqual(analysis.requirements.environment,[]);
  assert.deepEqual(analysis.tool_policy.allowed,['Bash(git:*)','Read']);
  assert(analysis.observed_dependencies.some(item=>item.kind==='executable' && item.name==='python'));
  assert(analysis.observed_dependencies.some(item=>item.kind==='environment' && item.name==='UPLOAD_TOKEN'));
});

test('an explicit missing inline script is unresolved instead of self-contained', () => {
  const analysis=analyzeSkillDependencies({root:'/synthetic/source',metadata:{},problems:[],inventory:[],files:{'source/SKILL.md':Buffer.from('Run `python scripts/missing.py input.json`.\n')}});
  assert(analysis.unresolved.some(item=>item.code==='UNRESOLVED_COMMAND_REFERENCE' && item.target==='scripts/missing.py'));
  assert.notEqual(analysis.classification,'self_contained_candidate');
});

test('contract anchors retain entrypoint artifacts and dependencies without promoting optional references', () => {
  const requirements=observedSourceRequirements({'source/SKILL.md':Buffer.from('Write trend_result.csv and dominant_factor.csv.\nIf rendering is requested, use ffmpeg.\nIf audio is present, use ffprobe.\nUse ffmpeg only when video is requested.\nWhen rendering, use ffprobe.\n'), 'source/reference.md':Buffer.from('Create compressed_video.mp4 and compression_report.json.') , 'source/example.js':Buffer.from('const output = "answer.json"; require("ffmpeg");')});
  assert.deepEqual(requirements.filter(item=>item.requirement_kind==='artifact_path').map(item=>item.details.artifact_path).sort(),['dominant_factor.csv','trend_result.csv']);
  assert(requirements.filter(item=>item.requirement_kind==='dependency').every(item=>item.details.phase==='conditional'));
  assert(!requirements.some(item=>item.source_spans[0].resource==='source/reference.md'));
  assert(!requirements.some(item=>item.source_spans[0].resource==='source/example.js'));
});

test('literal product artifacts exclude project-memory bookkeeping and remain trigger-scoped', () => {
  const resources={'source/SKILL.md':Buffer.from([
    'Update project_memory/progress.md and changelog.md; update decision_log.md when a shared contract moves.',
    'Write final_report.pdf after review; save debug_trace.json if a check fails.',
    'Never write obsolete_report.pdf.',
    'When a preview is requested:',
    '  - Update optional_preview.mp4.',
  ].join('\n'))};
  const paths=observedSourceRequirements(resources).filter(item=>item.requirement_kind==='artifact_path').map(item=>item.details.artifact_path);
  assert.deepEqual(paths,['final_report.pdf']);
});

test('host never projects project-memory bookkeeping as product completion artifacts', () => {
  const source='Update project_memory/progress.md and changelog.md; update decision_log.md when a shared contract moves.\nWrite final_report.pdf.\n';
  const resources={'source/SKILL.md':Buffer.from(source)};
  const span={resource:'source/SKILL.md',start_line:1,end_line:2};
  const node=(id,operation_mode,prompt_template)=>({id,type:'agent',operation_mode,prompt_template,source_spans:[span],input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:[]});
  const proposal={source_requirements:[],requirement_mappings:[],nodes:[
    node('document','write','Update project_memory/progress.md and changelog.md with verification results. Write final_report.pdf.'),
    node('review','read','Review project_memory/progress.md and changelog.md.'),
  ],edges:[]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.deepEqual(projected.requirement_mappings.map(mapping=>mapping.node_ids),[['document']]);
  assert.deepEqual(projected.nodes[0].required_artifacts.map(item=>item.path),['final_report.pdf']);
  assert.deepEqual(projected.nodes[1].required_artifacts,[]);
  assert.equal(projected.source_requirements.some(item=>/project_memory|changelog|decision_log/.test(item.details?.artifact_path??'')),false);
});

test('a basename under an explicit runtime output root is not an exact Host path gate', () => {
  const resources={'source/SKILL.md':Buffer.from('All session outputs go into `<videos_dir>/edit/`.\nProduce takes_packed.md and edl.json.\n')};
  const observed=observedSourceRequirements(resources).filter(item=>item.requirement_kind==='artifact_path');
  assert.deepEqual(observed.map(item=>[item.details.artifact_path,item.trigger]),[['takes_packed.md','runtime_resolved_artifact'],['edl.json','runtime_resolved_artifact']]);
  for(const item of observed)assert.doesNotThrow(()=>validateData(item,EXPANSION_PROPOSAL_SCHEMA.properties.source_requirements.items));
  const proposal={source_requirements:[],requirement_mappings:observed.map(item=>({requirement_id:item.requirement_id,node_ids:['produce'],binding_names:[],runtime_guards:[],resource_refs:['source/SKILL.md'],status:'agent_assisted',rationale:'Writer resolves the runtime output root.'})),nodes:[{id:'produce',type:'agent',operation_mode:'write',prompt_template:'Produce takes_packed.md and edl.json under the supplied edit directory.',source_spans:[{resource:'source/SKILL.md',start_line:2,end_line:2}],input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:[]}],edges:[]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.deepEqual(projected.nodes[0].required_artifacts,[]);
  assert.deepEqual(projected.nodes[0].requirement_ids,observed.map(item=>item.requirement_id));
});

test('explicit readiness in a retained candidate section reaches the Host preparation gate', () => {
  const resources={'source/SKILL.md':Buffer.from([
    '# Example workflow',
    '## Principle',
    'The only things you MUST do are in the Hard Rules section. Everything else is a worked example.',
    '## Hard Rules',
    'Never change source footage.',
    '## Setup',
    'On cold start verify:',
    '- `ffmpeg` + `ffprobe` on PATH.',
    '- Python deps installed.',
    '- Node.js available if animation is requested.',
  ].join('\n'))};
  const setup=sourceSectionInventory(resources).find(section=>section.title==='Setup');
  assert.equal(setup.authority,'reference_candidate');
  const proposal={source_requirements:[],requirement_mappings:[],source_dispositions:[{section_id:setup.section_id,disposition:'workflow',node_ids:['prepare'],requirement_ids:[],rationale:'Retain explicit readiness checks.'}],nodes:[{id:'prepare',type:'agent',operation_mode:'read',source_spans:[setup.source_span],input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:[]}],edges:[]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.deepEqual(projected.required_executables.map(item=>item.name),['ffmpeg','ffprobe','python']);
  assert.deepEqual(projected.source_requirements.filter(item=>item.requirement_kind==='dependency').map(item=>[item.details.executable,item.details.phase]),[['ffmpeg','unconditional'],['ffprobe','unconditional'],['python','unconditional'],['node','conditional']]);
  assert(projected.requirement_mappings.filter(item=>item.requirement_id.startsWith('observed_dependency_')).every(item=>item.node_ids.includes('prepare')));
});

test('Host node evidence includes its mapped source sections and requirement lines', () => {
  const resources={'source/SKILL.md':Buffer.from([
    '# Example',
    '## Implementation',
    'Never use a placeholder token/card or a number as the visible card name.',
    '## Review',
    'Inspect the implementation against every assigned rule.',
  ].join('\n'))};
  const sections=sourceSectionInventory(resources);
  const implementation=sections.find(item=>item.title==='Implementation');
  const review=sections.find(item=>item.title==='Review');
  assert(implementation && review);
  const rule={requirement_id:'rule_exact_source_line',requirement_kind:'method_rule',source_spans:[{resource:'source/SKILL.md',start_line:3,end_line:3}],trigger:'perform the implementation',required_result:'Never use a placeholder card.',resource_refs:['source/SKILL.md'],details:{}};
  const proposal={source_requirements:[rule],requirement_mappings:[{requirement_id:rule.requirement_id,node_ids:['review'],binding_names:[],runtime_guards:[],resource_refs:['source/SKILL.md'],status:'agent_assisted',rationale:'The review checks this exact implementation rule.'}],source_dispositions:[{section_id:implementation.section_id,disposition:'workflow',node_ids:['review'],requirement_ids:[],rationale:'The review verifies the implementation rule.'}],nodes:[{id:'review',type:'agent',operation_mode:'read',source_span:review.source_span,source_spans:[review.source_span],input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:[]}],edges:[]};
  const projected=projectObservedRequirements(proposal,resources);
  const node=projected.nodes[0];
  assert(node.requirement_ids.includes(rule.requirement_id));
  assert(node.source_spans.some(span=>span.resource===implementation.source_span.resource && span.start_line===implementation.source_span.start_line && span.end_line===implementation.source_span.end_line));
  assert(node.source_spans.some(span=>span.resource===rule.source_spans[0].resource && span.start_line===rule.source_spans[0].start_line && span.end_line===rule.source_spans[0].end_line));
  assert.deepEqual(projectObservedRequirements(projected,resources).nodes[0].source_spans,node.source_spans);
});

test('contract anchors recognize executable command lines and CodeGraph as unconditional dependencies', () => {
  const source = [
    'Build a concrete trace with CodeGraph (`codegraph explore` and `codegraph node`).',
    '   python scripts/run_semantic_scenario.py case.json --project-root . --evidence result.json',
    '   python -m pytest tests/test_cards.py -q',
    '   node --check web/app.js',
    '   git diff --check',
  ].join('\n');
  const dependencies = observedSourceRequirements({ 'source/SKILL.md': Buffer.from(source) })
    .filter(item => item.requirement_kind === 'dependency');
  assert.deepEqual([...new Set(dependencies.map(item => item.details.executable))].sort(),
    ['codegraph', 'git', 'node', 'python']);
  assert(dependencies.every(item => item.details.phase === 'unconditional'));
});

test('contract anchors require explicitly referenced pinned guidance at its source trigger', () => {
  const resources={
    'source/SKILL.md':Buffer.from('Read install.md on setup.\nWhen building a diagram, read skills/manim-video/SKILL.md.\n'),
    'source/install.md':Buffer.from('Install instructions.\n'),
    'source/skills/manim-video/SKILL.md':Buffer.from('Diagram instructions.\n'),
  };
  const references=observedSourceRequirements(resources).filter(item=>item.requirement_id.startsWith('observed_reference_'));
  assert.deepEqual(references.map(item=>item.resource_refs[0]).sort(),['source/install.md','source/skills/manim-video/SKILL.md']);
  assert.equal(references.find(item=>item.resource_refs[0].endsWith('manim-video/SKILL.md')).trigger.startsWith('conditional:'),true);
});

test('contract anchors retain exact statistical APIs, formulas, scaling and method preferences from Markdown', () => {
  const source = [
    "## Non-Parametric Method: Sen's Slope with Mann-Kendall Test",
    'Recommended for environmental data.',
    'result = mk.original_test(values)',
    'fa = FactorAnalyzer(n_factors=4, rotation=\'varimax\')',
    'scaler = StandardScaler()',
    'contrib_0 = full_r2 - calc_r2(scores[:, [1, 2, 3]], y)',
    "contributions = {'Heat': contrib_0 * 100}",
    'dominant_pct = round(contributions[dominant])',
    "df['NetRadiation'] = df['Longwave'] + df['Shortwave']",
    "Prefer Sen's slope for environmental time series.",
  ].join('\n');
  const rules = observedSourceRequirements({ 'source/SKILL.md': Buffer.from(source) })
    .filter(item => item.requirement_kind === 'method_rule')
    .map(item => item.details.rule_text);
  for (const expected of ['Mann-Kendall', 'Recommended for environmental data', 'mk.original_test', 'FactorAnalyzer', 'StandardScaler', 'full_r2 - calc_r2', '* 100', 'round(', 'NetRadiation', "Prefer Sen's slope"]) {
    assert(rules.some(rule => rule.includes(expected)), `missing deterministic method anchor: ${expected}`);
  }
});

test('contract anchors distinguish deterministic output canonicalization from semantic work', () => {
  const requirements = observedSourceRequirements({ 'source/SKILL.md': Buffer.from([
    '`time`: ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`).',
    'Round distance_km to 2 decimal places.',
  ].join('\n')) });
  const rules = requirements.filter(item => item.requirement_kind === 'canonicalization');
  assert.equal(rules.length, 2);
  assert(rules.some(item => item.details.rule_text.includes('YYYY-MM-DDTHH:MM:SSZ')));
  assert(rules.some(item => item.details.rule_text.includes('2 decimal places')));
});

test('source anchors preserve absolute artifacts, list continuations, independent input/approval, negative commands and paragraph conditionals', () => {
  const source=[
    '## Hard Rules',
    'Write:',
    '- C:\\deliverables\\final-report.json',
    'Ask the user for a brief and obtain confirmation before rendering.',
    'Never run `python scripts/unsafe.py`.',
    'When statistical analysis is requested:',
    '  This task requires Rscript.',
  ].join('\n');
  const requirements=observedSourceRequirements({'source/SKILL.md':Buffer.from(source)});
  assert.equal(requirements.find(item=>item.requirement_kind==='artifact_path')?.details.artifact_path,'C:\\deliverables\\final-report.json');
  assert(requirements.some(item=>item.requirement_kind==='user_input'));
  assert(requirements.some(item=>item.requirement_kind==='approval'));
  assert.equal(requirements.some(item=>item.requirement_kind==='script_operation'),false);
  const dependency=requirements.find(item=>item.requirement_kind==='dependency');
  assert.equal(dependency.details.executable,'Rscript');assert.equal(dependency.details.phase,'conditional');
});

test('source-section inventory preserves workflow contracts while exposing worked examples for pruning', () => {
  const requiredSections=sourceSectionInventory({'source/SKILL.md':Buffer.from([
    '# Build artifacts','An artifact is done only when source, behavior and checks agree.',
    '## Non-negotiable rules','Never use placeholders. Do not duplicate UI.',
    '## Visibility contract','The controller must see private inputs. Never leak them.',
    '## Implementation loop','1. Read sources.','2. Implement.','3. Verify.',
    '## Review checklist','- Source and behavior agree.',
  ].join('\n'))});
  assert.deepEqual(requiredSections.map(item=>item.authority),['required','required','required','required','required']);

  const exampleHeavy=sourceSectionInventory({'source/SKILL.md':Buffer.from([
    '# Artifact Use','## Principle','Ask → confirm → execute → iterate → persist. The only things you MUST do are in the Hard Rules section below. Everything else is a worked example.',
    '## Hard Rules (production correctness — non-negotiable)','Never corrupt an input boundary.','## The process','1. Inventory.','2. Confirm.','3. Execute.',
    '## Optional styling (when requested)','Example presets: warm_presentation.','## Output format','```json','{"style":"warm"}','```',
    '## Anti-patterns','Never edit before confirming.',
  ].join('\n'))});
  assert.equal(exampleHeavy.find(item=>item.title==='Hard Rules (production correctness — non-negotiable)').authority,'required');
  assert.equal(exampleHeavy.find(item=>item.title==='The process').authority,'required');
  assert.equal(exampleHeavy.find(item=>item.title==='Anti-patterns').authority,'required');
  assert.equal(exampleHeavy.find(item=>item.title==='Optional styling (when requested)').authority,'reference_candidate');
  assert.equal(exampleHeavy.find(item=>item.title==='Output format').authority,'reference_candidate');
});

test('source dispositions reject silent loss but allow justified pruning of non-mandatory examples', () => {
  const resources={'source/SKILL.md':Buffer.from('# Demo\n## The process\nExecute and verify.\n## Worked examples\nExample palette only.\n')};
  const inventory=sourceSectionInventory(resources);
  const proposal={source_requirements:[],nodes:[{id:'work'}],source_dispositions:inventory.map(section=>({section_id:section.section_id,disposition:section.title==='Worked examples'?'omit':'workflow',node_ids:section.title==='Worked examples'?[]:['work'],requirement_ids:[],rationale:section.title==='Worked examples'?'Illustrative values are not task constraints.':'Defines the executable process.'}))};
  assert.deepEqual(validateSourceDispositions(proposal,resources),[]);
  proposal.source_dispositions.find(item=>item.section_id===inventory.find(section=>section.title==='The process').section_id).disposition='omit';
  assert(validateSourceDispositions(proposal,resources).some(item=>item.code==='SOURCE_DISPOSITION_REQUIRED'));
});

test('proposal validation applies safe host repairs locally and records each action', () => {
  const proposal={source_requirements:[{requirement_id:'rule',requirement_kind:'knowledge',source_spans:[{resource:'source/SKILL.md',start_line:1,end_line:1}],trigger:'always',required_result:'Apply rule.',resource_refs:[]}],requirement_mappings:[],nodes:[{id:'work',type:'agent',confidence:1,source_span:{resource:'source/SKILL.md',start_line:1,end_line:1},outputs_schema:{properties:{ok:{const:true}},required:['ok']}}],edges:[]};
  const result=decodeGeneratedProposalDetailed({proposal_json:JSON.stringify(proposal)},'pinned');
  assert.equal(result.proposal.source_revision,'pinned');
  assert.deepEqual(result.proposal.source_requirements[0].details,{});
  assert.equal(result.proposal.nodes[0].outputs_schema.type,'object');
  assert.equal(result.proposal.nodes[0].outputs_schema.properties.ok.type,'boolean');
  assert.deepEqual(result.repairs.map(item=>item.kind).sort(),['requirement_details_defaulted','schema_closed_by_host','schema_type_inferred','schema_type_inferred','source_revision_injected'].sort());
});

test('host never guesses semantic equivalence between model requirements and observed anchors', () => {
  const resources={'source/SKILL.md':Buffer.from('Render the preview.\nUse ffmpeg only when video rendering is requested.\n')};
  const proposal={source_requirements:[{requirement_id:'conditional_render',requirement_kind:'dependency',source_spans:[{resource:'source/SKILL.md',start_line:1,end_line:2}],trigger:'when rendering video',required_result:'Conditionally verify ffmpeg.',resource_refs:['source/SKILL.md'],details:{executable:'ffmpeg',phase:'conditional'}}],requirement_mappings:[{requirement_id:'conditional_render',node_ids:['render'],binding_names:['task'],runtime_guards:['Only when rendering.'],resource_refs:['source/SKILL.md'],status:'agent_assisted',rationale:'Rendering is task-dependent.'}],nodes:[{id:'render',type:'agent',input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:['conditional_render']}],edges:[]};
  const projected=projectObservedRequirements(proposal,resources);
  const observed=projected.source_requirements.find(item=>item.requirement_id.startsWith('observed_dependency_'));
  const mapping=projected.requirement_mappings.find(item=>item.requirement_id===observed.requirement_id);
  assert.equal(mapping,undefined);
  assert.equal(projected.nodes[0].requirement_ids.includes(observed.requirement_id),false);
});

test('host replaces model echoes of observed typed requirements with canonical facts', () => {
  const resources={'source/SKILL.md':Buffer.from('Use ffmpeg only when video rendering is requested.\n')};
  const canonical=observedSourceRequirements(resources)[0];
  const proposal={source_requirements:[{...canonical,details:{executable:'invented',phase:'unconditional'},required_result:'model rewrite'}],requirement_mappings:[{requirement_id:canonical.requirement_id,node_ids:['render'],binding_names:[],runtime_guards:['Only for video.'],resource_refs:['source/SKILL.md'],status:'agent_assisted',rationale:'Conditional rendering.'}],nodes:[{id:'render',type:'agent',input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:[canonical.requirement_id]}],edges:[]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.deepEqual(projected.source_requirements,[canonical]);
  assert.equal(projected.requirement_mappings.filter(item=>item.requirement_id===canonical.requirement_id).length,1);
});

test('host projects a compiled approval gate onto its explicit dependent operation', () => {
  const resources={'source/SKILL.md':Buffer.from('You must obtain approval before rendering.\n')};
  const approval=observedSourceRequirements(resources)[0];
  const proposal={source_requirements:[],requirement_mappings:[{requirement_id:approval.requirement_id,node_ids:['approve'],binding_names:[],runtime_guards:[],resource_refs:['source/SKILL.md'],status:'compiled',rationale:'Explicit approval gate.'}],nodes:[{id:'approve',type:'human_gate',input_bindings:{},resource_refs:['source/SKILL.md'],requirement_ids:[approval.requirement_id]},{id:'render',type:'agent',input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:[]}],edges:[{id:'approved-render',source:'approve',target:'render'}]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.deepEqual(projected.requirement_mappings[0].node_ids,['approve','render']);
  assert(projected.nodes[1].requirement_ids.includes(approval.requirement_id));
});

test('approval coverage rejects any success path that bypasses the human gate', () => {
  const resources={'source/SKILL.md':Buffer.from('You must obtain approval before rendering.\n')};
  const approval=observedSourceRequirements(resources)[0];const span=approval.source_spans[0];
  const proposal={source_requirements:[],requirement_mappings:[{requirement_id:approval.requirement_id,node_ids:['approve','render'],binding_names:[],runtime_guards:[],resource_refs:['source/SKILL.md'],status:'compiled',rationale:'Gate should dominate rendering.'}],nodes:[{id:'approve',semantic_key:'approve_strategy',type:'human_gate',source_span:span},{id:'render',semantic_key:'render_video',type:'agent',operation_mode:'write',source_span:span}],edges:[{id:'to-gate',source:'start',target:'approve'},{id:'approved',source:'approve',target:'render'},{id:'bypass',source:'start',target:'render'}]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.throws(()=>compileRequirementCoverage(projected,resources,projected.nodes,projected.edges),error=>{
    assert.equal(error.code,'EXPANSION_REQUIREMENT_COVERAGE');assert.equal(error.findings.length,1);
    assert.equal(error.findings[0].requirement_id,approval.requirement_id);
    assert.deepEqual(error.findings[0].semantic_keys,['approve_strategy','render_video']);
    assert(error.findings[0].affected_semantic_fields.includes('approvals.before'));
    return true;
  });
});

test('host projects authoritative mappings into redundant node requirement IDs', () => {
  const proposal={source_requirements:[{requirement_id:'semantic_rule',requirement_kind:'knowledge',source_spans:[{resource:'source/SKILL.md',start_line:1,end_line:1}],trigger:'always',required_result:'Use the rule.',resource_refs:['source/SKILL.md'],details:{}}],requirement_mappings:[{requirement_id:'semantic_rule',node_ids:['work'],binding_names:[],runtime_guards:[],resource_refs:['source/SKILL.md'],status:'agent_assisted',rationale:'Applied by work.'}],nodes:[{id:'work',type:'agent',input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:[]}],edges:[]};
  const projected=projectObservedRequirements(proposal,{'source/SKILL.md':Buffer.from('Use the rule.\n')});
  assert.deepEqual(projected.nodes[0].requirement_ids,['semantic_rule']);
});

test('host derives ordinary agent bindings and mapping resources instead of asking the planner to duplicate them', () => {
  const resources={'source/SKILL.md':Buffer.from('Use the reference to prepare and review the result.\n'),'source/reference.md':Buffer.from('Exact method.\n')};
  const requirement={requirement_id:'method',requirement_kind:'method_rule',source_spans:[{resource:'source/reference.md',start_line:1,end_line:1}],trigger:'prepare',required_result:'Use exact method.',resource_refs:['source/reference.md'],details:{rule_text:'Exact method.'}};
  const proposal={source_requirements:[requirement],requirement_mappings:[{requirement_id:'method',node_ids:['prepare'],binding_names:[],runtime_guards:[],resource_refs:['source/reference.md'],status:'agent_assisted',rationale:'Agent follows pinned method.'}],nodes:[
    {id:'prepare',type:'agent',source_span:{resource:'source/SKILL.md',start_line:1,end_line:1}},
    {id:'review',type:'agent',source_span:{resource:'source/SKILL.md',start_line:1,end_line:1}},
  ],edges:[{id:'prepare-review',source:'prepare',target:'review'}]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.deepEqual(projected.nodes[0].input_bindings,{task:'/inputs/task'});
  assert.deepEqual(projected.nodes[0].resource_refs,['source/SKILL.md','source/reference.md']);
  assert.deepEqual(projected.nodes[0].requirement_ids,['method']);
  assert.deepEqual(projected.nodes[1].input_bindings,{task:'/inputs/task',upstream_prepare:'/nodes/prepare/output'});
  assert.deepEqual(projected.nodes[1].resource_refs,['source/SKILL.md']);
});

test('host carries data producers across gates, conditions and joins without model-authored pointers', () => {
  const resources={'source/SKILL.md':Buffer.from('Inspect, approve, branch, join, and deliver.\n')};const span={resource:'source/SKILL.md',start_line:1,end_line:1};
  const proposal={source_requirements:[],requirement_mappings:[],nodes:[
    {id:'inspect',type:'agent',source_span:span},{id:'approve',type:'human_gate',source_span:span},
    {id:'route',type:'condition',source_span:span},{id:'left',type:'agent',source_span:span},{id:'right',type:'agent',source_span:span},
    {id:'join',type:'join',source_span:span},{id:'deliver',type:'agent',source_span:span},
  ],edges:[
    {id:'a',source:'inspect',target:'approve'},{id:'b',source:'approve',target:'route'},
    {id:'c',source:'route',target:'left'},{id:'d',source:'route',target:'right'},
    {id:'e',source:'left',target:'join'},{id:'f',source:'right',target:'join'},{id:'g',source:'join',target:'deliver'},
  ]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.equal(projected.nodes.find(node=>node.id==='left').input_bindings.upstream_inspect,'/nodes/inspect/output');
  assert.equal(projected.nodes.find(node=>node.id==='right').input_bindings.upstream_inspect,'/nodes/inspect/output');
  assert.deepEqual(projected.nodes.find(node=>node.id==='deliver').input_bindings,{task:'/inputs/task',upstream_left:'/nodes/left/output',upstream_right:'/nodes/right/output'});
});

test('host downgrades prose-only compiled claims while retaining structurally enforced mappings', () => {
  const resources={'source/SKILL.md':Buffer.from('Apply the rule.\nObtain approval before work.\n')};
  const approval=observedSourceRequirements(resources).find(item=>item.requirement_kind==='approval');
  const semantic={requirement_id:'semantic_rule',requirement_kind:'knowledge',source_spans:[{resource:'source/SKILL.md',start_line:1,end_line:1}],trigger:'always',required_result:'Apply rule.',resource_refs:['source/SKILL.md'],details:{}};
  const proposal={source_requirements:[semantic],requirement_mappings:[
    {requirement_id:'semantic_rule',node_ids:['work'],binding_names:[],runtime_guards:[],resource_refs:['source/SKILL.md'],status:'compiled',rationale:'Prompt says so.'},
    {requirement_id:approval.requirement_id,node_ids:['approve','work'],binding_names:[],runtime_guards:[],resource_refs:['source/SKILL.md'],status:'compiled',rationale:'Gate precedes work.'},
  ],nodes:[{id:'approve',type:'human_gate',source_span:approval.source_spans[0]},{id:'work',type:'agent',source_span:semantic.source_spans[0]}],edges:[{id:'approve-work',source:'approve',target:'work'}]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.equal(projected.requirement_mappings.find(item=>item.requirement_id==='semantic_rule').status,'agent_assisted');
  assert.equal(projected.requirement_mappings.find(item=>item.requirement_id===approval.requirement_id).status,'compiled');
});

test('host refuses fully-compiled artifact schemas that omit exact source fields', () => {
  const resources={'source/SKILL.md':Buffer.from('Return exact keys `id` and `place`.\n')};
  const requirement=observedSourceRequirements(resources).find(item=>item.requirement_kind==='artifact_schema');
  const proposal={source_requirements:[],requirement_mappings:[{requirement_id:requirement.requirement_id,node_ids:['produce'],binding_names:['id'],runtime_guards:[],resource_refs:['source/SKILL.md'],status:'compiled',rationale:'Structured output.'}],nodes:[{id:'produce',type:'agent',outputs_schema:{type:'object',properties:{id:{type:'string'}},required:['id']},source_span:requirement.source_spans[0]}],edges:[]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.equal(projected.requirement_mappings[0].status,'agent_assisted');
  projected.nodes[0].outputs_schema.properties.place={type:'string'};projected.nodes[0].outputs_schema.required.push('place');projected.requirement_mappings[0].status='compiled';
  assert.equal(projectObservedRequirements(projected,resources).requirement_mappings[0].status,'compiled');
});

test('host preserves explicit bindings including invalid pointers for visible validation', () => {
  const resources={'source/SKILL.md':Buffer.from('Prepare and review the result.\n'),'source/reference.md':Buffer.from('Exact method.\n')};
  const requirement={requirement_id:'method',requirement_kind:'method_rule',source_spans:[{resource:'source/reference.md',start_line:1,end_line:1}],trigger:'prepare',required_result:'Use exact method.',resource_refs:['source/reference.md'],details:{rule_text:'Exact method.'}};
  const proposal={source_requirements:[requirement],requirement_mappings:[{requirement_id:'method',node_ids:['prepare'],binding_names:[],runtime_guards:[],resource_refs:['source/reference.md'],status:'agent_assisted',rationale:'Agent follows pinned method.'}],nodes:[
    {id:'prepare',type:'agent',input_bindings:{task:'/inputs/invented',semantic_choice:'/inputs/style'},resource_refs:['source/SKILL.md'],requirement_ids:['invented_requirement'],source_span:{resource:'source/SKILL.md',start_line:1,end_line:1}},
    {id:'review',type:'agent',input_bindings:{task:'/inputs/invented',upstream_wrong:'/nodes/missing/output',semantic_choice:'/inputs/style'},resource_refs:['source/SKILL.md'],requirement_ids:['invented_requirement'],source_span:{resource:'source/SKILL.md',start_line:1,end_line:1}},
  ],edges:[{id:'prepare-review',source:'prepare',target:'review'}]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.deepEqual(projected.nodes[0].input_bindings,proposal.nodes[0].input_bindings);
  assert.deepEqual(projected.nodes[0].requirement_ids,['method']);
  assert.deepEqual(projected.nodes[1].input_bindings,proposal.nodes[1].input_bindings);
  assert.throws(()=>resolveBindings(projected.nodes[1].input_bindings,{inputs:{invented:'declared task',style:'plain'},nodes:{prepare:{output:{}}}}),{code:'BINDING_MISSING'});
  assert.deepEqual(projected.nodes[1].requirement_ids,[]);
});

test('host derives unique semantic producer bindings and accepts mapped output fields', () => {
  const resources={'source/SKILL.md':Buffer.from('Produce and review the result.\n')};const span={resource:'source/SKILL.md',start_line:1,end_line:1};
  const requirement={requirement_id:'result_contract',requirement_kind:'artifact_schema',source_spans:[span],trigger:'produce',required_result:'Produce the result.',resource_refs:['source/SKILL.md'],details:{}};
  const proposal={source_requirements:[requirement],requirement_mappings:[{requirement_id:'result_contract',node_ids:['produce','review'],binding_names:['result'],runtime_guards:[],resource_refs:[],status:'agent_assisted',rationale:'Produce then review.'}],nodes:[{id:'produce',type:'agent',outputs_schema:{type:'object',properties:{result:{type:'string'}},required:['result']},source_span:span},{id:'review',type:'agent',source_span:span}],edges:[{id:'produce-review',source:'produce',target:'review'}]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.equal(projected.nodes.find(node=>node.id==='review').input_bindings.result,'/nodes/produce/output/result');
  assert.deepEqual(projected.requirement_mappings[0].resource_refs,['source/SKILL.md']);
  assert.equal(compileRequirementCoverage(projected,resources,projected.nodes,projected.edges).coverage.find(item=>item.requirement_id==='result_contract').status,'agent_assisted');
});

test('host reports an unmapped observed anchor instead of fabricating coverage', () => {
  const resources={'source/SKILL.md':Buffer.from('Round distance to 2 decimal places.\n')};
  const proposal={source_requirements:[],requirement_mappings:[],nodes:[{id:'work',type:'agent',input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:[]}],edges:[]};
  const projected=projectObservedRequirements(proposal,resources), observed=projected.source_requirements[0];
  assert.equal(projected.requirement_mappings.length,0);
  const coverage=compileRequirementCoverage(projected,resources,projected.nodes,projected.edges).coverage;
  assert(coverage.some(item=>item.requirement_id===observed.requirement_id && item.status==='unsupported'));
});

test('host derives unconditional executable preparation from canonical dependency mappings', () => {
  const resources={'source/SKILL.md':Buffer.from('This task requires ffmpeg.\n')};
  const dependency=observedSourceRequirements(resources).find(item=>item.requirement_kind==='dependency');
  const proposal={source_requirements:[],requirement_mappings:[{requirement_id:dependency.requirement_id,node_ids:['work'],binding_names:[],runtime_guards:[],resource_refs:['source/SKILL.md'],status:'compiled',rationale:'Required for every run.'}],nodes:[{id:'work',type:'agent',input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:[]}],edges:[],required_executables:[{name:'invented',confidence:0,source_span:{resource:'source/SKILL.md',start_line:1,end_line:1}}]};
  const projected=projectObservedRequirements(proposal,resources);
  assert.deepEqual(projected.required_executables,[{name:'ffmpeg',confidence:1,source_span:{resource:'source/SKILL.md',start_line:1,end_line:1}}]);
});

test('host fills mechanical human-gate projection fields from its source span and mappings', () => {
  const resources={'source/SKILL.md':Buffer.from('You must obtain approval before rendering.\n')},approval=observedSourceRequirements(resources)[0];
  const proposal={source_requirements:[],requirement_mappings:[{requirement_id:approval.requirement_id,node_ids:['approve'],binding_names:[],runtime_guards:[],resource_refs:['source/SKILL.md'],status:'compiled',rationale:'Explicit gate.'}],nodes:[{id:'approve',type:'human_gate',source_span:{resource:'source/SKILL.md',start_line:1,end_line:1},confidence:1},{id:'render',type:'agent',input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:[],source_span:{resource:'source/SKILL.md',start_line:1,end_line:1},confidence:1}],edges:[{id:'approved-render',source:'approve',target:'render'}]};
  const projected=projectObservedRequirements(proposal,resources),gate=projected.nodes[0];
  assert.deepEqual(gate.input_bindings,{});assert.deepEqual(gate.resource_refs,['source/SKILL.md']);assert(gate.requirement_ids.includes(approval.requirement_id));
});

test('code and binary assets relocate byte-for-byte and are not definition errors', async t => {
  const f=await fixture(t,'Use the bundled script and binary asset at execution time.');
  await mkdir(join(f.sourceRoot,'scripts'));
  const code=Buffer.from('print("portable")\n'); const binary=Buffer.from([0,255,128,1]);
  await writeFile(join(f.sourceRoot,'scripts','run.py'),code);await writeFile(join(f.sourceRoot,'asset.bin'),binary);
  await writeFile(join(f.sourceRoot,'.env.example'),'API_KEY=\n');
  const pack=await importCoarseSkill(f.store,f.source,{id:'portable'});
  await rm(f.sourceRoot,{recursive:true});
  const files=await f.store.resources('portable');
  assert.deepEqual(files['source/scripts/run.py'],code);assert.deepEqual(files['source/asset.bin'],binary);
  assert.equal(files['source/.env.example'].toString(),'API_KEY=\n');
  const definition=validateWorkflowGraph({...pack.workflow,status:'ready'},{tools:['read_workflow_resource']});
  assert.equal(definition.launch_ready,true);
  assert(!pack.workflow.requirements.executables.includes('python'));
  assert(pack.import_report.observed_dependencies.some(item=>item.kind==='executable' && item.name==='python'));
  assert(pack.import_report.observations.some(i=>i.code==='SCRIPT_REQUIRES_REVIEW'));
});

test('source status detects changes to imported resources, not only SKILL.md', async t => {
  const f=await fixture(t,'Run the bundled script.');await mkdir(join(f.sourceRoot,'scripts'));const script=join(f.sourceRoot,'scripts','run.py');await writeFile(script,'print("one")\n');
  const pack=await importCoarseSkill(f.store,f.source,{id:'status-resources'});
  const initial=await skillSourceStatus(pack);assert.equal(initial.scope,'complete imported Skill source inventory bytes');assert(initial.entries.every(item=>item.status==='unchanged'));
  await writeFile(script,'print("two")\n');const changed=await skillSourceStatus(pack);assert.equal(changed.entries.find(item=>item.resource==='source/scripts/run.py').status,'update_available');assert.equal(changed.entries.find(item=>item.resource==='source/SKILL.md').status,'unchanged');
});

test('automatic planning pins model suitability and compiles main, independent parallel agents and human approval', async t => {
  const f=await fixture(t,'Inspect two independent sources and synthesize a result.');
  const providers=[{id:'custom-fast',description:'Fast bounded evidence extraction',enabled:true,kind:'native_agent',capabilities:{read:true},config:{model:'custom-model',role:'implementer'}}];
  const pack=await importCoarseSkill(f.store,f.source,{id:'automatic'});
  const resources=await f.store.resources('automatic'); const rules=defaultRoutingRules(providers);
  const span={resource:'source/SKILL.md',start_line:9,end_line:9};
  const proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],planning_analysis:{parallelism:'A and B read independent sources, join before synthesis.',main_responsibilities:'Main synthesizes evidence.',human_intervention:'Confirm synthesis before final acceptance.'},nodes:[
    {id:'fork',type:'parallel',join_id:'join'},
    ...['a','b'].map(id=>({id,type:'agent',execution_target:'thread',provider_choice:'custom-fast',operation_mode:'read',task_type:'implementation',routing_reason:'Fast bounded evidence extraction fits the independent read task',prompt_template:'Read evidence'})),
    {id:'join',type:'join',parallel_id:'fork'},
    {id:'synthesize',type:'agent',execution_target:'main',task_type:'planning',routing_reason:'Main retains cross-source synthesis and user decisions',prompt_template:'Synthesize'},
    {id:'confirm',type:'human_gate',prompt_template:'Confirm synthesis'},
  ].map(n=>({...n,confidence:0.9,source_span:span})),edges:[['start','fork'],['fork','a'],['fork','b'],['a','join'],['b','join'],['join','synthesize'],['synthesize','confirm'],['confirm','final']].map(([source,target])=>({id:source+'-'+target,source,target,...(source==='fork'?{label:target}:{}),confidence:0.9,source_span:span}))};
  const context={providers,roles:roleProfiles,routing_rules:rules,tools:['read_workflow_resource']};
  const planningPrompt=expansionPacket(pack,resources,providers[0],rules,providers).prompt;
  assert.doesNotMatch(planningPrompt,/Fast bounded evidence extraction/);
  assert.match(planningPrompt,/Routing is entirely Host-owned/);
  const result=compileExpansion(pack,resources,proposal,context);
  assert.equal(result.validation.valid,true);
  assert.notEqual(result.workflow.import_status.conversion_level,'unsupported',JSON.stringify(result.workflow.import_status.requirement_coverage));
  const invalidChoice=structuredClone(proposal);invalidChoice.nodes.find(n=>n.id==='a').provider_choice='invented';
  assert.throws(()=>compileExpansion(pack,resources,invalidChoice,context),{code:'ROUTING_CLASSIFICATION'});
  assert.equal(result.workflow.nodes.find(n=>n.id==='synthesize').executor.kind,'main');
  assert.equal(result.workflow.nodes.find(n=>n.id==='a').executor.provider_id,'custom-fast');
  assert.equal(result.workflow.nodes.find(n=>n.id==='a').executor.kind,'thread');
  assert.equal(result.workflow.nodes.find(n=>n.id==='a').executor.lifecycle,'start');
  assert(result.workflow.requirements.providers.includes('custom-fast'));
  assert.equal(result.workflow.nodes.find(n=>n.id==='confirm').approval.required,true);
  assert.throws(()=>compileExpansion(pack,resources,{...proposal,planning_analysis:undefined},context),{code:'EXPANSION_PLANNING_ANALYSIS'});
  assert.throws(()=>compileExpansion(pack,resources,proposal,{...context,providers:[],routing_catalog:providers}),{code:'ROUTING_PROVIDER_UNAVAILABLE'});
  const saved=await applyExpansion(f.store,'automatic',proposal,{expected_revision:pack.revision_hash,context,inference_confirmation:'Confirmed all displayed nodes and edges',conversion_review_contract_version:CONVERSION_CONTRACT.version});
  assert(!validateWorkflowGraph(saved.workflow,context).blockers.some(i=>i.code==='AI_INFERENCE_UNREVIEWED'));
  assert.equal(saved.provenance.kind,'workflow_conversion');
  assert.equal(saved.workflow.nodes.find(n=>n.id==='a').origin.kind,'converted');
  assert(saved.import_report.expansion.inference_confirmation.note);
  assert.equal(saved.resources.some(item=>item.path.startsWith('source/')),false);
  assert.equal(saved.workflow.status,'draft');
  assert.doesNotThrow(()=>requireCurrentConversionCertificate(saved.workflow,saved.resources,saved.import_report));
  const reviewOnly=structuredClone(saved.workflow);const reviewedNode=reviewOnly.nodes.find(node=>node.origin?.kind==='converted');
  reviewedNode.origin.reviewed=!reviewedNode.origin.reviewed;reviewedNode.origin.review={actor:'user',revision:'later-review-revision',note:'Confirmed the exact certified inference.'};
  assert.doesNotThrow(()=>requireCurrentConversionCertificate(reviewOnly,saved.resources,saved.import_report));
  const forgedStatus=structuredClone(saved.workflow);forgedStatus.import_status.conversion_level=forgedStatus.import_status.conversion_level==='unsupported'?'fully_compiled':'unsupported';
  assert.throws(()=>requireCurrentConversionCertificate(forgedStatus,saved.resources,saved.import_report),{code:'CONVERSION_CERTIFICATE_STALE'});
  assert.throws(()=>createConversionCertificate(saved.workflow,saved.resources,{source_revision:pack.revision_hash,proposal_hash:saved.import_report.expansion.proposal_hash}),{code:'CONVERSION_REVIEW_CONTRACT_STALE'});
  const mutated=structuredClone(saved.workflow);mutated.nodes.find(node=>node.id==='synthesize').prompt_template+=' changed';
  assert.throws(()=>requireCurrentConversionCertificate(mutated,saved.resources,saved.import_report),{code:'CONVERSION_CERTIFICATE_STALE'});
  assert.deepEqual(saved.workflow.requirements.executables,pack.workflow.requirements.executables);
  assert.throws(()=>expansionPacket(saved,resources,providers[0],rules,providers),{code:'AUTHORING_SOURCE'});
  const rerouted=structuredClone(proposal);
  rerouted.source_revision=saved.revision_hash;
  for(const node of rerouted.nodes.filter(n=>n.type==='agent')) {node.execution_target='main';delete node.provider_choice;}
  assert.throws(()=>compileExpansion(saved,resources,rerouted,context),{code:'AUTHORING_SOURCE'});
  assert.equal((await f.store.snapshot('automatic',pack.revision_hash)).revision_hash,pack.revision_hash);
  await f.store.resumeHistoryPurge('automatic',saved.revision_hash,{beforePurge:async()=>{}});
  await assert.rejects(f.store.snapshot('automatic',pack.revision_hash),{code:'ENOENT'});
  await assert.rejects(applyExpansion(f.store,'automatic',proposal,{expected_revision:pack.revision_hash,context,conversion_review_contract_version:CONVERSION_CONTRACT.version}),{code:'ENOENT'});
});

test('folder discovery scans default Codex roots without a binary and reselects custom folders by source hash', async t => {
  const f = await fixture(t);
  const home = join(f.root,'codex');
  await mkdir(join(home,'skills','demo'),{recursive:true});
  await mkdir(join(home,'plugins','cache'),{recursive:true});
  await writeFile(join(home,'skills','demo','SKILL.md'),await readFile(f.source));
  const inventory = new SkillInventory(folder=>discoverFolderSkills(folder,{env:{CODEX_HOME:home}}));
  const found = await inventory.list();
  assert.equal(found.entries.length,1); assert.equal(found.complete,true);
  assert.equal(found.model_invocations,0); assert.equal(found.entries[0].enabled,false);
  const custom = await inventory.list(f.sourceRoot);
  assert.equal(custom.entries.length,1);
  await writeFile(f.source,(await readFile(f.source,'utf8'))+'\nChanged');
  await assert.rejects(inventory.select(f.sourceRoot,custom.entries[0].id),{code:'SKILL_SELECTION_STALE'});
  const absent = await inventory.list(join(f.root,'absent'));
  assert.equal(absent.complete,false); assert.equal(absent.errors[0].code,'ENOENT');
  await assert.rejects(inventory.list('relative'),{code:'SKILL_DISCOVERY_FOLDER'});
});

test('routed expansion assigns each responsibility independently and pins editable planning rules', async t => {
  const f = await fixture(t,'Implement a result.\nReview the result.');
  const providers = [
    {id:'native-luna',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},config:{role:'advisor'}},
    {id:'native-sol',enabled:true,kind:'native_agent',capabilities:{read:true,write:false},config:{role:'reviewer'}},
  ];
  const pack = await importCoarseSkill(f.store,f.source,{id:'routed'});
  const resources = await f.store.resources('routed');
  const rules = {...defaultRoutingRules(providers),selection_mode:"fixed",generation:{planner_provider_id:'native-luna',review_provider_id:'native-sol',max_rounds:2}};
  const span = {resource:'source/SKILL.md',start_line:10,end_line:10};
  const proposal = {source_revision:pack.revision_hash,nodes:[
    {id:'build',type:'agent',task_type:'implementation',routing_reason:'Routine production',prompt_template:'Implement',confidence:0.9,source_span:span},
    {id:'check',type:'agent',task_type:'review',routing_reason:'Independent checking',prompt_template:'Review',confidence:0.9,source_span:span},
  ],edges:[['start','build'],['build','check'],['check','final']].map(([source,target])=>({id:source+'-'+target,source,target,confidence:0.9,source_span:span}))};
  const packet = expansionPacket(pack,resources,providers[0],rules);
  assert.deepEqual(packet.routing_rules,rules);
  assert.throws(()=>compileExpansion(pack,resources,proposal,{providers,roles:roleProfiles}),{code:'ROUTING_RULES_REQUIRED'});
  const result = compileExpansion(pack,resources,proposal,{providers,roles:roleProfiles,routing_rules:packet.routing_rules,tools:['read_workflow_resource']});
  const boundPack = structuredClone(pack); boundPack.workflow.nodes.find(n=>n.id==='instructions').executor={kind:'provider',provider_id:'native-luna'};
  assert.throws(()=>compileExpansion(boundPack,resources,proposal,{providers,roles:roleProfiles}),{code:'ROUTING_RULES_REQUIRED'});
  const bound = compileExpansion(boundPack,resources,proposal,{providers,roles:roleProfiles,routing_rules:packet.routing_rules,tools:['read_workflow_resource']});
  assert.equal(bound.workflow.nodes.find(n=>n.id==='check').executor.provider_id,'native-sol');
  assert.equal(result.workflow.nodes.find(n=>n.id==='build').executor.provider_id,'native-luna');
  assert.equal(result.workflow.nodes.find(n=>n.id==='check').executor.provider_id,'native-sol');
  assert.equal(Object.hasOwn(result.workflow.nodes.find(n=>n.id==='build'),'role_ref'),false);
  assert.equal(Object.hasOwn(result.workflow.nodes.find(n=>n.id==='check'),'role_ref'),false);
  const reviewAndFix = structuredClone(proposal);
  reviewAndFix.nodes.find(node => node.id === 'check').operation_mode = 'write';
  const writeCapable = providers.map(provider => provider.id === 'native-sol'
    ? { ...provider, capabilities: { read: true, write: true } } : provider);
  const convertedReviewAndFix = compileExpansion(pack,resources,reviewAndFix,
    {providers:writeCapable,roles:roleProfiles,routing_rules:packet.routing_rules,tools:['read_workflow_resource']});
  assert.equal(convertedReviewAndFix.validation.valid,true);
  assert.equal(convertedReviewAndFix.workflow.nodes.find(node=>node.id==='check').access,'bounded_write');
  assert.equal(Object.hasOwn(convertedReviewAndFix.workflow.nodes.find(node=>node.id==='check'),'role_ref'),false);
  assert.throws(()=>compileExpansion(pack,resources,reviewAndFix,
    {providers,roles:roleProfiles,routing_rules:packet.routing_rules,tools:['read_workflow_resource']}),{code:'EXPANSION_WRITE_PROVIDER'});
  assert.equal(result.workflow.nodes.find(n=>n.id==='final').executor.kind,'main');
  assert.equal(result.workflow.status,'draft');
  const job = expansionRunPack(pack,resources,providers[0],'planning-job',rules,false,providers[1],providers);
  rules.routes.implementation.provider_id='native-luna';
  assert.equal(job.provenance.routing_rules.routes.implementation.provider_id,'native-luna');
  assert.doesNotMatch(job.resources['analysis/request.txt'],/Every agent requires task_type/);
  assert.match(job.resources['analysis/request.txt'],/compact activity profile/);
  const dependencyPack=structuredClone(pack);dependencyPack.workflow.requirements.executables=['ffmpeg','ffprobe'];
  const dependencyJob=expansionRunPack(dependencyPack,resources,providers[0],'dependency-planning-job',packet.routing_rules,false,providers[1],providers);
  assert.match(dependencyJob.resources['analysis/request.txt'],/Imported Draft baseline requirements/);
  assert.match(dependencyJob.resources['analysis/request.txt'],/"ffprobe"/);
  const expanded = await applyExpansion(f.store,'routed',proposal,{expected_revision:pack.revision_hash,context:{providers,roles:roleProfiles,routing_rules:packet.routing_rules,tools:['read_workflow_resource']},conversion_review_contract_version:CONVERSION_CONTRACT.version});
  const regeneratedJob = expansionRunPack(expanded,resources,providers[0],'regeneration-job',packet.routing_rules,false,providers[1],providers);
  assert.match(regeneratedJob.resources['analysis/request.txt'],/source\/SKILL.md/);
  const regenerated = await applyExpansion(f.store,'routed',{...proposal,source_revision:expanded.revision_hash},{expected_revision:expanded.revision_hash,context:{providers,roles:roleProfiles,routing_rules:packet.routing_rules,tools:['read_workflow_resource']},conversion_review_contract_version:CONVERSION_CONTRACT.version});
  assert.deepEqual(regenerated.resources,expanded.resources);
  assert.equal(regenerated.workflow.nodes.find(n=>n.id==='check').executor.provider_id,'native-sol');
  assert.equal(regenerated.workflow.import_status.unresolved.filter(i=>i.code==='AI_INFERENCES_REQUIRE_REVIEW').length,1);
  const disabled = providers.map(p=>p.id==='native-sol'?{...p,enabled:false}:p);
  assert.throws(()=>compileExpansion(pack,resources,proposal,{providers:disabled,roles:roleProfiles,routing_rules:rules}),{code:'ROUTING_PROVIDER_UNAVAILABLE'});
  const invalid = structuredClone(proposal); invalid.nodes[0].task_type='invented';
  assert.throws(()=>compileExpansion(pack,resources,invalid,{providers,roles:roleProfiles,routing_rules:rules}),{code:'ROUTING_CLASSIFICATION'});
  const forged = structuredClone(proposal); forged.nodes[0].executor={kind:'main'};
  assert.throws(()=>compileExpansion(pack,resources,forged,{providers,roles:roleProfiles,routing_rules:rules}),{code:'EXPANSION_AUTHORITY'});
});

async function fixture(t, body = 'Read [the guide](references/guide.md) and return a result.') {
  const root = await mkdtemp(join(tmpdir(), 'skill-import-')); t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const sourceRoot = join(root, 'original'); await mkdir(join(sourceRoot, 'references'), { recursive: true });
  const source = join(sourceRoot, 'SKILL.md');
  await writeFile(source, '---\nname: "Example: quoted name"\ndescription: >-\n  A folded description\n  across two lines.\nlicense: ISC\n---\n\n' + body);
  await writeFile(join(sourceRoot, 'references', 'guide.md'), 'A self-contained reference.');
  const store = await new WorkflowStore(join(root, 'packs')).initialize(); return { root, sourceRoot, source, store };
}

test('real YAML parsing preserves quoted and folded metadata and rejects duplicate keys and unsafe aliases', () => {
  assert.equal(parseSkill('---\nname: "A: B"\ndescription: >-\n  First\n  second\n---\nDo work.').metadata.description, 'First second');
  assert.throws(() => parseSkill('---\nname: a\nname: b\ndescription: test\n---\nDo work.'), { code: 'SKILL_YAML' });
  assert.throws(() => parseSkill('---\nname: a\ndescription: !unsafe test\n---\nDo work.'), { code: 'SKILL_YAML' });
});

test('coarse import is deterministic, preserves both metadata formats and survives source removal', async t => {
  const f = await fixture(t); const original = await readFile(f.source);
  await mkdir(join(f.sourceRoot, 'agents')); await writeFile(join(f.sourceRoot, 'agents', 'openai.yaml'), 'interface:\n  display_name: Example\n');
  await writeFile(join(f.sourceRoot, 'SKILL.json'), '{"name":"Example"}');
  const source = await readSkillSnapshot(f.source, { expectedSourceHash: digest(original) });
  const one = compileCoarseSkill(source, { id: 'imported', providerId: 'chosen' });
  const two = compileCoarseSkill(source, { id: 'imported', providerId: 'chosen' });
  assert.equal(canonicalJSON(one.workflow), canonicalJSON(two.workflow)); assert.equal(one.workflow.status, 'draft');
  const main = compileCoarseSkill(source, { id: 'main-import' }); assert.deepEqual(main.workflow.nodes[1].executor, { kind: 'main' });
  assert.deepEqual(main.workflow.requirements.providers, []); assert.equal(main.workflow.skill_policy.mode, 'cooperative');
  assert.deepEqual(one.workflow.nodes.map(node => node.type), ['start', 'agent', 'agent', 'end']);
  assert.equal(one.workflow.nodes[1].executor.provider_id, 'chosen'); assert.deepEqual(Object.keys(one.provenance.metadata_files).sort(), ['SKILL.json', 'agents/openai.yaml']);
  const pack = await f.store.create(one.workflow, one); assert.deepEqual(await readFile(f.source), original);
  await rm(f.sourceRoot, { recursive: true });
  const resources = await f.store.resources('imported'); const evidence = verifyCoarseRelocation(pack, resources);
  assert.equal(evidence.source_independent, true); assert.equal(evidence.original_source_read, false); assert.equal(evidence.files_verified, 4);
  assert.equal(resources['source/SKILL.md'].toString(), original.toString());
});

test('scripts, missing references, external paths and credential resources stay observable and blocked', async t => {
  const f = await fixture(t, 'Read [missing](../outside.txt). Use C:\\private\\source.');
  await mkdir(join(f.sourceRoot, 'scripts')); await writeFile(join(f.sourceRoot, 'scripts', 'run.mjs'), 'throw new Error("IMPORT_MUST_NEVER_EXECUTE_THIS");\nconst key = process.env.REQUIRED_KEY;');
  await writeFile(join(f.sourceRoot, '.env'), 'SYNTHETIC_SECRET_VALUE=must-not-be-copied');
  const pack = await importCoarseSkill(f.store, f.source, { id: 'requirements', providerId: 'chosen' });
  assert.equal(pack.import_report.scripts_executed, 0);
  assert(pack.import_report.observations.some(item => item.code === 'SCRIPT_REQUIRES_REVIEW'));
  assert(pack.workflow.import_status.unresolved.some(item => item.code === 'UNRESOLVED_LOCAL_REFERENCE'));
  assert(pack.workflow.import_status.unresolved.some(item => item.code === 'CREDENTIAL_FILE_EXCLUDED'));
  const resources = await f.store.resources('requirements'); assert.equal(resources['source/.env'], undefined);
  assert.deepEqual(pack.workflow.requirements.environment, []);
  assert(pack.import_report.observed_dependencies.some(item=>item.kind==='environment' && item.name==='REQUIRED_KEY'));
  const validation = validateWorkflowGraph({ ...pack.workflow, status: 'ready' }, { providers: [{ id: 'chosen', enabled: true, capabilities: { read: true } }], tools: ['read_workflow_resource'], executables: ['node'] });
  assert(validation.blockers.some(item => item.code === 'IMPORT_UNRESOLVED'));
  assert(!validation.blockers.some(item => item.requirement === 'REQUIRED_KEY'));
  assert(!validateWorkflowGraph({...pack.workflow,status:'ready'},{providers:[{id:'chosen',enabled:true,capabilities:{read:true}}],check_runtime_requirements:true}).blockers.some(item=>item.requirement==='REQUIRED_KEY'));
  assert.throws(() => verifyCoarseRelocation(pack, resources), { code: 'IMPORT_UNRESOLVED' });
});

test('declared metadata dependencies become requirements without activating commands, connections or Provider bindings', async t => {
  const f = await fixture(t); await mkdir(join(f.sourceRoot, 'agents'));
  await writeFile(join(f.sourceRoot, 'agents', 'openai.yaml'), 'dependencies:\n  tools:\n    - type: mcp\n      value: github\n      transport: streamable_http\n      url: https://example.invalid/mcp\n');
  await writeFile(join(f.sourceRoot, 'SKILL.json'), JSON.stringify({ name: 'Example', requirements: { executables: ['git'], environment: ['REQUIRED_NAME'], providers: ['never-bind-this'] } }));
  const pack = await importCoarseSkill(f.store, f.source, { id: 'declared', providerId: 'chosen' });
  assert.deepEqual(pack.workflow.requirements.mcp_servers, ['github']); assert.deepEqual(pack.workflow.requirements.executables, ['git']);
  assert.deepEqual(pack.workflow.requirements.environment, ['REQUIRED_NAME']); assert.deepEqual(pack.workflow.requirements.providers, ['chosen']);
  assert(pack.workflow.import_status.unresolved.some(item => item.code === 'MCP_CONNECTION_REQUIRES_REVIEW'));
  assert(pack.workflow.import_status.unresolved.some(item => item.code === 'UNSUPPORTED_DECLARED_REQUIREMENT'));
  assert.equal(pack.import_report.scripts_executed, 0); assert.equal(pack.workflow.import_status.classification, 'external_requirements');
});

test('Python executable metadata retains its portable version and module requirements', async t => {
  const f = await fixture(t);
  await writeFile(join(f.sourceRoot, 'SKILL.json'), JSON.stringify({ requirements: { executables: [
    { name: 'python', version: '>=3.11,<4', python_modules: ['yaml', 'requests'] },
  ] } }));
  const pack = await importCoarseSkill(f.store, f.source, { id: 'python-requirements' });
  assert.deepEqual(pack.workflow.requirements.executables, [
    { name: 'python', version: '>=3.11.0,<4.0.0', python_modules: ['requests', 'yaml'] },
  ]);
  assert.equal(pack.workflow.import_status.classification, 'external_requirements');
});

test('invalid optional metadata remains a visible Draft blocker and does not silently lose declared dependencies', async t => {
  const f = await fixture(t); await mkdir(join(f.sourceRoot, 'agents'));
  await writeFile(join(f.sourceRoot, 'agents', 'openai.yaml'), 'dependencies:\n  tools: []\ndependencies: {}\n');
  await writeFile(join(f.sourceRoot, 'SKILL.json'), '{"requirements": {"environment": {"TOKEN": "${FROM_ENV}"}}}');
  const pack = await importCoarseSkill(f.store, f.source, { id: 'invalid-metadata' });
  assert.equal(pack.workflow.status, 'draft');
  assert.equal(pack.workflow.import_status.unresolved.filter(item => item.code === 'INVALID_DEPENDENCY_METADATA').length, 2);
  assert.throws(() => verifyCoarseRelocation(pack, {}), { code: 'IMPORT_UNRESOLVED' });
});

test('known secret values are redacted with explicit Draft blockers; source bytes stay unchanged', async t => {
  const secret = 'sk-proj-' + 'x'.repeat(40); const f = await fixture(t, 'Use token ' + secret + ' in an example.');
  const password = randomBytes(24).toString('hex');
  await writeFile(join(f.sourceRoot, 'settings.json'), JSON.stringify({ password }));
  const sourceBytes = await readFile(f.source); const pack = await importCoarseSkill(f.store, f.source, { id: 'redacted' });
  const resources = await f.store.resources('redacted');
  assert(!resources['source/SKILL.md'].toString().includes(secret));
  assert(!resources['source/settings.json'].toString().includes(password));
  assert(pack.workflow.import_status.unresolved.some(item => item.code === 'CREDENTIAL_REDACTED'));
  assert.equal(pack.provenance.source_hash, digest(sourceBytes)); assert.deepEqual(await readFile(f.source), sourceBytes);
});

test('credential scanning preserves executable references, type annotations and shell templates byte-for-byte', async t => {
  const f = await fixture(t);
  const code = 'def transcribe(api_key: str):\n    api_key = load_api_key()\n    return request(headers={"xi-api-key": api_key}, api_key=api_key)\n';
  const docs = '```bash\nprintf \'ELEVENLABS_API_KEY=%s\\n\' "$KEY"\ngrep -q \'^ELEVENLABS_API_KEY=..\' .env\n```\n`ELEVENLABS_API_KEY=...`\n';
  await writeFile(join(f.sourceRoot, 'transcribe.py'), code);
  await writeFile(join(f.sourceRoot, 'install.md'), docs);
  const snapshot = await readSkillSnapshot(f.source);
  assert.equal(snapshot.files['source/transcribe.py'].toString(), code);
  assert.equal(snapshot.files['source/install.md'].toString(), docs);
  assert(!snapshot.problems.some(item => item.code === 'CREDENTIAL_REDACTED'));
});

test('literal credentials remain blocked in source, configuration and documentation', () => {
  const credential = randomBytes(24).toString('hex');
  for (const [sourcePath, source] of [
    ['app.py', `api_key: str = "${credential}"`],
    ['app.js', `const password = "${credential}";`],
    ['config.yaml', `password: ${credential}`],
    ['install.md', '```bash\nexport API_KEY=' + credential + '\n```'],
  ]) {
    const result = redactKnownCredentials(source, { sourcePath });
    assert(!result.text.includes(credential), sourcePath);
    assert.equal(result.findings.length, 1, sourcePath);
  }
});

test('linked resources are excluded with evidence and stale selected source is rejected', async t => {
  const f = await fixture(t); await mkdir(join(f.root, 'outside')); await symlink(join(f.root, 'outside'), join(f.sourceRoot, 'linked'), 'junction');
  const snapshot = await readSkillSnapshot(f.source); assert(snapshot.problems.some(item => item.code === 'LINK_OR_SPECIAL_RESOURCE'));
  await assert.rejects(readSkillSnapshot(f.source, { expectedSourceHash: 'a'.repeat(64) }), { code: 'SKILL_SOURCE_CHANGED' });
});

test('host inventory exposes per-path read errors and stale selections cannot import changed bytes', async t => {
  const f = await fixture(t);
  const inventory = new SkillInventory(async () => ({ skills: [{ path: f.source, scope: 'user', enabled: true }, { path: join(f.sourceRoot, 'missing', 'SKILL.md'), scope: 'user', enabled: true }], errors: [] }));
  const listed = await inventory.list(f.root); assert.equal(listed.complete, false); assert.equal(listed.entries.length, 1); assert.equal(listed.errors.length, 1);
  assert.equal((await inventory.select(f.root, listed.entries[0].id)).source_hash, digest(await readFile(f.source)));
  await writeFile(f.source, (await readFile(f.source, 'utf8')) + '\nChanged');
  await assert.rejects(inventory.select(f.root, listed.entries[0].id), { code: 'SKILL_SELECTION_STALE' });
});

test('configured-profile inventory uses only actual metadata RPCs, keeps path errors and closes without model or config operations', async t => {
  const f = await fixture(t); const calls = []; let closed = false;
  const home = join(f.root, 'codex-profile'); await mkdir(home); await writeFile(join(home, 'config.toml'), 'model = "synthetic"\n');
  const result = await discoverCodexSkills(f.root, { config: {}, env: { CODEX_HOME: home }, qualify: async () => {},
    clientFactory: (_binary, settings) => {
      assert.equal(settings.home, home); return { initialized() { calls.push('initialized'); }, async close() { closed = true; },
        async call(method, params) { calls.push(method); if (method === 'initialize') return {};
          assert.equal(method, 'skills/list'); assert.deepEqual(params, { cwds: [f.root], forceReload: true });
          return { data: [{ cwd: f.root, skills: [{ path: f.source, scope: 'user', enabled: true }], errors: [{ path: 'unreadable-skill', message: 'Do not echo raw host diagnostics' }] }] };
        } };
    } });
  assert.deepEqual(calls, ['initialize', 'initialized', 'skills/list']); assert.equal(closed, true); assert.equal(result.model_invocations, 0);
  assert.deepEqual(result.errors, [{ code: 'CODEX_SKILL_DISCOVERY_ERROR', path: 'unreadable-skill' }]);
  const inventory = await new SkillInventory(async () => result).list(f.root); assert.equal(inventory.complete, false); assert.equal(inventory.entries.length, 1);
});

test('inventory detects concurrent host config edits without reverting them', async t => {
  const f = await fixture(t); const home = join(f.root, 'codex-profile'); await mkdir(home); const path = join(home, 'config.toml'); await writeFile(path, 'before');
  await assert.rejects(discoverCodexSkills(f.root, { config: {}, env: { CODEX_HOME: home }, qualify: async () => {},
    clientFactory: () => ({ initialized() {}, async close() {}, async call(method) {
      if (method === 'initialize') return {};
      await writeFile(path, 'concurrent user edit'); return { data: [{ cwd: f.root, skills: [], errors: [] }] };
    } }) }), { code: 'SKILL_DISCOVERY_CONFIG_CHANGED' });
  assert.equal(await readFile(path, 'utf8'), 'concurrent user edit');
});

test('AI expansion stays Draft, pins inferences, preserves authority and retains the coarse revision on failure', async t => {
  const f = await fixture(t); const provider = { id: 'chosen', enabled: true, capabilities: { read: true } };
  const pack = await importCoarseSkill(f.store, f.source, { id: 'expanded', providerId: provider.id }); const resources = await f.store.resources('expanded');
  const packet = expansionPacket(pack, resources, provider); assert.equal(packet.access, 'read_only'); assert.equal(packet.source_revision, pack.revision_hash);
  assert.match(packet.prompt, /planning Run task is not the future task/);
  assert.match(packet.prompt, /fixed-shape semantic blueprint/i);
  assert.match(packet.prompt, /Host owns all strict Workflow fields/i);
  assert.match(packet.prompt, /Existing input schema and coarse instructions/);
  assert.throws(() => expansionPacket(pack, resources, { ...provider, enabled: false }), { code: 'EXPANSION_PROVIDER' });
  const inference = { confidence: 0.7, source_span: { resource: 'source/SKILL.md', start_line: 9, end_line: 9 } };
  const proposal = { source_revision: pack.revision_hash, nodes: [{ id: 'step', type: 'agent', prompt_template: 'Apply the pinned guide to {{task}}', ...inference }],
    edges: [{ id: 'start-step', source: 'start', target: 'step', ...inference }, { id: 'step-final', source: 'step', target: 'final', ...inference }] };
  const invalid = structuredClone(proposal); invalid.nodes[0].access = 'bounded_write';
  await assert.rejects(applyExpansion(f.store, 'expanded', invalid, { expected_revision: pack.revision_hash, context: { providers: [provider] }, conversion_review_contract_version:CONVERSION_CONTRACT.version }), { code: 'EXPANSION_AUTHORITY' });
  assert.equal((await f.store.snapshot('expanded')).revision_hash, pack.revision_hash);
  const next = await applyExpansion(f.store, 'expanded', proposal, { expected_revision: pack.revision_hash, context: { providers: [provider] }, conversion_review_contract_version:CONVERSION_CONTRACT.version });
  assert.equal(next.workflow.status, 'draft'); assert.equal(next.workflow.nodes.find(node => node.id === 'step').access, 'read_only');
  assert.equal(next.workflow.nodes.find(node => node.id === 'step').executor.provider_id, provider.id);
  assert.equal(next.workflow.nodes.find(node => node.id === 'final').executor.kind, 'main');
  assert(next.workflow.import_status.unresolved.some(item => item.code === 'AI_INFERENCES_REQUIRE_REVIEW'));
  assert.equal((await f.store.snapshot('expanded', pack.revision_hash)).workflow.import_status.mode, 'coarse');
  const regenerated = expansionPacket(next, resources, provider, defaultRoutingRules([{id:'native-luna',enabled:true}]), []);
  assert.match(regenerated.prompt, /previous graph is not source authority/);
  const stale = structuredClone(proposal); stale.source_revision = 'a'.repeat(64);
  await assert.rejects(applyExpansion(f.store, 'expanded', stale, { expected_revision: next.revision_hash, context: { providers: [provider] }, conversion_review_contract_version:CONVERSION_CONTRACT.version }), { code: 'EXPANSION_SCHEMA' });
  const review = importReviewPacket(next); assert.equal(review.inferences.length, 3);
  await assert.rejects(reviewImportedDraft(f.store, 'expanded', { expected_revision: next.revision_hash, decisions: [{ issue_id: review.issues.find(issue => issue.code === 'AI_INFERENCES_REQUIRE_REVIEW').id, resolution: 'resolved', note: 'Cannot blanket-approve inferred flow' }] }), { code: 'IMPORT_REVIEW_ISSUE' });
  const reviewed = await reviewImportedDraft(f.store, 'expanded', { expected_revision: next.revision_hash,
    inferences: review.inferences.map(item => ({ kind: item.kind, id: item.id, note: 'Checked this item against its pinned source span' })) });
  assert.equal(reviewed.workflow.status, 'draft'); assert.deepEqual(reviewed.workflow.import_status.unresolved.map(item=>item.code),['CONVERSION_REQUIREMENT_UNSUPPORTED']);
  assert.equal(reviewed.workflow.import_status.conversion_level,'unsupported');
  assert.equal(reviewed.workflow.nodes.find(node => node.id === 'step').executor.provider_id, provider.id);
  assert(reviewed.import_report.review_history[0].decisions.length === 3);
  const forged = structuredClone(next.workflow); forged.import_status.unresolved = []; forged.status = 'ready';
  assert(validateWorkflowGraph(forged, { providers: [provider] }).blockers.some(item => item.code === 'AI_INFERENCE_UNREVIEWED'));
});

test('published expansion contract compiles a named gate and finite condition without granting model authority', async t => {
  const f = await fixture(t); const provider = { id: 'chosen', enabled: true, capabilities: { read: true } };
  const pack = await importCoarseSkill(f.store, f.source, { id: 'contract', providerId: provider.id });
  const resources = await f.store.resources('contract');
  const origin = { confidence: 0.9, source_span: { resource: 'source/SKILL.md', start_line: 9, end_line: 9 } };
  const proposal = { source_revision: pack.revision_hash, nodes: [
    { id: 'confirm', name: 'Confirm strategy', type: 'human_gate', prompt_template: 'Wait for explicit confirmation.', ...origin },
    { id: 'route', type: 'condition', ...structuredClone(EXPANSION_CONTRACT.condition_example), ...origin },
    ...['yes', 'no', 'aggregate'].map(id => ({ id, name: id, type: 'agent', prompt_template: id === 'aggregate' ? 'Aggregate the selected branch through declared inputs.' : 'Report the actual result.', ...(id === 'aggregate' ? { input_bindings: { task: '/inputs/task', yes_result: '/nodes/yes/output', no_result: '/nodes/no/output' } } : {}), outputs_schema: { type: 'object', properties: { result: { type: 'string' } }, required: ['result'] }, ...origin }))
  ], edges: [
    { id: 'a', source: 'start', target: 'confirm' }, { id: 'b', source: 'confirm', target: 'route' },
    { id: 'c', source: 'route', target: 'yes', label: 'yes' }, { id: 'd', source: 'route', target: 'no', label: 'no' },
    { id: 'e', source: 'yes', target: 'aggregate' }, { id: 'f', source: 'no', target: 'aggregate' }, { id: 'g', source: 'aggregate', target: 'final' }
  ].map(edge => ({ ...edge, ...origin })) };
  const compiled = compileExpansion(pack, resources, proposal, { providers: [provider] });
  const unsupportedTool = structuredClone(proposal);
  unsupportedTool.nodes[2] = { id: 'yes', type: 'tool', tool: 'read_workflow_resource', ...origin };
  assert.throws(() => compileExpansion({...pack,workflow:{...pack.workflow,skill_policy:{...pack.workflow.skill_policy,mode:'strict',implicit:'deny'}}}, resources, unsupportedTool, { providers: [provider] }), { code: 'EXPANSION_HOST_TOOL_UNAUTHORIZED' });
  const gate = compiled.workflow.nodes.find(node => node.id === 'confirm');
  assert.equal(gate.name, 'Confirm strategy'); assert.equal(gate.executor.kind, 'human'); assert.equal(gate.approval.required, true);
  assert.equal(compiled.workflow.nodes.find(node => node.id === 'final').input_bindings.upstream_result, '/nodes/aggregate/output');
  const unboundAggregate = structuredClone(proposal); delete unboundAggregate.nodes.find(node => node.id === 'aggregate').input_bindings;
  const hostBound=compileExpansion(pack, resources, unboundAggregate, { providers: [provider] });
  assert.deepEqual(hostBound.workflow.nodes.find(node=>node.id==='aggregate').input_bindings,{task:'/inputs/task',upstream_selected:{coalesce:['/nodes/no/output','/nodes/yes/output']}});
  assert.deepEqual(compiled.workflow.nodes.find(node => node.id === 'yes').outputs_schema, proposal.nodes[2].outputs_schema);
  const invalid = structuredClone(proposal); invalid.nodes[1].condition_dsl = 'choice == true';
  assert.throws(() => compileExpansion(pack, resources, invalid, { providers: [provider] }), { code: 'EXPANSION_AUTHORITY' });
  const cyclic = structuredClone(proposal); cyclic.edges.find(edge => edge.id === 'e').target = 'confirm';
  assert.throws(() => compileExpansion(pack, resources, cyclic, { providers: [provider] }), { code: 'EXPANSION_GRAPH_INVALID' });
  const inventedGate = structuredClone(proposal);
  inventedGate.nodes[0].outputs_schema = { type: 'object', properties: { strategy_approved: { type: 'boolean' } }, required: ['strategy_approved'] };
  assert.throws(() => compileExpansion(pack, resources, inventedGate, { providers: [provider] }), { code: 'EXPANSION_GRAPH_INVALID' });
  delete inventedGate.nodes[0].outputs_schema;
  inventedGate.nodes[1].cases[0].when = { op: 'eq', args: [{ path: '/nodes/confirm/output/strategy_approved' }, { value: true }] };
  assert.throws(() => compileExpansion(pack, resources, inventedGate, { providers: [provider] }), { code: 'EXPANSION_GRAPH_INVALID' });
  inventedGate.nodes[1].cases[0].when.args[0].path = '/nodes/confirm/output/approved';
  assert.equal(compileExpansion(pack, resources, inventedGate, { providers: [provider] }).validation.valid, true);
  assert.equal((await f.store.snapshot('contract')).revision_hash, pack.revision_hash);
});

test('condition fan-in uses one selected binding while parallel fan-in stays strict', async t => {
  const f=await fixture(t);const provider={id:'chosen',enabled:true,capabilities:{read:true}};
  const pack=await importCoarseSkill(f.store,f.source,{id:'exclusive-fan-in',providerId:provider.id});
  const resources=await f.store.resources('exclusive-fan-in');
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:9,end_line:9}};
  const node=(id,type='agent',extra={})=>({id,type,...(type==='agent'?{prompt_template:id,outputs_schema:{type:'object',properties:{result:{type:'string'}},required:['result']}}:{}),...extra,...origin});
  const proposal={source_revision:pack.revision_hash,nodes:[
    node('initial'),node('decision','condition',{cases:[{label:'pass',when:{op:'eq',args:[{value:true},{value:true}]}}],default_label:'remediate'}),node('remediate'),node('final_review'),node('deliver')
  ],edges:[
    ['a','start','initial'],['b','initial','decision'],['c','decision','deliver','pass'],['d','decision','remediate','remediate'],['e','remediate','final_review'],['f','final_review','deliver'],['g','deliver','final']
  ].map(([id,source,target,label])=>({id,source,target,...(label?{label}:{}),...origin}))};
  assert(exclusiveConditionFanIn(proposal.nodes,proposal.edges,'deliver'));
  const compiled=compileExpansion(pack,resources,proposal,{providers:[provider]});
  assert.deepEqual(compiled.workflow.nodes.find(item=>item.id==='deliver').input_bindings,{task:'/inputs/task',upstream_selected:{coalesce:['/nodes/final_review/output','/nodes/initial/output']}});
  const explicit=structuredClone(proposal),selected={selected_result:{coalesce:['/nodes/final_review/output/result','/nodes/initial/output/result']}};
  explicit.nodes.find(item=>item.id==='deliver').input_bindings=selected;
  const explicitCompiled=compileExpansion(pack,resources,explicit,{providers:[provider]});
  assert.deepEqual(explicitCompiled.workflow.nodes.find(item=>item.id==='deliver').input_bindings,selected);
  assert.deepEqual({...resolveBindings(selected,{nodes:{initial:{output:{result:'initial'}}}})},{selected_result:'initial'});
  assert.deepEqual({...resolveBindings(selected,{nodes:{initial:{output:{result:'initial'}},final_review:{output:{result:'reviewed'}}}})},{selected_result:'reviewed'});
  const direct=structuredClone(proposal);direct.nodes=direct.nodes.filter(item=>item.id!=='deliver');
  direct.edges=direct.edges.filter(edge=>!['c','f','g'].includes(edge.id));
  direct.edges.push({...origin,id:'c2',source:'decision',target:'final',label:'pass'},{...origin,id:'f2',source:'final_review',target:'final'});
  const directCompiled=compileExpansion(pack,resources,direct,{providers:[provider]});
  assert.deepEqual(directCompiled.workflow.nodes.find(item=>item.id==='final').input_bindings.upstream_result,{coalesce:['/nodes/final_review/output','/nodes/initial/output']});
  const ambiguous=structuredClone(direct);delete ambiguous.edges.find(edge=>edge.id==='c2').label;
  assert.throws(()=>compileExpansion(pack,resources,ambiguous,{providers:[provider]}),{code:'EXPANSION_FINAL_INPUT'});
});

test('conversion inventory limits fail before a planning packet is dispatched', async t => {
  const f=await fixture(t);const provider={id:'chosen',enabled:true,capabilities:{read:true}};
  const pack=await importCoarseSkill(f.store,f.source,{id:'bounded-inventory',providerId:provider.id});
  const resources=await f.store.resources('bounded-inventory');
  resources['source/SKILL.md']=Buffer.from(Array.from({length:201},(_,index)=>`## Step ${index+1}\nDo work.`).join('\n'));
  assert.throws(()=>expansionPacket({...pack,resources:prepareResources(resources).manifest},resources,provider,null),{code:'EXPANSION_SOURCE_INVENTORY_LIMIT'});
});

test('a pinned script requirement binds only to a host-authorized contract and executes through the host runner', async t => {
  const f=await fixture(t,'Run `python scripts/run.py input.json` and use its structured result.');
  await mkdir(join(f.sourceRoot,'scripts'));await writeFile(join(f.sourceRoot,'scripts','run.py'),'print("registered broker owns execution")\n');
  const provider={id:'chosen',enabled:true,capabilities:{read:true}};
  const pack=await importCoarseSkill(f.store,f.source,{id:'script-bound',providerId:provider.id});
  const resources=await f.store.resources('script-bound');
  const contract={id:'skill_script_run',identity:{name:'source/scripts/run.py',version:'1',sha256:digest(resources['source/scripts/run.py'])},argv:['python','source/scripts/run.py'],input_schema:{type:'object',required:['task'],additionalProperties:false,properties:{task:{type:'string'}}},output_schema:{type:'object',required:['result'],additionalProperties:false,properties:{result:{type:'string'}}},implements:['observed_script_9_1'],env_allow:[],permissions:{network:false,read_paths:['source/scripts/run.py'],write_paths:[]},output_cap_bytes:4096,deadline_ms:1000,idempotency:{mode:'safe'}};
  const origin={confidence:1,source_span:{resource:'source/SKILL.md',start_line:9,end_line:9}};
  const requirement={requirement_id:'observed_script_9_1',requirement_kind:'script_operation',source_spans:[origin.source_span],trigger:'source_observed',required_result:'Execute the pinned script resource source/scripts/run.py with declared inputs and verified outputs.',resource_refs:['source/scripts/run.py']};
  const dependency=observedSourceRequirements(resources).find(item=>item.requirement_kind==='dependency');assert(dependency);
  const proposal={source_revision:pack.revision_hash,source_requirements:[requirement],requirement_mappings:[{requirement_id:requirement.requirement_id,node_ids:['run_script'],binding_names:['task'],runtime_guards:['exact pinned host contract and receipt'],resource_refs:['source/scripts/run.py'],status:'compiled',rationale:'The registered broker executes the exact pinned script and returns schema-checked output.'},{requirement_id:dependency.requirement_id,node_ids:['run_script'],binding_names:[],runtime_guards:['Host prepares the exact interpreter.'],resource_refs:['source/SKILL.md'],status:'compiled',rationale:'The command-position dependency is bound to the script operation.'}],nodes:[{id:'run_script',type:'tool',tool:contract.id,input_bindings:{task:'/inputs/task'},resource_refs:['source/scripts/run.py'],requirement_ids:[requirement.requirement_id,dependency.requirement_id],...origin}],edges:[{id:'start-run',source:'start',target:'run_script',...origin},{id:'run-final',source:'run_script',target:'final',...origin}]};
  assert.throws(()=>compileExpansion(pack,resources,proposal,{providers:[provider]}),{code:'EXPANSION_HOST_TOOL_UNAUTHORIZED'});
  const genericContract=structuredClone(contract);delete genericContract.implements;
  assert.equal(compileExpansion(pack,resources,proposal,{providers:[provider],host_tool_contracts:[genericContract],host_tools:[genericContract.id]}).workflow.import_status.conversion_level,'agent_assisted');
  const compiled=compileExpansion(pack,resources,proposal,{providers:[provider],host_tool_contracts:[contract],host_tools:[contract.id]});
  assert.equal(compiled.workflow.import_status.conversion_level,'fully_compiled');
  assert.deepEqual(compiled.workflow.nodes.find(node=>node.id==='run_script').outputs_schema,contract.output_schema);
  const implementation={identity:contract.identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:contract.identity,broker_id:'fixture-broker',evidence_sha256:'e'.repeat(64)},execute:async({input})=>({exit_code:0,output:{result:`done:${input.task}`},diagnostic:'ok',effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}}),cancel:async()=>({termination_confirmed:true,evidence:[{kind:'fixture',sha256:'f'.repeat(64)}],effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}})};
  const runner=new HostToolRunner({registry:{[contract.id]:implementation}});
  const executed=await runner.execute(compiled.workflow.host_tools[0],{task:'demo'},{run_id:'run',node_id:'run_script',attempt_id:'attempt',permissions:{access:'read_only',allowed_paths:[]}});
  assert.equal(executed.receipt.status,'succeeded');assert.deepEqual(executed.output,{result:'done:demo'});
  const deployed=await applyExpansion(f.store,'script-bound',proposal,{expected_revision:pack.revision_hash,
    context:{providers:[provider],host_tool_contracts:[contract],host_tools:[contract.id]},
    inference_confirmation:'Accepted exact reviewed script conversion',conversion_review_contract_version:CONVERSION_CONTRACT.version});
  assert(deployed.resources.some(item=>item.path==='workflow-assets/scripts/run.py'));
  assert.deepEqual(deployed.workflow.nodes.find(node=>node.id==='run_script').resources,['workflow-assets/scripts/run.py']);
  assert.deepEqual(deployed.workflow.host_tools[0].argv,['python','workflow-assets/scripts/run.py']);
  assert.deepEqual(deployed.workflow.host_tools[0].permissions.read_paths,['workflow-assets/scripts/run.py']);
  assert.doesNotMatch(canonicalJSON(deployed),/source\/scripts\/run\.py|source\/SKILL\.md/);
});

test('nested Skill documents become Workflow-owned instructions without retaining Skill entrypoints',()=>{
  const resources={
    'source/SKILL.md':Buffer.from('# Source\n\n## Step\nUse the nested reference.'),
    'source/skills/animation/SKILL.md':Buffer.from('# Animation\nRead source/skills/animation/references/guide.md.'),
    'source/skills/animation/references/guide.md':Buffer.from('# Guide\nReturn the animation.'),
  };
  const workflow={id:'converted-nested',nodes:[{id:'work',resources:Object.keys(resources),outputs_schema:{type:'object',properties:{source_path:{type:'string'},source_span:{type:'string'}}}}],edges:[],import_status:{conversion_level:'agent_assisted'}};
  const pack={revision_hash:'a'.repeat(64),provenance:{source_hash:digest(resources['source/SKILL.md'])}};
  const converted=compileDeployableConversion({workflow,proposal:{nodes:[],edges:[]},resources,pack,proposalHash:'b'.repeat(64),reviewContractVersion:CONVERSION_CONTRACT.version});
  const nested='workflow-assets/skills/animation/instructions.md';
  assert(converted.resources[nested]);
  assert(converted.resources['workflow-assets/skills/animation/references/guide.md']);
  assert(!Object.keys(converted.resources).some(path=>path.toLowerCase().endsWith('/skill.md')));
  assert(converted.workflow.nodes[0].resources.includes(nested));
  assert.equal(converted.workflow.import_status.source_independent,true);
  assert.doesNotThrow(()=>requireDeployableConvertedSnapshot({...converted,resources:Object.keys(converted.resources).map(path=>({path}))}));
  assert.throws(()=>requireDeployableConvertedSnapshot({...converted,provenance:{...converted.provenance,source_path:'C:/private/SKILL.md'},resources:Object.keys(converted.resources).map(path=>({path}))}),{code:'CONVERTED_SOURCE_LEAK'});
  const collision={...resources,'source/skills/animation/instructions.md':Buffer.from('Existing instructions.')};
  assert.throws(()=>compileDeployableConversion({workflow:{...workflow,nodes:[{id:'work',resources:Object.keys(collision)}]},proposal:{nodes:[],edges:[]},resources:collision,pack,proposalHash:'b'.repeat(64),reviewContractVersion:CONVERSION_CONTRACT.version}),{code:'CONVERTED_ASSET_COLLISION'});
});

test('review cannot approve a proposal that omits a source-required approval gate', () => {
  const span={resource:'source/SKILL.md',start_line:1,end_line:1};
  const proposal={source_requirements:[{requirement_id:'approval_1',requirement_kind:'approval',source_spans:[span],trigger:'before render',required_result:'approved'}],requirement_mappings:[{requirement_id:'approval_1',node_ids:['render'],status:'compiled'}],source_dispositions:[{section_id:'section_01_overview',disposition:'workflow',node_ids:['render'],requirement_ids:['approval_1'],rationale:'The entrypoint requires approval before render.'}],nodes:[{id:'render',type:'agent'}],edges:[{id:'render-final',source:'render',target:'final'}]};
  const checks=REVIEW_IDS.map(()=>({status:'pass',evidence:'Reviewed against the exact source.'}));
  const result=evaluateReview({checks},proposal,{'source/SKILL.md':Buffer.from('Render only after user approval.')});
  assert.equal(result.approved,false);assert(result.findings.some(item=>item.includes('no human_gate')));
});

test('review validation projects source spans and graph identities in Host order', () => {
  const span={resource:'source/SKILL.md',start_line:1,end_line:1};
  const proposal={source_requirements:[],requirement_mappings:[],source_dispositions:[{section_id:'section_01_overview',disposition:'workflow',node_ids:['work'],requirement_ids:[],rationale:'The entrypoint defines the task.'}],nodes:[{id:'work',type:'agent'}],edges:[{id:'work-final',source:'work',target:'final'}]};
  const checks=REVIEW_IDS.map(()=>({status:'pass',evidence:'Checked.'}));
  const resources={'source/SKILL.md':Buffer.from('Do the work.')};
  const reviewed=evaluateReview({checks},proposal,resources);
  assert.equal(reviewed.approved,true);
  assert.deepEqual(reviewed.checks.map(row=>row.id),REVIEW_IDS);
  assert(reviewed.checks.every(row=>row.node_ids.includes('work')&&row.edge_ids.includes('work-final')&&row.source_spans.length));
  const transcribed=structuredClone(checks);transcribed[0].source_spans=[span];
  assert.throws(()=>evaluateReview({checks:transcribed},proposal,resources),{code:'GENERATION_CHECKLIST_INVALID'});
});

test('v4 contract rejects an all-pass generic proposal that omits exact artifact, method and interface rules', async t => {
  const f=await fixture(t,'Write `record.json` with exact keys `id` and `label`. Apply the declared transform and round to 2 decimal places.');
  const provider={id:'chosen',enabled:true,kind:'native_agent',capabilities:{read:true},config:{role:'implementer'}};
  const reviewer={id:'native-sol',enabled:true,kind:'native_agent',capabilities:{read:true,write:false},config:{role:'reviewer'}};
  const pack=await importCoarseSkill(f.store,f.source,{id:'v4-generic',providerId:provider.id}); const resources=await f.store.resources('v4-generic');
  const origin={confidence:0.9,source_span:{resource:'source/SKILL.md',start_line:9,end_line:9}};
  const proposal={source_revision:pack.revision_hash,source_requirements:[],requirement_mappings:[],required_executables:[],nodes:[{id:'do_task',type:'agent',operation_mode:'read',prompt_template:'Do the task.',input_bindings:{task:'/inputs/task'},resource_refs:['source/SKILL.md'],requirement_ids:[],...origin}],edges:[{id:'start-do',source:'start',target:'do_task',...origin},{id:'do-final',source:'do_task',target:'final',...origin}]};
  const checks=REVIEW_IDS.map(()=>({status:'pass',evidence:'All source requirements are covered.'}));
  const verdict=evaluateReview({checks},proposal,resources);
  assert.equal(verdict.approved,false); assert(verdict.findings.some(finding=>finding.includes('artifact_path'))); assert(verdict.findings.some(finding=>finding.includes('method_rule')));
  const job=expansionRunPack(pack,resources,provider,'v4-projection',null,false,reviewer,[provider,reviewer]);
  assert.deepEqual(job.workflow.nodes.find(node=>node.id==='final').input_bindings,{});
  const expand=job.workflow.nodes.find(node=>node.id==='expand');
  assert.deepEqual(expand.outputs_schema,AUTHORING_RUNTIME_ENVELOPE_SCHEMA);
  assert.doesNotThrow(()=>managedNativeResultSchema(expand));
  assert.match(job.resources['analysis/request.txt'],/workflow-semantic-blueprint\/v6/);
  const outputMeta=EXPANSION_PROPOSAL_SCHEMA.properties.nodes.items.properties.outputs_schema;
  for(const schema of [
    {type:'object',properties:{item_counts:{type:'object',additionalProperties:{type:'integer'}},item_coordinates:{type:'object',additionalProperties:{type:'array',items:{type:'string'}}}},required:['item_counts','item_coordinates'],additionalProperties:false},
    {type:'object',properties:{id:{type:'string'},label:{type:'string'},timestamp:{type:'string'},score:{type:'number'},x:{type:'number'},y:{type:'number'},distance:{type:'number',minimum:0}},required:['id','label','timestamp','score','x','y','distance'],additionalProperties:false},
    {type:'object',properties:{measurements:{type:'array',items:{type:'object',properties:{value:{type:'number'},confidence:{type:'number'}},required:['value','confidence'],additionalProperties:false}}},required:['measurements'],additionalProperties:false},
    {type:'object',properties:{source_value:{type:'number',minimum:0},result_value:{type:'number',minimum:0},delta:{type:'number'},ratio:{type:'number'},operations:{type:'integer',minimum:0}},required:['source_value','result_value','delta','ratio','operations'],additionalProperties:false},
  ]) assert.doesNotThrow(()=>validateData(schema,outputMeta));
});

test('generated proposal envelope is strict while the host validates the decoded full contract', () => {
  const span={resource:'source/SKILL.md',start_line:1,end_line:1};
  const proposal={source_revision:'revision',source_requirements:[],requirement_mappings:[],nodes:[{id:'work',type:'agent',confidence:1,source_span:span}],edges:[]};
  assert.deepEqual(decodeGeneratedProposal({proposal_json:JSON.stringify(proposal)},'revision'),proposal);
  assert.throws(()=>decodeGeneratedProposal({proposal_json:'{'},'revision'),{code:'GENERATION_PROPOSAL_JSON'});
  assert.deepEqual(decodeGeneratedProposal({proposal_json:JSON.stringify({...proposal,source_revision:'wrong'})},'revision'),proposal);
  const {source_revision,...withoutRevision}=proposal;
  assert.deepEqual(decodeGeneratedProposal({proposal_json:JSON.stringify(withoutRevision)},'revision'),proposal);
  assert.throws(()=>decodeGeneratedProposal({proposal_json:JSON.stringify(proposal),extra:true},'revision'),{code:'GENERATION_PROPOSAL_ENVELOPE'});
});

test('generated proposal canonicalizes an omitted requirement details bag', () => {
  const proposal={source_revision:'revision',source_requirements:[{requirement_id:'semantic_rule',requirement_kind:'knowledge',source_spans:[{resource:'source/SKILL.md',start_line:1,end_line:1}],trigger:'always',required_result:'Apply the rule.',resource_refs:['source/SKILL.md']}],requirement_mappings:[],nodes:[{id:'work',type:'agent',outputs_schema:{properties:{fixed_path:{const:'edit/final.mp4'},ready:{const:true},retries:{const:3},order:{const:['base','subtitles']},mode:{enum:['cached','fresh']}}},confidence:1,source_span:{resource:'source/SKILL.md',start_line:1,end_line:1}}],edges:[]};
  const decoded=decodeGeneratedProposal({proposal_json:JSON.stringify(proposal)},'revision');
  assert.deepEqual(decoded.source_requirements[0].details,{});
  assert.equal(decoded.nodes[0].outputs_schema.type,'object');
  assert.deepEqual(Object.fromEntries(Object.entries(decoded.nodes[0].outputs_schema.properties).map(([key,value])=>[key,value.type])),{fixed_path:'string',ready:'boolean',retries:'integer',order:'array',mode:'string'});
});

test('generated proposal canonicalizes one unambiguous upstream boolean condition', () => {
  const span={resource:'source/SKILL.md',start_line:1,end_line:1};
  const proposal={source_revision:'revision',source_requirements:[],requirement_mappings:[],nodes:[{id:'inspect',type:'agent',confidence:1,source_span:span},{id:'route',type:'condition',cases:[{label:'install',when:'environment.triggered && !environment.ready'}],default_label:'skip',confidence:1,source_span:span},{id:'install',type:'agent',confidence:1,source_span:span}],edges:[{id:'inspect-route',source:'inspect',target:'route',confidence:1,source_span:span},{id:'route-install',source:'route',target:'install',on:'install',confidence:1,source_span:span}]};
  const decoded=decodeGeneratedProposal({proposal_json:JSON.stringify(proposal)},'revision');
  assert.deepEqual(decoded.nodes[1].cases[0].when,{op:'and',args:[{op:'eq',args:[{path:'/nodes/inspect/output/environment/triggered'},{value:true}]},{op:'eq',args:[{path:'/nodes/inspect/output/environment/ready'},{value:false}]}]});
  assert.equal(decoded.edges[1].label,'install');assert.equal(decoded.edges[1].on,undefined);
  const ambiguous=structuredClone(proposal);ambiguous.edges.push({id:'other-route',source:'other',target:'route',confidence:1,source_span:span});
  assert.throws(()=>decodeGeneratedProposal({proposal_json:JSON.stringify(ambiguous)},'revision'),{code:'GENERATION_PROPOSAL_CONTRACT'});
});

test('import issue review retains exact evidence and requirements under CAS without publishing', async t => {
  const f = await fixture(t, 'Read [missing](references/missing.md).');
  const pack = await importCoarseSkill(f.store, f.source, { id: 'reviewed', providerId: 'chosen' });
  const review = importReviewPacket(pack); const issue = review.issues.find(item => item.code === 'UNRESOLVED_LOCAL_REFERENCE'); assert(issue);
  const args = { expected_revision: pack.revision_hash, decisions: [{ issue_id: issue.id, resolution: 'not_required', note: 'Citation is contextual; source instructions are complete locally' }] };
  const next = await reviewImportedDraft(f.store, 'reviewed', args);
  assert.equal(next.workflow.status, 'draft'); assert.deepEqual(next.workflow.requirements, pack.workflow.requirements);
  assert.equal(next.import_report.review_history[0].source_revision, pack.revision_hash);
  assert.equal(next.import_report.review_history[0].decisions[0].observation.target, 'references/missing.md');
  assert.equal(next.workflow.import_status.unresolved.length, 0);
  await assert.rejects(reviewImportedDraft(f.store, 'reviewed', args), { code: 'REVISION_CONFLICT' });
});
