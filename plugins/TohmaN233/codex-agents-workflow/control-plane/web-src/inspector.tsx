import { useState } from 'react';
import { Field, JsonField, ProviderField, Select, Details, useLocale, type Json, uid } from './shared';
import { findUpstreamThreadSources, resolveThreadSource } from './thread-source-options.mjs';
import { renameLoopId } from './graph-adapter.mjs';

function LoopSelectorField({ label, value, placeholder, onChange }: { label: string, value: any, placeholder: string, onChange: (value: any) => void }) {
  const t = useLocale();
  if (value !== undefined && value !== null && typeof value !== 'string') return <JsonField label={label} value={value} onChange={onChange}/>;
  return <>
    <Field label={label} value={value ?? ''} placeholder={placeholder} onChange={onChange}/>
    <details><summary>{t('高级选择器（JSON）', 'Advanced selector (JSON)')}</summary><JsonField label={label} value={value ?? null} onChange={onChange}/></details>
  </>;
}

function loopBooleanPath(condition: Json) {
  if (condition?.op !== 'eq' || !Array.isArray(condition.args) || condition.args.length !== 2) return '';
  const [left, right] = condition.args;
  if (typeof left?.path === 'string' && right?.value === true) return left.path;
  if (typeof right?.path === 'string' && left?.value === true) return right.path;
  return '';
}

function LoopRegions({ workflow, change }: { workflow: Json, change: (w: Json) => void }) {
  const t = useLocale(); const loops: Json[] = workflow.loops ?? []; const [roundInputs, setRoundInputs] = useState<Record<string, string>>({});
  const setLoops = (next: Json[]) => change({ ...workflow, loops: next });
  const patchLoop = (id: string, fields: Json) => setLoops(loops.map(loop => loop.id === id ? { ...loop, ...fields } : loop));
  const setItemScope = (id: string, item_scope: Json | null) => setLoops(loops.map(loop => {
    if (loop.id !== id) return loop;
    const next = { ...loop }; if (item_scope) next.item_scope = item_scope; else delete next.item_scope; return next;
  }));
  const renameLoop = (oldId: string, id: string) => change(renameLoopId(workflow, oldId, id));
  const addLoop = () => {
    const id = uid('loop');
    setLoops([...loops, { id, entry_node: '', exit_node: '', node_ids: [], max_rounds: 3, until: {} }]);
  };
  const nodeOptions = workflow.nodes.map((node: Json) => ({ value: node.id, label: `${node.name ?? node.id} · ${node.id}` }));
  return <section className="loop-editor">
    <div className="loop-editor-heading"><div><h3>{t('返修循环', 'Repair loops')}</h3><p>{t('只在所选 DAG 区域内重复审查与修复。循环次数包含第一轮审查。', 'Repeat review and repair only inside a selected DAG region. The round limit includes the first review.')}</p></div>
      <button type="button" onClick={addLoop}>{t('添加循环', 'Add loop')} ＋</button></div>
    {!loops.length && <p className="muted">{t('此 Workflow 尚未定义返修循环。', 'This Workflow has no repair loop.')}</p>}
    {loops.map((loop, index) => <details className="loop-editor-item" key={index} open>
      <summary>{loop.id || `${t('循环', 'Loop')} ${index + 1}`} · {loop.node_ids?.length ?? 0} {t('个节点', 'nodes')}</summary>
      <Field label={t('循环 ID', 'Loop ID')} value={loop.id} onChange={id => renameLoop(loop.id, id)}/>
      <Select label={t('入口节点', 'Entry node')} value={loop.entry_node ?? ''} options={[{ value: '', label: t('请选择入口节点', 'Choose an entry node') }, ...nodeOptions]} onChange={entry_node => patchLoop(loop.id, { entry_node })}/>
      <Select label={t('出口节点', 'Exit node')} value={loop.exit_node ?? ''} options={[{ value: '', label: t('请选择出口节点', 'Choose an exit node') }, ...nodeOptions]} onChange={exit_node => patchLoop(loop.id, { exit_node })}/>
      <fieldset className="loop-node-list"><legend>{t('循环区域内的节点', 'Nodes inside the region')}</legend>
        {workflow.nodes.map((node: Json) => <label className="check" key={node.id}><input type="checkbox" checked={(loop.node_ids ?? []).includes(node.id)} onChange={event => {
          const node_ids = event.target.checked ? [...(loop.node_ids ?? []), node.id] : (loop.node_ids ?? []).filter((id: string) => id !== node.id);
          patchLoop(loop.id, { node_ids });
        }}/>{node.name ?? node.id} <code>{node.id}</code></label>)}
      </fieldset>
      <small>{t('区域由这些节点组成；在 DAG 中连接入口到出口。保存为循环区域不会添加返向连线。', 'Choose the region nodes and connect its entry to its exit in the DAG. The region does not add a backward edge.')}</small>
      <label className="field">{t('最大轮数（包含第一轮审查）', 'Maximum rounds (includes first review)')}<input type="number" min={1} step={1} value={roundInputs[loop.id] ?? String(loop.max_rounds ?? 3)} onChange={event => {
        const value = event.target.value; setRoundInputs(current => ({ ...current, [loop.id]: value }));
        if (value !== '' && Number.isInteger(Number(value))) patchLoop(loop.id, { max_rounds: Number(value) });
      }} onBlur={() => { if (roundInputs[loop.id] === '') patchLoop(loop.id, { max_rounds: 0 }); }}/></label>
      <Field label={t('结束条件的布尔 JSON Pointer', 'Boolean JSON Pointer for the stop condition')} value={loopBooleanPath(loop.until)} placeholder={t('例如：/nodes/review/output/accepted', 'For example: /nodes/review/output/accepted')} onChange={path => patchLoop(loop.id, { until: path ? { op: 'eq', args: [{ path }, { value: true }] } : {} })}/>
      <details><summary>{t('高级结束条件 DSL（JSON）', 'Advanced stop condition DSL (JSON)')}</summary><JsonField label={t('条件 DSL', 'Condition DSL')} value={loop.until ?? {}} onChange={until => patchLoop(loop.id, { until })}/></details>
      {loop.item_scope && <button type="button" onClick={() => patchLoop(loop.id, { until: { op: 'eq', args: [{ path: `/loops/${loop.id}/all_accepted` }, { value: true }] } })}>{t('设为“所有范围项均已接受”', 'Use “all scoped items accepted” condition')}</button>}
      <small>{t('有逐项范围时可使用 all_accepted；否则请把条件指向审查节点的语义输出。', 'With an item scope, use all_accepted; otherwise point the condition to the review node’s semantic output.')}</small>
      <JsonField label={t('反馈输入绑定（可选）', 'Feedback input bindings (optional)')} value={loop.feedback_bindings ?? {}} onChange={feedback_bindings => patchLoop(loop.id, { feedback_bindings })}/>
      <label className="check"><input type="checkbox" checked={!!loop.item_scope} onChange={event => setItemScope(loop.id, event.target.checked ? { items: null, verdicts: null, paths_field: 'files' } : null)}/>{t('启用逐项审查与返修', 'Enable item-level review and repair')}</label>
      {loop.item_scope && <fieldset className="loop-scope-fields"><legend>{t('原始项、审查结论和文件依赖', 'Original items, review verdicts, and file dependencies')}</legend>
        <LoopSelectorField label={t('输入项绑定', 'Items binding')} value={loop.item_scope.items} placeholder="/inputs/items" onChange={items => setItemScope(loop.id, { ...loop.item_scope, items })}/>
        <LoopSelectorField label={t('审查结论绑定', 'Review verdicts binding')} value={loop.item_scope.verdicts} placeholder="/nodes/review/output/verdicts" onChange={verdicts => setItemScope(loop.id, { ...loop.item_scope, verdicts })}/>
        <Field label={t('产物路径字段（必须是字符串数组）', 'Artifact path field (string array)')} value={loop.item_scope.paths_field ?? ''} placeholder="files" onChange={paths_field => setItemScope(loop.id, { ...loop.item_scope, paths_field })}/>
        <label className="check"><input type="checkbox" checked={loop.item_scope.dependencies_field !== undefined} onChange={event => {
          const item_scope = { ...loop.item_scope };
          if (event.target.checked) item_scope.dependencies_field = 'dependencies'; else delete item_scope.dependencies_field;
          setItemScope(loop.id, item_scope);
        }}/>{t('跟踪依赖文件', 'Track dependency files')}</label>
        {loop.item_scope.dependencies_field !== undefined && <Field label={t('依赖路径字段（字符串数组）', 'Dependency path field (string array)')} value={loop.item_scope.dependencies_field} placeholder="dependencies" onChange={dependencies_field => setItemScope(loop.id, { ...loop.item_scope, dependencies_field })}/>}
      </fieldset>}
      <button type="button" className="danger" onClick={() => setLoops(loops.filter(item => item.id !== loop.id))}>{t('删除循环区域', 'Remove loop region')}</button>
    </details>)}
  </section>;
}

export function Inspector({ workflow, selection, providers, change, select, inline }: { workflow: Json, selection: { kind: string, id: string }, providers: Json[], change: (w: Json) => void, select: (kind: string, id: string) => void, inline: () => void }) {
  const t = useLocale();
  const node = workflow.nodes.find((item: Json) => item.id === selection.id); const edge = workflow.edges.find((item: Json) => item.id === selection.id);
  const patch = (fields: Json) => change({ ...workflow, nodes: workflow.nodes.map((item: Json) => item.id === node.id ? { ...item, ...fields } : item) });
  const edgePatch = (fields: Json) => change({ ...workflow, edges: workflow.edges.map((item: Json) => item.id === edge.id ? { ...item, ...fields } : item) });
  const providerId = node?.executor?.provider_id ?? providers.find((provider: Json) => provider.enabled && provider.capabilities?.read)?.id ?? '';
  const threadSources = node ? findUpstreamThreadSources(workflow, node.id) : [];
  const sourceNodeId = node?.executor?.source_node ?? '';
  const sourceResolution = node?.executor?.kind === 'thread'
    ? resolveThreadSource(workflow, node.id, { providerId, sourceNodeId })
    : { options: [], sourceNodeId: '', providerId, needsSelection: false, ambiguous: false, noMatch: false };
  const selectedSource = threadSources.find(source => source.id === sourceNodeId);
  const sourceNeedsSelection = node?.executor?.kind === 'thread' && node.executor.lifecycle === 'continue' && !selectedSource;
  const sourceOptions = threadSources.map(source => ({
    value: source.id,
    label: `${source.id}${source.providerId ? ` · ${source.providerId}` : ''}${source.distance > 1 ? ` · ${t('上游', 'upstream')} ${source.distance} ${t('层', 'levels')}` : ''}`,
  }));
  const sourceProviderId = selectedSource?.providerId ?? node?.executor?.provider_id ?? '';
  const setThreadLifecycle = (lifecycle: string) => {
    if (lifecycle === 'continue') {
      const resolved = resolveThreadSource(workflow, node.id, { providerId, sourceNodeId });
      patch({ executor: {
        ...node.executor,
        kind: 'thread',
        lifecycle,
        source_node: resolved.sourceNodeId,
        provider_id: resolved.providerId,
      }, subagent_count: 'auto', fanout: undefined });
      return;
    }
    patch({ executor: { kind: 'thread', provider_id: node.executor.provider_id, lifecycle } });
  };
  const setAgentExecutor = (kind: string) => {
    if (kind === 'main_worker' || kind === 'main_orchestration') patch({ executor: { kind: 'main', mode: kind === 'main_worker' ? 'worker' : 'orchestration' }, subagent_count: undefined, fanout: undefined });
    else if (kind === 'thread') patch({ executor: { kind: 'thread', provider_id: providerId, lifecycle: 'start' }, subagent_count: node.subagent_count ?? 'auto' });
    else patch({ executor: { kind: 'provider', provider_id: providerId }, subagent_count: node.subagent_count ?? 'auto' });
  };
  const supportsSubagentCount = !!node?.executor && node.executor.kind !== 'main' && !(node.executor.kind === 'thread' && node.executor.lifecycle === 'continue');
  const defaultFanout = (distribution: 'one_per_item' | 'partition') => {
    const input = Object.keys(node?.input_bindings ?? {})[0] ?? 'items';
    const properties = node?.outputs_schema?.properties ?? {};
    const result_output = Object.keys(properties).find(key => properties[key]?.type === 'array') ?? 'results';
    return { input, item_name: 'item', result_output, distribution, scheduling: 'parallel', join: 'all_required' };
  };
  return <aside className="inspector scroll"><div className="panel-heading"><h2>{selection.kind === 'node' && node ? t('节点属性', 'Node properties') : selection.kind === 'edge' && edge ? t('连接属性', 'Connection properties') : t('Workflow 属性', 'Workflow properties')}</h2><button onClick={() => select('workflow', '')}>{t('全局', 'Global')}</button></div>
    {selection.kind === 'node' && node ? <>
      <div className="muted">{node.id} · {node.type}</div>
      <Field label={t('名称', 'Name')} value={node.name ?? node.id} onChange={name => patch({ name })}/>
      {node.type === 'agent' && <>
        <Select label={t('执行方式', 'Execution mode')} value={node.executor?.kind === 'main' ? 'main_' + (node.executor.mode ?? 'worker') : node.executor?.kind ?? 'main_worker'} options={[{value:'main_worker',label:t('主 Agent（worker）· 隔离会话', 'Main (worker) · isolated session')},{value:'main_orchestration',label:t('主 Agent（orchestration）· 当前聊天', 'Main (orchestration) · current conversation')},{value:'provider',label:t('Provider · 原生交接', 'Provider · native handoff')},{value:'thread',label:t('Codex task · 独立会话', 'Codex task · independent session')}]} onChange={setAgentExecutor}/>
        {node.executor?.kind === 'main' && <small>{node.executor.mode === 'orchestration' ? t('由启动任务的当前主 Agent 接手，保留当前聊天的完整可用上下文。请从该聊天启动。', 'The initiating Main Agent takes over with its current conversation context. Start from that conversation.') : t('使用主 Agent 当前模型的新会话，仅接收声明的输入和资源。', 'A fresh session using Main’s current model receives only declared inputs and resources.')}</small>}
        {node.executor?.kind !== 'main' && <fieldset disabled={node.executor?.kind === 'thread' && node.executor.lifecycle === 'continue'}><ProviderField providers={node.executor?.kind === 'thread' ? providers.filter((provider: Json) => provider.kind === 'native_agent') : providers} main={false} label={node.executor?.kind === 'thread' ? t('Task Provider（续聊时由来源决定）', 'Task provider (determined by source when continuing)') : t('固定 Provider', 'Fixed provider')} value={node.executor?.kind === 'thread' && node.executor.lifecycle === 'continue' ? sourceProviderId : node.executor?.provider_id ?? ''} onChange={id => patch({ executor: { ...node.executor, provider_id: id } })}/></fieldset>}
        {supportsSubagentCount && <>
          <Select label={t('子 Agent 数量', 'Sub-Agent count')} value={Number.isInteger(node.subagent_count)?'fixed':'auto'} options={[{value:'auto',label:t('自动（按运行时任务）','Auto (from runtime task)')},{value:'fixed',label:t('固定数量','Fixed count')}]} onChange={mode=>{
            const distribution=mode==='auto'?'one_per_item':'partition';
            patch({subagent_count:mode==='auto'?'auto':Number.isInteger(node.subagent_count)?node.subagent_count:2,...(node.fanout?{fanout:{...node.fanout,distribution}}:mode==='fixed'?{fanout:defaultFanout(distribution)}:{})});
          }}/>
          {Number.isInteger(node.subagent_count) && <label>{t('固定数量（1–32）','Fixed count (1–32)')}<input type="number" min={1} max={32} value={node.subagent_count} onChange={e=>patch({subagent_count:Number(e.target.value),fanout:node.fanout??defaultFanout('partition')})}/></label>}
          <small>{t('auto 按输入列表与 batch_size 确定批数；parallel 可用 max_concurrency 限制同时运行数量，serial 在上一批结果入账后才释放下一批。图上的 ×auto 表示运行时批数。','Auto derives batch count from the input list and batch_size; parallel may use max_concurrency to limit active Agents, while serial releases the next batch only after the previous result is journaled. ×auto is a runtime count.')}</small>
          {!node.fanout && <button type="button" onClick={()=>patch({subagent_count:'auto',fanout:defaultFanout('one_per_item')})}>{t('启用列表 fan-out','Enable list fan-out')}</button>}
          {node.fanout && <><JsonField label={t('运行时 fanout 合同','Runtime fanout contract')} value={node.fanout} onChange={fanout=>patch({fanout})}/><button type="button" onClick={()=>patch({subagent_count:'auto',fanout:undefined})}>{t('关闭列表 fan-out','Disable list fan-out')}</button></>}
        </>}
        {node.executor?.kind === 'thread' && node.executor.lifecycle === 'continue' && <small>{t('续聊复用一个确定的 Codex Task，不提供子 Agent 数量设置。','Continuation reuses one exact Codex task, so sub-Agent count is unavailable.')}</small>}
        <Field label={t('节点职责', 'Node responsibility')} value={node.role} onChange={role => patch({ role })}/>
        {node.executor?.kind === 'thread' && <>
          <Select label={t('Task 生命周期', 'Task lifecycle')} value={node.executor.lifecycle ?? 'start'} options={[{value:'start',label:t('创建独立 Task', 'Create independent task')},...(threadSources.length?[{value:'continue',label:t('续聊已有 Task', 'Continue existing task')}]:[])]} onChange={setThreadLifecycle}/>
          {node.executor.lifecycle === 'continue' && <div className={sourceNeedsSelection ? 'invalid-field' : undefined}>
            <Select label={t('续聊来源节点（必选）', 'Continuation source node (required)')} value={sourceNodeId} options={[{ value: '', label: t('请选择来源节点', 'Select a source node') }, ...sourceOptions]} onChange={source_node => {
              const source = threadSources.find(option => option.id === source_node);
              patch({ executor: { ...node.executor, lifecycle: 'continue', source_node, ...(source?.providerId ? { provider_id: source.providerId } : {}) } });
            }}/>
            {sourceNeedsSelection && <small role="alert">{t(`请选择一个实际的上游 Codex task 作为续聊来源；${sourceResolution.ambiguous ? '存在多个同 Provider 的候选' : '当前 Provider 没有唯一匹配来源'}。`, `Select an actual upstream Codex task as the continuation source; ${sourceResolution.ambiguous ? 'multiple candidates use the same provider' : 'the current provider has no unique matching source'}.`)}</small>}
          </div>}
        </>}
      </>}
      {node.type === 'skill_ref' && <><ProviderField label={t('固定 Provider', 'Fixed provider')} providers={providers} value={node.executor?.kind === 'main' ? '$main' : node.executor?.provider_id ?? ''} onChange={id => patch({ executor: id === '$main' ? { kind: 'main' } : { kind: 'provider', provider_id: id } })}/><Field label={t('节点职责', 'Node responsibility')} value={node.role} onChange={role => patch({ role })}/></>}
      {node.type === 'agent' && <Field label={t('任务指令 / 模板', 'Task instruction / template')} value={node.prompt_template} multiline onChange={prompt_template => patch({ prompt_template })}/>}
      {node.executor && <>
        <Select label={t('访问权限', 'Access')} value={typeof node.access === 'string' ? node.access : '$run'} options={[{value:'read_only',label:t('只读','Read only')},{value:'bounded_write',label:t('受限写入','Bounded write')}, ...(['main','subworkflow'].includes(node.executor.kind) ? [{ value: '$run', label: t('继承 Run 权限', 'Inherit Run access') }] : [])]} onChange={access => patch({ access: access === '$run' ? { binding: 'run.access' } : access })}/>
        <JsonField label={t('写入路径范围（非 glob；或 Run 绑定）', 'Write path scope (no glob; or Run binding)')} value={node.path_scope ?? []} onChange={path_scope => patch({ path_scope })}/>
        <label className="check"><input type="checkbox" checked={!!node.approval?.required} onChange={e => patch({ approval: { ...node.approval, required: e.target.checked } })}/>{t('执行前需批准', 'Approval required before execution')}</label>
        <Field label={t('最大尝试次数（1–10）', 'Maximum attempts (1–10)')} value={node.retry?.max_attempts} onChange={value => patch({ retry: { ...node.retry, max_attempts: Number(value) } })}/>
        <JsonField label={t('输入绑定（上游 JSON Pointer）', 'Input bindings (upstream JSON Pointer)')} value={node.input_bindings ?? {}} onChange={input_bindings => patch({ input_bindings })}/>
        <JsonField label={t('输出 Schema', 'Output schema')} value={node.outputs_schema ?? {}} onChange={outputs_schema => patch({ outputs_schema })}/>
        <JsonField label={t('资源路径', 'Resource paths')} value={node.resources ?? []} onChange={resources => patch({ resources })}/>
        <details><summary>{t('节点 Skill 策略（只可收紧）', 'Node Skill policy (tightening only)')}</summary><JsonField label={t('留空对象表示继承', 'An empty object means inherit')} value={node.skill_policy ?? {}} onChange={value => { const next = { ...node }; if (!Object.keys(value).length) delete next.skill_policy; else next.skill_policy = value; change({ ...workflow, nodes: workflow.nodes.map((n: Json) => n.id === node.id ? next : n) }); }}/></details>
      </>}
      {node.type === 'condition' && <><JsonField label={t('按顺序匹配的条件 DSL', 'Conditions DSL matched in order')} value={node.cases} onChange={cases => patch({ cases })}/><Field label={t('默认连接标签', 'Default connection label')} value={node.default_label} onChange={default_label => patch({ default_label })}/></>}
      {node.type === 'parallel' && <><Select label={t('汇合节点', 'Join node')} value={node.join_id} options={workflow.nodes.filter((n: Json) => n.type === 'join').map((n: Json) => n.id)} onChange={join_id => patch({ join_id })}/><Select label={t('分支失败策略', 'Branch failure policy')} value={node.failure_policy} options={[{value:'collect',label:t('收集所有结果','Collect all results')},{value:'fail_fast',label:t('快速失败','Fail fast')}]} onChange={failure_policy => patch({ failure_policy })}/></>}
      {node.type === 'join' && <Select label={t('对应并行节点', 'Matching parallel node')} value={node.parallel_id} options={workflow.nodes.filter((n: Json) => n.type === 'parallel').map((n: Json) => n.id)} onChange={parallel_id => patch({ parallel_id })}/>}
      {node.type === 'skill_ref' && <><JsonField label={t('SkillRef（精确路径、名称、哈希、嵌套 pin）', 'SkillRef (exact path, name, hash, nested pins)')} value={node.skill_ref} onChange={skill_ref => patch({ skill_ref })}/><button onClick={inline}>{t('将已保存的 SkillRef 转为 Inline Draft', 'Convert the saved SkillRef to an inline draft')}</button></>}
      {node.type === 'subworkflow' && <JsonField label={t('子 Workflow / revision_pin / output_bindings', 'Child workflow / revision_pin / output_bindings')} value={node.subworkflow} onChange={subworkflow => patch({ subworkflow })}/>}
      {node.type === 'tool' && <Field label={t('确切 Host Tool 名称', 'Exact host tool name')} value={node.executor.tool} onChange={tool => patch({ executor: { ...node.executor, tool } })}/>}
      {node.origin && <Details title={t('来源与审查记录', 'Origin and review record')} value={node.origin}/>}
      <button className="danger" onClick={() => { change({ ...workflow, nodes: workflow.nodes.filter((n: Json) => n.id !== node.id), edges: workflow.edges.filter((e: Json) => e.source !== node.id && e.target !== node.id) }); select('workflow', ''); }}>{t('删除节点及相关连接', 'Delete node and related connections')}</button>
    </> : selection.kind === 'edge' && edge ? <>
      <div className="muted">{edge.id}</div>
      <Select label={t('起点', 'Source')} value={edge.source} options={workflow.nodes.map((n: Json) => n.id)} onChange={source => edgePatch({ source })}/>
      <Select label={t('终点', 'Target')} value={edge.target} options={workflow.nodes.map((n: Json) => n.id)} onChange={target => edgePatch({ target })}/>
      <Field label={t('条件 / 分支标签', 'Condition / branch label')} value={edge.label} onChange={label => edgePatch({ label })}/>
      <Select label={t('前置节点结果', 'Previous node result')} value={edge.on ?? 'success'} options={[{value:'success',label:t('成功','Success')},{value:'failure',label:t('失败','Failure')},{value:'always',label:t('始终','Always')}]} onChange={on => edgePatch({ on })}/>
      {edge.origin && <Details title={t('来源', 'Origin')} value={edge.origin}/>}
      <button className="danger" onClick={() => { change({ ...workflow, edges: workflow.edges.filter((e: Json) => e.id !== edge.id) }); select('workflow',''); }}>{t('删除连接', 'Delete connection')}</button>
    </> : <>
      <Field label={t('名称', 'Name')} value={workflow.name} onChange={name => change({ ...workflow, name })}/>
      <Field label={t('说明', 'Description')} value={workflow.description} multiline onChange={description => change({ ...workflow, description })}/>
      <label className="check"><input type="checkbox" checked={workflow.enabled} onChange={e => change({ ...workflow, enabled: e.target.checked })}/>{workflow.template_kind==='role'?t('启用此 Role', 'Enable this role'):t('允许启动此 Workflow', 'Allow this workflow to start')}</label>
      <Select label={t('隔离模式', 'Isolation mode')} value={workflow.skill_policy.mode} options={[{value:'strict',label:t('严格','Strict')},{value:'cooperative',label:t('协作','Cooperative')}]} onChange={mode => change({ ...workflow, skill_policy: { ...workflow.skill_policy, mode } })}/>
      <JsonField label={t('完整 Skill 策略', 'Complete Skill policy')} value={workflow.skill_policy} onChange={skill_policy => change({ ...workflow, skill_policy })}/>
      <Select label={t('Main 最终验收节点', 'Main finalization node')} value={workflow.finalization.node_id} options={workflow.nodes.filter((n: Json) => n.executor?.kind === 'main').map((n: Json) => n.id)} onChange={node_id => change({ ...workflow, finalization: { required: true, node_id } })}/>
      <JsonField label={t('输入 Schema', 'Input schema')} value={workflow.inputs_schema} onChange={inputs_schema => change({ ...workflow, inputs_schema })}/>
      <JsonField label={t('输出 Schema', 'Output schema')} value={workflow.outputs_schema} onChange={outputs_schema => change({ ...workflow, outputs_schema })}/>
      <JsonField label={t('外部依赖要求', 'External requirements')} value={workflow.requirements} onChange={requirements => change({ ...workflow, requirements })}/>
      <LoopRegions workflow={workflow} change={change}/>
      <JsonField label={t('标签', 'Tags')} value={workflow.tags ?? []} onChange={tags => change({ ...workflow, tags })}/>
    </>}
  </aside>;
}
