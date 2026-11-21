// An example step for run_step.mjs: the settings page at desktop and phone widths, in light and dark.
// Keep your real steps in $QA_DIR/steps/, one per screen or state, and run them again for the "after" shots.
import fs from 'node:fs'
import path from 'node:path'

export default async function (page, qa) {
  await page.goto(qa.url('/settings'))

  // Sign in only when the saved session has expired. The credentials file (QA_EMAIL=..., QA_PASSWORD=...) comes from
  // your test-user script and stays in $QA_DIR. Adjust the URL check and the selectors to your app.
  if (new URL(page.url()).pathname === '/sign_in') {
    const env = Object.fromEntries(
      fs
        .readFileSync(path.join(process.env.QA_DIR, 'login.env'), 'utf8')
        .trim()
        .split('\n')
        .map((line) => [line.slice(0, line.indexOf('=')), line.slice(line.indexOf('=') + 1)])
    )
    await page.fill('#email', env.QA_EMAIL)
    await page.fill('#password', env.QA_PASSWORD)
    await Promise.all([page.waitForURL((url) => url.pathname !== '/sign_in'), page.keyboard.press('Enter')])
    await page.goto(qa.url('/settings'))
  }

  for (const width of [1440, 390]) {
    await qa.viewport(width)
    for (const theme of ['light', 'dark']) {
      await qa.theme(theme)
      await qa.clearHover()
      await qa.settle('main')
      await qa.shot(`settings-${width}-${theme}`)
    }
  }

  // Return whatever you need to check by number rather than by eye: here, the gaps between stacked cards.
  const cards = await qa.boxes('main .card')
  return { cardGaps: cards.slice(1).map((b, i) => b.top - cards[i].bottom) }
}
