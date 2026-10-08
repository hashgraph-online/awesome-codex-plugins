import { canonicalJSON } from './workflow-revisions.mjs';
import { requireValue } from './workflow-paths.mjs';

const MAX_MICROS = 10 ** 15;
const usageFields = new Set(['input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'reasoning_output_tokens', 'visual_input_units', 'cost_micros', 'unknown']);
function micros(value, code, message, { allowZero = false } = {}) { requireValue(Number.isSafeInteger(value) && value >= (allowZero ? 0 : 1) && value <= MAX_MICROS, code, message); return value; }

export function validateCostBudget(value) {
  requireValue(value && typeof value === 'object' && !Array.isArray(value), 'COST_BUDGET', 'Cost budget must be an object');
  requireValue(typeof value.approval_id === 'string' && value.approval_id.length > 0 && value.approval_id.length <= 256, 'COST_BUDGET', 'Cost budget requires an approval ID');
  requireValue(typeof value.currency === 'string' && /^[A-Z]{3}$/.test(value.currency), 'COST_BUDGET', 'Cost budget currency must be an ISO uppercase code');
  micros(value.limit_micros, 'COST_BUDGET', 'Cost budget needs a positive integer micro-unit limit');
  return { approval_id: value.approval_id, currency: value.currency, limit_micros: value.limit_micros };
}
export function validateNodeCost(value) {
  requireValue(value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).every(key => key === 'maximum_micros'), 'NODE_COST', 'Node cost only declares a worst-case micro-unit maximum');
  return { maximum_micros: micros(value.maximum_micros, 'NODE_COST', 'Node cost needs a positive worst-case micro-unit maximum') };
}
export function initialCostLedger(budget = null) { return { version: 1, budget: budget ? validateCostBudget(budget) : null, reserved_micros: 0, spent_micros: 0, uncertain_micros: 0, unknown_usage_count: 0, calls: [] }; }
function verifyLedger(ledger) {
  requireValue(ledger && ledger.version === 1 && Array.isArray(ledger.calls), 'COST_LEDGER_CORRUPT', 'Cost ledger is malformed');
  micros(ledger.reserved_micros, 'COST_LEDGER_CORRUPT', 'Reserved cost is invalid', { allowZero: true }); micros(ledger.spent_micros, 'COST_LEDGER_CORRUPT', 'Spent cost is invalid', { allowZero: true }); micros(ledger.uncertain_micros, 'COST_LEDGER_CORRUPT', 'Uncertain terminal cost is invalid', { allowZero: true });
}
export function reserveCost(ledger, { call_id, node_id, attempt_id, maximum_micros, kind = 'model' }) {
  verifyLedger(ledger); requireValue(typeof call_id === 'string' && call_id.length > 0 && call_id.length <= 256 && typeof node_id === 'string' && typeof attempt_id === 'string', 'COST_RESERVATION', 'Cost reservation needs exact run-node-attempt call identity');
  requireValue(['model', 'retry', 'cache', 'visual'].includes(kind), 'COST_RESERVATION', 'Cost reservation kind is unsupported');
  const maximum = maximum_micros === null ? null : micros(maximum_micros, 'COST_RESERVATION', 'Cost reservation needs a positive maximum'); const existing = ledger.calls.find(item => item.call_id === call_id);
  if (existing) { requireValue(canonicalJSON(existing.reservation) === canonicalJSON({ maximum_micros: maximum, kind }), 'COST_RESERVATION_CONFLICT', 'A call already has a different reservation'); return existing; }
  if (ledger.budget) { requireValue(maximum !== null, 'COST_RESERVATION_REQUIRED', 'Budgeted model work needs a declared worst-case cost'); requireValue(ledger.spent_micros + ledger.uncertain_micros + ledger.reserved_micros + maximum <= ledger.budget.limit_micros, 'COST_BUDGET_EXCEEDED', 'Reserve cost before the model call; remaining budget is insufficient'); ledger.reserved_micros += maximum; }
  const entry = { call_id, node_id, attempt_id, reservation: { maximum_micros: maximum, kind }, usage: null }; ledger.calls.push(entry); return entry;
}
export function validateUsage(usage) {
  requireValue(usage && typeof usage === 'object' && !Array.isArray(usage) && Object.keys(usage).every(key => usageFields.has(key)), 'USAGE_SCHEMA', 'Usage has an unsupported field'); requireValue(typeof usage.unknown === 'boolean', 'USAGE_SCHEMA', 'Usage must explicitly say whether metering is unknown');
  for (const field of ['input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'reasoning_output_tokens', 'visual_input_units', 'cost_micros']) if (usage[field] !== undefined) micros(usage[field], 'USAGE_SCHEMA', `${field} must be a nonnegative integer`, { allowZero: true });
  requireValue(usage.unknown || usage.cost_micros !== undefined, 'USAGE_SCHEMA', 'Known usage must include actual cost micro-units'); return structuredClone(usage);
}
export function recordUsage(ledger, callId, usage) {
  verifyLedger(ledger); const entry = ledger.calls.find(item => item.call_id === callId); requireValue(entry, 'USAGE_CALL_MISSING', 'Usage belongs to no reserved model call'); const value = validateUsage(usage);
  if (entry.usage) { requireValue(canonicalJSON(entry.usage) === canonicalJSON(value), 'USAGE_CONFLICT', 'Usage differs from the exact prior record'); return entry; }
  const maximum = entry.reservation.maximum_micros;
  if (value.unknown) {
    // A terminal unknown is no longer an in-flight reservation.  Keep the
    // bounded exposure visible even when no admission budget was configured.
    if (maximum !== null) {
      if (ledger.budget) ledger.reserved_micros -= maximum;
      ledger.uncertain_micros += maximum;
    } else requireValue(!ledger.budget, 'COST_RESERVATION_REQUIRED', 'Unknown budgeted use needs a prior worst-case reservation');
    ledger.unknown_usage_count++; entry.usage = value; return entry;
  }
  if (maximum !== null) requireValue(value.cost_micros <= maximum, 'USAGE_OVER_RESERVATION', 'Reported cost exceeds the pinned worst-case reservation');
  if (ledger.budget) ledger.reserved_micros -= maximum;
  // Record actual spend even without an admission budget.  The ledger is an
  // evidence record, not only a budget gate.
  ledger.spent_micros += value.cost_micros;
  entry.usage = value; return entry;
}
