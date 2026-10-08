import {
  type CliContext,
  CliUserError,
  createCliContext,
  describeCommand,
  writeOutput,
} from '../../cli/contract.mts';
import { commandDescriptions } from '../../cli/registry.mts';
import { type QaAttackResult, runQaAttack } from '../../runtime/application/qa-attack.mts';

function removeFirstPositional(argv: string[], positional: string | undefined): string[] {
  if (!positional) return argv;
  const index = argv.indexOf(positional);
  if (index === -1) return argv;
  return [...argv.slice(0, index), ...argv.slice(index + 1)];
}

function parseAttackFeature(argv: string[]): string {
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
      message: 'Usage: boss qa attack FEATURE [options]',
      input: { argument: 'feature' },
      retryable: false,
      suggestion: 'Run boss qa attack --describe to verify command parameters',
    });
  }
  return feature;
}

function renderAttackText(result: QaAttackResult): string {
  const lines = [
    result.status === 'passed' ? 'QA attack passed' : 'QA attack failed',
    `Feature: ${result.feature}`,
  ];
  for (const finding of result.findings) {
    lines.push(`${finding.severity.toUpperCase()} ${finding.status}: ${finding.id}`);
  }
  lines.push('');
  return lines.join('\n');
}

function writeDescribe(command: 'boss qa' | 'boss qa attack', context: CliContext): void {
  const description = describeCommand(commandDescriptions[command]!);
  writeOutput(description, context, () => `${JSON.stringify(description, null, 2)}\n`);
}

function toFeatureNotFound(err: unknown, feature: string): never {
  const message = err instanceof Error ? err.message : String(err);
  if (message.includes('未找到执行文件') || message.includes('未找到事件文件')) {
    throw new CliUserError({
      code: 'feature_not_found',
      message,
      input: { feature },
      retryable: false,
      suggestion: 'Run boss runtime init-pipeline before QA attack',
    });
  }
  throw err;
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss qa' });
  const subcommand = context.positionals[0];

  if (context.values.describe && !subcommand) {
    writeDescribe('boss qa', context);
    return 0;
  }

  if (subcommand !== 'attack') {
    throw new CliUserError({
      code: 'missing_argument',
      message: 'Usage: boss qa attack FEATURE [options]',
      input: { argument: 'subcommand' },
      retryable: false,
      suggestion: 'Run boss qa --describe to list available commands',
    });
  }

  const attackArgv = removeFirstPositional(argv, subcommand);
  const attackContext = createCliContext(attackArgv, { command: 'boss qa attack' });
  if (attackContext.values.describe) {
    writeDescribe('boss qa attack', attackContext);
    return 0;
  }

  const feature = parseAttackFeature(attackArgv);
  let result: QaAttackResult;
  try {
    result = runQaAttack(feature, { cwd });
  } catch (err) {
    toFeatureNotFound(err, feature);
  }
  writeOutput(result, attackContext, (data) => renderAttackText(data as QaAttackResult));
  return result.status === 'passed' ? 0 : 1;
}
