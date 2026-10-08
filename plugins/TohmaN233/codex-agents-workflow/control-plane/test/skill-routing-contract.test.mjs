import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { defaultRoutingRules, routeAgent, validateRoutingRules } from '../lib/skill-import/routing-rules.mjs';

const pluginRoot = join(dirname(fileURLToPath(import.meta.url)), '..', '..');

test('workflow-control-plane reserves Runs for concrete execution intent', async () => {
  const skill = await readFile(join(pluginRoot, 'skills', 'control-plane', 'SKILL.md'), 'utf8');
  const normalized = skill.replace(/\s+/g, ' ');
  const native = await readFile(join(pluginRoot, 'skills', 'control-plane', 'references', 'native-execution.md'), 'utf8');

  assert.match(skill, /persistent control plane/i);
  assert.match(skill, /planning, comparing, auditing, evaluating, or designing experiments/i);
  assert.match(skill, /mentioning this plugin is not\s+permission to start a Run/i);
  assert.match(skill, /call\s+`workflow_route` with the concrete task/i);
  assert.match(normalized, /Start the selected candidate automatically/i);
  assert.match(normalized, /differ materially in outcome, permissions or side effects/i);
  assert.match(normalized, /Do not select by keyword overlap alone\./);
  assert.match(skill, /host already supplies an exact Ready Workflow ID\/revision or a node\s+`agent_packet`/i);
  assert.match(normalized, /host owns launch, node claims, identities, leases, receipts, context projection, completion envelopes, retries and continuation/i);
  assert.match(normalized, /Drafts, retired Role graphs, previous revisions and conversion history are not execution context/i);
  assert.match(normalized, /Host advances deterministic and Main worker work/i);
  assert.match(normalized, /orchestration_handoff.*initiating conversation/i);
  assert.match(normalized, /workflow_orchestration_complete.*newly authored semantic/i);
  assert.match(normalized, /launch its exact `spawn_config` plus `prompt` with `spawn_agent`/i);
  assert.match(normalized, /materializes one local task bundle/i);
  assert.match(native, /must not create an App Server thread or Codex task/i);
  assert.match(native, /records valid\s+items immediately/i);
  assert.match(skill, /converted Workflow is a self-contained replacement for its source Skill/i);
  assert.doesNotMatch(skill,/source\/SKILL\.md/);
  assert.ok(skill.length<6000,'the always-available routing Skill must stay compact');
});

test('plugin starters describe user tasks while routing policy stays in the Skill', async () => {
  const manifest = JSON.parse(await readFile(join(pluginRoot, '.codex-plugin', 'plugin.json'), 'utf8'));
  const pluginPrompt = manifest.interface.defaultPrompt[0];
  const prompt = manifest.interface.defaultPrompt.join(' ');
  const skillUi = await readFile(join(pluginRoot, 'skills', 'control-plane', 'agents', 'openai.yaml'), 'utf8');
  const skillPrompt = skillUi.match(/^\s*default_prompt:\s*"([^"]+)"\s*$/m)?.[1];

  assert.match(pluginPrompt, /open.*workbench/i);
  assert.match(prompt, /Skill.*Workflow/);
  assert.match(prompt, /review.*Role/i);
  assert.doesNotMatch(prompt, /only for matched execution|never planning/i);
  assert.ok(manifest.interface.defaultPrompt.every((value) => value.length <= 128));
  assert.match(skillPrompt, /\$workflow-control-plane/);
  assert.match(skillPrompt, /open.*workbench/i);
  assert.ok(skillPrompt.length <= 128);
});

test('plugin startup enables automatic Workbench Roles without fixed duplicate Agents', async () => {
  const manifest = JSON.parse(await readFile(join(pluginRoot, '.codex-plugin', 'plugin.json'), 'utf8'));
  const skill = await readFile(join(pluginRoot, 'skills', 'orchestration', 'SKILL.md'), 'utf8');
  assert.equal(manifest.skills, './skills/');
  assert.match(skill, /description:.*Automatically use enabled Workbench Roles/i);
  assert.match(skill, /user does not need to ask\s+for a Role or name one/i);
  assert.match(skill, /workflow_role_templates/);
  assert.match(skill, /workflow_role_template/);
  assert.match(skill, /adapter\.spawn_config/);
  assert.match(skill, /longest supported\s+timeout/i);
  assert.match(skill, /Never inject Role instructions into a Workflow node/i);
  const agentFiles = await readdir(join(pluginRoot, 'agents')).catch(error => error.code === 'ENOENT' ? [] : Promise.reject(error));
  assert.deepEqual(agentFiles, []);
});

test('Host routing selects a Provider without injecting a Workbench Role',()=>{
  const providers=[
    {id:'native-luna',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},config:{role:'advisor'}},
    {id:'native-sol',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},config:{role:'advisor'}},
    {id:'native-astra',enabled:true,kind:'native_agent',capabilities:{read:true,write:true},config:{role:'advisor'}},
  ];
  const fixed=validateRoutingRules({...defaultRoutingRules(providers),selection_mode:'fixed'});
  const routed=routeAgent({task_type:'implementation',routing_reason:'Bounded implementation.',execution_target:undefined},fixed,providers);
  assert.equal(routed.executor.provider_id,'native-luna');
  assert.equal(Object.hasOwn(routed,'role_ref'),false);
  fixed.routes.implementation={...fixed.routes.implementation,provider_id:'native-sol'};
  const changed=routeAgent({task_type:'implementation',routing_reason:'Use another model connection.',execution_target:undefined},fixed,providers);
  assert.equal(changed.executor.provider_id,'native-sol');
  assert.equal(Object.hasOwn(changed,'role_ref'),false);
});
