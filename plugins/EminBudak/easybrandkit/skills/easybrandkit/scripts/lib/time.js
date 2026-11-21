"use strict";

// One deadline for the whole run. Every wait and every browser call takes
// what is left of it, so a slow or broken site ends with a clear error
// instead of a hang.
let deadline = Date.now() + 120_000;

function setTimeLimit(ms) {
  deadline = Date.now() + ms;
}

function timeLeft() {
  return deadline - Date.now();
}

// Whether the run has used up its own time, so that more of it can help: one
// call's own limit does not change with --timeout.
const outOfTime = () => timeLeft() < 2_000;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// A timer longer than this goes off at once, and a program that calls makeKit
// can give it any time limit.
const LONGEST_TIMER = 2 ** 31 - 1;

module.exports = { setTimeLimit, timeLeft, outOfTime, sleep, LONGEST_TIMER };
