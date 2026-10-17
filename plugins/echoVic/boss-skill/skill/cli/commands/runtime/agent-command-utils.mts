import {
  type CliContext,
  CliUserError,
  type JsonObject,
  renderHelp,
  writeOutput,
} from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';

export function missingRequiredArgument(argument: string): CliUserError {
  return new CliUserError({
    code: 'missing_required_argument',
    message: `Missing ${argument} argument`,
    input: { argument },
    retryable: false,
    suggestion: 'Run this command with --describe to see required parameters',
  });
}

export function requireInputString(value: unknown, argument: string): string {
  if (value === undefined || value === null || value === '') {
    throw missingRequiredArgument(argument);
  }
  return String(value);
}

export function optionalInputString(value: unknown): string | undefined {
  return value === undefined || value === null || value === '' ? undefined : String(value);
}

export function requireOptionValue(flag: string, value: string | undefined): string {
  if (!value || value.startsWith('-')) {
    throw new CliUserError({
      code: 'missing_option_value',
      message: `${flag} requires a value`,
      input: { option: flag },
      retryable: false,
      suggestion: `Pass a value after ${flag}`,
    });
  }
  return value;
}

export function toFeatureNotFoundError(err: unknown, feature: string): unknown {
  const message = err instanceof Error ? err.message : String(err);
  if (message.includes('未找到执行文件') || message.includes('未找到事件文件')) {
    return new CliUserError({
      code: 'feature_not_found',
      message,
      input: { feature },
      retryable: false,
      suggestion: 'Run boss runtime init-pipeline <feature> first',
    });
  }
  return err;
}

export function writeActionPlan(
  actions: JsonObject[],
  context: CliContext,
  riskTier: 'low' | 'medium' | 'high' = 'medium',
): void {
  writeOutput(
    {
      actions,
      risk_tier: riskTier,
      requires_approval: riskTier === 'high',
    },
    context,
    () => actions.map((action) => `Would ${String(action.type)}\n`).join(''),
  );
}

export function printRuntimeHelp(commandName: string, usage: string): void {
  const description = runtimeCommandDescriptions[commandName];
  if (!description) {
    throw new Error(`Missing runtime command description: ${commandName}`);
  }
  process.stdout.write(renderHelp(description, usage));
}
