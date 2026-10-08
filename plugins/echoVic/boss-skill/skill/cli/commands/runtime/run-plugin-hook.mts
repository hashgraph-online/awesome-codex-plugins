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
import { runHook } from '../../runtime/application/plugins.mts';
import {
  optionalInputString,
  printRuntimeHelp,
  requireInputString,
  requireOptionValue,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

interface RunPluginHookInput {
  hook: string;
  feature: string;
  stage: string | null;
}

function printHelp(): void {
  printRuntimeHelp('run-plugin-hook', 'boss runtime run-plugin-hook HOOK FEATURE [options]');
}

function parseFlatInput(argv: string[]): RunPluginHookInput {
  let hook = '';
  let feature = '';
  let stage: string | null = null;
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--stage') {
      stage = requireOptionValue('--stage', argv[index + 1]);
      index += 1;
      continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) throw new Error(`未知选项: ${arg}`);
    if (!hook) hook = arg;
    else if (!feature) feature = arg;
    else throw new Error(`多余的参数: ${arg}`);
  }
  return {
    hook: requireInputString(hook, 'hook'),
    feature: requireInputString(feature, 'feature'),
    stage,
  };
}

function resolveInput(argv: string[], context: CliContext): RunPluginHookInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      hook: requireInputString(input.hook, 'hook'),
      feature: requireInputString(input.feature, 'feature'),
      stage: optionalInputString(input.stage) || null,
    };
  }
  return parseFlatInput(argv);
}

function actionFor(input: RunPluginHookInput) {
  return {
    type: 'run_plugin_hook',
    feature: input.feature,
    hook: input.hook,
    stage: input.stage,
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime run-plugin-hook' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['run-plugin-hook']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['run-plugin-hook'], null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    printHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveInput(argv, context);
  if (context.values.dryRun) {
    writeActionPlan([actionFor(input)], context, 'medium');
    return 0;
  }

  try {
    const result = runHook(input.hook, input.feature, {
      cwd,
      stage: input.stage,
    });

    writeOutput(
      {
        hook: result.hook,
        feature: result.feature,
        stage: result.stage,
        results: result.results,
      },
      context,
      () =>
        `${JSON.stringify({ hook: result.hook, feature: result.feature, stage: result.stage, results: result.results }, null, 2)}\n`,
    );
    return result.results.some((item) => item.passed === false) ? 1 : 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime run-plugin-hook',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
