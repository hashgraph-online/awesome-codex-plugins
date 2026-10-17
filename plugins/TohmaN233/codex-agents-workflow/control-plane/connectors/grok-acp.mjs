import { existsSync } from 'node:fs';
import { pathClientCandidates, CLIENT_MANAGED_MODELS } from './local-client-paths.mjs';
import { createHash, randomUUID } from 'node:crypto';
import { spawn } from 'node:child_process';
import { access, mkdir } from 'node:fs/promises';
import { homedir } from 'node:os';
import { dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { JsonRpcPeer } from './json-rpc-peer.mjs';
import { connectorError, publicConnectorError } from './errors.mjs';
import {
  captureWorkspaceSnapshot,
  pathAllowed,
  startWorkspaceScopeMonitor,
  validateAllowedPaths,
  validateWorkspace,
  verifyWorkspaceScope,
} from './scope-guard.mjs';

const RESULT_STATES = new Set(['completed', 'failed', 'cancelled', 'scope_violation', 'abandoned']);
const STARTUP_STOP_WAIT_MS = 3_000;

export function stopOwnedProcess(child, name, waitMs = STARTUP_STOP_WAIT_MS) {
  if (!child || typeof child.exitCode === 'number' || typeof child.signalCode === 'string') return Promise.resolve();
  return new Promise((resolveStop, rejectStop) => {
    let timer;
    const done = (error) => {
      clearTimeout(timer);
      child.off('exit', onExit); child.off('close', onExit); child.off('error', onError);
      if (error) rejectStop(error); else resolveStop();
    };
    const onExit = () => done();
    const onError = error => done(error);
    child.once('exit', onExit); child.once('close', onExit); child.once('error', onError);
    timer = setTimeout(() => done(connectorError('CONNECTOR_PROCESS_STOP_PENDING', `${name} did not confirm exit within ${waitMs}ms`)), waitMs);
    try { child.kill(); } catch (error) { done(error); }
  });
}

function defaultGrokBinary() {
  return join(homedir(), '.grok', 'bin', process.platform === 'win32' ? 'grok.exe' : 'grok');
}

function redactDiagnostic(value) {
  return String(value || '')
    .replace(/\bBearer\s+[^\s]+/gi, 'Bearer [redacted]')
    .replace(/((?:api[-_]?key|token|secret|password)\s*[:=]\s*)[^\s]+/gi, '$1[redacted]')
    .trim()
    .slice(-2048);
}

function validateInputContent(schema, content) {
  if (!content || typeof content !== 'object' || Array.isArray(content)) {
    throw connectorError('INPUT_INVALID', 'input content must be an object');
  }
  const properties = schema?.properties && typeof schema.properties === 'object'
    ? schema.properties : {};
  const required = Array.isArray(schema?.required) ? schema.required : [];
  const output = {};
  for (const [key, value] of Object.entries(content)) {
    const property = properties[key];
    if (!property || typeof property !== 'object') {
      throw connectorError('INPUT_INVALID', `input content contains unknown field: ${key}`);
    }
    if (property.type === 'string') {
      if (typeof value !== 'string') {
        throw connectorError('INPUT_INVALID', `input field ${key} must be a string`);
      }
      const allowed = Array.isArray(property.enum)
        ? property.enum
        : Array.isArray(property.oneOf)
          ? property.oneOf.map((option) => option?.const).filter((item) => typeof item === 'string')
          : null;
      if (allowed && !allowed.includes(value)) {
        throw connectorError('INPUT_INVALID', `input field ${key} is not one of the allowed values`);
      }
    } else if (property.type === 'number'
      && (typeof value !== 'number' || !Number.isFinite(value))) {
      throw connectorError('INPUT_INVALID', `input field ${key} must be a finite number`);
    } else if (property.type === 'integer' && !Number.isInteger(value)) {
      throw connectorError('INPUT_INVALID', `input field ${key} must be an integer`);
    } else if (property.type === 'boolean' && typeof value !== 'boolean') {
      throw connectorError('INPUT_INVALID', `input field ${key} must be a boolean`);
    } else if (property.type === 'array') {
      if (!Array.isArray(value) || value.some((item) => typeof item !== 'string')) {
        throw connectorError('INPUT_INVALID', `input field ${key} must be an array of strings`);
      }
    } else if (!['string', 'number', 'integer', 'boolean', 'array'].includes(property.type)) {
      throw connectorError('INPUT_INVALID', `input field ${key} has an unsupported type`);
    }
    output[key] = value;
  }
  for (const key of required) {
    if (!Object.hasOwn(output, key)) {
      throw connectorError('INPUT_INVALID', `input content is missing required field: ${key}`);
    }
  }
  if (Buffer.byteLength(JSON.stringify(output)) > 8 * 1024) {
    throw connectorError('INPUT_INVALID', 'input content exceeds the 8 KiB response limit');
  }
  return output;
}



function collectStrings(value, output = [], depth = 0, key = '') {
  if (depth > 6 || output.length >= 100) return output;
  if (typeof value === 'string') {
    output.push({ key, value });
    return output;
  }
  if (Array.isArray(value)) {
    value.forEach((child, index) => collectStrings(child, output, depth + 1, `${key}[${index}]`));
    return output;
  }
  if (value && typeof value === 'object') {
    Object.entries(value).forEach(([childKey, child]) =>
      collectStrings(child, output, depth + 1, key ? `${key}.${childKey}` : childKey));
  }
  return output;
}

function normalizePermissionPath(workspace, candidate) {
  const raw = String(candidate || '').trim().replace(/\\/g, '/');
  if (!raw || raw.includes('\n') || raw.length > 2048) return null;
  const pathLike = /(?:^|[\\/])[^\\/]+/.test(raw)
    || /^[A-Za-z]:[\\/]/.test(raw)
    || /\.[A-Za-z0-9]{1,12}$/.test(raw);
  if (!pathLike) return null;
  const absolute = isAbsolute(raw) ? resolve(raw) : resolve(workspace, raw);
  const relativePath = relative(workspace, absolute).replace(/\\/g, '/');
  if (!relativePath || relativePath === '.' || relativePath === '..' || relativePath.startsWith('../')) {
    return null;
  }
  return relativePath;
}

function permissionIntent(params, workspace) {
  const strings = collectStrings(params?.toolCall || {});
  const combined = strings.map((item) => `${item.key}:${item.value}`).join('\n');
  const writeLike = /\b(write|edit|modify|delete|remove|rename|move|mkdir|create|patch|apply|save|replace|overwrite)\b/i.test(combined)
    || /(?:fs\/write|write_text_file|apply_patch)/i.test(combined);
  const paths = [...new Set(strings
    .filter((item) => /path|file|location|cwd|target|uri/i.test(item.key) || /[\\/]/.test(item.value))
    .map((item) => normalizePermissionPath(workspace, item.value))
    .filter(Boolean))];
  return {
    write_like: writeLike,
    paths,
    tool_title: String(params?.toolCall?.title || 'Unnamed Grok tool call'),
  };
}

function accessEnvelope(prompt, workspace, readOnly, allowedPaths) {
  const boundary = readOnly
    ? [
      'Access mode: READ ONLY.',
      'Do not create, modify, rename, or delete files and do not run commands that change repository state.',
    ]
    : [
      'Access mode: BOUNDED WRITE.',
      'You may modify only these workspace-relative paths:',
      ...allowedPaths.map((path) => `- ${path}`),
      'Do not modify any other path. Ask through the normal ACP permission flow before consequential tools.',
    ];
  return [
    '[Codex Agents Workflow connector access boundary]',
    `Workspace: ${workspace}`,
    ...boundary,
    'The primary agent remains the final verifier. Your completion statement is only an implementation claim.',
    '[/Codex Agents Workflow connector access boundary]',
    '',
    prompt,
  ].join('\n');
}

function textChunk(params) {
  const update = params?.update;
  if (update?.sessionUpdate !== 'agent_message_chunk') return '';
  return update?.content?.type === 'text' && typeof update.content.text === 'string'
    ? update.content.text : '';
}

export class GrokAcpConnector {
  constructor({ store, configPath, env = process.env, spawnImpl = spawn }) {
    this.store = store;
    this.configPath = configPath;
    this.env = env;
    this.spawnImpl = spawnImpl;
    this.active = new Map();
    this.waiters = new Map();
  }

  binaryFor(provider) {
    const envName = provider.config.binary_env || 'GROK_BIN';
    const configured = String(this.env[envName] || '').trim();
    const binary = configured || pathClientCandidates('grok',this.env).find(path=>existsSync(path)) || defaultGrokBinary();
    return isAbsolute(binary) ? resolve(binary) : binary;
  }

  async probe(provider, { workspace } = {}) {
    const binary = this.binaryFor(provider);
    await access(binary).catch(() => {
      throw connectorError('GROK_BINARY_MISSING', `Grok binary not found: ${binary}`, {
        retryable: true,
        actionRequired: `Install Grok or set ${provider.config.binary_env || 'GROK_BIN'} before the MCP server starts.`,
      });
    });
    return {
      provider_id: provider.id,
      connector: 'grok_acp',
      state: 'available',
      ready: false,
      observed: {
        transport: 'leader_acp_stdio',
        binary_present: true, binary, models:CLIENT_MANAGED_MODELS,
        workspace: workspace ? await validateWorkspace(workspace) : null,
      },
      action_required: 'Start an explicitly approved read-only or bounded-write Stage to establish a live ACP session.',
      error: null,
    };
  }

  async start({ provider, stage, prompt, workspace, taskTypeId, stageId, allowedPaths = [], taskId, assertActive, signal, registerCleanup }) {
    const assertAdmission = () => { assertActive?.(); if (signal?.aborted) throw connectorError('CONNECTOR_STOPPED', 'Connector startup was revoked'); };
    assertAdmission();
    const fullWorkspace = await validateWorkspace(workspace);
    assertAdmission();
    const readOnly = stage.read_only === true;
    const boundedPaths = readOnly
      ? await validateAllowedPaths(fullWorkspace, allowedPaths)
      : await validateAllowedPaths(fullWorkspace, allowedPaths, { required: true });
    assertAdmission();
    if (readOnly && boundedPaths.length > 0) {
      throw connectorError('ALLOWED_PATHS_READ_ONLY_CONFLICT',
        'read-only connector tasks must not declare allowed_paths');
    }
    if (!readOnly && provider.capabilities.write !== true) {
      throw connectorError('WRITE_CAPABILITY_REQUIRED',
        `Provider ${provider.id} does not advertise bounded-write capability`);
    }
    const binary = this.binaryFor(provider);
    await access(binary).catch(() => {
      throw connectorError('GROK_BINARY_MISSING', `Grok binary not found: ${binary}`);
    });
    assertAdmission();
    const boundedPrompt = accessEnvelope(prompt, fullWorkspace, readOnly, boundedPaths);
    assertAdmission();
    const task = await this.store.create({
      ...(taskId ? { task_id: taskId } : {}),
      task_type_id: taskTypeId,
      stage_id: stageId,
      provider_id: provider.id,
      connector: 'grok_acp',
      workspace: fullWorkspace,
      read_only: readOnly,
      allowed_paths: boundedPaths,
      prompt_sha256: createHash('sha256').update(boundedPrompt).digest('hex'),
      baseline_snapshot: null,
      deadline_at: provider.config.task_timeout_ms > 0
        ? new Date(Date.now() + provider.config.task_timeout_ms).toISOString() : null,
    });
    const runtimeRoot = join(dirname(this.configPath), 'grok-runtime');
    const leaderSocket = join(runtimeRoot, `leader-${task.task_id}.sock`);
    const stderrTail = [];
    let leader;
    let acp;
    let peer;
    let active = null;
    let scopeMonitor = null;
    let baseline = null;
    let startupError = null;
    let promptSubmitted = false;
    let cleanupJob = null;
    const cleanupStartup = () => {
      if (cleanupJob) return cleanupJob;
      cleanupJob = (async () => {
        peer?.close(); scopeMonitor?.close();
        const stopped = await Promise.allSettled([stopOwnedProcess(acp, 'Grok ACP'), stopOwnedProcess(leader, 'Grok leader')]);
        const errors = stopped.filter(item => item.status === 'rejected').map(item => item.reason);
        if (errors.length) {
          await this.store.update(task.task_id, { state: 'needs_attention', error: publicConnectorError(connectorError('CONNECTOR_CLEANUP_INCOMPLETE', 'Grok startup processes did not confirm exit')),
            startup_cleanup: { local_quiescent: false, prompt_submitted: promptSubmitted } });
          throw Object.assign(new AggregateError(errors, 'Grok startup process cleanup is unconfirmed'), { code: 'CONNECTOR_CLEANUP_INCOMPLETE' });
        }
        await this.store.update(task.task_id, { state: 'failed', error: publicConnectorError(startupError ?? connectorError('CONNECTOR_STOPPED', 'Grok startup stopped')),
          startup_cleanup: { local_quiescent: true, prompt_submitted: promptSubmitted } });
        this.active.delete(task.task_id);
      })().finally(() => { cleanupJob = null; });
      return cleanupJob;
    };
    const runCleanup = registerCleanup?.(cleanupStartup) ?? cleanupStartup;
    const observeProcessError = (processName) => (error) => {
      if (active) {
        void this.#background(active, () => this.#onProcessError(active, processName, error));
      } else {
        startupError = connectorError('TRANSPORT_START_FAILED',
          `${processName} process could not start: ${redactDiagnostic(error?.message || error)}`);
      }
    };
    try {
      assertAdmission();
      await mkdir(runtimeRoot, { recursive: true, mode: 0o700 });
      assertAdmission();
      // The task-store reservation is the workspace exclusion transaction. Capture
      // the baseline only after that reservation is durable, so two connectors
      // cannot both pass a check-before-create window.
      baseline = await captureWorkspaceSnapshot(fullWorkspace);
      assertAdmission();
      await this.store.update(task.task_id, { baseline_snapshot: baseline });
      assertAdmission();
      scopeMonitor = startWorkspaceScopeMonitor(fullWorkspace, {
        readOnly,
        allowedPaths: boundedPaths,
        onViolation: (attempt) => this.#background(active, () => this.#runtimeScopeViolation(active, attempt)),
      });
      assertAdmission();
      leader = this.spawnImpl(binary, [
        'agent', 'leader', '--no-exit-on-disconnect', '--relay-on-demand', '--no-auto-update',
        '--leader-socket', leaderSocket,
      ], {
        cwd: fullWorkspace,
        stdio: ['ignore', 'ignore', 'pipe'],
        windowsHide: true,
        env: this.env,
      });
      leader.once('error', observeProcessError('leader'));
      leader.stderr?.on('data', (chunk) => {
        stderrTail.push(redactDiagnostic(chunk));
        if (stderrTail.length > 10) stderrTail.shift();
      });
      await new Promise((resolveWait) => setTimeout(resolveWait, 200));
      assertAdmission();
      if (startupError || leader.exitCode !== null) {
        throw startupError || connectorError('GROK_LEADER_START_FAILED',
          `Grok Leader exited before ACP initialization (code=${leader.exitCode})`, {
            details: { stderr_tail: stderrTail.filter(Boolean).slice(-5) },
          });
      }
      assertAdmission();
      acp = this.spawnImpl(binary, [
        '--permission-mode', 'default', 'agent', '--leader', '--leader-socket', leaderSocket, 'stdio',
      ], {
        cwd: fullWorkspace,
        stdio: ['pipe', 'pipe', 'pipe'],
        windowsHide: true,
        env: this.env,
      });
      acp.once('error', observeProcessError('acp'));
      acp.stderr?.on('data', (chunk) => {
        stderrTail.push(redactDiagnostic(chunk));
        if (stderrTail.length > 10) stderrTail.shift();
      });
      peer = new JsonRpcPeer({
        input: acp.stdout,
        output: acp.stdin,
        defaultTimeoutMs: provider.config.startup_timeout_ms,
      });
      active = {
        taskId: task.task_id,
        provider,
        stage,
        workspace: fullWorkspace,
        baseline,
        readOnly,
        allowedPaths: boundedPaths,
        preventedAttempts: [],
        binary,
        leaderSocket,
        leader,
        acp,
        peer,
        stderrTail,
        scopeMonitor,
        scopeViolationTriggered: false,
        pendingRequest: null,
        resultText: '',
        intentionalCleanup: false,
        initializing: true,
        processExit: null,
        timeout: null,
        inactivityGeneration: 0,
        deadlinePersistTimer: null,
      };
      if (startupError) throw startupError;
      this.active.set(task.task_id, active);
      peer.onNotification('session/update', (params) => this.#onSessionUpdate(active, params));
      peer.onRequest('session/request_permission', (params) => this.#onPermission(active, params));
      peer.onRequest('elicitation/create', (params) => this.#onInput(active, params));
      leader.once('exit', (code, signal) => this.#background(active, () => this.#onProcessExit(active, 'leader', code, signal)));
      acp.once('exit', (code, signal) => this.#background(active, () => this.#onProcessExit(active, 'acp', code, signal)));
      const initialized = await peer.request('initialize', {
        protocolVersion: 1,
        clientCapabilities: { elicitation: { form: {} } },
      }, provider.config.startup_timeout_ms);
      assertAdmission();
      const created = await peer.request('session/new', {
        cwd: fullWorkspace,
        mcpServers: [],
      }, provider.config.startup_timeout_ms);
      assertAdmission();
      const sessionId = String(created?.sessionId || '');
      if (!sessionId) throw connectorError('ACP_INIT_FAILED', 'Grok ACP did not return a sessionId');
      const runId = randomUUID();
      active.sessionId = sessionId;
      active.runId = runId;
      if (scopeMonitor.violations.length > 0) {
        throw connectorError('SCOPE_VIOLATION',
          'The workspace changed outside the declared scope before Grok prompt submission.', {
            details: { prevented_attempts: scopeMonitor.violations },
          });
      }
      const inactivityDeadline = this.#nextInactivityDeadline(active);
      await this.store.update(task.task_id, {
        state: 'running',
        deadline_at: inactivityDeadline,
        remote_identity: {
          session_id: sessionId,
          run_id: runId,
          protocol_version: initialized?.protocolVersion ?? 1,
        },
        transport: {
          leader_socket: leaderSocket,
          binary,
        },
      });
      assertAdmission();
      // An exit observed during asynchronous initialization must survive the
      // running-state publication and must prevent prompt submission.
      active.initializing = false;
      if (active.processExit) {
        await this.#onProcessExit(active, ...active.processExit);
        return this.publicTask(await this.store.get(task.task_id));
      }
      this.#signal(task.task_id);
      this.#armInactivityTimeout(active, inactivityDeadline);
      assertAdmission();
      promptSubmitted = true;
      void this.#background(active, () => peer.request('session/prompt', {
        sessionId,
        prompt: [{ type: 'text', text: boundedPrompt }],
      }, provider.config.max_task_duration_ms ?? 21_600_000)
        .then((result) => this.#complete(active, result))
        .catch((error) => this.#fail(active, error)));
      return this.publicTask(await this.store.get(task.task_id));
    } catch (error) {
      const safeError = typeof error?.code === 'string'
        ? error
        : connectorError('ACP_INIT_FAILED', redactDiagnostic(error?.message || error), {
          details: { stderr_tail: stderrTail.filter(Boolean).slice(-5) },
        });
      startupError = safeError;
      try { await runCleanup(); }
      catch (cleanupError) { throw Object.assign(new AggregateError([safeError, cleanupError], 'Connector startup and owned process cleanup both failed'), { code: 'CONNECTOR_CLEANUP_INCOMPLETE' }); }
      if (signal?.aborted && !promptSubmitted) safeError.cancellation_confirmed = true;
      throw safeError;
    }
  }

  async status(taskId, waitMs = 0) {
    let task = await this.store.get(taskId);
    if (!task) throw connectorError('TASK_NOT_FOUND', `Unknown connector task: ${taskId}`);
    const boundedWait = Math.max(0, Math.min(Number(waitMs) || 0, 25_000));
    const deadline = Date.now() + boundedWait;
    while (boundedWait > 0 && !RESULT_STATES.has(task.state)
      && !['needs_permission', 'needs_input', 'needs_attention', 'unknown_after_restart'].includes(task.state)) {
      const remaining = deadline - Date.now();
      if (remaining <= 0) break;
      await this.#waitForChange(taskId, task.updated_at, remaining);
      task = await this.store.get(taskId);
      if (!task) break;
    }
    return this.publicTask(task);
  }

  async control(taskId, args) {
    const task = await this.store.get(taskId);
    if (!task) throw connectorError('TASK_NOT_FOUND', `Unknown connector task: ${taskId}`);
    let active = this.active.get(taskId);
    const action = String(args.action || '');
    if (action === 'reconcile') {
      if (!['unknown_after_restart', 'needs_attention'].includes(task.state)) {
        throw connectorError('RECONCILE_NOT_ALLOWED',
          'reconcile is only available for unknown_after_restart or needs_attention tasks');
      }
      active = await this.#reconcile(task);
      return this.publicTask(await this.store.get(taskId));
    }
    if (RESULT_STATES.has(task.state)) {
      throw connectorError('TASK_ALREADY_TERMINAL',
        `Connector task is already terminal: ${task.state}`);
    }
    if (action === 'respond_permission') {
      if (task.state !== 'needs_permission') {
        throw connectorError('DECISION_NOT_DELIVERED', 'The task is no longer waiting for this decision; reconcile its current state');
      }
      if (task.pending_request?.request_id !== args.request_id) throw connectorError('IDENTITY_MISMATCH', 'request_id does not match the durable pending request');
      if (!active?.pendingRequest || active.pendingRequest.kind !== 'permission') {
        throw connectorError('PERMISSION_NOT_PENDING', 'No permission request is pending for this task');
      }
      if (args.request_id !== active.pendingRequest.requestId) {
        throw connectorError('IDENTITY_MISMATCH', 'request_id does not match the pending permission');
      }
      let response;
      if (args.decision === 'cancel') {
        response = { outcome: { outcome: 'cancelled' } };
      } else if (args.decision === 'select') {
        const option = active.pendingRequest.options.find((item) => item.optionId === args.option_id);
        if (!option) throw connectorError('IDENTITY_MISMATCH', 'option_id was not returned by Grok');
        response = { outcome: { outcome: 'selected', optionId: option.optionId } };
      } else {
        throw connectorError('CONTROL_ACTION_INVALID', 'permission decision must be select or cancel');
      }
      const committed = await this.#commitDecision(active, response);
      this.#signal(taskId);
      return this.publicTask(committed);
    }
    if (action === 'respond_input') {
      if (task.state !== 'needs_input') {
        throw connectorError('DECISION_NOT_DELIVERED', 'The task is no longer waiting for this decision; reconcile its current state');
      }
      if (task.pending_request?.request_id !== args.request_id) throw connectorError('IDENTITY_MISMATCH', 'request_id does not match the durable pending request');
      if (!active?.pendingRequest || active.pendingRequest.kind !== 'input') {
        throw connectorError('INPUT_NOT_PENDING', 'No input request is pending for this task');
      }
      if (args.request_id !== active.pendingRequest.requestId) {
        throw connectorError('IDENTITY_MISMATCH', 'request_id does not match the pending input');
      }
      const decision = args.decision || 'decline';
      if (!['accept', 'decline', 'cancel'].includes(decision)) {
        throw connectorError('CONTROL_ACTION_INVALID',
          'input decision must be accept, decline, or cancel');
      }
      const response = decision === 'accept'
        ? {
          action: 'accept',
          content: validateInputContent(active.pendingRequest.requestedSchema, args.content || {}),
        }
        : { action: decision };
      const committed = await this.#commitDecision(active, response);
      this.#signal(taskId);
      return this.publicTask(committed);
    }
    if (action === 'cancel') {
      if (args.confirm !== true) throw connectorError('CONFIRMATION_REQUIRED', 'cancel requires confirm=true');
      if (!active || !active.sessionId || !active.runId) {
        throw connectorError('CANCEL_UNCONFIRMED', 'No live exact Grok session/run is attached');
      }
      if (!String(args.expected_session_id || '').trim()
        || !String(args.expected_run_id || '').trim()) {
        throw connectorError('IDENTITY_REQUIRED',
          'cancel requires the exact expected_session_id and expected_run_id returned by start/status');
      }
      if (args.expected_session_id !== active.sessionId) {
        throw connectorError('IDENTITY_MISMATCH', 'expected_session_id does not match');
      }
      if (args.expected_run_id !== active.runId) {
        throw connectorError('IDENTITY_MISMATCH', 'expected_run_id does not match');
      }
      active.peer.notify('session/cancel', { sessionId: active.sessionId });
      await this.store.update(taskId, { state: 'cancelling' });
      this.#signal(taskId);
      return this.publicTask(await this.store.get(taskId));
    }
    if (action === 'disconnect') {
      if (args.confirm !== true) throw connectorError('CONFIRMATION_REQUIRED', 'disconnect requires confirm=true');
      if (active) await this.#cleanup(active);
      await this.store.update(taskId, {
        state: 'needs_attention',
        error: publicConnectorError(connectorError('DISCONNECTED_UNCONFIRMED',
          'The local ACP transport was disconnected without a confirmed remote terminal state.')),
      });
      this.#signal(taskId);
      return this.publicTask(await this.store.get(taskId));
    }
    if (action === 'abandon') {
      if (args.confirm !== true || args.acknowledge_may_still_run !== true || !String(args.reason || '').trim()) {
        throw connectorError('CONFIRMATION_REQUIRED',
          'abandon requires confirm=true, acknowledge_may_still_run=true, and a reason');
      }
      if (active) await this.#cleanup(active);
      await this.store.update(taskId, {
        state: 'abandoned',
        error: {
          code: 'ABANDONED_UNCONFIRMED',
          message: String(args.reason),
          retryable: false,
          action_required: 'Inspect the workspace before overlapping work; the remote process may have continued.',
        },
      });
      this.#signal(taskId);
      return this.publicTask(await this.store.get(taskId));
    }
    throw connectorError('CONTROL_ACTION_INVALID',
      'action must be reconcile, respond_permission, respond_input, cancel, disconnect, or abandon');
  }

  publicTask(task) {
    if (!task) return null;
    return {
      task_id: task.task_id,
      task_type_id: task.task_type_id,
      stage_id: task.stage_id,
      provider_id: task.provider_id,
      connector: task.connector,
      state: task.state,
      workspace: task.workspace,
      read_only: task.read_only,
      allowed_paths: task.allowed_paths || [],
      remote_identity: task.remote_identity || {},
      pending_request: task.pending_request || null,
      created_at: task.created_at,
      updated_at: task.updated_at,
      deadline_at: task.deadline_at,
      finished_at: task.finished_at,
      terminal_evidence: task.terminal_evidence,
      execution_cleanup: task.execution_cleanup ?? null,
      startup_cleanup: task.startup_cleanup ?? null,
      scope: task.scope || null,
      result: task.result,
      error: task.error,
    };
  }

  async #onSessionUpdate(active, params) {
    if (params?.sessionId && params.sessionId !== active.sessionId) return;
    this.#recordActivity(active);
    const chunk = textChunk(params);
    if (!chunk) return;
    const max = active.provider.config.max_result_chars;
    active.resultText = `${active.resultText}${chunk}`.slice(-max);
  }

  async #onPermission(active, params) {
    if (params?.sessionId && params.sessionId !== active.sessionId) {
      return { outcome: { outcome: 'cancelled' } };
    }
    const intent = permissionIntent(params, active.workspace);
    if (intent.write_like) {
      const outside = active.readOnly
        ? (intent.paths.length ? intent.paths : ['<unscoped-write>'])
        : intent.paths.length === 0
          ? ['<unscoped-write>']
          : intent.paths.filter((path) => !pathAllowed(path, active.allowedPaths));
      if (outside.length > 0) {
        const attempted = outside.map((path) => ({
          source: 'acp_permission',
          tool_title: intent.tool_title,
          path,
          reason: active.readOnly ? 'read_only' : 'outside_allowed_paths',
          observed_at: new Date().toISOString(),
        }));
        active.preventedAttempts.push(...attempted);
        const scope = await verifyWorkspaceScope(active.workspace, active.baseline, {
          readOnly: active.readOnly,
          allowedPaths: active.allowedPaths,
          preventedAttempts: active.preventedAttempts,
          runtimeAttempts: active.scopeMonitor?.violations || [],
        }).catch(() => ({
          read_only: active.readOnly,
          allowed_paths: [...active.allowedPaths],
          changed_paths: [],
          outside_paths: [],
          prevented_attempts: [...active.preventedAttempts],
          compliant: false,
          unchanged: false,
          baseline_digest: active.baseline?.digest || null,
          observed_digest: null,
        }));
        await this.store.update(active.taskId, {
          state: 'needs_attention',
          scope,
          pending_request: null,
          terminal_evidence: {
            kind: 'acp_permission_denied',
            observed_at: new Date().toISOString(),
            session_id: active.sessionId,
            run_id: active.runId,
          },
          result: null,
          error: publicConnectorError(connectorError('SCOPE_VIOLATION',
            'Grok requested a write outside the declared connector scope; the ACP permission was denied before execution.', {
              details: { prevented_attempts: attempted },
            })),
        });
        this.#signal(active.taskId);
        setImmediate(() => {
          try { active.peer?.notify('session/cancel', { sessionId: active.sessionId }); } catch {}
          void this.#cleanup(active);
        });
        return { outcome: { outcome: 'cancelled' } };
      }
    }
    if (active.pendingRequest) {
      throw connectorError('MULTIPLE_PENDING_REQUESTS', 'Grok issued overlapping permission/input requests');
    }
    const requestId = randomUUID();
    const options = (params.options || []).slice(0, 20).map((item) => ({
      optionId: item.optionId,
      name: item.name,
      kind: item.kind,
    }));
    const pending = { kind: 'permission', requestId, options, resolve: null, reject: null };
    const waiting = new Promise((resolve, reject) => {
      pending.resolve = resolve;
      pending.reject = reject;
      active.pendingRequest = pending;
      void this.#persistPendingRequest(active, pending, {
        state: 'needs_permission',
        pending_request: {
          kind: 'permission', request_id: requestId,
          tool_title: intent.tool_title,
          paths: intent.paths,
          write_like: intent.write_like,
          options,
        },
      });
    });
    return waiting;
  }

  #onInput(active, params) {
    if (params.mode !== 'form' || params.sessionId !== active.sessionId) {
      return { action: 'decline' };
    }
    if (active.pendingRequest) {
      throw connectorError('MULTIPLE_PENDING_REQUESTS', 'Grok issued overlapping permission/input requests');
    }
    const requestId = randomUUID();
    const pending = {
      kind: 'input', requestId, requestedSchema: params.requestedSchema || {},
      resolve: null, reject: null,
    };
    return new Promise((resolve, reject) => {
      pending.resolve = resolve;
      pending.reject = reject;
      active.pendingRequest = pending;
      void this.#persistPendingRequest(active, pending, {
        state: 'needs_input',
        pending_request: {
          kind: 'input', request_id: requestId,
          message: params.message || 'Grok needs input.',
          requested_schema: params.requestedSchema || null,
        },
      });
    });
  }

  async #background(active, operation) {
    try { await operation(); }
    catch (error) {
      // An asynchronous lifecycle failure must remain visible, but must never
      // leave an owned process/monitor running just because the store is down.
      this.store.persistenceError ||= error;
      process.stderr.write(`codex-agents-workflow Grok lifecycle failed (${active?.taskId || 'startup'}): ${redactDiagnostic(error?.message || error)}\n`);
      if (active) {
        this.#signal(active.taskId);
        await this.#cleanup(active);
      }
    }
  }

  async #persistPendingRequest(active, pending, fields) {
    try {
      this.#pauseInactivityTimeout(active);
      await this.store.update(active.taskId, { ...fields, deadline_at: null });
      if (active.pendingRequest?.requestId === pending.requestId) this.#signal(active.taskId);
    } catch (error) {
      if (active.pendingRequest?.requestId === pending.requestId) {
        active.pendingRequest = null;
        pending.reject?.(error);
      }
      // Keep the failure on the normal connector lifecycle. The pending ACP
      // request is rejected above; a second persistence failure is observable
      // through the store's poisoned state rather than becoming an unhandled
      // rejection.
      await this.#background(active, () => this.#fail(active, error));
    }
  }

  async #complete(active, result) {
    if (active.intentionalCleanup || this.active.get(active.taskId) !== active) return;
    // The remote deadline ends when its result arrives. Scope verification and
    // durable publication still gate acceptance, but are not a remote timeout.
    active.terminalObservedAt = new Date().toISOString();
    clearTimeout(active.timeout);
    clearTimeout(active.deadlinePersistTimer);
    const current = await this.store.get(active.taskId);
    if (current && RESULT_STATES.has(current.state)) {
      await this.#cleanup(active);
      return;
    }
    const cancelled = current?.state === 'cancelling'
      || String(result?.stopReason || '').toLowerCase().includes('cancel');
    const scope = await verifyWorkspaceScope(active.workspace, active.baseline, {
      readOnly: active.readOnly,
      allowedPaths: active.allowedPaths,
      preventedAttempts: active.preventedAttempts,
      runtimeAttempts: active.scopeMonitor?.violations || [],
    });
    const state = !scope.compliant ? 'scope_violation' : cancelled ? 'cancelled' : 'completed';
    await this.store.update(active.taskId, {
      state,
      pending_request: null,
      scope,
      terminal_evidence: {
        kind: 'acp_prompt_result',
        observed_at: active.terminalObservedAt,
        stop_reason: result?.stopReason || null,
      },
      result: state === 'scope_violation' ? null : { text: active.resultText.trim(), artifact_path: null },
      error: state === 'scope_violation'
        ? publicConnectorError(connectorError('SCOPE_VIOLATION',
          'Grok attempted or produced repository changes outside the declared connector scope.', {
            details: {
              changed_paths: scope.changed_paths,
              outside_paths: scope.outside_paths,
              prevented_attempts: scope.prevented_attempts,
            },
          }))
        : null,
    }, { guard: current => !active.intentionalCleanup && this.active.get(active.taskId) === active && !RESULT_STATES.has(current.state) });
    this.#signal(active.taskId);
    await this.#cleanup(active);
  }

  async #fail(active, error) {
    try {
      if (active.intentionalCleanup || this.active.get(active.taskId) !== active) return;
      const current = await this.store.get(active.taskId);
      if (!current || RESULT_STATES.has(current.state)) return;
      const scope = await verifyWorkspaceScope(active.workspace, active.baseline, {
        readOnly: active.readOnly,
        allowedPaths: active.allowedPaths,
        preventedAttempts: active.preventedAttempts,
        runtimeAttempts: active.scopeMonitor?.violations || [],
      }).catch(() => null);
      const unconfirmed = ['ACP_TRANSPORT_CLOSED', 'ACP_REQUEST_TIMEOUT'].includes(error?.code);
      const state = scope && !scope.compliant ? 'scope_violation' : unconfirmed ? 'needs_attention' : 'failed';
      await this.store.update(active.taskId, {
        state,
        scope,
        error: publicConnectorError(state === 'scope_violation'
          ? connectorError('SCOPE_VIOLATION',
            'Grok attempted or produced repository changes outside the declared connector scope.', {
              details: {
                changed_paths: scope.changed_paths,
                outside_paths: scope.outside_paths,
                prevented_attempts: scope.prevented_attempts,
              },
            })
          : connectorError(unconfirmed ? 'ACP_TERMINAL_UNCONFIRMED' : 'ACP_PROMPT_FAILED', redactDiagnostic(error instanceof Error ? error.message : error), {
            ...(unconfirmed ? { actionRequired: 'Reconcile the exact remote session before abandoning or starting overlapping work.' } : {}),
            details: { stderr_tail: active.stderrTail.filter(Boolean).slice(-5) },
          })),
      }, { guard: current => !active.intentionalCleanup && this.active.get(active.taskId) === active && !RESULT_STATES.has(current.state) });
      this.#signal(active.taskId);
    } finally {
      await this.#cleanup(active);
    }
  }

  async #runtimeScopeViolation(active, attempt) {
    if (!active || active.intentionalCleanup || active.scopeViolationTriggered) return;
    active.scopeViolationTriggered = true;
    const current = await this.store.get(active.taskId);
    if (!current || RESULT_STATES.has(current.state)) return;
    let cancelSent = false;
    if (active.sessionId) {
      try {
        active.peer?.notify('session/cancel', { sessionId: active.sessionId });
        cancelSent = true;
      } catch {}
    }
    await this.store.update(active.taskId, {
      state: cancelSent ? 'cancelling' : 'needs_attention',
      scope: {
        read_only: active.readOnly,
        allowed_paths: [...active.allowedPaths],
        changed_paths: [],
        metadata_changes: [],
        outside_paths: [attempt.path],
        prevented_attempts: [
          ...active.preventedAttempts,
          ...(active.scopeMonitor?.violations || [attempt]),
        ],
        compliant: false,
        unchanged: false,
        evidence_status: 'runtime_observed_terminal_unconfirmed',
      },
      error: publicConnectorError(connectorError('RUNTIME_SCOPE_VIOLATION',
        'A workspace write outside the declared Grok scope was observed while the task was active.', {
          details: { prevented_attempts: [attempt] },
          actionRequired: 'The connector requested exact session cancellation; inspect final scope evidence before acceptance.',
        })),
    });
    this.#signal(active.taskId);
  }

  #nextInactivityDeadline(active) {
    if (!(active.provider.config.task_timeout_ms > 0)) return null;
    return new Date(Date.now() + active.provider.config.task_timeout_ms).toISOString();
  }

  #armInactivityTimeout(active, deadlineAt = this.#nextInactivityDeadline(active)) {
    clearTimeout(active.timeout);
    const generation = ++active.inactivityGeneration;
    if (!deadlineAt) {
      active.timeout = null;
      return null;
    }
    active.timeout = setTimeout(
      () => this.#background(active, () => this.#timeout(active, generation)),
      Math.max(0, new Date(deadlineAt).getTime() - Date.now()),
    );
    return deadlineAt;
  }

  #pauseInactivityTimeout(active) {
    clearTimeout(active.timeout);
    clearTimeout(active.deadlinePersistTimer);
    active.timeout = null;
    active.deadlinePersistTimer = null;
    active.inactivityGeneration += 1;
  }

  #recordActivity(active) {
    if (active.intentionalCleanup || active.terminalObservedAt || active.pendingRequest
      || this.active.get(active.taskId) !== active) return;
    const deadlineAt = this.#armInactivityTimeout(active);
    clearTimeout(active.deadlinePersistTimer);
    if (!deadlineAt) {
      active.deadlinePersistTimer = null;
      return;
    }
    const generation = active.inactivityGeneration;
    active.deadlinePersistTimer = setTimeout(() => {
      active.deadlinePersistTimer = null;
      void this.#background(active, async () => {
        await this.store.update(active.taskId, { deadline_at: deadlineAt }, {
          guard: current => this.active.get(active.taskId) === active
            && !active.intentionalCleanup && !active.terminalObservedAt
            && active.inactivityGeneration === generation
            && !RESULT_STATES.has(current.state),
        });
        this.#signal(active.taskId);
      });
    }, 250);
  }

  async #timeout(active, generation) {
    if (active.processExit || active.terminalObservedAt
      || active.inactivityGeneration !== generation) return;
    const current = await this.store.get(active.taskId);
    if (!current || RESULT_STATES.has(current.state) || active.terminalObservedAt
      || active.inactivityGeneration !== generation) return;
    await this.store.update(active.taskId, {
      state: 'needs_attention',
      error: publicConnectorError(connectorError('TIMEOUT_UNCONFIRMED',
        'The Grok task produced no ACP activity before the configured inactivity deadline.', {
          actionRequired: 'Inspect or cancel the exact session/run; do not resubmit automatically.',
        })),
    }, { guard: current => !active.terminalObservedAt
      && active.inactivityGeneration === generation && !RESULT_STATES.has(current.state) });
    this.#signal(active.taskId);
  }

  async #onProcessExit(active, processName, code, signal) {
    if (active.intentionalCleanup || active.terminalObservedAt) return;
    active.processExit ??= [processName, code, signal];
    if (active.initializing) return;
    const current = await this.store.get(active.taskId);
    if (!current || RESULT_STATES.has(current.state) || active.terminalObservedAt) return;
    await this.store.update(active.taskId, {
      state: 'needs_attention',
      error: publicConnectorError(connectorError('TRANSPORT_EXITED',
        `${processName} process exited before a confirmed terminal state`, {
          details: { code, signal, stderr_tail: active.stderrTail.filter(Boolean).slice(-5) },
        })),
    });
    this.#signal(active.taskId);
  }

  async #onProcessError(active, processName, error) {
    if (active.intentionalCleanup || active.terminalObservedAt) return;
    const current = await this.store.get(active.taskId);
    if (!current || RESULT_STATES.has(current.state) || active.terminalObservedAt) return;
    await this.store.update(active.taskId, {
      state: 'needs_attention',
      error: publicConnectorError(connectorError('TRANSPORT_ERROR',
        `${processName} process error before a confirmed terminal state`, {
          details: {
            message: redactDiagnostic(error?.message || error),
            stderr_tail: active.stderrTail.filter(Boolean).slice(-5),
          },
        })),
    });
    this.#signal(active.taskId);
  }

  async #reconcile(task) {
    const identity = task.remote_identity || {};
    if (!identity.session_id || !identity.run_id) {
      throw connectorError('IDENTITY_REQUIRED',
        'restart reconciliation requires the persisted exact session_id and run_id');
    }
    const transport = task.transport || {};
    if (!transport.leader_socket || !transport.binary) {
      throw connectorError('RECOVERY_UNAVAILABLE',
        'persisted Grok transport identity is unavailable for this task');
    }
    const existing = this.active.get(task.task_id);
    if (existing) await this.#cleanup(existing);
    const stderrTail = [];
    const acp = this.spawnImpl(transport.binary, [
      '--permission-mode', 'default', 'agent', '--leader',
      '--leader-socket', transport.leader_socket, 'stdio',
    ], {
      cwd: task.workspace,
      stdio: ['pipe', 'pipe', 'pipe'],
      windowsHide: true,
      env: this.env,
    });
    acp.stderr?.on('data', (chunk) => {
      stderrTail.push(redactDiagnostic(chunk));
      if (stderrTail.length > 10) stderrTail.shift();
    });
    const peer = new JsonRpcPeer({ input: acp.stdout, output: acp.stdin, defaultTimeoutMs: 15_000 });
    let recoveredActive = null;
    const scopeMonitor = startWorkspaceScopeMonitor(task.workspace, {
      readOnly: task.read_only === true,
      allowedPaths: task.allowed_paths || [],
      onViolation: (attempt) => this.#background(recoveredActive, () => this.#runtimeScopeViolation(recoveredActive, attempt)),
    });
    const active = {
      taskId: task.task_id,
      provider: { config: { max_result_chars: 131_072, task_timeout_ms: 0 } },
      stage: { read_only: task.read_only },
      workspace: task.workspace,
      baseline: task.baseline_snapshot,
      readOnly: task.read_only === true,
      allowedPaths: task.allowed_paths || [],
      preventedAttempts: task.scope?.prevented_attempts || [],
      binary: transport.binary,
      leaderSocket: transport.leader_socket,
      leader: null,
      ownsLeader: false,
      acp,
      peer,
      stderrTail,
      scopeMonitor,
      scopeViolationTriggered: false,
      pendingRequest: null,
      resultText: '',
      intentionalCleanup: false,
      timeout: null,
      inactivityGeneration: 0,
      deadlinePersistTimer: null,
      sessionId: identity.session_id,
      runId: identity.run_id,
      recovered: true,
    };
    recoveredActive = active;
    this.active.set(task.task_id, active);
    peer.onNotification('session/update', (params) => this.#onSessionUpdate(active, params));
    peer.onRequest('session/request_permission', (params) => this.#onPermission(active, params));
    peer.onRequest('elicitation/create', (params) => this.#onInput(active, params));
    acp.once('exit', (code, signal) => this.#background(active, () => this.#onProcessExit(active, 'acp', code, signal)));
    try {
      const initialized = await peer.request('initialize', {
        protocolVersion: 1,
        clientCapabilities: { elicitation: { form: {} } },
      }, 15_000);
      if (initialized?.agentCapabilities?.loadSession !== true) {
        throw connectorError('RECOVERY_UNAVAILABLE',
          'Grok ACP did not advertise exact session/load recovery support');
      }
      await peer.request('session/load', {
        sessionId: identity.session_id,
        cwd: task.workspace,
        mcpServers: [],
      }, 15_000);
      await this.store.update(task.task_id, {
        state: 'needs_attention',
        remote_identity: {
          ...identity,
          protocol_version: initialized?.protocolVersion ?? identity.protocol_version ?? 1,
          recovered_attachment: true,
        },
        error: publicConnectorError(connectorError('RECOVERED_RUN_STATE_UNKNOWN',
          'The exact Grok session was reattached, but ACP does not prove the prior run terminal state.', {
            actionRequired: 'Inspect or cancel the exact session/run; do not resubmit automatically.',
          })),
      });
      this.#signal(task.task_id);
      return active;
    } catch (error) {
      await this.#cleanup(active);
      throw connectorError('RECOVERY_FAILED',
        `Could not reattach the exact Grok session: ${redactDiagnostic(error?.message || error)}`, {
          details: { stderr_tail: stderrTail.filter(Boolean).slice(-5) },
        });
    }
  }

  async #commitDecision(active, response) {
    const pending = active.pendingRequest;
    if (pending.committing) throw connectorError('CONTROL_IN_PROGRESS', 'This decision is already being committed');
    pending.committing = true;
    try {
      const inactivityDeadline = this.#nextInactivityDeadline(active);
      const committed = await this.store.update(active.taskId, {
        state: 'running', pending_request: null, deadline_at: inactivityDeadline,
        last_decision: { request_id: pending.requestId, kind: pending.kind,
          decision: pending.kind === 'permission' ? response.outcome.outcome : response.action,
          ...(pending.kind === 'permission' && response.outcome.optionId ? { option_id: response.outcome.optionId } : {}),
          committed_at: new Date().toISOString(), delivery: 'unconfirmed' },
      }, { guard: current => this.active.get(active.taskId) === active
        && !active.intentionalCleanup && active.pendingRequest === pending
        && !active.processExit && !active.terminalObservedAt && !active.scopeViolationTriggered
        && current.state === (pending.kind === 'permission' ? 'needs_permission' : 'needs_input')
        && current.pending_request?.request_id === pending.requestId });
      if (committed.last_decision?.request_id !== pending.requestId
        || active.intentionalCleanup || active.processExit || active.terminalObservedAt
        || active.scopeViolationTriggered || active.pendingRequest !== pending) {
        throw connectorError('DECISION_NOT_DELIVERED', 'Task ownership changed before decision delivery; reconcile the task');
      }
      active.pendingRequest = null;
      this.#armInactivityTimeout(active, inactivityDeadline);
      pending.resolve(response);
      return committed;
    } catch (error) {
      // No approval is delivered if durability fails. Cleanup only declines pending requests.
      await this.#cleanup(active);
      throw error;
    }
  }

  async #cleanup(active) {
    if (this.active.get(active.taskId) !== active) return;
    if (active.cleanupJob) return active.cleanupJob;
    active.cleanupJob = this.#cleanupOwned(active);
    try { await active.cleanupJob; } finally { active.cleanupJob = null; }
  }

  async #cleanupOwned(active) {
    active.intentionalCleanup = true;
    clearTimeout(active.timeout);
    clearTimeout(active.deadlinePersistTimer);
    active.scopeMonitor?.close();
    if (active.pendingRequest) {
      active.pendingRequest.resolve(active.pendingRequest.kind === 'permission'
        ? { outcome: { outcome: 'cancelled' } }
        : { action: 'cancel' });
      active.pendingRequest = null;
    }
    active.peer?.close();
    const stopped = await Promise.allSettled([
      stopOwnedProcess(active.acp, 'Grok ACP'),
      active.ownsLeader === false ? Promise.resolve() : stopOwnedProcess(active.leader, 'Grok leader'),
    ]);
    const errors = stopped.filter(item => item.status === 'rejected').map(item => item.reason);
    if (errors.length) {
      await this.store.update(active.taskId, { state: 'needs_attention', execution_cleanup: { local_quiescent: false },
        error: publicConnectorError(connectorError('CONNECTOR_CLEANUP_INCOMPLETE', 'Grok processes did not confirm exit')) });
      this.#signal(active.taskId);
      throw Object.assign(new AggregateError(errors, 'Grok process cleanup is unconfirmed'), { code: 'CONNECTOR_CLEANUP_INCOMPLETE' });
    }
    this.active.delete(active.taskId);
    this.#signal(active.taskId);
    await this.store.update(active.taskId, { execution_cleanup: { local_quiescent: true, observed_at: new Date().toISOString() } });
  }

  async #waitForChange(taskId, observedUpdatedAt, waitMs) {
    let done;
    const waiting = new Promise((resolveWait) => {
      const timer = setTimeout(() => {
        const set = this.waiters.get(taskId);
        set?.delete(done);
        if (set?.size === 0) this.waiters.delete(taskId);
        resolveWait();
      }, waitMs);
      done = () => {
        clearTimeout(timer);
        resolveWait();
      };
      const set = this.waiters.get(taskId) || new Set();
      set.add(done);
      this.waiters.set(taskId, set);
    });
    const refreshed = await this.store.get(taskId);
    if (!refreshed || refreshed.updated_at !== observedUpdatedAt) {
      const set = this.waiters.get(taskId);
      set?.delete(done);
      if (set?.size === 0) this.waiters.delete(taskId);
      done();
    }
    await waiting;
  }

  #signal(taskId) {
    const set = this.waiters.get(taskId);
    if (!set) return;
    this.waiters.delete(taskId);
    for (const done of set) done();
  }
}
