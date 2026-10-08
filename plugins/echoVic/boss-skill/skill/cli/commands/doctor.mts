#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import { createCliContext, describeCommand, runMain, writeOutput } from '../cli/contract.mts';
import { commandDescriptions } from '../cli/registry.mts';
import { readJsonlTolerant } from '../infrastructure/fs.mts';
import { readSkillVersion } from '../infrastructure/paths.mts';
import { findFailedGates } from '../runtime/application/final-gate.mts';
import { AGENTS, PLUGIN_ROOT, SKILL_ROOT, VERSION } from './install/index.mts';

type CheckStatus = 'ok' | 'warn' | 'error';

interface DoctorCheck {
  name: string;
  status: CheckStatus;
  detail: string;
}

/** boss 装到哪些 agent、版本是否与当前包一致。 */
function checkInstalls(): DoctorCheck[] {
  const checks: DoctorCheck[] = [];
  for (const agent of AGENTS) {
    if (agent.method === 'plugin') {
      checks.push({
        name: `install:${agent.name}`,
        status: 'ok',
        detail: `plugin 模式，根目录 ${agent.dest()}`,
      });
      continue;
    }
    const dest = agent.dest();
    const detected = agent.detect();
    if (!fs.existsSync(dest)) {
      checks.push({
        name: `install:${agent.name}`,
        status: detected ? 'warn' : 'ok',
        detail: detected
          ? `已检测到 ${agent.name} 但未安装 boss（用 skill 市场安装，或运行 boss install）`
          : `未检测到 ${agent.name}，跳过`,
      });
      continue;
    }
    const installedVersion = fs.existsSync(path.join(dest, 'SKILL.md'))
      ? readSkillVersion(dest)
      : undefined;
    const versionMatch = installedVersion === VERSION;
    checks.push({
      name: `install:${agent.name}`,
      status: versionMatch ? 'ok' : 'warn',
      detail: versionMatch
        ? `已安装 v${installedVersion}（与当前 skill 一致）`
        : `已安装 v${installedVersion ?? '未知'}，当前 skill 为 v${VERSION}（建议重装）`,
    });
  }
  return checks;
}

/**
 * 网络边界自检：把 network-boundary 源码守卫的清单在运行时可视化。
 * 本函数只报告 boss 自身管辖范围（依赖树里没有 http/fetch 客户端、preview server 只绑
 * 127.0.0.1、已移除 knowledge 外挂环境变量），不能证明宿主 agent 不出网。
 */
function checkNetworkBoundary(): DoctorCheck[] {
  const checks: DoctorCheck[] = [];

  // 1. 声明 boss 自身范围（避免用户误读为「宿主也零出网」）
  checks.push({
    name: 'network:scope',
    status: 'ok',
    detail: 'boss 自身零出网；宿主 agent 的出网行为不在本自检范围内',
  });

  // 2. 已移除的 knowledge 外挂配置：任一环境变量仍被设置，就提示用户可以清理
  const knowledgeEnvs = [
    'BOSS_KNOWLEDGE_API_KEY',
    'BOSS_KNOWLEDGE_BASE_URL',
    'BOSS_KNOWLEDGE_MODEL',
  ];
  const stillSet = knowledgeEnvs.filter((name) => process.env[name] !== undefined);
  checks.push({
    name: 'network:legacy-knowledge-env',
    status: stillSet.length > 0 ? 'warn' : 'ok',
    detail:
      stillSet.length > 0
        ? `检测到已废弃的 knowledge 环境变量：${stillSet.join(', ')}（boss 4.0 起不再读取，可从环境中删除）`
        : '未检测到已废弃的 knowledge 环境变量',
  });

  // 3. 源码级守卫存在性：network-boundary 测试与 PRIVACY.md 都在。
  //    插件安装保留完整仓库（plugin root = 仓库根），复制安装只有 skill/ 目录；
  //    两处都查，缺失时如实报 warn。
  const guards = [
    { rel: 'test/runtime/network-boundary.test.ts', name: 'network-boundary test' },
    { rel: 'PRIVACY.md', name: 'PRIVACY.md' },
  ];
  for (const guard of guards) {
    const candidates = [path.join(PLUGIN_ROOT, guard.rel), path.join(SKILL_ROOT, guard.rel)];
    const found = candidates.find((candidate) => fs.existsSync(candidate));
    checks.push({
      name: `network:guard:${guard.name}`,
      status: found ? 'ok' : 'warn',
      detail: found
        ? `${guard.rel} 存在（CI 会在源码引入出站客户端时变红）`
        : `${guard.rel} 未随安装分发，无法从本地文件复核；可到 GitHub 查看源码`,
    });
  }

  return checks;
}

/** 运行环境边界：Node 版本、平台、git 是否可用（WIP checkpoint 依赖 git，缺失则静默降级）。 */
function checkEnvironment(): DoctorCheck[] {
  const checks: DoctorCheck[] = [];

  const [majorRaw, minorRaw] = process.versions.node.split('.');
  const major = Number(majorRaw);
  const minor = Number(minorRaw);
  const nodeSupported = major > 22 || (major === 22 && minor >= 18);
  checks.push({
    name: 'node',
    status: nodeSupported ? 'ok' : 'warn',
    detail: nodeSupported
      ? `Node ${process.versions.node}（满足 engines >=22.18）`
      : `Node ${process.versions.node} 低于要求的 >=22.18，无法直接运行 .mts 源码，行为可能不可预期`,
  });

  // 平台声明：boss 已避开 shell:true 与硬编码 /bin 路径，POSIX 与 Windows 均可运行；
  // 仅把当前平台如实报出，便于排查跨平台问题。
  checks.push({
    name: 'platform',
    status: 'ok',
    detail: `${process.platform}/${process.arch}`,
  });

  // git 是可选依赖：仅 WIP checkpoint（stash/commit/branch）用到；不在 git 仓库或未装 git
  // 时 checkpoint 会静默跳过而非报错。这里把该边界显式化。
  const git = spawnSync('git', ['--version'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  });
  const gitOk = git.status === 0;
  checks.push({
    name: 'git',
    status: 'ok', // git 缺失不是错误，只影响可选的 WIP checkpoint
    detail: gitOk
      ? `${(git.stdout || '').trim() || 'available'}（WIP checkpoint 可用）`
      : 'git 不可用：WIP checkpoint 将静默跳过，其余功能不受影响',
  });

  return checks;
}

/** 项目内每个 feature 的事件流完整性与孤儿 lock。 */
function checkFeatures(cwd: string): DoctorCheck[] {
  const bossRoot = path.join(cwd, '.boss');
  if (!fs.existsSync(bossRoot)) {
    return [{ name: 'features', status: 'ok', detail: '当前目录无 .boss/（非 boss 项目）' }];
  }

  const checks: DoctorCheck[] = [];
  const features = fs
    .readdirSync(bossRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && !entry.name.startsWith('.'))
    .map((entry) => entry.name);

  if (features.length === 0) {
    return [{ name: 'features', status: 'ok', detail: '.boss/ 下暂无 feature' }];
  }

  for (const feature of features) {
    const metaDir = path.join(bossRoot, feature, '.meta');
    const eventsFile = path.join(metaDir, 'events.jsonl');

    if (!fs.existsSync(eventsFile)) {
      checks.push({
        name: `feature:${feature}`,
        status: 'warn',
        detail: '缺少 events.jsonl（事件流真相源不存在）',
      });
      continue;
    }

    try {
      const { records, corruptLines } = readJsonlTolerant(eventsFile);
      if (corruptLines.length > 0) {
        checks.push({
          name: `feature:${feature}`,
          status: 'warn',
          detail: `事件流有 ${corruptLines.length} 条损坏行（疑似写入中途崩溃，将被跳过）：第 ${corruptLines[0]!.line} 行 ${corruptLines[0]!.text.slice(0, 60)}`,
        });
      } else {
        checks.push({
          name: `feature:${feature}`,
          status: 'ok',
          detail: `事件流完整，${records.length} 条事件`,
        });
      }
    } catch (err) {
      checks.push({
        name: `feature:${feature}`,
        status: 'error',
        detail: `事件流中间行损坏（篡改或磁盘错误，无法投影）：${(err as Error).message}`,
      });
    }

    // 门禁失败却把阶段标记为完成：阶段推进没有门禁前置条件，这两条事实可以同时成立。
    // 这里不追溯改写历史，只保证矛盾在体检时显形，而不是让 feature 看起来是健康的。
    try {
      const failedGates = findFailedGates(feature, cwd);
      if (failedGates.length > 0) {
        const first = failedGates[0]!;
        checks.push({
          name: `gates:${feature}`,
          status: 'error',
          detail: `${failedGates.length} 个门禁未通过但所在阶段已标记完成：${first.gate}（阶段 ${first.stage}）`,
        });
      }
    } catch {
      // 状态尚不可投影时跳过：事件流本身的问题已由上面的检查覆盖
    }

    // 孤儿 lock：knowledge worker lock 早已废弃；任何残留 *.lock 都提示可清理
    if (fs.existsSync(metaDir)) {
      const locks = fs.readdirSync(metaDir).filter((name) => name.endsWith('.lock'));
      for (const lock of locks) {
        checks.push({
          name: `feature:${feature}:lock`,
          status: 'warn',
          detail: `残留 lock 文件 ${lock}（若无正在运行的进程可安全删除）`,
        });
      }
    }
  }

  return checks;
}

function showHelp(): void {
  process.stdout.write(
    'boss doctor [--json]\n  诊断安装位置、版本一致性、事件流完整性、孤儿 lock、网络边界（boss 自身）。\n',
  );
}

export function main(
  argv: string[] = process.argv.slice(2),
  { cwd = process.cwd() }: { cwd?: string } = {},
): number {
  const context = createCliContext(argv, { command: 'boss doctor' });
  if (context.values.describe) {
    writeOutput(
      describeCommand(commandDescriptions['boss doctor']!),
      context,
      () => `${JSON.stringify(commandDescriptions['boss doctor'], null, 2)}\n`,
    );
    return 0;
  }
  if (argv.includes('-h') || argv.includes('--help')) {
    showHelp();
    return 0;
  }

  const checks: DoctorCheck[] = [
    { name: 'version', status: 'ok', detail: `boss-skill v${VERSION}` },
    ...checkEnvironment(),
    ...checkNetworkBoundary(),
    ...checkInstalls(),
    ...checkFeatures(cwd),
  ];

  const errorCount = checks.filter((c) => c.status === 'error').length;
  const warnCount = checks.filter((c) => c.status === 'warn').length;
  const overall: CheckStatus = errorCount > 0 ? 'error' : warnCount > 0 ? 'warn' : 'ok';

  writeOutput({ status: overall, errorCount, warnCount, checks }, context, () => {
    const icon = (s: CheckStatus) => (s === 'ok' ? '✅' : s === 'warn' ? '⚠️ ' : '❌');
    const lines = [
      `boss doctor — ${icon(overall)} ${overall.toUpperCase()}（${errorCount} 错误 / ${warnCount} 警告）`,
      '',
      ...checks.map((c) => `  ${icon(c.status)} ${c.name}: ${c.detail}`),
    ];
    return `${lines.join('\n')}\n`;
  });

  // error 才非零退出；warn 不阻断（诊断信息，不是门禁）
  return errorCount > 0 ? 1 : 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const context = createCliContext(process.argv.slice(2), {
    command: 'boss doctor',
    validateOptionValues: false,
  });
  process.exit(await runMain(() => main(process.argv.slice(2), { cwd: process.cwd() }), context));
}
