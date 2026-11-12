"use strict";

// Addresses on this machine or on a private network: loopback, private and
// link-local ones, and names such as localhost. easybrandkit opens a page on
// one only when the address the user gave is on that same host and port. A
// site, a store listing or a page's own redirect never leads it there on its
// own, to another program that listens on this machine, a router's page or
// a cloud server's metadata.

const net = require("net");
const { promises: dns } = require("dns");

// The names Chrome takes as this machine itself: localhost, and any name
// under it.
const OWN_NAME = /(^|\.)localhost\.?$/i;

// An address's host, without the brackets of an IPv6 one, as a host is
// compared: in small letters and without a last dot.
const bare = (url) => url.hostname.replace(/^\[|\]$/g, "").toLowerCase().replace(/\.$/, "");

// The eight 16-bit groups of an IPv6 address, an IPv4 address at its end
// included.
function groupsOf(address) {
  let text = address.toLowerCase().replace(/%.*$/, "");
  const dotted = /(\d+)\.(\d+)\.(\d+)\.(\d+)$/.exec(text);
  if (dotted) {
    const [a, b, c, d] = dotted.slice(1).map(Number);
    text = `${text.slice(0, dotted.index)}${((a << 8) | b).toString(16)}:${((c << 8) | d).toString(16)}`;
  }
  const [head, tail] = text.split("::");
  const front = head ? head.split(":") : [];
  const back = tail ? tail.split(":") : [];
  const zeros = tail === undefined ? [] : Array(8 - front.length - back.length).fill("0");
  return [...front, ...zeros, ...back].map((group) => parseInt(group, 16));
}

// The IPv4 address an IPv6 address stands for: one mapped into IPv6
// (::ffff:0:0/96), or one a NAT64 gateway reaches (64:ff9b::/96), as a
// network that has only IPv6 gives every name that has only IPv4. "" for any
// other address.
function ipv4Within(address) {
  if (net.isIP(address) !== 6) return "";
  const g = groupsOf(address);
  const mapped = g.slice(0, 5).every((group) => group === 0) && g[5] === 0xffff;
  const nat64 = g[0] === 0x64 && g[1] === 0xff9b && g.slice(2, 6).every((group) => group === 0);
  return mapped || nat64 ? [g[6] >> 8, g[6] & 255, g[7] >> 8, g[7] & 255].join(".") : "";
}

// Whether an IP address is on this machine or on a private network: 0/8,
// 10/8, 100.64/10 (carrier-grade NAT, and the addresses Tailscale gives),
// 127/8, 169.254/16, 172.16/12 and 192.168/16; ::, ::1, fc00::/7, fe80::/10
// and fec0::/10; and an IPv4 address in IPv6 form by the IPv4 address it
// stands for. An address that is only not public, as the 198.18.0.0/15 a
// proxy in fake-ip mode gives every name, is not one of these.
function localAddress(raw) {
  const address = String(raw || "").replace(/^\[|\]$/g, "");
  const family = net.isIP(address);
  if (family === 4) {
    const [a, b] = address.split(".").map(Number);
    return a === 0 || a === 10 || a === 127 || (a === 100 && b >= 64 && b <= 127) || (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168);
  }
  if (family !== 6) return false;
  const within = ipv4Within(address);
  if (within) return localAddress(within);
  const g = groupsOf(address);
  return loopback(address) || (g[0] & 0xfe00) === 0xfc00 || (g[0] & 0xffc0) === 0xfe80 || (g[0] & 0xffc0) === 0xfec0;
}

// Whether a host is this machine itself, by a name or an address of its
// own: localhost and the names under it, 127/8, ::1, and 0.0.0.0 and ::,
// which reach this machine too.
function loopback(host) {
  const v4 = ipv4Within(host) || host;
  if (net.isIP(v4) === 4) return v4.startsWith("127.") || v4 === "0.0.0.0";
  if (net.isIP(v4) === 6) {
    const g = groupsOf(v4);
    return g.slice(0, 7).every((group) => group === 0) && g[7] <= 1;
  }
  return OWN_NAME.test(v4);
}

// Whether an address is on a local or private network by its form alone:
// such an IP address, or a name of this machine's own.
function localByForm(url) {
  const host = bare(url);
  return net.isIP(host) ? localAddress(host) : OWN_NAME.test(host);
}

// How long a name is looked up for. Chrome looks it up again itself, and a
// name that is not found is a page it cannot open.
const LOOKUP_WAIT = 5_000;

// Whether a page is on a local or private network. seen is what the browser
// said of where it got the page: the IP address space Chrome gave the
// response (space) and the address it connected to (ip). Chrome gives a
// space of its own only when it reached the server itself, so then ip is the
// server's, and it decides as an address does; through a proxy it says
// Unknown and gives the proxy's address, which says nothing of the page.
// Then, and for a page it said nothing of, the page is on such a network
// when its address is by its form, or when any address its name is found
// at is. A name that cannot be looked up in time is not, as a page the
// browser cannot open.
async function onLocalNetwork(url, { space = "", ip = "" } = {}) {
  if (space && space !== "Unknown" && localAddress(ip)) return true;
  if (localByForm(url)) return true;
  const host = bare(url);
  if (net.isIP(host)) return false;
  let timer;
  try {
    const found = await Promise.race([dns.lookup(host, { all: true, verbatim: true }), new Promise((resolve) => (timer = setTimeout(resolve, LOOKUP_WAIT, [])))]);
    return found.some((record) => localAddress(record.address));
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

// Where such an address is, in words that can follow it.
const LOCAL = "is on a local or private network";

// The port a web address is served on, the scheme's own when it names none.
const portOf = (url) => url.port || (url.protocol === "https:" ? "443" : "80");

// Whether two web addresses are on the same host and port. A local site can
// send its visitors from one name of this machine to another, as from
// 127.0.0.1:8080 to localhost:8080, so two loopback hosts on the same port
// count as one.
function sameHost(a, b) {
  if (portOf(a) !== portOf(b)) return false;
  const [one, two] = [bare(a), bare(b)];
  return one === two || (loopback(one) && loopback(two));
}

// Whether a web page may be opened or read when the address the user gave
// is given: always on that same host and port, and elsewhere when it is not
// on a local or private network; seen is what the browser said of where it
// got the page, once it has. What is not a web page is not asked about here.
async function mayOpen(raw, given, seen) {
  const url = new URL(raw);
  if (!/^https?:$/.test(url.protocol)) return true;
  return sameHost(url, new URL(given)) || !(await onLocalNetwork(url, seen));
}

module.exports = { localByForm, localAddress, ipv4Within, onLocalNetwork, sameHost, portOf, mayOpen, LOCAL };
