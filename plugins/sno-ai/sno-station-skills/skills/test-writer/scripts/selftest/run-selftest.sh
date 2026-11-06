#!/usr/bin/env bash
# Deployable contract check for Test Writer's core testing principles.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$DIR/../../SKILL.md"
[ -f "$SOURCE" ] || { echo "cannot find SKILL.md above $DIR"; exit 2; }

fail=0

require() {
  if grep -Fq -- "$1" "$SOURCE"; then
    echo "PASS required: $1"
  else
    echo "FAIL missing: $1"
    fail=1
  fi
}

require "Write the best test code"
require "The output of this skill is test-owned code and the result of running it."
require "Everything should be real."
require "We hate mocking."
require "Assert observable results."
require "A test must catch a real defect."
require "Use realistic data."
require "Run the narrowest command that executes the changed test."

if [ "$fail" = 0 ]; then
  echo "test-writer selftest: PASS"
else
  echo "test-writer selftest: FAIL"
fi
exit "$fail"
