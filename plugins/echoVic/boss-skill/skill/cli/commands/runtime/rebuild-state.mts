#!/usr/bin/env node
/**
 * 从事件流重建 `.boss/<feature>/.meta/execution.json`。
 *
 * 架构主张是「事件是真相源，execution.json 是只读投影」，但此前没有任何命令能重建它：
 * 投影一旦损坏（手工编辑、磁盘错误、写入中途被杀），事件流完好也没用——每条命令都先
 * readExecutionView，直接抛出裸 JSON 解析错误，feature 从此不可用。这条命令补上那个出口。
 */
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import { createCliContext, describeCommand, runMain, writeOutput } from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { materializeState } from '../../runtime/projectors/materialize-state.mts';
import { printRuntimeHelp } from './agent-command-utils.mts';

function printHelp(): void {
  printRuntimeHelp('rebuild-state', 'boss runtime rebuild-state FEATURE [options]');
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime rebuild-state' });
  if (context.values.describe) {
    const description = describeCommand(runtimeCommandDescriptions['rebuild-state']!);
    writeOutput(description, context, () => `${JSON.stringify(description, null, 2)}\n`);
    return 0;
  }

  const feature = context.positionals[0];
  if (!feature || argv.includes('-h') || argv.includes('--help')) {
    printHelp();
    return feature ? 0 : 1;
  }

  const result = materializeState(feature, cwd);
  writeOutput(
    {
      feature,
      eventCount: result.eventCount,
      execJsonPath: path.relative(cwd, result.execJsonPath),
      rebuilt: true,
    },
    context,
    (data) => {
      const payload = data as { eventCount: number; execJsonPath: string };
      return `已从 ${payload.eventCount} 条事件重建 ${payload.execJsonPath}\n`;
    },
  );
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime rebuild-state',
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
