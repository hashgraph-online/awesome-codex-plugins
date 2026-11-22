#!/usr/bin/env python3
"""art_route.py: read a brief and propose an art form for the video, with the reason.

    python3 scripts/art_route.py BRIEF.md          a short report
    python3 scripts/art_route.py BRIEF.md --json   the same as JSON
    echo "a claymation ad for our tea" | python3 scripts/art_route.py -

A keyword scorer over references/art-forms.json, not a judge. A look named in the brief wins. Otherwise it looks at
what the video is about and the mood. One stray word is never enough, and when nothing fits it says so: the plain
formats in references/formats.md are a look too. Standard library only.
"""
import json
import re
import sys
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / 'references'

# what the video is about, or its mood -> art forms in order, and the reason given
SUBJECTS = [
    (r'\b(kids?|children|toddlers?|family|bedtime|nursery|preschool)\b', ['paper-cutout', 'claymation', 'felt'], 'a young or family audience: handmade textures feel warm'),
    (r'\b(folk ?tale|myth\w*|legend|epic|heritage|tradition\w*|ramayana|mahabharata|fable|ancestral)\b', ['shadow-puppet', 'linocut', 'ink-wash'], 'a traditional story: the form carries the tradition'),
    (r'\b(explain\w*|how it works|onboarding|tutorial|walkthrough|process|workflow|saas|software)\b', ['flat-explainer', 'isometric', 'whiteboard'], 'explaining something: clean shapes keep attention on the idea'),
    (r'\b(lesson|lecture|classroom|teach\w*|maths?|physics|equation)\b', ['whiteboard', 'flat-explainer', 'line-art'], 'teaching: a drawing that builds as it is explained'),
    (r'\b(data|statistics?|stats|numbers|percent\w*|growth|survey|report|chart|graph)\b', ['infographic', 'flat-explainer', 'isometric'], 'numbers: the chart is the picture'),
    (r'\b(song|lyrics?|music video|single|track|album|chorus)\b', ['lyric-video', 'kinetic-type', 'vhs-glitch'], 'a song: the words are timed to the vocal'),
    (r'\b(quote|manifesto|slogan|tagline|poem|spoken word)\b', ['kinetic-type', 'line-art', 'ink-wash'], 'a line of words: let the type carry it'),
    (r'\b(product shot|packshot|launch|unboxing|hardware|device|bottle|perfume|watch|headphones|gadget)\b', ['product-render', 'claymation', 'isometric'], 'a physical product: the object is the hero'),
    (r'\b(architecture|infrastructure|logistics|city|factory|network|system diagram|supply chain)\b', ['isometric', 'blueprint', 'low-poly'], 'a system: a small model seen from above explains it'),
    (r'\b(engineering|mechanical|machine|invention|patent|specification|how it is made)\b', ['blueprint', 'line-art', 'isometric'], 'something engineered: a technical drawing suits it'),
    (r'\b(game|gaming|arcade|console|8-?bit|16-?bit)\b', ['pixel-art', 'voxel', 'low-poly'], 'games: the look of the medium'),
    (r'\b(80s|1980s|90s|1990s|nostalgi\w+|throwback|retro|vintage|old-?school)\b', ['vhs-glitch', 'pixel-art', 'upa-midcentury'], 'a past decade: its own recording medium is the look'),
    (r'\b(1920s|1930s|jazz age|old cartoon|silent film)\b', ['rubber-hose', 'upa-midcentury', 'linocut'], 'early animation: the cartoon style of that time'),
    (r'\b(calm|meditat\w+|mindful\w*|quiet|gentle|reflective|serene|slow)\b', ['watercolour', 'ink-wash', 'line-art'], 'a calm tone: slow, sparse, quiet looks'),
    (r'\b(bold|loud|punk|zine|indie|diy|street|poster|protest)\b', ['risograph', 'collage', 'motion-comic'], 'a loud, independent tone: print energy and hard cuts'),
    (r'\b(craft\w*|handmade|artisan\w*|cosy|cozy|homemade|bakery|knit\w*|wool)\b', ['paper-cutout', 'felt', 'stop-motion'], 'something handmade: show the hand'),
    (r'\b(night|bar|club|nightlife|after dark|city lights|open late)\b', ['neon-sign', 'vhs-glitch', 'kinetic-type'], 'night: light that glows on dark'),
    (r'\b(action|fight|hero\w*|superhero|battle|chase)\b', ['cel-shaded', 'motion-comic', 'kinetic-type'], 'action: hard poses and hard cuts'),
    (r'\b(nature|landscape|mountain|forest|travel|outdoors?)\b', ['low-poly', 'watercolour', 'paper-cutout'], 'landscape: simple forms and soft colour'),
]


# A brief with characters or dialogue also needs the character kit, whichever look it picks. It takes a character noun
# or a scripted scene, never a bare "says" or "characters": "a chart that says revenue doubled, 40 characters per line" has none.
_PEOPLE = r'(?:child|kid|boy|girl|man|woman|crow|bird|fox|dog|cat|robot|chef|tomato|mascot|hero|villain|knight|king|queen|monkey|owl)'
CHARACTERS = re.compile(
    r"\b(?:dialogue|dialog|conversation|skit|mascot|lip[- ]?sync(?:ed)?|short story|animated story|cartoon)\b"     # words that mean a scripted scene
    r"|\b(?:a|an|the|our|my|your|his|her|their|two|three|four|five|six|several|main|animated|cartoon|story)\s+(?:[a-z-]+\s+)?characters?\b"
    r"(?!\s+(?:per|long|limit|max|maximum|wide|count|in\s+(?:a|the|each|every)\b))"                              # not "characters per line"
    r"|\b" + _PEOPLE + r"s?\s+(?:says|said|asks|replies|shouts|whispers|answers|talks|speaks)\b"                  # a someone who talks
    r"|\btalking\s+" + _PEOPLE + r"|\btalking\s+(?:character|animal)s?\b", re.I)
KIT = 'characters/README-CHARACTERS.md'
KIT_SKINS = ('line-art', 'paper-cutout', 'shadow-puppet', 'cel-shaded', 'motion-comic', 'flat-explainer')


def kit_reason(form):
    base = 'the brief has characters or dialogue: use the character kit (%s) for poses, walk cycles, blinks and lip sync' % KIT
    if form in KIT_SKINS:
        return base + '; it has a skin for this look'
    return base + '; its skins are ' + ', '.join(KIT_SKINS) + ', so use the nearest and say so in SPEC.md'


def norm(text):
    """Lower case, with hyphens, underscores and runs of spaces as single spaces: "Shadow-Puppet" and "shadow  puppet" match."""
    return re.sub(r'[\s_\-]+', ' ', str(text or '').lower()).strip()


def load():
    return json.loads((REF / 'art-forms.json').read_text(encoding='utf-8'))


def route(brief, data=None):
    data = data or load()
    text = str(brief or '').replace('’', "'")
    score, why, strong = {}, {}, set()

    def bump(fid, n, reason, is_strong=False):
        score[fid] = score.get(fid, 0) + n
        why.setdefault(fid, [])
        if reason not in why[fid]:
            why[fid].append(reason)
        if is_strong:
            strong.add(fid)

    named = False
    flat = norm(text)
    for f in data['forms']:
        for nm in [f['name']] + f['aliases'] + [f['id']]:
            short = norm(re.sub(r'\s*\(.*\)', '', nm).split(' and ')[0])
            # hyphens, spaces and plurals do not matter: "shadow-puppet", "shadow puppets" and "shadow puppetry" all name Shadow puppetry
            if len(short) > 3 and re.search(r'\b%s(?:s|es|ry|ing|ed)?\b' % re.escape(short), flat):
                bump(f['id'], 20, 'the brief names "%s"' % short, True)
                named = True
                break
        for kw in f['keywords']:
            if re.search(r'\b%s\w*\b' % re.escape(norm(kw)), flat):
                bump(f['id'], 3, 'it says "%s"' % kw)
    for pattern, forms, reason in SUBJECTS:
        m = re.search(pattern, text, re.I)
        if m:
            for i, fid in enumerate(forms):
                bump(fid, 4.5 - i, '%s ("%s")' % (reason, m.group(0).lower()), True)
    kit = bool(CHARACTERS.search(text))
    ranked = sorted(((s, fid) for fid, s in score.items() if fid in strong or s >= 6), key=lambda x: (-x[0], [f['id'] for f in data['forms']].index(x[1])))
    by_id = {f['id']: f for f in data['forms']}
    if not ranked:
        return {'form': None, 'confidence': 'none', 'why': ['the brief names no look, subject or mood the table knows'] + ([kit_reason(None)] if kit else []), 'alternatives': [], 'read': ['references/formats.md', 'references/art-forms.md'] + ([KIT] if kit else []), 'kit': KIT if kit else None}
    top = by_id[ranked[0][1]]
    return {
        'form': top['id'], 'name': top['name'], 'confidence': 'named' if named and ranked[0][0] >= 20 else 'inferred', 'why': why[top['id']][:3] + ([kit_reason(top['id'])] if kit else []), 'kit': KIT if kit else None,
        'cadence': 'steps %d times a second' % top['fps'] if top['fps'] else 'smooth, full frame rate', 'route': top['route'], 'blender': top['blender'],
        'pitfalls': top['pitfalls'], 'alternatives': [{'form': by_id[fid]['id'], 'name': by_id[fid]['name']} for _, fid in ranked[1:3]],
        'read': ['references/art-forms/%s.md' % top['id'], 'references/art-forms.md'] + ([KIT] if kit else []), 'demo': 'art-forms/gallery.html?look=%s' % top['looks'][0],
    }


def report(r):
    if not r['form']:
        note = ('\nCharacters: ' + r['why'][1] + '.') if len(r['why']) > 1 else ''
        return 'Art form: none suggested. %s. Use a format from references/formats.md, or choose a look from references/art-forms.md and say why in SPEC.md.%s' % (r['why'][0].capitalize(), note)
    lines = ['Art form: %s (%s)' % (r['name'], 'named in the brief' if r['confidence'] == 'named' else 'inferred')]
    lines += ['  why: ' + w for w in r['why']]
    lines += ['  cadence: ' + r['cadence'], '  usual tool: ' + r['route']]
    if r['blender']:
        lines.append('  note: ' + r['blender'])
    if r['alternatives']:
        lines.append('  or: ' + ', '.join(a['name'] for a in r['alternatives']))
    lines += ['  watch for: ' + '; '.join(r['pitfalls']), '  read: ' + r['read'][0], '  demo: ' + r['demo']]
    if r['confidence'] == 'inferred':
        lines.append('Note: this is a guess from the subject and mood words. If the brief or the brand has its own look, that wins.')
    return '\n'.join(lines)


def main(argv):
    for stream in (sys.stdout, sys.stdin):          # Windows consoles default to a legacy code page
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    args = [a for a in argv if not a.startswith('--')]
    if '--help' in argv or '-h' in argv or not args:
        print('usage: python3 art_route.py <BRIEF.md | -> [--json]\n  Proposes an art form for a video brief, with reasons. "-" reads the brief from standard input.')
        return 0 if ('--help' in argv or '-h' in argv) else 2
    try:
        brief = sys.stdin.read() if args[0] == '-' else Path(args[0]).read_text(encoding='utf-8')
    except OSError as e:
        print('art_route.py: cannot read %s: %s' % (args[0], e), file=sys.stderr)
        return 2
    if not brief.strip():
        print('art_route.py: the brief is empty', file=sys.stderr)
        return 2
    r = route(brief)
    print(json.dumps(r, indent=2) if '--json' in argv else report(r))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
