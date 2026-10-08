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
import {
  checkCanProceed,
  checkCanRetry,
  checkStage,
} from '../../runtime/application/inspection.mts';
import { printRuntimeHelp } from './agent-command-utils.mts';

function printHelp(): void {
  printRuntimeHelp('check-stage', 'boss runtime check-stage FEATURE [stage] [options]');
}

export function parseArgs(argv: string[]) {
  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    return { help: true } as const;
  }

  const parsed = {
    feature: '',
    stage: '',
    canProceed: false,
    canRetry: false,
    agents: false,
    json: false,
    summary: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--can-proceed') {
      parsed.canProceed = true;
      continue;
    }
    if (arg === '--can-retry') {
      parsed.canRetry = true;
      continue;
    }
    if (arg === '--agents') {
      parsed.agents = true;
      continue;
    }
    if (arg === '--json') {
      parsed.json = true;
      continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg === '--summary') {
      parsed.summary = true;
      continue;
    }
    if (arg.startsWith('-')) {
      throw new Error(`未知选项: ${arg}`);
    }
    if (!parsed.feature) {
      parsed.feature = arg;
      continue;
    }
    if (!parsed.stage) {
      parsed.stage = arg;
      continue;
    }
    throw new Error(`多余的参数: ${arg}`);
  }

  if (!parsed.feature) {
    throw new Error('缺少 feature 参数');
  }
  return parsed;
}

function renderTextStage(
  stageId: string,
  payload: { name?: string; status?: string } | null,
): string {
  if (!payload) {
    return `阶段 ${stageId}: unknown\n`;
  }
  return `阶段 ${stageId} (${payload.name || ''}): ${payload.status}\n`;
}

function renderSummary(payload: {
  status: string;
  stages: Record<string, { status: string }>;
}): string {
  const lines = [`status: ${payload.status}`];
  for (const [stageId, stage] of Object.entries(payload.stages || {})) {
    lines.push(`stage ${stageId}: ${stage.status}`);
  }
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
  const context = createCliContext(argv, { command: 'boss runtime check-stage' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['check-stage']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['check-stage'], null, 2)}\n`,
    );
    return 0;
  }

  const parsed = parseArgs(argv);
  if ('help' in parsed) {
    printHelp();
    return 0;
  }

  try {
    if (parsed.canProceed) {
      const result = checkCanProceed(parsed.feature, parsed.stage, { cwd });
      if (!result.ok) {
        if (context.useJson) {
          writeOutput({ ok: false, reason: result.reason }, context, () => '');
        } else {
          process.stderr.write(`${result.reason}\n`);
        }
        return 1;
      }
      writeOutput({ ok: true, reason: '' }, context, () => `阶段 ${parsed.stage} 可以开始\n`);
      return 0;
    }

    if (parsed.canRetry) {
      const result = checkCanRetry(parsed.feature, parsed.stage, { cwd });
      if (!result.ok) {
        if (context.useJson) {
          writeOutput({ ok: false, reason: result.reason }, context, () => '');
        } else {
          process.stderr.write(`${result.reason}\n`);
        }
        return 1;
      }
      writeOutput({ ok: true, reason: '' }, context, () => `阶段 ${parsed.stage} 可以重试\n`);
      return 0;
    }

    const payload = checkStage(parsed.feature, parsed.stage, { cwd });
    if (parsed.agents && parsed.stage) {
      const agents =
        payload && typeof payload === 'object' && 'agents' in payload && payload.agents
          ? payload.agents
          : {};
      writeOutput(
        agents,
        context,
        () =>
          Object.entries(agents)
            .map(
              ([agentName, agentState]) =>
                `${agentName}: ${(agentState as { status: string }).status}`,
            )
            .join('\n') + '\n',
      );
      return 0;
    }

    if (parsed.summary || !parsed.stage) {
      writeOutput(payload, context, (data) =>
        renderSummary(data as { status: string; stages: Record<string, { status: string }> }),
      );
      return 0;
    }

    writeOutput(payload, context, (data) =>
      renderTextStage(parsed.stage, data as { name?: string; status?: string } | null),
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, parsed.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime check-stage',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
