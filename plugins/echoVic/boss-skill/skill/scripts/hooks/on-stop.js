import { findActiveFeature, readExecJson } from '../lib/boss-utils.js';
import { normalizeHookInput } from './lib/normalize-input.js';

function run(rawInput) {
  const input = normalizeHookInput(rawInput);
  if (!input) return '';
  const stopHookActive = input.stopHookActive;
  const cwd = input.cwd;

  if (stopHookActive === true || stopHookActive === 'true') {
    return '';
  }

  const active = findActiveFeature(cwd);
  if (!active) return '';

  const execData = readExecJson(cwd, active.feature);
  if (!execData) return '';

  const pendingStages = [];
  const stages = execData.stages || {};
  for (const sKey of Object.keys(stages).sort((a, b) => Number(a) - Number(b))) {
    const stage = stages[sKey] || {};
    if (stage.status === 'running') {
      const sName = stage.name || 'unknown';
      pendingStages.push(`Stage ${sKey} (${sName}) is still running`);
    }
  }

  if (pendingStages.length === 0) return '';

  let reason = `[Boss Harness] 流水线 '${active.feature}' 有未完成的阶段:\n`;
  for (const info of pendingStages) {
    reason += `  - ${info}\n`;
  }
  reason += '请先完成当前阶段或使用 boss runtime update-stage 更新状态后再停止。';

  return JSON.stringify({
    decision: 'block',
    reason,
  });
}

export { run };
