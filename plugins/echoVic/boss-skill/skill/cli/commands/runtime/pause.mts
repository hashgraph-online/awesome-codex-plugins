#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  type CliContext,
  consumeCliContractOption,
  createCliContext,
  describeCommand,
  readJsonInput,
  runMain,
  writeOutput,
} from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { pausePipeline } from '../../runtime/application/pipeline.mts';
import {
  optionalInputString,
  printRuntimeHelp,
  requireInputString,
  requireOptionValue,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

interface PauseInput {
  feature: string;
  reason?: string;
  requestedBy?: string;
}

function showHelp(): void {
  printRuntimeHelp('pause', 'boss runtime pause FEATURE [options]');
}

function parseFlatInput(argv: string[]): PauseInput {
  let feature = '';
  let reason: string | undefined;
  let requestedBy: string | undefined;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--reason') {
      reason = requireOptionValue('--reason', argv[index + 1]);
      index += 1;
      continue;
    }
    if (arg === '--requested-by') {
      requestedBy = requireOptionValue('--requested-by', argv[index + 1]);
      index += 1;
      continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) throw new Error(`未知选项: ${arg}`);
    if (!feature) feature = arg;
    else throw new Error(`多余的参数: ${arg}`);
  }

  return {
    feature: requireInputString(feature, 'feature'),
    reason,
    requestedBy,
  };
}

function resolveInput(argv: string[], context: CliContext): PauseInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      reason: optionalInputString(input.reason),
      requestedBy: optionalInputString(input.requestedBy),
    };
  }
  return parseFlatInput(argv);
}

function actionFor(input: PauseInput) {
  return {
    type: 'pause_pipeline',
    feature: input.feature,
    reason: input.reason || '',
    requested_by: input.requestedBy || 'user',
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime pause' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions.pause!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions.pause, null, 2)}\n`,
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

  try {
    const execution = pausePipeline(input.feature, {
      cwd,
      reason: input.reason || '',
      requestedBy: input.requestedBy || 'user',
    });
    writeOutput(
      {
        feature: input.feature,
        status: execution.status,
        pause: execution.pause || null,
      },
      context,
      () => `Pipeline ${input.feature}: paused\n`,
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime pause',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
