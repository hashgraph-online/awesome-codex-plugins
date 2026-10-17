#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  CliUserError,
  createCliContext,
  describeCommand,
  runMain,
  writeOutput,
} from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import {
  getArtifactStatus,
  getReadyArtifacts,
  listArtifactStatuses,
} from '../../runtime/application/pipeline.mts';
import { printRuntimeHelp } from './agent-command-utils.mts';

function showHelp(): void {
  printRuntimeHelp(
    'get-ready-artifacts',
    'boss runtime get-ready-artifacts FEATURE [ARTIFACT] [options]',
  );
}

function exitError(message: string): never {
  throw new Error(message);
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
  const context = createCliContext(argv, { command: 'boss runtime get-ready-artifacts' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['get-ready-artifacts']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['get-ready-artifacts'], null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  let feature = '';
  let artifact = '';
  let canStart = false;
  let ready = false;
  let dagPath = '';
  let jsonOutput = false;

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]!;
    if (arg === '--can-start') {
      canStart = true;
      continue;
    }
    if (arg === '--ready') {
      ready = true;
      continue;
    }
    if (arg === '--dag') {
      const nextValue = argv[i + 1];
      if (!nextValue || nextValue.startsWith('-')) {
        exitError('--dag 需要指定 path');
      }
      dagPath = nextValue;
      i += 1;
      continue;
    }
    if (arg === '--json') {
      jsonOutput = true;
      continue;
    }
    if (arg === '--describe' || arg === '--dry-run') {
      continue;
    }
    if (arg === '--fields' || arg === '--limit' || arg === '--json-input') {
      if (argv[i + 1] && !argv[i + 1]!.startsWith('-')) i += 1;
      continue;
    }
    if (
      arg.startsWith('--fields=') ||
      arg.startsWith('--limit=') ||
      arg.startsWith('--json-input=')
    ) {
      continue;
    }
    if (arg.startsWith('-')) {
      exitError(`未知选项: ${arg}`);
    }
    if (!feature) {
      feature = arg;
    } else if (!artifact) {
      artifact = arg;
    } else {
      exitError(`多余的参数: ${arg}`);
    }
  }

  if (!feature) {
    exitError('缺少 feature 参数');
  }

  try {
    if (canStart) {
      if (!artifact) {
        exitError('--can-start 需要指定 artifact');
      }
      const status = getArtifactStatus(feature, artifact, {
        cwd,
        dagPath,
        ignoreSkipped: true,
      });
      if (status.status === 'completed') {
        writeOutput(status, context, () => `${artifact} 已完成\n`);
        return 0;
      }
      if (status.status === 'ready') {
        writeOutput(status, context, () => `${artifact} 可以开始（所有依赖已就绪）\n`);
        return 0;
      }
      if (status.status === 'blocked') {
        process.stderr.write(`${artifact} 不能开始，缺少依赖:${status.missing!.join(' ')}\n`);
        return 1;
      }
      process.stderr.write(`${artifact} 不能开始\n`);
      return 1;
    }

    if (ready) {
      const readyList = getReadyArtifacts(feature, { cwd, dagPath });
      if (readyList.length === 0) {
        writeOutput([], context, () => (jsonOutput ? '[]\n' : '没有就绪的产物\n'));
        return 0;
      }
      const payload = readyList.map((item) => item.artifact);
      if (context.useJson || jsonOutput) {
        writeOutput(payload, context, () => `${JSON.stringify(payload)}\n`);
        return 0;
      }
      writeOutput(
        payload,
        context,
        () =>
          `就绪的产物：\n${readyList.map((item) => `  ✅ ${item.artifact} (Agent: ${item.agent}, 阶段: ${item.stage})`).join('\n')}\n`,
      );
      return 0;
    }

    if (artifact) {
      const status = getArtifactStatus(feature, artifact, { cwd, dagPath });
      writeOutput(
        status,
        context,
        () =>
          `${artifact}: ${status.status === 'skipped' ? 'skipped' : status.status === 'completed' ? 'completed' : 'pending'}\n`,
      );
      return 0;
    }

    const statuses = listArtifactStatuses(feature, { cwd, dagPath });
    writeOutput(
      statuses,
      context,
      () =>
        statuses
          .map(({ artifact: name, status }) =>
            status === 'completed'
              ? `  ✅ ${name}`
              : status === 'skipped'
                ? `  ⏭️  ${name} (skipped)`
                : `  ⏳ ${name}`,
          )
          .join('\n') + '\n',
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime get-ready-artifacts',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
