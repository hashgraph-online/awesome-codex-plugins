import { authoringSourcePath } from './authoring-source.mjs';

const slug = value => String(value ?? '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 48) || 'section';

function sourceLines(resources) {
  const bytes = resources?.[authoringSourcePath(resources)];
  return Buffer.isBuffer(bytes) ? bytes.toString('utf8').split('\n') : [];
}

function frontmatterEnd(lines) {
  if (lines[0]?.trim() !== '---') return 0;
  const end = lines.slice(1).findIndex(line => line.trim() === '---');
  return end < 0 ? 0 : end + 2;
}

function sectionAuthority(title, text, { scopedExamples }) {
  if (/^(overview|principles?)$/i.test(title)) return 'required';
  if (/(hard\s+rules?|non[- ]negotiable|anti[- ]patterns?|review\s+checklist|implementation\s+loop|\bprocess\b|\bworkflow\b|procedure|steps?|methods?|algorithms?|contracts?|specifications?)/i.test(title)) return 'required';
  if (scopedExamples) return 'reference_candidate';
  const normative = text.match(/\b(?:must|shall|required|never|do not|forbidden)\b|(?:必须|务必|不得|禁止)/gi)?.length ?? 0;
  return normative >= 2 ? 'required' : 'candidate';
}

/**
 * Stable, bounded semantic units from the always-active Skill entrypoint.
 * The host owns IDs, spans and authority hints; a model chooses only how each
 * unit participates in the resulting Workflow.
 */
export function sourceSectionInventory(resources) {
  const entrypoint=authoringSourcePath(resources);
  const lines = sourceLines(resources);
  if (!lines.length) return [];
  const start = frontmatterEnd(lines);
  const headings = [];
  let fence=null;
  for (let index = start; index < lines.length; index++) {
    const fenceMatch=/^\s*(```+|~~~+)/.exec(lines[index]);
    if(fenceMatch){if(!fence)fence=fenceMatch[1][0];else if(fence===fenceMatch[1][0])fence=null;continue;}
    if(fence)continue;
    const match = /^(#{1,2})\s+(.+?)\s*$/.exec(lines[index]);
    if (match) headings.push({ index, level: match[1].length, title: match[2].replace(/[`*_]/g, '').trim() });
  }
  const h1 = headings.find(item => item.level === 1);
  const h2s = headings.filter(item => item.level === 2);
  const units = [];
  const prefaceStart = (h1?.index ?? start - 1) + 1;
  const prefaceEnd = (h2s[0]?.index ?? lines.length) - 1;
  if (prefaceEnd >= prefaceStart && lines.slice(prefaceStart, prefaceEnd + 1).some(line => line.trim())) {
    units.push({ title: 'Overview', start_line: prefaceStart + 1, end_line: prefaceEnd + 1 });
  }
  for (const [ordinal, heading] of h2s.entries()) {
    const next = h2s[ordinal + 1];
    units.push({ title: heading.title, start_line: heading.index + 1, end_line: next ? next.index : lines.length });
  }
  const wholeText = lines.join('\n');
  const scopedExamples = /only\s+(?:things?\s+)?(?:you\s+)?must\s+do\s+(?:are|is)\s+in\s+the\s+hard\s+rules?|everything\s+else.{0,120}(?:worked\s+example|artistic\s+freedom)/is.test(wholeText);
  return units.map((unit, ordinal) => {
    const text = lines.slice(unit.start_line - 1, unit.end_line).join('\n');
    return {
      section_id: `section_${String(ordinal + 1).padStart(2, '0')}_${slug(unit.title)}`,
      title: unit.title,
      source_span: { resource: entrypoint, start_line: unit.start_line, end_line: unit.end_line },
      authority: sectionAuthority(unit.title, text, { scopedExamples }),
    };
  });
}

export function validateSourceDispositions(proposal, resources, { required = true } = {}) {
  const inventory = sourceSectionInventory(resources);
  const dispositions = proposal?.source_dispositions;
  if (!Array.isArray(dispositions)) return required ? [{ code: 'SOURCE_DISPOSITION_MISSING', reason: 'Every source section needs an explicit semantic disposition.' }] : [];
  const findings = [];
  const knownNodes = new Set((proposal.nodes ?? []).map(node => node.id));
  const knownRequirements = new Set((proposal.source_requirements ?? []).map(item => item.requirement_id));
  const inventoryById = new Map(inventory.map(item => [item.section_id, item]));
  const seen = new Set();
  for (const item of dispositions) {
    const section = inventoryById.get(item?.section_id);
    if (!section) { findings.push({ code: 'SOURCE_DISPOSITION_UNKNOWN', section_id: item?.section_id, reason: 'Disposition names no host-observed source section.' }); continue; }
    if (seen.has(item.section_id)) { findings.push({ code: 'SOURCE_DISPOSITION_DUPLICATE', section_id: item.section_id, reason: 'Each source section must be classified exactly once.' }); continue; }
    seen.add(item.section_id);
    if (!['workflow', 'conditional', 'reference', 'omit'].includes(item.disposition)) findings.push({ code: 'SOURCE_DISPOSITION_INVALID', section_id: item.section_id, reason: 'Unsupported disposition.' });
    const nodeIds = Array.isArray(item.node_ids) ? item.node_ids : [];
    const requirementIds = Array.isArray(item.requirement_ids) ? item.requirement_ids : [];
    if (nodeIds.some(id => !knownNodes.has(id))) findings.push({ code: 'SOURCE_DISPOSITION_NODE', section_id: item.section_id, reason: 'Disposition maps an unknown node.' });
    if (requirementIds.some(id => !knownRequirements.has(id) && !String(id).startsWith('observed_'))) findings.push({ code: 'SOURCE_DISPOSITION_REQUIREMENT', section_id: item.section_id, reason: 'Disposition maps an unknown requirement.' });
    if (section.authority === 'required' && !['workflow', 'conditional'].includes(item.disposition)) findings.push({ code: 'SOURCE_DISPOSITION_REQUIRED', section_id: item.section_id, reason: 'A required workflow/rule section cannot be reduced to reference-only or omitted.' });
    if (['workflow', 'conditional', 'reference'].includes(item.disposition) && nodeIds.length === 0 && requirementIds.length === 0) findings.push({ code: 'SOURCE_DISPOSITION_UNMAPPED', section_id: item.section_id, reason: 'A retained section must map to a graph node or source requirement.' });
    if (item.disposition === 'conditional' && !(typeof item.trigger === 'string' && item.trigger.trim())) findings.push({ code: 'SOURCE_DISPOSITION_TRIGGER', section_id: item.section_id, reason: 'A conditional section needs its source trigger.' });
    if (!(typeof item.rationale === 'string' && item.rationale.trim())) findings.push({ code: 'SOURCE_DISPOSITION_RATIONALE', section_id: item.section_id, reason: 'Every disposition needs a concise semantic rationale.' });
  }
  for (const section of inventory) if (!seen.has(section.section_id)) findings.push({ code: 'SOURCE_DISPOSITION_UNCLASSIFIED', section_id: section.section_id, reason: 'Source section has no disposition.' });
  return findings;
}

export function dispositionReport(proposal, resources) {
  const inventory = new Map(sourceSectionInventory(resources).map(item => [item.section_id, item]));
  return (proposal.source_dispositions ?? []).map(item => ({ ...structuredClone(item), title: inventory.get(item.section_id)?.title, source_span: structuredClone(inventory.get(item.section_id)?.source_span), authority: inventory.get(item.section_id)?.authority }));
}
