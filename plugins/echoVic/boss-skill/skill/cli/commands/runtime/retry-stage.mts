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
import { retryStage } from '../../runtime/application/pipeline.mts';
import {
  printRuntimeHelp,
  requireInputString,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

interface RetryStageInput {
  feature: string;
  stage: string;
}

function showHelp(): void {
  printRuntimeHelp('retry-stage', 'boss runtime retry-stage FEATURE STAGE [options]');
}

function parseFlatInput(argv: string[]): RetryStageInput {
  let feature = '';
  let stage = '';
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) {
      throw new Error(`未知选项: ${arg}`);
    }
    if (!feature) {
      feature = arg;
    } else if (!stage) {
      stage = arg;
    } else {
      throw new Error(`多余的参数: ${arg}`);
    }
  }
  return {
    feature: requireInputString(feature, 'feature'),
    stage: requireInputString(stage, 'stage'),
  };
}

function resolveInput(argv: string[], context: CliContext): RetryStageInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      stage: requireInputString(input.stage, 'stage'),
    };
  }
  return parseFlatInput(argv);
}

function actionFor(input: RetryStageInput) {
  return {
    type: 'retry_stage',
    feature: input.feature,
    stage: Number(input.stage),
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime retry-stage' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['retry-stage']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['retry-stage'], null, 2)}\n`,
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

  assertConfirmed(context, 'retry_stage');

  try {
    const state = retryStage(input.feature, Number(input.stage), { cwd });
    const stageState = state.stages?.[input.stage];
    writeOutput(
      {
        feature: input.feature,
        stage: Number(input.stage),
        status: stageState?.status,
        retryCount: stageState?.retryCount,
      },
      context,
      () =>
        `${JSON.stringify({ feature: input.feature, stage: Number(input.stage), status: stageState?.status, retryCount: stageState?.retryCount }, null, 2)}\n`,
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime retry-stage',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
