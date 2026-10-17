/**
 * Shared intent plan schema — single source of truth used by:
 *  - register_intent_plan MCP tool (validates Codex's input)
 *  - register_intent_plan inputSchema (model sees this when invoking the tool)
 *
 * Codex has no ExitPlanMode-equivalent event, so unlike ArmorClaude there is
 * no plan-file extraction path on Codex.
 */

import { z } from "zod";

export const PLAN_STEP_SCHEMA = z.object({
  action: z.string().min(1).describe("Tool name (e.g. Read, Edit, Bash, mcp__server__tool)"),
  description: z.string().optional().describe("Why this step is needed"),
  metadata: z
    .object({
      inputs: z
        .record(z.string(), z.unknown())
        .optional()
        .describe("Expected tool parameters for enforcement")
    })
    .optional()
});

export const INTENT_PLAN_ZOD = z.object({
  goal: z.string().min(1).describe("One-line summary of what the plan accomplishes"),
  steps: z
    .array(PLAN_STEP_SCHEMA)
    .min(1)
    .describe("Ordered list of tool calls the agent intends to make")
});

/**
 * Human-readable format string injected into Codex's context so it knows
 * exactly what shape to produce.
 */
export const INTENT_PLAN_FORMAT = `{
  "goal": "<one-line summary of the task>",
  "steps": [
    {
      "action": "<ToolName e.g. Read, Edit, Bash, Grep, Glob, Write, WebFetch>",
      "description": "<why this step is needed>",
      "metadata": { "inputs": { /* expected tool parameters, optional */ } }
    }
  ]
}`;

/**
 * Normalize a validated plan into the internal format used by requestIntent()
 * and the plan enforcement pipeline.
 */
export function normalizeIntentPlan(parsed) {
  return {
    steps: parsed.steps.map((s) => ({
      // Both `action` and `tool` are populated to match the backend's
      // CSRG/policy enforcer expectations: the SDK's invoke() does the
      // same (sets tool: action). The backend hashes `step.tool` for
      // policy paths like /steps/[i]/tool.
      action: s.action,
      tool: s.action,
      mcp: "codex",
      description: s.description || "",
      metadata: s.metadata || {}
    })),
    metadata: {
      goal: parsed.goal,
      source: "codex-registered"
    }
  };
}
