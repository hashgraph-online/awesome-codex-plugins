#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createCliContext, describeCommand, runMain, writeOutput } from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { printRuntimeHelp, writeActionPlan } from './agent-command-utils.mts';
import {
  materializeTodoRuntime,
  renderMutationText,
  resolveMaterializeTodoInput,
  toFeatureNotFoundError,
} from './conversation-command-utils.mts';

function showHelp(): void {
  printRuntimeHelp('materialize-todo', 'boss runtime materialize-todo FEATURE [options]');
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime materialize-todo' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['materialize-todo']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['materialize-todo'], null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveMaterializeTodoInput(argv, context);
  if (context.values.dryRun) {
    writeActionPlan(
      [
        {
          type: 'materialize_todo',
          feature: input.feature,
          threadId: input.threadId,
          writes_event: true,
        },
      ],
      context,
      'medium',
    );
    return 0;
  }

  try {
    const payload = materializeTodoRuntime(input, { cwd });
    writeOutput(payload, context, () => renderMutationText(payload));
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime materialize-todo',
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
