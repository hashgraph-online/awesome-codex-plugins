#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  type CliContext,
  CliUserError,
  consumeCliContractOption,
  createCliContext,
  describeCommand,
  readJsonInput,
  runMain,
  writeOutput,
} from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { updateAgent } from '../../runtime/application/pipeline.mts';
import {
  AGENT_REPORT_STATUS_VALUES,
  type AgentReportStatus,
  isAgentReportStatus,
  toPipelineAgentStatus,
} from '../../runtime/domain/agent-report.mts';
import {
  optionalInputString,
  printRuntimeHelp,
  requireInputString,
  requireOptionValue,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

interface ReportAgentStatusInput {
  feature: string;
  stage: string;
  agent: string;
  status: AgentReportStatus;
  reason?: string;
}

function showHelp(): void {
  printRuntimeHelp(
    'report-agent-status',
    'boss runtime report-agent-status FEATURE STAGE AGENT STATUS [--reason <text>]',
  );
}

/**
 * 校验状态枚举。非法值抛结构化错误让调用方重试，
 * 而不是像旧的散文解析那样静默降级成 failed。
 */
function requireReportStatus(value: unknown): AgentReportStatus {
  const raw = requireInputString(value, 'status');
  if (!isAgentReportStatus(raw)) {
    throw new CliUserError({
      code: 'invalid_agent_status',
      message: `Unknown agent status: ${raw}`,
      input: { status: raw, allowed: [...AGENT_REPORT_STATUS_VALUES] },
      retryable: true,
      suggestion: `Use one of: ${AGENT_REPORT_STATUS_VALUES.join(', ')}`,
    });
  }
  return raw;
}

function parseFlatInput(argv: string[]): ReportAgentStatusInput {
  let feature = '';
  let stage = '';
  let agent = '';
  let status = '';
  let reason: string | undefined;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--reason') {
      reason = requireOptionValue('--reason', argv[index + 1]);
      index += 1;
      continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) {
      throw new Error(`未知选项: ${arg}`);
    }
    if (!feature) feature = arg;
    else if (!stage) stage = arg;
    else if (!agent) agent = arg;
    else if (!status) status = arg;
    else throw new Error(`多余的参数: ${arg}`);
  }

  return {
    feature: requireInputString(feature, 'feature'),
    stage: requireInputString(stage, 'stage'),
    agent: requireInputString(agent, 'agent'),
    status: requireReportStatus(status),
    reason,
  };
}

function resolveInput(argv: string[], context: CliContext): ReportAgentStatusInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      stage: requireInputString(input.stage, 'stage'),
      agent: requireInputString(input.agent, 'agent'),
      status: requireReportStatus(input.status),
      reason: optionalInputString(input.reason),
    };
  }
  return parseFlatInput(argv);
}

function actionFor(input: ReportAgentStatusInput) {
  return {
    type: 'report_agent_status',
    feature: input.feature,
    stage: Number(input.stage),
    agent: input.agent,
    reported_status: input.status,
    target_status: toPipelineAgentStatus(input.status),
    reason: input.reason,
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime report-agent-status' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['report-agent-status']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['report-agent-status'], null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveInput(argv, context);
  if (context.values.dryRun) {
    writeActionPlan([actionFor(input)], context, 'medium');
    return 0;
  }

  const pipelineStatus = toPipelineAgentStatus(input.status);
  try {
    updateAgent(input.feature, input.stage, input.agent, pipelineStatus, {
      // 失败时把上报原因带进事件流，便于诊断；成功路径不写 reason。
      reason: pipelineStatus === 'failed' ? input.reason || input.status : '',
      cwd,
    });
    writeOutput(
      {
        feature: input.feature,
        stage: Number(input.stage),
        agent: input.agent,
        reportedStatus: input.status,
        agentStatus: pipelineStatus,
        reason: input.reason ?? '',
      },
      context,
      () => `Agent ${input.agent} (阶段 ${input.stage}): ${input.status} -> ${pipelineStatus}\n`,
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime report-agent-status',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
