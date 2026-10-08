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
import { evaluateGates } from '../../runtime/application/gates.mts';
import {
  printRuntimeHelp,
  requireInputString,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

interface EvaluateGatesInput {
  feature: string;
  gateName: string;
  dryRun: boolean;
  skipOnError: boolean;
}

function showHelp(): void {
  printRuntimeHelp('evaluate-gates', 'boss runtime evaluate-gates FEATURE GATE [options]');
}

function parseFlatInput(argv: string[], context: CliContext): EvaluateGatesInput {
  let feature = '';
  let gateName = '';
  let skipOnError = false;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--skip-on-error') {
      skipOnError = true;
      continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) throw new Error(`未知选项: ${arg}`);
    if (!feature) feature = arg;
    else if (!gateName) gateName = arg;
    else throw new Error(`多余的参数: ${arg}`);
  }

  return {
    feature: requireInputString(feature, 'feature'),
    gateName: requireInputString(gateName, 'gate'),
    dryRun: context.values.dryRun,
    skipOnError,
  };
}

function resolveInput(argv: string[], context: CliContext): EvaluateGatesInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      gateName: requireInputString(input.gate || input.gateName, 'gate'),
      dryRun: typeof input.dryRun === 'boolean' ? input.dryRun : context.values.dryRun,
      skipOnError: typeof input.skipOnError === 'boolean' ? input.skipOnError : false,
    };
  }
  return parseFlatInput(argv, context);
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime evaluate-gates' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['evaluate-gates']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['evaluate-gates'], null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveInput(argv, context);
  if (input.dryRun) {
    writeActionPlan(
      [
        {
          type: 'evaluate_gate',
          feature: input.feature,
          gate: input.gateName,
          writes_event: false,
        },
      ],
      context,
      'medium',
    );
    return 0;
  }

  try {
    const result = evaluateGates(input.feature, input.gateName, {
      cwd,
      dryRun: false,
      skipOnError: input.skipOnError,
    });

    const payload = {
      feature: input.feature,
      gate: result.gate,
      passed: result.passed,
      checks: result.checks,
      skipped: Boolean(result.skipped),
    };

    writeOutput(payload, context, () => `${JSON.stringify(payload, null, 2)}\n`);
    return result.passed ? 0 : 1;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime evaluate-gates',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
