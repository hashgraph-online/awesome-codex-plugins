"""Copy every on-screen excerpt verbatim from the {{TITLE}} build record into data/evidence.js (and evidence.json).
Text excerpts keep path + line range; JSON excerpts keep path + the picked keys, so the video never shows a
hand-typed claim. Add one entry per excerpt in main(); the timeline reads them by key.
Run: python3 extract-evidence.py   (override the build folder with TUTORIAL_BUILD_DIR)"""
import json, os
from pathlib import Path

BUILD = Path(os.environ.get('TUTORIAL_BUILD_DIR') or os.path.expanduser('{{BUILD_DIR}}')).resolve()
HERE = Path(__file__).parent
ROOT = BUILD.parent.parent                       # the repo that holds builds/<name>
rel = lambda p: str(Path(p).resolve().relative_to(ROOT))   # repo-relative: never an absolute home path

def lines(p, a, z):
    t = Path(p).read_text().splitlines()
    return {'path': rel(p), 'from': a, 'to': z, 'lines': t[a - 1:z]}

def sentinel(p):  # a step's verdict is its LAST sentinel line
    t = Path(p).read_text().splitlines()
    i = max(k for k, l in enumerate(t) if l.startswith(('AGENT_OK', 'AGENT_FAIL')))
    return {'path': rel(p), 'from': i + 1, 'to': i + 1, 'excerpt': True, 'lines': t[i:i + 1]}

def main():
    ev = {
        # 'state_goal': lines(BUILD / 'state.md', 1, 5),
    }
    text = json.dumps(ev, ensure_ascii=False)
    assert '/Users/' not in text, 'an excerpt carries an absolute home path'
    (HERE / 'data').mkdir(exist_ok=True)
    (HERE / 'data/evidence.json').write_text(json.dumps(ev, ensure_ascii=False, indent=1))
    (HERE / 'data/evidence.js').write_text('window.EVIDENCE = ' + text + ';\n')
    print(f'{len(ev)} excerpts -> data/evidence.js')

main()
