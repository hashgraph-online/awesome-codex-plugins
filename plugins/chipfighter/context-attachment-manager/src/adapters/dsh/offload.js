// Purpose: v0.11 — what the dsh plugin (index.js) decides, apart from dsh itself so it can be tested without it: which
// image occurrences to mark as offloaded, and whether a step starts a new turn.
// Input: a dsh session (eventAt, deriveEventMessage, append) and its surface's event sequence numbers. Output: one
// image/offload event.

// Marks up to `count` retained input images, in request order (assistant messages hold no input images). Image indexes
// count every image of a message, marked ones included, as dsh's own plugin does. False when none was left.
export function offloadImages(session, seqs, count) {
  const targets = [];
  for (const seq of seqs) {
    if (count <= 0) break;
    const event = session.eventAt(seq);
    if (!event || (event.type !== "user/message" && event.type !== "tool/result")) continue;
    const message = session.deriveEventMessage(event);
    if (!message) continue;
    const imageIndexes = [];
    let index = 0;
    for (const block of message.content) {
      if (count <= 0) break;
      if (block.type !== "image") continue;
      if (block.offloaded !== true) { imageIndexes.push(index); count--; }
      index++;
    }
    if (imageIndexes.length) targets.push({ seq, imageIndexes });
  }
  if (!targets.length) return false;
  session.append("image/offload", { targets });
  return true;
}

// A new turn starts when the agent's turn differs from the one it was last in (the first step seen counts too: on a
// resumed session every image on the surface is from before).
export function startsTurn(turnOf, agent, turn) {
  if (turnOf.get(agent) === turn) return false;
  turnOf.set(agent, turn);
  return true;
}
