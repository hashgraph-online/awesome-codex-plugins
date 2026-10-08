import fs from 'node:fs';
import path from 'node:path';
import * as runtime from '../../cli/runtime/application/pipeline.mts';
import { STAGE_MAP } from '../lib/boss-utils.js';
import { emitProgress } from '../lib/progress-emitter.js';
import { normalizeHookInput } from './lib/normalize-input.js';

function hasArtifactInEventLog(eventsPath, artifact, stage) {
  if (!fs.existsSync(eventsPath)) return false;

  try {
    const lines = fs.readFileSync(eventsPath, 'utf8').split('\n').filter(Boolean);
    return lines.some((line) => {
      // 跳过崩溃残留的损坏行，而不是让整个查询降级为 false（会导致工件被重复记录）
      let event;
      try {
        event = JSON.parse(line);
      } catch {
        return false;
      }
      if (event.type === 'ArtifactRecorded' && event.data) {
        return event.data.artifact === artifact && String(event.data.stage) === String(stage);
      }

      if (event.type === 'PipelineInitialized' && event.data && event.data.initialState) {
        const stages = event.data.initialState.stages || {};
        const artifacts = (stages[String(stage)] || {}).artifacts || [];
        return artifacts.includes(artifact);
      }

      return false;
    });
  } catch (err) {
    process.stderr.write('[boss-skill] post-tool-write/readEvents: ' + err.message + '\n');
    return false;
  }
}

function run(rawInput) {
  const input = normalizeHookInput(rawInput);
  if (!input) return '';
  const cwd = input.cwd;
  const recordedArtifacts = [];

  for (const filePath of input.filePaths) {
    if (!filePath.includes('.boss/')) continue;

    const match = filePath.match(/\.boss\/([^/]+)\//);
    const artifact = path.basename(filePath);

    if (!match || !artifact) continue;

    if (
      artifact === 'execution.json' ||
      artifact === 'summary-report.md' ||
      artifact === 'summary-report.json'
    ) {
      continue;
    }

    const feature = match[1];
    const execJsonPath = path.join(cwd, '.boss', feature, '.meta', 'execution.json');
    const eventsPath = path.join(cwd, '.boss', feature, '.meta', 'events.jsonl');

    if (!fs.existsSync(execJsonPath)) continue;

    const stage = STAGE_MAP[artifact];
    if (stage === undefined) continue;

    if (hasArtifactInEventLog(eventsPath, artifact, stage)) continue;

    emitProgress(cwd, feature, {
      type: 'artifact-written',
      data: { artifact, stage },
    });

    try {
      runtime.recordArtifact(feature, artifact, stage, { cwd });
    } catch (err) {
      process.stderr.write('[boss-skill] post-tool-write/materialize: ' + err.message + '\n');
      continue;
    }

    recordedArtifacts.push({ artifact, stage });
  }

  if (recordedArtifacts.length === 0) return '';

  const context = recordedArtifacts
    .map(({ artifact, stage }) => `[Harness] 产物 ${artifact} 已通过事件记录到阶段 ${stage}`)
    .join('\n');

  return JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PostToolUse',
      additionalContext: context,
    },
  });
}

export { run };
