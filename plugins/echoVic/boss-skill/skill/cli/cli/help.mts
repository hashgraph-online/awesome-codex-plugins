import { renderHelp } from './contract.mts';
import {
  artifactDescription,
  designDescription,
  gateDescription,
  hooksDescription,
  packsDescription,
  projectDescription,
  qaDescription,
  rootDescription,
  runtimeCommandNames,
  runtimeDescription,
} from './registry.mts';

/**
 * 根 help 是新用户敲下的第一条命令，必须先回答「我下一步做什么」。
 *
 * Boss 的产品入口是 coding agent 里的 `/boss` 系列命令，这个 CLI 是它的运行时。
 * 因此先给上手指引，再列命令（每条带描述），把 --json / --fields 这些
 * 给调用方 agent 用的全局选项放到最后。
 */
const ROOT_COMMANDS: Array<[string, string]> = [
  ['install', 'Install the Boss skill into your coding agents'],
  ['uninstall', 'Remove the Boss skill from your coding agents'],
  ['path', 'Print where the Boss skill is installed'],
  ['doctor', 'Diagnose install, runtime and per-feature event streams'],
  ['status FEATURE', 'Show pipeline state and the next checkpoint'],
  ['continue FEATURE', 'Advance a pipeline to the next safe checkpoint'],
  ['gate FEATURE', 'Run a quality gate on a feature'],
  ['gate final FEATURE', 'Run the release gate (required artifacts, QA findings, gates)'],
  ['qa attack FEATURE', 'Generate structured QA findings'],
  ['runtime COMMAND', 'Low-level runtime commands used by the skill'],
  ['design preview', 'Preview ui-design.json in a local browser'],
  ['project init', 'Create a .boss/<feature>/ workspace'],
  ['artifact prepare', 'Prepare an artifact from its template'],
  ['packs detect', 'Show which pipeline pack matches this project'],
  ['hooks run', 'Run a Boss hook (invoked by your agent, not by hand)'],
];

const GETTING_STARTED = [
  'Boss is a skill for your coding agent. This CLI is its runtime.',
  '',
  'Getting started — type one of these in Claude Code / Codex / OpenClaw:',
  '  /boss:review    review existing code or a PR (read-only, good first try)',
  '  /boss:qa        run tests and quality gates on an existing project',
  '  /boss           the full pipeline, from requirement to delivery',
  '',
  'Not installed yet?  npx skills add echoVic/boss-skill',
  '',
];

function commandLines(): string[] {
  const width = Math.max(...ROOT_COMMANDS.map(([name]) => name.length));
  return ROOT_COMMANDS.map(([name, summary]) => `  ${name.padEnd(width)}  ${summary}`);
}

export const ROOT_USAGE = [
  'Usage: boss COMMAND [options]',
  '',
  ...GETTING_STARTED,
  'Commands:',
  ...commandLines(),
  '',
  'Compatibility:',
  '  boss-skill install',
  '',
  renderHelp(rootDescription, 'boss COMMAND [options]').split('\n').slice(2).join('\n'),
].join('\n');

export const RUNTIME_USAGE = [
  renderHelp(runtimeDescription, 'boss runtime COMMAND [args...]'),
  'Commands:',
  ...runtimeCommandNames.map((name) => `  ${name}`),
  '',
].join('\n');

export const GATE_USAGE = [
  renderHelp(gateDescription, 'boss gate <feature> [--gate <gateName>]'),
  'Commands:',
  '  final',
  '',
].join('\n');

export const QA_USAGE = [
  renderHelp(qaDescription, 'boss qa attack <feature>'),
  'Commands:',
  '  attack',
  '',
].join('\n');

export const DESIGN_USAGE = [
  renderHelp(designDescription, 'boss design preview <feature> [--no-open] [--port <port>]'),
  'Commands:',
  '  preview',
  '',
].join('\n');

export const PROJECT_USAGE = [
  renderHelp(projectDescription, 'boss project init <feature-name> [--template] [--force]'),
  'Commands:',
  '  init',
  '',
].join('\n');

export const ARTIFACT_USAGE = [
  renderHelp(
    artifactDescription,
    'boss artifact prepare <feature-name> <artifact-name> [template-name]',
  ),
  'Commands:',
  '  prepare',
  '',
].join('\n');

export const PACKS_USAGE = [
  renderHelp(packsDescription, 'boss packs detect [project-dir]'),
  'Commands:',
  '  detect',
  '',
].join('\n');

export const HOOKS_USAGE = [
  renderHelp(hooksDescription, 'boss hooks run <hook-id> <script-relative-path> [profiles-csv]'),
  'Commands:',
  '  run',
  '',
].join('\n');

export function showRootHelp(): void {
  process.stdout.write(ROOT_USAGE);
}

export function showRuntimeHelp(): void {
  process.stdout.write(RUNTIME_USAGE);
}
