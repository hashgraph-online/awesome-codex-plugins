import { canonicalJSON, digest } from '../workflow-revisions.mjs';

const typeCounts = items => {
  const counts = {};
  for (const item of Array.isArray(items) ? items : []) counts[item] = (counts[item] ?? 0) + 1;
  return counts;
};

export function compactCodexResultEvidence(result) {
  const commandAudit = Array.isArray(result?.command_audit) ? result.command_audit : [];
  return {
    ...(result?.audit === undefined ? {} : { audit: structuredClone(result.audit) }),
    item_type_counts: typeCounts(result?.item_types),
    command_audit_count: commandAudit.length,
    command_audit_sha256: digest(canonicalJSON(commandAudit)),
  };
}

export async function persistCodexCommandAudits(runtime, runId, label, records) {
  const retained = records.flatMap(record => {
    const commandAudit = Array.isArray(record.result?.command_audit) ? record.result.command_audit : [];
    if (!commandAudit.length) return [];
    return [{ ...structuredClone(record.identity), command_audit: structuredClone(commandAudit) }];
  });
  if (!retained.length) return null;
  const body = Buffer.from(canonicalJSON({ version: 1, records: retained }), 'utf8');
  const reference = await runtime.runs.saveArtifact(runId, label, body);
  return { ...reference, record_count: retained.length,
    command_count: retained.reduce((sum, item) => sum + item.command_audit.length, 0) };
}
