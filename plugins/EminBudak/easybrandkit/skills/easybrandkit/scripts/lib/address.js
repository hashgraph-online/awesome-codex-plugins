"use strict";

// Which addresses a run opens. The address the user gives is opened whatever
// its host and port, and so are the pages on its scheme, host and port: a
// site on this machine, as http://localhost:3000, is the user's own choice.
// Any other address a run opens is one it was not given: a page it chose
// (the home page of a deeper address, the website a store listing names, a
// site another source named, a menu page with --facts), each hop of a
// redirect, a page's own move, a frame or a window a page opens, and
// robots.txt with each of its redirects. Such an address is opened only on
// port 80 or 443 and only on the public internet, and not at an address of
// this machine's own there (see ownIp): no document the browser loads and
// no request the kit makes itself goes to another program of this machine
// or of a private network, to another port of a public host, or to a
// router's page or a cloud server's metadata. The same rule holds for
// every request the browser makes, whatever makes it: a page's pictures,
// scripts and data, its WebSockets, a service worker's fetch, a prefetch,
// the fetch of a certificate's issuer and a page's WebAuthn check all go
// through the kit's own proxy (see proxy.js), which judges each by it and
// connects only to an address it took.
//
// MAKERSMCP_REFUSE_ADDRESSES, a comma list of IP addresses and CIDR ranges,
// names more addresses that the host the kit runs on refuses, as a server's
// own public addresses, which lead back inside its network. They are refused
// for every address a run opens, the one given included.
//
// A host name is judged by every address it is found at here, looked up once
// a run, and a connection, the browser's through the proxy and the kit's
// own, goes only to one of those (see guardFor).

const fs = require("fs");
const net = require("net");
const dns = require("dns");
const os = require("os");
const util = require("util");
const { domainToASCII, domainToUnicode } = require("url");

// The ranges that are not on the public internet, as MakersMCP's worker
// counts them: this machine, private and shared networks, link-local, and
// in IPv4 the ranges kept for protocol assignments (192.0.0.0/24), 6to4
// relays (192.88.99.0/24), documentation, benchmarks, multicast and later
// use; in IPv6 multicast, the documentation range 2001:db8::/32, the discard
// range 100::/64, Teredo (2001::/32), whose addresses hold the IPv4
// addresses of a server and of a client, either of which can be this
// machine or its network, NAT64's local use prefix (64:ff9b:1::/48) and the
// site local range (fec0::/10). The other IPv6 ranges count as public, the
// newer documentation range 3fff::/20 and the benchmarking one, 2001:2::/48,
// among them, as the worker counts them too. The test cases are in
// test/address-cases.json.
const V4 = [
  ["0.0.0.0", 8], ["10.0.0.0", 8], ["100.64.0.0", 10], ["127.0.0.0", 8], ["169.254.0.0", 16],
  ["172.16.0.0", 12], ["192.0.0.0", 24], ["192.0.2.0", 24], ["192.88.99.0", 24], ["192.168.0.0", 16],
  ["198.18.0.0", 15], ["198.51.100.0", 24], ["203.0.113.0", 24], ["224.0.0.0", 4], ["240.0.0.0", 4],
];
const V6 = [
  ["::", 128], ["::1", 128], ["64:ff9b:1::", 48], ["100::", 64], ["2001::", 32], ["2001:db8::", 32],
  ["fc00::", 7], ["fe80::", 10], ["fec0::", 10], ["ff00::", 8],
];
const blocked4 = new net.BlockList();
for (const [address, prefix] of V4) blocked4.addSubnet(address, prefix, "ipv4");
const blocked6 = new net.BlockList();
for (const [address, prefix] of V6) blocked6.addSubnet(address, prefix, "ipv6");

// An IP address as written, without the brackets of one in an address and
// without a zone (%eth0), which is no part of it.
const plainIp = (raw) => String(raw || "").replace(/^\[|\]$/g, "").replace(/%.*$/, "");

// An IPv6 address as its eight 16 bit groups, or null: a dotted IPv4 tail
// is two groups.
function groupsOf(address) {
  let text = plainIp(address).toLowerCase();
  const tail = /(\d+)\.(\d+)\.(\d+)\.(\d+)$/.exec(text);
  if (tail) {
    const [a, b, c, d] = tail.slice(1).map(Number);
    text = `${text.slice(0, tail.index)}${((a << 8) | b).toString(16)}:${((c << 8) | d).toString(16)}`;
  }
  const halves = text.split("::");
  if (halves.length > 2) return null;
  const part = (half) => (half ? half.split(":") : []);
  const head = part(halves[0]);
  const rest = halves.length === 2 ? part(halves[1]) : [];
  const fill = halves.length === 2 ? 8 - head.length - rest.length : 0;
  const groups = [...head, ...Array(Math.max(0, fill)).fill("0"), ...rest];
  if (groups.length !== 8 || groups.some((group) => !/^[0-9a-f]{1,4}$/.test(group))) return null;
  return groups.map((group) => parseInt(group, 16));
}

// The IPv4 address an IPv6 address holds, dotted, or "": mapped
// (::ffff:a.b.c.d), compatible (::a.b.c.d, past :: and ::1), translated
// (::ffff:0:a.b.c.d), 6to4 (2002:aabb:ccdd::/48) and NAT64's well known
// prefix (64:ff9b::/96), as a network with IPv6 only gives a name that has
// only IPv4. Each reaches that IPv4 address wherever it is routed, so it is
// judged as that address: ::7f00:1, 2002:7f00:1:: and ::ffff:0:7f00:1 are
// 127.0.0.1, and a NAT64 address of a public site is as public as the site.
function heldIpv4(raw) {
  const address = plainIp(raw);
  if (net.isIP(address) !== 6) return "";
  const groups = groupsOf(address);
  if (!groups) return "";
  const v4 = (high, low) => [high >> 8, high & 255, low >> 8, low & 255].join(".");
  const zero = (from, to) => groups.slice(from, to).every((group) => group === 0);
  if (zero(0, 5) && groups[5] === 0xffff) return v4(groups[6], groups[7]);
  if (zero(0, 6) && (groups[6] !== 0 || groups[7] > 1)) return v4(groups[6], groups[7]);
  if (zero(0, 4) && groups[4] === 0xffff && groups[5] === 0) return v4(groups[6], groups[7]);
  if (groups[0] === 0x2002) return v4(groups[1], groups[2]);
  if (groups[0] === 0x64 && groups[1] === 0xff9b && zero(2, 6)) return v4(groups[6], groups[7]);
  return "";
}

// The IPv4 addresses a Teredo address (2001::/32) holds, dotted: its
// server's, the 32 bits after 2001:0, and its client's, the last 32 bits
// with each bit turned over. Either can be this machine or the network of
// the host the kit runs on, and a machine with a Teredo client reaches such
// an address through them. [] for any other address.
function teredoIpv4(groups) {
  if (groups[0] !== 0x2001 || groups[1] !== 0) return [];
  const v4 = (high, low) => [high >> 8, high & 255, low >> 8, low & 255].join(".");
  return [v4(groups[2], groups[3]), v4(groups[6] ^ 0xffff, groups[7] ^ 0xffff)];
}

// Whether an IPv6 address is in NAT64's local use prefix, 64:ff9b:1::/48,
// where a network puts the IPv4 address its translator reaches in a way of
// its own choosing: in the last 32 bits, in another of the places RFC 6052
// gives, or by a table of its own.
const localNat64 = (groups) => groups[0] === 0x64 && groups[1] === 0xff9b && groups[2] === 1;

// The IPv4 address or range an IPv6 address or range holds, in one of the
// forms heldIpv4 reads or NAT64's local use prefix, as [address, prefix], or
// null: the IPv4 part is the last 32 bits of the mapped, compatible,
// translated and NAT64 forms, the local use prefix's too, as
// 64:ff9b:1::185.137.215.163 writes it, so a range of them at /96 or longer
// holds the IPv4 range of its last bits, and the 32 bits after 2002 in 6to4,
// so a range of those at /16 or longer holds the IPv4 range of its next
// bits, /32 from /48 on. A shorter range holds none. A compatible range that
// holds only :: and ::1, which are no IPv4 address, holds none.
// ::ffff:185.137.215.0/120 holds 185.137.215.0/24, and ::ffff:0:0/96 every
// IPv4 address, 0.0.0.0/0. As easyscreenshotkit reads it.
function heldRange(groups, bits) {
  const v4 = (high, low) => [high >> 8, high & 255, low >> 8, low & 255].join(".");
  const zero = (from, to) => groups.slice(from, to).every((group) => group === 0);
  if (bits >= 96) {
    const prefix = bits - 96;
    if ((zero(0, 5) && groups[5] === 0xffff) || (zero(0, 4) && groups[4] === 0xffff && groups[5] === 0) || (groups[0] === 0x64 && groups[1] === 0xff9b && zero(2, 6)) || localNat64(groups)) return [v4(groups[6], groups[7]), prefix];
    if (zero(0, 6)) {
      const low = ((groups[6] << 16) | groups[7]) >>> 0;
      const size = 2 ** (32 - prefix);
      const first = low - (low % size);
      return first + size - 1 >= 2 ? [v4(groups[6], groups[7]), prefix] : null;
    }
  }
  if (groups[0] === 0x2002 && bits >= 16) return [v4(groups[1], groups[2]), Math.min(bits, 48) - 16];
  return null;
}

// Whether an IP address is on the public internet. Anything that is no IP
// address is not.
function isPublicAddress(raw) {
  const address = plainIp(raw);
  const family = net.isIP(address);
  if (family === 4) return !blocked4.check(address, "ipv4");
  if (family !== 6) return false;
  const held = heldIpv4(address);
  if (held && !isPublicAddress(held)) return false;
  return !blocked6.check(address, "ipv6");
}

// Whether an IP address is this machine's own: "machine" for one of the
// addresses it holds, "network" for one of the IPv6 network of an address
// of an interface on the public internet (see machineNow), else "". A
// machine on an IPv6 network holds global addresses of its own
// (SLAAC, or DHCPv6), temporary ones among them that come and go, and a
// server can hold a public IPv4 address on an interface: such an address is
// on the public internet by its range, so a site that read it off the
// kit's own connection had the browser load a frame, a picture or a fetch()
// from a service of this machine that listens on all its addresses, and a
// site that sent its visitors there had the kit saved as that service's,
// with no word. A global IPv6 network is mostly the user's own, whose
// router and other machines answer there, and on a server whose provider
// puts other customers' servers in it, as a DigitalOcean droplet's /64,
// theirs, which are refused all the same (the README's Limits say so); the
// rest of a public IPv4 range on an interface is other people's servers, so
// in IPv4 the address alone. An IPv6 address that holds an IPv4 one is
// judged by that IPv4 address (see heldIpv4) and by itself, as any other
// IPv6 address: a network that gives this machine a 6to4 address builds it
// from the IPv4 address of its 6to4 router, which another box holds, and
// judged by that IPv4 address alone, the machine's own 6to4 address and
// every device of its 6to4 network, the router at the prefix's ::1 among
// them, were taken for the public internet. An address that leads into
// this machine or its network from outside, as the public IPv4 address of
// a router that turns a connection back inside, is no address it holds,
// and cannot be told from any other, nor can the rest of the user's own
// network at addresses on the public internet outside the networks of its
// interfaces, as another IPv6 network of the same site:
// MAKERSMCP_REFUSE_ADDRESSES is for those (the README's Limits say so).
function ownIp(raw) {
  const address = plainIp(raw);
  const family = net.isIP(address);
  if (!family) return "";
  const { mine, networks } = machineNow();
  if (family === 4) return mine.check(address, "ipv4") ? "machine" : "";
  const held = heldIpv4(address);
  if ((held && mine.check(held, "ipv4")) || mine.check(address, "ipv6")) return "machine";
  return networks.check(address, "ipv6") ? "network" : "";
}

// This machine's own addresses (mine) and the IPv6 networks of them
// (networks), read again once a second has passed since the last reading
// (wait, see below), or the clock went back, or a function that reads them
// is another, as a test puts one in its place. os.networkInterfaces() lists
// the addresses of the interfaces that are up and have a link alone, as
// Node.js's libuv leaves the others out, on every system. On Linux the
// kernel takes a connection to more of them for one to this machine, which
// its own files list (see kernelAddresses), and those are read too, as
// easyscreenshotkit reads them: an address of an interface that is up with
// no link, as a cable out, a veth whose other end is down or a bridge whose
// containers or virtual machines are all stopped, of an interface that is
// down, and every address of a range routed to the machine itself, as a
// pool of addresses for a proxy is set up (ip route add local ... dev lo).
// Read from the interfaces alone, each was taken for an address on the
// public internet away from the address given: a page's pictures, frames
// and fetch() reached a service of this machine that listens on all its
// addresses there, through the kit's proxy, what a fetch() read went into
// brand.json, and a site that sent its visitors there had the kit saved as
// that service's, with no word.
//
// The proxy judges every address of every request the browser makes, and
// each reading takes longer the more interfaces the machine has, as a
// Docker host has one for each container: read at each judgement, as
// easyscreenshotkit first read them, they were read 4001 times for one load
// of a news site's home page, and with 200 interfaces such a page loaded 3
// to 5 times more slowly, the main thread busy reading them. The kernel's
// lists of its routes take longer to read the more routes it holds (see
// KERNEL_ROUTES), so a machine of many is read again only once a second has
// passed for each ROUTES_A_SECOND of them, where that is longer.
//
// A reading of the interfaces that the system refuses, as where a Linux
// service's RestrictAddressFamilies leaves out AF_NETLINK, or where this
// process has as many files open as it may, leaves the last one of the same
// functions in its place, as this machine's addresses seldom change while a
// run goes. With none, it gives why not (unread, see interfacesUnread), and
// a run stops before any work: where the error was let go, the machine was
// taken for one with no addresses, so every address of this machine and of
// its IPv6 networks was opened away from the address given, and a name that
// answered with one of them beside an address on the public internet was
// no name whose answers mix, with no word.
//
// The IPv6 network of an address on the public internet is the prefix its
// interface gives it, held to /48 at the widest, as a wider one would take
// in other people's networks, and to /64 at the narrowest, as IPv6
// networks are /64 (RFC 7421): a DHCPv6 client holds the address it gets
// at /128, and the network's /64 comes from the router's advertisement as
// a route alone, which the kit does not take for a network (of the
// kernel's routes it takes the local ones alone, see kernelAddresses), so
// with the interface's prefix alone the router at the prefix's ::1 and
// every other device of such a network counted as the public internet. ::1
// and the other addresses that are not on the public internet give none:
// ::1 is held at /128, and the /64 around it holds addresses the rule takes
// for public by their range.
const INTERFACES_WAIT = 1_000;
const ROUTES_A_SECOND = 20_000;
let machine = null;

// The kernel's lists of this machine's addresses and routes, on Linux, and
// how the kit reads one (read(file), the file's text), which a test puts
// another function in place of.
const KERNEL_FILES = {
  trieStats: "/proc/net/fib_triestat",
  trie: "/proc/net/fib_trie",
  inet6: "/proc/net/if_inet6",
  routeStats6: "/proc/net/rt6_stats",
  route6: "/proc/net/ipv6_route",
};
const kernel = { read: (file) => fs.readFileSync(file, "latin1") };

// The most routes the kernel's list of them is read with: it lists them a
// page at a time, each page counted from the first route again, so the time
// a reading takes grows with the square of their number, the run's main
// thread doing nothing else meanwhile. On a busy machine here
// /proc/net/fib_trie took 5 to 7 ms to read with 2,000 IPv4 routes, which
// /proc/net/fib_triestat counts as 4,000 where the kernel keeps its local
// and main tables as one, 150 ms with 20,000 and 75 s with 300,000;
// /proc/net/ipv6_route took 7 ms with 2,000 IPv6 routes and 1.7 to 2.1 s
// with 20,000. A machine of more, as a router, is read by its interfaces
// that are up and have a link, and in IPv6 by the addresses of all its
// interfaces too (/proc/net/if_inet6, a line for each address).
const KERNEL_ROUTES = 4_000;

// An IPv6 address as the kernel's files write it, 32 hex digits, in the
// form a BlockList takes, or "".
function hexIpv6(hex) {
  if (!/^[0-9a-f]{32}$/i.test(hex)) return "";
  return hex.match(/.{4}/g).join(":");
}

// The text each of the kernel's files last gave, for the function that read
// it: a file that cannot be read is taken as it was last read, as a reading
// of the interfaces that the system refuses is (see machineNow), so a moment
// where this process has as many files open as it may does not have the
// addresses it lists taken for the public internet until it is read again.
// A file never read, as where /proc is not there or the system does not let
// it be read, is taken as empty, and the interfaces stand alone for what it
// lists.
let kernelTexts = { read: null, texts: {} };

// The addresses the kernel takes a connection to for one to this machine,
// as [address, prefix] pairs: in IPv4 (four) every LOCAL entry of the
// tables every connection is looked up in by the kernel's own rules, local,
// main and default (the parts of /proc/net/fib_trie after "Local:", "Main:"
// and "Id 253:"), an address of an interface, whatever its state, or a range
// routed to the machine itself; in IPv6 (six) every address of an
// interface, whatever its state (/proc/net/if_inet6), and every route of
// the kind local (RTF_LOCAL in /proc/net/ipv6_route) of /48 or longer; and
// each address of an interface with the prefix its interface gives it
// (prefixes), for its network (see machineNow). A transparent proxy routes
// every address to the machine itself in a table of its own, 0.0.0.0/0 and
// ::/0, which only the packets it marks go by, as a rule of its own says:
// taken, it made every address of the internet one of this machine's. In
// IPv4 such a table is a part of fib_trie of its own, as "Id 100:"; the
// kernel names no table for an IPv6 route, so a local route shorter than
// /48 is left out. The routes are listed only where the kernel's counts of
// them (/proc/net/fib_triestat, /proc/net/rt6_stats) are KERNEL_ROUTES at
// most. Empty on any other system; routes: how many routes the kernel
// counted.
function kernelAddresses() {
  const found = { four: [], six: [], prefixes: [], routes: 0 };
  if (process.platform !== "linux") return found;
  if (kernelTexts.read !== kernel.read) kernelTexts = { read: kernel.read, texts: {} };
  const { texts } = kernelTexts;
  const text = (file) => {
    try {
      texts[file] = String(kernel.read(file));
    } catch {
      // As it was last read, or empty (see kernelTexts).
    }
    return texts[file] || "";
  };
  // fib_triestat names each table and its count of prefixes, the routes
  // fib_trie lists for it.
  const counts4 = [...text(KERNEL_FILES.trieStats).matchAll(/^\s*Prefixes:\s*(\d+)\s*$/gm)].map((m) => Number(m[1]));
  const routes4 = counts4.reduce((sum, n) => sum + n, 0);
  // rt6_stats: seven counts in hex, the fourth the routes.
  const counts6 = text(KERNEL_FILES.routeStats6).trim().split(/\s+/);
  const routes6 = /^[0-9a-f]+$/i.test(counts6[3] || "") ? parseInt(counts6[3], 16) : Infinity;
  found.routes = routes4 + (Number.isFinite(routes6) ? routes6 : 0);
  let local = false;
  let leaf = "";
  for (const line of counts4.length && routes4 <= KERNEL_ROUTES ? text(KERNEL_FILES.trie).split("\n") : []) {
    if (/^\S/.test(line)) {
      local = /^(?:Local|Main|Id 253):/.test(line);
      leaf = "";
      continue;
    }
    if (!local) continue;
    const key = /^\s*\|-- (\d{1,3}(?:\.\d{1,3}){3})\s*$/.exec(line);
    if (key) {
      leaf = key[1];
      continue;
    }
    if (/^\s*\+--/.test(line)) {
      leaf = "";
      continue;
    }
    const entry = /^\s*\/(\d{1,2}) \S+ (\S+)/.exec(line);
    if (entry && leaf && entry[2] === "LOCAL" && net.isIP(leaf) === 4 && Number(entry[1]) <= 32) found.four.push([leaf, Number(entry[1])]);
  }
  for (const line of text(KERNEL_FILES.inet6).split("\n")) {
    const [hex, , bits] = line.trim().split(/\s+/);
    const at = hexIpv6(hex || "");
    if (!at) continue;
    found.six.push([at, 128]);
    found.prefixes.push([at, parseInt(bits, 16)]);
  }
  for (const line of routes6 <= KERNEL_ROUTES ? text(KERNEL_FILES.route6).split("\n") : []) {
    const fields = line.trim().split(/\s+/);
    const at = hexIpv6(fields[0] || "");
    const prefix = parseInt(fields[1], 16);
    if (!at || !(prefix >= 48 && prefix <= 128) || !/^[0-9a-f]{8}$/i.test(fields[8] || "")) continue;
    if (parseInt(fields[8], 16) & 0x80000000) found.six.push([at, prefix]);
  }
  return found;
}

function machineNow() {
  const now = Date.now();
  if (machine && machine.read === os.networkInterfaces && machine.kernel === kernel.read && now >= machine.at && now - machine.at < machine.wait) return machine;
  const read = os.networkInterfaces;
  let interfaces = {};
  try {
    interfaces = read.call(os);
  } catch (err) {
    const last = machine && machine.read === read && machine.kernel === kernel.read ? machine : null;
    machine = last ? { ...last, at: now } : { at: now, read, kernel: kernel.read, wait: INTERFACES_WAIT, mine: new net.BlockList(), networks: new net.BlockList(), unread: unreadWhy(err) };
    return machine;
  }
  const mine = new net.BlockList();
  const networks = new net.BlockList();
  // The network of an IPv6 address on the public internet (see above); one
  // whose prefix is not given is held alone, at /128.
  const network = (at, bits) => {
    if (isPublicAddress(at)) networks.addSubnet(at, Math.min(64, Math.max(48, bits || 128)), "ipv6");
  };
  for (const list of Object.values(interfaces || {})) {
    for (const one of list || []) {
      const at = plainIp(one && one.address);
      const kind = net.isIP(at);
      if (!kind) continue;
      mine.addAddress(at, kind === 4 ? "ipv4" : "ipv6");
      if (kind === 6) network(at, Number(String(one.cidr || "").split("/")[1]));
    }
  }
  const { four, six, prefixes, routes } = kernelAddresses();
  for (const [at, bits] of four) mine.addSubnet(at, bits, "ipv4");
  for (const [at, bits] of six) mine.addSubnet(at, bits, "ipv6");
  for (const [at, bits] of prefixes) network(at, bits);
  // wait: how long this reading is kept.
  machine = { at: now, read, kernel: kernel.read, wait: Math.max(INTERFACES_WAIT, (routes / ROUTES_A_SECOND) * 1_000), mine, networks };
  return machine;
}

// Why this machine's network interfaces could not be read, as
// { code, words }: the system's words for the error by its code, as "too
// many open files (EMFILE)", where Node.js names it by its number alone, as
// "Unknown system error 24", or its message cut to 200 characters, its
// control characters made spaces, when it has no number.
function unreadWhy(err) {
  const number = err && Number.isInteger(err.errno) ? -Math.abs(err.errno) : 0;
  const known = number ? util.getSystemErrorMap().get(number) : null;
  if (known) return { code: known[0], words: `${known[1]} (${known[0]})` };
  return { code: "", words: String((err && err.message) || err).replace(/[\u0000-\u001f\u007f]+/g, " ").slice(0, 200) };
}

// Why this machine's network interfaces cannot be read, as { code, words },
// or null where they could be read, now or earlier in the run (see
// machineNow): a run stops before any work then, as it could not tell this
// machine's own addresses from those on the public internet (see kit.js
// makeKit).
const interfacesUnread = () => machineNow().unread || null;

// Where an IP address stands for a run away from the address given: "" for
// one on the public internet that is not this machine's own, else "not
// public", or "machine" or "network" for one on the public internet that
// is this machine's (see ownIp). Each such address is refused there.
function standingOf(raw) {
  if (!isPublicAddress(raw)) return "not public";
  return ownIp(raw);
}

// The names a browser takes for this machine without asking the DNS:
// localhost, and any name under it.
const localName = (host) => /(^|\.)localhost$/i.test(host);

// The names the system can look up on this machine's own networks, by
// multicast: a name under .local, which goes to multicast DNS on each of
// them (RFC 6762), as nss-mdns hands it to avahi on a Linux desktop, and a
// name of one label, which goes to LLMNR where the system has it on, as
// Windows and systemd-resolved can. Looked up for a page, a picture at
// such a name put a question of the page's choosing on the user's own
// networks, and how soon it failed told the page whether a device there
// answers to that name. Neither is a name on the public internet, so one
// the run was not given is refused by its form, before any lookup.
const linkName = (host) => !net.isIP(host) && (/(^|\.)local$/i.test(host) || !host.includes("."));

// Whether a host has a label of broken punycode: one that starts with xn--
// and does not decode to a name that is written back as that label, as
// xn--a, xn--, xn--zz, or xn--a-, which decodes to a. The URL parser of
// Node.js 22.22 refuses such a host, that of Node.js 22.23 reads xn--a- as
// a host, and that of Node.js 24 keeps each as it is written, and the
// browser reads them all the same: the kit reads each as no address, so its
// rule is the same whatever Node.js it runs on. A label that decodes, as
// xn--bcher-kva, is the name it stands for.
const brokenPunycode = (host) =>
  String(host)
    .split(".")
    .some((label) => {
      if (!/^xn--/i.test(label)) return false;
      const name = domainToUnicode(label);
      return !name || /^xn--/i.test(name) || domainToASCII(name) !== label.toLowerCase();
    });

// A web address as the URL parser here reads it, or null for one it cannot
// read: one whose host has a label of broken punycode is not read either.
function readUrl(raw) {
  let url;
  try {
    url = new URL(String(raw));
  } catch {
    return null;
  }
  return brokenPunycode(url.hostname) ? null : url;
}

// An address's host as it is judged: in small letters, without the brackets
// of an IPv6 address and without its last dots, as 127.0.0.1.. is still
// 127.0.0.1 to the browser. What is left is read again as the URL parser
// reads a host, so a short or other IPv4 form with its dots taken off is
// the address it is: 127.1.., 0x7f.1.. and 192.168.1.. are 127.0.0.1,
// 127.0.0.1 and 192.168.0.1, where the URL parser leaves them names, as it
// does any host with two dots or more after it.
function bare(url) {
  const host = url.hostname.replace(/^\[|\]$/g, "").toLowerCase();
  const plain = host.replace(/\.+$/, "");
  if (plain === host || net.isIP(plain)) return plain;
  try {
    const again = new URL(`http://${plain}/`).hostname;
    return net.isIP(again) === 4 ? again : plain;
  } catch {
    return plain;
  }
}

// This machine's loopback addresses, in the order a connection to
// localhost tries them, ::1 first, as this machine's resolver and the
// browser order them: with 127.0.0.1 first, a site under development that
// listens on ::1 alone, as Node.js's own listen(port, "localhost") binds
// on Ubuntu, was passed over for another program that listens on
// 127.0.0.1 on the same port, whose pages the run then saved with no word.
const LOOPBACK = ["::1", "127.0.0.1"];

// The addresses of this machine that one of its own names for itself
// stands for, for a host as it is judged (see bare): localhost both of its
// loopback addresses (see LOOPBACK), and 127.0.0.1 and ::1 themselves; null
// for any other host. A name under localhost is none of them: a router on
// this machine, as Traefik or Caddy, serves each such name, as
// app1.localhost or traefik.localhost, as a site of its own. Nor are
// another address of 127.0.0.0/8, where another program can listen, as on
// 127.0.0.2 or 127.0.0.53, 0.0.0.0 and ::, which a connection takes for
// 127.0.0.1 and ::1 but a server there can tell apart by the name a
// request is for, and an IPv6 form of 127.0.0.1, as ::ffff:127.0.0.1.
function machineAddresses(host) {
  if (host === "localhost") return [...LOOPBACK];
  return host === "127.0.0.1" || host === "::1" ? [host] : null;
}

// The addresses of this machine that two hosts both stand for (see
// machineAddresses), or null: localhost and 127.0.0.1 share 127.0.0.1, and
// 127.0.0.1 and ::1 share none, as they can be two programs on one port.
function sharedAddresses(one, two) {
  const mine = machineAddresses(one);
  const theirs = machineAddresses(two);
  const both = mine && theirs ? mine.filter((address) => theirs.includes(address)) : [];
  return both.length ? both : null;
}

// Whether an address is not on the public internet by its form alone, or
// is this machine's own: an IP address that is not on it or is one of
// this machine's (see standingOf), a name of this machine's own, or a name
// the system looks up on this machine's own networks (see linkName).
function notPublicByForm(url) {
  const host = bare(url);
  return net.isIP(host) ? Boolean(standingOf(host)) : localName(host) || linkName(host);
}

// The port a web address is served on, the scheme's own when it names none.
const portOf = (url) => url.port || (url.protocol === "https:" ? "443" : "80");

// Whether an address is written with http: or https:, read as the URL
// parser reads a scheme: in any case, with tabs and line breaks taken out
// and the control characters and spaces before it left off.
const webScheme = (raw) => /^https?:/i.test(String(raw).replace(/[\t\n\r]/g, "").replace(/^[\u0000- ]+/, ""));

// The ports an address the run was not given may be on.
const WEB_PORTS = new Set(["80", "443"]);

// Whether two web addresses are on the same host and port: the same host,
// or two of this machine's own names for itself that reach an address of
// each other's, on the same port (see sharedAddresses). A local site can
// send its visitors from one of them to another, as from 127.0.0.1:8080 to
// localhost:8080, which reaches the same program at 127.0.0.1. Any other
// name is another host, though it lead to the same address and port: many
// sites are served at one address and port, a program there picking each
// by the name a request is for, as Laravel Valet or Herd serve *.test,
// DDEV's router *.ddev.site, which the public DNS answers with 127.0.0.1,
// Traefik or Caddy the names under localhost, and a web server its virtual
// hosts. Counted as the host given, a name under localhost had a page of
// http://localhost:3000/ load a frame, a picture and the data of a fetch()
// from http://traefik.localhost:3000/, another site of the same program.
function sameHost(a, b) {
  if (portOf(a) !== portOf(b)) return false;
  const [one, two] = [bare(a), bare(b)];
  return one === two || Boolean(sharedAddresses(one, two));
}

// ---- MAKERSMCP_REFUSE_ADDRESSES ----

const SETTING = "MAKERSMCP_REFUSE_ADDRESSES";

// The addresses the setting refuses: a comma list of IP addresses and CIDR
// ranges, as 185.137.215.163,10.0.0.0/8,fd00::/8, spaces around each
// allowed. Missing or empty, it refuses nothing more. A value that does not
// parse stops the run before any work, in words that name the setting.
//
// IPv4 entries and IPv6 entries are kept apart, as easyscreenshotkit keeps
// them: kept together, an IPv4 address was checked against an IPv6 entry as
// ::ffff:a.b.c.d, so ::/0 or ::/80 refused every IPv4 address, and so every
// site. An IPv4 entry refuses that address in every IPv6 form that holds it
// too (see heldIpv4) and a Teredo address whose server or client it is (see
// teredoIpv4), and while the setting names an IPv4 address or range, every
// address of NAT64's local use prefix is refused, as one can stand for any
// IPv4 address (see localNat64). An IPv6 entry refuses the IPv6 addresses it
// covers, and one written as an IPv6 form of an IPv4 address or range (see
// heldRange) that IPv4 address or range as well, and so every form of it:
// 2002:b989:d7a3::/48 named only itself, and 185.137.215.163 was opened. An
// entry that holds every IPv4 address, as 64:ff9b::/96 and 2002::/16 do,
// stops the run as a value that does not parse does: it would refuse every
// site, with words that blamed each site's address, and a host can copy
// such a range from a firewall's list of the IPv6 ranges it refuses whole.
//
// A connection to 0.0.0.0 goes to 127.0.0.1 and one to :: to ::1, on
// Linux, so the list judges each as the address it reaches as well: a
// list that refuses 127.0.0.1 refuses 0.0.0.0 and every IPv6 form of it, as
// ::ffff:0.0.0.0, and one that refuses ::1 refuses ::, written so or found
// for a name. Judged as written, each was opened as the address given, and
// the program on this machine's loopback at its port was read.
//
// match(address) gives the address that the list refuses for an IP address,
// the IPv4 address it holds or else it, or the loopback address it reaches,
// or "".
function refusedAddresses(value = process.env[SETTING]) {
  const v4 = new net.BlockList();
  const v6 = new net.BlockList();
  // size: the entries; fours: those that refuse IPv4 addresses.
  let size = 0;
  let fours = 0;
  for (const item of String(value === undefined ? "" : value).split(",")) {
    const text = item.trim();
    if (!text) continue;
    const range = /^([^/\s]+)(?:\/(\d{1,3}))?$/.exec(text);
    const family = range ? net.isIP(range[1]) : 0;
    const prefix = range && range[2] !== undefined ? Number(range[2]) : family === 6 ? 128 : 32;
    const shown = JSON.stringify(text.length > 60 ? `${text.slice(0, 60)}...` : text);
    if (!family || range[1].includes("%") || prefix > (family === 6 ? 128 : 32)) {
      throw new Error(`${SETTING} holds ${shown}, which is neither an IP address nor a range such as 10.0.0.0/8, so nothing was read. Give IP addresses and ranges parted by commas, or leave it empty.`);
    }
    const held = family === 6 ? heldRange(groupsOf(range[1]) || [], prefix) : null;
    if (held && held[1] === 0) {
      throw new Error(`${SETTING} holds ${shown}, a range of every IPv4 address in an IPv6 form, which would refuse every site, so nothing was read. An IPv6 form of an IPv4 address is judged by that address: give the IPv4 addresses and ranges to refuse, or leave it empty.`);
    }
    if (family === 4) v4.addSubnet(range[1], prefix, "ipv4");
    else v6.addSubnet(range[1], prefix, "ipv6");
    if (held) v4.addSubnet(held[0], held[1], "ipv4");
    if (family === 4 || held) fours++;
    size++;
  }
  return {
    size,
    match(raw) {
      if (!size) return "";
      const address = plainIp(raw);
      const family = net.isIP(address);
      const four = (one) => (v4.check(one, "ipv4") ? one : one === "0.0.0.0" && v4.check("127.0.0.1", "ipv4") ? "127.0.0.1" : "");
      if (family === 4) return four(address);
      const groups = family === 6 ? groupsOf(address) : null;
      if (!groups) return "";
      for (const held of [heldIpv4(address), ...teredoIpv4(groups)]) if (held && four(held)) return four(held);
      if (v6.check(address, "ipv6") || (fours && localNat64(groups))) return address;
      if (groups.every((group) => group === 0) && v6.check("::1", "ipv6")) return "::1";
      return "";
    },
  };
}

// ---- The words ----

// What an address that is not opened is, as said after "it" or "which".
const NOT_PUBLIC = "is not on the public internet";
const UNRESOLVED = "is on a host whose name could not be looked up";
// An http or https address that the URL parser here cannot read, as one
// whose host has a label of broken punycode (xn--a, see readUrl), which the
// browser reads all the same: where it leads cannot be judged.
const UNREADABLE = "is not an address easybrandkit can read";
const onPort = (port) => `is on port ${port}, not 80 or 443`;
const atNotPublic = (address) => `is at ${address}, an address not on the public internet`;
const atRefused = (address) => `is at ${address}, an address ${SETTING} refuses`;
// An address on the public internet that is this machine's own, or on the
// IPv6 network of one of its own (see ownIp), as easyscreenshotkit names it.
const atMachine = (address) => `is at ${address}, an address of this machine`;
const atNetwork = (address) => `is at ${address}, on a network of this machine`;

// Why an address is refused away from the address given, by where it
// stands (see standingOf).
const insideWhy = (address, standing) => (standing === "machine" ? atMachine(address) : standing === "network" ? atNetwork(address) : atNotPublic(address));

// Behind a proxy in fake-ip mode, as Clash, Surge or sing-box run with a
// TUN device, every name answers in 198.18.0.0/15, which is not on the
// public internet: an IPv4 address there or an IPv6 form of one.
const FAKE_IP = new net.BlockList();
FAKE_IP.addSubnet("198.18.0.0", 15, "ipv4");
function inFakeRange(raw) {
  const address = plainIp(raw);
  const v4 = net.isIP(address) === 6 ? heldIpv4(address) : address;
  return net.isIP(v4) === 4 && FAKE_IP.check(v4, "ipv4");
}

// Why a name whose addresses mix is refused, as said after "it" or
// "which", or "": one that answers both with an address on the public
// internet and with one that is not, or that is this machine's own or on
// one of its networks (see standingOf), named by its first answer of each
// kind. Such a name is refused wherever the run meets it, the address given
// included, before any work: taken for the user's own, as one of its
// answers was, its every answer was opened, so a site whose name answered
// with its public address and with 127.0.0.1 had every request of the run
// go to a service of this machine on 127.0.0.1, where the system put that
// address first, as glibc can by the order of RFC 6724, or once the public
// address had stopped answering, and that service's page was saved as the
// site's with no note. Away from the address given, such a name is named
// in the same words, never as one not on the public internet, which it is
// not alone. As easyscreenshotkit words it.
function mixedWhy(addresses) {
  const standings = addresses.map((address) => [plainIp(address), standingOf(address)]);
  const outside = standings.find(([, standing]) => !standing);
  const inside = standings.find(([, standing]) => standing);
  if (!outside || !inside) return "";
  const [at, standing] = inside;
  const kind = standing === "network" ? "one on a network of this machine" : standing === "machine" ? "one of this machine's" : inFakeRange(at) ? "one in the range a proxy in fake-ip mode gives every name, 198.18.0.0/15" : "one that is not";
  return `is on a host whose name answers with an address on the public internet, ${outside[0]}, and with ${kind}, ${at}`;
}

// How a name whose addresses mix answers, as said after the name itself,
// or "": mixedWhy's words, the name said in place of "is on a host whose
// name", as for a store's host, which the kit names itself (see stores.js
// judgedFetch).
const mixedAnswers = (addresses) => mixedWhy(addresses).replace(/^is on a host whose name /, "");

// Why a host found at these addresses is refused away from the address
// given, as said after "it" or "which", or "" for one every address of
// which is on the public internet and none this machine's own: a name whose
// answers mix by both (see mixedWhy), else by its first address that is not
// (see standingOf).
function awayWhy(addresses) {
  const mixed = mixedWhy(addresses);
  if (mixed) return mixed;
  for (const address of addresses) {
    const standing = standingOf(address);
    if (standing) return insideWhy(plainIp(address), standing);
  }
  return "";
}

// ---- The rule for a run ----

// How long a name is looked up for: one that gives no answer in this time
// is not opened.
const LOOKUP_WAIT = 5_000;

// The rule for the addresses a run opens, for the address given (given, a
// web address, whose scheme, host and port are the run's own; null for a
// run that has none, as one reading a site another source named, see
// makeKit), with the addresses refused (refused, from refusedAddresses).
// Each name is looked up once a run, and every connection the run makes,
// the browser's through the kit's proxy (see proxy.js) and the kit's own,
// goes only to an address that lookup found and the rule took, so no name
// is looked up twice and no later answer is ever used.
//
// judge(raw) resolves to "" for an address the run may open, and else to
// why not, to follow "it" or "which". What is not a web address is not
// judged here: a page that leads to one fails or is cancelled on its own
// (see chrome.js). One written with http: or https: that the URL parser
// here cannot read is not opened: the browser can read it, and go where
// its host leads.
//
// route(raw): { why, addresses }, why as judge gives it, and the addresses
// a connection to it may go to, for one the run may open: every address
// the lookup found for its host. For the address given they are looked up
// too, and none, for a name not found, is no refusal but a connection that
// cannot be made. For another of this machine's names that is the host
// given, as localhost from 127.0.0.1, they are the addresses the two share
// alone (see sharedAddresses).
//
// found(host): the addresses a host is at, by the same lookup: an IP
// address is at itself, and localhost and the names under it are on this
// machine's loopback, ::1 first (see LOOPBACK). [] for a name not found.
//
// inside(url): whether a host is not on the public internet or is this
// machine's own, by the same lookup, or cannot be told by it, as a name
// not found.
//
// addressesFor(raw): the addresses a request the kit makes itself to raw
// connects to (see dial.js), those route gives; it fails for one the rule
// refuses or the URL parser cannot read, and for a name not found.
function guardFor(givenRaw, { refused = refusedAddresses("") } = {}) {
  const given = givenRaw ? new URL(givenRaw) : null;
  const answers = new Map();
  const lookup = (host) => {
    if (!answers.has(host)) {
      let timer;
      const asked = Promise.race([
        dns.promises.lookup(host, { all: true, verbatim: true }).then((list) => ({ list: list.map((record) => record.address) })),
        new Promise((resolve) => (timer = setTimeout(resolve, LOOKUP_WAIT, { list: [] }))),
      ])
        .catch(() => ({ list: [] }))
        .finally(() => clearTimeout(timer));
      answers.set(host, asked);
    }
    return answers.get(host);
  };
  const found = async (host) => {
    if (net.isIP(host)) return [host];
    if (localName(host)) return [...LOOPBACK];
    return (await lookup(host)).list;
  };
  // On the scheme, host and port of the address given: its own pages; and
  // https on the host and port of an http address given, the same program,
  // which the browser asks over https by itself for a name that takes only
  // https (HSTS), as every .dev and .app name, keeping the port. A move
  // from https down to http there is not the address given, nor https on
  // port 443 of a host given on port 80, which is another program. The host
  // given is its own name, and of this machine's own names only those that
  // reach an address of it on its port (see sameHost).
  const givenHost = given ? bare(given) : "";
  const own = (url) => Boolean(given) && sameHost(url, given) && (url.protocol === given.protocol || (given.protocol === "http:" && url.protocol === "https:"));
  // The rule for one address. resolve: whether the addresses of one the run
  // may open are wanted, as for a connection; without it, the address given
  // is looked up only to check its answers, at a name, and to check them
  // against the refused addresses.
  async function rule(raw, resolve) {
    const url = readUrl(raw);
    if (!url) return { why: webScheme(raw) ? UNREADABLE : "", addresses: [] };
    if (!/^https?:$/.test(url.protocol)) return { why: "", addresses: [] };
    const mine = own(url);
    if (!mine && !WEB_PORTS.has(portOf(url))) return { why: onPort(portOf(url)), addresses: [] };
    const host = bare(url);
    if (!mine && (localName(host) || linkName(host))) return { why: NOT_PUBLIC, addresses: [] };
    // An IP address away from the address given that is not on the public
    // internet, by its form, or that is this machine's own.
    if (!mine && net.isIP(host)) {
      const standing = standingOf(host);
      if (standing) return { why: standing === "not public" ? NOT_PUBLIC : insideWhy(host, standing), addresses: [] };
    }
    // The address given at an IP address or a name of this machine's own
    // needs no lookup to be judged: no such host has answers that mix.
    const name = !net.isIP(host) && !localName(host);
    if (mine && !refused.size && !resolve && !name) return { why: "", addresses: [] };
    // Another of this machine's names that is the host given goes to the
    // addresses the two share alone: from http://127.0.0.1:4000/, a page's
    // picture at http://localhost:4000/ comes from 127.0.0.1, never from
    // ::1, which can be another program on that port.
    const addresses = (mine && sharedAddresses(host, givenHost)) || (await found(host));
    if (!addresses.length) return { why: mine && !refused.size ? "" : UNRESOLVED, addresses: [] };
    // A name whose answers mix is refused wherever it is, the address given
    // and its own pages included (see mixedWhy).
    const away = mine ? (name ? mixedWhy(addresses) : "") : awayWhy(addresses);
    if (away) return { why: away, addresses: [] };
    for (const address of addresses) if (refused.match(address)) return { why: atRefused(refused.match(address)), addresses: [] };
    return { why: "", addresses: addresses.map(plainIp) };
  }
  const judge = async (raw) => (await rule(raw, false)).why;
  const route = (raw) => rule(raw, true);
  async function inside(url) {
    const addresses = await found(bare(url));
    return !addresses.length || addresses.some((address) => Boolean(standingOf(address)));
  }
  async function addressesFor(raw) {
    const { why, addresses } = await route(raw);
    if (why || !addresses.length) throw Object.assign(new Error(`${String(raw).slice(0, 300)} ${why || UNRESOLVED}`), { code: why ? "ENOTPUBLIC" : "ENOTFOUND" });
    return addresses;
  }
  return { given: given ? given.href : "", refused, judge, route, found, inside, addressesFor };
}

module.exports = { isPublicAddress, heldIpv4, ownIp, kernel, interfacesUnread, notPublicByForm, sameHost, portOf, refusedAddresses, guardFor, readUrl, atRefused, awayWhy, mixedAnswers, UNRESOLVED };
