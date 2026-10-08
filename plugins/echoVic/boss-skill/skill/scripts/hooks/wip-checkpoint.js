#!/usr/bin/env node
/**
 * WIP Checkpoint Hook
 *
 * Triggered after an agent completes work. It creates a restorable WIP stash
 * while leaving the working tree exactly where the agent left it.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

import { findActiveFeature, readExecJson } from '../lib/boss-utils.js';

const CHECKPOINT_PATHSPEC = ['--', '.', ':(exclude).boss'];

function hasChanges(cwd) {
  const result = spawnSync(
    'git',
    ['status', '--porcelain', '--untracked-files=all', ...CHECKPOINT_PATHSPEC],
    {
      cwd,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    },
  );
  return (result.stdout || '').trim().length > 0;
}

function countChangedFiles(cwd) {
  const result = spawnSync(
    'git',
    ['status', '--porcelain', '--untracked-files=all', ...CHECKPOINT_PATHSPEC],
    {
      cwd,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    },
  );
  return (result.stdout || '').trim().split('\n').filter(Boolean).length;
}

function createStashCheckpoint({ cwd, feature, stage }) {
  const timestamp = new Date().toISOString();
  const changedFiles = countChangedFiles(cwd);
  const message = `boss-wip: ${feature} stage-${stage ?? '?'} ${timestamp}`;
  const result = spawnSync(
    'git',
    ['stash', 'push', '-m', message, '--include-untracked', ...CHECKPOINT_PATHSPEC],
    {
      cwd,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    },
  );
  if (result.status !== 0) return null;

  const listResult = spawnSync('git', ['stash', 'list', '--max-count=1'], {
    cwd,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  });
  const ref = (listResult.stdout || '').split(':')[0] || 'stash@{0}';
  const applyResult = spawnSync('git', ['stash', 'apply', '--index', ref], {
    cwd,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  });
  if (applyResult.status !== 0) return null;

  return { ref, message, timestamp, strategy: 'stash', changedFiles };
}

function recordCheckpoint(cwd, feature, checkpoint) {
  const metaDir = path.join(cwd, '.boss', feature, '.meta');
  fs.mkdirSync(metaDir, { recursive: true });
  const checkpointsFile = path.join(metaDir, 'wip-checkpoints.json');
  const existing = fs.existsSync(checkpointsFile)
    ? JSON.parse(fs.readFileSync(checkpointsFile, 'utf8'))
    : [];
  existing.push(checkpoint);
  fs.writeFileSync(checkpointsFile, JSON.stringify(existing.slice(-10), null, 2), 'utf8');
}

function run(cwd = process.cwd()) {
  const gitCheck = spawnSync('git', ['rev-parse', '--is-inside-work-tree'], {
    cwd,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  });
  if (gitCheck.status !== 0) return;
  if (!hasChanges(cwd)) return;

  const active = findActiveFeature(cwd);
  if (!active) return;

  const execData = readExecJson(cwd, active.feature);
  const runningStageEntry = Object.entries(execData?.stages ?? {}).find(
    ([, stage]) => stage && typeof stage === 'object' && stage.status === 'running',
  );
  const currentStage =
    execData && typeof execData.currentStage === 'number'
      ? execData.currentStage
      : (runningStageEntry?.[0] ?? null);
  const numericStage = currentStage == null ? null : Number(currentStage);
  const stage = Number.isInteger(numericStage) ? numericStage : null;

  const checkpoint = createStashCheckpoint({ cwd, feature: active.feature, stage });
  if (checkpoint) {
    recordCheckpoint(cwd, active.feature, checkpoint);
  }
}

if (process.argv[1] && import.meta.url === new URL(process.argv[1], 'file:').href) {
  run();
}

export { run };
