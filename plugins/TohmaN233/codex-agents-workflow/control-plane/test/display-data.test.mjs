import test from 'node:test';
import assert from 'node:assert/strict';
import { displayDetails } from '../web-src/display-data.mjs';

test('diagnostics hide nested Run and lease capabilities without changing execution data', () => {
  const value = { child: { control_token: 'example-controller-secret', nodes: [{ lease_token: 'example-lease-secret', output: { count: 2 } }] }, revision_hash: 'public-hash' };
  const before = JSON.stringify(value);
  const display = displayDetails(value);
  assert(!display.includes('example-controller-secret'));
  assert(!display.includes('example-lease-secret'));
  assert(display.includes('public-hash'));
  assert.equal(JSON.parse(display).child.nodes[0].output.count, 2);
  assert.equal(JSON.stringify(value), before);
});
