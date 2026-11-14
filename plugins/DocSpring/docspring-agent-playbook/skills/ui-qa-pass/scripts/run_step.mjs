#!/usr/bin/env node
// An example QA step runner, built on Playwright. Copy it into your repo (for example scripts/qa/run_step.mjs) and
// adapt it: it's a starting point, not a library.
//
//   QA_BASE_URL=http://localhost:3000 QA_DIR=~/qa/myapp/my-branch node run_step.mjs steps/settings.mjs [args...]
//   QA_SUFFIX=R2 ...same command...    # the "after" shots, saved beside the "before" ones as <name>-R2.png
//
// A step file exports `default async (page, qa, args) => result`. The runner launches Chromium with a persistent
// profile in $QA_DIR/browser-profile (so sign-ins survive between runs), at 1440x900, light theme, 2x pixels. It
// prints the step's result as JSON, then the console errors and uncaught exceptions from every page the step used:
// popups and new tabs, and pages in the fresh contexts `qa.newContext()` makes (for a signed-out visitor, say). Each
// error is tagged with its context and URL. Pages opened any other way aren't watched. Needs Playwright at an exact
// version and its Chromium: `npm install --save-dev --save-exact playwright@1.64.1 && npx playwright install chromium`.
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { chromium } from 'playwright'

const required = (name) => {
  if (!process.env[name]) throw new Error(`Set ${name} (see the comment at the top of run_step.mjs)`)
  return process.env[name]
}
const BASE_URL = required('QA_BASE_URL')
const QA_DIR = path.resolve(required('QA_DIR'))
const SUFFIX = process.env.QA_SUFFIX ? `-${process.env.QA_SUFFIX}` : ''
const [stepFile, ...args] = process.argv.slice(2)
if (!stepFile) throw new Error('Usage: node run_step.mjs <step.mjs> [args...]')

const context = await chromium.launchPersistentContext(path.join(QA_DIR, 'browser-profile'), {
  headless: true,
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
  colorScheme: 'light',
})
const errors = []
const watched = []
// Records console errors and uncaught exceptions from every page in a context, including pages opened later.
const watch = (ctx, label) => {
  const watchPage = (p) => {
    p.setDefaultTimeout(60_000)
    // The first load of a page in development can compile its assets for a minute or more.
    p.setDefaultNavigationTimeout(300_000)
    p.on('console', (m) => m.type() === 'error' && errors.push(`[${label}] ${p.url()}: ${m.text().slice(0, 300)}`))
    p.on('pageerror', (e) => errors.push(`[${label}] ${p.url()}: pageerror: ${String(e).slice(0, 300)}`))
  }
  ctx.pages().forEach(watchPage)
  ctx.on('page', watchPage)
  watched.push(ctx)
}
watch(context, 'profile')
const page = context.pages()[0] ?? (await context.newPage())
let freshBrowser = null

// Development bundles often have unhashed names, so a cached copy would show the code from before the fix.
await (await context.newCDPSession(page)).send('Network.clearBrowserCache')

const qa = {
  context,
  errors,
  // A fresh context with no cookies (a signed-out visitor, a second user), with the same size, theme and pixels, and
  // its pages watched for errors. `label` tags its errors. Use it instead of creating contexts yourself.
  async newContext(label = 'fresh', options = {}) {
    freshBrowser ??= await chromium.launch({ headless: true })
    const ctx = await freshBrowser.newContext({
      viewport: { width: 1440, height: 900 },
      deviceScaleFactor: 2,
      colorScheme: 'light',
      ...options,
    })
    watch(ctx, label)
    return ctx
  },
  url: (pathname) => new URL(pathname, BASE_URL).href,
  viewport: (width, height = 900) => page.setViewportSize({ width, height }),
  // Emulates the OS setting. If your app stores the person's own theme choice, set that here too.
  theme: (name) => page.emulateMedia({ colorScheme: name }),
  // Waits for the load event, fonts, the visible images in the element and a stable size. Call it before every shot.
  async settle(selector = 'body') {
    await page.waitForLoadState('load')
    await page.evaluate(() => document.fonts.ready)
    const el = page.locator(selector).first()
    await el.waitFor({ state: 'visible' })
    let previous = null
    for (let i = 0; i < 40; i++) {
      await page.waitForTimeout(300)
      const state = await el.evaluate((e) => {
        const box = e.getBoundingClientRect()
        const imagesLoaded = [...e.querySelectorAll('img')]
          .filter((img) => {
            const r = img.getBoundingClientRect()
            return r.bottom > 0 && r.top < window.innerHeight
          })
          .every((img) => img.complete)
        return `${box.width}x${box.height} ${imagesLoaded}`
      })
      if (state === previous && state.endsWith('true')) return
      previous = state
    }
    throw new Error(`${selector} was still loading or changing size after 12 seconds (${previous})`)
  },
  // Keeps hover and focus styles out of the next shot. Blurring also closes open dropdowns.
  async clearHover() {
    await page.mouse.move(0, 0)
    await page.evaluate(() => document.activeElement?.blur())
  },
  // Saves $QA_DIR/screenshots/<name><suffix>.png: the viewport, the full page or one element. Returns the path.
  async shot(name, { selector, fullPage = false } = {}) {
    const file = path.join(QA_DIR, 'screenshots', `${name}${SUFFIX}.png`)
    fs.mkdirSync(path.dirname(file), { recursive: true })
    if (selector) await page.locator(selector).first().screenshot({ path: file })
    else await page.screenshot({ path: file, fullPage })
    console.log(`saved ${file} at ${new Date().toISOString()}`)
    return file
  },
  // The rounded boxes of every element matching the selector, for measuring gaps and alignment.
  boxes: (selector) =>
    page.locator(selector).evaluateAll((els) =>
      els.map((e) => {
        const r = e.getBoundingClientRect()
        const keys = ['top', 'bottom', 'left', 'right', 'width', 'height']
        return Object.fromEntries(keys.map((k) => [k, Math.round(r[k])]))
      })
    ),
}

try {
  const { default: step } = await import(pathToFileURL(path.resolve(stepFile)).href)
  const result = await step(page, qa, args)
  if (result !== undefined) console.log(typeof result === 'string' ? result : JSON.stringify(result, null, 1))
} catch (e) {
  console.log(`STEP FAILED: ${e?.stack ?? e}`)
  process.exitCode = 1
} finally {
  if (errors.length) console.log(`CONSOLE ERRORS:\n${errors.join('\n')}`)
  console.log(`Watched for errors: ${watched.length} context(s), ${watched.flatMap((c) => c.pages()).length} open page(s)`)
  await context.close()
  if (freshBrowser) await freshBrowser.close()
}
