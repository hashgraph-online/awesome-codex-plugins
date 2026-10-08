import { ConnectorTaskStore, resolveConnectorTaskPath } from './task-store.mjs';
import { GrokAcpConnector } from './grok-acp.mjs';
import { CursorCdpConnector } from './cursor-cdp.mjs';
import { connectorError } from './errors.mjs';
import { setTimeout as delay } from 'node:timers/promises';

const registries = new Map();
const confirmedStates = new Set(['completed', 'failed', 'cancelled', 'scope_violation']);
const cursorEvidence = new Set(['stable_cursor_reply', 'exact_cursor_stop', 'stable_cursor_composer', 'stable_cursor_history']);

export function connectorExecutionQuiescent(task) {
  if (task?.state === 'failed' && task.startup_cleanup?.local_quiescent === true
    && task.startup_cleanup.prompt_submitted === false) return true;
  if (!confirmedStates.has(task?.state) || task.execution_cleanup?.local_quiescent !== true) return false;
  const evidence = task.terminal_evidence?.kind;
  return task.connector === 'grok_acp' ? evidence === 'acp_prompt_result'
    : task.connector === 'cursor_cdp' && cursorEvidence.has(evidence);
}

export async function confirmConnectorExecutionQuiescent(registry, taskId, waitMs = 5_000) {
  const deadline = Date.now() + waitMs;
  let task;
  do {
    task = await registry.status(taskId, 0);
    if (connectorExecutionQuiescent(task)) return task;
    if (Date.now() >= deadline) break;
    await delay(Math.min(100, deadline - Date.now()));
  } while (true);
  throw connectorError('CONNECTOR_CANCEL_INCOMPLETE', `Exact connector ${taskId} lacks confirmed remote terminal and local cleanup evidence`);
}

export class ConnectorRegistry {
  constructor({ configPath, env = process.env, spawnImpl, execFileImpl, processRunningImpl }) {
    this.configPath = configPath;
    this.env = env;
    this.store = new ConnectorTaskStore({ statePath: resolveConnectorTaskPath(configPath) });
    this.grok = new GrokAcpConnector({
      store: this.store,
      configPath,
      env,
      ...(spawnImpl ? { spawnImpl } : {}),
    });
    this.cursor = new CursorCdpConnector({
      store: this.store,
      env,
      ...(spawnImpl ? { spawnImpl } : {}),
      ...(execFileImpl ? { execFileImpl } : {}),
      ...(processRunningImpl ? { processRunningImpl } : {}),
    });
  }

  async initialize() {
    await this.store.initialize();
    return this;
  }

  connector(provider) {
    if (provider.kind !== 'builtin_connector') {
      throw connectorError('PROVIDER_NOT_BUILTIN', `Provider is not a built-in connector: ${provider.id}`);
    }
    if (provider.config.connector === 'grok_acp') return this.grok;
    if (provider.config.connector === 'cursor_cdp') return this.cursor;
    throw connectorError('CONNECTOR_UNSUPPORTED', `Unsupported built-in connector: ${provider.config.connector}`);
  }

  async probe(provider, args) {
    await this.initialize();
    return this.connector(provider).probe(provider, args);
  }

  async start(params) {
    params.assertActive?.();
    await this.initialize();
    params.assertActive?.();
    const writeRequested = params?.stage?.read_only !== true;
    const approvalRequired = params?.provider?.requires_user_approval === true
      || params?.stage?.requires_user_approval === true;
    if (approvalRequired && params?.userApproved !== true) {
      throw connectorError('APPROVAL_REQUIRED',
        `Connector stage ${params?.taskTypeId || 'unknown'}.${params?.stageId || params?.stage?.id || 'unknown'} requires explicit current-task user approval`);
    }
    if (writeRequested && params?.provider?.capabilities?.write !== true) {
      throw connectorError('WRITE_CAPABILITY_REQUIRED',
        `Provider ${params?.provider?.id || 'unknown'} is not write-capable`);
    }
    return this.connector(params.provider).start(params);
  }

  async status(taskId, waitMs) {
    await this.initialize();
    const task = await this.store.get(taskId);
    if (!task) throw connectorError('TASK_NOT_FOUND', `Unknown connector task: ${taskId}`);
    if (task.connector === 'grok_acp') return this.grok.status(taskId, waitMs);
    if (task.connector === 'cursor_cdp') return this.cursor.status(taskId, waitMs);
    throw connectorError('CONNECTOR_UNSUPPORTED', `Unsupported task connector: ${task.connector}`);
  }

  async control(taskId, args) {
    await this.initialize();
    const task = await this.store.get(taskId);
    if (!task) throw connectorError('TASK_NOT_FOUND', `Unknown connector task: ${taskId}`);
    if (task.connector === 'grok_acp') return this.grok.control(taskId, args);
    if (task.connector === 'cursor_cdp') return this.cursor.control(taskId, args);
    throw connectorError('CONNECTOR_UNSUPPORTED', `Unsupported task connector: ${task.connector}`);
  }
}

export function connectorRegistryFor({ configPath, env = process.env }) {
  const key = `${configPath}\0${env.GROK_BIN || ''}\0${env.CURSOR_EXE || ''}`;
  if (!registries.has(key)) registries.set(key, new ConnectorRegistry({ configPath, env }));
  return registries.get(key);
}
