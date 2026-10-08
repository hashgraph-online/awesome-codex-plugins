#!/usr/bin/env node
import { createHash } from 'node:crypto';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  assertConfirmed,
  CliUserError,
  createCliContext,
  describeCommand,
  renderHelp,
  runMain,
  writeOutput,
} from '../../cli/contract.mts';
import { commandDescriptions } from '../../cli/registry.mts';
import { copyDirectory, readJsonFile, writeJsonFile } from '../../infrastructure/fs.mts';
import { readSkillVersion, skillRootFromImportMeta } from '../../infrastructure/paths.mts';

export const SKILL_ROOT = skillRootFromImportMeta(import.meta.url);
export const PLUGIN_ROOT = path.dirname(SKILL_ROOT);
export const VERSION = readSkillVersion(SKILL_ROOT);
export const REPO_SLUG = 'echoVic/boss-skill';
const CODEX_HOOKS_SOURCE = path.join(SKILL_ROOT, 'hooks', 'codex', 'hooks.json');
const CODEX_HOOKS_STATE = '.boss-hooks-state.json';
const __filename = fileURLToPath(import.meta.url);
const HOME = os.homedir();

export interface Agent {
  name: string;
  detect: () => boolean;
  dest: () => string;
  method: 'copy' | 'codex-copy' | 'plugin';
}

type InstallAction = {
  type: 'install_skill' | 'register_plugin';
  agent: string;
  path: string;
};

type UninstallAction = {
  type: 'remove_skill' | 'skip_missing';
  agent: string;
  path: string;
};

type HookHandler = {
  type?: string;
  command?: string;
  [key: string]: unknown;
};

type HookEntry = {
  id?: string;
  hooks?: HookHandler[];
  [key: string]: unknown;
};

type HooksConfig = {
  hooks?: Record<string, HookEntry[]>;
};

type CodexHooksState = {
  version: string;
  installMode: 'hooks-json';
  hookIds: string[];
  manifestChecksum?: string;
};

export const LEGACY_BOSS_HOOK_IDS = [
  'session:start',
  'session:resume',
  'pre:write:artifact-guard',
  'pre:bash:dangerous-cmd-guard',
  'post:write:artifact-track',
  'post:bash:context',
  'stop:pipeline-guard',
  'subagent:start',
  'subagent:stop',
  'post:stage:wip-checkpoint',
  'notification:log',
  'session:end',
];

const CODEX_MATCHER_ALIASES: Record<string, string[]> = {
  apply_patch: ['apply_patch', 'Edit', 'Write', 'Edit|Write'],
  Edit: ['apply_patch', 'Edit', 'Write', 'Edit|Write'],
  Write: ['apply_patch', 'Edit', 'Write', 'Edit|Write'],
  'Edit|Write': ['apply_patch', 'Edit', 'Write', 'Edit|Write'],
};

const METADATA: Record<string, string> = {
  OpenClaw: `metadata:
  openclaw:
    emoji: "👔"
    primaryEnv: BOSS_HOOK_PROFILE
    requires:
      bins:
        - node
        - bash`,

  Codex: `metadata:
  codex:
    emoji: "👔"
    requires:
      bins:
        - node
        - bash`,

  Antigravity: `metadata:
  antigravity:
    emoji: "👔"
    requires:
      bins:
        - node
        - bash`,

  Hermes: `metadata:
  hermes:
    emoji: "👔"
    requires:
      bins:
        - node
        - bash`,
};

export const AGENTS: Agent[] = [
  {
    name: 'OpenClaw',
    detect: () => fs.existsSync(path.join(HOME, '.openclaw')),
    dest: () => path.join(HOME, '.openclaw', 'skills', 'boss'),
    method: 'copy',
  },
  {
    name: 'Codex',
    detect: () => fs.existsSync(path.join(HOME, '.codex')),
    dest: () => path.join(HOME, '.codex', 'skills', 'boss'),
    method: 'codex-copy',
  },
  {
    name: 'Antigravity',
    detect: () => fs.existsSync(path.join(HOME, '.gemini', 'antigravity')),
    dest: () => path.join(HOME, '.gemini', 'antigravity', 'skills', 'boss'),
    method: 'copy',
  },
  {
    name: 'Hermes',
    detect: () => fs.existsSync(path.join(HOME, '.hermes')),
    dest: () => path.join(HOME, '.hermes', 'skills', 'boss'),
    method: 'copy',
  },
  {
    name: 'Claude Code',
    detect: () => true,
    dest: () => PLUGIN_ROOT,
    method: 'plugin',
  },
];

const USAGE = `
Boss Skill v${VERSION}
BMAD Harness Engineer — pluggable pipeline skill for coding agents.
Compatible with Claude Code, OpenClaw, Codex, Antigravity & Hermes.

Marketplace install (recommended, no npm):
  Claude Code:  /plugin marketplace add ${REPO_SLUG}
                /plugin install boss@boss-skill
  Codex:        codex plugin marketplace add ${REPO_SLUG}
  Any agent:    npx skills add ${REPO_SLUG}

Usage:
  boss install              Copy skill + merge Codex hooks into detected agents
  boss install --dry-run    Preview install actions without writing
  boss uninstall            Remove boss from all detected agents
  boss path                 Print the skill root directory
  boss --version            Print version
  boss --help               Show this help

Auto-detect logic (checks all, installs to every detected agent):
  ~/.openclaw/                →  ~/.openclaw/skills/boss/     (copy + inject metadata)
  ~/.codex/                   →  ~/.codex/skills/boss/        (copy + inject metadata + hooks merge)
  ~/.gemini/antigravity/      →  ~/.gemini/.../skills/boss/   (copy + inject metadata)
  ~/.hermes/                  →  ~/.hermes/skills/boss/       (copy + inject metadata)
  Claude Code                 →  plugin marketplace (see above)
`;

const installDescription = commandDescriptions['boss install']!;
const uninstallDescription = commandDescriptions['boss uninstall']!;
const pathDescription = commandDescriptions['boss path']!;
const INSTALL_HELP = renderHelp(installDescription, 'boss install [options]');

function injectMetadata(content: string, agentName: string): string {
  const meta = METADATA[agentName];
  if (!meta) return content;
  return content.replace(/^(---\n[\s\S]*?)(^---)/m, `$1${meta}\n$2`);
}

function copyInstall(agent: Agent, dryRun: boolean, silent = false): void {
  const dest = agent.dest();

  if (dryRun) {
    if (!silent) console.log(`  [dry-run] ${agent.name}: would install to ${dest}`);
    return;
  }

  if (fs.existsSync(dest)) {
    fs.rmSync(dest, { recursive: true });
  }

  copyDirectory(SKILL_ROOT, dest);

  const skillMd = path.join(dest, 'SKILL.md');
  if (fs.existsSync(skillMd)) {
    const content = fs.readFileSync(skillMd, 'utf8');
    fs.writeFileSync(skillMd, injectMetadata(content, agent.name));
  }

  if (!silent) console.log(`  ✅ ${agent.name}: ${dest} (copied + metadata injected)`);
}

function readHooksConfig(filePath: string): HooksConfig {
  if (!fs.existsSync(filePath)) {
    return { hooks: {} };
  }
  return readJsonFile<HooksConfig>(filePath);
}

function getBossHookIds(hooksConfig: HooksConfig): string[] {
  const ids: string[] = [];
  for (const entries of Object.values(hooksConfig.hooks || {})) {
    for (const entry of entries || []) {
      if (typeof entry.id === 'string' && entry.id.length > 0) {
        ids.push(entry.id);
      }
    }
  }
  return ids;
}

function mergeHooksConfig(existingConfig: HooksConfig, bossConfig: HooksConfig): HooksConfig {
  const result: HooksConfig = { hooks: {} };
  const allEventNames = new Set([
    ...Object.keys(existingConfig.hooks || {}),
    ...Object.keys(bossConfig.hooks || {}),
  ]);
  const bossHookIds = new Set(getBossHookIds(bossConfig));

  for (const eventName of allEventNames) {
    const existingEntries = (existingConfig.hooks || {})[eventName] || [];
    const bossEntries = (bossConfig.hooks || {})[eventName] || [];
    const preservedExisting = existingEntries.filter(
      (entry) => !entry.id || !bossHookIds.has(String(entry.id)),
    );
    const mergedEntries = [...preservedExisting, ...bossEntries];
    if (mergedEntries.length > 0) {
      result.hooks![eventName] = mergedEntries;
    }
  }

  return result;
}

function removeBossHooks(existingConfig: HooksConfig, hookIds: string[]): HooksConfig {
  const result: HooksConfig = { hooks: {} };
  const blockedIds = new Set([...hookIds, ...LEGACY_BOSS_HOOK_IDS]);

  for (const [eventName, entries] of Object.entries(existingConfig.hooks || {})) {
    const preservedEntries = (entries || []).filter((entry) => {
      if (!entry.id) return true;
      const id = String(entry.id);
      return !blockedIds.has(id);
    });
    if (preservedEntries.length > 0) {
      result.hooks![eventName] = preservedEntries;
    }
  }

  return result;
}

function fileSha256(filePath: string): string {
  return 'sha256:' + createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function findDuplicateMatcherWarnings(
  existingConfig: HooksConfig,
  bossConfig: HooksConfig,
): string[] {
  const warnings: string[] = [];
  for (const [eventName, bossEntries] of Object.entries(bossConfig.hooks || {})) {
    const existingEntries = existingConfig.hooks?.[eventName] || [];
    for (const bossEntry of bossEntries || []) {
      if (typeof bossEntry.matcher !== 'string') continue;
      const equivalentMatchers = new Set(
        CODEX_MATCHER_ALIASES[bossEntry.matcher] || [bossEntry.matcher],
      );
      const duplicate = existingEntries.find((entry) => {
        return (
          !entry.id && typeof entry.matcher === 'string' && equivalentMatchers.has(entry.matcher)
        );
      });
      if (duplicate) {
        warnings.push(`${eventName}/${bossEntry.matcher}`);
      }
    }
  }
  return warnings;
}

/**
 * Codex 插件 hooks 用 ${PLUGIN_ROOT} 指向插件根（仓库布局下 skill 位于 <plugin>/skill）。
 * 复制安装没有插件根，合并进 ~/.codex/hooks.json 时把占位符物化为实际 skill 目录，
 * 这样 hooks 里引用的 node <skill>/cli/bin/boss.mts 不依赖 PATH 上的 boss 二进制。
 */
function materializeHookRoots(config: HooksConfig, skillDest: string): HooksConfig {
  const substitute = (command: string): string =>
    command
      // biome-ignore lint/suspicious/noTemplateCurlyInString: 字面占位符（运行时替换），不是模板插值
      .replaceAll('${PLUGIN_ROOT}/skill', skillDest)
      // biome-ignore lint/suspicious/noTemplateCurlyInString: 字面占位符（运行时替换），不是模板插值
      .replaceAll('${CLAUDE_PLUGIN_ROOT}/skill', skillDest)
      // biome-ignore lint/suspicious/noTemplateCurlyInString: 字面占位符（运行时替换），不是模板插值
      .replaceAll('${PLUGIN_ROOT}', skillDest)
      // biome-ignore lint/suspicious/noTemplateCurlyInString: 字面占位符（运行时替换），不是模板插值
      .replaceAll('${CLAUDE_PLUGIN_ROOT}', skillDest);

  const result: HooksConfig = { hooks: {} };
  for (const [eventName, entries] of Object.entries(config.hooks || {})) {
    result.hooks![eventName] = (entries || []).map((entry) => {
      const handlers = Array.isArray(entry.hooks) ? entry.hooks : undefined;
      if (!handlers) return entry;
      return {
        ...entry,
        hooks: handlers.map((handler) =>
          typeof handler.command === 'string'
            ? { ...handler, command: substitute(handler.command) }
            : handler,
        ),
      };
    });
  }
  return result;
}

function installCodexHooks(dryRun: boolean, silent = false): void {
  const codexHome = path.join(HOME, '.codex');
  const hooksPath = path.join(codexHome, 'hooks.json');
  const statePath = path.join(codexHome, CODEX_HOOKS_STATE);
  const skillDest = path.join(codexHome, 'skills', 'boss');

  if (dryRun) {
    if (!silent) console.log(`  [dry-run] Codex: would merge hooks into ${hooksPath}`);
    return;
  }

  const existingConfig = readHooksConfig(hooksPath);
  const sourceConfig = readJsonFile<HooksConfig>(CODEX_HOOKS_SOURCE);
  const bossConfig = materializeHookRoots(sourceConfig, skillDest);
  const currentChecksum = fileSha256(CODEX_HOOKS_SOURCE);
  const previousState = fs.existsSync(statePath) ? readJsonFile<CodexHooksState>(statePath) : null;
  const duplicateWarnings = findDuplicateMatcherWarnings(existingConfig, bossConfig);
  const mergedConfig = mergeHooksConfig(existingConfig, bossConfig);
  writeJsonFile(hooksPath, mergedConfig);
  writeJsonFile(statePath, {
    version: VERSION,
    installMode: 'hooks-json',
    hookIds: getBossHookIds(sourceConfig),
    manifestChecksum: currentChecksum,
  } satisfies CodexHooksState);

  if (!silent) console.log(`  ✅ Codex: merged hooks into ${hooksPath}`);
  if (
    !silent &&
    previousState?.manifestChecksum &&
    previousState.manifestChecksum !== currentChecksum
  ) {
    console.log(
      '  ℹ️  Codex: hook manifest changed since last install; refreshed Boss-managed hooks.',
    );
  }
  if (!silent && duplicateWarnings.length > 0) {
    console.log(
      `  ⚠️  Codex: existing hook(s) without id share matcher(s): ${duplicateWarnings.join(', ')}`,
    );
  }
}

function uninstallCodexHooks(silent = false): void {
  const codexHome = path.join(HOME, '.codex');
  const hooksPath = path.join(codexHome, 'hooks.json');
  const statePath = path.join(codexHome, CODEX_HOOKS_STATE);

  if (!fs.existsSync(statePath)) {
    return;
  }

  const state = readJsonFile<CodexHooksState>(statePath);
  const existingConfig = readHooksConfig(hooksPath);
  const cleanedConfig = removeBossHooks(existingConfig, state.hookIds);
  writeJsonFile(hooksPath, cleanedConfig);
  fs.rmSync(statePath, { force: true });

  if (!silent) console.log(`  ✅ Codex: removed Boss-managed hooks from ${hooksPath}`);
}

function codexInstall(agent: Agent, dryRun: boolean, silent = false): void {
  copyInstall(agent, dryRun, silent);
  installCodexHooks(dryRun, silent);
}

function pluginInstall(dryRun: boolean, silent = false): void {
  const pluginRootReady = fs.existsSync(path.join(PLUGIN_ROOT, '.claude-plugin', 'plugin.json'));

  if (dryRun) {
    if (!silent)
      console.log('  [dry-run] Claude Code: would print plugin marketplace install steps');
    return;
  }

  if (silent) return;
  console.log('  ✅ Claude Code: 用插件市场安装（skill 随插件分发，无需 npm）：');
  console.log(`     /plugin marketplace add ${REPO_SLUG}`);
  console.log('     /plugin install boss@boss-skill');
  if (pluginRootReady) {
    console.log(`     本地开发可用: claude --plugin-dir "${PLUGIN_ROOT}"`);
  }
}

export function buildInstallPlan(): InstallAction[] {
  return AGENTS.filter((agent) => agent.detect()).map((agent) => ({
    type: agent.method === 'plugin' ? 'register_plugin' : 'install_skill',
    agent: agent.name,
    path: agent.dest(),
  }));
}

async function runInteractiveInstall(): Promise<number> {
  // 交互向导依赖 @clack/prompts（仓库 devDependency 链）。marketplace 安装副本没有
  // node_modules，动态导入失败时退回非交互安装，保证 boss install 始终可用。
  let runInstallWizard: typeof import('../../skills/self-install-wizard.mts').runInstallWizard;
  try {
    ({ runInstallWizard } = await import('../../skills/self-install-wizard.mts'));
  } catch {
    console.log('ℹ️  交互向导不可用（未安装 @clack/prompts），改用非交互安装。\n');
    autoInstall(false);
    return 0;
  }
  return runInstallWizard({
    version: VERSION,
    agents: AGENTS.map((agent) => {
      const dest = agent.dest();
      const sideEffects: string[] = [];
      if (agent.method === 'codex-copy') {
        sideEffects.push(`merge Boss hooks into ${path.join(HOME, '.codex', 'hooks.json')}`);
      }
      if (agent.method === 'plugin') {
        sideEffects.push('no files copied — install via plugin marketplace');
      }
      return {
        name: agent.name,
        detected: agent.detect(),
        dest,
        method: agent.method,
        sideEffects,
        postInstallNote:
          agent.method === 'plugin'
            ? [`/plugin marketplace add ${REPO_SLUG}`, '/plugin install boss@boss-skill']
            : undefined,
        install: () => {
          if (agent.method === 'copy') {
            copyInstall(agent, false, true);
          } else if (agent.method === 'codex-copy') {
            copyInstall(agent, false, true);
            installCodexHooks(false, true);
          }
        },
      };
    }),
  });
}

function shouldRunWizard(context: ReturnType<typeof createCliContext>): boolean {
  return (
    context.stdinIsTTY &&
    context.stdoutIsTTY &&
    !context.useJson &&
    !context.values.yes &&
    !context.values.dryRun &&
    !context.values.describe
  );
}

export function buildUninstallPlan(): UninstallAction[] {
  return AGENTS.filter((agent) => agent.method !== 'plugin' && agent.detect()).map((agent) => {
    const dest = agent.dest();
    return {
      type: fs.existsSync(dest) ? 'remove_skill' : 'skip_missing',
      agent: agent.name,
      path: dest,
    };
  });
}

function autoInstall(dryRun: boolean, silent = false): void {
  if (!silent) console.log(`Boss Skill v${VERSION}${dryRun ? ' (dry-run)' : ''}\n`);

  const detected = AGENTS.filter((a) => a.detect());
  if (!silent) console.log(`Detected ${detected.length} agent(s):\n`);

  for (const agent of detected) {
    if (agent.method === 'copy') {
      copyInstall(agent, dryRun, silent);
    } else if (agent.method === 'codex-copy') {
      codexInstall(agent, dryRun, silent);
    } else {
      pluginInstall(dryRun, silent);
    }
  }

  if (silent) return;
  if (dryRun) {
    console.log('\nDry-run complete. No files were modified.');
  } else {
    console.log('\nDone! Restart your agent or start a new session to pick up boss-skill.');
  }
}

function uninstall(silent = false): void {
  if (!silent) console.log(`Boss Skill v${VERSION} — uninstall\n`);

  const copyAgents = AGENTS.filter((a) => a.method !== 'plugin' && a.detect());

  for (const agent of copyAgents) {
    const dest = agent.dest();
    if (fs.existsSync(dest)) {
      fs.rmSync(dest, { recursive: true });
      if (!silent) console.log(`  ✅ ${agent.name}: removed ${dest}`);
    } else {
      if (!silent) console.log(`  ⏭️  ${agent.name}: not installed, skipped`);
    }

    if (agent.name === 'Codex') {
      uninstallCodexHooks(silent);
    }
  }

  if (silent) return;
  console.log('  ℹ️  Claude Code: 插件由市场管理 — 卸载请用 /plugin uninstall boss@boss-skill。');

  console.log('\nUninstall complete.');
}

export function showHelp(): void {
  console.log(`${USAGE}\n${INSTALL_HELP}`);
}

export function installMain(argv: string[] = process.argv.slice(2)): number | Promise<number> {
  const forceHuman = argv.includes('--human');
  const normalizedArgv = argv.filter((arg) => arg !== '--human');
  const context = createCliContext(normalizedArgv, { command: 'boss install' });
  if (forceHuman) {
    context.useJson = false;
  }
  const cmd = normalizedArgv[0];
  const dryRun = context.values.dryRun;

  switch (cmd) {
    case 'install':
    case undefined:
      if (context.values.describe) {
        writeOutput(
          describeCommand(installDescription),
          context,
          (data) => `${JSON.stringify(data, null, 2)}\n`,
        );
        return 0;
      }
      if (dryRun && context.useJson) {
        writeOutput(
          { actions: buildInstallPlan(), risk_tier: 'medium', requires_approval: false },
          context,
          () => '',
        );
        return 0;
      }
      if (context.useJson) {
        const actions = buildInstallPlan();
        autoInstall(false, true);
        writeOutput(
          { actions, risk_tier: 'medium', requires_approval: false, status: 'installed' },
          context,
          () => '',
        );
        return 0;
      }
      if (shouldRunWizard(context)) {
        return runInteractiveInstall();
      }
      autoInstall(dryRun);
      return 0;

    case 'uninstall':
      if (context.values.describe) {
        writeOutput(
          describeCommand(uninstallDescription),
          context,
          (data) => `${JSON.stringify(data, null, 2)}\n`,
        );
        return 0;
      }
      if (dryRun && context.useJson) {
        writeOutput(
          { actions: buildUninstallPlan(), risk_tier: 'high', requires_approval: true },
          context,
          () => '',
        );
        return 0;
      }
      assertConfirmed(context, 'uninstall');
      if (context.useJson) {
        const actions = buildUninstallPlan();
        uninstall(true);
        writeOutput(
          { actions, risk_tier: 'high', requires_approval: true, status: 'uninstalled' },
          context,
          () => '',
        );
        return 0;
      }
      uninstall();
      return 0;

    case 'path':
      if (context.values.describe) {
        writeOutput(
          describeCommand(pathDescription),
          context,
          (data) => `${JSON.stringify(data, null, 2)}\n`,
        );
        return 0;
      }
      if (context.values.json) {
        writeOutput({ path: SKILL_ROOT }, context, () => `${SKILL_ROOT}\n`);
      } else {
        process.stdout.write(`${SKILL_ROOT}\n`);
      }
      return 0;

    case '--version':
    case '-v':
      console.log(VERSION);
      return 0;

    case '--help':
    case '-h':
      console.log(USAGE);
      return 0;

    default:
      throw new CliUserError({
        code: 'unknown_command',
        message: `Unknown command: ${cmd}`,
        input: { command: cmd },
        retryable: false,
        suggestion: 'Run boss-skill --help to list available commands',
      });
  }
}

export const main = installMain;

const entrypoint = process.argv[1];
if (entrypoint && fs.realpathSync(entrypoint) === fs.realpathSync(__filename)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss install',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => installMain(), context));
}
