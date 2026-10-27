#!/usr/bin/env python3
"""pr_triage.py [--author LOGIN] [--json out.json] — every open PR you authored, sorted into what needs action.
Uses `gh` (logged in). Known bot messages are classified so you don't chase noise:

  ACTION   a check or bot is blocking and you can fix it (scan score, validation, missing listing, conflict)
  YOU      only the account owner can do it (register on a site, authorize an app, sign a CLA)
  WAIT     nothing to do: waiting for a maintainer, or the failing check is expected / not ours
  MERGED / CLOSED   reported for the record
"""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

BOT_HINTS = ('qodo', 'coderabbit', 'copilot', 'sourcery', 'gemini-code-assist', 'codeant', 'greptile')  # review apps whose login lacks [bot]
RULES = [  # (substring in a bot comment or check name, bucket, what to do)
    ('ai-plugin-scanner', 'ACTION', 'Centralized plugin scan below 80: reproduce with the pinned plugin-scanner version, fix findings (SECURITY.md, plugin LICENSE, token-like strings in data), push, comment asking for a re-scan.'),
    ('centralized scan', 'ACTION', 'Centralized plugin scan below 80: reproduce with the pinned plugin-scanner version, fix findings, push, ask for a re-scan.'),
    ('glama', 'YOU', 'List the server on glama.ai (account owner) and add the Glama badge to the PR line.'),
    ('vercel', 'WAIT', 'Vercel preview needs a maintainer to authorize fork deploys; not ours to fix.'),
    ('cla', 'YOU', 'Sign the CLA linked in the comment (account owner).'),
    ('ready-to-merge', 'WAIT', 'Auto-labeler accepted it; waiting for a maintainer.'),
]
EXPECTED_FAIL = {('ComposioHQ/awesome-claude-skills', 'validate'): 'auto-labeler only accepts README-only listing PRs'}

def gh(*a):
    r = subprocess.run(['gh', *a], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return r.stdout if r.returncode == 0 else ''

me = ''

def one(item):
    repo, num = item['repository']['nameWithOwner'], str(item['number'])
    raw = gh('pr', 'view', num, '-R', repo, '--json', 'title,state,labels,mergeable,statusCheckRollup,comments,reviews,url')
    if not raw: return dict(ref=f'{repo}#{num}', bucket='WAIT', why='could not read PR', url=item.get('url'))
    d = json.loads(raw); ref = f'{repo}#{num}'
    if d['state'] != 'OPEN': return dict(ref=ref, bucket=d['state'], why='', url=d['url'], title=d['title'])
    labels = [l['name'] for l in d['labels']]
    failing = [c.get('name') or c.get('context') for c in d.get('statusCheckRollup') or [] if str(c.get('conclusion') or c.get('state')).upper() in ('FAILURE', 'ERROR')]
    others = [c for c in d['comments'] if c['author']['login'] != me]
    is_bot = lambda login: '[bot]' in login or login in ('github-actions', 'vercel', 'netlify') or any(k in login for k in BOT_HINTS)
    humans = [c for c in others if not is_bot(c['author']['login'])]
    reviews = [r for r in d['reviews'] if r['state'] in ('CHANGES_REQUESTED', 'COMMENTED') and r['body'] and not is_bot(r['author']['login'])]
    text = ' '.join([c['body'] for c in others] + failing + labels).lower()
    bucket, why = 'WAIT', 'waiting for a maintainer'
    if d['mergeable'] == 'CONFLICTING': bucket, why = 'ACTION', 'merge conflict: rebase the branch on the base branch and push'
    for key, b, w in RULES:
        if key in text and (b != 'WAIT' or bucket == 'WAIT'): bucket, why = b, w; break
    real_fail = [f for f in failing if (repo, f) not in EXPECTED_FAIL and 'vercel' not in f.lower()]
    if real_fail and bucket == 'WAIT': bucket, why = 'ACTION', 'failing check: ' + ', '.join(real_fail) + ' — open the run log'
    if humans or reviews: bucket, why = 'ACTION', 'maintainer replied: ' + ((humans or reviews)[-1]['body'].replace('\n', ' ')[:200])
    if bucket == 'ACTION' and d['comments'] and d['comments'][-1]['author']['login'] == me and not d['mergeable'] == 'CONFLICTING':
        bucket, why = 'WAIT', 'you replied last (' + why[:80] + ') — waiting for them'
    return dict(ref=ref, bucket=bucket, why=why, url=d['url'], title=d['title'], labels=labels, failing=failing)

def main():
    global me
    me = gh('api', 'user', '--jq', '.login').strip()
    author = sys.argv[sys.argv.index('--author') + 1] if '--author' in sys.argv else '@me'
    items = json.loads(gh('search', 'prs', '--author', author, '--limit', '200', '--json', 'repository,number,url,state') or '[]')
    with ThreadPoolExecutor(8) as ex: rows = list(ex.map(one, items))
    order = {'ACTION': 0, 'YOU': 1, 'WAIT': 2, 'MERGED': 3, 'CLOSED': 4}
    rows.sort(key=lambda r: (order.get(r['bucket'], 9), r['ref']))
    counts = {}
    for r in rows: counts[r['bucket']] = counts.get(r['bucket'], 0) + 1
    print(' · '.join(f'{k} {v}' for k, v in sorted(counts.items(), key=lambda kv: order.get(kv[0], 9))))
    for r in rows:
        print(f"{r['bucket']:7} {r['ref']}  {r.get('title', '')[:60]}" + (f"\n        → {r['why']}" if r['bucket'] in ('ACTION', 'YOU') else ''))
    if '--json' in sys.argv: json.dump(rows, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1, ensure_ascii=False)

if __name__ == '__main__':
    main()
