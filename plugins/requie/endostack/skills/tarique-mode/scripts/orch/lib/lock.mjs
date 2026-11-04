// Store lock: a file holding the owner's pid, created with O_EXCL so only
// one writer can hold it. A lock left by a dead process is taken over; a
// live holder can only be displaced with force.

import fs from 'node:fs';
import { UserError } from './errors.mjs';

export function pidAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (err) {
    return err.code === 'EPERM';
  }
}

function createExclusive(file) {
  const fd = fs.openSync(file, 'wx', 0o644);
  try {
    fs.writeSync(fd, `${process.pid}\n`);
  } finally {
    fs.closeSync(fd);
  }
}

export function acquireLock(file, { force = false, warn = () => {} } = {}) {
  try {
    createExclusive(file);
    return;
  } catch (err) {
    if (err.code !== 'EEXIST') throw err;
  }
  let raw = '';
  try {
    raw = fs.readFileSync(file, 'utf8').trim();
  } catch (err) {
    if (err.code !== 'ENOENT') throw err;
  }
  const wellFormed = /^[1-9][0-9]*$/.test(raw) && Number.isSafeInteger(Number(raw));
  const holder = raw === '' ? 'unknown' : raw;
  if (wellFormed && !pidAlive(Number(raw))) {
    warn(`removing stale store lock from pid ${raw}, which is no longer running`);
  } else if (force) {
    warn(`--force: taking the store lock from pid ${holder}`);
  } else {
    throw new UserError(`another writer (pid ${holder}) holds the store lock`);
  }
  fs.rmSync(file, { force: true });
  try {
    createExclusive(file);
  } catch (err) {
    if (err.code === 'EEXIST') throw new UserError(`another writer (pid ${readHolder(file)}) holds the store lock`);
    throw err;
  }
}

function readHolder(file) {
  try {
    return fs.readFileSync(file, 'utf8').trim() || 'unknown';
  } catch {
    return 'unknown';
  }
}

export function releaseLock(file) {
  try {
    if (fs.readFileSync(file, 'utf8').trim() === String(process.pid)) fs.rmSync(file, { force: true });
  } catch (err) {
    if (err.code !== 'ENOENT') throw err;
  }
}
