#!/usr/bin/env python3
"""Summarize a running or finished second-opinion review from its JSONL events. See ../SKILL.md.

Usage: progress.py <out_dir> [--run first|recheck-N] [--last N]

By default it shows the newest run in the folder (the latest recheck if there is one).
The parser reads Codex's `exec --json` events; for another CLI, change summarize_event.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def option(name, default):
    if name in sys.argv:
        index = sys.argv.index(name)
        if index + 1 >= len(sys.argv):
            sys.exit(f'{name} needs a value\n\n{__doc__}')
        return sys.argv[index + 1]
    return default


def newest_prefix(out):
    rechecks = []
    for path in out.glob('recheck-*-events.jsonl'):
        match = re.fullmatch(r'recheck-(\d+)-events\.jsonl', path.name)
        if match:
            rechecks.append(int(match.group(1)))
    return f'recheck-{max(rechecks)}-' if rechecks else ''


def summarize_event(event, summary):
    kind = event.get('type')
    item = event.get('item') or {}
    if kind == 'thread.started':
        summary['session'] = event.get('thread_id')
    elif kind == 'item.completed' and item.get('type') == 'command_execution':
        summary['commands'].append(item.get('command', ''))
    elif kind == 'item.completed' and item.get('type') == 'agent_message':
        summary['messages'].append(item.get('text', ''))
    elif kind == 'item.completed' and item.get('type') == 'mcp_tool_call':
        summary['mcp_calls'].append(f"{item.get('server')}.{item.get('tool')}")
    elif kind == 'turn.completed':
        summary['usage'] = event.get('usage')
    elif kind in ('error', 'turn.failed'):
        summary['errors'].append(json.dumps(event)[:300])


def read_text(path):
    return path.read_text().strip() if path.exists() else None


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith('-'):
        sys.exit(__doc__)
    out = Path(sys.argv[1])
    last = int(option('--last', '8'))
    run = option('--run', None)
    if run is None:
        prefix = newest_prefix(out)
    elif run == 'first':
        prefix = ''
    else:
        prefix = f'{run}-'

    events_path = out / f'{prefix}events.jsonl'
    if not events_path.exists():
        sys.exit(f'No events yet: {events_path}')

    summary = {'session': None, 'commands': [], 'messages': [], 'mcp_calls': [], 'usage': None, 'errors': []}
    for line in events_path.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            summarize_event(event, summary)

    print(f"Run: {prefix.rstrip('-') or 'first'}")
    started = read_text(out / f'{prefix}started-at.txt')
    finished = read_text(out / f'{prefix}finished-at.txt')
    if started:
        start = datetime.fromisoformat(started.replace('Z', '+00:00'))
        end = datetime.fromisoformat(finished.replace('Z', '+00:00')) if finished else datetime.now(timezone.utc)
        print(f"{'Finished after' if finished else 'Running for'} {int((end - start).total_seconds() // 60)} min")

    # A recheck's events may not repeat the session ID; the first run's events have it.
    session = summary['session']
    if session is None and prefix:
        for line in (out / 'events.jsonl').read_text().splitlines() if (out / 'events.jsonl').exists() else []:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and event.get('type') == 'thread.started':
                session = event.get('thread_id')
                break
    print(f'Session: {session} (recheck with: start_review --resume {session} <repo_worktree> {out})')

    mcp_calls = summary['mcp_calls']
    print(f"Commands run: {len(summary['commands'])}; MCP calls: {len(mcp_calls)}"
          + (f" ({', '.join(sorted(set(mcp_calls)))})" if mcp_calls else ''))
    written = sorted(
        str(p.relative_to(out)) for p in out.rglob('*.md')
        if p.relative_to(out).parts[0] != 'checkout'
        and not re.fullmatch(r'(recheck-\d+-)?(recheck-)?prompt(-sent)?\.md|(recheck-\d+-)?final-message\.md', p.name)
    )
    print(f"Files written: {', '.join(written) or 'none yet'}")
    if summary['errors']:
        print('Errors:')
        for error in summary['errors'][-3:]:
            print(f'  {error}')
    print(f'Last {last} commands:')
    for command in summary['commands'][-last:]:
        print(f'  {command[:160]}')
    print('Last message:')
    if summary['messages']:
        print('  ' + summary['messages'][-1][:600].replace('\n', '\n  '))
    if summary['usage']:
        print(f"Usage: {summary['usage']}")
    for name in ('exit-status.txt', 'repo-check.txt', 'findings-check.txt'):
        value = read_text(out / f'{prefix}{name}')
        if value is not None:
            print(f'{name}: {value}')


if __name__ == '__main__':
    main()
