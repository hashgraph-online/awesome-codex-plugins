import { requireValue } from '../workflow-paths.mjs';

function boundedIdentity(value, field) {
  requireValue(typeof value === 'string' && value.length > 0 && value.length <= 256, 'MAIN_SESSION_IDENTITY', `Main semantic receipt needs ${field}`);
  return value;
}

/** A host attestation, not a claim that the remote model is isolated. */
export function mainSessionIdentity(receipt, mainActor) {
  requireValue(receipt && typeof receipt === 'object' && !Array.isArray(receipt), 'MAIN_SESSION_IDENTITY', 'Main semantic receipt must be an object');
  const identity = {
    session_id: boundedIdentity(receipt.session_id, 'session_id'),
    call_chain_id: boundedIdentity(receipt.call_chain_id, 'call_chain_id'),
    main_actor: boundedIdentity(receipt.main_actor, 'main_actor'),
  };
  requireValue(identity.main_actor === mainActor, 'MAIN_SESSION_IDENTITY', 'Main semantic receipt belongs to a different main actor');
  return identity;
}

export function sameMainSession(left, right) {
  return left?.session_id === right.session_id && left?.call_chain_id === right.call_chain_id && left?.main_actor === right.main_actor;
}
