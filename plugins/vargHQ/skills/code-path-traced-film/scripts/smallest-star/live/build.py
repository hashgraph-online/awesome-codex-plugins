#!/usr/bin/env python3
"""Bundle the live page: bun bundles live/main.js, this inlines it with a poster frame into one HTML file."""
import base64, os, re, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
tmp = sys.argv[1] if len(sys.argv) > 1 else '/tmp'
out_js = os.path.join(tmp, 'live.bundle.js')
subprocess.check_call(['bun', 'build', os.path.join(here, 'main.js'), '--minify', '--target=browser', '--format=iife', f'--outfile={out_js}'])
js = open(out_js).read().replace('</script', '<\\/script')
html = open(os.path.join(here, 'template.html')).read()
poster = os.path.join(here, 'poster.jpg')
src = 'data:image/jpeg;base64,' + base64.b64encode(open(poster, 'rb').read()).decode() if os.path.exists(poster) else 'data:image/gif;base64,R0lGODlhAQABAIAAAAcKFwAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw=='
shader = open(os.path.join(root, 'src', 'shader.js')).read()
glsl = len([l for l in shader.split('\n') if l.strip() and not l.strip().startswith('//')])
html = html.replace('__POSTER__', src).replace('__GLSL__', f'{glsl:,}').replace('__BUNDLE__', js)
dst = os.path.join(here, 'the-smallest-star-live.html')
open(dst, 'w').write(html)
print(dst, len(html) // 1024, 'KB', 'shader lines', glsl)
