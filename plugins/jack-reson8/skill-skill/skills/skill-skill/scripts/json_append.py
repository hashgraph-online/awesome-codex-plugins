#!/usr/bin/env python3
"""Add entries to a JSON list file without reformatting it.

usage: json_append.py FILE NEW.json [--key KEY]
  NEW.json holds a list (appended to a top-level list or to FILE[KEY]) or an
  object (merged into a top-level object or FILE[KEY]). Indent and ensure_ascii
  are detected from FILE; the write is refused if any existing line changes.
"""
import difflib, json, re, sys

def detect(text):
    m = re.search(r'\n( +|\t)["{\[]', text)
    indent = (m.group(1) if m.group(1) == '\t' else len(m.group(1))) if m else 2
    ascii_ = bool(re.search(r'\\u[0-9a-fA-F]{4}', text)) or not re.search(r'[^\x00-\x7f]', text)
    return indent, ascii_

def main(a):
    if len(a) < 2: sys.exit(__doc__)
    path, new = a[0], json.load(open(a[1]))
    key = a[a.index('--key') + 1] if '--key' in a else None
    text = open(path).read()
    data = json.loads(text)
    target = data[key] if key else data
    if isinstance(target, list) and isinstance(new, list): target.extend(new)
    elif isinstance(target, dict) and isinstance(new, dict):
        clash = set(target) & set(new)
        if clash: sys.exit(f'already present: {sorted(clash)}')
        target.update(new)
    else: sys.exit('NEW must be the same type (list/object) as the target')
    indent, ascii_ = detect(text)
    out = json.dumps(data, indent=indent, ensure_ascii=ascii_) + ('\n' if text.endswith('\n') else '')
    removed = [l for l in difflib.ndiff(text.splitlines(), out.splitlines()) if l.startswith('- ')]
    # a trailing comma added to the previous last entry is the only allowed change
    bad = [l for l in removed if l[2:].rstrip() + ',' not in out.splitlines()]
    if bad: sys.exit('refusing: existing lines would change, e.g.\n' + '\n'.join(bad[:5]))
    open(path, 'w').write(out)
    print(f'ok: +{len(out.splitlines()) - len(text.splitlines())} lines, indent={indent!r}, ensure_ascii={ascii_}')

if __name__ == '__main__': main(sys.argv[1:])
