import assert from 'node:assert/strict';
import test from 'node:test';
import { callableInventory, callableCoverageIssues } from '../lib/skill-import/callable-inventory.mjs';

const resources = entries => Object.fromEntries(Object.entries(entries).map(([key, value]) => [key, Buffer.from(value)]));
const skill = text => resources({ 'source/SKILL.md': text });

test('same-line calls retain separate exact identities and literal CLI transports', () => {
  const bundle = resources({
    'source/SKILL.md': '# Skill\n## Workflow\nRun `python scripts/build.py --mode fast < input.json > output.json`; run `python scripts/build.py --mode slow`.\n',
    'source/scripts/build.py': 'import argparse\np = argparse.ArgumentParser()\np.add_argument("--mode", choices=["fast", "slow"])\n',
  });
  const found = callableInventory(bundle);
  assert.equal(found.callsites.length, 2);
  const [first, second] = found.callsites;
  assert.notEqual(first.callsite_id, second.callsite_id);
  assert.equal(first.classification, 'exact_call');
  assert.equal(first.authority, 'required');
  assert.equal(first.target_resource, 'source/scripts/build.py');
  assert.deepEqual(first.interface.argv, ['scripts/build.py', '--mode', 'fast']);
  assert.deepEqual(first.interface.stdin, { kind: 'file', path: 'input.json' });
  assert.deepEqual(first.interface.files, [{ direction: 'write', path: 'output.json' }]);
  assert.equal(first.source_contract_ids.length, 1);
  assert.equal(first.source_span.start_line, 3);
  assert.equal(first.source_quote, 'python scripts/build.py --mode fast < input.json > output.json');
  assert.equal(bundle[first.source_span.resource].subarray(first.source_location.start_byte, first.source_location.end_byte).toString(), first.source_quote);
  const proposal = {nodes:[{id:'build',resource_refs:[first.target_resource]}],requirement_mappings:[{requirement_id:first.callsite_id,resource_refs:[first.target_resource],node_ids:['build']}]};
  assert.equal(callableCoverageIssues(found, proposal).filter(item => item.code === 'CALLABLE_COVERAGE_MISSING').length, 1);
  proposal.requirement_mappings.push({requirement_id:second.callsite_id,resource_refs:[second.target_resource],node_ids:['build']});
  assert.deepEqual(callableCoverageIssues(found, proposal), []);
});

test('examples optional triggers and incidental package scripts never become unconditional roots', () => {
  const found = callableInventory(resources({
    'source/SKILL.md': '# Skill\n## Workflow\nIf the user requests export, run `node scripts/export.mjs --file scene.json`.\n## Examples\nFor example: `node scripts/demo.mjs`.\n',
    'source/package.json': '{"scripts":{"test":"node scripts/missing.mjs"},"dependencies":{"unused":"1"}}',
    'source/scripts/export.mjs': 'export const ready = true;',
    'source/scripts/demo.mjs': 'import unused from "unused";',
  }));
  assert.equal(found.callsites.find(item => item.source_quote.startsWith('node scripts/export')).authority, 'conditional');
  assert.equal(found.callsites.find(item => item.source_quote.startsWith('node scripts/demo')).authority, 'example');
  assert.equal(found.callsites.find(item => item.origin === 'package_script').classification, 'candidate');
  assert.equal(found.packages.length, 0);
  assert.equal(found.unresolved.length, 0);
});

test('transitive JS imports and process aliases preserve provenance without executing source', () => {
  const found = callableInventory(resources({
    'source/WORKFLOW.md': '# Brief\nRun `node scripts/main.mjs --input task.json`.\n',
    'source/package.json': '{"dependencies":{"kleur":"^4.1.5"}}',
    'source/scripts/main.mjs': 'import {spawn as launch} from "node:child_process";\nimport "./helper.mjs";\nlaunch("python", ["scripts/child.py", "--json", "task.json"]);\n// launch("node", ["fake.mjs"]);\nconst documentation = "launch(unknown)";\n',
    'source/scripts/helper.mjs': 'import kleur from "kleur";\nimport "./leaf.mjs";',
    'source/scripts/leaf.mjs': 'export const leaf = true;',
    'source/scripts/child.py': 'from . import local\nimport requests\n',
    'source/scripts/local.py': 'import json\n',
  }));
  assert.equal(found.callsites.filter(item => item.origin === 'process_call').length, 1);
  assert.ok(found.imports.some(item => item.target_resource === 'source/scripts/leaf.mjs'));
  assert.ok(found.imports.some(item => item.target_resource === 'source/scripts/local.py'));
  assert.ok(found.packages.some(item => item.name === 'kleur' && item.version === '^4.1.5'));
  assert.ok(found.packages.some(item => item.name === 'requests'));
  const root = found.callsites.find(item => item.origin === 'markdown');
  assert.ok(found.imports.find(item => item.target_resource === 'source/scripts/leaf.mjs').reached_by_callsite_ids.includes(root.callsite_id));
  assert.ok(found.callsites.find(item => item.origin === 'process_call').reached_by_callsite_ids.includes(root.callsite_id));
  assert.equal(found.unresolved.length, 0);
});

test('dynamic process arguments and imports expose exact unknown evidence', () => {
  const found = callableInventory(resources({
    'source/SKILL.md': 'Run `node scripts/main.mjs`.\n',
    'source/scripts/main.mjs': 'import {spawn} from "node:child_process";\nspawn(command, args);\nimport(moduleName);\n',
  }));
  assert.ok(found.unresolved.some(item => item.code === 'DYNAMIC_PROCESS_CALL' && item.source_quote === 'spawn(command, args)'));
  assert.ok(found.unresolved.some(item => item.code === 'DYNAMIC_IMPORT' && item.source_quote === 'import(moduleName)'));
  assert.ok(found.limitations.length);
});

test('tools retain exact qualified names and distinct invocation authority', () => {
  const found = callableInventory(skill('## Workflow\nCall `mcp__draw__render` with scene input; then call `mcp__draw__export`.\n## Examples\nExample: `mcp__draw__help`.\n'));
  assert.equal(found.callsites.filter(item => item.kind === 'tool').length, 3);
  assert.equal(found.callsites[0].interface.tool, 'mcp__draw__render');
  assert.equal(found.callsites[0].interface.mcp_server, 'draw');
  const render = found.callsites[0];
  assert.ok(callableCoverageIssues(found, {requirement_mappings:[{requirement_id:render.callsite_id,node_ids:['render']}],nodes:[{id:'render',tool:'mcp__draw__export'}]}).some(item => item.code === 'CALLABLE_COVERAGE_TARGET'));
  const proposal = {requirement_mappings:found.callsites.filter(item => item.actionable).map(item => ({requirement_id:item.callsite_id,node_ids:['agent'],status:'agent_assisted'})),nodes:[{id:'agent',type:'agent',requirement_ids:found.callsites.filter(item => item.actionable).map(item => item.callsite_id)}]};
  assert.deepEqual(callableCoverageIssues(found, proposal), []);
});

test('Unicode spans hash exact bytes and deterministic inventory does not mutate resources', () => {
  const bundle = resources({'source/SKILL.md':'# 文档\n必须运行 `python scripts/a.py --name "中文"`。\n','source/scripts/a.py':'print("test")\n'});
  const before = bundle['source/SKILL.md'].toString();
  const one = callableInventory(bundle), two = callableInventory(bundle);
  assert.deepEqual(one, two);
  const call = one.callsites[0];
  assert.equal(bundle[call.resource].subarray(call.source_location.start_byte, call.source_location.end_byte).toString(), call.source_quote);
  assert.equal(bundle['source/SKILL.md'].toString(), before);
});

test('runnable fences nested paths and missing local imports preserve bounded runtime facts', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'# Skill\n## Workflow\nRun this command:\n```sh\nnode lib/nested/main.mjs --config "<configuration.json>"\n```\n',
    'source/lib/nested/main.mjs':'import fs from "fs";\nimport "./absent.mjs";\n',
  }));
  const call = found.callsites[0];
  assert.equal(call.classification, 'exact_call');
  assert.equal(call.authority, 'required');
  assert.equal(call.target_resource, 'source/lib/nested/main.mjs');
  assert.deepEqual(call.interface.argv, ['lib/nested/main.mjs','--config','<configuration.json>']);
  assert.equal(found.packages.length, 0);
  assert.ok(call.runtime_dependencies.some(item => item.kind === 'local_import' && item.status === 'missing'));
  assert.ok(found.unresolved.some(item => item.code === 'MISSING_LOCAL_IMPORT' && item.callsite_id === call.callsite_id));
});

test('same-section auxiliary examples and prohibited guidance do not hide or require runnable calls', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'# Skill\n## Workflow\nExample: `node scripts/missing.mjs`.\nDo not run:\n```sh\nnode scripts/prohibited.mjs\n```\nRun `node scripts/real.mjs`.\n',
    'source/references/example.md':'Run `python missing.py`.\n',
    'source/scripts/real.mjs':'export const ready = true;\n',
  }));
  assert.equal(found.callsites.find(item => item.source_quote.includes('missing.mjs')).authority, 'example');
  assert.equal(found.callsites.find(item => item.source_quote.includes('prohibited')).classification, 'candidate');
  assert.equal(found.callsites.find(item => item.resource.includes('references/')).authority, 'source_observation');
  assert.equal(found.unresolved.length, 0);
});

test('literal generic process executables and literal stdin keep their original interface', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'Run `node scripts/main.cjs`.\n',
    'source/scripts/main.cjs':'const {execFileSync: launch} = require("child_process");\nlaunch("pandoc", ["--from", "markdown"], {input: "# title"});\n',
  }));
  const call = found.callsites.find(item => item.origin === 'process_call');
  assert.equal(call.interface.executable, 'pandoc');
  assert.deepEqual(call.interface.argv, ['--from','markdown']);
  assert.deepEqual(call.interface.stdin, {kind:'literal',value:'# title'});
  assert.equal(found.unresolved.length, 0);
  assert.equal(found.packages.length, 0);
});

test('dynamic arguments retain the fixed process target and unknown expressions', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'Run `node scripts/main.mjs`.\n',
    'source/scripts/main.mjs':'import {spawn} from "node:child_process";\nspawn(process.execPath, ["scripts/child.mjs", taskPath]);\n',
    'source/scripts/child.mjs':'import "./leaf.mjs";\n',
    'source/scripts/leaf.mjs':'export const leaf = true;\n',
  }));
  const call = found.callsites.find(item => item.origin === 'process_call');
  assert.equal(call.target_resource, 'source/scripts/child.mjs');
  assert.equal(call.interface.status, 'unresolved');
  assert.ok(call.interface.argv_expressions.includes('taskPath'));
  assert.ok(found.callsites.find(item => item.origin === 'markdown').resolved_resource_refs.includes('source/scripts/leaf.mjs'));
  assert.ok(found.unresolved.some(item => item.code === 'DYNAMIC_PROCESS_CALL'));
});

test('string concatenation is unresolved and regex documentation is never a process call', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'Run `node scripts/main.mjs`.\n',
    'source/scripts/main.mjs':'import {spawn} from "child_process";\nconst sample = /spawn(command, args)/;\nspawn("py" + "thon", ["scripts/a.py"]);\n',
  }));
  assert.equal(found.callsites.filter(item => item.origin === 'process_call').length, 1);
  assert.ok(found.unresolved.some(item => item.code === 'DYNAMIC_PROCESS_CALL'));
  assert.equal(found.callsites.find(item => item.origin === 'process_call').interface.status, 'unresolved');
});

test('coverage cannot map only the root while omitting transitive runtime resources', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'Run `node scripts/main.mjs`.\n',
    'source/scripts/main.mjs':'import "./helper.mjs";\n',
    'source/scripts/helper.mjs':'export const helper = true;\n',
  }));
  const call = found.callsites.find(item => item.actionable), proposal = {requirement_mappings:[{requirement_id:call.callsite_id,node_ids:['work'],resource_refs:[call.target_resource]}],nodes:[{id:'work',type:'agent',resource_refs:[call.target_resource]}]};
  assert.ok(callableCoverageIssues(found,proposal).some(item => item.resource === 'source/scripts/helper.mjs'));
  proposal.requirement_mappings[0].resource_refs = call.resolved_resource_refs;
  proposal.nodes[0].resource_refs = call.resolved_resource_refs;
  assert.deepEqual(callableCoverageIssues(found,proposal),[]);
});

test('required-section lexical script and tool mentions remain candidates', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'# Skill\n## Workflow\nThe interface lives in `scripts/missing.py`; the service exposes `mcp__scene__unused`.\nRun `python scripts/real.py`.\n',
    'source/scripts/real.py':'print("real")\n',
  }));
  assert.equal(found.callsites.find(item => item.source_quote === 'scripts/missing.py').classification,'candidate');
  assert.equal(found.callsites.find(item => item.source_quote === 'mcp__scene__unused').classification,'candidate');
  assert.equal(found.callsites.filter(item => item.actionable).length,1);
  assert.equal(found.unresolved.length,0);
});

test('an imported exec alias retains its command semantics rather than spawn argv semantics', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'Run `node scripts/main.mjs`.\n',
    'source/scripts/main.mjs':'import {execSync as execute} from "node:child_process";\nexecute("python scripts/child.py --json input.json");\n',
    'source/scripts/child.py':'print("child")\n',
  }));
  const call = found.callsites.find(item => item.origin === 'process_call');
  assert.equal(call.target_resource,'source/scripts/child.py');
  assert.deepEqual(call.interface.argv,['scripts/child.py','--json','input.json']);
  assert.equal(found.unresolved.length,0);
});

test('only an explicitly selected npm script contributes its runtime closure', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'Run `npm run build`.\n',
    'source/package.json':'{"scripts":{"build":"node lib/build.mjs","test":"node missing.mjs"}}',
    'source/lib/build.mjs':'import "./helper.mjs";\n',
    'source/lib/helper.mjs':'export const helper = true;\n',
  }));
  const call = found.callsites.find(item => item.actionable);
  assert.deepEqual(call.resolved_resource_refs,['source/lib/build.mjs','source/lib/helper.mjs','source/package.json']);
  assert.ok(call.runtime_dependencies.some(item => item.name === 'node'));
  assert.equal(found.unresolved.length,0);
});

test('composite shell process expressions expose the unparsed remainder', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'Run `node scripts/main.mjs`.\n',
    'source/scripts/main.mjs':'import {execSync} from "node:child_process";\nexecSync("node scripts/a.mjs && node scripts/b.mjs");\n',
    'source/scripts/a.mjs':'export const a = true;\n',
    'source/scripts/b.mjs':'export const b = true;\n',
  }));
  const call = found.callsites.find(item => item.origin === 'process_call');
  assert.equal(call.interface.shell_tail,'&& node scripts/b.mjs');
  assert.ok(found.unresolved.some(item => item.code === 'COMPOSITE_SHELL_COMMAND'));
});

test('source-declared CLI aliases and the Skill directory bind literal call variants to pinned bytes', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'---\ndescription: Use `/skill config` to configure.\n---\n# Skill\n## 用户要改配置时\n- `config`：运行 `am config`。\n- `config <键> <值>`：运行 `am config set <键> <值>`。\n## 工作流\n下文的 `am` 都指：\n```bash\nnode "${CLAUDE_SKILL_DIR}/scripts/am.mjs"\n```\n完整说明：`am help format`。\n',
    'source/scripts/am.mjs':'export const ready = true;\n',
  }));
  const actions = found.callsites.filter(item => item.actionable);
  assert.deepEqual(actions.map(item=>item.source_quote),['am config','am config set <键> <值>','am help format']);
  assert.ok(actions.every(item=>item.target_resource==='source/scripts/am.mjs'));
  assert.equal(actions[0].authority,'conditional');
  assert.deepEqual(actions[1].interface.argv,['${CLAUDE_SKILL_DIR}/scripts/am.mjs','config','set','<键>','<值>']);
  assert.ok(actions.every(item=>item.resolved_resource_refs.includes('source/scripts/am.mjs')));
  assert.equal(found.unresolved.length,0);
  assert.equal(found.callsites.filter(item=>item.kind==='tool').length,0);
});

test('four-backtick shell heredocs preserve stdin through nested markup fences', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'# Skill\n## 工作流\n用 heredoc 渲染：\n````bash\nnode "${CLAUDE_SKILL_DIR}/scripts/am.mjs" render - <<\'AM_EOF\'\n## Scene\n```flow\nA -> B\n```\nAM_EOF\n````\n完整用法：`am help patch`。\n',
    'source/scripts/am.mjs':'export const ready = true;\n',
  }));
  const render = found.callsites.find(item=>item.source_quote.startsWith('node '));
  assert.equal(render.actionable,true);
  assert.equal(render.target_resource,'source/scripts/am.mjs');
  assert.deepEqual(render.interface.argv,['${CLAUDE_SKILL_DIR}/scripts/am.mjs','render','-']);
  assert.equal(render.interface.stdin.kind,'heredoc');
  assert.equal(render.interface.stdin.delimiter,'AM_EOF');
  assert.equal(render.interface.stdin.body,'## Scene\n```flow\nA -> B\n```\n');
  assert.equal(found.unresolved.length,0);
});

test('a source-only trigger persists across paragraphs to its callable variant', () => {
  const found = callableInventory(resources({
    'source/SKILL.md':'# Skill\n下文的 `am` 都指：\n```sh\nnode "${CLAUDE_SKILL_DIR}/scripts/am.mjs"\n```\n## 视频\n只在用户明确要视频时使用。\n\n视频内容格式相同。\n\n```sh\nnode "${CLAUDE_SKILL_DIR}/scripts/am.mjs" video -\n```\n## 配置\n用户提出设置时，同样换算成 `am config set`。\n',
    'source/scripts/am.mjs':'export const ready = true;\n',
  }));
  const video=found.callsites.find(item=>item.interface.argv?.includes('video'));
  assert.equal(video.authority,'conditional');
  assert.match(video.trigger,/只在用户明确要视频时使用/);
  const config=found.callsites.find(item=>item.source_quote==='am config set');
  assert.equal(config.actionable,true);
});

test('tool argument transport retains exact JSON and explicit unresolved opaque expressions', () => {
  const bundle=skill('## Workflow\nCall `mcp__draw__render({"theme":"dark","width":1000})`; call `mcp__draw__render(makePayload() || fallback)`; call `mcp__draw__render({"width":})`.\n');
  const found=callableInventory(bundle), actions=found.callsites.filter(item=>item.actionable);
  assert.equal(actions.length,3);
  const [literal,dynamic,malformed]=actions;
  assert.equal(literal.interface.arguments_expression,'{"theme":"dark","width":1000}');
  assert.equal(literal.interface.arguments_transport,'literal_json');
  assert.deepEqual(literal.interface.arguments,{theme:'dark',width:1000});
  assert.equal(bundle['source/SKILL.md'].subarray(literal.interface.arguments_source_location.start_byte,literal.interface.arguments_source_location.end_byte).toString(),literal.interface.arguments_expression);
  assert.equal(dynamic.interface.arguments_expression,'makePayload() || fallback');
  assert.equal(dynamic.interface.arguments_transport,'opaque_expression');
  assert.equal(dynamic.interface.status,'unresolved');
  assert.equal(malformed.interface.arguments_expression,'{"width":}');
  assert.equal(found.unresolved.filter(item=>item.code==='UNRESOLVED_TOOL_ARGUMENTS').length,2);
});

test('pipeline segments preserve original transport and pipe stdin identity without executable source command', () => {
  const found=callableInventory(resources({'source/SKILL.md':'Run `node scripts/produce.mjs | node scripts/consume.mjs`.\n','source/scripts/produce.mjs':'export const p=true;','source/scripts/consume.mjs':'export const c=true;'}));
  const [producer,consumer]=found.callsites.filter(item=>item.actionable);
  assert.notEqual(producer.callsite_id,consumer.callsite_id);
  assert.equal(producer.interface.composite_transport.composite_id,consumer.interface.composite_transport.composite_id);
  assert.equal(producer.interface.composite_transport.source_quote,'node scripts/produce.mjs | node scripts/consume.mjs');
  assert.equal(producer.interface.composite_transport.transport_status,'authoring_only');
  assert.equal(consumer.interface.composite_transport.connector_before,'|');
  assert.deepEqual(consumer.interface.stdin,{kind:'pipeline',source_callsite_id:producer.callsite_id,composite_id:producer.interface.composite_transport.composite_id});
  assert.equal(consumer.interface.composite_transport.previous_callsite_id,producer.callsite_id);
  assert.equal(producer.interface.composite_transport.next_callsite_id,consumer.callsite_id);
  assert.equal(producer.interface.shell_command,undefined);
  assert.equal(found.unresolved.length,0);
});

test('guarded shell connectors retain conditional downstream identities while semicolon retains sequencing', () => {
  const found=callableInventory(resources({'source/SKILL.md':'Run `node scripts/a.mjs && node scripts/b.mjs || node scripts/c.mjs; node scripts/d.mjs`.\n',...Object.fromEntries(['a','b','c','d'].map(name=>[`source/scripts/${name}.mjs`,'export const x=true;']))}));
  const [a,b,c,d]=found.callsites.filter(item=>item.actionable);
  assert.equal(a.authority,'required');
  assert.equal(b.authority,'conditional');
  assert.equal(c.authority,'conditional');
  assert.equal(d.authority,'required');
  assert.equal(b.interface.composite_transport.connector_before,'&&');
  assert.equal(c.interface.composite_transport.connector_before,'||');
  assert.equal(d.interface.composite_transport.connector_before,';');
  assert.match(b.trigger,/&&/);
  assert.match(c.trigger,/\|\|/);
});

test('unrecognized pipeline source is explicit and quoted operators stay ordinary argv or JSON', () => {
  const found=callableInventory(resources({'source/SKILL.md':'Run `make_payload | node scripts/consume.mjs --name "|"`; call `mcp__draw__render({"label":"a|b"})`.\n','source/scripts/consume.mjs':'export const c=true;'}));
  const consume=found.callsites.find(item=>item.target_resource==='source/scripts/consume.mjs');
  assert.deepEqual(consume.interface.argv,['scripts/consume.mjs','--name','|']);
  assert.equal(consume.interface.composite_transport.segment_count,2);
  assert.ok(found.unresolved.some(item=>item.code==='UNRESOLVED_COMPOSITE_SEGMENT'));
  assert.equal(found.callsites.find(item=>item.kind==='tool').interface.arguments.label,'a|b');
});
