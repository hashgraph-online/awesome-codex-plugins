#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createCliContext, describeCommand, runMain, writeOutput } from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { printRuntimeHelp } from './agent-command-utils.mts';
import {
  listTodosRuntime,
  renderTodoListText,
  toFeatureNotFoundError,
} from './conversation-command-utils.mts';

function showHelp(): void {
  printRuntimeHelp('list-todos', 'boss runtime list-todos FEATURE [options]');
}

function resolveFeature(argv: string[]): string {
  const feature = argv.find((arg) => !arg.startsWith('-'));
  if (!feature) {
    throw new Error('缺少 feature 参数');
  }
  return feature;
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime list-todos' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['list-todos']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['list-todos'], null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const feature = resolveFeature(argv);
  try {
    const payload = listTodosRuntime(feature, context, { cwd });
    writeOutput(payload, context, (data) =>
      renderTodoListText(data as Array<Record<string, unknown>>),
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), { command: 'boss runtime list-todos' });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
