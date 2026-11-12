"use strict";

// readSnapshot on a thread of its own (see findLogos in logos.js).

const { parentPort, workerData } = require("worker_threads");
const { readSnapshot } = require("./logos");

parentPort.postMessage(readSnapshot(workerData));
