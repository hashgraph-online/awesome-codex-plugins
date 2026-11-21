// Purpose: v0.11 — DeepSeek Harness (dsh): automatic selection as a dsh plugin, in place of dsh's own
// `@deepseek-ai/dsh-compaction-image-offload` (docs/v0.11/plan.md 3.9). dsh keeps an image's offload as a durable mark
// in the session log (an `image/offload` event); every later request shows that image to the model as text naming the
// attachment and a read-only path it can read the image back from. dsh's plugin marks the oldest images only when a
// route refuses a request as over its image budget. This one does the same, and also, as a new turn starts, marks every
// image of the turns before it — what automatic selection does on the other platforms. The model reads an image back
// through its path when it needs it; what it reads is a new occurrence, kept for that turn and marked when the next one
// starts. Marks never revert, so the provider's cached prefix only moves forward. No request goes through the engine.
// Packaged as a dsh bundle (package.json, cordis.patch.yml): installing it turns dsh's own row off and adds this one.
// JavaScript, not TypeScript: dsh loads it with its own runtime. Written against dsh's docs and the source of its
// image-offload plugin (agent/pre-step, agent/request-error, compaction/summary-error, image/offload); not tested live.
// Input: dsh's events. Output: image/offload events in the session log.

import { IMAGE_OFFLOAD_REQUIRED_CODE, LlmError } from "@deepseek-ai/dsh-llm";
import { imageOffloadProjection } from "@deepseek-ai/dsh-compaction-image-offload/projection";
import { offloadImages, startsTurn } from "./offload.js";

export const name = "context-attachment-manager";
export const inject = ["agents", "sessions"];

export function apply(ctx) {
  ctx.sessions.registerMessageProjection(imageOffloadProjection);
  // The turn each agent was last in: a different one means a new turn starts, and its user messages are not on the
  // surface yet, so every image there belongs to an earlier turn (on a resumed session too).
  const turnOf = new WeakMap();
  ctx.on("agent/pre-step", ({ agent, turn, signal }, next) => {
    if (!signal.aborted && startsTurn(turnOf, agent, turn)) offloadImages(agent.session, agent.session.surface.nodes, Number.POSITIVE_INFINITY);
    return next();
  });
  // As dsh's own plugin: a route that refuses the request as over its image budget names how many more to mark. Kept,
  // because one turn alone (a browser driven step by step) can pass the budget.
  ctx.on("agent/request-error", ({ agent, failure, signal }, next) => {
    if (failure.code !== IMAGE_OFFLOAD_REQUIRED_CODE || failure.offloadImages === undefined || signal.aborted) return next();
    if (!offloadImages(agent.session, agent.session.surface.nodes, failure.offloadImages)) return next();
    return Promise.resolve({ kind: "retry" });
  });
  ctx.on("compaction/summary-error", ({ session, sourceEventSeqs, error, signal }, next) => {
    if (!(error instanceof LlmError) || error.code !== IMAGE_OFFLOAD_REQUIRED_CODE || error.failure?.offloadImages === undefined) return next();
    signal?.throwIfAborted();
    if (!offloadImages(session, sourceEventSeqs, error.failure.offloadImages)) return next();
    return true;
  });
}
