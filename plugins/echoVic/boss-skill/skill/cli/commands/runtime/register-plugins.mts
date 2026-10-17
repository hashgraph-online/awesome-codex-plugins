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
import {
  discoverPlugins,
  registerPlugins,
  validatePlugins,
} from '../../runtime/application/plugins.mts';
import {
  optionalInputString,
  printRuntimeHelp,
  requireInputString,
  requireOptionValue,
  toFeatureNotFoundError,
  writeActionPlan,
} from './agent-command-utils.mts';

type RegisterPluginsAction = 'list' | 'validate' | 'register' | 'help';

interface RegisterPluginsInput {
  action: RegisterPluginsAction;
  type: string;
  feature: string;
}

function printHelp(): void {
  printRuntimeHelp('register-plugins', 'boss runtime register-plugins [FEATURE] [options]');
}

function parseFlatInput(argv: string[]): RegisterPluginsInput {
  const parsed: RegisterPluginsInput = {
    action: 'list',
    type: '',
    feature: '',
  };
  let explicitAction = false;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    switch (arg) {
      case '-h':
      case '--help':
        parsed.action = 'help';
        continue;
      case '--list':
        parsed.action = 'list';
        explicitAction = true;
        continue;
      case '--validate':
        parsed.action = 'validate';
        explicitAction = true;
        continue;
      case '--type':
        parsed.type = requireOptionValue('--type', argv[index + 1]);
        index += 1;
        continue;
      case '--register':
        parsed.action = 'register';
        explicitAction = true;
        parsed.feature = requireOptionValue('--register', argv[index + 1]);
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
    if (!explicitAction && !parsed.feature) {
      parsed.action = 'register';
      parsed.feature = arg;
      continue;
    }
    throw new Error(`多余的参数: ${arg}`);
  }

  return parsed;
}

function resolveInput(argv: string[], context: CliContext): RegisterPluginsInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    const action = optionalInputString(input.action) || 'register';
    return {
      action: action as RegisterPluginsAction,
      type: optionalInputString(input.type) || '',
      feature:
        action === 'register'
          ? requireInputString(input.feature, 'feature')
          : optionalInputString(input.feature) || '',
    };
  }
  return parseFlatInput(argv);
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss runtime register-plugins' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(runtimeCommandDescriptions['register-plugins']!),
      context,
      () => `${JSON.stringify(runtimeCommandDescriptions['register-plugins'], null, 2)}\n`,
    );
    return 0;
  }

  const input = resolveInput(argv, context);
  if (input.action === 'help') {
    printHelp();
    return 0;
  }

  if (input.action === 'list') {
    const result = discoverPlugins({ cwd, type: input.type, strict: false });
    writeOutput({ plugins: result.plugins, errors: result.errors }, context, () =>
      result.plugins.length === 0
        ? '未发现已启用插件\n'
        : `${result.plugins.map((plugin) => `  ${plugin.name}@${plugin.version} (${plugin.type})`).join('\n')}\n共发现 ${result.plugins.length} 个插件\n`,
    );
    if (result.errors.length > 0 && !context.useJson) {
      process.stderr.write(`${result.errors.join('\n')}\n`);
    }
    return result.errors.length > 0 ? 1 : 0;
  }

  if (input.action === 'validate') {
    const result = validatePlugins({ cwd, type: input.type });
    writeOutput(
      { valid: result.valid, plugins: result.plugins, errors: result.errors },
      context,
      () =>
        result.valid
          ? `${result.plugins.map((plugin) => `${plugin.name}@${plugin.version} (${plugin.type}) - valid`).join('\n')}\n所有插件验证通过\n`
          : `${result.errors.join('\n')}\n`,
    );
    return result.valid ? 0 : 1;
  }

  if (input.action === 'register') {
    if (context.values.dryRun) {
      const result = discoverPlugins({ cwd, type: input.type, strict: false });
      writeActionPlan(
        [
          {
            type: 'register_plugins',
            feature: input.feature,
            plugin_count: result.plugins.length,
            plugin_names: result.plugins.map((plugin) => plugin.name),
          },
        ],
        context,
        'medium',
      );
      return result.errors.length > 0 ? 1 : 0;
    }

    try {
      const result = registerPlugins(input.feature, { cwd, type: input.type });
      const executionPath = `.boss/${input.feature}/.meta/execution.json`;
      writeOutput(
        {
          feature: input.feature,
          plugin_count: result.plugins.length,
          plugin_names: result.plugins.map((plugin) => plugin.name),
          executionPath,
        },
        context,
        () =>
          `已追加 ${result.plugins.length} 个插件注册事件，并物化 read model: ${path.join(cwd, executionPath)}\n`,
      );
      return 0;
    } catch (err) {
      throw toFeatureNotFoundError(err, input.feature);
    }
  }

  throw new Error(`不支持的 action: ${input.action}`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss runtime register-plugins',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
