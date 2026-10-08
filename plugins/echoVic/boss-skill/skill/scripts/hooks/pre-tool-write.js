import fs from 'node:fs';
import path from 'node:path';

import {
  getReadyArtifacts,
  loadArtifactDag,
  resolveArtifactDagPath,
  STAGE_MAP,
} from '../lib/boss-utils.js';
import { normalizeHookInput } from './lib/normalize-input.js';

function classifyWriteDecision(filePath, cwd) {
  if (!filePath) return '';

  if (filePath.includes('.boss/') && filePath.endsWith('execution.json')) {
    return JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason:
          'execution.json 由 runtime 事件流管理，不允许直接编辑。请使用 boss runtime update-stage 或其他 runtime CLI',
      },
    });
  }

  if (!filePath.includes('.boss/')) {
    return '';
  }

  const match = filePath.match(/\.boss\/([^/]+)\//);
  const artifact = path.basename(filePath);

  if (match) {
    const feature = match[1];
    const execJsonPath = path.join(cwd, '.boss', feature, '.meta', 'execution.json');

    if (fs.existsSync(execJsonPath)) {
      const expectedStage = STAGE_MAP[artifact];

      if (expectedStage !== undefined) {
        let data;
        try {
          data = JSON.parse(fs.readFileSync(execJsonPath, 'utf8'));
        } catch (err) {
          process.stderr.write('[boss-skill] pre-tool-write/readExecJson: ' + err.message + '\n');
          return '';
        }

        const stages = data.stages || {};
        const stage = stages[String(expectedStage)] || {};
        const stageStatus = stage.status || 'unknown';

        if (stageStatus !== 'running' && stageStatus !== 'retrying') {
          const dagPath = resolveArtifactDagPath(cwd);
          const dag = dagPath ? loadArtifactDag(dagPath) : null;
          if (dag && dag.artifacts && dag.artifacts[artifact]) {
            const ready = getReadyArtifacts(dag, data, data.parameters || {});
            const isReady = ready.some((r) => r.artifact === artifact);
            if (isReady) {
              return '';
            }
          }

          return JSON.stringify({
            hookSpecificOutput: {
              hookEventName: 'PreToolUse',
              permissionDecision: 'deny',
              permissionDecisionReason: `产物 ${artifact} 属于阶段 ${expectedStage}，但该阶段状态为 ${stageStatus}（非 running）。请先通过 boss runtime update-stage 将对应阶段置为 running/retrying，或按产物 DAG 进入可写状态后再写入。`,
            },
          });
        }
      }
    }
  }

  return '';
}

function askForUnparsedPatch() {
  return JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason:
        '[boss-skill] apply_patch payload 未能解析出目标文件。为避免绕过 .boss 产物护栏，请使用标准 apply_patch 文件头后重试。',
    },
  });
}

function run(rawInput) {
  const input = normalizeHookInput(rawInput);
  if (!input) return '';
  const filePaths = input.filePaths;
  const cwd = input.cwd;

  if (filePaths.length === 0) {
    if (input.toolName === 'apply_patch' && input.patch && input.patch.includes('.boss/')) {
      return askForUnparsedPatch();
    }
    return '';
  }

  for (const filePath of filePaths) {
    const decision = classifyWriteDecision(filePath, cwd);
    if (!decision) continue;
    const parsed = JSON.parse(decision);
    if (parsed.hookSpecificOutput?.permissionDecision === 'deny') {
      return decision;
    }
  }

  return '';
}

export { run };
