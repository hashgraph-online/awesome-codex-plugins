import { pathClientCandidates, CLIENT_MANAGED_MODELS } from './local-client-paths.mjs';
import { createHash } from 'node:crypto';
import { execFile, spawn } from 'node:child_process';
import { access } from 'node:fs/promises';
import { homedir } from 'node:os';
import { isAbsolute, join, resolve, win32 as winPath } from 'node:path';
import { promisify } from 'node:util';
import http from 'node:http';
import { CdpClient } from './cdp-client.mjs';
import { connectorError, publicConnectorError } from './errors.mjs';
import {
  captureWorkspaceSnapshot,
  startWorkspaceScopeMonitor,
  validateAllowedPaths,
  validateWorkspace,
  verifyWorkspaceScope,
} from './scope-guard.mjs';
import {
  classifyCursorEntry,
  cursorClickSendExpression,
  cursorComposerExpression,
  cursorCreateAgentExpression,
  cursorExtractExpression,
  cursorFillExpression,
  cursorHistoryExpression,
  cursorOpenAgentExpression,
  cursorProbeExpression,
  cursorSnapshotExpression,
  cursorStopExpression,
  selectNewCursorAgent,
} from './cursor-profile.mjs';

const TERMINAL = new Set(['completed', 'failed', 'cancelled', 'scope_violation', 'abandoned']);

function sleep(ms) {
  return new Promise((resolveWait) => setTimeout(resolveWait, ms));
}

function redact(value) {
  return String(value || '')
    .replace(/\bBearer\s+[^\s]+/gi, 'Bearer [redacted]')
    .replace(/((?:api[-_]?key|token|secret|password)\s*[:=]\s*)[^\s]+/gi, '$1[redacted]')
    .trim()
    .slice(-2048);
}

function accessEnvelope(prompt, workspace, readOnly, allowedPaths) {
  return [
    '[Codex Agents Workflow connector access boundary]',
    `Workspace: ${workspace}`,
    readOnly ? 'Access mode: READ ONLY.' : 'Access mode: BOUNDED WRITE.',
    readOnly
      ? 'Do not create, modify, rename, or delete files and do not run commands that change repository state.'
      : `Modify only these workspace-relative paths:\n${allowedPaths.map((path) => `- ${path}`).join('\n')}\nDo not modify any other path.`,
    'Do not push or publish. The primary agent remains the final verifier; your completion response is only a claim.',
    '[/Codex Agents Workflow connector access boundary]',
    '',
    prompt,
  ].join('\n');
}

function defaultCursorCandidates(env = process.env, platform = process.platform) {
  const configured = String(env.CURSOR_EXE || '').trim();
  if (configured) return [configured];
  if (platform === 'win32') {
    const local = env.LOCALAPPDATA || winPath.join(homedir(), 'AppData', 'Local');
    const programFiles = env.ProgramFiles || env.PROGRAMFILES || 'C:\\Program Files';
    const programFilesX86 = env['ProgramFiles(x86)'] || env.PROGRAMFILES_X86 || '';
    return [
      ...pathClientCandidates('cursor',env,platform),
      winPath.join(local, 'Programs', 'Cursor', 'Cursor.exe'),
      winPath.join(programFiles, 'Cursor', 'Cursor.exe'),
      programFilesX86 ? winPath.join(programFilesX86, 'Cursor', 'Cursor.exe') : '',
    ].filter(Boolean);
  }
  if (platform === 'darwin') {
    return [
      ...pathClientCandidates('cursor',env,platform),
      '/Applications/Cursor.app/Contents/MacOS/Cursor',
      join(homedir(), 'Applications', 'Cursor.app', 'Contents', 'MacOS', 'Cursor'),
    ];
  }
  return pathClientCandidates('cursor',env,platform);
}

async function firstAccessible(candidates) {
  for (const candidate of candidates) {
    const resolved = isAbsolute(candidate) ? resolve(candidate) : candidate;
    if (!isAbsolute(resolved)) continue;
    if (await access(resolved).then(() => true).catch(() => false)) return resolved;
  }
  return null;
}

function httpJson(port, path, timeoutMs = 3000) {
  return new Promise((resolveResult, reject) => {
    let settled = false;
    const finish = (fn, value) => {
      if (settled) return;
      settled = true;
      fn(value);
    };
    const req = http.get({ host: '127.0.0.1', port, path }, (response) => {
      if (response.statusCode !== 200) {
        response.resume();
        finish(reject, new Error(`Cursor CDP returned HTTP ${response.statusCode}`));
        return;
      }
      const chunks = [];
      let total = 0;
      response.on('data', (chunk) => {
        total += chunk.length;
        if (total > 2 * 1024 * 1024) {
          response.destroy(new Error('Cursor CDP response exceeded 2 MiB'));
          return;
        }
        chunks.push(chunk);
      });
      response.on('error', (error) => finish(reject, error));
      response.on('end', () => {
        try { finish(resolveResult, JSON.parse(Buffer.concat(chunks).toString('utf8'))); }
        catch (error) { finish(reject, new Error(`Cursor CDP returned invalid JSON: ${error.message}`)); }
      });
    });
    req.once('error', (error) => finish(reject, error));
    req.setTimeout(timeoutMs, () => req.destroy(new Error(`Cursor CDP port ${port} timed out`)));
  });
}

function isCursorIdentity(version, pages) {
  const payload = JSON.stringify({ version, pages });
  if (/windsurf/i.test(payload)) return false;
  return /Cursor\//i.test(String(version?.Browser || ''))
    || /[\\/]cursor[\\/](?:resources|app)/i.test(payload)
    || /cursor\.exe/i.test(payload)
    || (pages || []).some((page) => /cursor agents/i.test(String(page?.title || '')));
}

export class CursorCdpConnector {
  constructor({
    store,
    env = process.env,
    spawnImpl = spawn,
    execFileImpl = execFile,
    processRunningImpl = null,
  }) {
    this.store = store;
    this.env = env;
    this.spawnImpl = spawnImpl;
    this.execFileImpl = execFileImpl;
    this.processRunningImpl = processRunningImpl;
    this.active = new Map();
    this.waiters = new Map();
  }

  async binaryFor(provider) {
    const envName = provider.config.executable_env || 'CURSOR_EXE';
    const env = { ...this.env, CURSOR_EXE: this.env[envName] || this.env.CURSOR_EXE };
    return firstAccessible(defaultCursorCandidates(env));
  }

  async probe(provider, { workspace } = {}) {
    const fullWorkspace = workspace ? await validateWorkspace(workspace) : null;
    const port = provider.config.cdp_port;
    if (!fullWorkspace) {
      try {
        const [version, pages] = await Promise.all([httpJson(port, '/json/version'), httpJson(port, '/json/list')]);
        if (!isCursorIdentity(version, pages)) {
          throw connectorError('PORT_NOT_CURSOR', `Port ${port} is not a verified Cursor CDP endpoint`);
        }
        return {
          provider_id: provider.id, connector: 'cursor_cdp', state: 'available', ready: false,
          observed: { transport: 'cdp_ui', cdp_port: port, cursor_identity: true, client_version:String(version.Browser ?? ''), models:CLIENT_MANAGED_MODELS, workspace: null },
          action_required: 'Provide an absolute Git workspace to verify the exact repository and supported Cursor Agent UI profile.',
          error: null,
        };
      } catch (error) {
        if (error?.code === 'PORT_NOT_CURSOR') throw error;
        const binary = await this.binaryFor(provider);
        return {
          provider_id: provider.id, connector: 'cursor_cdp',
          state: binary ? 'available' : 'needs_user_action', ready: false,
          observed: { transport: 'cdp_ui', cdp_port: port, binary_present: Boolean(binary), binary, models:CLIENT_MANAGED_MODELS, workspace: null },
          action_required: binary
            ? 'Provide a workspace and start an explicitly approved connector task.'
            : `Install Cursor or set ${provider.config.executable_env || 'CURSOR_EXE'} to an absolute executable path before the MCP server starts.`,
          error: null,
        };
      }
    }
    try {
      const transport = await this.#attach(provider, fullWorkspace, { launch: false });
      transport.client.close();
      return {
        provider_id: provider.id,
        connector: 'cursor_cdp',
        state: 'ready',
        ready: true,
        observed: {
          transport: 'cdp_ui',
          cdp_port: port,
          target_id: transport.page.id,
          ui_profile: transport.profile.ui_flavor,
          workspace: fullWorkspace,
        },
        action_required: null,
        error: null,
      };
    } catch (error) {
      if (!['CURSOR_CDP_UNAVAILABLE', 'CURSOR_NOT_RUNNING'].includes(error?.code)) throw error;
      const binary = await this.binaryFor(provider);
      return {
        provider_id: provider.id,
        connector: 'cursor_cdp',
        state: binary ? 'available' : 'needs_user_action',
        ready: false,
        observed: {
          transport: 'cdp_ui',
          cdp_port: port,
          binary_present: Boolean(binary),
          workspace: fullWorkspace,
        },
        action_required: binary
          ? 'Start an explicitly approved connector task to launch Cursor with loopback CDP.'
          : `Install Cursor or set ${provider.config.executable_env || 'CURSOR_EXE'} before the MCP server starts.`,
        error: null,
      };
    }
  }

  async start({ provider, stage, prompt, workspace, taskTypeId, stageId, allowedPaths = [], taskId, assertActive, signal }) {
    const assertAdmission = () => { assertActive?.(); if (signal?.aborted) throw connectorError('CONNECTOR_STOPPED', 'Connector startup was revoked'); };
    assertAdmission();
    const fullWorkspace = await validateWorkspace(workspace);
    assertAdmission();
    const readOnly = stage.read_only === true;
    const boundedPaths = readOnly
      ? await validateAllowedPaths(fullWorkspace, allowedPaths)
      : await validateAllowedPaths(fullWorkspace, allowedPaths, { required: true });
    assertAdmission();
    if (readOnly && boundedPaths.length) {
      throw connectorError('ALLOWED_PATHS_READ_ONLY_CONFLICT', 'read-only tasks must not declare allowed_paths');
    }
    if (!readOnly && provider.capabilities.write !== true) {
      throw connectorError('WRITE_CAPABILITY_REQUIRED', `Provider ${provider.id} is not write-capable`);
    }
    const boundedPrompt = accessEnvelope(prompt, fullWorkspace, readOnly, boundedPaths);
    assertAdmission();
    const task = await this.store.create({
      ...(taskId ? { task_id: taskId } : {}),
      task_type_id: taskTypeId,
      stage_id: stageId,
      provider_id: provider.id,
      connector: 'cursor_cdp',
      workspace: fullWorkspace,
      read_only: readOnly,
      allowed_paths: boundedPaths,
      prompt_sha256: createHash('sha256').update(boundedPrompt).digest('hex'),
      baseline_snapshot: null,
      deadline_at: provider.config.task_timeout_ms > 0
        ? new Date(Date.now() + provider.config.task_timeout_ms).toISOString() : null,
    });
    let transport;
    let active = null;
    let scopeMonitor = null;
    let baseline = null;
    let submissionAttempted = false;
    let submissionAccepted = false;
    let baselineMessageCount = 0;
    let lastSubmitSnapshot = null;
    try {
      assertAdmission();
      // Reserve the workspace in the durable task store before taking the
      // baseline or touching the remote UI. This closes the check-before-create
      // race shared by all connector backends.
      baseline = await captureWorkspaceSnapshot(fullWorkspace);
      assertAdmission();
      await this.store.update(task.task_id, { baseline_snapshot: baseline });
      assertAdmission();
      scopeMonitor = startWorkspaceScopeMonitor(fullWorkspace, {
        readOnly,
        allowedPaths: boundedPaths,
        onViolation: (attempt) => this.#background(active, () => this.#runtimeScopeViolation(active, attempt)),
      });
      transport = await this.#attach(provider, fullWorkspace, { launch: true, assertActive: assertAdmission });
      assertAdmission();
      active = {
        taskId: task.task_id,
        provider,
        stage,
        workspace: fullWorkspace,
        readOnly,
        allowedPaths: boundedPaths,
        baseline,
        client: transport.client,
        page: transport.page,
        profile: transport.profile,
        process: transport.process || null,
        stderrTail: transport.stderrTail || [],
        scopeMonitor,
        scopeViolationTriggered: false,
        resultText: '',
        agentId: null,
        timeout: null,
        terminalObservedAt: null,
        intentionalCleanup: false,
      };
      this.active.set(task.task_id, active);
      const deferredIdentity = active.profile.ui_flavor === 'agents_panel';
      const before = deferredIdentity ? null : await this.#waitForHistory(active);
      assertAdmission();
      const created = JSON.parse(await active.client.evaluate(cursorCreateAgentExpression(fullWorkspace)) || '{}');
      assertAdmission();
      if (!created.ok) {
        throw connectorError('CURSOR_WORKSPACE_BIND_FAILED',
          `Cursor could not create an Agent in the exact workspace: ${created.state || 'unknown'}`, {
            details: { available: created.available || [] },
          });
      }
      if (deferredIdentity && created.previous_composer_id) {
        let previousStillVisible = true;
        for (let attempt = 0; attempt < 40; attempt += 1) {
          const observed = JSON.parse(await active.client.evaluate(cursorComposerExpression()) || '{}');
          previousStillVisible = observed.ok && observed.id === created.previous_composer_id;
          if (!previousStillVisible) break;
          await sleep(200);
        }
        if (previousStillVisible) {
          throw connectorError('REMOTE_IDENTITY_AMBIGUOUS',
            'Cursor did not replace the previous composer after the exact New Agent action.', {
              details: { previous_composer_id: created.previous_composer_id },
            });
        }
      }
      if (!deferredIdentity) {
        let composer = null;
        for (let attempt = 0; attempt < 30; attempt += 1) {
          composer = JSON.parse(await active.client.evaluate(cursorComposerExpression()) || '{}');
          if (composer.ok && composer.id) break;
          await sleep(200);
        }
        if (!composer?.ok || !composer.id) {
          throw connectorError('REMOTE_IDENTITY_AMBIGUOUS', 'Cursor did not expose one exact composer identity');
        }
        let selected = { agent: null, ambiguous: false, count: 0 };
        for (let attempt = 0; attempt < 25; attempt += 1) {
          const after = await this.#waitForHistory(active, 1200);
          selected = selectNewCursorAgent(before, after);
          if (selected.agent || selected.ambiguous) break;
          await sleep(200);
        }
        if (selected.ambiguous || !selected.agent || selected.agent.id !== composer.id) {
          throw connectorError('REMOTE_IDENTITY_AMBIGUOUS',
            'Cursor Agent history did not yield one unique identity matching the created composer', {
              details: { composer_id: composer.id, new_agent_count: selected.count },
            });
        }
        active.agentId = selected.agent.id;
      }
      if (scopeMonitor.violations.length > 0) {
        const error = connectorError('SCOPE_VIOLATION',
          'The workspace changed outside the declared scope before Cursor task submission.', {
            details: { prevented_attempts: scopeMonitor.violations },
          });
        error.confirmedNotSent = true;
        throw error;
      }
      assertAdmission();
      const filled = await active.client.evaluate(cursorFillExpression(boundedPrompt));
      assertAdmission();
      if (filled !== 'FILLED') throw connectorError('CURSOR_COMPOSER_FAILED', `Cursor input fill failed: ${filled}`);
      const baselineUi = JSON.parse(await active.client.evaluate(cursorSnapshotExpression(active.agentId)) || '{}');
      assertAdmission();
      baselineMessageCount = Number(baselineUi.message_count || 0);
      assertAdmission();
      submissionAttempted = true;
      await active.client.key('Enter', 'Enter', 13);
      let accepted = false;
      const submissionObserved = async () => {
        const snapshot = JSON.parse(await active.client.evaluate(cursorSnapshotExpression(active.agentId)) || '{}');
        lastSubmitSnapshot = snapshot;
        return Number(snapshot.stop || 0) > 0
          || Number(snapshot.message_count || 0) > baselineMessageCount
          || Number(snapshot.input_length) === 0;
      };
      for (let attempt = 0; attempt < 16; attempt += 1) {
        if (await submissionObserved()) { accepted = true; break; }
        await sleep(200);
      }
      if (!accepted) {
        const click = await active.client.evaluate(cursorClickSendExpression());
        if (click !== 'CLICKED') {
          const error = connectorError('SUBMIT_NOT_ACCEPTED', `Cursor did not accept the task: ${click}`);
          error.confirmedNotSent = Number(lastSubmitSnapshot?.input_length || 0) > 0;
          throw error;
        }
        for (let attempt = 0; attempt < 20; attempt += 1) {
          if (await submissionObserved()) { accepted = true; break; }
          await sleep(200);
        }
      }
      if (!accepted) {
        const error = connectorError('SUBMISSION_STATE_UNCERTAIN',
          'Cursor submission could not be confirmed after Enter and the exact Send control.');
        error.confirmedNotSent = Number(lastSubmitSnapshot?.input_length || 0) > 0;
        throw error;
      }
      submissionAccepted = true;
      if (deferredIdentity) {
        let composer = null;
        for (let attempt = 0; attempt < 50; attempt += 1) {
          composer = JSON.parse(await active.client.evaluate(cursorComposerExpression()) || '{}');
          if (composer.ok && composer.id) break;
          await sleep(200);
        }
        if (!composer?.ok || !composer.id) {
          throw connectorError('REMOTE_IDENTITY_UNBOUND',
            'Cursor accepted the task but did not expose one exact composer identity.', {
              actionRequired: 'Inspect the visible Cursor task and do not resubmit automatically.',
              details: { observed: composer },
            });
        }
        active.agentId = composer.id;
        const bound = JSON.parse(await active.client.evaluate(cursorSnapshotExpression(active.agentId)) || '{}');
        lastSubmitSnapshot = bound;
        if (bound.identity_match !== true || Number(bound.visible_composer_count || 0) !== 1) {
          throw connectorError('REMOTE_IDENTITY_AMBIGUOUS',
            'Cursor exposed a composer id, but it was not the unique visible task identity.', {
              details: { composer_id: active.agentId, observed: bound },
            });
        }
      }
      await this.store.update(task.task_id, {
        state: 'running',
        remote_identity: {
          agent_id: active.agentId,
          target_id: active.page.id,
          cdp_port: provider.config.cdp_port,
          ui_profile: provider.config.ui_profile,
          ui_flavor: active.profile.ui_flavor,
        },
        transport: {
          cdp_port: provider.config.cdp_port,
          target_id: active.page.id,
          web_socket_url: active.page.webSocketDebuggerUrl,
        },
      });
      this.#signal(task.task_id);
      active.lastActivityKey = this.#activityKey(lastSubmitSnapshot);
      this.#armInactivityTimeout(active);
      active.monitorReady = true;
      if (scopeMonitor.violations.length) await this.#runtimeScopeViolation(active, scopeMonitor.violations[0]);
      void this.#background(active, () => this.#monitor(active, baselineMessageCount));
      return this.publicTask(await this.store.get(task.task_id));
    } catch (error) {
      const safeError = typeof error?.code === 'string'
        ? error
        : connectorError('CURSOR_START_FAILED', redact(error?.message || error));
      const sentOrUncertain = submissionAccepted
        || (submissionAttempted && error?.confirmedNotSent !== true);
      if (sentOrUncertain && active?.agentId) {
        const uncertain = connectorError('SUBMISSION_STATE_UNCERTAIN',
          'Cursor may have accepted the task, but the connector did not complete durable submission setup.', {
            details: { task_id: task.task_id, agent_id: active.agentId, cause: redact(safeError.message) },
            actionRequired: 'Inspect or reconcile the exact task_id/agent_id; do not resubmit automatically.',
          });
        try {
          await this.store.update(task.task_id, {
            state: 'needs_attention',
            remote_identity: {
              agent_id: active.agentId, target_id: active.page?.id || null,
              cdp_port: provider.config.cdp_port, ui_profile: provider.config.ui_profile,
              ui_flavor: active.profile?.ui_flavor || null,
            },
            transport: {
              cdp_port: provider.config.cdp_port, target_id: active.page?.id || null,
              web_socket_url: active.page?.webSocketDebuggerUrl || null,
            },
            error: publicConnectorError(uncertain),
          });
          this.#signal(task.task_id);
          this.#armInactivityTimeout(active);
          void this.#background(active, () => this.#monitor(active, baselineMessageCount));
          return this.publicTask(await this.store.get(task.task_id));
        } catch {
          // The durable task already exists in starting state; restart recovery will
          // convert it to unknown_after_restart rather than allowing a duplicate send.
          throw uncertain;
        }
      }
      if (sentOrUncertain && active && !active.agentId) {
        const unbound = connectorError('REMOTE_IDENTITY_UNBOUND',
          'Cursor may have accepted the task, but no exact composer identity was published.', {
            details: { task_id: task.task_id, target_id: active.page?.id || null, cause: redact(safeError.message) },
            actionRequired: 'Inspect the visible Cursor task; use abandon only after confirming it stopped. Do not resubmit automatically.',
          });
        await this.store.update(task.task_id, {
          state: 'needs_attention',
          remote_identity: {
            agent_id: null,
            target_id: active.page?.id || null,
            cdp_port: provider.config.cdp_port,
            ui_profile: provider.config.ui_profile,
            ui_flavor: active.profile?.ui_flavor || null,
          },
          transport: {
            cdp_port: provider.config.cdp_port,
            target_id: active.page?.id || null,
            web_socket_url: active.page?.webSocketDebuggerUrl || null,
          },
          error: publicConnectorError(unbound),
        });
        this.#signal(task.task_id);
        return this.publicTask(await this.store.get(task.task_id));
      }
      transport?.client?.close(safeError);
      scopeMonitor?.close();
      this.active.delete(task.task_id);
      try {
        await this.store.update(task.task_id, {
          state: 'failed',
          error: publicConnectorError(safeError),
        });
      } catch (cleanupError) {
        throw Object.assign(new AggregateError([safeError, cleanupError], 'Connector startup and durable cleanup both failed'), { code: 'CONNECTOR_CLEANUP_INCOMPLETE' });
      }
      if (signal?.aborted && !submissionAttempted) safeError.cancellation_confirmed = true;
      throw safeError;
    } finally {
      if (this.store.persistenceError && active) await this.#cleanup(active);
    }
  }

  async status(taskId, waitMs = 0) {
    let task = await this.store.get(taskId);
    if (!task) throw connectorError('TASK_NOT_FOUND', `Unknown connector task: ${taskId}`);
    const boundedWait = Math.max(0, Math.min(Number(waitMs) || 0, 25_000));
    const deadline = Date.now() + boundedWait;
    while (boundedWait > 0 && !TERMINAL.has(task.state)
      && !['needs_attention', 'unknown_after_restart'].includes(task.state)) {
      const remaining = deadline - Date.now();
      if (remaining <= 0) break;
      await this.#waitForChange(taskId, task.updated_at, remaining);
      task = await this.store.get(taskId);
      if (!task) break;
    }
    return this.publicTask(task);
  }

  async control(taskId, args) {
    try { return await this.#control(taskId, args); }
    catch (error) {
      if (this.store.persistenceError) {
        const active = this.active.get(taskId);
        if (active) await this.#cleanup(active);
      }
      throw error;
    }
  }

  async #control(taskId, args) {
    const task = await this.store.get(taskId);
    if (!task) throw connectorError('TASK_NOT_FOUND', `Unknown connector task: ${taskId}`);
    const action = String(args.action || '');
    if (action === 'reconcile') return this.#reconcile(task);
    if (TERMINAL.has(task.state)) {
      throw connectorError('TASK_ALREADY_TERMINAL', `Connector task is already terminal: ${task.state}`);
    }
    let active = this.active.get(taskId);
    if (action === 'cancel') {
      if (args.confirm !== true) throw connectorError('CONFIRMATION_REQUIRED', 'cancel requires confirm=true');
      const expected = String(args.expected_agent_id || '').trim();
      const agentId = task.remote_identity?.agent_id;
      if (!expected) throw connectorError('IDENTITY_REQUIRED', 'cancel requires expected_agent_id');
      if (expected !== agentId) throw connectorError('IDENTITY_MISMATCH', 'expected_agent_id does not match');
      if (!active) throw connectorError('CANCEL_UNCONFIRMED', 'No live exact Cursor connection is attached');
      clearTimeout(active.timeout);
      await this.store.update(taskId, { state: 'cancelling' });
      try {
        const click = JSON.parse(await active.client.evaluate(cursorStopExpression(agentId)) || '{}');
        if (!click.clicked) throw connectorError('CANCEL_UNCONFIRMED', `Exact Cursor stop could not be invoked: ${click.state || 'unknown'}`);
      } catch (error) {
        await this.store.update(taskId, { state: 'needs_attention', error: publicConnectorError(error) });
        this.#signal(taskId);
        throw error;
      }
      return this.#confirmExactStop(active);
    }
    if (action === 'disconnect') {
      if (args.confirm !== true) throw connectorError('CONFIRMATION_REQUIRED', 'disconnect requires confirm=true');
      if (active) await this.#cleanup(active);
      await this.store.update(taskId, {
        state: 'needs_attention',
        error: publicConnectorError(connectorError('DISCONNECTED_UNCONFIRMED',
          'The Cursor CDP connection was closed without a confirmed remote terminal state.')),
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
          code: 'ABANDONED_UNCONFIRMED', message: String(args.reason), retryable: false,
          action_required: 'Inspect the workspace before overlapping work; the Cursor Agent may still run.',
        },
      });
      this.#signal(taskId);
      return this.publicTask(await this.store.get(taskId));
    }
    throw connectorError('CONTROL_ACTION_INVALID', 'action must be reconcile, cancel, disconnect, or abandon');
  }

  publicTask(task) {
    return task && {
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
      created_at: task.created_at,
      updated_at: task.updated_at,
      deadline_at: task.deadline_at,
      finished_at: task.finished_at,
      terminal_evidence: task.terminal_evidence,
      execution_cleanup: task.execution_cleanup ?? null,
      scope: task.scope || null,
      result: task.result,
      error: task.error,
    };
  }

  async #attach(provider, workspace, { launch, assertActive = () => {} }) {
    assertActive();
    const port = provider.config.cdp_port;
    let version;
    let pages;
    try {
      [version, pages] = await Promise.all([httpJson(port, '/json/version'), httpJson(port, '/json/list')]);
      assertActive();
    } catch {
      assertActive();
      if (!launch) throw connectorError('CURSOR_CDP_UNAVAILABLE', `Cursor CDP is not available on port ${port}`);
      if (provider.config.launch_if_closed !== true) {
        throw connectorError('CURSOR_NOT_RUNNING',
          'Cursor is not attached and this provider is configured not to launch it automatically.', {
            retryable: true,
            actionRequired: 'Start Cursor with the configured loopback CDP port, then retry the approved task.',
          });
      }
      if (await this.#cursorRunning()) {
        assertActive();
        throw connectorError('CURSOR_RUNNING_WITHOUT_CDP',
          'Cursor is already running without the required CDP port. The connector will not force-close it.', {
            retryable: true,
            actionRequired: 'Save work, exit Cursor normally once, then retry the same approved connector task.',
          });
      }
      const binary = await this.binaryFor(provider);
      assertActive();
      if (!binary) throw connectorError('CURSOR_BINARY_MISSING',
        `Cursor was not found; set ${provider.config.executable_env || 'CURSOR_EXE'} before starting the MCP server`);
      assertActive();
      const child = this.spawnImpl(binary, [
        `--remote-debugging-port=${port}`,
        `--remote-allow-origins=http://localhost:${port}`,
        workspace,
      ], { cwd: workspace, detached: true, stdio: ['ignore', 'ignore', 'pipe'], windowsHide: false, env: this.env });
      // Cursor is a user application, not a connector-owned worker. Release the
      // MCP process handles immediately even if later UI-profile probing fails;
      // never keep Codex alive or force-close Cursor merely because attachment
      // could not be proven.
      child.unref?.();
      child.stderr?.unref?.();
      const stderr = [];
      let spawnError = null;
      child.once('error', (error) => { spawnError = error; });
      child.stderr?.on('data', (chunk) => {
        stderr.push(redact(chunk));
        if (stderr.length > 10) stderr.shift();
      });
      const deadline = Date.now() + provider.config.startup_timeout_ms;
      while (Date.now() < deadline) {
        assertActive();
        if (spawnError) {
          throw connectorError('CURSOR_START_FAILED', `Cursor could not be started: ${redact(spawnError.message)}`);
        }
        if (child.exitCode !== null) {
          throw connectorError('CURSOR_START_FAILED', `Cursor exited before CDP became ready (code=${child.exitCode})`, {
            details: { stderr_tail: stderr.filter(Boolean).slice(-5) },
          });
        }
        try {
          const [candidateVersion, candidatePages] = await Promise.all([
            httpJson(port, '/json/version'),
            httpJson(port, '/json/list'),
          ]);
          assertActive();
          const hasTarget = Array.isArray(candidatePages)
            && candidatePages.some((page) => page?.type === 'page' && page.webSocketDebuggerUrl);
          if (isCursorIdentity(candidateVersion, candidatePages) && hasTarget) {
            version = candidateVersion;
            pages = candidatePages;
            break;
          }
        } catch {}
        await sleep(250);
      }
      assertActive();
      if (!version || !pages) throw connectorError('CURSOR_START_TIMEOUT', `Cursor did not expose CDP within ${provider.config.startup_timeout_ms}ms`);
      const attached = await this.#selectTarget(provider, workspace, version, pages);
      assertActive();
      return { ...attached, process: child, stderrTail: stderr };
    }
    assertActive();
    return this.#selectTarget(provider, workspace, version, pages);
  }

  async #selectTarget(provider, workspace, version, pages) {
    if (!isCursorIdentity(version, pages)) {
      throw connectorError('PORT_NOT_CURSOR', `Port ${provider.config.cdp_port} is not a verified Cursor CDP endpoint`);
    }
    const candidates = (Array.isArray(pages) ? pages : [])
      .filter((page) => page?.type === 'page' && page.webSocketDebuggerUrl);
    const usable = [];
    for (const page of candidates) {
      let client = null;
      try {
        client = await new CdpClient({
          webSocketDebuggerUrl: page.webSocketDebuggerUrl,
          origin: `http://localhost:${provider.config.cdp_port}`,
          timeoutMs: provider.config.command_timeout_ms,
        }).connect();
        const profile = JSON.parse(await client.evaluate(cursorProbeExpression(workspace)) || '{}');
        if (profile.ok) usable.push({ page, client, profile });
        else client.close();
      } catch {
        client?.close();
      }
    }
    if (usable.length !== 1) {
      usable.forEach((candidate) => candidate.client.close());
      throw connectorError('CURSOR_UI_UNSUPPORTED',
        usable.length > 1
          ? 'More than one Cursor page matched the exact workspace and supported UI profile'
          : 'No Cursor page matched the exact workspace and supported Agent UI profile', {
            details: { page_count: candidates.length, matched_count: usable.length },
          });
    }
    return usable[0];
  }

  async #history(active) {
    const result = JSON.parse(await active.client.evaluate(cursorHistoryExpression()) || '{}');
    if (!result.ok) throw connectorError('CURSOR_AGENT_ADAPTER_UNAVAILABLE', result.error || 'Cursor Agent adapter unavailable');
    return result.entries || [];
  }

  async #waitForHistory(active, timeoutMs = 5000) {
    const deadline = Date.now() + timeoutMs;
    let lastError = null;
    while (Date.now() < deadline) {
      try { return await this.#history(active); }
      catch (error) { lastError = error; }
      await sleep(150);
    }
    throw lastError || connectorError('CURSOR_AGENT_ADAPTER_UNAVAILABLE', 'Cursor Agent history did not become available');
  }

  async #background(active, operation) {
    try { await operation(); }
    catch (error) {
      this.store.persistenceError ||= error;
      process.stderr.write(`codex-agents-workflow Cursor lifecycle failed (${active?.taskId || 'startup'}): ${redact(error?.message || error)}\n`);
      if (active) {
        this.#signal(active.taskId);
        try { await this.#cleanup(active); }
        catch (cleanupError) {
          this.store.persistenceError ||= cleanupError;
          process.stderr.write(`codex-agents-workflow Cursor cleanup failed (${active.taskId}): ${redact(cleanupError?.message || cleanupError)}\n`);
        }
      }
    }
  }

  async #monitor(active, baselineMessageCount) {
    let sawStop = false;
    let lastKey = '';
    let lastActivityKey = active.lastActivityKey ?? '';
    let stable = 0;
    try {
      while (this.active.has(active.taskId)) {
        await sleep(500);
        const current = await this.store.get(active.taskId);
        if (!current || TERMINAL.has(current.state) || current.state === 'cancelling' || active.scopeViolationTriggered) return;
        const snapshot = JSON.parse(await active.client.evaluate(cursorSnapshotExpression(active.agentId)) || '{}');
        if (snapshot.identity_match === false) {
          await this.store.update(active.taskId, {
            state: 'needs_attention',
            error: publicConnectorError(connectorError('REMOTE_IDENTITY_LOST',
              'The exact Cursor Agent composer is no longer the uniquely visible task identity.', {
                actionRequired: 'Use reconcile to reopen the persisted agent_id; do not accept the visible chat as the task result.',
              })),
          });
          this.#signal(active.taskId);
          return;
        }
        const activityKey = this.#activityKey(snapshot);
        if (activityKey !== lastActivityKey) {
          lastActivityKey = activityKey;
          this.#armInactivityTimeout(active);
        }
        if (Number(snapshot.stop || 0) > 0) {
          sawStop = true;
          stable = 0;
          continue;
        }
        const complete = sawStop && Number(snapshot.reply_length || 0) > 0;
        const fallback = !sawStop
          && Number(snapshot.message_count || 0) >= baselineMessageCount + 2
          && Number(snapshot.reply_length || 0) > 0;
        if (complete || fallback) {
          const key = `${snapshot.reply_length}:${snapshot.reply_hash}`;
          stable = key === lastKey ? stable + 1 : 1;
          lastKey = key;
          if ((complete && stable >= 2) || (fallback && stable >= 4)) {
            // The stable reply is the remote terminal observation. Mark it
            // before extracting the text so a slow CDP read cannot race the
            // connector deadline and misclassify an already completed Agent.
            active.terminalObservedAt = new Date().toISOString();
            clearTimeout(active.timeout);
            active.resultText = String(await active.client.evaluate(cursorExtractExpression()) || '').trim();
            await this.#complete(active);
            return;
          }
        }
      }
    } catch (error) {
      await this.#transportLost(active, error);
    }
  }

  #activityKey(snapshot) {
    return `${snapshot?.stop ?? ''}:${snapshot?.message_count ?? ''}:${snapshot?.reply_length ?? ''}:${snapshot?.reply_hash ?? ''}`;
  }

  async #complete(active) {
    // Stable reply observation is the remote terminal boundary. Clear the
    // remote deadline before local scope verification and durable publication
    // so slow local finalization cannot be reported as a remote timeout.
    active.terminalObservedAt = new Date().toISOString();
    clearTimeout(active.timeout);
    const current = await this.store.get(active.taskId);
    if (current && TERMINAL.has(current.state)) {
      await this.#cleanup(active);
      return;
    }
    const scope = await verifyWorkspaceScope(active.workspace, active.baseline, {
      readOnly: active.readOnly,
      allowedPaths: active.allowedPaths,
      runtimeAttempts: active.scopeMonitor?.violations || [],
    });
    if (active.scopeViolationTriggered) return;
    const state = scope.compliant ? 'completed' : 'scope_violation';
    await this.store.update(active.taskId, {
      state,
      scope,
      terminal_evidence: {
        kind: 'stable_cursor_reply',
        observed_at: new Date().toISOString(),
        agent_id: active.agentId,
      },
      result: state === 'completed' ? { text: active.resultText, artifact_path: null } : null,
      error: state === 'scope_violation'
        ? publicConnectorError(connectorError('SCOPE_VIOLATION',
          'Cursor changed paths outside the declared connector scope.', { details: scope }))
        : null,
    });
    this.#signal(active.taskId);
    await this.#cleanup(active);
  }

  async #confirmExactStop(active, { stopClicked = true } = {}) {
    const taskId = active.taskId;
    try {
      // A missing Stop control is only terminal evidence alongside a visible
      // completed reply. Missing/mismatched identity is never proof of a stop.
      const stopped = snapshot => snapshot.identity_match === true && snapshot.stop === 0
        && (stopClicked || (snapshot.reply_length > 0 && snapshot.message_count >= 2));
      for (let attempt = 0; attempt < 30; attempt += 1) {
        const snapshot = JSON.parse(await active.client.evaluate(cursorSnapshotExpression(active.agentId)) || '{}');
        if (snapshot.identity_match !== true) throw connectorError('REMOTE_IDENTITY_LOST', 'Exact Cursor identity was lost while confirming Stop');
        if (stopped(snapshot)) {
          await sleep(250);
          const second = JSON.parse(await active.client.evaluate(cursorSnapshotExpression(active.agentId)) || '{}');
          if (second.identity_match !== true) throw connectorError('REMOTE_IDENTITY_LOST', 'Exact Cursor identity was lost while confirming Stop');
          if (stopped(second)) {
            const scope = await verifyWorkspaceScope(active.workspace, active.baseline, {
              readOnly: active.readOnly, allowedPaths: active.allowedPaths,
              runtimeAttempts: active.scopeMonitor?.violations || [],
            });
            const current = await this.store.get(taskId);
            if (!current || TERMINAL.has(current.state) || active.intentionalCleanup) return this.publicTask(current);
            const state = scope.compliant ? 'cancelled' : 'scope_violation';
            await this.store.update(taskId, {
              state, scope, result: null,
              terminal_evidence: { kind: stopClicked ? 'exact_cursor_stop' : 'stable_cursor_reply', agent_id: active.agentId, observed_at: new Date().toISOString() },
              error: state === 'scope_violation' ? publicConnectorError(connectorError('SCOPE_VIOLATION',
                'Cursor changed paths outside the declared connector scope.', { details: scope })) : null,
            });
            await this.#cleanup(active);
            this.#signal(taskId);
            return this.publicTask(await this.store.get(taskId));
          }
        }
        await sleep(200);
      }
      throw connectorError('CANCEL_UNCONFIRMED', 'The exact Cursor Agent did not expose a stable terminal state after Stop');
    } catch (error) {
      // Persistence failures poison the store and propagate through this write.
      const current = await this.store.get(taskId);
      if (!current || TERMINAL.has(current.state) || active.intentionalCleanup) return this.publicTask(current);
      await this.store.update(taskId, { state: 'needs_attention', error: publicConnectorError(error) });
      this.#signal(taskId);
      return this.publicTask(await this.store.get(taskId));
    }
  }

  async #runtimeScopeViolation(active, attempt) {
    if (!active?.monitorReady || active.intentionalCleanup || active.scopeViolationTriggered) return;
    active.scopeViolationTriggered = true;
    const current = await this.store.get(active.taskId);
    if (!current || TERMINAL.has(current.state)) return;
    clearTimeout(active.timeout);
    await this.store.update(active.taskId, {
      state: 'cancelling',
      scope: {
        read_only: active.readOnly,
        allowed_paths: [...active.allowedPaths],
        changed_paths: [],
        metadata_changes: [],
        outside_paths: [attempt.path],
        prevented_attempts: [...(active.scopeMonitor?.violations || [attempt])],
        compliant: false,
        unchanged: false,
        evidence_status: 'runtime_observed_terminal_unconfirmed',
      },
      error: publicConnectorError(connectorError('RUNTIME_SCOPE_VIOLATION',
        'A workspace write outside the declared Cursor scope was observed while the task was active.', {
          details: { prevented_attempts: [attempt] },
          actionRequired: 'The connector is stopping the exact Agent; inspect scope evidence before accepting any result.',
        })),
    });
    this.#signal(active.taskId);
    try {
      const stopped = JSON.parse(await active.client.evaluate(cursorStopExpression(active.agentId)) || '{}');
      if (stopped.clicked !== true && stopped.state !== 'not_generating') {
        throw connectorError('CANCEL_UNCONFIRMED', `Exact Cursor stop could not be invoked: ${stopped.state || 'unknown'}`);
      }
      await this.#confirmExactStop(active, { stopClicked: stopped.clicked === true });
    } catch (error) {
      const current = await this.store.get(active.taskId);
      if (!current || TERMINAL.has(current.state) || active.intentionalCleanup) return;
      await this.store.update(active.taskId, { state: 'needs_attention', error: publicConnectorError(error) });
      this.#signal(active.taskId);
    }
  }

  async #timeout(active) {
    if (active.terminalObservedAt) return;
    const current = await this.store.get(active.taskId);
    if (!current || TERMINAL.has(current.state) || active.terminalObservedAt) return;
    await this.store.update(active.taskId, {
      state: 'needs_attention',
      error: publicConnectorError(connectorError('TIMEOUT_UNCONFIRMED',
        'The Cursor task had no observable Agent activity before its inactivity deadline.', {
          actionRequired: 'Inspect, reconcile, or cancel the exact Agent; do not resubmit automatically.',
        })),
    }, { guard: current => !active.terminalObservedAt && !TERMINAL.has(current.state) });
    this.#signal(active.taskId);
  }

  #armInactivityTimeout(active) {
    clearTimeout(active.timeout);
    const timeoutMs = active.provider.config.task_timeout_ms ?? 0;
    if (!(timeoutMs > 0)) {
      active.timeout = null;
      void this.store.update(active.taskId, { deadline_at: null }, {
        guard: current => this.active.get(active.taskId) === active && !active.terminalObservedAt && !TERMINAL.has(current.state),
      }).catch(error => { this.store.persistenceError ||= error; });
      return;
    }
    const deadlineAt = new Date(Date.now() + timeoutMs).toISOString();
    active.timeout = setTimeout(() => this.#background(active, () => this.#timeout(active)), timeoutMs);
    void this.store.update(active.taskId, { deadline_at: deadlineAt }, {
      guard: current => this.active.get(active.taskId) === active && !active.terminalObservedAt && !TERMINAL.has(current.state),
    }).catch(error => { this.store.persistenceError ||= error; });
  }

  async #transportLost(active, error) {
    if (active.intentionalCleanup) return;
    const current = await this.store.get(active.taskId);
    if (!current || TERMINAL.has(current.state)) return;
    await this.store.update(active.taskId, {
      state: 'needs_attention',
      error: publicConnectorError(connectorError('TRANSPORT_LOST',
        'The Cursor CDP connection was lost before a confirmed terminal state.', {
          details: {
            message: redact(error?.message || error),
            stderr_tail: (active.stderrTail || []).filter(Boolean).slice(-5),
          },
          actionRequired: 'Use reconcile with the persisted exact agent_id; do not resubmit automatically.',
        })),
    });
    this.#signal(active.taskId);
  }

  async #waitForExactComposer(client, agentId, timeoutMs = 15_000) {
    const deadline = Date.now() + timeoutMs;
    let last = null;
    while (Date.now() < deadline) {
      last = JSON.parse(await client.evaluate(cursorComposerExpression()) || '{}');
      if (last.ok && last.id === agentId) return last;
      await sleep(200);
    }
    throw connectorError('REMOTE_IDENTITY_LOST',
      `Cursor did not present the exact Agent composer after selection: ${agentId}`, {
        details: { observed: last },
      });
  }

  async #reconcile(task) {
    if (!['unknown_after_restart', 'needs_attention'].includes(task.state)) {
      throw connectorError('RECONCILE_NOT_ALLOWED',
        'reconcile is only available for unknown_after_restart or needs_attention tasks');
    }
    const agentId = task.remote_identity?.agent_id;
    if (!agentId) throw connectorError('IDENTITY_REQUIRED', 'reconcile requires a persisted exact agent_id');
    const existing = this.active.get(task.task_id);
    if (existing) await this.#cleanup(existing);
    const provider = {
      id: task.provider_id,
      config: {
        cdp_port: task.transport?.cdp_port,
        command_timeout_ms: 30_000,
      },
    };
    const version = await httpJson(provider.config.cdp_port, '/json/version');
    const pages = await httpJson(provider.config.cdp_port, '/json/list');
    if (!isCursorIdentity(version, pages)) throw connectorError('PORT_NOT_CURSOR', 'Persisted CDP port is not Cursor');
    const selectedTarget = await this.#selectTarget({
      ...provider,
      config: { ...provider.config, ui_profile: task.remote_identity?.ui_profile || 'agents_v2_2026_08' },
    }, task.workspace, version, pages);
    const page = selectedTarget.page;
    const client = selectedTarget.client;
    let recoveredActive = null;
    try {
    const uiFlavor = selectedTarget.profile?.ui_flavor || task.remote_identity?.ui_flavor || null;
    let entry;
    if (uiFlavor === 'agents_panel') {
      const composer = JSON.parse(await client.evaluate(cursorComposerExpression()) || '{}');
      if (!composer.ok || composer.id !== agentId) {
        client.close();
        throw connectorError('REMOTE_IDENTITY_MISSING',
          'Cursor Agents panel is not displaying the persisted exact agent_id; recovery will not guess another task.', {
            details: { expected_agent_id: agentId, observed: composer },
          });
      }
      const status = String(composer.status || '').toLowerCase();
      const state = /generating|running|in_progress/.test(status)
        ? 'running'
        : /completed|done|finished|success/.test(status)
          ? 'completed'
          : /cancel/.test(status)
            ? 'cancelled'
            : /failed|error/.test(status)
              ? 'failed'
              : 'unknown';
      entry = { id: agentId, state };
    } else {
      const history = JSON.parse(await client.evaluate(cursorHistoryExpression()) || '{}');
      entry = (history.entries || []).find((candidate) => candidate.id === agentId);
      if (!entry) {
        client.close();
        throw connectorError('REMOTE_IDENTITY_MISSING', 'Cursor Agent history no longer contains the exact agent_id');
      }
      const opened = await client.evaluate(cursorOpenAgentExpression(agentId));
      if (opened !== 'OPENED') {
        client.close();
        throw connectorError('RECOVERY_FAILED', `Could not open exact Cursor Agent: ${opened}`);
      }
      try {
        await this.#waitForExactComposer(client, agentId);
      } catch (error) {
        client.close();
        throw error;
      }
    }
    const scopeMonitor = startWorkspaceScopeMonitor(task.workspace, {
      readOnly: task.read_only === true,
      allowedPaths: task.allowed_paths || [],
      onViolation: (attempt) => this.#background(recoveredActive, () => this.#runtimeScopeViolation(recoveredActive, attempt)),
    });
    const active = {
      taskId: task.task_id,
      provider: { config: { ...provider.config, task_timeout_ms: 0 } },
      stage: { read_only: task.read_only },
      workspace: task.workspace,
      readOnly: task.read_only,
      allowedPaths: task.allowed_paths || [],
      baseline: task.baseline_snapshot,
      client,
      page,
      profile: { ui_flavor: uiFlavor },
      process: null,
      stderrTail: [],
      scopeMonitor,
      scopeViolationTriggered: false,
      resultText: '',
      agentId,
      timeout: null,
      terminalObservedAt: null,
      intentionalCleanup: false,
      recovered: true,
    };
    recoveredActive = active;
    this.active.set(task.task_id, active);
    await this.store.update(task.task_id, {
      remote_identity: {
        ...task.remote_identity,
        target_id: page.id,
        ui_flavor: uiFlavor,
        recovered_attachment: true,
      },
      transport: {
        ...(task.transport || {}),
        target_id: page.id,
        web_socket_url: page.webSocketDebuggerUrl,
      },
    });
    const state = classifyCursorEntry(entry);
    if (state === 'completed') {
      active.resultText = String(await client.evaluate(cursorExtractExpression()) || '').trim();
      await this.#complete(active);
    } else if (state === 'cancelled' || state === 'failed') {
      const scope = await verifyWorkspaceScope(active.workspace, active.baseline, {
        readOnly: active.readOnly,
        allowedPaths: active.allowedPaths,
        runtimeAttempts: active.scopeMonitor?.violations || [],
      });
      const terminalState = scope.compliant ? state : 'scope_violation';
      await this.store.update(task.task_id, {
        state: terminalState,
        scope,
        terminal_evidence: {
          kind: uiFlavor === 'agents_panel' ? 'stable_cursor_composer' : 'stable_cursor_history',
          observed_at: new Date().toISOString(), agent_id: agentId,
        },
        error: terminalState === 'scope_violation'
          ? publicConnectorError(connectorError('SCOPE_VIOLATION',
            'Cursor changed paths outside the declared connector scope.', { details: scope }))
          : state === 'failed'
            ? publicConnectorError(connectorError('REMOTE_TASK_FAILED', 'Cursor Agent history reports failure'))
            : null,
      });
      await this.#cleanup(active);
    } else if (state === 'running') {
      await this.store.update(task.task_id, {
        state: 'running',
        error: null,
      });
      active.monitorReady = true;
      if (scopeMonitor.violations.length) await this.#runtimeScopeViolation(active, scopeMonitor.violations[0]);
      void this.#background(active, () => this.#monitor(active, 0));
    } else {
      await this.store.update(task.task_id, {
        state: 'needs_attention',
        error: publicConnectorError(connectorError('RECOVERED_RUN_STATE_UNKNOWN',
          'The exact Cursor Agent was reopened, but its terminal state is not proven.')),
      });
    }
    this.#signal(task.task_id);
    return this.publicTask(await this.store.get(task.task_id));
    } catch (error) {
      if (recoveredActive) await this.#cleanup(recoveredActive);
      else client.close();
      throw error;
    }
  }

  async #cursorRunning() {
    if (this.processRunningImpl) return this.processRunningImpl();
    try {
      if (process.platform === 'win32') {
        const { stdout } = await promisify(this.execFileImpl)('tasklist.exe', ['/fi', 'imagename eq Cursor.exe', '/nh'], {
          encoding: 'utf8', windowsHide: true, timeout: 5000,
        });
        return /Cursor\.exe/i.test(stdout || '');
      }
      const { stdout } = await promisify(this.execFileImpl)('pgrep', ['-f', '[Cc]ursor(?:\.app/Contents/MacOS/[Cc]ursor)?'], {
        encoding: 'utf8', timeout: 5000,
      });
      return Boolean(String(stdout || '').trim());
    } catch {
      return false;
    }
  }

  async #cleanup(active) {
    if (this.active.get(active.taskId) !== active) return;
    active.intentionalCleanup = true;
    clearTimeout(active.timeout);
    active.scopeMonitor?.close();
    await active.client?.close();
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
      done = () => { clearTimeout(timer); resolveWait(); };
      const set = this.waiters.get(taskId) || new Set();
      set.add(done);
      this.waiters.set(taskId, set);
    });
    const refreshed = await this.store.get(taskId);
    if (!refreshed || refreshed.updated_at !== observedUpdatedAt) {
      this.waiters.get(taskId)?.delete(done);
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

export { httpJson, isCursorIdentity, redact as redactCursorDiagnostic };
