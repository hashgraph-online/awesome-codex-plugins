#!/usr/bin/env node
import * as fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { CliUserError, createCliContext, describeCommand, runMain } from '../cli/contract.mts';
import {
  describeRegisteredCommand,
  removeFirstPositional,
  runArtifactCommand,
  runDesignCommand,
  runGateCommand,
  runHooksCommand,
  runPacksCommand,
  runProjectCommand,
  runQaCommand,
  runRuntimeCommand,
  throwUnknownCommand,
  writeDescription,
} from '../cli/dispatcher.mts';
import { showRootHelp } from '../cli/help.mts';
import { rootDescription, runtimeCommandNames } from '../cli/registry.mts';
import { main as continueMain } from '../commands/continue.mts';
import { main as doctorMain } from '../commands/doctor.mts';
import { installMain } from '../commands/install/index.mts';
import { main as statusMain } from '../commands/status.mts';
import { readSkillVersion, skillRootFromImportMeta } from '../infrastructure/paths.mts';

const __filename = fileURLToPath(import.meta.url);
const SKILL_ROOT = skillRootFromImportMeta(import.meta.url);
const version = readSkillVersion(SKILL_ROOT);

export function showHelp(): void {
  showRootHelp();
}

function describeRoot() {
  return {
    ...describeCommand(rootDescription),
    version,
    commands: [
      'install',
      'uninstall',
      'path',
      'doctor',
      'status FEATURE',
      'continue FEATURE',
      'launch FEATURE',
      'attach FEATURE',
      'pause FEATURE',
      'gate FEATURE',
      'qa attack',
      'runtime COMMAND',
      'design preview',
      'project init',
      'artifact prepare',
      'packs detect',
      'hooks run',
    ],
    runtime_commands: runtimeCommandNames,
  };
}

export async function main(argv: string[] = process.argv.slice(2)): Promise<number> {
  const rootContext = createCliContext(argv, { command: 'boss', validateOptionValues: false });

  if (rootContext.values.describe && rootContext.positionals.length === 0) {
    writeDescription(describeRoot(), rootContext);
    return 0;
  }

  const cmd = rootContext.positionals[0];
  const commandArgv = removeFirstPositional(argv, cmd);

  switch (cmd) {
    case undefined:
      if (argv.includes('--version') || argv.includes('-v')) {
        console.log(version);
        return 0;
      }
      if (argv.includes('--help') || argv.includes('-h')) {
        showHelp();
        return 0;
      }
      return installMain(argv);

    case 'install':
    case 'uninstall':
    case 'path':
      if (rootContext.values.describe && rootContext.positionals.length === 1) {
        writeDescription(
          describeRegisteredCommand(`boss ${cmd}`),
          createCliContext(commandArgv, { command: `boss ${cmd}` }),
        );
        return 0;
      }
      return installMain(argv);

    case 'skills':
      // `boss skills`（管理他人 skill 的通用管理器）已移除：boss 是被安装的 skill，
      // 不再充当安装别的 skill 的工具。安装 boss 自身走 skill 市场。
      throw new CliUserError({
        code: 'command_removed',
        message: 'boss skills 命令组已移除',
        retryable: false,
        suggestion:
          '安装 boss 自身请用 skill 市场（/plugin marketplace add echoVic/boss-skill，或 npx skills add echoVic/boss-skill）；boss 不再管理其它 skill',
      });

    case 'doctor':
      if (rootContext.values.describe && rootContext.positionals.length === 1) {
        writeDescription(
          describeRegisteredCommand('boss doctor'),
          createCliContext(commandArgv, { command: 'boss doctor' }),
        );
        return 0;
      }
      return doctorMain(commandArgv, { cwd: process.cwd() });

    case 'status':
      return statusMain(commandArgv, { cwd: process.cwd() });

    case 'continue':
      return continueMain(commandArgv, { cwd: process.cwd() });

    case 'launch':
      return runRuntimeCommand(['launch', ...commandArgv]);

    case 'attach':
      return runRuntimeCommand(['attach', ...commandArgv]);

    case 'pause':
      return runRuntimeCommand(['pause', ...commandArgv]);

    case 'gate':
      return runGateCommand(commandArgv);

    case 'qa':
      return runQaCommand(commandArgv);

    case 'runtime':
      return runRuntimeCommand(commandArgv);

    case 'design':
      return runDesignCommand(commandArgv);

    case 'project':
      return runProjectCommand(commandArgv);

    case 'artifact':
      return runArtifactCommand(commandArgv);

    case 'packs':
      return runPacksCommand(commandArgv);

    case 'hooks':
      return runHooksCommand(commandArgv);

    case '--version':
    case '-v':
      console.log(version);
      return 0;

    case '--help':
    case '-h':
      showHelp();
      return 0;

    default:
      throwUnknownCommand('boss', cmd);
  }
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === fs.realpathSync(__filename)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2)), context));
}
