import {
  appendAuditEvent,
  findProvider,
  findTaskType,
  isEnvironmentDisabled,
  loadConfig,
  sanitizeConfig,
} from './config.mjs';
import { buildProviderAdapter, invokeOpenAICompatible } from './providers.mjs';
import { renderTemplate } from './templates.mjs';
import { connectorRegistryFor } from '../connectors/registry.mjs';

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function normalizeApproval(value) {
  return value === true;
}

export async function getControlStatus({ configPath, defaultConfigPath, env = process.env }) {
  const config = await loadConfig({ configPath, defaultConfigPath });
  return sanitizeConfig(config, { env });
}

function resolveStage(config, taskType, stage, args, env) {
  const provider = findProvider(config, stage.provider_id);
  assert(provider, `task type ${taskType.id} stage ${stage.id} provider is missing: ${stage.provider_id}`);
  assert(provider.enabled, `provider is disabled: ${provider.id}`);
  const approvalRequired = Boolean(
    stage.requires_user_approval || provider.requires_user_approval,
  );
  if (approvalRequired) {
    assert(normalizeApproval(args.user_approved),
      `task type ${taskType.id} stage ${stage.id} requires explicit current-task user approval`);
  }
  assert(provider.capabilities.read, `provider ${provider.id} cannot read task context`);
  if (stage.access === 'bounded_write') {
    assert(provider.capabilities.write, `provider ${provider.id} is not configured for write-capable work`);
  }
  const compiledPrompt = renderTemplate(stage.template, {
    task: String(args.task || '').trim(),
    context: args.context,
    constraints: args.constraints,
    verification: args.verification,
    task_type_id: taskType.id,
    stage_id: stage.id,
    provider_name: provider.name,
  }, config.global.max_prompt_chars);
  const adapter = buildProviderAdapter(provider, stage, {
    env,
    allowDirectApi: config.global.allow_direct_api,
  });
  return {
    stage: { id: stage.id, role: stage.role, access: stage.access },
    provider: { id: provider.id, name: provider.name, kind: provider.kind },
    approval_required: approvalRequired,
    adapter,
    ...(provider.kind === 'builtin_connector'
      ? { prompt_delivery: 'internal', next_operation: 'codex_agents_workflow_connector_start' }
      : { compiled_prompt: compiledPrompt }),
    _stage: stage,
    _provider: provider,
    _compiledPrompt: compiledPrompt,
  };
}

export async function resolveSelection(args, {
  configPath,
  defaultConfigPath,
  env = process.env,
  audit = true,
} = {}) {
  const config = await loadConfig({ configPath, defaultConfigPath });
  assert(!isEnvironmentDisabled(env), 'Codex Agents Workflow is disabled by CODEX_WORKFLOW_DISABLED');
  assert(config.global.enabled, 'Codex Agents Workflow is disabled in the user configuration');

  const taskTypeId = String(args?.task_type_id || '').trim();
  const task = String(args?.task || '').trim();
  assert(taskTypeId, 'task_type_id is required');
  assert(task, 'task is required');

  const taskType = findTaskType(config, taskTypeId);
  assert(taskType, `unknown task type: ${taskTypeId}`);
  assert(taskType.enabled, `task type is disabled: ${taskTypeId}`);
  const resolvedStages = taskType.stages.map((stage) => resolveStage(config, taskType, stage, args, env));
  const result = {
    task_type: {
      id: taskType.id,
      name: taskType.name,
      route: taskType.route,
      tags: taskType.tags,
    },
    stages: resolvedStages.map(({ _stage, _provider, _compiledPrompt, ...stageResult }) => stageResult),
  };

  if (audit) {
    await appendAuditEvent(configPath, {
      event: 'resolve',
      task_type_id: taskType.id,
      outcome: 'ok',
    });
  }
  return { result, config, taskType, resolvedStages };
}

export async function invokeSelection(args, {
  configPath,
  defaultConfigPath,
  env = process.env,
  fetchImpl = globalThis.fetch,
} = {}) {
  const resolved = await resolveSelection(args, {
    configPath,
    defaultConfigPath,
    env,
    audit: false,
  });
  const stageId = String(args?.stage_id || '').trim();
  assert(stageId, 'stage_id is required');
  const selected = resolved.resolvedStages.find((item) => item.stage.id === stageId);
  assert(selected, `unknown stage for task type ${resolved.taskType.id}: ${stageId}`);
  const { config, taskType, result } = resolved;
  const provider = selected._provider;
  const stage = selected._stage;
  assert(provider.kind === 'openai_compatible',
    'codex_agents_workflow_invoke supports only openai_compatible providers; native and MCP providers must be executed by Codex through their returned adapter contract');
  assert(config.global.allow_direct_api,
    'direct API invocation is disabled in the user configuration');
  assert(stage.access === 'read_only',
    'direct API providers are advisory-only and require a read-only stage');

  try {
    const invocation = await invokeOpenAICompatible(provider, selected._compiledPrompt, {
      env,
      fetchImpl,
    });
    await appendAuditEvent(configPath, {
      event: 'invoke',
      task_type_id: taskType.id,
      stage_id: stage.id,
      provider_id: provider.id,
      outcome: 'ok',
    }, { effectCommitted: true });
    return {
      task_type: result.task_type,
      stage: selected.stage,
      provider: selected.provider,
      advisory_only: true,
      response: invocation,
    };
  } catch (error) {
    if (error.code === 'AUDIT_WRITE_FAILED') throw error;
    await appendAuditEvent(configPath, {
      event: 'invoke',
      task_type_id: taskType.id,
      stage_id: stage.id,
      provider_id: provider.id,
      outcome: 'error',
      detail: error.message,
    });
    throw error;
  }
}


export async function probeConnector(args, {
  configPath,
  defaultConfigPath,
  env = process.env,
  registry = connectorRegistryFor({ configPath, env }),
} = {}) {
  const config = await loadConfig({ configPath, defaultConfigPath });
  assert(!isEnvironmentDisabled(env), 'Codex Agents Workflow is disabled by CODEX_WORKFLOW_DISABLED');
  assert(config.global.enabled, 'Codex Agents Workflow is disabled in the user configuration');
  const providerId = String(args?.provider_id || '').trim();
  assert(providerId, 'provider_id is required');
  const provider = findProvider(config, providerId);
  assert(provider, `unknown provider: ${providerId}`);
  assert(provider.enabled, `provider is disabled: ${providerId}`);
  assert(provider.kind === 'builtin_connector', `provider is not a built-in connector: ${providerId}`);
  return registry.probe(provider, { workspace: args?.workspace });
}

export async function startConnectorSelection(args, {
  configPath,
  defaultConfigPath,
  env = process.env,
  registry = connectorRegistryFor({ configPath, env }),
} = {}) {
  const resolved = await resolveSelection(args, {
    configPath, defaultConfigPath, env, audit: false,
  });
  const stageId = String(args?.stage_id || '').trim();
  assert(stageId, 'stage_id is required');
  const selected = resolved.resolvedStages.find((item) => item.stage.id === stageId);
  assert(selected, `unknown stage for task type ${resolved.taskType.id}: ${stageId}`);
  const { taskType } = resolved;
  const stage = selected._stage;
  const provider = selected._provider;
  assert(provider.kind === 'builtin_connector',
    `stage provider is not a built-in connector: ${provider.id}`);
  const connectorStage = {
    id: stage.id,
    read_only: stage.access === 'read_only',
    requires_user_approval: stage.requires_user_approval,
  };
  const task = await registry.start({
    provider,
    stage: connectorStage,
    prompt: selected._compiledPrompt,
    workspace: args.workspace,
    taskTypeId: taskType.id,
    stageId: stage.id,
    allowedPaths: args.allowed_paths,
    userApproved: args.user_approved === true,
  });
  await appendAuditEvent(configPath, {
    event: 'connector-start', task_type_id: taskType.id, stage_id: stage.id, provider_id: provider.id,
    task_id: task.task_id, outcome: 'ok',
  }, { effectCommitted: true });
  return task;
}

export async function getConnectorTask(args, {
  configPath,
  env = process.env,
  registry = connectorRegistryFor({ configPath, env }),
} = {}) {
  return registry.status(String(args?.task_id || ''), args?.wait_ms);
}

export async function controlConnectorTask(args, {
  configPath,
  env = process.env,
  registry = connectorRegistryFor({ configPath, env }),
} = {}) {
  const taskId = String(args?.task_id || '');
  const result = await registry.control(taskId, args || {});
  await appendAuditEvent(configPath, {
    event: 'connector-control', task_id: taskId,
    action: String(args?.action || ''), outcome: 'ok',
  }, { effectCommitted: true });
  return result;
}
