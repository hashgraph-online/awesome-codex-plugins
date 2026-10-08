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
import { updateAgent } from '../../runtime/application/pipeline.mts';
import {
  optionalInputString,
  printRuntimeHelp,
  requireInputString,
  requireOptionValue,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

interface UpdateAgentInput {
  feature: string;
  stage: string;
  agent: string;
  status: string;
  reason?: string;
  prompt?: string;
  promptFingerprint?: string;
  dependencyArtifacts: string[];
  opts?: Record<string, unknown>;
}

function showHelp(): void {
  printRuntimeHelp(
    'update-agent',
    'boss runtime update-agent FEATURE STAGE AGENT STATUS [options]',
  );
}

function parseFlatInput(argv: string[]): UpdateAgentInput {
  let feature = '';
  let stage = '';
  let agent = '';
  let status = '';
  let reason: string | undefined;
  let prompt: string | undefined;
  let promptFingerprint: string | undefined;
  let dependencyArtifacts: string[] = [];
  let opts: Record<string, unknown> | undefined;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === '--reason') {
      reason = requireOptionValue('--reason', argv[index + 1]);
      index += 1;
      continue;
    }
    if (arg === '--prompt') {
      prompt = requireOptionValue('--prompt', argv[index + 1]);
      index += 1;
      continue;
    }
    if (arg === '--prompt-fingerprint') {
      promptFingerprint = requireOptionValue('--prompt-fingerprint', argv[index + 1]);
      index += 1;
      continue;
    }
    if (arg === '--depends-on') {
      dependencyArtifacts = requireOptionValue('--depends-on', argv[index + 1])
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
      index += 1;
      continue;
    }
    if (arg === '--opts') {
      const parsed = JSON.parse(requireOptionValue('--opts', argv[index + 1])) as unknown;
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        throw new Error('--opts 必须是 JSON 对象');
      }
      opts = parsed as Record<string, unknown>;
      index += 1;
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
    if (!feature) feature = arg;
    else if (!stage) stage = arg;
    else if (!agent) agent = arg;
    else if (!status) status = arg;
    else throw new Error(`多余的参数: ${arg}`);
  }

  return {
    feature: requireInputString(feature, 'feature'),
    stage: requireInputString(stage, 'stage'),
    agent: requireInputString(agent, 'agent'),
    status: requireInputString(status, 'status'),
    reason,
    prompt,
    promptFingerprint,
    dependencyArtifacts,
    opts,
  };
}

function resolveInput(argv: string[], context: CliContext): UpdateAgentInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      stage: requireInputString(input.stage, 'stage'),
      agent: requireInputString(input.agent, 'agent'),
      status: requireInputString(input.status, 'status'),
      reason: optionalInputString(input.reason),
      prompt: optionalInputString(input.prompt),
      promptFingerprint: optionalInputString(input.promptFingerprint),
      dependencyArtifacts: Array.isArray(input.dependencyArtifacts)
        ? input.dependencyArtifacts.filter(
            (item): item is string => typeof item === 'string' && item.length > 0,
          )
        : [],
      opts:
        input.opts && typeof input.opts === 'object' && !Array.isArray(input.opts)
          ? (input.opts as Record<string, unknown>)
          : undefined,
    };
  }
  return parseFlatInput(argv);
}

function actionFor(input: UpdateAgentInput) {
  return {
    type: 'update_agent',
    feature: input.feature,
    stage: Number(input.stage),
    agent: input.agent,
    target_status: input.status,
    reason: input.reason,
    dependency_artifacts: input.dependencyArtifacts,
  };
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime update-agent' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['update-agent']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['update-agent'], null, 2)}\n`,
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
    updateAgent(input.feature, input.stage, input.agent, input.status, {
      reason: input.reason || '',
      cwd,
      prompt: input.prompt,
      promptFingerprint: input.promptFingerprint,
      dependencyArtifacts: input.dependencyArtifacts,
      opts: input.opts || {},
    });
    writeOutput(
      {
        feature: input.feature,
        stage: Number(input.stage),
        agent: input.agent,
        status: input.status,
      },
      context,
      () => `Agent ${input.agent} (阶段 ${input.stage}): -> ${input.status}\n`,
    );
    return 0;
  } catch (err) {
    throw toFeatureNotFoundError(err, input.feature);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime update-agent',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
