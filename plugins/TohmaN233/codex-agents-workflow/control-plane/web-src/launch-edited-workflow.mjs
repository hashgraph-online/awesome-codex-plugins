// Worker launches pin the selected revision; conversation launches request the current published Workflow.
import { t } from '../web/i18n.js';
export async function publishEditedWorkflow({pack,dirty,save,request,onSaved}) {
  let current=dirty || !pack ? await save() : pack;
  if(current.workflow.status!=='ready')current=await request('publish',{
    workflow_id:current.workflow.id,expected_revision:current.revision_hash,
  });
  await onSaved(current);
  return current;
}
export async function launchEditedWorkflow({pack,dirty,request,options,conversationLaunch}) {
  if(dirty || !pack || pack.workflow.status!=='ready')throw new Error(t('请先发布工作流，再运行任务。', 'Publish the workflow before running a task.'));
  if(!pack.workflow.enabled)throw new Error(t('此流程已禁用，请先启用并发布。', 'This workflow is disabled. Enable and publish it first.'));
  if (pack.workflow.nodes.some(node => node.executor?.kind === 'main' && node.executor.mode === 'orchestration')) {
    if (!conversationLaunch) throw new Error(t('请在当前 Codex 聊天中启动：该流程需要主 Agent 已有的工作上下文。', 'Start from the current Codex conversation: this Workflow needs Main’s existing working context.'));
    await conversationLaunch({workflow_id:pack.workflow.id,task:options.inputs?.task ?? '',workspace:options.workspace});
    return {conversation_requested:true};
  }
  return request('run_main',{...options,workflow_id:pack.workflow.id,revision_hash:pack.revision_hash});
}
