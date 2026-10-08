#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  assertConfirmed,
  type CliContext,
  consumeCliContractOption,
  createCliContext,
  describeCommand,
  readJsonInput,
  runMain,
  writeOutput,
} from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { retryAgent } from '../../runtime/application/pipeline.mts';
import {
  printRuntimeHelp,
  requireInputString,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

interface RetryAgentInput {
  feature: string;
  stage: string;
  agent: string;
}

function showHelp(): void {
  printRuntimeHelp('retry-agent', 'boss runtime retry-agent FEATURE STAGE AGENT [options]');
}

function parseFlatInput(argv: string[]): RetryAgentInput {
  let feature = '';
  let stage = '';
  let agent = '';
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) throw new Error(`未知选项: ${arg}`);
    if (!feature) feature = arg;
    else if (!stage) stage = arg;
    else if (!agent) agent = arg;
    else throw new Error(`多余的参数: ${arg}`);
  }
  return {
    feature: requireInputString(feature, 'feature'),
    stage: requireInputString(stage, 'stage'),
    agent: requireInputString(agent, 'agent'),
  };
}

function resolveInput(argv: string[], context: CliContext): RetryAgentInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      stage: requireInputString(input.stage, 'stage'),
      agent: requireInputString(input.agent, 'agent'),
    };
  }
  return parseFlatInput(argv);
}

function actionFor(input: RetryAgentInput) {
  return {
    type: 'retry_agent',
    feature: input.feature,
    stage: Number(input.stage),
    agent: input.agent,
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime retry-agent' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['retry-agent']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['retry-agent'], null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveInput(argv, context);
  if (context.values.dryRun) {
    writeActionPlan([actionFor(input)], context, 'high');
    return 0;
  }

  assertConfirmed(context, 'retry_agent');

  try {
    const state = retryAgent(input.feature, Number(input.stage), input.agent, { cwd });
    const agentState = state.stages?.[input.stage]?.agents?.[input.agent];
    writeOutput(
      {
        feature: input.feature,
        stage: Number(input.stage),
        agent: input.agent,
        status: agentState?.status,
        retryCount: agentState?.retryCount,
      },
      context,
      () =>
        `${JSON.stringify({ feature: input.feature, stage: Number(input.stage), agent: input.agent, status: agentState?.status, retryCount: agentState?.retryCount }, null, 2)}\n`,
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime retry-agent',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
