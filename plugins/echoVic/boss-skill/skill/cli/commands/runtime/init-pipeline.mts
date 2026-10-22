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
import { initPipeline } from '../../runtime/application/pipeline.mts';
import { printRuntimeHelp, requireInputString, writeActionPlan } from './agent-command-utils.mts';

interface InitPipelineInput {
  feature: string;
}

function showHelp(): void {
  printRuntimeHelp('init-pipeline', 'boss runtime init-pipeline FEATURE [options]');
}

function parseFlatInput(argv: string[]): InitPipelineInput {
  let feature = '';
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) throw new Error(`未知选项: ${arg}`);
    if (!feature) feature = arg;
    else throw new Error(`多余的参数: ${arg}`);
  }
  return { feature: requireInputString(feature, 'feature') };
}

function resolveInput(argv: string[], context: CliContext): InitPipelineInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    return {
      feature: requireInputString((jsonInput as Record<string, unknown>).feature, 'feature'),
    };
  }
  return parseFlatInput(argv);
}

function actionFor(input: InitPipelineInput) {
  return {
    type: 'init_pipeline',
    feature: input.feature,
    path: `.boss/${input.feature}/.meta/execution.json`,
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime init-pipeline' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['init-pipeline']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['init-pipeline'], null, 2)}\n`,
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

  const execution = initPipeline(input.feature, { cwd });
  writeOutput(
    {
      feature: execution.feature,
      status: execution.status,
      executionPath: `.boss/${execution.feature}/.meta/execution.json`,
    },
    context,
    () =>
      `${JSON.stringify({ feature: execution.feature, status: execution.status, executionPath: `.boss/${execution.feature}/.meta/execution.json` }, null, 2)}\n`,
  );
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime init-pipeline',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
