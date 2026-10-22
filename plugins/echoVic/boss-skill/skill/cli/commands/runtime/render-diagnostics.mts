#!/usr/bin/env node
import * as fs from 'node:fs';
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
import {
  inspectEvents,
  inspectPipeline,
  inspectProgress,
} from '../../runtime/application/inspection.mts';
import { renderHtml } from '../../runtime/report/render-html.mts';
import { buildSummaryModel } from '../../runtime/report/summary-model.mts';
import { printRuntimeHelp } from './agent-command-utils.mts';

function printHelp(): void {
  printRuntimeHelp('render-diagnostics', 'boss runtime render-diagnostics FEATURE [options]');
}

export function parseArgs(argv: string[]) {
  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    return { help: true } as const;
  }

  const parsed = { feature: '', stdout: false };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--stdout') {
      parsed.stdout = true;
      continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
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

export function buildDiagnosticsModel(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
) {
  const summary = buildSummaryModel(feature, { cwd });
  const inspection = inspectPipeline(feature, { cwd });
  let events: ReturnType<typeof inspectEvents>['events'] = [];
  let progress: ReturnType<typeof inspectProgress>['events'] = [];
  try {
    events = inspectEvents(feature, { cwd, limit: 8 }).events;
  } catch {
    events = [];
  }
  try {
    progress = inspectProgress(feature, { cwd, limit: 8 }).events;
  } catch {
    progress = [];
  }

  return {
    ...summary,
    currentStage: inspection.currentStage,
    readyArtifacts: inspection.readyArtifacts,
    activeAgents: inspection.activeAgents.map((item) => `${item.agent}@${item.stage}`),
    recentFailures: inspection.recentFailures,
    recentEvents: events,
    progressEvents: progress.map((event) => ({
      type: String(event.type || ''),
      timestamp: String(event.timestamp || ''),
    })),
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime render-diagnostics' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['render-diagnostics']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['render-diagnostics'], null, 2)}\n`,
    );
    return 0;
  }

  const parsed = parseArgs(argv);
  if ('help' in parsed) {
    printHelp();
    return 0;
  }

  const relativeOutputPath = path.posix.join('.boss', parsed.feature, 'diagnostics.html');
  const outputPath = path.join(cwd, '.boss', parsed.feature, 'diagnostics.html');

  try {
    if (context.values.dryRun && !parsed.stdout) {
      writeOutput(
        {
          actions: [{ type: 'write_file', path: relativeOutputPath, format: 'html' }],
          risk_tier: 'medium',
          requires_approval: false,
        },
        context,
        () => `would write ${relativeOutputPath}\n`,
      );
      return 0;
    }

    const model = buildDiagnosticsModel(parsed.feature, { cwd });
    const html = renderHtml(model);
    if (parsed.stdout) {
      process.stdout.write(html);
      return 0;
    }

    fs.writeFileSync(outputPath, html, 'utf8');
    writeOutput(
      { feature: parsed.feature, outputPath: relativeOutputPath, format: 'html' },
      context,
      () => `诊断页已生成: ${outputPath}\n`,
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, parsed.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime render-diagnostics',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
