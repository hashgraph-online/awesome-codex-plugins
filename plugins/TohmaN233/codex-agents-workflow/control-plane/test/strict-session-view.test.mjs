import assert from 'node:assert/strict';
import test from 'node:test';
import { strictSessionPresentation } from '../web-src/strict-session-view.mjs';

const node = (status, sessionStatus, id = 'attempt-a') => ({ status,
  attempts: [{ id, dispatch: { receipt: { executor: 'codex-app-server' } },
    executor_events: [{ kind: 'session_state', metadata: { status: 'running' } },
      { kind: 'session_state', metadata: { status: sessionStatus } }] }],
});

test('terminal journal overrides a stale running session snapshot after automatic completion', () => {
  const view = strictSessionPresentation(node('succeeded', 'closed'), {
    attempt_id: 'attempt-a', value: { status: 'running', output_preview: { text: 'partial' } },
  });
  assert.equal(view.status, 'closed');
  assert.equal(view.show_login, false);
});

test('switching attempts never displays another attempt preview or login state', () => {
  const view = strictSessionPresentation(node('running', 'auth_required', 'attempt-b'), {
    attempt_id: 'attempt-a', value: { status: 'running', output_preview: { text: 'other task' } },
  });
  assert.equal(view.status, 'auth_required');
  assert.equal(view.output_preview, undefined);
  assert.equal(view.show_login, true);
});

test('closed finalizer awaits main acceptance but does not retain its login link', () => {
  const view = strictSessionPresentation(node('running', 'closed'), null);
  assert.equal(view.status, 'closed');
  assert.equal(view.show_login, false);
});

test('non-Strict nodes never display an old Strict session', () => {
  assert.equal(strictSessionPresentation({ status: 'ready', attempts: [] }, {
    attempt_id: 'attempt-a', value: { status: 'running' },
  }), null);
});

test('an unavailable active session preserves its diagnostic error', () => {
  const view = strictSessionPresentation(node('running', 'running'), {
    attempt_id: 'attempt-a', value: { status: 'unavailable', error: 'Session process no longer exists' },
  });
  assert.equal(view.status, 'unavailable');
  assert.equal(view.error, 'Session process no longer exists');
  assert.equal(view.show_login, false);
});
