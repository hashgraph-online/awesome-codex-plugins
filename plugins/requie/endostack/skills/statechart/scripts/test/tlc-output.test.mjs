import test from 'node:test';
import assert from 'node:assert/strict';
import { renderPlainText, formatDuration, parseMessages, runFacts, trace, actionName } from '../lib/tlc-output.mjs';

const msg = (code, level, ...lines) => [`@!@!@STARTMSG ${code}:${level} @!@!@`, ...lines, `@!@!@ENDMSG ${code} @!@!@`].join('\n');

test('prefixes by level, warning hint once, SANY markers dropped', () => {
  const text = [
    msg(2262, 0, 'TLC2 Version 2.19'),
    msg(2401, 3, 'Please use the parallel GC.'),
    msg(2220, 0, 'Starting SANY...'),
    'Parsing file /x/M.tla',
    msg(2219, 0, 'SANY finished.'),
    msg(2110, 1, 'Invariant Inv is violated.'),
    msg(2121, 1, 'The behavior up to this point is:'),
    msg(2217, 4, '1: <Initial predicate>', 'x = 0', ''),
    msg(2401, 3, 'Another warning.'),
    msg(1000, 2, 'Something internal.'),
    '',
  ].join('\n');
  assert.equal(renderPlainText(text), [
    'TLC2 Version 2.19',
    'Warning: Please use the parallel GC.',
    '(Use the -nowarning option to disable this warning.)',
    'Parsing file /x/M.tla',
    'Error: Invariant Inv is violated.',
    'Error: The behavior up to this point is:',
    'State 1: <Initial predicate>',
    'x = 0',
    '',
    'Warning: Another warning.',
    'TLC Bug: Something internal.',
    '',
  ].join('\n'));
});

test('progress before final statistics is dropped, otherwise kept', () => {
  const a = [msg(2200, 0, 'Progress(3) at t: 4 states'), msg(2199, 0, '4 states generated'), ''].join('\n');
  assert.equal(renderPlainText(a), '4 states generated\n');
  const b = [msg(2200, 0, 'Progress(3) at t: 4 states'), msg(2186, 0, 'Finished in 12ms at (t)'), ''].join('\n');
  assert.equal(renderPlainText(b), 'Progress(3) at t: 4 states\nFinished in 00s at (t)\n');
});

test('nested messages and an end marker closing the innermost message', () => {
  const text = ['@!@!@STARTMSG 2102:1 @!@!@', '@!@!@STARTMSG 2154:0 @!@!@', 'inner', '@!@!@ENDMSG 9999 @!@!@', 'outer tail', '@!@!@ENDMSG 2102 @!@!@', ''].join('\n');
  assert.equal(renderPlainText(text), 'Error: inner\nouter tail\n');
});

test('a message starting mid-line keeps the text before it on that line', () => {
  const text = ['partial line @!@!@STARTMSG 2110:1 @!@!@', 'Invariant I is violated.', '@!@!@ENDMSG 2110 @!@!@', ''].join('\n');
  assert.equal(renderPlainText(text), 'partial line Error: Invariant I is violated.\n');
});

test('output cut mid-message prints like plain TLC cut at the same point', () => {
  const text = [msg(2185, 0, 'Starting...'), '@!@!@STARTMSG 2217:4 @!@!@', '1: <Initial predicate>', 'x = '].join('\n');
  assert.equal(renderPlainText(text), 'Starting...\nState 1: <Initial predicate>\nx = ');
});

test('back-to-state line takes the plain form', () => {
  const text = [msg(2122, 4, '1: Back to state: <Stop line 1, col 1 to line 1, col 9 of module M>'), ''].join('\n');
  assert.equal(renderPlainText(text), 'Back to state 1: <Stop line 1, col 1 to line 1, col 9 of module M>\n');
});

test('durations format like TLC', () => {
  assert.equal(formatDuration(450), '00s');
  assert.equal(formatDuration(9000), '09s');
  assert.equal(formatDuration(61000), '01min 01s');
  assert.equal(formatDuration(3600000 + 5 * 60000), '01h 05min');
  assert.equal(formatDuration(26 * 3600000), '1d 02h');
});

test('facts: broken rule kinds, counts with commas', () => {
  const f = runFacts(parseMessages([msg(2190, 0, 'Finished computing initial states: 2 distinct states generated at t.'), msg(2107, 1, 'Invariant A is violated by the initial state:', 'x = 0'), msg(2199, 0, '9 states generated, 1,234 distinct states found, 0 states left on queue.')].join('\n')));
  assert.deepEqual([f.broken.kind, f.broken.name, f.initial, f.distinct], ['invariant', 'A', 2, 1234]);
  assert.equal(runFacts(parseMessages(msg(2114, 1, 'Deadlock reached.'))).broken.kind, 'deadlock');
  assert.equal(runFacts(parseMessages(msg(2116, 1, 'Temporal properties were violated.'))).broken.kind, 'temporal');
  assert.equal(runFacts(parseMessages(msg(2112, 1, 'Action property P is violated.'))).broken.name, 'P');
  assert.equal(runFacts(parseMessages(msg(2108, 1, 'Property Q is violated by the initial state:'))).broken.name, 'Q');
});

test('trace reads states, loop back, and stuttering', () => {
  const t = trace(parseMessages([
    msg(2217, 4, '1: <Initial predicate>', 'x = 0', ''),
    msg(2217, 4, '2: <A!Step line 3, col 1 to line 3, col 9 of module M>', 'x = 1', ''),
    msg(2122, 4, '1: Back to state: <Back line 4, col 1 to line 4, col 9 of module M>'),
  ].join('\n')));
  assert.deepEqual(t.states.map((s) => s.action), [null, 'A!Step']);
  assert.deepEqual(t.loopBack, { index: 0, action: 'Back' });
  const s = trace(parseMessages([msg(2217, 4, '1: <Initial predicate>', 'x = 0'), msg(2218, 4, '2: Stuttering')].join('\n')));
  assert.equal(s.stutter, true);
  assert.equal(actionName('<Go line 5, col 7 to line 5, col 39 of module Loop>'), 'Go');
});
