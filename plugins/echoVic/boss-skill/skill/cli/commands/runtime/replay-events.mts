#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  CliUserError,
  createCliContext,
  describeCommand,
  parseLimit,
  runMain,
  writeOutput,
} from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { replayEvents, replaySnapshot } from '../../runtime/application/inspection.mts';
import { printRuntimeHelp } from './agent-command-utils.mts';

function printHelp(): void {
  printRuntimeHelp('replay-events', 'boss runtime replay-events FEATURE [options]');
}

export function parseArgs(argv: string[]) {
  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    return { help: true } as const;
  }

  const parsed = {
    feature: '',
    at: '',
    type: '',
    limit: undefined as string | undefined,
    compact: false,
    json: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--at') {
      parsed.at = argv[index + 1] || '';
      index += 1;
      continue;
    }
    if (arg === '--type') {
      parsed.type = argv[index + 1] || '';
      index += 1;
      continue;
    }
    if (arg === '--limit') {
      parsed.limit = argv[index + 1] || '20';
      index += 1;
      continue;
    }
    if (arg === '--compact') {
      parsed.compact = true;
      continue;
    }
    if (arg === '--json') {
      parsed.json = true;
      continue;
    }
    if (arg.startsWith('-')) {
      if (arg === '--describe' || arg === '--dry-run') {
        continue;
      }
      if (arg === '--fields' || arg === '--json-input') {
        if (argv[index + 1] && !argv[index + 1]!.startsWith('-')) index += 1;
        continue;
      }
      if (arg.startsWith('--limit=')) {
        parsed.limit = arg.slice('--limit='.length);
        continue;
      }
      if (arg.startsWith('--type=')) {
        parsed.type = arg.slice('--type='.length);
        continue;
      }
      if (arg.startsWith('--at=')) {
        parsed.at = arg.slice('--at='.length);
        continue;
      }
      if (arg.startsWith('--fields=') || arg.startsWith('--json-input=')) {
        continue;
      }
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

function renderVerbose(payload: unknown): string {
  return `${JSON.stringify(payload, null, 2)}\n`;
}

function renderCompactText(payload: {
  events?: Array<{ id: number; timestamp: string; type: string; data?: Record<string, unknown> }>;
}): string {
  return (
    (payload.events || [])
      .map((event) => {
        const stage = event.data && event.data.stage != null ? event.data.stage : '-';
        const agent = event.data && event.data.agent ? event.data.agent : '-';
        return `#${event.id} [${event.timestamp}] ${event.type} stage=${stage} agent=${agent}`;
      })
      .join('\n') + ((payload.events || []).length ? '\n' : '')
  );
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
  const context = createCliContext(argv, { command: 'boss runtime replay-events' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['replay-events']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['replay-events'], null, 2)}\n`,
    );
    return 0;
  }

  const parsed = parseArgs(argv);
  if ('help' in parsed) {
    printHelp();
    return 0;
  }

  try {
    if (parsed.at) {
      const payload = replaySnapshot(parsed.feature, parsed.at, { cwd });
      writeOutput(payload, context, renderVerbose);
      return 0;
    }

    const payload = replayEvents(parsed.feature, {
      cwd,
      limit: parseLimit(parsed.limit ?? '20'),
      type: parsed.type,
    });

    writeOutput(payload, context, (data) =>
      parsed.compact ? renderCompactText(data as typeof payload) : renderVerbose(data),
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, parsed.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime replay-events',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
