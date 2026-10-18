import test from 'node:test';
import assert from 'node:assert/strict';
import { compileWorkflowBrief } from '../lib/skill-import/workflow-authoring.mjs';
import { WorkflowForge } from '../lib/authoring/workflow-forge.mjs';
import { SEMANTIC_BLUEPRINT_CONTRACT } from '../lib/authoring/blueprint-contract.mjs';
import { sourceSectionInventory } from '../lib/skill-import/source-dispositions.mjs';
import { callableSourceRequirements, observedSourceRequirements } from '../lib/skill-import/source-requirements.mjs';
import { prepareResources, revisionHash } from '../lib/workflow-revisions.mjs';
import { sourceResourceMentions } from '../lib/skill-import/source-resource-mentions.mjs';

const providers=[{id:'worker',enabled:true,kind:'native_agent',capabilities:{read:true,write:true}}];
const routing={version:1,instructions:'Use the existing worker.',selection_mode:'automatic',routes:Object.fromEntries(['implementation','complex_implementation','review','planning'].map(type=>[type,{provider_id:'worker'}]))};
function compileSource(body){
  const build=compileWorkflowBrief({workflow_id:'resource-mentions',name:'Resource mentions',brief:'# Workflow\n\n## Procedure\n\n'+body,provider_id:'worker'});
  const resources={...build.resources,
    'source/scripts/produce.mjs':Buffer.from("import './dependency.mjs';"),
    'source/scripts/dependency.mjs':Buffer.from('export const value=1;'),
    'source/benchmarks/answer.txt':Buffer.from('Historical answer.'),
    'source/answer.txt':Buffer.from('Reusable required input template.'),
    'source/reference.txt':Buffer.from('Unclassified reference.'),
  };
  const snapshot={workflow:build.workflow,resources:prepareResources(resources).manifest,provenance:build.provenance,import_report:build.import_report};
  const pack={...snapshot,revision_hash:revisionHash(snapshot)},sections=sourceSectionInventory(resources);
  const requirements=[...observedSourceRequirements(resources,{source_resource_policy:true}),...callableSourceRequirements(resources)];
  const plan={contract:SEMANTIC_BLUEPRINT_CONTRACT,purpose:'Preserve the original production work.',
    source_dispositions:sections.map(section=>({section_id:section.section_id,disposition:'workflow',activity_keys:['produce'],note:'Original procedure.'})),
    requirement_assignments:[...new Set(requirements.map(item=>item.requirement_id))].map(requirement_id=>({requirement_id,activity_keys:['produce']})),
    runtime_dependencies:[],records:[],lists:[],enums:[],activities:[{key:'produce',instructions:'Use the original production entrypoint and required inputs.',profile:'worker_write',
      source_sections:sections.map(section=>section.section_id),inputs:[{name:'task',from:'input:task'}],outputs:[{name:'result',kind:'text',values:[],type_ref:''}],tool:''}],
    approvals:[],sequences:[],parallels:[],choices:[]};
  const compiled=new WorkflowForge().compile({pack,resources,blueprint:plan,context:{providers,routing_rules:routing}}).compiled;
  assert.equal(compiled.validation.valid,true);
  return compiled.workflow.nodes.find(node=>node.origin?.semantic_key==='produce').resources;
}

test('same retained section excludes explicitly historical non-input evidence while retaining executable import closure',()=>{
  const resources=compileSource('Use `node scripts/produce.mjs --stdin`.\nHistorical benchmark example `benchmarks/answer.txt` is not an execution input.');
  assert(resources.includes('source/scripts/produce.mjs'));
  assert(resources.includes('source/scripts/dependency.mjs'));
  assert(!resources.includes('source/benchmarks/answer.txt'));
});

test('an answer-named resource explicitly used as an input template remains a runtime resource',()=>{
  const resources=compileSource('Use `node scripts/produce.mjs --stdin`.\nUse `answer.txt` as the required input template.');
  assert(resources.includes('source/answer.txt'));
});

test('positive runtime evidence in a separate paragraph overrides an archive occurrence for the same resource',()=>{
  const resources=compileSource('Historical benchmark example `benchmarks/answer.txt` is not an execution input.\n\nUse `benchmarks/answer.txt` as the required input template.');
  assert(resources.includes('source/benchmarks/answer.txt'));
});

test('positive runtime evidence within the same paragraph is retained independently of negative reference evidence',()=>{
  const resources=compileSource('Historical benchmark example `answer.txt` is not an execution input. Use `answer.txt` as the required input template.\nMention `reference.txt` without assigning its runtime role.');
  assert(resources.includes('source/answer.txt'));
  assert(resources.includes('source/reference.txt'),'ambiguous source references retain existing inclusion semantics');
});

test('each occurrence reports its source evidence and a direct prohibition does not create a runtime input',()=>{
  const source='Do not read `benchmarks/answer.txt`.\n\nUse `benchmarks/answer.txt` as the required input template.';
  const [entry]=sourceResourceMentions(source,['source/benchmarks/answer.txt']);
  assert.equal(entry.retained,true);
  assert.deepEqual(entry.mentions.map(mention=>mention.disposition),['non_runtime_reference','runtime']);
  assert.deepEqual(entry.mentions.map(mention=>source.slice(mention.from,mention.to)),['benchmarks/answer.txt','benchmarks/answer.txt']);
  assert.equal(entry.mentions[0].evidence,'Do not read `benchmarks/answer.txt`.');
  assert.equal(entry.mentions[1].evidence,'Use `benchmarks/answer.txt` as the required input template.');
  assert.equal(sourceResourceMentions(source.split('\n\n')[0],['source/benchmarks/answer.txt'])[0].retained,false);
});

test('a neighboring historical resource cannot exclude an ambiguous occurrence in the same sentence',()=>{
  const source='Mention `reference.txt` and historical benchmark example `benchmarks/answer.txt` is not an execution input.';
  const entries=sourceResourceMentions(source,['source/reference.txt','source/benchmarks/answer.txt']);
  assert.equal(entries[0].retained,true);
  assert.equal(entries[0].mentions[0].disposition,'ambiguous');
  assert.equal(entries[1].retained,false);
});

test('explicit historical list scope supports CRLF and ends at a new paragraph',()=>{
  const source='Historical benchmark examples, not execution inputs:\r\n- `benchmarks/answer.txt`\r\n- `reference.txt`\r\n\r\nUse `answer.txt` as the required input template.';
  const entries=sourceResourceMentions(source,['source/benchmarks/answer.txt','source/reference.txt','source/answer.txt']);
  assert.equal(entries[0].retained,false);
  assert.equal(entries[1].retained,false);
  assert.equal(entries[1].mentions[0].scope_evidence,'Historical benchmark examples, not execution inputs:');
  assert.equal(entries[2].retained,true);
});

test('non-runtime phrases inside code data do not become prose resource exclusions',()=>{
  const [entry]=sourceResourceMentions('Example payload:\n```json\n{"path":"answer.txt","note":"not an execution input"}\n```',['source/answer.txt']);
  assert.equal(entry.retained,true);
  assert.equal(entry.mentions[0].disposition,'ambiguous');
});

test('full and source-relative aliases share one occurrence while backslash references retain their meaning',()=>{
  const [entry]=sourceResourceMentions('Use `source\\benchmarks\\answer.txt` as the required input template.',['source/benchmarks/answer.txt']);
  assert.equal(entry.retained,true);
  assert.equal(entry.mentions.length,1);
  assert.equal(entry.mentions[0].disposition,'runtime');
  assert.equal(entry.mentions[0].evidence,'Use `source\\benchmarks\\answer.txt` as the required input template.');
});

test('comma-separated declarations keep each resource role local',()=>{
  const entries=sourceResourceMentions('Mention `reference.txt`, historical benchmark example `benchmarks/answer.txt` is not an execution input.',['source/reference.txt','source/benchmarks/answer.txt']);
  assert.equal(entries[0].retained,true);
  assert.equal(entries[1].retained,false);
  const uses=sourceResourceMentions('Read `reference.txt`, historical benchmark example `benchmarks/answer.txt` is not an execution input.',['source/reference.txt','source/benchmarks/answer.txt']);
  assert.equal(uses[0].retained,true);
  assert.equal(uses[1].retained,false);
});

test('a trailing explicit non-input qualifier stays attached to its reference use',()=>{
  for(const conjunction of [',',' but']){
    const [entry]=sourceResourceMentions(`Use \`answer.txt\` for comparison${conjunction} not an execution input.`,['source/answer.txt']);
    assert.equal(entry.retained,false);
    assert.equal(entry.mentions[0].disposition,'non_runtime_reference');
  }
});

test('positive input binding under a historical list label still remains an input',()=>{
  const [entry]=sourceResourceMentions('Historical benchmark examples, not execution inputs:\n- Read `benchmarks/answer.txt` as the required input template.',['source/benchmarks/answer.txt']);
  assert.equal(entry.retained,true);
  assert.equal(entry.mentions[0].disposition,'runtime');
});

test('the original historical-answer reproduction is excluded while explicit input use is retained',()=>{
  const phrase='For example, benchmarks/answer.txt shows a historical answer; it is not an execution input.';
  assert.equal(sourceResourceMentions(phrase,['source/benchmarks/answer.txt'])[0].retained,false);
  assert.equal(sourceResourceMentions(`${phrase}\n\nRead \`benchmarks/answer.txt\` as the required input template.`,['source/benchmarks/answer.txt'])[0].retained,true);
});
