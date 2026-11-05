#!/usr/bin/env python3
"""Advisory single-writer lock for a Figma file, shared by every agent session on one machine.

Two agents writing to the same Figma file at the same time corrupt each other's work: one
switches the current page while the other is mid-batch, or both clone into the same spot.
This lock lets a session say "I am writing to this file" before it starts.

Usage:
  figma_lock.py claim <fileKey> --agent NAME --task ID [--ttl SECONDS]
  figma_lock.py check <fileKey>
  figma_lock.py release <fileKey> --agent NAME --task ID [--force]
  figma_lock.py sweep

The lock is TTL based on purpose. A lock tied to the PID of the shell that created it dies
the moment that shell exits, and agent tool shells exit right after every command.

Every command prints one JSON object. Exit 0 on success, 1 on conflict or invalid input.
Locks live in ~/.cache/figma-maxxing/locks (override with FIGMA_LOCK_DIR).
The lock is advisory: it only protects sessions that check it.
"""
import argparse
import json
import os
import re
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None
    import msvcrt

KEY_RE = re.compile(r'[A-Za-z0-9_-]{1,64}')
DEFAULT_TTL = 1800
MAX_TTL = 86400


def lock_dir() -> Path:
    custom = os.environ.get('FIGMA_LOCK_DIR')
    return Path(custom).expanduser() if custom else Path.home() / '.cache' / 'figma-maxxing' / 'locks'


def iso(ts: float) -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(ts))


@contextmanager
def mutex(directory: Path):
    """Serialize claim and release across processes with an OS file lock.

    The operating system drops the lock when the holding process dies, so a crashed
    session never leaves the directory blocked.
    """
    directory.mkdir(parents=True, exist_ok=True)
    fd = os.open(directory / '.mutex', os.O_CREAT | os.O_RDWR)
    try:
        try:
            if fcntl:
                fcntl.flock(fd, fcntl.LOCK_EX)
            else:
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)  # retries for about 10 s, then raises
        except OSError as error:
            raise TimeoutError('lock directory is busy') from error
        try:
            yield
        finally:
            if fcntl:
                fcntl.flock(fd, fcntl.LOCK_UN)
            else:
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(fd)


def read_lock(path: Path):
    """Return the live lock record, or None when the file is free, expired or unreadable."""
    try:
        record = json.loads(path.read_text())
        if float(record['expires_epoch']) > time.time():
            return record
    except (FileNotFoundError, ValueError, KeyError, TypeError):
        pass
    return None


def public(record: dict) -> dict:
    return {k: record[k] for k in ('agent', 'task', 'claimed_at', 'expires_at')}


def claim(args) -> int:
    directory = lock_dir()
    path = directory / f'{args.file_key}.json'
    task = args.task or f'adhoc-{uuid.uuid4()}'
    with mutex(directory):
        held = read_lock(path)
        if held and (held['agent'], held['task']) != (args.agent, task):
            print(json.dumps({'claimed': False, 'held': True, **public(held)}))
            return 1
        now = time.time()
        record = {
            'file_key': args.file_key,
            'agent': args.agent,
            'task': task,
            'claimed_at': held['claimed_at'] if held else iso(now),
            'expires_at': iso(now + args.ttl),
            'expires_epoch': now + args.ttl,
        }
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(record))
        os.replace(tmp, path)
    print(json.dumps({'claimed': True, 'renewed': bool(held), **public(record)}))
    return 0


def check(args) -> int:
    held = read_lock(lock_dir() / f'{args.file_key}.json')
    print(json.dumps({'held': True, **public(held)} if held else {'held': False}))
    return 0


def release(args) -> int:
    directory = lock_dir()
    path = directory / f'{args.file_key}.json'
    with mutex(directory):
        held = read_lock(path)
        if not held:
            path.unlink(missing_ok=True)
            print(json.dumps({'released': False, 'held': False}))
            return 0
        if not args.force and (held['agent'], held['task']) != (args.agent, args.task):
            print(json.dumps({'released': False, 'held': True, **public(held)}))
            return 1
        path.unlink(missing_ok=True)
    print(json.dumps({'released': True, 'held': False}))
    return 0


def sweep(_args) -> int:
    directory = lock_dir()
    removed = 0
    if directory.is_dir():
        with mutex(directory):
            for path in directory.glob('*.json'):
                if read_lock(path) is None:
                    path.unlink(missing_ok=True)
                    removed += 1
    print(json.dumps({'swept': removed}))
    return 0


def file_key(value: str) -> str:
    if not KEY_RE.fullmatch(value):
        raise argparse.ArgumentTypeError('fileKey must be 1 to 64 letters, digits, "_" or "-"')
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('claim', help='claim or renew the lock')
    p.add_argument('file_key', type=file_key)
    p.add_argument('--agent', default=os.environ.get('FIGMA_LOCK_AGENT', 'agent'))
    p.add_argument('--task', default=os.environ.get('FIGMA_LOCK_TASK'))
    p.add_argument('--ttl', type=int, default=DEFAULT_TTL, help='seconds until the lock expires')
    p.set_defaults(run=claim)

    p = sub.add_parser('check', help='report who holds the lock; never reserves it')
    p.add_argument('file_key', type=file_key)
    p.set_defaults(run=check)

    p = sub.add_parser('release', help='release a lock you hold')
    p.add_argument('file_key', type=file_key)
    p.add_argument('--agent', default=os.environ.get('FIGMA_LOCK_AGENT', 'agent'))
    p.add_argument('--task', default=os.environ.get('FIGMA_LOCK_TASK'))
    p.add_argument('--force', action='store_true', help='release a lock held by another task (for the human, not the agent)')
    p.set_defaults(run=release)

    p = sub.add_parser('sweep', help='delete expired lock files')
    p.set_defaults(run=sweep)

    args = parser.parse_args(argv)
    if not 0 < getattr(args, 'ttl', 1) <= MAX_TTL:
        parser.error(f'--ttl is in seconds and must be between 1 and {MAX_TTL}')
    if args.command == 'release' and not args.force and not args.task:
        parser.error('release needs --task (or FIGMA_LOCK_TASK) from the claim')
    try:
        return args.run(args)
    except TimeoutError as error:
        print(json.dumps({'error': str(error)}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
