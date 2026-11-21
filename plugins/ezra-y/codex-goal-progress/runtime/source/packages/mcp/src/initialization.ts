import { createHash } from "node:crypto";
import type { z } from "zod";
import {
  GoalContractIdSchema,
  type GoalContractInitialization,
  GoalContractInitializationSchema,
} from "../../contracts/src/index.js";

export const GoalProgressInitializeBusinessSchema = GoalContractInitializationSchema.extend({
  contractId: GoalContractIdSchema.optional().describe(
    "Omit on initialize; plugin generates this gp_ ID.",
  ),
});

export function completeInitialization(
  input: z.infer<typeof GoalProgressInitializeBusinessSchema>,
  identity: { readonly sessionId: string; readonly callId: string },
): GoalContractInitialization {
  // The same authorized call produces the same ID, including after an MCP restart.
  const contractId =
    input.contractId ??
    `gp_${createHash("sha256")
      .update(JSON.stringify([identity.sessionId, identity.callId]))
      .digest("hex")}`;
  return { ...input, contractId };
}
