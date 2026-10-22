#!/usr/bin/env node
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  type CliContext,
  consumeCliContractOption,
  createCliContext,
  describeCommand,
  readJsonInput,
  runMain,
  writeOutput,
} from '../../cli/contract.mts';
import { runtimeCommandDescriptions } from '../../cli/registry.mts';
import { resumeWorkflow } from '../../runtime/application/workflow.mts';
import {
  printRuntimeHelp,
  requireInputString,
  requireOptionValue,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

interface ResumeInput {
  feature: string;
  fromRunId: string;
}

function showHelp(): void {
  printRuntimeHelp('resume', 'boss runtime resume FEATURE --from-run RUN_ID [options]');
}

function parseFlatInput(argv: string[]): ResumeInput {
  let feature = '';
  let fromRunId = '';

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--from-run') {
      fromRunId = requireOptionValue('--from-run', argv[index + 1]);
      index += 1;
      continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) throw new Error(`未知选项: ${arg}`);
    if (!feature) feature = arg;
    else throw new Error(`多余的参数: ${arg}`);
  }

  return {
    feature: requireInputString(feature, 'feature'),
    fromRunId: requireInputString(fromRunId, 'fromRunId'),
  };
}

function resolveInput(argv: string[], context: CliContext): ResumeInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      fromRunId: requireInputString(input.fromRunId, 'fromRunId'),
    };
  }
  return parseFlatInput(argv);
}

function actionFor(input: ResumeInput) {
  return {
    type: 'resume_workflow',
    feature: input.feature,
    from_run: input.fromRunId,
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime resume' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions.resume!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions.resume, null, 2)}\n`,
    );
    return 0;
  }

  if (argv.length === 0 || argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return argv.length === 0 ? 1 : 0;
  }

  const input = resolveInput(argv, context);
  if (context.values.dryRun) {
    writeActionPlan([actionFor(input)], context, 'medium');
    return 0;
  }

  try {
    const result = resumeWorkflow(input.feature, {
      cwd,
      fromRunId: input.fromRunId,
    });
    writeOutput(result, context, (data) => {
      const payload = data as typeof result;
      const reused = payload.nodes.filter((node) => node.decision === 'reuse').length;
      const runnable = payload.nodes.filter((node) => node.decision === 'run').length;
      return `Workflow ${payload.feature}: resume ${payload.fromRunId} (${reused} reuse, ${runnable} run)\n`;
    });
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime resume',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
