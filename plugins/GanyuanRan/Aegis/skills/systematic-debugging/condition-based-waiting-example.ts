// Complete implementation of condition-based waiting utilities
// From: Lace test infrastructure improvements (2025-10-03)
// Context: Fixed 15 flaky tests by replacing arbitrary timeouts

import type { ThreadManager } from '~/threads/thread-manager';
import type { LaceEvent, LaceEventType } from '~/threads/types';

// A timer callback runs after the Promise executor has returned, so every
// poll must explicitly convert getter/predicate exceptions into rejection.
function pollUntil<T>(
  read: () => T | undefined,
  timeoutMessage: () => string,
  timeoutMs: number
): Promise<T> {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    const check = () => {
      try {
        const result = read();
        if (result !== undefined) {
          resolve(result);
        } else if (Date.now() - startTime >= timeoutMs) {
          reject(new Error(timeoutMessage()));
        } else {
          setTimeout(check, 10);
        }
      } catch (error) {
        reject(error);
      }
    };
    check();
  });
}

/**
 * Wait for a specific event type to appear in thread
 *
 * @param threadManager - The thread manager to query
 * @param threadId - Thread to check for events
 * @param eventType - Type of event to wait for
 * @param timeoutMs - Maximum time to wait (default 5000ms)
 * @returns Promise resolving to the first matching event
 *
 * Example:
 *   await waitForEvent(threadManager, agentThreadId, 'TOOL_RESULT');
 */
export function waitForEvent(
  threadManager: ThreadManager,
  threadId: string,
  eventType: LaceEventType,
  timeoutMs = 5000
): Promise<LaceEvent> {
  return pollUntil(
    () => threadManager.getEvents(threadId).find((e) => e.type === eventType),
    () => `Timeout waiting for ${eventType} event after ${timeoutMs}ms`,
    timeoutMs
  );
}

/**
 * Wait for a specific number of events of a given type
 *
 * @param threadManager - The thread manager to query
 * @param threadId - Thread to check for events
 * @param eventType - Type of event to wait for
 * @param count - Number of events to wait for
 * @param timeoutMs - Maximum time to wait (default 5000ms)
 * @returns Promise resolving to all matching events once count is reached
 *
 * Example:
 *   // Wait for 2 AGENT_MESSAGE events (initial response + continuation)
 *   await waitForEventCount(threadManager, agentThreadId, 'AGENT_MESSAGE', 2);
 */
export function waitForEventCount(
  threadManager: ThreadManager,
  threadId: string,
  eventType: LaceEventType,
  count: number,
  timeoutMs = 5000
): Promise<LaceEvent[]> {
  let observedCount = 0;
  return pollUntil(
    () => {
      const matches = threadManager.getEvents(threadId).filter((e) => e.type === eventType);
      observedCount = matches.length;
      return observedCount >= count ? matches : undefined;
    },
    () => `Timeout waiting for ${count} ${eventType} events after ${timeoutMs}ms (got ${observedCount})`,
    timeoutMs
  );
}

/**
 * Wait for an event matching a custom predicate
 * Useful when you need to check event data, not just type
 *
 * @param threadManager - The thread manager to query
 * @param threadId - Thread to check for events
 * @param predicate - Function that returns true when event matches
 * @param description - Human-readable description for error messages
 * @param timeoutMs - Maximum time to wait (default 5000ms)
 * @returns Promise resolving to the first matching event
 *
 * Example:
 *   // Wait for TOOL_RESULT with specific ID
 *   await waitForEventMatch(
 *     threadManager,
 *     agentThreadId,
 *     (e) => e.type === 'TOOL_RESULT' && e.data.id === 'call_123',
 *     'TOOL_RESULT with id=call_123'
 *   );
 */
export function waitForEventMatch(
  threadManager: ThreadManager,
  threadId: string,
  predicate: (event: LaceEvent) => boolean,
  description: string,
  timeoutMs = 5000
): Promise<LaceEvent> {
  return pollUntil(
    () => threadManager.getEvents(threadId).find(predicate),
    () => `Timeout waiting for ${description} after ${timeoutMs}ms`,
    timeoutMs
  );
}

// Usage example from actual debugging session:
//
// BEFORE (flaky):
// ---------------
// const messagePromise = agent.sendMessage('Execute tools');
// await new Promise(r => setTimeout(r, 300)); // Hope tools start in 300ms
// agent.abort();
// await messagePromise;
// await new Promise(r => setTimeout(r, 50));  // Hope results arrive in 50ms
// expect(toolResults.length).toBe(2);         // Fails randomly
//
// AFTER (reliable):
// ----------------
// const messagePromise = agent.sendMessage('Execute tools');
// await waitForEventCount(threadManager, threadId, 'TOOL_CALL', 2); // Wait for tools to start
// agent.abort();
// await messagePromise;
// await waitForEventCount(threadManager, threadId, 'TOOL_RESULT', 2); // Wait for results
// expect(toolResults.length).toBe(2); // Always succeeds
//
// Result: 60% pass rate → 100%, 40% faster execution
