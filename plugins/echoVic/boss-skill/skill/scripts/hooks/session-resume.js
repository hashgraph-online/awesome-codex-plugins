import fs from 'node:fs';
import path from 'node:path';
import { normalizeHookInput } from './lib/normalize-input.js';

function run(rawInput) {
  const input = normalizeHookInput(rawInput);
  if (!input) return '';
  const cwd = input.cwd;

  if (!cwd) return '';

  const bossDir = path.join(cwd, '.boss');
  if (!fs.existsSync(bossDir)) return '';

  let entries;
  try {
    entries = fs.readdirSync(bossDir, { withFileTypes: true });
  } catch (err) {
    process.stderr.write('[boss-skill] session-resume/readdirSync: ' + err.message + '\n');
    return '';
  }

  let pendingFeatures = '';

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const execJsonPath = path.join(bossDir, entry.name, '.meta', 'execution.json');
    if (!fs.existsSync(execJsonPath)) continue;

    let data;
    try {
      data = JSON.parse(fs.readFileSync(execJsonPath, 'utf8'));
    } catch (err) {
      process.stderr.write('[boss-skill] session-resume/readExecJson: ' + err.message + '\n');
      continue;
    }

    const status = data.status || 'unknown';
    const feature = data.feature || entry.name;

    if (status === 'running' || status === 'initialized' || status === 'failed') {
      let nextStage = 'done';
      const stages = data.stages || {};
      for (const sKey of Object.keys(stages).sort((a, b) => Number(a) - Number(b))) {
        const sStatus = (stages[sKey] || {}).status || 'unknown';
        if (sStatus === 'pending' || sStatus === 'running' || sStatus === 'failed') {
          nextStage = sKey;
          break;
        }
      }
      pendingFeatures += `  - ${feature} (status: ${status}, next stage: ${nextStage})\n`;
    }
  }

  if (!pendingFeatures) return '';

  let context = `[Boss Harness] 会话恢复。未完成的流水线:\n${pendingFeatures}`;
  context += '\n使用 /boss <feature> --continue-from <stage> 继续。';

  const sessionStatePath = path.join(cwd, '.boss', '.session-state.json');
  let previousSession = null;
  if (fs.existsSync(sessionStatePath)) {
    try {
      previousSession = JSON.parse(fs.readFileSync(sessionStatePath, 'utf8'));
      context += '\n[Boss Harness] 已加载上次会话状态';
    } catch (err) {
      process.stderr.write('[boss-skill] session-resume/readSessionState: ' + err.message + '\n');
    }
  }

  const result = {
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext: context,
    },
  };

  if (previousSession) {
    result.hookSpecificOutput.previousSessionState = previousSession;
  }

  return JSON.stringify(result);
}

export { run };
