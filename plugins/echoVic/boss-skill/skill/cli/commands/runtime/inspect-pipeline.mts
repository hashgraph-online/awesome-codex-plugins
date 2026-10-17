#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  CliUserError,
  consumeCliContractOption,
  createCliContext,
  describeCommand,
  runMain,
  writeOutput,
} from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { inspectPipeline } from '../../runtime/application/inspection.mts';
import { printRuntimeHelp } from './agent-command-utils.mts';

function printHelp(): void {
  printRuntimeHelp('inspect-pipeline', 'boss runtime inspect-pipeline FEATURE [options]');
}

export function parseArgs(argv: string[]) {
  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    return { help: true } as const;
  }

  const parsed = {
    feature: '',
    json: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      if (arg === '--json') parsed.json = true;
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) {
      throw new Error(`未知选项: ${arg}`);
    }
    if (!parsed.feature) {
      parsed.feature = arg;
      continue;
    }
    throw new Error(`多余的参数: ${arg}`);
  }

  if (!parsed.feature) {
    throw new Error('缺少 feature 参数');
  }
  return parsed;
}

function renderText(summary: ReturnType<typeof inspectPipeline>): string {
  const lines: string[] = [];
  lines.push(`feature: ${summary.feature}`);
  lines.push(`status: ${summary.status}`);
  if (summary.currentStage) {
    lines.push(
      `currentStage: ${summary.currentStage.id} (${summary.currentStage.name}) ${summary.currentStage.status}\n`,
    );
  }
  lines.push(`readyArtifacts: ${summary.readyArtifacts.join(', ') || 'none'}`);
  lines.push(
    `activeAgents: ${summary.activeAgents.map((item) => `${item.agent}@${item.stage}`).join(', ') || 'none'}`,
  );
  lines.push(`pack: ${summary.pack.name}`);
  if (summary.artifactDag.warning) {
    lines.push(`artifactDagWarning: ${summary.artifactDag.warning}`);
  }
  if (summary.pause?.paused) {
    lines.push(`pause: ${summary.pause.reason || 'paused'}`);
  }
  lines.push(
    `plugins: ${summary.plugins.active.map((plugin) => plugin.name).join(', ') || 'none'}`,
  );
  lines.push(
    `conversationMetrics: opened=${summary.conversationMetrics.opened} resolved=${summary.conversationMetrics.resolved} todos=${summary.conversationMetrics.todos} huddles=${summary.conversationMetrics.huddles} unresolved=${summary.conversationMetrics.unresolved}`,
  );
  lines.push(`derivedTodos: ${summary.derivedTodos.length}`);
  lines.push(
    `memoryStartup: ${((summary.memory && summary.memory.startupSummary) || []).map((item) => item.summary).join(' | ') || 'none'}`,
  );
  return `${lines.join('\n')}\n`;
}

function toFeatureNotFoundError(err: unknown, feature: string): unknown {
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

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime inspect-pipeline' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['inspect-pipeline']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['inspect-pipeline'], null, 2)}\n`,
    );
    return 0;
  }

  const parsed = parseArgs(argv);
  if ('help' in parsed) {
    printHelp();
    return 0;
  }

  try {
    const summary = inspectPipeline(parsed.feature, { cwd });
    writeOutput(summary, context, (data) => renderText(data as ReturnType<typeof inspectPipeline>));
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, parsed.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime inspect-pipeline',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
