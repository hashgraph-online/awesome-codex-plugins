// Renders clean previz frames (24 fps, no HUD, no text) for the video-to-video pack from the running previz server.
// Needs playwright-core (bun add playwright-core) and Chrome/Chromium (set CHROME=/path/to/chrome if not found).
// Usage: bun capture.mjs <outDir> <id[:tailSeconds]>,...   (the list with tails is printed by build_pack.py --plan)
//        PREVIZ_URL=http://localhost:8765/previz/ bun capture.mjs …   (default shown)
import { chromium } from 'playwright-core';
import { existsSync, mkdirSync } from 'fs';
const [,, outDir, list] = process.argv;
if (!outDir || !list) { console.error('usage: bun capture.mjs <outDir> <id[:tail]>,...'); process.exit(1); }
const FPS = 24;
const URL_ = process.env.PREVIZ_URL || 'http://localhost:8765/previz/';
const chrome = [process.env.CHROME, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser']
  .find(p => p && existsSync(p));
const b = await chromium.launch({ executablePath: chrome, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const p = await b.newPage({ viewport: { width: 1280, height: 1280 }, deviceScaleFactor: 1 });
p.on('pageerror', e => console.log('[pageerror]', e.message));
await p.goto(URL_ + '?export=1');
await p.waitForFunction(() => window.app?.exportFrame);
const { width, height } = await p.evaluate(() => app.exportSize);
await p.setViewportSize({ width, height });
await p.waitForTimeout(500);
for (const item of list.split(',')) {
  const [id, tail = '0'] = item.split(':');
  const dur = await p.evaluate(id => app.shots.find(s => s.id === id)?.dur, id);
  if (dur == null) throw new Error(`unknown shot ${id}`);
  const n = Math.round((dur + +tail) * FPS);
  mkdirSync(`${outDir}/${id}`, { recursive: true });
  for (let i = 0; i < n; i++) {
    await p.evaluate(([id, t]) => app.exportFrame(id, t), [id, (i + 0.5) / FPS]);
    await p.screenshot({ path: `${outDir}/${id}/${String(i).padStart(4, '0')}.png`, clip: { x: 0, y: 0, width, height } });
  }
  console.log(id, n, 'frames', `${width}x${height}`);
}
await b.close();
