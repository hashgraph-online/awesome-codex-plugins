#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createCliContext, describeCommand, runMain, writeOutput } from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { printRuntimeHelp, writeActionPlan } from './agent-command-utils.mts';
import {
  openConversationRuntime,
  renderMutationText,
  resolveOpenConversationInput,
  toFeatureNotFoundError,
} from './conversation-command-utils.mts';

function showHelp(): void {
  printRuntimeHelp('open-conversation', 'boss runtime open-conversation FEATURE [options]');
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime open-conversation' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['open-conversation']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['open-conversation'], null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveOpenConversationInput(argv, context);
  if (context.values.dryRun) {
    writeActionPlan(
      [{ type: 'open_conversation', feature: input.feature, writes_event: true }],
      context,
      'medium',
    );
    return 0;
  }

  try {
    const payload = openConversationRuntime(input, { cwd });
    writeOutput(payload, context, () =>
      renderMutationText(payload as unknown as Record<string, unknown>),
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime open-conversation',
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
