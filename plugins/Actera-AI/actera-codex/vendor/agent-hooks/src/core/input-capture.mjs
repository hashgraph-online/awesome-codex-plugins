import { scan, scanOnce } from './scanner-client.mjs'
export { scannerBinary } from './scanner-client.mjs'
const sensitiveKey = /authorization|password|passwd|secret|token|api.?key|credential|cookie|private.?key/i
const maxInputBytes = 512 * 1024
const pointer = key => String(key).replaceAll('~', '~0').replaceAll('/', '~1')

// The original hook input is never mutated. Both the queue and API use this copy.
// scannerRoot keeps a host's scanner cache inside that host's bridge directory;
// persistentScanner: false scans with a helper that exits before this returns.
export async function captureInput(input, mode = 'tool-inputs', { scannerRoot, persistentScanner = true } = {}) {
  const metadata = { status: 'complete', scanner: 'gitleaks', scanner_version: '8.30.1', redactions: [] }
  if (mode === 'metadata') return { metadata: { status: 'omitted', reason: 'metadata_only' } }
  if (Buffer.byteLength(JSON.stringify(input)) > maxInputBytes)
    return { metadata: { status: 'omitted', reason: 'size_limit' } }
  const strings = []
  function maskFields(value, location = '', depth = 0) {
    if (depth > 32) throw new Error('nesting_limit')
    if (Array.isArray(value)) return value.map((item, i) => maskFields(item, `${location}/${i}`, depth + 1))
    if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key, item]) => {
      const field = `${location}/${pointer(key)}`
      if (sensitiveKey.test(key)) {
        metadata.redactions.push({ path: field, reason: 'sensitive_field' })
        return [key, '[redacted]']
      }
      return [key, maskFields(item, field, depth + 1)]
    }))
    if (typeof value === 'string') strings.push(`${location.split('/').at(-1)} = ${value}`)
    return value
  }
  try {
    const masked = maskFields(input)
    const findings = strings.length ? await (persistentScanner ? scan : scanOnce)(strings.join('\n'), scannerRoot) : []
    // Longest first prevents a shorter overlapping match exposing a suffix.
    const secrets = [...new Set(findings.map((f) => f.Secret))].sort((a, b) => b.length - a.length)
    function replace(value, location = '') {
      if (Array.isArray(value)) return value.map((v, i) => replace(v, `${location}/${i}`))
      if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key, v]) => [key, replace(v, `${location}/${pointer(key)}`)]))
      if (typeof value !== 'string') return value
      const matches = secrets.filter((secret) => value.includes(secret))
      for (const secret of matches) {
        for (const rule of new Set(findings.filter((f) => f.Secret === secret).map((f) => f.RuleID)))
          metadata.redactions.push({ path: location, reason: 'detected_secret', rule_id: rule })
      }
      // Merge overlapping spans before replacement so no suffix is left behind.
      const spans = []
      for (const secret of matches) {
        for (let at = value.indexOf(secret); at >= 0; at = value.indexOf(secret, at + 1)) spans.push([at, at + secret.length])
      }
      spans.sort((a, b) => a[0] - b[0])
      const merged = []
      for (const span of spans) {
        const last = merged.at(-1)
        if (last && span[0] <= last[1]) last[1] = Math.max(last[1], span[1])
        else merged.push([...span])
      }
      for (const [start, end] of merged.reverse()) value = value.slice(0, start) + '[redacted]' + value.slice(end)
      return value
    }
    const parameters = replace(masked)
    metadata.status = metadata.redactions.length ? 'redacted' : 'complete'
    if (Buffer.byteLength(JSON.stringify({ parameters, metadata })) > maxInputBytes)
      return { metadata: { status: 'omitted', reason: 'size_limit' } }
    return { parameters, metadata }
  } catch (error) {
    const known = ['unsupported_platform', 'scanner_integrity_failure', 'scanner_failure', 'scanner_invalid_output', 'nesting_limit']
    return { metadata: { status: 'omitted', reason: known.includes(error.message) ? error.message : 'scanner_failure' } }
  }
}
