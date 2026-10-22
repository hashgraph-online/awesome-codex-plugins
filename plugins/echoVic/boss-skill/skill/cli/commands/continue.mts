import { createCliContext, describeCommand, writeOutput } from '../cli/contract.mts';
import { commandDescriptions } from '../cli/registry.mts';
import { type BossStatus, buildBossStatus } from '../runtime/application/checkpoints.mts';

function parseFeatureAndDriver(argv: string[]): { feature: string; driver: string } {
  let feature = '';
  let driver = 'generic';

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--json' || arg === '--describe') {
      continue;
    }
    if (arg === '--driver') {
      const value = argv[index + 1];
      if (!value || value.startsWith('-')) {
        throw new Error('--driver requires a value');
      }
      driver = value;
      index += 1;
      continue;
    }
    if (arg.startsWith('--driver=')) {
      driver = arg.slice('--driver='.length);
      continue;
    }
    if (arg.startsWith('-')) {
      throw new Error(`未知选项: ${arg}`);
    }
    if (!feature) {
      feature = arg;
      continue;
    }
    throw new Error(`多余的参数: ${arg}`);
  }

  if (!feature) {
    throw new Error('Usage: boss continue FEATURE [options]');
  }
  return { feature, driver };
}

function renderText(status: BossStatus): string {
  if (!status.checkpoint.checkpointRequired) {
    return [
      'Ready to continue',
      `Feature: ${status.feature}`,
      `Driver: ${status.driver.name}`,
      `Next: ${status.readyArtifacts[0] || 'none'}`,
      '',
    ].join('\n');
  }

  const checks = status.checkpoint.requiredChecks.map((check) => `- ${check.command}`);
  return [
    'CHECKPOINT_REQUIRED',
    `Feature: ${status.feature}`,
    `Driver: ${status.driver.name}`,
    `Reason: ${status.checkpoint.reason}`,
    'Required checks:',
    ...(checks.length > 0 ? checks : ['- none']),
    `Continue: ${status.checkpoint.continueCommand}`,
    '',
  ].join('\n');
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss continue' });
  if (context.values.describe) {
    const description = describeCommand(commandDescriptions['boss continue']!);
    writeOutput(description, context, () => `${JSON.stringify(description, null, 2)}\n`);
    return 0;
  }

  const { feature, driver } = parseFeatureAndDriver(argv);
  const status = buildBossStatus(feature, { cwd, driver });
  writeOutput(status, context, (data) => renderText(data as BossStatus));
  return status.blockedReason ? 1 : 0;
}
