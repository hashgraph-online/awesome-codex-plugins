import { useContext, useEffect, useMemo, useState } from 'react';
import { api, JsonField, Details, Status, FormValidContext, pretty, useLocale, type Json, uid } from './shared';
import { Canvas } from './canvas';
import { createRunRefresh, loadRunPanelSnapshot } from './run-refresh.mjs';
import { strictSessionPresentation } from './strict-session-view.mjs';
export const controllers = new Map<string, string>();
const leases = new Map<string, Json>();
export function rememberRun(run: Json) {
  if (run.control_token && controllers.get(run.run_id) !== run.control_token) {
    for (const id of run.stopped_run_ids ?? []) if (id !== run.run_id) controllers.delete(id);
    for (const key of leases.keys()) if (key.startsWith(run.run_id + '/')) leases.delete(key);
    controllers.set(run.run_id, run.control_token);
  }
  return run.run_id as string;
}
export function RunPanel({ runId, providers, act, onRun }: { runId: string, providers: Json[], act: (work: () => Promise<any>) => void, onRun: (id: string) => void }) {
  const t = useLocale();
  const [snapshot, setSnapshot] = useState<Json | null>(null); const [pack, setPack] = useState<Json | null>(null);
  const state = snapshot?.state; const next = snapshot?.next ?? {}; const events = snapshot?.events ?? []; const liveSnapshot = snapshot?.live ?? null;
  const bridgeProposal = snapshot?.bridgeProposal ?? null;
  const [nodeId, setNodeId] = useState(''); const [result, setResult] = useState<Json | null>(null); const [login, setLogin] = useState<Json | null>(null);
  const [nodeDetails, setNodeDetails] = useState<Json | null>(null);
  const [receipt, setReceipt] = useState<Json>({}); const [completion, setCompletion] = useState<Json>({ status: 'succeeded', summary: '', structured_output: {}, artifacts: [], evidence: [], changed_paths: [], outside_paths: [] });
  const refreshController = useMemo(() => createRunRefresh(), [runId]);
  const valid = useContext(FormValidContext);
  const [accepted, setAccepted] = useState(false); const [merge, setMerge] = useState<Json | null>(null); const [reconciliation, setReconciliation] = useState<Json>({}); const [connectorControl, setConnectorControl] = useState<Json>({});
  const token = controllers.get(runId); const control = { run_id: runId, control_token: token };
  const key = runId + '/' + nodeId; const lease = leases.get(key); const args = { ...control, ...(lease ? { node_id: nodeId, attempt_id: lease.attempt_id, lease_token: lease.lease_token } : {}) };
  const liveStatusLabel = (status: unknown) => {
    const value = String(status ?? '');
    const labels: Record<string, [string, string]> = { unavailable: ['不可用', 'Unavailable'], closed: ['已关闭', 'Closed'], auth_required: ['需要认证', 'Authentication required'], running: ['运行中', 'Running'], claimed: ['已领取', 'Claimed'] };
    return labels[value] ? t(...labels[value]) : value;
  };
  async function refresh() {
    return refreshController.refresh((previous: Json | null) => loadRunPanelSnapshot(api, runId, controllers.get(runId), previous, async ({ state: s }: Json) => {
      let nextLive = null;
      if (lease && pack?.workflow.skill_policy.mode === 'strict' && ['claimed','running'].includes(s.nodes[nodeId]?.status) && s.nodes[nodeId]?.attempts.at(-1)?.dispatch?.receipt?.executor === 'codex-app-server') {
        try { nextLive = { attempt_id: lease.attempt_id, value: await api('strict_status', args) }; }
        catch (cause) {
          if ((cause as any).detail?.code !== 'STRICT_SESSION_UNAVAILABLE') throw cause;
          nextLive = { attempt_id: lease.attempt_id, value: { status: 'unavailable', error: (cause as any).detail } };
        }
      }
      return nextLive;
    }), setSnapshot);
  }
  useEffect(() => {
    let current = true;
    refreshController.activate();
    setSnapshot(null); setPack(null); setNodeId(''); setResult(null); setLogin(null); setMerge(null);
    act(async () => {
      const definition = await api('run_definition', { run_id: runId });
      if (!current) return;
      setPack(definition); await refresh();
    });
    return () => { current = false; refreshController.dispose(); };
  }, [runId]);
  useEffect(() => { if (['succeeded','failed','cancelled'].includes(state?.status)) return; let stopped = false; let timer: ReturnType<typeof setTimeout>; const poll = async () => { if (stopped) return; try { await refresh(); } catch (error) { act(async () => { throw error; }); return; } if (!stopped) timer = setTimeout(poll, 2500); }; timer = setTimeout(poll, 2500); return () => { stopped = true; clearTimeout(timer); }; }, [runId, token, nodeId, lease?.attempt_id, pack?.revision_hash, state?.status]);
  useEffect(() => {
    let current = true;
    const selectedRunId = runId;
    const selectedNodeId = nodeId;
    refreshController.invalidate();
    setResult(null); setLogin(null); setAccepted(false); setSnapshot(value => value ? { ...value, live: null } : value); setNodeDetails(null);
    if (selectedNodeId) act(async () => {
      const details = await api('node_details', { run_id: selectedRunId, node_id: selectedNodeId });
      if (current) setNodeDetails(details);
    });
    return () => { current = false; };
  }, [runId, nodeId]);
  const call = (operation: string, extra: Json = {}) => act(async () => { if (!valid) throw new Error(t('请先修正 JSON 格式错误。', 'Fix the invalid JSON first.')); const value = await api(operation, { ...args, ...extra }); if (value.child?.control_token) rememberRun(value.child); setResult(value); await refresh(); });
  const recover = (operation: string) => act(async () => { if (!valid) throw new Error(t('请先修正 JSON 格式错误。', 'Fix the invalid JSON first.')); const value = await api(operation, { ...control, node_id: nodeId, attempt_id: state?.nodes[nodeId]?.attempts.at(-1)?.id, reconciliation }); leases.set(key, value.envelope); if (value.child?.control_token) rememberRun(value.child); setResult(value); await refresh(); });
  if (!state || !pack) return <section className="detail-page">{t('读取固定 Run…', 'Loading pinned Run…')}</section>;
  const current = state.nodes[nodeId]; const definition = pack.workflow.nodes.find((n: Json) => n.id === nodeId); const attempt = current?.attempts.at(-1);
  const live = strictSessionPresentation(current, liveSnapshot);
  const currentLogin = live?.show_login && login?.attempt_id === attempt?.id ? login?.value : null;
  return <div className="run-workspace"><div className="run-toolbar"><strong>{pack.workflow.name}</strong><Status value={state.status}/><span className="muted">{runId} · #{state.sequence}</span><button onClick={() => act(refresh)}>{t('刷新', 'Refresh')}</button>
    {token && <><button disabled={state.status !== 'running'} onClick={() => call('pause', { reason: '用户暂停' })}>{t('暂停', 'Pause')}</button><button disabled={!['paused','blocked','interrupted'].includes(state.status)} onClick={() => call('resume')}>{t('继续', 'Resume')}</button><button className="danger" disabled={['succeeded','cancelled'].includes(state.status)} onClick={() => call('cancel')}>{t('取消 Run', 'Cancel Run')}</button></>}
  </div>
  {!token && <div className="notice">{t('此页面只读。可在 Codex 主会话中授权恢复此 Run，或在此接管。接管会使旧控制权和租约失效，并暂停整个 Run 树，不会自动批准或完成节点。子 Run 从父节点领取其控制权。', 'This page is read only. Authorize recovery of this Run in the main Codex conversation, or take control here. Recovery invalidates old control and leases and pauses the entire Run tree; it does not approve or complete nodes. Child Runs claim control from their parent.')}<button onClick={() => act(async () => { const adopted = await api('adopt_run', { run_id: runId, expected_sequence: state.sequence, reason: '用户在本地控制台显式接管', main_actor: 'human-console' }); rememberRun(adopted); setResult(adopted); await refresh(); })}>{t('接管并暂停 Run', 'Take control and pause Run')}</button></div>}
  {state.control_recovery?.errors?.length > 0 && <div className="error-banner" role="alert">{t('恢复或清理尚未完成，继续运行已阻止。', 'Recovery or cleanup is incomplete; continued execution is blocked.')}<Details title={t('待处理错误', 'Pending errors')} value={state.control_recovery.errors}/></div>}
  <div className="run-body"><Canvas workflow={pack.workflow} runtime={{ nodes: state.nodes, loops: state.loops }} providers={providers} onChange={() => {}} onSelect={(kind,id) => { if (kind === 'node') setNodeId(id); }} readOnly/>
    <aside className="inspector scroll"><h2>{nodeId || t('运行详情', 'Run details')}</h2>{!nodeId && <p>{t('选择节点查看状态、产物、证据及可用操作。', 'Select a node to view its status, artifacts, evidence, and available actions.')}</p>}
      {!!pack.workflow.loops?.length && <section className="loop-run-summary"><h3>{t('返修循环状态', 'Repair loop status')}</h3>{pack.workflow.loops.map((loop: Json) => {
        const currentLoop = state.loops?.[loop.id] ?? {};
        return <article className="loop-run-item" key={loop.id}><div><strong>{loop.id}</strong><Status value={currentLoop.status}/><span className="loop-round-badge">{t('第', 'Round ')}{currentLoop.round ?? 0}/{loop.max_rounds}</span></div>
          <Details title={t('本循环的轮次、反馈与验收项', 'Rounds, feedback, and accepted items')} value={currentLoop}/></article>;
      })}</section>}
      {state.environment_attention && <section role="status"><h3>{t('节点 0：重新准备依赖','Step 0: prepare dependencies again')}</h3><p>{t('本机依赖已失效，尚未执行的步骤会等待重新登记。可在「执行能力」填写已有安装路径；安装新依赖前需要同意。','A local dependency is unavailable. Pending steps wait for re-registration. Register an existing installation in Execution; installing a dependency requires approval.')}</p><Details title={t('发现结果','Discovery results')} value={state.environment_attention}/><button disabled={!token} onClick={()=>act(async()=>{await api('recheck_runtime_environment',control);await refresh();})}>{t('重新发现并验证','Rediscover and verify')}</button></section>}
      {!nodeId && (state.runtime_environment ?? state.constraints?.runtime_environment) && <Details title={t('本次运行的依赖位置','Runtime dependency locations')} value={state.runtime_environment ?? state.constraints.runtime_environment}/>}
      <Details title={t('输入、范围与固定版本', 'Inputs, scope, and pinned revision')} value={{ inputs: state.inputs, permissions: state.permissions, revision: pack.revision_hash, finalization: pack.workflow.finalization }}/>
      {next.parent_block && <Details title={t('父 Run 阻塞', 'Parent Run blocked')} value={next.parent_block}/>}
      {(next.pending_approvals ?? next.approvals ?? []).map((approval: Json) => <article className="review-item" key={approval.id}><Details title={t('待批准的节点与范围', 'Node and scope awaiting approval')} value={approval}/>{token && <><button onClick={() => call('approve', { approval_id: approval.id, decision: true })}>{t('批准此范围', 'Approve this scope')}</button><button onClick={() => call('approve', { approval_id: approval.id, decision: false })}>{t('拒绝', 'Reject')}</button></>}</article>)}
      {bridgeProposal?.kind === 'final_acceptance' && <article className="review-item"><h3>{t('隔离 Main 最终验收', 'Isolated Main final acceptance')}</h3><p>{t('语义提案由 Host 管理的隔离 Main 节点生成；模型没有接触控制令牌、租约或工作流生命周期工具。请审查后明确接受或拒绝。', 'The semantic proposal came from a Host-managed isolated Main node; the model never received controller tokens, leases, or Workflow lifecycle tools. Review it, then explicitly accept or reject it.')}</p><Details title={t('待验收提案', 'Proposal awaiting acceptance')} value={{ proposal: bridgeProposal.proposal }}/><button className="primary" onClick={() => act(async () => { setResult(await api('current_main_accept', { run_id: runId, control_token: token, accepted: true })); await refresh(); })}>{t('接受最终提案', 'Accept final proposal')}</button><button onClick={() => act(async () => { setResult(await api('current_main_accept', { run_id: runId, control_token: token, accepted: false })); await refresh(); })}>{t('拒绝最终提案', 'Reject final proposal')}</button></article>}
      {bridgeProposal?.kind === 'control_wait' && <article className="review-item"><h3>{t('后台工作流等待人工控制', 'Background Workflow awaiting human control')}</h3><Details title={t('等待原因', 'Waiting outcome')} value={bridgeProposal.outcome}/>{bridgeProposal.outcome?.stop_reason === 'approval' && (bridgeProposal.outcome.approvals ?? []).map((approval: Json) => <div key={approval.id}><button className="primary" onClick={() => act(async () => { setResult(await api('current_main_approve', { run_id: runId, control_token: token, owner: state.main_actor, approval_id: approval.id, decision: true })); await refresh(); })}>{t('批准', 'Approve')} · {approval.node_id ?? approval.id}</button><button onClick={() => act(async () => { setResult(await api('current_main_approve', { run_id: runId, control_token: token, owner: state.main_actor, approval_id: approval.id, decision: false })); await refresh(); })}>{t('拒绝', 'Reject')}</button></div>)}<button onClick={() => act(async () => { setResult(await api('current_main_cancel', { run_id: runId, control_token: token })); await refresh(); })}>{t('取消 Run', 'Cancel Run')}</button></article>}
      {bridgeProposal?.kind === 'host_main' && <article className="review-item"><h3>{t('Host Main 执行状态', 'Host Main execution status')}</h3><Details title={t('执行状态与诊断', 'Execution status and diagnostics')} value={bridgeProposal}/></article>}
      {(next.integration_gates ?? []).map((gate: Json | string) => { const id = typeof gate === 'string' ? gate : gate.region_id; return <button disabled={!token} key={id} onClick={() => act(async () => { await api('prepare_integration', { ...control, region_id: id }); setMerge({ region_id: id, ...(await api('review_integration', { ...control, region_id: id })) }); await refresh(); })}>{t('审查并行合并', 'Review parallel merge')} · {id}</button>; })}
      {merge && <article className="review-item"><h3>{t('精确合并提案', 'Exact merge proposal')}</h3><pre>{typeof merge.patch === 'string' ? merge.patch : pretty(merge)}</pre><button disabled={!token} onClick={() => call('integrate_parallel', { region_id: merge.region_id, patch_sha256: merge.patch_sha256 ?? merge.proposal?.patch_sha256, accepted: true })}>{t('接受并应用所示补丁', 'Accept and apply the shown patch')}</button></article>}
      {current && <><Status value={current.status}/><Details title={t('节点输出、证据和诊断', 'Node output, evidence, and diagnostics')} value={current}/>
        <p>{t('尝试 ', 'Attempts ')}{current.attempts.length} · {attempt?.owner ?? t('尚未领取', 'Not claimed')}</p>
        {attempt?.started_at && <p>{t('本次尝试历时 ', 'This attempt has run for ')}{Math.max(0, Math.floor(((attempt.finished_at ? Date.parse(attempt.finished_at) : Date.now()) - Date.parse(attempt.started_at)) / 1000))}{t(' 秒（含暂停和恢复等待）', ' seconds (including pause and resume waits)')}</p>}
        {nodeDetails && <Details title={t('固定 Provider、有效访问范围与 Skill 策略', 'Pinned Provider, effective access scope, and Skill policy')} value={nodeDetails}/>}
        {attempt?.dispatch?.cancellation_pending && <p role="status">{t('本地执行已停止接受结果；远程停止尚未确认。请核对原任务状态。', 'Local execution stopped accepting results; remote stop is not confirmed. Check the original task status.')}</p>}
        {live && <><p role="status">{t('Strict 会话：', 'Strict session: ')}{liveStatusLabel(live.status)}</p>{live.error && <Details title={t('会话诊断', 'Session diagnostics')} value={live.error}/>} {['claimed','running'].includes(current.status) && live.status !== 'closed' && <details open={!!live.output_preview?.text}><summary>{t('实时输出预览 · 尚未验收', 'Live output preview · not yet accepted')}</summary><pre>{live.output_preview?.text || t('尚无输出', 'No output yet')}</pre>{live.output_preview?.truncated && <small>{t('仅展示最近 32K 字符；最终结果以持久化产物为准。', 'Showing only the latest 32K characters; the persisted artifact is authoritative for the final result.')}</small>}</details>}</>}
        {token && current.status === 'ready' && <button className="primary" onClick={() => act(async () => { const value = await api('claim_node', { ...control, node_id: nodeId, owner: state.main_actor, request_id: uid('claim') }); leases.set(key, value); setResult(value); await refresh(); })}>{t('领取节点', 'Claim node')}</button>}
        {token && ['interrupted','failed'].includes(current.status) && <><JsonField label={t('重试 / Host 重连证据', 'Retry / host re-connection evidence')} value={reconciliation} onChange={setReconciliation}/><button onClick={() => call('retry_node', { node_id: nodeId, reconciliation })}>{t('显式重试（消耗预算）', 'Explicit retry (consumes budget)')}</button>{current.status === 'interrupted' && <>
          {!attempt.dispatch ? <button onClick={() => recover('recover_claim')}>{t('恢复尚未派发的原尝试', 'Recover the original attempt that was not dispatched')}</button> : definition.executor.kind === 'subworkflow' ? <button onClick={() => recover('reattach_subworkflow')}>{t('重连原子 Run', 'Reattach the atomic Run')}</button> : pack.workflow.skill_policy.mode === 'strict' ? <button onClick={() => recover('recover_strict_result')}>{t('恢复已持久化的 Strict 结果', 'Recover the persisted Strict result')}</button> : attempt.dispatch.receipt?.connector ? <button onClick={() => recover('reattach_connector')}>{t('核对并重连同一远程任务', 'Verify and reattach the same remote task')}</button> : <button onClick={() => recover('reattach_handoff')}>{t('按 Host 的精确身份核对记录重连', 'Verify the exact Host identity record and reattach')}</button>}
        </>}</>}
        {lease && token && ['claimed','running'].includes(current.status) && <>
          {!attempt?.dispatch && <button className="primary" disabled={state.status !== 'running'} onClick={() => call('dispatch')}>{t('执行固定节点', 'Execute pinned node')}</button>}
          {attempt?.dispatch && <>
            {pack.workflow.skill_policy.mode === 'strict' && definition.executor.kind !== 'subworkflow' && <><button onClick={() => call('strict_status')}>{t('读取 Strict 会话状态', 'Read Strict session status')}</button>{live?.show_login && <button onClick={() => act(async () => setLogin({ attempt_id: attempt.id, value: await api('strict_login', args) }))}>{t('获取此会话的官方登录链接', 'Get the official sign-in link for this session')}</button>}{definition.role === 'finalizer' && <label className="check"><input type="checkbox" checked={accepted} onChange={e => setAccepted(e.target.checked)}/>{t('我已审查并接受主节点提案', 'I reviewed and accept the Main node proposal')}</label>}<button onClick={() => call('collect_strict', { accepted })}>{t('收集固定 Strict 结果', 'Collect pinned Strict result')}</button></>}
            {definition.executor.kind === 'subworkflow' && <><button onClick={() => call('collect_subworkflow')}>{t('收集子 Run 验收结果', 'Collect child Run acceptance result')}</button>{attempt.child_run_id && <button onClick={() => act(async () => { const child = await api('child_control', args); rememberRun(child); onRun(child.run_id); })}>{t('打开并管理原子 Run', 'Open and manage atomic Run')}</button>}</>}
            {definition.executor.kind === 'provider' && pack.workflow.skill_policy.mode === 'cooperative' && <><button onClick={() => call('reconcile_connector')}>{t('核对 Connector 身份', 'Verify Connector identity')}</button><button onClick={() => call('collect_connector')}>{t('收集 Connector 结果', 'Collect Connector result')}</button></>}
          </>}
          {pack.workflow.skill_policy.mode === 'cooperative' && definition.executor?.kind !== 'main' && <details><summary>{t('Host / Human 执行结果交接', 'Host / human execution result handoff')}</summary><p>{t('填写真实工具返回的身份、产物及验证证据。此页面不会代替主会话创建、续聊或收集 Codex task；必须使用派发结果中的精确 task ID。', 'Enter the identity, artifacts, and verification evidence returned by the real tool. This page does not create, continue, or collect Codex tasks on behalf of the Main session; use the exact task ID from the dispatch result.')}</p><JsonField label={t('真实派发回执', 'Actual dispatch receipt')} value={receipt} onChange={setReceipt}/><button onClick={() => call('dispatch_receipt', { receipt, request_id: attempt?.dispatch?.request_id })}>{t('记录精确回执', 'Record exact receipt')}</button><JsonField label={t('完成记录（需真实证据）', 'Completion record (real evidence required)')} value={completion} onChange={setCompletion} rows={14}/><label className="check"><input type="checkbox" checked={accepted} onChange={e => setAccepted(e.target.checked)}/>{t('主控制者接受最终结果', 'Main controller accepts the final result')}</label><button onClick={() => call('complete_node', { completion: { ...completion, ...(definition.role === 'finalizer' ? { acceptance: { accepted } } : {}) } })}>{t('提交完成记录', 'Submit completion record')}</button></details>}
        </>}
      </>}
      {token && lease && attempt?.dispatch?.receipt?.connector && <details><summary>{t('远程取消、权限或输入响应', 'Remote cancellation, permission, or input response')}</summary><p>{t('使用最近一次 Connector 状态返回的精确 request_id、选项和远程身份。取消 Run 会先使本地租约失效；远程停止需要确认。', 'Use the exact request_id, options, and remote identity from the latest Connector status response. Cancelling the Run first invalidates the local lease; remote stopping requires confirmation.')}</p><JsonField label={t('Connector 控制请求', 'Connector control request')} value={connectorControl} onChange={setConnectorControl}/><button onClick={() => call('control_connector', { control: connectorControl })}>{t('提交所示控制请求', 'Submit the shown control request')}</button></details>}
      {currentLogin && <Details title={t('此会话登录信息', 'This session sign-in information')} value={currentLogin}/>}
      {currentLogin && Object.entries(currentLogin).filter(([key,value]) => /url/i.test(key) && typeof value === 'string' && /^https?:\/\//.test(value)).map(([key,value]) => <a key={key} href={String(value)} target="_blank" rel="noreferrer">{t('打开官方登录页面', 'Open the official sign-in page')}</a>)}
      {result && <Details title={t('最近一次操作结果', 'Most recent operation result')} value={result}/>}
      {token && ['succeeded','failed','cancelled'].includes(state.status) && <button onClick={() => call('cleanup_parallel')}>{t('清理已验收且未变化的工作树', 'Clean up accepted, unchanged worktrees')}</button>}
      {state.status === 'succeeded' && ['authoring_workflow_run','skill_expansion_job'].includes(pack.provenance?.kind) && token && <button onClick={() => call('apply_authoring_result', { workflow_id: pack.provenance.source_workflow_id, expected_revision: pack.provenance.source_revision })}>{t('将验收后的规划应用到源 Draft', 'Apply the accepted plan to the source Draft')}</button>}
      <Details title={t('运行事件（后端日志）', 'Run events (backend log)')} value={events}/>
    </aside></div></div>;
}
