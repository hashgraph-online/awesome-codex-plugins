#!/usr/bin/env python3
"""build_art_forms.py: make the art-form reference pages from one data file.

    references/art-forms.json + art-forms/looks.js
        -> references/art-forms.md            the index the agent reads first
        -> references/art-forms/<id>.md       one page per art form, with the tested demo code

    python3 scripts/build_art_forms.py           write the files
    python3 scripts/build_art_forms.py --check   exit 1 if any generated file is out of date

Standard library only. Edit the JSON (facts) or looks.js (code), run this, then run tests/art_forms/check_looks.mjs.
"""
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
REF = SKILL / 'references'
DATA = json.loads((REF / 'art-forms.json').read_text(encoding='utf-8'))
LOOKS_JS = (SKILL / 'art-forms' / 'looks.js').read_text(encoding='utf-8').replace('\r\n', '\n')


def look_source(look_id):
    """The source of one look, cut out of looks.js: from its key to the line that closes it."""
    m = re.search(r"^  (?:'%s'|%s): \{ kind:" % (re.escape(look_id), re.escape(look_id)), LOOKS_JS, re.M)
    if not m:
        raise SystemExit('build_art_forms: no look called %r in art-forms/looks.js' % look_id)
    rest = LOOKS_JS[m.start():]
    end = re.search(r"^  \} \},\n", rest, re.M)
    return rest[:end.end()].rstrip().rstrip(',') if end else rest


def cadence(f):
    return 'steps %d times a second' % f['fps'] if f['fps'] else 'smooth, full frame rate'


def bullets(items):
    return '\n'.join('- ' + x for x in items)


def page(f):
    out = ['# ' + f['name'], '']
    if f['aliases']:
        out += ['Also called: ' + ', '.join(f['aliases']) + '.', '']
    out += ['Family: %s. Cadence: %s. Usual tool: %s.' % (DATA['families'][f['family']], cadence(f), f['route']), '', f['what'], '', f['origin'], '']
    if f['thin']:
        out += ['Sourcing note: ' + f['thin'], '']
    out += ['## What makes it read as this', '', bullets(f['rules']), '', '## Timing', '', f['timing'], '', '## How to build it', '', bullets(f['build']), '']
    if f['blender']:
        out += [f['blender'], '']
    out += ['## Assets', '', f['assets'] + ' Use only pictures, footage and music the user owns or may reuse; if the user has an image model available, generate textures and cut-out parts with it and say so in REPORT.md.', '',
            '## Sound and pacing', '', f['sound'], '', '## What makes it look wrong', '', bullets(f['pitfalls']), '', '## Tested demo', '',
            'This is the look from `art-forms/looks.js`, which `tests/art_forms/check_looks.mjs` draws in a real browser: it must paint, change over time, and give the same pixels when the same time is drawn twice. '
            'View it: open `art-forms/gallery.html?look=%s` through a local server. The helpers it calls (`held`, `frameOf`, `jit`, `hash`, `grain`, `prog`, the easings) are at the top of that file. '
            'Take the technique, not the picture.' % f['looks'][0], '']
    for look in f['looks']:
        out += ['```js', look_source(look), '```', '']
    out += ['To use a look in a HyperFrames composition, drive it from the timeline the way `references/threejs.md` shows: a paused GSAP timeline tweens a plain object\'s `t` from 0 to the duration with `ease: "none"`, and `onUpdate` calls `draw` with that `t`. Vendor GSAP and three.js into the project first.', '',
            '## Sources', '', bullets('<%s>' % u for u in f['sources']), '', 'Facts checked on %s. Lines marked "practice note" are working advice, not sourced facts.' % DATA['checked'], '']
    return '\n'.join(out)


def index():
    n = len(DATA['forms'])
    out = ['# Art forms: %d looks for animated video, and how to build each' % n, '',
           'Read this when a brief names a look ("claymation", "paper cut-out", "anime", "like a blueprint") or describes a feeling that a look would carry. '
           'It is the index. Each art form has its own page in `references/art-forms/` with its visual rules, timing, build recipe, assets, sound, pitfalls, sources and a tested demo. '
           '`scripts/art_route.py BRIEF.md` proposes one from a brief and says why.', '',
           'An art form sets the look and the timing. The format (`references/formats.md`) still sets the beats, and the tool table in SKILL.md still sets the route.', '',
           '## Three rules behind every look', '',
           '1. **The picture is a function of time.** No clock, no timers, no `Math.random()`. HyperFrames renders by seeking, so anything that depends on the frame before it will be wrong. Randomness comes from a hash of the frame number or of a position.',
           '2. **Handmade looks hold their drawings.** Clay, paper, felt, cel and ink change 8 to 12 times a second while the video stays at 24 or 30. Quantise time before posing anything: `const ts = Math.floor(t * 12) / 12`. In GSAP the same thing is `ease: "steps(12)"` on a one-second tween. Clean looks (flat explainer, low-poly, product render, type) stay smooth.',
           '3. **Imperfection is seeded.** Line boil, paper jitter, lamp flicker, misregistered ink and tape damage are all keyed to the drawing number, so two renders of the same frame match exactly.', '',
           'A `setInterval` that re-rolls a filter, the usual web recipe for line boil, breaks rule 1 and will not render correctly. Key the change to `Math.floor(t * 10)` instead.', '']
    for fam, title in DATA['families'].items():
        out += ['## ' + title, '', '| Art form | What it is | Cadence | Usual tool |', '|---|---|---|---|']
        for f in DATA['forms']:
            if f['family'] == fam:
                out.append('| [%s](art-forms/%s.md) | %s | %s | %s |' % (f['name'], f['id'], f['what'].split('. ')[0].rstrip('.') + '.', cadence(f), f['route']))
        out.append('')
    out += ['## Choosing one from a brief', '',
            '| The brief is about | Try | Why |', '|---|---|---|',
            '| children, family, a gentle story | paper cut-out, claymation, felt | handmade textures feel warm and safe |',
            '| a folk tale, a myth, heritage | shadow puppetry, linocut, ink wash | the form carries the tradition; check the iconography with a source |',
            '| explaining a product or a process | flat vector explainer, isometric, whiteboard | clean shapes keep attention on the idea |',
            '| numbers | infographic | the chart is the picture; every number needs a source |',
            '| a song or a quote | lyric video, kinetic typography | the words are the content |',
            '| a physical product | 3D product render, claymation for a playful take | the object is the hero |',
            '| nostalgia | VHS and glitch, pixel art, rubber-hose, UPA mid-century | each one is a decade |',
            '| calm, reflective | watercolour, ink wash, line art | slow, sparse, quiet |',
            '| loud, independent | risograph, collage, motion comic | print energy and hard cuts |', '',
            'If the brief names a look, use it. If it names none and nothing above fits, do not force one: the plain formats in `references/formats.md` are a look too.', '',
            '## Tools that exist, by name', '',
            '- SVG filters: `feTurbulence` (noise), `feDisplacementMap` (bend by noise: rough edges, line boil, ink bleed), `feMorphology` (thicken or thin: outlines), `feColorMatrix` and `feComponentTransfer` (recolour, threshold, duotone), `feGaussianBlur`.',
            '- CSS: `steps()` timing, `mix-blend-mode: multiply` for overprinted ink and `screen` or `plus-lighter` for glow, `image-rendering: pixelated`, `filter: drop-shadow()`.',
            '- GSAP: `ease: "steps(n)"`; `fromTo` inside scenes; one paused root timeline.',
            '- three.js materials and passes that ship in its examples: `MeshToonMaterial` with a `gradientMap`, `OutlineEffect`, `SobelOperatorShader`, `HalftonePass`, `RenderPixelatedPass`, `FilmPass`, `RGBShiftShader`, `GlitchPass`, `UnrealBloomPass`, `OutputPass`. It ships no watercolour (Kuwahara) pass and no VHS pass.',
            '- Blender does these better than a browser: real subsurface clay, fur and felt fibre, folded paper with thickness, photoreal product shots, Freestyle line art.', '',
            '## Repositories studied', '',
            'Each was cloned outside this repository and its licence file was read first. No code from any of them is copied here; the demos were written for this skill. Licences as written in each repo on 17 Nov 2026.', '',
            '| Repo | Licence | What it taught |', '|---|---|---|',
            '| [mrdoob/three.js](https://github.com/mrdoob/three.js) | MIT | which toon, outline, halftone, pixel, film and glitch files really ship in its examples, and how its toon example builds a gradient map |',
            '| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Apache-2.0 | the seek rules that every look obeys: no clock, no unseeded randomness, time as the only input |',
            '| [pmndrs/postprocessing](https://github.com/pmndrs/postprocessing) | Zlib | the effects it offers for print, pixel, scan-line and glitch looks |',
            '| [pmndrs/drei](https://github.com/pmndrs/drei) | MIT | helper patterns for outlines and toon materials in React Three Fiber |',
            '| [paper-design/shaders](https://github.com/paper-design/shaders) | Apache-2.0 | paper texture, halftone and dithering as shaders; a source to reach for when a look needs more than a canvas |',
            '| [rough-stuff/rough](https://github.com/rough-stuff/rough) | MIT | sketchy shapes and hachure fills for whiteboard and line-art looks |',
            '| [pixijs/filters](https://github.com/pixijs/filters) | MIT | which artefacts make a CRT, old-film or glitch filter convincing |',
            '| [amandaghassaei/OrigamiSimulator](https://github.com/amandaghassaei/OrigamiSimulator) | MIT | folding from crease patterns, for origami beyond a few folds |',
            '| [danielesteban/cubitos](https://github.com/danielesteban/cubitos) | MIT | voxel rendering in three.js |',
            '| [motion-canvas/motion-canvas](https://github.com/motion-canvas/motion-canvas) | MIT | another code-first animation tool; how it structures time |',
            '| [ykob/sketch-threejs](https://github.com/ykob/sketch-threejs) | MIT | a gallery of shader sketches |',
            '| [mattatz/THREE.Watercolor](https://github.com/mattatz/THREE.Watercolor) | MIT (2015) | an older watercolour shader; too dated to build on |',
            '| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | Remotion licence (a company licence above a size) | read only, for how its examples stage looks |',
            '| [nidorx/matcaps](https://github.com/nidorx/matcaps) | no licence file | read only: a matcap gives a quick clay look, but these images cannot be reused, so the clay demo uses a rough material and a generated bump map |', '',
            '## The demos', '',
            '`art-forms/looks.js` holds one small demo per look (%d in all), and `art-forms/gallery.html` plays them. `tests/art_forms/check_looks.mjs` checks every one in a real browser.' % sum(len(f['looks']) for f in DATA['forms']),
            'These pages are generated from `references/art-forms.json` and `art-forms/looks.js` by `scripts/build_art_forms.py`.', '']
    return '\n'.join(out)


def main():
    files = {REF / 'art-forms.md': index()}
    for f in DATA['forms']:
        files[REF / 'art-forms' / (f['id'] + '.md')] = page(f)
    check = '--check' in sys.argv
    stale = 0
    for path, text in files.items():
        if path.exists() and path.read_text(encoding='utf-8').replace('\r\n', '\n') == text:   # a Windows checkout may hold CRLF
            continue
        if check:
            print('out of date: %s' % path.relative_to(SKILL))
            stale += 1
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8', newline='\n')
    if check:
        print('art forms: %d generated files are current' % len(files) if not stale else '%d generated file(s) out of date: run python3 scripts/build_art_forms.py' % stale)
        sys.exit(1 if stale else 0)
    print('art forms: %d forms, %d files written' % (len(DATA['forms']), len(files)))


if __name__ == '__main__':
    main()
