"use strict";

// The proxy every request of a run's browser goes through: a small HTTP
// proxy of the kit's own on 127.0.0.1, started before the browser, which is
// started with it as its proxy for every address, this machine's own among
// them, with every name failing in its own lookup and with its own DNS over
// HTTPS off (see chrome.js launch). So the browser looks no name up and
// connects nowhere itself, but to a server of DNS over HTTPS that a Chrome
// policy names at 127.0.0.1: whatever asks for an address, a page, a frame,
// a picture, a script, the data a page fetches, a WebSocket, a service
// worker, a prefetch, the fetch of a site certificate's issuer or a page's
// WebAuthn check, the request comes here. It takes plain http requests,
// which the browser sends with the whole address, and CONNECT tunnels, which
// it opens for https and for WebSockets, and nothing else. Each is judged by
// the run's rule (see address.js guardFor, route), which looks each name up
// once a run, and is connected only to an address that rule took for it,
// without asking the DNS again. What the rule refuses gets a 403 and no
// connection, and is kept with its address and why for the kit's notes (see
// chrome.js proxyNotes).
//
// It listens on 127.0.0.1 alone, on a port the system picks, for as long as
// its browser runs. A request it gets that is not one of these, as one
// that names no host, gets a 400.

const fs = require("fs");
const http = require("http");
const crypto = require("crypto");
const { dialFirst } = require("./dial");

// The tables of this machine's TCP sockets on Linux, each with the uid of
// the user whose socket it is.
const TCP_TABLES = ["/proc/net/tcp", "/proc/net/tcp6"];
// 127.0.0.1 as those tables write an address, in either byte order, also
// mapped into IPv6 (::ffff:127.0.0.1).
const TABLE_LOOPBACK = /^(?:0100007F|7F000001|0000000000000000FFFF00000100007F|00000000000000000000FFFF7F000001):[0-9A-F]{4}$/;

// Whose program a connection to the proxy comes from, on Linux: the uid
// those tables give the socket at its other end, which is on 127.0.0.1 as
// well, as the proxy listens there alone, found by the ports the connection
// had when the proxy took it (see startProxy's hold), as a closed one has
// none. "gone" when the tables could be read and hold no such socket, as
// for a program that has closed it, and null where it cannot be told: on
// another system, or with no table to read.
async function ownerOf(socket) {
  const ports = socket.easybrandkitPorts || { remote: socket.remotePort, local: socket.localPort };
  if (process.platform !== "linux" || !ports.remote || !ports.local) return null;
  const hex = (port) => Number(port).toString(16).toUpperCase().padStart(4, "0");
  const [mine, theirs] = [hex(ports.remote), hex(ports.local)];
  let read = false;
  for (const file of TCP_TABLES) {
    let table;
    try {
      table = await fs.promises.readFile(file, "latin1");
    } catch {
      continue;
    }
    read = true;
    for (const line of table.split("\n")) {
      const fields = line.trim().split(/\s+/);
      if (fields.length > 7 && fields[1].endsWith(`:${mine}`) && fields[2].endsWith(`:${theirs}`) && TABLE_LOOPBACK.test(fields[1]) && TABLE_LOOPBACK.test(fields[2])) return Number(fields[7]);
    }
  }
  return read ? "gone" : null;
}

// Whose program a connection to the proxy comes from (see ownerOf). Tests
// put their own owners here. The proxy connects to the addresses the rule
// took for a host as every connection of a run is made (see dial.js), so a
// name is never looked up again.
const wire = { owner: ownerOf };

// The headers that belong to one connection and not to the request or the
// answer it carries, which the proxy does not pass on, with those a
// Connection header names.
const HOP = new Set(["connection", "proxy-connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade"]);

function passedOn(raw) {
  const named = new Set();
  for (let i = 0; i < raw.length; i += 2) {
    if (/^(proxy-)?connection$/i.test(raw[i])) for (const name of String(raw[i + 1]).split(",")) named.add(name.trim().toLowerCase());
  }
  const out = [];
  for (let i = 0; i < raw.length; i += 2) {
    const name = String(raw[i]).toLowerCase();
    if (!HOP.has(name) && !named.has(name)) out.push(raw[i], raw[i + 1]);
  }
  return out;
}

// The largest headers taken, of a request and of an answer: Node's own 16
// KB would refuse a site's large cookies or policies that the browser takes.
const HEADER_MOST = 256 * 1024;

// The headers of a site's answer that are passed on to the browser: those
// passedOn keeps that Node can write, and no Content-Length, as the proxy
// gives each answer its own framing (see answer). A site's answer is read
// the way the browser reads one (insecureHTTPParser), which takes headers
// Node does not write, as one with a control character in its value; such
// a header is left out, where it ended the whole answer.
function answerHeaders(raw) {
  const kept = passedOn(raw);
  const out = [];
  for (let i = 0; i < kept.length; i += 2) {
    if (/^content-length$/i.test(kept[i])) continue;
    try {
      http.validateHeaderName(kept[i]);
      http.validateHeaderValue(kept[i], kept[i + 1]);
    } catch {
      continue;
    }
    out.push(kept[i], kept[i + 1]);
  }
  return out;
}

// A reason phrase Node can write, else none, for which it writes the one it
// knows for the status.
const reasonOf = (text) => (/^[\t\x20-\x7e\x80-\xff]*$/.test(String(text)) ? text : undefined);

// How many refused addresses are kept, each once, and how many failed
// connections.
const KEEP_REFUSED = 50;
const KEEP_FAILED = 100;

// What a request the proxy got stands for: the address it judges, as a URL,
// and how it is told in the kit's notes, the whole address of a plain http
// request and the host and port of a tunnel.
function tunnelUrl(authority) {
  const form = /^(\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9._~!$&'()*+,;=-]+):(\d{1,5})$/.exec(authority);
  if (!form || Number(form[2]) < 1 || Number(form[2]) > 65535) return null;
  try {
    const url = new URL(`https://${authority}/`);
    const port = url.port || "443";
    return port === String(Number(form[2])) && !url.username && !url.password ? url : null;
  } catch {
    return null;
  }
}

// The port of a web address, the scheme's own when it names none.
const portOf = (url) => url.port || (url.protocol === "https:" ? "443" : "80");

// A host as a connection names it: an IPv6 address without its brackets.
const plainHost = (url) => url.hostname.replace(/^\[|\]$/g, "");

// Where a failed connection is kept: its host and port.
const keyOf = (url) => `${plainHost(url).toLowerCase()}:${portOf(url)}`;

// The proxy's own name, under .invalid, which no DNS answers: the browser
// is asked for it to show that its requests come here (see chrome.js
// throughProxy), and its own push channel is pointed at it (see chrome.js
// launch). A request for it, or for this machine on the proxy's own port,
// is the proxy's own: answered here, and kept nowhere but as a probe.
const OWN_NAME = "easybrandkit-proxy.invalid";

// Why a request is refused when the browser was started with no rule.
const NO_RULE = "is not opened by a browser the kit gave no rule for the addresses it opens";
// Why one is refused when the rule itself failed.
const NOT_JUDGED = "could not be judged";
// What a tunnel or a request whose address cannot be read is.
const UNREADABLE = "is not an address easybrandkit can read";

// Starts the proxy for a run's rule (guard, see address.js guardFor; null
// for a browser that is to open no web page) and resolves to it, once it
// listens:
//   port         the port it listens on, on 127.0.0.1
//   token        a word of its own, which the probes of chrome.js put in
//                their paths: a request for /<token>/<n> that comes to it
//                as a proxy request it answers itself, and keeps n in
//                through
//   accepted     how many connections it has taken
//   reading      the page the kit reads, which the kit sets as it opens one
//   refused      what it refused: { what, why, page }, each address once,
//                the first 50, refusedMore saying that there were more
//   failed       the connections it could not make to addresses the rule
//                took, and those a server reset before it answered:
//                { n, key, code }, the last 100, key being host:port and n
//                counting them from 1, failedCount being the last n
//   close()      stops it and every connection it holds
function startProxy(guard) {
  const token = crypto.randomBytes(12).toString("hex");
  const sockets = new Set();
  const proxy = { port: 0, token, through: new Set(), accepted: 0, reading: "", refused: [], refusedMore: false, failed: [], failedCount: 0, closed: false };
  const hold = (socket) => {
    sockets.add(socket);
    socket.easybrandkitPorts = { remote: socket.remotePort, local: socket.localPort };
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => {});
    if (proxy.closed) socket.destroy();
    return socket;
  };
  const route = async (raw) => {
    if (!guard) return { why: NO_RULE, addresses: [] };
    try {
      return await guard.route(raw);
    } catch {
      return { why: NOT_JUDGED, addresses: [] };
    }
  };
  // A request refused, kept for the kit's notes when it came from a program
  // of this user's, as the browser is: any program of this machine can
  // connect to the proxy, as to any port of 127.0.0.1, and what another
  // user's asks is refused as any request is, but not named in the notes as
  // the browser's. Where that cannot be told, as on another system than
  // Linux, it is kept. The table is read before the refusal is answered,
  // while the connection is still there.
  const own = process.getuid ? process.getuid() : null;
  const refuse = async (what, why, socket) => {
    const page = proxy.reading;
    if (proxy.refused.some((one) => one.what === what) || (proxy.refusedMore && proxy.refused.length >= KEEP_REFUSED)) return;
    if (own !== null && socket) {
      let owner = null;
      try {
        owner = await wire.owner(socket);
      } catch {
        // Cannot be told.
      }
      if (owner !== null && owner !== own) return;
    }
    if (proxy.refused.some((one) => one.what === what)) return;
    if (proxy.refused.length < KEEP_REFUSED) proxy.refused.push({ what, why, page });
    else proxy.refusedMore = true;
  };
  const failed = (url, err) => {
    proxy.failed.push({ n: ++proxy.failedCount, key: keyOf(url), code: String((err && err.code) || "") });
    if (proxy.failed.length > KEEP_FAILED) proxy.failed.shift();
    if (err) err.kept = true;
  };
  // A connection to url's host and port at one of addresses, the ones the
  // rule took for it (see dial.js): the socket, once connected. Every
  // attempt is held, so close ends those still under way too.
  const connect = (url, addresses, signal = null) => dialFirst(addresses, Number(portOf(url)), { name: plainHost(url), hold, signal });
  // Whether an address is the proxy's own.
  const ownAddress = (url) => url.hostname === OWN_NAME || (["127.0.0.1", "localhost", "[::1]"].includes(url.hostname) && portOf(url) === String(proxy.port));
  // The probes of chrome.js: /<token>/<n>, answered here.
  const probe = (path) => {
    const n = new RegExp(`^/${token}/(\\d)$`).exec(path);
    if (!n) return false;
    proxy.through.add(Number(n[1]));
    return true;
  };

  // The connections of plain http requests with no body, kept open between
  // requests to the same host and port, as the browser keeps its own: a
  // page of a site under development that loads its modules one request
  // each, a few hundred of them, loaded half as fast with a connection of
  // its own for each. Agent keeps them by the host as the request names it,
  // a name or an IP address, and its port, and makes each by connect, so to
  // an address the rule took for that host and held (see hold), which close
  // ends; one idle for 5 s is closed.
  const agent = new http.Agent({ keepAlive: true, timeout: 5_000 });
  agent.createConnection = (options, made) => {
    connect(options.easybrandkitUrl, options.easybrandkitAddresses).then(
      (socket) => made(null, socket),
      (err) => {
        failed(options.easybrandkitUrl, err);
        made(err);
      },
    );
  };

  // A plain http request, the whole address in its first line.
  const answer = async (req, res) => {
    res.sendDate = false;
    const target = String(req.url || "");
    // A request with no whole address came to this port as an address of
    // its own, past the proxy, and is answered with nothing.
    if (!/^http:\/\//i.test(target)) return res.writeHead(400, { "content-length": "0", connection: "close" }).end();
    let url;
    try {
      url = new URL(target);
    } catch {
      await refuse(target.slice(0, 300), UNREADABLE, req.socket);
      return res.writeHead(403, { "content-length": "0" }).end();
    }
    if (ownAddress(url)) {
      if (probe(url.pathname)) return res.writeHead(200, { "content-type": "text/plain", "content-length": "0" }).end();
      return res.writeHead(404, { "content-length": "0" }).end();
    }
    const { why, addresses } = await route(url.href);
    if (why) {
      await refuse(url.href.slice(0, 300), why, req.socket);
      return res.writeHead(403, { "content-length": "0" }).end();
    }
    if (req.socket.destroyed) return;
    // The request as the browser sent it, for the address's own host, which
    // the connection already reaches.
    const headers = ["Host", url.host];
    const kept = passedOn(req.rawHeaders);
    for (let i = 0; i < kept.length; i += 2) if (!/^host$/i.test(kept[i])) headers.push(kept[i], kept[i + 1]);
    // A request with a body goes on a connection of its own, which is
    // closed after it: one kept open that the site has closed meanwhile
    // fails it, and its body cannot be sent again.
    const bodiless = req.headers["content-length"] === undefined && req.headers["transfer-encoding"] === undefined;
    const options = { method: req.method, path: `${url.pathname}${url.search}`, headers, setHost: false, maxHeaderSize: HEADER_MOST, insecureHTTPParser: true, host: plainHost(url), port: Number(portOf(url)), easybrandkitUrl: url, easybrandkitAddresses: addresses };
    let answered = false;
    let gone = false;
    let asked;
    // A connection that was kept open can have been closed by the site just
    // as the request went out on it: the request is sent once more, on a
    // connection of its own. A request with no agent connects only through
    // createConnection; agent: false would have Node make one of its own,
    // which looks the name up again.
    const send = (again) => {
      const one = http.request(bodiless && !again ? { ...options, agent } : { ...options, headers: [...headers, "Connection", "close"], createConnection: (opts, made) => agent.createConnection(opts, made) });
      asked = one;
      one.on("response", (answer) => {
        answered = true;
        try {
          res.writeHead(answer.statusCode, reasonOf(answer.statusMessage), answerHeaders(answer.rawHeaders));
        } catch {
          // A status Node does not write, as one under 100.
          failed(url, { code: "HPE_INVALID_STATUS" });
          one.destroy();
          return req.socket.destroy();
        }
        answer.pipe(res);
        // An answer cut short by the site, which Node.js tells as an error
        // of the answer, is cut short for the browser too.
        answer.on("error", () => res.destroy());
      });
      // A server that closes the connection before it answers is told by
      // the browser as an empty answer, as it would be told without the
      // proxy; one that resets it, a system error, is kept as that, and so
      // is an answer that is not HTTP as the browser reads it, which the
      // browser is told nothing of (see chrome.js navigate). Node.js tells a
      // request's error once.
      one.on("error", (err) => {
        if (answered || gone) return res.destroy();
        if (bodiless && !again && one.reusedSocket && !err.kept) return send(true);
        if (err && !err.kept && (err.syscall || /^HPE_/.test(String(err.code)))) failed(url, err);
        req.socket.destroy();
      });
      if (bodiless) one.end();
      else req.pipe(one);
    };
    send(false);
    // The browser that gives the request up ends its connection too.
    res.on("close", () => {
      gone = true;
      if (!res.writableFinished) asked.destroy();
    });
  };
  // A CONNECT tunnel to the host and port it names.
  const tunnel = async (req, socket, head) => {
    const authority = String(req.url || "");
    const url = tunnelUrl(authority);
    if (!url) {
      await refuse(authority.slice(0, 300), UNREADABLE, socket);
      return socket.end("HTTP/1.1 403 Forbidden\r\ncontent-length: 0\r\n\r\n");
    }
    if (ownAddress(url)) return socket.end("HTTP/1.1 403 Forbidden\r\ncontent-length: 0\r\n\r\n");
    const what = `${url.hostname}:${portOf(url)}`;
    // A tunnel carries https, or a WebSocket, to the host and port it
    // names: it is judged as an https address there.
    const { why, addresses } = await route(url.href);
    if (why) {
      await refuse(what, why, socket);
      return socket.end("HTTP/1.1 403 Forbidden\r\ncontent-length: 0\r\n\r\n");
    }
    // A browser that gives the tunnel up while it is made ends the attempts
    // under way.
    const given = new AbortController();
    const up = () => given.abort();
    socket.once("close", up);
    let upstream;
    try {
      upstream = await connect(url, addresses, given.signal);
    } catch (err) {
      if (given.signal.aborted) return;
      socket.removeListener("close", up);
      failed(url, err);
      return socket.end("HTTP/1.1 502 Bad Gateway\r\ncontent-length: 0\r\n\r\n");
    }
    socket.removeListener("close", up);
    if (socket.destroyed) return upstream.destroy();
    socket.write("HTTP/1.1 200 Connection Established\r\n\r\n");
    if (head && head.length) upstream.write(head);
    upstream.pipe(socket);
    socket.pipe(upstream);
    socket.on("close", () => upstream.destroy());
    upstream.on("close", () => socket.destroy());
  };

  const server = http.createServer({ maxHeaderSize: HEADER_MOST });
  server.on("connection", (socket) => {
    proxy.accepted++;
    hold(socket);
  });
  server.on("clientError", (err, socket) => socket.destroy());
  // What fails on the way ends that connection, and nothing else.
  server.on("request", (req, res) => answer(req, res).catch(() => req.socket.destroy()));
  server.on("connect", (req, socket, head) => tunnel(req, socket, head).catch(() => socket.destroy()));
  // A request that asks for another protocol on its own connection is no
  // request the browser sends a proxy: it sends a WebSocket through a
  // tunnel.
  server.on("upgrade", (req, socket) => socket.end("HTTP/1.1 501 Not Implemented\r\ncontent-length: 0\r\n\r\n"));

  proxy.close = () => {
    if (proxy.closed) return;
    proxy.closed = true;
    server.close();
    for (const socket of sockets) socket.destroy();
  };
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      server.removeListener("error", reject);
      server.on("error", () => {});
      proxy.port = server.address().port;
      resolve(proxy);
    });
  });
}

module.exports = { startProxy, wire, keyOf, OWN_NAME, UNREADABLE };
