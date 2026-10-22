#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  CliUserError,
  consumeCliContractOption,
  createCliContext,
  describeCommand,
  parseLimit,
  runMain,
  writeOutput,
} from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { queryAgentSection, readFeatureSummary } from '../../runtime/application/memory.mts';
import { printRuntimeHelp, requireOptionValue } from './agent-command-utils.mts';

function printHelp(): void {
  printRuntimeHelp('query-memory', 'boss runtime query-memory FEATURE [options]');
}

export function parseArgs(argv: string[]) {
  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    return { help: true } as const;
  }

  const parsed = {
    feature: '',
    startup: false,
    json: false,
    agent: '',
    stage: null as number | null,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--startup') {
      parsed.startup = true;
      continue;
    }
    if (arg === '--agent') {
      parsed.agent = requireOptionValue('--agent', argv[index + 1]);
      index += 1;
      continue;
    }
    if (arg === '--stage') {
      const rawStage = requireOptionValue('--stage', argv[index + 1]);
      const stage = Number(rawStage);
      if (!Number.isInteger(stage) || stage < 0) {
        throw new CliUserError({
          code: 'invalid_stage',
          message: `Invalid --stage value: ${rawStage}`,
          input: { stage: rawStage },
          retryable: false,
          suggestion: 'Use a non-negative integer stage number',
        });
      }
      parsed.stage = stage;
      index += 1;
      continue;
    }
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
  const context = createCliContext(argv, { command: 'boss runtime query-memory' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['query-memory']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['query-memory'], null, 2)}\n`,
    );
    return 0;
  }

  let feature = '';
  try {
    const parsed = parseArgs(argv);
    if ('help' in parsed) {
      printHelp();
      return 0;
    }
    feature = parsed.feature;

    const summary = readFeatureSummary(parsed.feature, { cwd });
    if (parsed.agent) {
      const payload = {
        feature: parsed.feature,
        agent: parsed.agent,
        stage: parsed.stage,
        memories: queryAgentSection(parsed.feature, {
          cwd,
          agent: parsed.agent,
          stage: parsed.stage ?? undefined,
          limit: parseLimit(context.values.limit),
        }),
      };
      writeOutput(
        payload,
        context,
        () =>
          payload.memories.map((item) => `- [${item.category}] ${item.summary}`).join('\n') + '\n',
      );
      return 0;
    }

    if (parsed.startup) {
      const payload = { feature: parsed.feature, startupSummary: summary.startupSummary || [] };
      writeOutput(
        payload,
        context,
        () =>
          payload.startupSummary.map((item) => `- [${item.category}] ${item.summary}`).join('\n') +
          '\n',
      );
      return 0;
    }

    writeOutput(summary, context, () => `${JSON.stringify(summary, null, 2)}\n`);
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime query-memory',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
