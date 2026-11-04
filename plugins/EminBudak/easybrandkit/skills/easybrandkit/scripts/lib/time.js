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

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

module.exports = { setTimeLimit, timeLeft, sleep };
