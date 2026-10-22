import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readJsonlTolerant } from '../../infrastructure/fs.mts';
import { projectAgentLifecycle } from './apply-agent.mts';
import { projectConversationLifecycle } from './apply-conversation.mts';
import { projectPipelineLifecycle } from './apply-pipeline.mts';
import { projectPluginLifecycle } from './apply-plugin.mts';
import { projectRevisionLifecycle } from './apply-revision.mts';
import { projectStageLifecycle } from './apply-stage.mts';
import { projectWaveLifecycle } from './apply-wave.mts';
import { finalizeState } from './finalize.mts';
import { defaultExecutionState } from './helpers.mts';
import type { ExecutionState, RuntimeEvent } from './types.mts';
import { validateEvent, validateExecutionState } from './validation.mts';

export { defaultExecutionState } from './helpers.mts';
// Re-export all types
export type {
  AgentState,
  ConversationMetrics,
  ConversationState,
  ExecutionMetrics,
  ExecutionState,
  GateResult,
  GateState,
  PluginHookResult,
  PluginLifecycleState,
  PluginSummary,
  RevisionRequest,
  RuntimeEvent,
  StageState,
  WorkflowExecutionNode,
  WorkflowExecutionNodeStatus,
  WorkflowExecutionState,
} from './types.mts';

const projectors = [
  projectPipelineLifecycle,
  projectStageLifecycle,
  projectAgentLifecycle,
  projectConversationLifecycle,
  projectPluginLifecycle,
  projectRevisionLifecycle,
  projectWaveLifecycle,
];

export function applyEvent(
  currentState: ExecutionState,
  event: RuntimeEvent,
  feature: string,
): ExecutionState {
  const state = currentState;
  state.updatedAt = event.timestamp || state.updatedAt;

  for (const projector of projectors) {
    const result = projector(state, event, feature);
    if (result !== null) return result;
  }

  return state;
}

export function readEvents(eventsFile: string): RuntimeEvent[] {
  const { records, corruptLines } = readJsonlTolerant(eventsFile);
  for (const corrupt of corruptLines) {
    process.stderr.write(
      `[boss-skill] 跳过 events.jsonl 第 ${corrupt.line} 行的损坏行（疑似写入中途崩溃，视作该事件未记录）: ${corrupt.text.slice(0, 120)}\n`,
    );
  }
  return records.map((event) => {
    validateEvent(event);
    return event;
  });
}

export function materializeState(
  feature: string,
  cwd = process.cwd(),
): { eventCount: number; execJsonPath: string; state: ExecutionState } {
  if (!feature) {
    throw new Error('缺少 feature 参数');
  }

  const metaDir = path.join(cwd, '.boss', feature, '.meta');
  const eventsFile = path.join(metaDir, 'events.jsonl');
  const execJsonPath = path.join(metaDir, 'execution.json');

  if (!fs.existsSync(eventsFile)) {
    throw new Error(`未找到事件文件: ${path.relative(cwd, eventsFile)}`);
  }

  const events = readEvents(eventsFile);
  const state = projectState(events, feature);
  validateExecutionState(state, feature);
  fs.writeFileSync(execJsonPath, JSON.stringify(state, null, 2) + '\n', 'utf8');

  return {
    eventCount: events.length,
    execJsonPath,
    state,
  };
}

export function projectState(events: RuntimeEvent[], feature: string): ExecutionState {
  let state = defaultExecutionState(feature);
  for (const event of events) {
    state = applyEvent(state, event, feature);
  }
  return finalizeState(state);
}

export function runCli(argv = process.argv.slice(2)): void {
  const [feature] = argv;
  if (!feature || feature === '-h' || feature === '--help') {
    process.stderr.write('用法: materialize-state.js <feature>\n');
    process.exit(feature ? 0 : 1);
  }

  try {
    const result = materializeState(feature, process.cwd());
    process.stderr.write(
      `[MATERIALIZE] 状态已从 ${result.eventCount} 条事件物化到 ${path.relative(process.cwd(), result.execJsonPath)}\n`,
    );
  } catch (err) {
    process.stderr.write(`[MATERIALIZE] ${(err as Error).message}\n`);
    process.exit(1);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  runCli();
}
