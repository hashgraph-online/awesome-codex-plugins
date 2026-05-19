import { execFileSync } from 'node:child_process'
import { resolve } from 'node:path'
import { test, expect } from '@playwright/test'

const runId = process.env.THOTH_SELFTEST_RUN_ID ?? ''
const taskId = process.env.THOTH_SELFTEST_TASK_ID ?? 'task-1'
const projectRoot = process.env.THOTH_SELFTEST_PROJECT_ROOT ?? resolve(__dirname, '..', '..', '..')
const sourceRoot = process.env.THOTH_SELFTEST_SOURCE_ROOT ?? resolve(__dirname, '..', '..', '..', '..', '..')
const pythonBin = process.env.THOTH_SELFTEST_PYTHON ?? 'python3'

test('dashboard reflects live runtime state and stop transitions', async ({ page }) => {
  test.skip(!runId, 'THOTH_SELFTEST_RUN_ID is required')

  await page.goto('/overview')
  const runtimeSection = page.locator('article.card').filter({
    has: page.getByRole('heading', { name: /运行态摘要|Runtime summary/ }),
  })
  await expect(runtimeSection).toContainText(taskId)
  await expect(runtimeSection).toContainText('codex')

  await page.goto('/work-items')
  await page.getByText(taskId).first().click()
  const taskDetail = page.locator('.task-detail').first()
  await expect(taskDetail).toContainText(runId)
  await expect(taskDetail).toContainText('codex')

  execFileSync(
    pythonBin,
    ['-m', 'thoth.cli', 'run', '--stop', runId],
    {
      cwd: projectRoot,
      env: {
        ...process.env,
        PYTHONPATH: process.env.PYTHONPATH
          ? `${sourceRoot}:${process.env.PYTHONPATH}`
          : sourceRoot,
      },
      stdio: 'ignore',
    },
  )

  await page.reload()
  await page.getByText(taskId).first().click()
  await expect(taskDetail).toContainText('stopped')
})
