"use strict";

// How a run connects to a host: the browser's requests through the kit's
// proxy (see proxy.js) and the kit's own requests alike (see stores.js and
// facts.js), each to the addresses the run's rule took for that host (see
// address.js route) and to no other. A host with more than one address is
// connected to with each attempt left to go on until it connects or fails,
// as the browser leaves its own: one attempt per address, the families
// taking turns, the next started 250 ms after the one before, or at once
// when every one started before it has failed. The first to connect is
// taken and the others are ended. Node's own connection to more than one
// address ends every attempt but the last after 250 ms, so a public site
// whose name has an IPv6 address this machine has no route to, and whose
// IPv4 address takes longer than that to answer, as a site far away does,
// failed with ETIMEDOUT, and so did a site of this machine given as
// localhost while this process was held a moment, where the browser by
// itself connects.

const net = require("net");
const tls = require("tls");

// Where each connection to one address is made: the one place a run makes
// one. name is the host the connection is for, a name or the address
// itself. Tests put their own servers in place of the addresses here.
// Nagle's algorithm is off on it, as the browser has it on its own
// connections: with it on, the browser's small writes through the proxy,
// as the frames of HTTP/2 and the records of TLS, could wait for the site
// to acknowledge the one before, and a page loaded more slowly than the
// browser loads it by itself.
const wire = { dial: (address, port, name) => net.connect({ host: address, port, autoSelectFamily: false, noDelay: true }) };

// How long an attempt is waited for before the next one starts, as RFC 8305
// has it.
const ATTEMPT_DELAY = 250;

// The addresses in the order they are tried: the first one's family first,
// then the two families in turn, each in the order it was found in.
function inTurns(addresses) {
  const list = addresses.map((address) => String(address).replace(/^\[|\]$/g, "")).filter((address) => net.isIP(address));
  if (!list.length) return [];
  const first = list.filter((address) => net.isIP(address) === net.isIP(list[0]));
  const other = list.filter((address) => net.isIP(address) !== net.isIP(list[0]));
  const order = [];
  for (let i = 0; i < Math.max(first.length, other.length); i++) {
    if (i < first.length) order.push(first[i]);
    if (i < other.length) order.push(other[i]);
  }
  return order;
}

// A connection to port at one of addresses, the IP addresses the rule took
// for name: resolves to the socket that connected first. hold(socket) is
// given each attempt's socket as it is made, as the proxy keeps every
// socket it makes to end it with itself. An aborted signal ends the
// attempts under way and fails with its reason. Fails once every attempt
// has failed, with the error of the first address tried, as a connection
// to that address alone fails, or with ENOTFOUND for no address at all.
function dialFirst(addresses, port, { name = "", hold = (socket) => socket, signal = null } = {}) {
  return new Promise((resolve, reject) => {
    const order = inTurns(addresses);
    if (!order.length) return reject(Object.assign(new Error(`${name || "the host"} was not found`), { code: "ENOTFOUND", hostname: name }));
    const sockets = [];
    const errors = [];
    let started = 0;
    let failed = 0;
    let done = false;
    let timer = null;
    const finish = (err, socket) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      if (signal) signal.removeEventListener("abort", aborted);
      for (const one of sockets) if (one !== socket) one.destroy();
      if (err) reject(err);
      else resolve(socket);
    };
    function aborted() {
      finish(signal.reason || Object.assign(new Error("The connection was given up"), { name: "AbortError", code: "ABORT_ERR" }));
    }
    const start = () => {
      clearTimeout(timer);
      if (done || started >= order.length) return;
      const at = started++;
      let socket;
      try {
        socket = hold(wire.dial(order[at], port, name || order[at]));
      } catch (err) {
        return lost(at, err);
      }
      sockets.push(socket);
      // Each attempt ends once: it connects, fails, or is closed, as one
      // the proxy ends with itself is.
      let over = false;
      const end = (err) => {
        if (over) return;
        over = true;
        socket.removeListener("close", closed);
        lost(at, err);
      };
      const closed = () => end(Object.assign(new Error(`The connection to ${order[at]} was closed before it was made`), { code: "ECONNABORTED" }));
      socket.on("error", () => {});
      socket.once("error", end);
      socket.once("close", closed);
      socket.once("connect", () => {
        if (over) return;
        over = true;
        socket.removeListener("error", end);
        socket.removeListener("close", closed);
        finish(null, socket);
      });
      if (started < order.length) timer = setTimeout(start, ATTEMPT_DELAY);
    };
    // An attempt that failed: the next one starts at once when no other is
    // under way, and the connection fails once none is left.
    function lost(at, err) {
      if (done) return;
      errors[at] = err;
      failed++;
      if (failed === order.length) return finish(errors[0] || err);
      if (failed === started) start();
    }
    if (signal) {
      if (signal.aborted) return aborted();
      signal.addEventListener("abort", aborted);
    }
    start();
  });
}

// The options of a request the kit makes itself to url, over http or https,
// that connect it to one of the addresses addressesOf() resolves to, the
// ones the rule took for url's host (see dialFirst). It is given no agent:
// Node.js sends a request on its global agent through the proxy HTTP_PROXY
// or HTTPS_PROXY names once NODE_USE_ENV_PROXY or --use-env-proxy is set,
// without the lookup the request was given, and that proxy looks the name
// up again for itself and connects wherever its answer points. Over https,
// TLS starts on the connection for url's host.
function judgedRequest(url, addressesOf, { signal = null } = {}) {
  const secure = url.protocol === "https:";
  const host = url.hostname.replace(/^\[|\]$/g, "");
  const port = Number(url.port || (secure ? 443 : 80));
  return {
    port,
    defaultPort: secure ? 443 : 80,
    createConnection: (options, made) => {
      Promise.resolve()
        .then(addressesOf)
        .then((addresses) => dialFirst(addresses, port, { name: host, signal }))
        .then(
          (socket) => made(null, secure ? tls.connect({ socket, host, ...(net.isIP(host) ? {} : { servername: host }) }) : socket),
          (err) => made(err),
        );
    },
  };
}

module.exports = { wire, dialFirst, judgedRequest, ATTEMPT_DELAY };
