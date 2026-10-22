import { createHmac } from 'node:crypto';
import { nodePermissions } from './workflow-execution-envelope.mjs';
import { effectiveSkillPolicy } from './workflow-reference-schema.mjs';
import { skillPathKey } from './execution/codex-skill-policy.mjs';
import { requireValue } from './workflow-paths.mjs';
import { digest } from './workflow-revisions.mjs';

export function childIdentity(runId, nodeId, attemptId, controlToken) {
  const identity = [runId, nodeId, attemptId].join('\0');
  return { run_id: 'child-' + digest(identity).slice(0, 58), control_token: createHmac('sha256', controlToken).update('subworkflow\0' + identity).digest('hex') };
}

export function childPermissions(node, state, parentPins, child) {
  const permissions = { workspace: state.permissions.workspace, ...nodePermissions(node, state) };
  const parentPolicy = effectiveSkillPolicy(parentPins.inherited_policy ?? parentPins.root.workflow.skill_policy, node.skill_policy);
  const policy = effectiveSkillPolicy(parentPolicy, child.workflow.skill_policy);
  // Explicit references are grants too. A child cannot turn a parent's denied
  // Skill into an explicit injection merely by referencing another saved Pack.
  const allowed = new Set(parentPolicy.ambient_allow.map(skillPathKey));
  const shadowed = new Set(policy.shadowed_skill_paths.map(skillPathKey));
  for (const definition of child.workflow.nodes) {
    if (definition.skill_policy) effectiveSkillPolicy(policy, definition.skill_policy);
    if (definition.type === 'skill_ref') for (const skill of [definition.skill_ref, ...definition.skill_ref.allowed_nested_skills]) {
      requireValue(allowed.has(skillPathKey(skill.path)) && !shadowed.has(skillPathKey(skill.path)), 'CHILD_SKILL_ESCALATION', 'Child SkillRef exceeds its parent Skill allowance');
    }
    if (['agent', 'skill_ref', 'tool', 'human_gate', 'subworkflow'].includes(definition.type)) nodePermissions(definition, { permissions });
  }
  return { permissions, policy, require_approval: Boolean(state.require_approval || node.approval.required) };
}

export function validateChildClosure(pins, state) {
  let visited = 0; const contexts = [];
  function visit(current, currentState, depth) {
    requireValue(depth <= 32 && ++visited <= 4096, 'SUBWORKFLOW_CONTEXT_LIMIT', 'Child permission contexts exceed their bounded limit');
    contexts.push({ pack: current.root, state: currentState });
    for (const node of current.root.workflow.nodes.filter(node => node.type === 'subworkflow')) {
      const child = current.children[node.subworkflow.workflow_id + '@' + node.subworkflow.revision_pin];
      requireValue(child, 'SUBWORKFLOW_PIN_MISSING', 'Child definition was not pinned');
      const inherited = childPermissions(node, currentState, current, child);
      visit({ ...current, root: child, inherited_policy: inherited.policy }, { ...currentState, permissions: inherited.permissions, require_approval: inherited.require_approval }, depth + 1);
    }
  }
  visit(pins, state, 0);
  return contexts;
}
