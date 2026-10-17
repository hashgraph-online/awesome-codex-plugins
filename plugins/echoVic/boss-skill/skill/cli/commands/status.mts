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
    throw new Error('Usage: boss status FEATURE [options]');
  }
  return { feature, driver };
}

function renderText(status: BossStatus): string {
  const stage = status.currentStage
    ? `${status.currentStage.id} (${status.currentStage.name || 'unnamed'}) ${status.currentStage.status}`
    : 'none';

  return [
    `Feature: ${status.feature}`,
    `Driver: ${status.driver.name}`,
    `Stage: ${stage}`,
    `Ready artifacts: ${status.readyArtifacts.join(', ') || 'none'}`,
    status.checkpoint.checkpointRequired
      ? `CHECKPOINT_REQUIRED: ${status.checkpoint.reason}`
      : status.driver.hooks
        ? 'Checkpoint: hooks-managed by Claude Code'
        : 'Checkpoint: ready',
    ...(status.checkpoint.continueCommand
      ? [`Continue: ${status.checkpoint.continueCommand}`]
      : ['Pipeline complete: no further action']),
    // 上游产品资产重做之后，上一轮的任务清单 / 测试报告不再对应当前状态。
    // 不提示的话，用户会把过期产物当成当前结论。
    ...(status.staleRunArtifacts.length > 0
      ? [
          `Stale from a previous round: ${status.staleRunArtifacts
            .map((item) => `${item.artifact} (superseded by ${item.supersededBy})`)
            .join(', ')}`,
        ]
      : []),
    '',
  ].join('\n');
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss status' });
  if (context.values.describe) {
    const description = describeCommand(commandDescriptions['boss status']!);
    writeOutput(description, context, () => `${JSON.stringify(description, null, 2)}\n`);
    return 0;
  }

  const { feature, driver } = parseFeatureAndDriver(argv);
  const status = buildBossStatus(feature, { cwd, driver });
  writeOutput(status, context, (data) => renderText(data as BossStatus));
  return 0;
}
