#!/usr/bin/env python3
"""publish_check.py <repo_dir> [--scan] — preflight before you submit a skill repo to any list or marketplace.
Every check here is a rejection or bot failure we actually hit. Exit 1 if anything blocks.

Checks
  frontmatter  every SKILL.md parses as strict YAML (an unquoted ": " in description breaks loaders and list bots)
               name = lowercase-hyphen = folder; description 1-1024 chars
  files        LICENSE and SECURITY.md at the repo root AND inside every plugins/<name>/ folder
  manifests    .claude-plugin/marketplace.json + plugins/<name>/.claude-plugin/plugin.json parse; names and sources agree
  secrets      provider-token prefixes inside data/report files (e.g. "waboxapp-x" contains "xapp-") — scanner false positives
  install      README install commands use ASCII "@" and real plugin@marketplace names
  --scan       run `plugin-scanner scan` (pip install plugin-scanner) and print the score; lists such as awesome-ai-plugins need >= 80
"""
import glob, json, os, re, subprocess, sys

TOKEN_PREFIXES = re.compile(  # same prefixes and minimum payload lengths as plugin-scanner's secret check
    r'AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20}|glpat-[A-Za-z0-9-]{20}'
    r'|(?:xox[bpas]-|xoxe-|xoxr-|xapp-)[A-Za-z0-9-]{10}|sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20}')
DATA_EXT = ('.json', '.jsonl', '.csv', '.tsv', '.txt', '.md', '.yaml', '.yml', '.html')

def frontmatter(text):
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    return m.group(1) if m else None

def strict_yaml(block):
    """Return (dict, error). Uses PyYAML or Ruby when present; otherwise a conservative check for plain scalars with ': '."""
    try:
        import yaml
        try:
            d = yaml.safe_load(block); return (d if isinstance(d, dict) else None), (None if isinstance(d, dict) else 'not a mapping')
        except yaml.YAMLError as e:
            return None, str(e).split('\n')[0]
    except ImportError:
        pass
    try:
        r = subprocess.run(['ruby', '-ryaml', '-rjson', '-e', 'puts JSON.dump(YAML.safe_load(STDIN.read))'], input=block, capture_output=True, text=True, timeout=20)
        if r.returncode == 0: return json.loads(r.stdout), None
        if 'Psych' in r.stderr or 'mapping' in r.stderr: return None, r.stderr.strip().splitlines()[0][:160]
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    d = {}
    for line in block.splitlines():
        k, sep, v = line.partition(':')
        if not sep or line.startswith((' ', '\t')): continue
        v = v.strip(); d[k.strip()] = v.strip('"\'')
        if v and v[0] not in '"\'>|[{' and ': ' in v:
            return None, f'"{k.strip()}" is a plain scalar containing ": " — quote it'
    return d, None

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args: sys.exit(__doc__)
    root = os.path.abspath(args[0]); block, warn, ok = [], [], []
    rel = lambda p: os.path.relpath(p, root)

    skills = [p for p in glob.glob(os.path.join(root, '**', 'SKILL.md'), recursive=True) if '/.git/' not in p and '/node_modules/' not in p]
    non_skill = not skills and any(os.path.exists(os.path.join(root, f)) for f in ('package.json', 'pyproject.toml', 'server.json', 'Dockerfile'))
    if not skills: (ok if non_skill else block).append('no SKILL.md — treated as a tool/MCP repo; skill checks skipped' if non_skill else 'no SKILL.md found')
    for p in skills:
        fm = frontmatter(open(p, encoding='utf-8').read())
        if fm is None: block.append(f'{rel(p)}: missing --- frontmatter ---'); continue
        d, err = strict_yaml(fm)
        if err: block.append(f'{rel(p)}: frontmatter is not valid YAML ({err})'); continue
        name, desc, folder = str(d.get('name', '')), str(d.get('description', '')), os.path.basename(os.path.dirname(p))
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', name) or len(name) > 64: block.append(f'{rel(p)}: name "{name}" must be lowercase-hyphen, ≤64')
        elif name != folder and os.path.dirname(p) != root: block.append(f'{rel(p)}: name "{name}" ≠ folder "{folder}"')
        if not 1 <= len(desc) <= 1024: block.append(f'{rel(p)}: description is {len(desc)} chars (1-1024)')
        ok.append(f'{rel(p)}: YAML ok, name "{name}", description {len(desc)} chars')

    plugin_dirs = [d for d in glob.glob(os.path.join(root, 'plugins', '*')) if os.path.isdir(d)]
    for d in [root] + plugin_dirs:
        for f in ('LICENSE', 'SECURITY.md'):
            if not any(os.path.exists(os.path.join(d, x)) for x in (f, f + '.md', f + '.txt')):
                (block if d == root and f == 'LICENSE' else warn).append(f'{rel(d) if d != root else "."}: missing {f} (scanners deduct points; copy the root one)')

    mp = os.path.join(root, '.claude-plugin', 'marketplace.json'); market = None
    if os.path.exists(mp):
        try:
            market = json.load(open(mp)); mname = market.get('name')
            for e in market.get('plugins', []):
                src = os.path.normpath(os.path.join(root, str(e.get('source', ''))))
                pj = os.path.join(src, '.claude-plugin', 'plugin.json')
                if not os.path.exists(pj): block.append(f'marketplace entry "{e.get("name")}": {rel(pj)} missing'); continue
                pdata = json.load(open(pj))
                if pdata.get('name') != e.get('name'): block.append(f'plugin.json name "{pdata.get("name")}" ≠ marketplace entry "{e.get("name")}"')
                if not glob.glob(os.path.join(src, 'skills', '*', 'SKILL.md')): warn.append(f'{rel(src)}: no skills/<name>/SKILL.md inside the plugin')
                ok.append(f'install: /plugin marketplace add <owner>/{os.path.basename(root)} → /plugin install {e.get("name")}@{mname}')
            if 'strict' in market: warn.append('marketplace.json has root-level "strict" — Claude Code expects it per plugins[] entry')
        except (ValueError, OSError) as e:
            block.append(f'marketplace.json / plugin.json do not parse: {e}')
    elif not non_skill:
        warn.append('no .claude-plugin/marketplace.json — plugin lists (ccplugins, buildwithclaude) and /plugin install need it')
    if skills and not glob.glob(os.path.join(root, '**', '.codex-plugin', 'plugin.json'), recursive=True):
        warn.append('no .codex-plugin/plugin.json — Codex can\'t install it as a plugin (see publishing.md "One skill, every agent")')
    elif skills and not os.path.exists(os.path.join(root, '.agents', 'plugins', 'marketplace.json')):
        warn.append('no .agents/plugins/marketplace.json — `codex plugin marketplace add owner/repo` won\'t find the plugin')
    for p in skills:
        real = os.path.realpath(os.path.dirname(p)); name = os.path.basename(real)
        for home in ('~/.claude/skills', '~/.codex/skills'):
            inst = os.path.expanduser(os.path.join(home, name))
            if os.path.exists(inst) and os.path.realpath(inst) != real:
                warn.append(f'{inst} is a separate copy, not this repo — symlink it to {rel(os.path.dirname(p))} so they can\'t drift')
    if skills and not any(re.search(r'[\u3040-\u30ff\uac00-\ud7af]', open(p, encoding='utf-8').read()[:3000]) for p in skills):
        warn.append('description has no Japanese/Korean trigger words — users writing in those languages may not trigger it')

    for p in glob.glob(os.path.join(root, '**', '*'), recursive=True):
        if '/.git/' in p or not p.endswith(DATA_EXT) or not os.path.isfile(p) or os.path.getsize(p) > 20_000_000: continue
        for i, line in enumerate(open(p, encoding='utf-8', errors='ignore'), 1):
            m = TOKEN_PREFIXES.search(line)
            if m: warn.append(f'{rel(p)}:{i}: "{m.group(0)[:16]}…" looks like a provider token to secret scanners (rename, compress or move the data)'); break

    risky = [(re.compile(r'releases/latest'), 'downloads an unpinned "latest" release — pin a version and verify its checksum'),
             (re.compile(r'(curl|wget)[^\n|]*\|\s*(ba)?sh'), 'pipes a download into a shell'),
             (re.compile(r'npm (i|install) (?![^\n]*@\d)[^\n-]*[a-z]'), 'npm install without pinned versions'),
             (re.compile(r'pip3? install (?![^\n]*==)(?!-r)[a-z]'), 'pip install without pinned versions')]
    for p in glob.glob(os.path.join(root, '**', '*'), recursive=True):
        if '/.git/' in p or not os.path.isfile(p) or not p.endswith(('.sh', '.py', '.js', '.mjs', '.ts')) or p.endswith('publish_check.py'): continue
        txt = '\n'.join(l for l in open(p, encoding='utf-8', errors='ignore') if not re.search(r'^\s*#|\becho\b|print\(', l))  # skip comments and printed hints
        for rx, why in risky:
            if rx.search(txt): warn.append(f'{rel(p)}: {why} (marketplace security reviews close PRs for this)')
    for p in glob.glob(os.path.join(root, 'README*.md')):
        for i, line in enumerate(open(p, encoding='utf-8'), 1):
            if 'plugin install' in line and '＠' in line: block.append(f'{rel(p)}:{i}: full-width "＠" in an install command')

    if '--scan' in sys.argv:
        r = subprocess.run(['plugin-scanner', 'scan', root, '--format', 'json'], capture_output=True, text=True)
        try:
            rep = json.loads(r.stdout); sc = rep.get('score')
            (ok if sc is not None and sc >= 80 else block).append(f'plugin-scanner score {sc} ' + ', '.join(sorted({f["ruleId"] for f in rep.get("findings", [])})))
        except ValueError:
            warn.append('plugin-scanner not available (pip install plugin-scanner) — skipped')

    for x in ok: print('  ✓', x)
    for x in warn: print('  ·', x)
    for x in block: print('  ✗', x)
    print(f'\n{"BLOCKED" if block else "READY"}: {len(block)} blocking, {len(warn)} warnings')
    sys.exit(1 if block else 0)

if __name__ == '__main__':
    main()
