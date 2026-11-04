import test from 'node:test';
import assert from 'node:assert/strict';
import { parseConfig } from '../lib/config.mjs';

const ok = (text) => parseConfig(text, 'm.cfg');
const refusal = (text, re) => assert.throws(() => ok(text), re);

test('reads rules, deadlock flag, and written sections', () => {
  const c = ok('CONSTANTS N = 3 S = {a, b, {}} M <- Other\nINIT Init NEXT Next\nINVARIANTS A B\nPROPERTY P\nCONSTRAINT C\nCHECK_DEADLOCK FALSE\n');
  assert.deepEqual(c.invariants, ['A', 'B']);
  assert.deepEqual(c.properties, ['P']);
  assert.equal(c.checkDeadlock, false);
  assert.deepEqual(c.constraints, ['C']);
  assert.equal(c.substitutions.get('M'), 'Other');
  assert.equal(c.written, 'CONSTANTS N = 3 S = { a , b , { } } M <- Other\nINIT Init\nNEXT Next\nCONSTRAINT C');
});

test('deadlock is checked by default', () => {
  assert.equal(ok('SPECIFICATION Spec').checkDeadlock, true);
});

test('comments: line, nested block, and strings keep comment text', () => {
  const c = ok('(* outer (* inner INVARIANT Hidden *) still *)\nSPECIFICATION Spec \\* INVARIANT Gone\nCONSTANT s = "(* not a comment \\\\* INVARIANT"\n');
  assert.deepEqual(c.invariants, []);
  assert.match(c.written, /"\(\* not a comment \\\\\* INVARIANT"/);
});

test('TYPE and TYPE_CONSTRAINT are keywords', () => {
  const c = ok('SPECIFICATION Spec\nTYPE T\nTYPE_CONSTRAINT TC\n');
  assert.match(c.written, /TYPE T\nTYPE_CONSTRAINT TC/);
});

test('operator constants with arguments and module overrides', () => {
  const c = ok('CONSTANT F(1, "x") = 2\nCONSTANT G = [Mod] h\nCONSTANT a!b <- [Mod] c\nINIT I NEXT N');
  assert.match(c.written, /F \( 1 , "x" \) = 2/);
});

test('refusals name the right line', () => {
  refusal('INITT Init\nNEXT Next', /TLC refuses the config m.cfg at line 1: expecting a keyword/);
  refusal('INIT Init\nNEXT Next\nCHECK_DEADLOCK false', /TLC refuses .* at line 3: CHECK_DEADLOCK takes TRUE or FALSE/);
  refusal('INIT Init\nNEXT Next\nALIAS A', /cannot read the config m.cfg at line 3: the ALIAS section/);
  refusal('INIT Init\nNEXT Next\nINVARIANT A, B', /TLC refuses .* at line 3: , is not defined/);
  refusal('INIT Init\nINIT Other\nNEXT Next', /line 2: INIT appears twice/);
  refusal('INIT Init\nNEXT Next\nCONSTANT N = -1', /cannot read .* at line 3: - is not allowed|cannot read .* at line 3/);
  refusal('SPECIFICATION Spec\nNEXT Next', /both SPECIFICATION and INIT\/NEXT/);
  refusal('NEXT Next', /neither SPECIFICATION nor INIT/);
  refusal('INIT I NEXT N\nCONSTANT\nF() = 1', /at line 2: TLC stops here without giving a reason/);
  refusal('INIT I NEXT N\nCONSTANT F(1 = 1', /at line 2: TLC stops here without giving a reason/);
  refusal('INIT I NEXT N\nINVARIANT A, B\nCHECK_DEADLOCK maybe', /line 3: CHECK_DEADLOCK takes/);
  refusal('INIT I NEXT N\n(* never closed\nINVARIANT X', /at line 2: a comment that starts here/);
  refusal('INIT I NEXT N\n(* CHECK_DEADLOCK FALSE', /at line 2: a comment/);
  refusal('INIT I\u00a0NEXT N', /"\u00a0" \(U\+00A0\)/);
  refusal('INIT I\u2028NEXT N', /U\+2028/);
  refusal('\ufeffINIT I NEXT N', /byte order mark/);
  refusal('INIT I NEXT N\nCONSTANT N = 2147483648', /larger than 2147483647/);
  refusal('INIT I NEXT N\nINVARIANT WF_x', /fairness keyword/);
  refusal('INIT I NEXT N\nCONSTANT N = 1_2', /mixes digits and underscores/);
  refusal('INIT I NEXT N\nINVARIANT A == B', /TLA\+ symbol ==/);
  refusal('INIT I NEXT N\nCONSTANT s = "a\\qb"', /escape \\q/);
  refusal('INIT I NEXT N\nCONSTANT N = INVARIANT', /keyword INVARIANT stands where a value belongs/);
  refusal('INIT', /ends where the name after INIT belongs/);
  refusal('INIT I NEXT N\nCONSTANT \u0001', /U\+0001/);
});

test('a later structural error wins over an earlier name problem', () => {
  refusal('INIT I NEXT N\nINVARIANT 1\nINIT J', /line 3: INIT appears twice/);
});

test('CRLF and lone CR count as line breaks', () => {
  refusal('INIT I\r\nNEXT N\rCHECK_DEADLOCK x', /at line 3/);
});
