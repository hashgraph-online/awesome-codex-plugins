import { readFile, writeFile, mkdir, rename, rm } from 'node:fs/promises'
import { randomUUID } from 'node:crypto'
import path from 'node:path'

// Codex plugins have no settings panel, so the mode lives next to the
// connection and is changed with the plugin's command line. ACTERA_MODE and
// ACTERA_EVALUATION_FAILURE override it for managed or scripted setups.
export const modes = Object.freeze({ monitoring: 'MONITORING', enforcing: 'ENFORCING' })
export const evaluationFailures = Object.freeze({ block: 'deny', allow: 'continue' })
const defaults = Object.freeze({ mode: 'monitoring', evaluationFailure: 'block' })

export class SettingsError extends Error {}

const settingsPath = home => path.join(home, 'settings.json')

async function stored(home) {
  try {
    return JSON.parse(await readFile(settingsPath(home), 'utf8'))
  } catch (error) {
    if (error?.code === 'ENOENT') return {}
    throw new SettingsError('Actera settings are unreadable. Set them again with actera-hook.mjs mode.')
  }
}

export async function runtimeSettings(home, env = process.env) {
  const saved = await stored(home)
  const mode = (env.ACTERA_MODE ?? saved.mode ?? defaults.mode).toLowerCase()
  const failure = (env.ACTERA_EVALUATION_FAILURE ?? saved.evaluationFailure ?? defaults.evaluationFailure).toLowerCase()
  if (!(mode in modes)) throw new SettingsError('Invalid Actera mode. Use monitoring or enforcing.')
  if (!(failure in evaluationFailures)) throw new SettingsError('Invalid evaluation failure setting. Use block or allow.')
  return { mode: modes[mode], onEvaluationError: evaluationFailures[failure], modeName: mode, evaluationFailureName: failure }
}

export async function saveSetting(home, name, value) {
  const choices = name === 'mode' ? modes : evaluationFailures
  const normalized = String(value ?? '').toLowerCase()
  if (!(normalized in choices)) throw new SettingsError(`Choose one of: ${Object.keys(choices).join(', ')}`)
  const next = { ...(await stored(home)), [name]: normalized }
  await mkdir(home, { recursive: true, mode: 0o700 })
  const temporary = `${settingsPath(home)}.${randomUUID()}.tmp`
  try {
    await writeFile(temporary, JSON.stringify(next) + '\n', { flag: 'wx', mode: 0o600 })
    await rename(temporary, settingsPath(home))
  } finally {
    await rm(temporary, { force: true })
  }
  return next
}
