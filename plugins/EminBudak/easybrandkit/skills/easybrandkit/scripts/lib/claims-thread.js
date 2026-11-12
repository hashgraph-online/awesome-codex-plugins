"use strict";

// findClaims on a thread of its own (see claimsOf in facts.js).

const { parentPort, workerData } = require("worker_threads");
const { findClaims } = require("./claims");

parentPort.postMessage(findClaims(workerData));
