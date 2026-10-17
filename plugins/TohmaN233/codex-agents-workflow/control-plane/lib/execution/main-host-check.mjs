import { requireValue } from '../workflow-paths.mjs';
import { validateData } from '../workflow-data-schema.mjs';
import { requireHostToolExecutionScope } from './host-tool-runner.mjs';
import { isOrchestrationMain } from './main-execution-mode.mjs';
import { semanticResultSchema } from './host-main-automation.mjs';
import { resolveBindings } from '../workflow-bindings.mjs';
import {canonicalJSON} from '../workflow-revisions.mjs';
import {validateTextAmendmentDeclaration} from './native-text-amendment.mjs';

const annotations = new Set(['title', 'description', 'default', 'examples']);
const unconstrained = schema => Object.keys(schema ?? {}).every(key => annotations.has(key));
const object = value => value && typeof value === 'object' && !Array.isArray(value);

/** Completion data stays in the pinned graph/journal, outside model projection. */
export function hostCompletionBindings(node) {
  const check=node.completion_contract?.host_check;
  if(!check||!Object.hasOwn(check,'input_bindings'))return node.input_bindings??{};
  requireValue(object(check.input_bindings),'MAIN_ORCHESTRATION_HOST_CHECK_CONTRACT','Host completion input_bindings must be an explicit binding map');
  return check.input_bindings;
}

export function hostCompletionInputs(node, context, legacyInputs) {
  return node.completion_contract?.host_check&&Object.hasOwn(node.completion_contract.host_check,'input_bindings')
    ? resolveBindings(hostCompletionBindings(node),context) : legacyInputs;
}

export function preflightHostCompletionInputs(node, context, legacyInputs, contracts) {
  const check=node.completion_contract?.host_check;
  if(!check)return;
  const contract=contracts.get(check.tool);
  requireValue(contract,'MAIN_ORCHESTRATION_HOST_CHECK_TOOL','Host completion check lost its pinned tool contract');
  // Resolve and validate before model handoff. A missing mechanical input is
  // a Host binding error, not a semantic turn the model can repair.
  validateData(hostCompletionInputs(node,context,legacyInputs),contract.input_schema.properties.inputs);
}

// Prove inclusion in the supported finite schema vocabulary. Unknown producer
// values may flow into an unconstrained consumer only; never guess compatibility.
export function schemaAcceptedBy(source = {}, target = {}) {
  if (unconstrained(target)) return true;
  const literals = Object.hasOwn(source, 'const') ? [source.const] : source.enum;
  if (literals) return literals.every(value => { try { validateData(value, target); return true; } catch { return false; } });
  if (Object.hasOwn(target, 'const') || target.enum) return false;
  if (target.type && source.type !== target.type && !(source.type === 'integer' && target.type === 'number')) return false;
  for (const [min, max] of [['minLength','maxLength'], ['minItems','maxItems'], ['minimum','maximum']]) {
    if (target[min] !== undefined && (source[min] ?? (min === 'minimum' ? -Infinity : 0)) < target[min]) return false;
    if (target[max] !== undefined && (source[max] ?? Infinity) > target[max]) return false;
  }
  if (target.exclusiveMinimum !== undefined && !((source.exclusiveMinimum ?? -Infinity) >= target.exclusiveMinimum
    || (source.minimum ?? -Infinity) > target.exclusiveMinimum)) return false;
  if (target.pattern !== undefined && source.pattern !== target.pattern) return false;
  if (target.uniqueItems === true && source.uniqueItems !== true) return false;
  if (target.required?.some(name => !(source.required ?? []).includes(name))) return false;
  for (const [name, schema] of Object.entries(source.properties ?? {})) {
    const accepted = target.properties?.[name] ?? target.additionalProperties ?? {};
    if (accepted === false || object(accepted) && !schemaAcceptedBy(schema, accepted)) return false;
  }
  for (const [name, schema] of Object.entries(target.properties ?? {})) {
    if (Object.hasOwn(source.properties ?? {}, name) || source.additionalProperties === false) continue;
    if (!schemaAcceptedBy(object(source.additionalProperties) ? source.additionalProperties : {}, schema)) return false;
  }
  if (source.additionalProperties !== false) {
    if (target.additionalProperties === false) return false;
    if (object(target.additionalProperties) && !schemaAcceptedBy(object(source.additionalProperties) ? source.additionalProperties : {}, target.additionalProperties)) return false;
  }
  if (target.items && !schemaAcceptedBy(source.items ?? {}, target.items)) return false;
  return true;
}

export function validateMainHostCheck(node, contracts, inputSchemas, nativeWorker = false) {
  const check = node.completion_contract?.host_check;
  if (check === undefined) return;
  const worker = nativeWorker || node.executor?.kind === 'main' && !isOrchestrationMain(node);
  requireValue(['agent','skill_ref'].includes(node.type) && (node.executor?.kind === 'main'||nativeWorker) && node.access === 'bounded_write', 'MAIN_ORCHESTRATION_HOST_CHECK_MODE',
    'Host completion checks require a writable Main or Cooperative native worker');
  requireValue(!nativeWorker||!node.fanout||node.fanout.result_mode==='per_item'&&node.fanout.workspace_field&&node.fanout.write_paths_field,
    'NATIVE_HOST_CHECK_FANOUT','Native fan-out checks require per-item results and complete item workspace grants');
  requireValue(!nativeWorker||node.fanout||node.subagent_count===undefined||node.subagent_count===1,
    'NATIVE_HOST_CHECK_FANOUT','Multiple checked native children require explicit per-item fan-out');
  requireValue(object(check) && typeof check.tool === 'string'
    && typeof check.success_field === 'string' && Object.keys(check).every(key => ['tool','success_field','correction_field','input_bindings','text_amendment'].includes(key)),
    'MAIN_ORCHESTRATION_HOST_CHECK_CONTRACT', 'Host completion check needs tool, success_field and optional exact input_bindings');
  hostCompletionBindings(node);
  const contract = contracts.get(check.tool);
  requireValue(contract, 'MAIN_ORCHESTRATION_HOST_CHECK_TOOL', 'Host completion check must name a pinned registered tool');
  validateTextAmendmentDeclaration(node,contract,nativeWorker);
  requireValue(contract.output_schema?.type === 'object' && contract.output_schema?.properties?.[check.success_field]?.type === 'boolean'
    && (contract.output_schema.required ?? []).includes(check.success_field), 'MAIN_ORCHESTRATION_HOST_CHECK_SUCCESS',
    'Host completion success_field must name a required boolean tool output');
  requireValue((!worker && check.correction_field === undefined) || typeof check.correction_field === 'string'
    && contract.output_schema?.properties?.[check.correction_field]?.type === 'string'
    && (contract.output_schema.required ?? []).includes(check.correction_field), 'MAIN_WORKER_HOST_CHECK_CORRECTION',
    'Worker Host completion correction_field must name a required string tool output');
  const schema = contract.input_schema;
  requireValue(schema.type === 'object' && object(schema.properties?.inputs) && object(schema.properties?.output)
    && ['inputs','output'].every(name => (schema.required ?? []).includes(name))
    && (schema.required ?? []).every(name => ['inputs','output'].includes(name)), 'MAIN_ORCHESTRATION_HOST_CHECK_SCHEMA',
    'Host completion input schema must accept exactly the projected inputs and semantic output');
  const semanticSchema = node.fanout && worker ? node.outputs_schema.properties[node.fanout.result_output].items : semanticResultSchema(node);
  requireValue(schemaAcceptedBy(semanticSchema, schema.properties.output), 'MAIN_ORCHESTRATION_HOST_CHECK_SCHEMA',
    'Host completion check output input is incompatible with the semantic node output');
  if (worker && node.fanout) inputSchemas = Object.fromEntries(Object.entries(inputSchemas).map(([name, alternatives]) =>
    [name, alternatives.map(schema => schema.type === 'array' && canonicalJSON(hostCompletionBindings(node)[name])===canonicalJSON(node.input_bindings[node.fanout.input]) ? {...schema,minItems:1,maxItems:1} : schema)]));
  const properties = Object.fromEntries(Object.entries(inputSchemas).map(([name, alternatives]) => [name, alternatives[0] ?? {}]));
  const projected = { type: 'object', properties, required: Object.keys(properties), additionalProperties: false };
  requireValue(schemaAcceptedBy({ type:'object', properties:{ inputs:projected, output:semanticSchema },
    required:['inputs','output'],additionalProperties:false }, schema), 'MAIN_ORCHESTRATION_HOST_CHECK_SCHEMA',
    'Host completion input schema imposes incompatible envelope constraints');
  requireValue(schemaAcceptedBy(projected, schema.properties.inputs), 'MAIN_ORCHESTRATION_HOST_CHECK_SCHEMA',
    'Host completion check inputs input is incompatible with the projected node bindings');
  for (const [name, alternatives] of Object.entries(inputSchemas)) for (const alternative of alternatives) {
    const consumer = schema.properties.inputs.properties?.[name] ?? schema.properties.inputs.additionalProperties ?? {};
    requireValue(consumer !== false && schemaAcceptedBy(alternative, consumer === true ? {} : consumer),
      'MAIN_ORCHESTRATION_HOST_CHECK_SCHEMA', `Host completion binding is incompatible: ${name}`);
  }
  // A dynamic Run grant is intersected again at startup, before any model work.
  if (Array.isArray(node.path_scope)) requireHostToolExecutionScope(contract, { access: node.access, allowed_paths: worker && node.fanout ? ['.'] : node.path_scope });
}
