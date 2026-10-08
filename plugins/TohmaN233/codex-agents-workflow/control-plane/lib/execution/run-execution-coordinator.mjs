import { interruptActiveNodes } from '../workflow-state.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { confirmConnectorExecutionQuiescent } from '../../connectors/registry.mjs';

const terminalTask = new Set(['completed', 'failed', 'cancelled', 'scope_violation', 'abandoned']);
const terminalRun = new Set(['succeeded', 'failed', 'cancelled']);
const terminalManager = new Set(['succeeded', 'failed', 'cancelled', 'accepted', 'stopped']);
const owned = entry => !terminalManager.has(entry.status) || entry.cleanupPending || entry.session || entry.broker
  || entry.sessions?.length || entry.brokers?.length;
const failed = results => results.filter(item => item.status === 'rejected').map(item => item.reason);

// The shared admission registry is the synchronous gate. This coordinator
// resolves the other exact owners and performs bounded, observable cleanup.
export class RunExecutionCoordinator {
  constructor({ admission, strictManager, managedNativeManager, hostMainManager, registry }) {
    this.admission = admission; this.strictManager = strictManager; this.managedNativeManager = managedNativeManager;
    this.hostMainManager = hostMainManager; this.registry = registry; this.jobs = admission.drainJobs; this.errors = admission.drainErrors;
  }

  bind(runtime) { this.runtime = runtime; }

  fenceRun(runId) {
    this.admission.fenceRun(runId);
    for (const manager of [this.strictManager, this.managedNativeManager, this.hostMainManager]) manager.fenceRun(runId);
  }

  fenceAttempt(runId, nodeId, attemptId) {
    this.admission.fenceAttempt(runId, nodeId, attemptId);
    for (const manager of [this.strictManager, this.managedNativeManager, this.hostMainManager]) manager.fenceAttempt(runId, nodeId, attemptId);
  }

  async fenceAndSnapshotAttempt(runId, nodeId, attemptId) {
    return this.runtime.runs.withRunWriter(runId, async () => {
      const record = await this.runtime.runs.read(runId);
      requireValue(record.state.nodes[nodeId]?.attempts.some(item => item.id === attemptId),
        'ATTEMPT_MISSING', 'The exact execution attempt is missing');
      this.fenceAttempt(runId, nodeId, attemptId);
      return record;
    });
  }

  async drainAttempt(runId, nodeId, attemptId, { skipManager = null } = {}) {
    // The fence is ordered with durable publication by the Run writer.  A
    // caller's earlier read is never an execution-ownership inventory.
    await this.fenceAndSnapshotAttempt(runId, nodeId, attemptId);
    const stopped = await Promise.allSettled([
      skipManager === this.strictManager ? undefined : this.strictManager.stopAttempt(runId, nodeId, attemptId),
      skipManager === this.managedNativeManager ? undefined : this.managedNativeManager.stopAttempt(runId, nodeId, attemptId),
      skipManager === this.hostMainManager ? undefined : this.hostMainManager.stopAttempt(runId, nodeId, attemptId),
      (async () => { await this.admission.retryCleanup(runId, 'connector', nodeId, attemptId); await this.admission.waitAttempt(runId, nodeId, attemptId); })(),
    ]);
    const errors = failed(stopped);
    const record = await this.runtime.runs.read(runId);
    const attempt = record.state.nodes[nodeId]?.attempts.find(item => item.id === attemptId);
    requireValue(attempt, 'ATTEMPT_MISSING', 'The exact execution attempt disappeared during cleanup');
    try { await this.stopConnector(record, nodeId, attempt); } catch (error) { errors.push(error); }
    if (attempt.child_run_id) try {
      await this.runtime.runs.mutate(attempt.child_run_id, 'parent_execution_lost', state => {
        if (state.status === 'running') { interruptActiveNodes(state, 'Parent attempt lost execution authority'); state.status = 'cancelled'; }
      });
      await this.drainRun(attempt.child_run_id);
    } catch (error) { errors.push(error); }
    if (errors.length) throw Object.assign(new AggregateError(errors, 'Exact attempt cleanup is unconfirmed'), { code: 'FAIL_NODE_STOP_INCOMPLETE' });
    const current = await this.runtime.runs.read(runId);
    const latest = current.state.nodes[nodeId]?.attempts.find(item => item.id === attemptId);
    requireValue(latest, 'ATTEMPT_MISSING', 'The exact execution attempt disappeared after cleanup');
    await this.assertAttemptQuiescent(current, nodeId, latest);
    return current;
  }

  async quiesceOrigin(entry) {
    const failures = [];
    const sessions = [...new Set([entry.session, ...(entry.sessions ?? [])].filter(Boolean))];
    const brokers = [...new Set([entry.broker, ...(entry.brokers ?? [])].filter(Boolean))];
    for (const session of sessions) try { await session.interrupt?.(); } catch (error) { failures.push(error); }
    for (const session of sessions) try { await session.close(); } catch (error) { failures.push(error); }
    for (const broker of brokers) try {
      const outcome = await broker.quiesce();
      requireValue(outcome?.quiescent !== false && broker.isQuiescent?.() !== false,
        'CODEX_BROKER_STOP_UNCONFIRMED', 'The failed producer still owns execution');
    } catch (error) { failures.push(error); }
    entry.cleanupPending = failures.length > 0;
    if (failures.length) throw Object.assign(new AggregateError(failures, 'Failed producer cleanup is unconfirmed'), { code: 'FAIL_NODE_STOP_INCOMPLETE' });
    entry.session = null; entry.sessions = []; entry.broker = null; entry.brokers = [];
    entry.status = 'stopped';
  }

  async failAttemptAfterQuiescence(runId, args, error, { originEntry = null, originManager = null, commitFailure = true } = {}) {
    this.fenceAttempt(runId, args.node_id, args.attempt_id);
    if (originEntry) await this.quiesceOrigin(originEntry);
    await this.drainAttempt(runId, args.node_id, args.attempt_id, { skipManager: originManager });
    const current = await this.runtime.get(runId);
    const node = current.nodes[args.node_id];
    if (!commitFailure || node?.active_attempt_id !== args.attempt_id || !['claimed', 'running'].includes(node.status)) return current;
    return this.runtime.failNode(runId, { ...args, error });
  }

  scheduleDrain(runId) {
    if (this.jobs.has(runId) && !this.errors.has(runId)) return this.jobs.get(runId);
    this.errors.delete(runId);
    const job = Promise.resolve().then(() => this.drainRun(runId));
    this.jobs.set(runId, job);
    void job.then(() => this.errors.delete(runId), error => { this.errors.set(runId, error); console.error(`Workflow Run ${runId} execution cleanup incomplete:`, error); });
    return job;
  }

  async waitDrain(runId) { if (this.jobs.has(runId)) await this.jobs.get(runId); }

  managerOwners(runId, attemptId = null) {
    return [this.strictManager, this.managedNativeManager, this.hostMainManager].flatMap(manager =>
      [...manager.entries.values()].filter(entry => entry.runId === runId
        && (!attemptId || (entry.args?.attempt_id ?? entry.handoff?.host_binding?.attempt_id) === attemptId) && owned(entry)));
  }

  async assertAttemptQuiescent(record, nodeId, attempt, { allowPausedChildren = false } = {}) {
    const runId = record.state.run_id;
    requireValue(!this.admission.pendingAttempt(runId, nodeId, attempt.id).length && !this.managerOwners(runId, attempt.id).length,
      'EXECUTION_OWNER_ACTIVE', 'The exact attempt still has active or unconfirmed local execution ownership');
    if (attempt.child_run_id) {
      const child = await this.runtime.runs.read(attempt.child_run_id);
      requireValue((terminalRun.has(child.state.status) || allowPausedChildren && child.state.status === 'paused') && !this.admission.pending(attempt.child_run_id).length
        && !this.managerOwners(attempt.child_run_id).length,
        'EXECUTION_OWNER_ACTIVE', 'The exact child Run has not finished and settled its execution ownership');
      for (const [childNodeId, childNode] of Object.entries(child.state.nodes))
        for (const childAttempt of childNode.attempts) await this.assertAttemptQuiescent(child, childNodeId, childAttempt, { allowPausedChildren });
    }
    const definition = record.pins.root.workflow.nodes.find(node => node.id === nodeId);
    const provider = record.pins.providers.find(item => item.id === definition?.executor?.provider_id);
    if (provider?.kind === 'builtin_connector' && attempt.dispatch) {
      let task;
      try { task = await this.registry.status(attempt.id, 0); }
      catch (error) { if (error.code === 'TASK_NOT_FOUND' && !attempt.dispatch.receipt) return; throw error; }
      await confirmConnectorExecutionQuiescent(this.registry, attempt.id);
    }
  }

  async assertRunQuiescent(record, { allowPausedChildren = false } = {}) {
    requireValue(!this.admission.pending(record.state.run_id).length && !this.managerOwners(record.state.run_id).length,
      'EXECUTION_OWNER_ACTIVE', 'Run still has local execution ownership');
    for (const [nodeId, node] of Object.entries(record.state.nodes))
      for (const attempt of node.attempts) await this.assertAttemptQuiescent(record, nodeId, attempt, { allowPausedChildren });
  }

  async stopConnector(record, nodeId, attempt) {
    const definition = record.pins.root.workflow.nodes.find(node => node.id === nodeId);
    const provider = record.pins.providers.find(item => item.id === definition?.executor?.provider_id);
    if (provider?.kind !== 'builtin_connector' || !attempt.dispatch) return;
    let task;
    try { task = await this.registry.status(attempt.id, 0); }
    catch (error) { if (error.code === 'TASK_NOT_FOUND' && !attempt.dispatch.receipt) return; throw error; }
    requireValue(task.task_id === attempt.id && task.provider_id === provider.id && task.stage_id === nodeId
      && task.task_type_id === record.state.workflow_id, 'CONNECTOR_IDENTITY', 'The connector task does not match its pinned attempt');
    if (!terminalTask.has(task.state)) {
      const remote = task.remote_identity ?? {};
      task = await this.registry.control(attempt.id, { action: 'cancel', confirm: true,
        ...(remote.agent_id ? { expected_agent_id: remote.agent_id } : {}),
        ...(remote.session_id ? { expected_session_id: remote.session_id } : {}),
        ...(remote.run_id ? { expected_run_id: remote.run_id } : {}) });
      if (!terminalTask.has(task.state)) task = await this.registry.status(attempt.id, 5_000);
    }
    task = await confirmConnectorExecutionQuiescent(this.registry, attempt.id);
    await this.runtime.runs.mutate(record.state.run_id, 'execution_drain', state => {
      const current = state.nodes[nodeId]?.attempts.find(item => item.id === attempt.id);
      requireValue(current, 'ATTEMPT_MISSING', 'Connector cleanup lost its exact attempt');
      current.connector_control = { action: 'cancel', phase: 'observed', state: task.state, at: new Date().toISOString() };
      if (current.dispatch) current.dispatch.cancellation_pending = false;
    });
  }

  async drainRun(runId, seen = new Set(), { cancelChildren = true } = {}) {
    requireValue(!seen.has(runId) && seen.size < 4096, 'RUN_EXECUTION_TREE', 'Invalid execution ownership tree');
    seen.add(runId); this.fenceRun(runId);
    const record = await this.runtime.runs.read(runId);
    const children = [...new Set(Object.values(record.state.nodes).flatMap(node => node.attempts.flatMap(attempt => attempt.child_run_id ? [attempt.child_run_id] : [])))];
    for (const childId of children) this.fenceRun(childId);
    const stopped = await Promise.allSettled([
      this.strictManager.stopRun(runId), this.managedNativeManager.stopRun(runId), this.hostMainManager.stopRun(runId),
      (async () => { await this.admission.retryCleanup(runId, 'connector'); await this.admission.wait(runId); })(),
    ]);
    const errors = failed(stopped);
    for (const [nodeId, node] of Object.entries(record.state.nodes)) for (const attempt of node.attempts) {
      try { await this.stopConnector(record, nodeId, attempt); } catch (error) { errors.push(error); }
    }
    for (const childId of children) {
      try {
        await this.runtime.runs.mutate(childId, 'parent_execution_lost', state => {
          if (state.status === 'running') { interruptActiveNodes(state, 'Parent Run lost execution authority'); state.status = cancelChildren ? 'cancelled' : 'interrupted'; }
        });
        await this.drainRun(childId, seen, { cancelChildren });
      } catch (error) { errors.push(error); }
    }
    if (errors.length) throw Object.assign(new AggregateError(errors, 'Run execution cleanup is unconfirmed'), { code: 'RUN_EXECUTION_STOP_INCOMPLETE' });
  }
}
