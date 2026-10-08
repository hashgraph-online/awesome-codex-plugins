import { EVENT_TYPE_VALUES, EVENT_TYPES, type EventType } from '../domain/event-types.mts';
import { PIPELINE_STATUS, type PipelineStatus } from '../domain/state-constants.mts';
import { isBoolean, isNonEmptyString, isObject, isPositiveInteger } from './helpers.mts';
import type { ExecutionState, PluginSummary, RuntimeEvent } from './types.mts';

function failValidation(message: string, context = ''): never {
  throw new Error(context ? `${context}: ${message}` : message);
}

function validatePluginSummary(plugin: unknown, context: string): asserts plugin is PluginSummary {
  if (!isObject(plugin)) {
    failValidation('plugin 必须是对象', context);
  }
  if (!isNonEmptyString(plugin.name)) {
    failValidation('plugin.name 必须是非空字符串', context);
  }
  if (!isNonEmptyString(plugin.version)) {
    failValidation('plugin.version 必须是非空字符串', context);
  }
  if (!isNonEmptyString(plugin.type)) {
    failValidation('plugin.type 必须是非空字符串', context);
  }
}

export function validateEvent(event: unknown): asserts event is RuntimeEvent {
  if (!isObject(event)) {
    failValidation('event 必须是对象');
  }
  if (!isPositiveInteger(event.id)) {
    failValidation('event.id 必须是正整数');
  }
  if (!EVENT_TYPE_VALUES.includes(event.type as EventType)) {
    failValidation(`未知事件类型 ${JSON.stringify(event.type)}`);
  }
  if (!isNonEmptyString(event.timestamp) || !Number.isFinite(Date.parse(event.timestamp))) {
    failValidation(`事件 ${String(event.type)} 的 timestamp 无效`);
  }
  if (!isObject(event.data)) {
    failValidation(`事件 ${String(event.type)} 的 data 必须是对象`);
  }

  const context = `事件 ${String(event.type)}`;
  switch (event.type) {
    case EVENT_TYPES.PIPELINE_INITIALIZED:
      if (!isObject(event.data.initialState)) {
        failValidation('initialState 必须是对象', context);
      }
      break;
    case EVENT_TYPES.PIPELINE_PAUSED:
      if (
        event.data.reason !== undefined &&
        event.data.reason !== null &&
        typeof event.data.reason !== 'string'
      ) {
        failValidation('reason 必须是字符串或 null', context);
      }
      if (
        event.data.requestedBy !== undefined &&
        event.data.requestedBy !== null &&
        typeof event.data.requestedBy !== 'string'
      ) {
        failValidation('requestedBy 必须是字符串或 null', context);
      }
      break;
    case EVENT_TYPES.PIPELINE_RESUMED:
      if (
        event.data.stage !== undefined &&
        event.data.stage !== null &&
        !isPositiveInteger(event.data.stage)
      ) {
        failValidation('stage 必须是正整数或 null', context);
      }
      if (
        event.data.requestedBy !== undefined &&
        event.data.requestedBy !== null &&
        typeof event.data.requestedBy !== 'string'
      ) {
        failValidation('requestedBy 必须是字符串或 null', context);
      }
      break;
    case EVENT_TYPES.PACK_APPLIED:
      if (!isNonEmptyString(event.data.pack)) {
        failValidation('pack 必须是非空字符串', context);
      }
      break;
    case EVENT_TYPES.STAGE_STARTED:
    case EVENT_TYPES.STAGE_COMPLETED:
    case EVENT_TYPES.STAGE_RETRYING:
    case EVENT_TYPES.STAGE_SKIPPED:
      if (!isPositiveInteger(event.data.stage)) {
        failValidation('stage 必须是正整数', context);
      }
      break;
    case EVENT_TYPES.STAGE_FAILED:
      if (!isPositiveInteger(event.data.stage)) {
        failValidation('stage 必须是正整数', context);
      }
      if (
        event.data.reason !== undefined &&
        event.data.reason !== null &&
        typeof event.data.reason !== 'string'
      ) {
        failValidation('reason 必须是字符串或 null', context);
      }
      break;
    case EVENT_TYPES.ARTIFACT_RECORDED:
      if (!isPositiveInteger(event.data.stage)) {
        failValidation('stage 必须是正整数', context);
      }
      if (!isNonEmptyString(event.data.artifact)) {
        failValidation('artifact 必须是非空字符串', context);
      }
      break;
    case EVENT_TYPES.GATE_EVALUATED:
      if (!isPositiveInteger(event.data.stage)) {
        failValidation('stage 必须是正整数', context);
      }
      if (!isNonEmptyString(event.data.gate)) {
        failValidation('gate 必须是非空字符串', context);
      }
      if (!isBoolean(event.data.passed)) {
        failValidation('passed 必须是布尔值', context);
      }
      if (event.data.checks !== undefined && !Array.isArray(event.data.checks)) {
        failValidation('checks 必须是数组', context);
      }
      break;
    case EVENT_TYPES.AGENT_STARTED:
    case EVENT_TYPES.AGENT_COMPLETED:
      if (!isPositiveInteger(event.data.stage)) {
        failValidation('stage 必须是正整数', context);
      }
      if (!isNonEmptyString(event.data.agent)) {
        failValidation('agent 必须是非空字符串', context);
      }
      break;
    case EVENT_TYPES.AGENT_FAILED:
    case EVENT_TYPES.AGENT_RETRY_SCHEDULED:
      if (!isPositiveInteger(event.data.stage)) {
        failValidation('stage 必须是正整数', context);
      }
      if (!isNonEmptyString(event.data.agent)) {
        failValidation('agent 必须是非空字符串', context);
      }
      if (
        event.data.reason !== undefined &&
        event.data.reason !== null &&
        typeof event.data.reason !== 'string'
      ) {
        failValidation('reason 必须是字符串或 null', context);
      }
      break;
    case EVENT_TYPES.REVISION_REQUESTED:
      if (!isNonEmptyString(event.data.from)) {
        failValidation('from 必须是非空字符串', context);
      }
      if (!isNonEmptyString(event.data.to)) {
        failValidation('to 必须是非空字符串', context);
      }
      if (!isNonEmptyString(event.data.artifact)) {
        failValidation('artifact 必须是非空字符串', context);
      }
      if (!isNonEmptyString(event.data.reason)) {
        failValidation('reason 必须是非空字符串', context);
      }
      break;
    case EVENT_TYPES.CONVERSATION_OPENED:
      if (!isObject(event.data.thread)) {
        failValidation('thread 必须是对象', context);
      }
      if (!isNonEmptyString(event.data.thread.id)) {
        failValidation('thread.id 必须是非空字符串', context);
      }
      break;
    case EVENT_TYPES.CONVERSATION_MESSAGE_APPENDED:
      if (!isObject(event.data.message)) {
        failValidation('message 必须是对象', context);
      }
      if (!isNonEmptyString(event.data.message.id)) {
        failValidation('message.id 必须是非空字符串', context);
      }
      if (!isNonEmptyString(event.data.message.threadId)) {
        failValidation('message.threadId 必须是非空字符串', context);
      }
      break;
    case EVENT_TYPES.CONVERSATION_RESOLVED:
      if (!isObject(event.data.resolution)) {
        failValidation('resolution 必须是对象', context);
      }
      if (!isNonEmptyString(event.data.resolution.threadId)) {
        failValidation('resolution.threadId 必须是非空字符串', context);
      }
      break;
    case EVENT_TYPES.TODO_MATERIALIZED:
      if (!isObject(event.data.todo)) {
        failValidation('todo 必须是对象', context);
      }
      if (!isNonEmptyString(event.data.todo.id)) {
        failValidation('todo.id 必须是非空字符串', context);
      }
      break;
    case EVENT_TYPES.PLUGIN_DISCOVERED:
    case EVENT_TYPES.PLUGIN_ACTIVATED:
      validatePluginSummary(event.data.plugin, `${context}.plugin`);
      break;
    case EVENT_TYPES.PLUGIN_HOOK_EXECUTED:
    case EVENT_TYPES.PLUGIN_HOOK_FAILED:
      validatePluginSummary(event.data.plugin, `${context}.plugin`);
      if (!isNonEmptyString(event.data.hook)) {
        failValidation('hook 必须是非空字符串', context);
      }
      if (!Number.isInteger(event.data.exitCode) || Number(event.data.exitCode) < 0) {
        failValidation('exitCode 必须是大于等于 0 的整数', context);
      }
      if (
        event.data.stage !== undefined &&
        event.data.stage !== null &&
        !isPositiveInteger(event.data.stage)
      ) {
        failValidation('stage 必须是正整数或 null', context);
      }
      break;
    case EVENT_TYPES.PLUGINS_REGISTERED:
      if (!Array.isArray(event.data.plugins)) {
        failValidation('plugins 必须是数组', context);
      }
      for (const plugin of event.data.plugins) {
        validatePluginSummary(plugin, `${context}.plugins`);
      }
      break;
    case EVENT_TYPES.WAVE_VERIFIED:
      if (!isNonEmptyString(event.data.waveId)) {
        failValidation('waveId 必须是非空字符串', context);
      }
      if (!isNonEmptyString(event.data.phase)) {
        failValidation('phase 必须是非空字符串', context);
      }
      if (!isBoolean(event.data.verified)) {
        failValidation('verified 必须是布尔值', context);
      }
      break;
    default:
      break;
  }
}

export function validateExecutionState(
  state: unknown,
  feature: string,
): asserts state is ExecutionState {
  if (!isObject(state)) {
    failValidation('execution state 必须是对象');
  }
  if (!isNonEmptyString(state.schemaVersion)) {
    failValidation('execution.schemaVersion 必须是非空字符串');
  }
  if (state.feature !== feature) {
    failValidation(`execution.feature 必须为 ${feature}`);
  }
  if (!Object.values(PIPELINE_STATUS).includes(state.status as PipelineStatus)) {
    failValidation(`execution.status 无效: ${JSON.stringify(state.status)}`);
  }
  if (!isObject(state.stages)) {
    failValidation('execution.stages 必须是对象');
  }
  if (!isObject(state.qualityGates)) {
    failValidation('execution.qualityGates 必须是对象');
  }
  if (!isObject(state.metrics)) {
    failValidation('execution.metrics 必须是对象');
  }
  for (const key of [
    'totalDuration',
    'stageTimings',
    'gatePassRate',
    'retryTotal',
    'agentSuccessCount',
    'agentFailureCount',
    'meanRetriesPerStage',
    'revisionLoopCount',
    'pluginFailureCount',
  ]) {
    if (!(key in state.metrics)) {
      failValidation(`execution.metrics.${key} 缺失`);
    }
  }
  if (!Array.isArray(state.plugins)) {
    failValidation('execution.plugins 必须是数组');
  }
  if (!isObject(state.pluginLifecycle)) {
    failValidation('execution.pluginLifecycle 必须是对象');
  }
  if (!Array.isArray(state.pluginLifecycle.discovered)) {
    failValidation('execution.pluginLifecycle.discovered 必须是数组');
  }
  if (!Array.isArray(state.pluginLifecycle.activated)) {
    failValidation('execution.pluginLifecycle.activated 必须是数组');
  }
  if (!Array.isArray(state.pluginLifecycle.executed)) {
    failValidation('execution.pluginLifecycle.executed 必须是数组');
  }
  if (!Array.isArray(state.pluginLifecycle.failed)) {
    failValidation('execution.pluginLifecycle.failed 必须是数组');
  }
  if (!isObject(state.conversations)) {
    failValidation('execution.conversations 必须是对象');
  }
  if (!Array.isArray(state.conversations.threads)) {
    failValidation('execution.conversations.threads 必须是数组');
  }
  if (!Array.isArray(state.conversations.messages)) {
    failValidation('execution.conversations.messages 必须是数组');
  }
  if (!Array.isArray(state.conversations.resolutions)) {
    failValidation('execution.conversations.resolutions 必须是数组');
  }
  if (!Array.isArray(state.derivedTodos)) {
    failValidation('execution.derivedTodos 必须是数组');
  }
  if (!isObject(state.conversationMetrics)) {
    failValidation('execution.conversationMetrics 必须是对象');
  }
  for (const key of ['opened', 'resolved', 'todos', 'huddles', 'unresolved']) {
    if (!(key in state.conversationMetrics)) {
      failValidation(`execution.conversationMetrics.${key} 缺失`);
    }
  }
}
