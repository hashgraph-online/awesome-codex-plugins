import {
  type CliContext,
  CliUserError,
  createCliContext,
  describeCommand,
  writeOutput,
} from '../../cli/contract.mts';
import { commandDescriptions } from '../../cli/registry.mts';
import { evaluateFinalGate, type FinalGateResult } from '../../runtime/application/final-gate.mts';
import { evaluateGates } from '../../runtime/application/gates.mts';

interface GateInput {
  feature: string;
  gateName: string;
}

function parseGateInput(argv: string[]): GateInput {
  let feature = '';
  let gateName = 'gate1';

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--json' || arg === '--describe') {
      continue;
    }
    if (arg === '--gate') {
      const value = argv[index + 1];
      if (!value || value.startsWith('-')) {
        throw new Error('--gate requires a value');
      }
      gateName = value;
      index += 1;
      continue;
    }
    if (arg.startsWith('--gate=')) {
      gateName = arg.slice('--gate='.length);
      continue;
    }
    if (arg.startsWith('-')) throw new Error(`未知选项: ${arg}`);
    if (!feature) {
      feature = arg;
      continue;
    }
    throw new Error(`多余的参数: ${arg}`);
  }

  if (!feature) {
    throw new CliUserError({
      code: 'missing_argument',
      message: 'Usage: boss gate FEATURE [--gate gateName] [options]',
      input: { argument: 'feature' },
      retryable: false,
      suggestion: 'Run boss gate --describe to verify command parameters',
    });
  }
  return { feature, gateName };
}

function parseFinalFeature(argv: string[]): string {
  let feature = '';
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--json' || arg === '--describe') {
      continue;
    }
    if (arg.startsWith('-')) throw new Error(`未知选项: ${arg}`);
    if (!feature) {
      feature = arg;
      continue;
    }
    throw new Error(`多余的参数: ${arg}`);
  }
  if (!feature) {
    throw new CliUserError({
      code: 'missing_argument',
      message: 'Usage: boss gate final FEATURE [options]',
      input: { argument: 'feature' },
      retryable: false,
      suggestion: 'Run boss gate final --describe to verify command parameters',
    });
  }
  return feature;
}

function renderGateText(payload: { feature: string; gate: string; passed: boolean }): string {
  return [
    payload.passed ? 'Gate passed' : 'Gate failed',
    `Feature: ${payload.feature}`,
    `Gate: ${payload.gate}`,
    '',
  ].join('\n');
}

function renderFinalText(result: FinalGateResult): string {
  return [
    result.passed ? 'Final gate passed' : 'Final gate failed',
    `Feature: ${result.feature}`,
    ...result.checks.map((check) => `${check.passed ? 'PASS' : 'FAIL'} ${check.name}`),
    '',
  ].join('\n');
}

function writeDescribe(command: 'boss gate' | 'boss gate final', context: CliContext): void {
  const description = describeCommand(commandDescriptions[command]!);
  writeOutput(description, context, () => `${JSON.stringify(description, null, 2)}\n`);
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss gate' });
  const subcommand = context.positionals[0];

  if (subcommand === 'final') {
    const finalArgv = argv.slice(1);
    const finalContext = createCliContext(finalArgv, { command: 'boss gate final' });
    if (finalContext.values.describe) {
      writeDescribe('boss gate final', finalContext);
      return 0;
    }
    const feature = parseFinalFeature(finalArgv);
    const result = evaluateFinalGate(feature, { cwd });
    writeOutput(result, finalContext, (data) => renderFinalText(data as FinalGateResult));
    return result.passed ? 0 : 1;
  }

  if (context.values.describe) {
    writeDescribe('boss gate', context);
    return 0;
  }

  const input = parseGateInput(argv);
  const result = evaluateGates(input.feature, input.gateName, { cwd });
  const payload = {
    feature: input.feature,
    gate: result.gate,
    passed: result.passed,
    checks: result.checks,
    skipped: Boolean(result.skipped),
  };
  writeOutput(payload, context, (data) => renderGateText(data as typeof payload));
  return result.passed ? 0 : 1;
}
