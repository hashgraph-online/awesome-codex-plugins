import assert from 'node:assert/strict';
import test from 'node:test';

import { parseOptions } from '../open-console.mjs';

test('one-click console CLI defaults to browser open and validates options', () => {
  assert.deepEqual(parseOptions([]), { port: 58712, open: true, help: false });
  assert.deepEqual(parseOptions(['--port', '0']), { port: 0, open: true, help: false });
  assert.deepEqual(parseOptions(['--port', '54321', '--no-open']), {
    port: 54321, open: false, help: false,
  });
  assert.deepEqual(parseOptions(['--help']), { port: 58712, open: true, help: true });
  assert.throws(() => parseOptions(['--port', '68712']), /between 0 and 65535/);
  assert.throws(() => parseOptions(['--unknown']), /unknown option/);
});
