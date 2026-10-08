import { useEffect, useState } from 'react';
import { api, Details, Field, uid, useLocale, type Json } from './shared';
import { controllers, rememberRun } from './run-panel';
import { Canvas } from './canvas';
import { adoptAuthoringRun, assessAuthoringRecovery, continueControlledAuthoringRun, inspectControlledAuthoringRun, mountedAuthoringSession, shouldPollAuthoring } from './skill-generation-recovery.mjs';

const sessions = new Map<string,Json>();
const suspendedPhases = new Map<string,Json>();
const reviewLabels:Record<string,[string,string]>={parallelism:['并行关系','Parallelism'],agent_ownership:['Main／Codex task 分工','Main/Codex task ownership'],human_intervention:['人类介入','Human intervention'],model_selection:['模型选择','Model selection'],phase_order:['阶段顺序','Phase order'],hard_rules:['原 Skill 硬性规则','Original Skill hard rules'],data_handoffs:['数据交接','Data handoffs'],failure_semantics:['失败语义','Failure semantics'],conversation_inputs:['输入与反馈','Conversation inputs and feedback'],human_confirmation:['确认时机','Confirmation timing'],conditional_dependencies:['条件依赖','Conditional dependencies'],portable_artifact:['资源与环境分层','Portable artifact layers'],source_support:['来源依据覆盖','Source support coverage'],review_scope:['审核范围','Review scope']};
function ReviewChecklist({result}:{result:Json}) {
  const t = useLocale();
  if(!Array.isArray(result?.checks))return <Details title={t('历史审核结果','Historical review result')} value={result}/>;
  const statusLabels:Record<string,[string,string]>={pass:['通过','Pass'],fail:['未通过','Fail'],not_applicable:['不适用','Not applicable']};
  return <><p>{t('审核结论：','Review conclusion: ')}{result.approved?t('通过','Passed'):t('未通过','Not passed')}{t('（程序按逐项结果汇总）',' (summarized from each check)')}</p><table><thead><tr><th>{t('检查项','Check')}</th><th>{t('结果','Result')}</th><th>{t('证据与依据','Evidence and basis')}</th></tr></thead><tbody>{result.checks.map((check:Json)=><tr key={check.id}><td>{reviewLabels[check.id] ? t(...reviewLabels[check.id]) : check.id}</td><td>{statusLabels[check.status as string] ? t(...statusLabels[check.status as string]) : check.status}</td><td>{check.evidence}<Details title={t('节点、连线和来源','Nodes, edges, and sources')} value={{node_ids:check.node_ids,edge_ids:check.edge_ids,source_spans:check.source_spans}}/></td></tr>)}</tbody></table></>;
}

export function SkillGeneration({pack,routing,workspace,providers,saved,openRun}: {pack:Json,routing:Json|null,workspace:string,providers:Json[],saved:(pack:Json)=>Promise<void>,openRun:(run:Json)=>void}) {
  const t = useLocale();
  const sessionKey = pack.workflow.id+'/'+pack.revision_hash;
  const [run,setRun] = useState<Json|null>(()=>mountedAuthoringSession(sessions,controllers,sessionKey));
  const [progress,setProgress] = useState<Json|null>(()=>suspendedPhases.get(sessionKey) ?? null);
  const [pollEnabled,setPollEnabled] = useState(false);
  const [error,setError] = useState<Json|null>(null);
  const [login,setLogin] = useState<Json|null>(null);
  const [busy,setBusy] = useState(false);
  const [stopping,setStopping] = useState(false);
  const [repairGuidance,setRepairGuidance] = useState('');
  const [previewNodeId,setPreviewNodeId] = useState('');
  const [recoveryId,setRecoveryId] = useState('');
  const [recovery,setRecovery] = useState<Json|null>(null);
  const [recoveryControl,setRecoveryControl] = useState('');
  const previewNode=progress?.workflow?.nodes?.find((node:Json)=>node.id===previewNodeId);
  const control = run ? {run_id:run.run_id,control_token:run.control_token} : null;
  const fail = (cause:any)=>setError({message:cause.message,...cause.detail});
  const publishProgress=(next:Json|null)=>{if(next?.phase==='user_input_required')suspendedPhases.set(sessionKey,next);else suspendedPhases.delete(sessionKey);setProgress(next);};
  useEffect(()=>{
    if (!shouldPollAuthoring({run,pollEnabled,stopping,error,phase:progress?.phase})) return;
    let active=true; let timer:ReturnType<typeof setTimeout>;
    const poll=async()=>{
      try { const next=await api('advance_authoring',{run_id:run!.run_id,control_token:run!.control_token}); if(active){publishProgress(next); if(!['review_required','ready_to_apply','user_input_required','attention','approval','authentication_required'].includes(next.phase)) timer=setTimeout(poll,2000);} }
      catch(cause){if(active)fail(cause);}
    };
    timer=setTimeout(poll,0);
    return ()=>{active=false;clearTimeout(timer);};
  },[run,pollEnabled,error,stopping,progress?.phase]);
  async function start(){
    setBusy(true);setError(null);publishProgress(null);setStopping(false);
    try {const result=await api('start_authoring',{workflow_id:pack.workflow.id,revision_hash:pack.revision_hash,run_id:uid('authoring'),...(routing?{routing_rules:routing}:{}),...(workspace?{workspace}:{})});rememberRun(result);sessions.set(sessionKey,result);setPollEnabled(true);setRun(result);}
    catch(cause){fail(cause);}finally{setBusy(false);}
  }
  async function accept(){setBusy(true);try{const result=await api('accept_authoring',{...control,accepted:true});sessions.delete(sessionKey);suspendedPhases.delete(sessionKey);await saved(result);}catch(cause){fail(cause);}finally{setBusy(false);}}
  async function checkExisting(){
    setBusy(true);setError(null);
    try{
      const {inspected:checked,controlToken}=await inspectControlledAuthoringRun(api,pack,run!.run_id,controllers);
      if(!controlToken)throw new Error('The saved controller token is unavailable; inspect and take control of the exact Run');
      const authority={run_id:checked.run_id,control_token:controlToken};
      sessions.set(sessionKey,authority);setRun(authority);
      if(checked.continuation==='guidance')publishProgress({phase:'user_input_required',status:'awaiting_user_input',error:checked.state.generation_repair.feedback,feedback:checked.state.generation_repair.feedback});
      else if(checked.continuation==='accepted')publishProgress({phase:'ready_to_apply',status:'succeeded',source:{workflow_id:pack.workflow.id,expected_revision:pack.revision_hash}});
      else if(checked.continuation==='advance'&&checked.state.status==='running'){publishProgress(null);setPollEnabled(true);}
      else publishProgress({phase:'attention',status:checked.state.status,error:{code:'AUTHORING_RECOVERY_RECONCILIATION',message:'Use the detailed Run to resume or reconcile this saved authoring session.'}});
    }catch(cause:any){
      if(cause?.code==='AUTHORING_RECOVERY_CONTROL_STALE'){
        sessions.delete(sessionKey);setRun(null);setPollEnabled(false);
        setRecoveryId(cause.inspected.run_id);setRecovery(cause.inspected);setRecoveryControl('');
      }
      fail(cause);
    }finally{setBusy(false);}
  }
  async function inspectRecovery(){
    setBusy(true);setError(null);setRecovery(null);setRecoveryControl('');
    try{const {inspected,controlToken}=await inspectControlledAuthoringRun(api,pack,recoveryId,controllers);setRecovery(inspected);setRecoveryControl(controlToken);}catch(cause:any){if(cause?.code==='AUTHORING_RECOVERY_CONTROL_STALE')setRecovery(cause.inspected);fail(cause);}finally{setBusy(false);}
  }
  async function adoptRecovery(){
    setBusy(true);setError(null);
    try{
      const {inspected,adopted}=await adoptAuthoringRun(api,pack,recovery!.run_id);
      rememberRun(adopted);setRecovery(assessAuthoringRecovery(pack,{provenance:inspected.provenance},adopted));setRecoveryControl(adopted.control_token);
    }catch(cause){fail(cause);}finally{setBusy(false);}
  }
  async function resumeRecovery(){
    setBusy(true);setError(null);
    try{
      if(!recoveryControl||!recovery)throw new Error('Take control of the exact authoring Run first');
      const {checked,controlToken}=await continueControlledAuthoringRun(api,pack,recovery.run_id,controllers);
      const authority={run_id:checked.run_id,control_token:controlToken};
      sessions.set(sessionKey,authority);setRun(authority);setRecovery(checked);setRecoveryControl(controlToken);
      if(checked.continuation==='guidance'){setPollEnabled(false);publishProgress({phase:'user_input_required',status:'awaiting_user_input',error:checked.state.generation_repair.feedback,feedback:checked.state.generation_repair.feedback});}
      else if(checked.continuation==='accepted'){setPollEnabled(false);publishProgress({phase:'ready_to_apply',status:'succeeded',source:{workflow_id:pack.workflow.id,expected_revision:pack.revision_hash}});}
      else{publishProgress(null);setPollEnabled(true);}
    }catch(cause){fail(cause);}finally{setBusy(false);}
  }
  const labels:Json={repairing:progress?.review_only?t('正在补正审核清单（保留生成结果）…','Repairing the review checklist (keeping the generated result)…'):t('正在根据检查意见定向修正…','Applying a targeted patch from the review findings…'),generating:t('正在生成工作流…','Generating workflow…'),reviewing:t('正在检查生成结果…','Reviewing the generated result…'),review_required:t('生成与检查已完成，请查看结果','Generation and review are complete; inspect the result'),ready_to_apply:t('检查已确认，可以保存草稿','Review confirmed; the draft can be saved'),user_input_required:t('自动语义修订已用完，可补充意见继续定向修改','Automatic semantic repairs are exhausted; add guidance to continue'),authentication_required:t('所选独立登录模式需要完成登录','The selected managed login mode requires authentication'),approval:t('需要你允许本次模型调用','Your approval is needed for this model call'),attention:t('生成已停止，需要处理','Generation stopped; attention is required')};
  return <section className="generation-panel"><h2>{t('从 Skill 生成 Workflow（自动选择）','Generate a workflow from a Skill (automatic routing)')}</h2><p>{t('自动安排步骤，在 Main 与 Codex task thread 之间分配执行者并检查结果。工作目录由系统准备，通常无需设置。','Automatically arranges steps, assigns executors between Main and Codex task threads, and reviews the result. The system prepares the workspace, so setup is usually unnecessary.')}</p>
    {!run && <><button className="primary" disabled={busy} onClick={start}>{busy?t('正在准备…','Preparing…'):t('自动生成 Workflow','Generate workflow automatically')}</button><details><summary>{t('恢复已有生成 Run（高级）','Recover an existing authoring Run (advanced)')}</summary><p>{t('输入已保存方案的 Run ID，先核对其来源 Draft 与版本；已有控制权会直接复用。首次接管会暂停 Run，之后需明确继续。不会重新启动规划模型。','Enter the Run ID of a saved plan. The source Draft and revision are checked first; existing control is reused. First-time adoption pauses the Run, then you explicitly continue. This does not restart the planner.')}</p><Field label={t('已有 authoring Run ID','Existing authoring Run ID')} value={recoveryId} onChange={value=>{setRecoveryId(value);setRecovery(null);setRecoveryControl('');}}/><button disabled={busy||!recoveryId.trim()} onClick={inspectRecovery}>{t('检查已保存方案','Inspect saved plan')}</button>{recovery && <div><p>{t('已核对来源版本：','Verified source revision: ')}<code>{recovery.provenance.source_revision}</code> · {t('Run 状态：','Run status: ')}{recovery.state.status}</p><Details title={t('已保存的方案和恢复状态','Saved plan and recovery status')} value={{run_id:recovery.run_id,continuation:recovery.continuation,feedback:recovery.state.generation_repair?.feedback,control_recovery:recovery.state.control_recovery}}/>{!recoveryControl && <button disabled={busy} onClick={adoptRecovery}>{t('接管并暂停此 Run','Take control and pause this Run')}</button>}{recoveryControl && <button disabled={busy||!!recovery.state.control_recovery?.errors?.length||recovery.continuation==='reconcile'} onClick={resumeRecovery}>{recovery.state.status==='succeeded'?t('打开已验收结果','Open accepted result'):recovery.state.status==='running'?t('附着并继续此 Run','Attach and continue this Run'):t('明确继续此 Run','Resume this Run')}</button>}{recoveryControl&&(recovery.continuation==='reconcile'||recovery.state.control_recovery?.errors?.length>0)&&<p role="status">{t('此 Run 需要在详细页面完成原节点的协调/清理后才能继续。','Complete exact node reconciliation or cleanup in the detailed Run before continuing.')}</p>}<button onClick={()=>openRun({run_id:recovery.run_id,...(recoveryControl?{control_token:recoveryControl}:{})})}>{t('查看详细 Run 与恢复证据','View detailed Run and recovery evidence')}</button></div>}</details></>}
    {run && <p role="status">{stopping?t('正在停止并确认会话退出…','Stopping and confirming session exit…'):labels[progress?.phase] ?? (pollEnabled?t('正在准备生成…','Preparing generation…'):t('已有会话待只读检查','Existing session awaits a read-only check'))}</p>}
    {progress?.progress && <p>{t('第 ','Round ')}{progress.progress.round} / {progress.progress.max_rounds} · {progress.progress.model} / {progress.progress.effort} · {t('本阶段已用 ','Stage time: ')}{Math.floor(progress.progress.stage_elapsed_ms/1000)} {t('秒','s')} · {t('近期资源读取 ','Recent resource reads: ')}{progress.progress.resource_reads} {t('次（最近 64 条事件）',' (last 64 events)')}{progress.progress.activity==='compacting'?t(' · 正在压缩上下文',' · Compacting context'):''}{progress.progress.last_resource?t(' · 最近读取 ',' · Last read ')+progress.progress.last_resource:''}</p>}
    {progress?.live?.output_preview?.text && <Details title={t('模型当前输出（尚未验收）','Current model output (not yet accepted)')} value={progress.live.output_preview.text}/>}
    {run && <button disabled={busy || stopping || ['cancelled','succeeded'].includes(progress?.status)} onClick={async()=>{setBusy(true);setStopping(true);try{await api('cancel',control!);publishProgress({phase:'attention',status:'cancelled'});}catch(cause){fail(cause);}finally{setBusy(false);setStopping(false);}}}>{t('停止生成','Stop generation')}</button>}
    {progress?.status==='cancelled' && <button onClick={()=>{sessions.delete(sessionKey);setRun(null);setPollEnabled(false);publishProgress(null);setError(null);}}>{t('返回生成入口（保留历史记录）','Return to generation (keep history)')}</button>}
    {error && <div role="alert"><p>{t('生成未完成：','Generation did not finish: ')}{error.message}</p><Details title={t('错误详情','Error details')} value={error}/></div>}
    {progress?.phase==='review_required' && <><h3>{t('待确认的生成图','Generated graph awaiting acceptance')}</h3><p>{t('这是转换产物的真实节点和连线，不是四节点导入骨架。点击节点查看任务指令、执行模型和权限；确认后才会替换库中的草稿。','These are the actual converted nodes and edges, not the four-node import scaffold. Click a node to inspect its task, executor, and access. The library draft changes only after acceptance.')}</p><div className="generation-preview" style={{display:'flex',height:480}}><Canvas workflow={progress.workflow} providers={providers} onChange={()=>{}} onSelect={(kind,id)=>setPreviewNodeId(kind==='node'?id:'')} readOnly/></div>{previewNode && <Details title={t('选中节点的任务和绑定','Selected node task and binding')} value={{id:previewNode.id,name:previewNode.name,prompt_template:previewNode.prompt_template,executor:previewNode.executor,access:previewNode.access,input_bindings:previewNode.input_bindings,resources:previewNode.resources,outputs_schema:previewNode.outputs_schema}}/>}<p>{t('结构检查：','Structure check: ')}{progress.validation?.valid?t('通过','Passed'):t('未通过','Failed')}{t('；','; ')}{t('最终确认：','Finalization: ')}{progress.workflow?.finalization?.required?t('必须完成','Required'):t('未要求','Not required')}{t('。','.')}</p><Details title={t('编排决策：并行、Main／Codex task、人类介入','Orchestration decisions: parallelism, Main/Codex task, and human intervention')} value={progress.proposal?.planning_analysis}/><p>{t('审核通过表示转换语义通过；下列启动限制不会被自动清除。','Passing review approves the conversion semantics; the launch constraints below are not removed automatically.')}</p><Details title={t('启动条件与待确认事项','Launch conditions and items needing confirmation')} value={progress.validation?.blockers}/><h3>{t('逐项审核清单','Review checklist')}</h3><ReviewChecklist result={progress.review?.structured_output}/><Details title={t('查看完整草稿和检查证据','View the full draft and review evidence')} value={{workflow:progress.workflow,validation:progress.validation,proposal:progress.proposal,review:progress.review}}/></>}
    {['review_required','ready_to_apply'].includes(progress?.phase) && <button className="primary" disabled={busy} onClick={accept}>{t('我确认所示步骤和连线，保存为可编辑草稿','I confirm the shown steps and edges; save as an editable draft')}</button>}
    {progress?.phase==='approval' && progress.approvals.map((approval:Json)=><div key={approval.id}><Details title={t('本次调用的权限要求','Permission requirements for this call')} value={approval}/><button disabled={busy} onClick={async()=>{setBusy(true);try{await api('approve',{...control,approval_id:approval.id,decision:true});publishProgress(null);setPollEnabled(true);}catch(cause){fail(cause);}finally{setBusy(false);}}}>{t('允许此次调用并继续','Allow this call and continue')}</button></div>)}
    {progress?.phase==='authentication_required' && <div><p>{t('此操作仅用于你主动选择的独立登录模式。完成登录后继续。','This only applies to the managed login mode you selected. Finish signing in, then continue.')}</p>{progress.live?.status==='auth_required' && <button disabled={busy} onClick={async()=>{setBusy(true);try{const value=await api('login_authoring',control!);setLogin(value);publishProgress({...progress,live:value});}catch(cause){fail(cause);}finally{setBusy(false);}}}>{t('获取官方登录链接','Get the official sign-in link')}</button>}{login?.auth_url && <a href={login.auth_url} target="_blank" rel="noreferrer">{t('打开官方登录页面','Open the official sign-in page')}</a>}<button onClick={()=>{setError(null);publishProgress(null);setPollEnabled(true);}}>{t('登录完成，继续','Sign-in complete; continue')}</button></div>}
    {progress?.phase==='repairing' && <p>{t('第 ','Round ')}{progress.round}{t(' 轮：已将具体问题反馈给生成模型。', ': Specific issues were sent back to the generation model.')}</p>}
    {progress?.phase==='user_input_required' && <div><Details title={t('尚未解决的语义问题','Unresolved semantic findings')} value={{error:progress.error,feedback:progress.feedback}}/><p>{t('当前语义方案已完整保留。下面的意见只会触发一次定向 patch，不会重新生成整份工作流。','The current semantic plan is retained exactly. The guidance below triggers one targeted patch, not a full regeneration.')}</p><Field label={t('继续修改的具体意见（最多 4000 字符）','Focused guidance for the next patch (maximum 4000 characters)')} value={repairGuidance} multiline onChange={setRepairGuidance}/><button className="primary" disabled={busy || !repairGuidance.trim() || repairGuidance.length>4000} onClick={async()=>{setBusy(true);try{const next=await api('continue_authoring',{...control,guidance:repairGuidance.trim()});setRepairGuidance('');publishProgress(next);setPollEnabled(true);}catch(cause){fail(cause);}finally{setBusy(false);}}}>{t('保留当前方案并继续定向修改','Keep the current plan and apply another targeted patch')}</button></div>}
    {progress?.phase==='attention' && <Details title={t('停止原因','Reason for stopping')} value={progress}/>}
    {run && <details><summary>{t('运行详情与恢复（高级）','Run details and recovery (advanced)')}</summary><button onClick={()=>openRun(run)}>{t('查看详细运行','View detailed run')}</button>{(!pollEnabled||error)&&<button disabled={busy} onClick={checkExisting}>{t('只读检查已保存状态','Inspect saved status without advancing')}</button>}</details>}
  </section>;
}
