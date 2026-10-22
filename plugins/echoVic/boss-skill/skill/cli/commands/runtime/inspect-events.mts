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
import { inspectEvents } from '../../runtime/application/inspection.mts';
import { printRuntimeHelp } from './agent-command-utils.mts';

function printHelp(): void {
  printRuntimeHelp('inspect-events', 'boss runtime inspect-events FEATURE [options]');
}

export function parseArgs(argv: string[]) {
  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    return { help: true } as const;
  }

  const parsed = {
    feature: '',
    limit: undefined as string | undefined,
    type: '',
    json: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]!;
    switch (arg) {
      case '--limit':
        if (!argv[i + 1]) throw new Error('--limit 需要指定值');
        parsed.limit = argv[i + 1];
        i += 1;
        break;
      case '--type':
        if (!argv[i + 1]) throw new Error('--type 需要指定值');
        parsed.type = argv[i + 1]!;
        i += 1;
        break;
      case '--json':
      case '--describe':
      case '--dry-run':
        parsed.json = true;
        break;
      case '--fields':
      case '--json-input':
        if (argv[i + 1] && !argv[i + 1]!.startsWith('-')) i += 1;
        break;
      default:
        if (arg.startsWith('--limit=')) {
          parsed.limit = arg.slice('--limit='.length);
          break;
        }
        if (arg.startsWith('--type=')) {
          parsed.type = arg.slice('--type='.length);
          break;
        }
        if (arg.startsWith('--fields=') || arg.startsWith('--json-input=')) {
          break;
        }
        if (arg.startsWith('-')) {
          throw new Error(`未知选项: ${arg}`);
        }
        if (!parsed.feature) {
          parsed.feature = arg;
        } else {
          throw new Error(`多余的参数: ${arg}`);
        }
    }
  }

  if (!parsed.feature) {
    throw new Error('缺少 feature 参数');
  }
  return parsed;
}

function renderText(payload: ReturnType<typeof inspectEvents>): string {
  const lines: string[] = [];
  for (const event of payload.events) {
    lines.push(`#${event.id} ${event.type} ${event.timestamp}`);
  }
  return `${lines.join('\n')}${lines.length ? '\n' : ''}`;
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
  const context = createCliContext(argv, { command: 'boss runtime inspect-events' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['inspect-events']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['inspect-events'], null, 2)}\n`,
    );
    return 0;
  }

  const parsed = parseArgs(argv);
  if ('help' in parsed) {
    printHelp();
    return 0;
  }

  try {
    const payload = inspectEvents(parsed.feature, {
      cwd,
      limit: parseLimit(parsed.limit ?? '20'),
      type: parsed.type,
    });
    writeOutput(payload, context, (data) => renderText(data as ReturnType<typeof inspectEvents>));
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, parsed.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime inspect-events',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
