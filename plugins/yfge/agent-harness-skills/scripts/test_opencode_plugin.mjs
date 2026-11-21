import assert from 'node:assert/strict';
import test from 'node:test';

import AgentHarnessSkillsPlugin from '../.opencode/plugins/agent-harness-skills.js';

test('injects startup bootstrap context after the OpenCode system header', async () => {
  const plugin = await AgentHarnessSkillsPlugin();
  const transform = plugin['experimental.chat.system.transform'];
  const output = { system: ['opencode header', 'existing system body'] };

  assert.equal(typeof transform, 'function');

  await transform({ sessionID: 'session-1' }, output);

  assert.equal(output.system[0], 'opencode header');
  assert.match(output.system[1], /agent-harness-skills:bootstrap:v1/);
  assert.match(output.system[1], /repo-harness-assessment/);
  assert.match(output.system[1], /OpenCode's native skill tool/);
  assert.equal(output.system[2], 'existing system body');
});

test('does not duplicate bootstrap context when the hook sees an already-injected prompt', async () => {
  const plugin = await AgentHarnessSkillsPlugin();
  const transform = plugin['experimental.chat.system.transform'];
  const output = { system: ['opencode header'] };

  await transform({ sessionID: 'session-2' }, output);
  await transform({ sessionID: 'session-2' }, output);

  const injectedCount = output.system.filter((part) =>
    part.includes('agent-harness-skills:bootstrap:v1')
  ).length;
  assert.equal(injectedCount, 1);
});

