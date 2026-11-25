"use strict";

// The browser: a Chrome, Chromium, Edge or Brave already on this machine,
// started headless with a throwaway profile and driven over the DevTools
// protocol through a pipe of its own. It opens no port, so no other program
// on the machine, another user's run among them, can reach it. Every
// request it makes goes through the kit's own proxy (see proxy.js), which
// judges it by the run's rule, and it looks no name up itself: every name
// fails in its own lookup but 127.0.0.1, so a Chrome policy that turns on
// the DNS over HTTPS the kit turns off has it reach that server only where
// the policy names it at 127.0.0.1 (see launch). Nothing is downloaded.

const fs = require("fs");
const os = require("os");
const path = require("path");
const dgram = require("dgram");
const crypto = require("crypto");
const { spawn } = require("child_process");
const { timeLeft, outOfTime, sleep, LONGEST_TIMER } = require("./time");
const { browserPlace, wrongWith, couldNotStart, endedEarly, closedEarly, systemWords, moreFiles, ownSandbox } = require("./program");
const { startProxy, keyOf, OWN_NAME } = require("./proxy");
const { UNRESOLVED } = require("./address");

// The browser this run would start, or "" when none is found or what is
// found cannot be started (browserPlace in program.js says why).
function findChrome() {
  try {
    return browserPlace().file;
  } catch {
    return "";
  }
}

// The programs Chrome on Linux hands an address that is not a web address
// to, such as mailto:, news: and snews:, which it opens without asking, when
// it has no session bus to reach the desktop's portal over:
// xdg-settings, asked first whether the browser is itself the one for such
// addresses, xdg-email and xdg-open, and the browsers xdg-open goes on to.
const HANDLERS = ["xdg-open", "xdg-email", "xdg-settings", "x-www-browser", "www-browser", "sensible-browser"];
// Where the browser gets those stand-ins, no session bus and no display: on
// Linux, and on the other systems whose Chrome hands such addresses on
// through PATH or the session bus, not macOS or Windows.
const STAND_INS = process.platform !== "win32" && process.platform !== "darwin";

// A path as a D-Bus address writes it: each byte but a letter, a digit and
// -_/.\* as %xx.
const busPath = (file) => Array.from(Buffer.from(file, "utf8"), (byte) => (/[-0-9A-Za-z_/.\\*]/.test(String.fromCharCode(byte)) ? String.fromCharCode(byte) : `%${byte.toString(16).padStart(2, "0")}`)).join("");

// A folder in the profile of stand-ins for those programs, put first on the
// browser's PATH, so that the system finds them instead: each a link to the
// system's own true, which does nothing and exits 0. A folder on a disk
// mounted noexec takes such a link as well, since the system runs the file
// it leads to. Where there is no true, each is a link to itself, which the
// system cannot follow, so its search ends there and starts nothing.
function standIns(profile) {
  const dir = path.join(profile, "stand-ins");
  fs.mkdirSync(dir, { mode: 0o700 });
  const nothing = ["/usr/bin/true", "/bin/true"].find((file) => !wrongWith(file));
  for (const name of HANDLERS) {
    const at = path.join(dir, name);
    fs.symlinkSync(nothing || at, at);
  }
  return dir;
}

// Chrome writes the first bytes of a file a page starts to download before
// it refuses the download (see launch), in a hidden file in the user's
// Downloads folder, .com.google.Chrome. and six letters, and removes it a
// moment later: a run stopped in that moment left the site's bytes there,
// and now and then the browser leaves the file there empty. On Linux and
// the other systems that get stand-ins, the browser finds that folder as
// xdg-user-dirs names it, in user-dirs.dirs in the config folder
// (XDG_CONFIG_HOME, ~/.config by default), so it is given a config folder in
// its profile whose user-dirs.dirs names the profile's own Downloads folder,
// which goes with the profile. That config folder links to every other
// entry of the user's own, so the browser reads the user's font and other
// settings as before; the links go with the profile, and what they lead to
// stays. Gives that config folder, and keeps the name of each link in
// linked.
function downloadsIn(profile, linked) {
  const config = path.join(profile, "config");
  const downloads = path.join(profile, "Downloads");
  fs.mkdirSync(config, { mode: 0o700 });
  fs.mkdirSync(downloads, { mode: 0o700 });
  const given = process.env.XDG_CONFIG_HOME;
  const own = path.resolve(given && path.isAbsolute(given) ? given : path.join(process.env.HOME || os.homedir(), ".config"));
  let names = [];
  try {
    names = fs.readdirSync(own);
  } catch {
    // None, or not to be read: there is nothing to keep.
  }
  for (const name of names) {
    if (name === "user-dirs.dirs") continue;
    try {
      fs.symlinkSync(path.join(own, name), path.join(config, name));
      linked.push(name);
    } catch {
      // Left out.
    }
  }
  // The path in double quotes, with a backslash before a quote, a
  // backslash, a $ or a backquote, as the file is read.
  fs.writeFileSync(path.join(config, "user-dirs.dirs"), `XDG_DOWNLOAD_DIR="${downloads.replace(/["\\$`]/g, (c) => `\\${c}`)}"\n`);
  return config;
}

// The browsers this process has open, so that a run that is stopped can end
// them at once instead of leaving them running.
const open = new Set();

// How long a wait on the browser may last: what the run has left, at least a
// second, and no more than cap where one is given. A busy machine can keep a
// browser from answering for many seconds, so the run's own limit, and not a
// fixed one, says how long its start, its tab and the connection to it are
// waited for.
const browserWait = (cap = Infinity) => Math.max(1_000, Math.min(cap, LONGEST_TIMER, timeLeft()));

// What the browser did, as an error whose words can start a sentence or
// follow "The card could not be drawn:", marked browserSaid. A run that ends
// on one adds what to do (noKit).
const browserSaid = (words, more = {}) => Object.assign(new Error(words), { browserSaid: true, outOfTime: false, ...more });

// A wait on the browser that ran out: what did not answer, and for how long.
// Its outOfTime says the run has used up its own time.
function noAnswer(what, ms) {
  const spent = outOfTime();
  return browserSaid(`${what} ${spent ? "before the run's time ran out" : `in ${Math.round(ms / 1_000)} s`}`, { noAnswer: true, outOfTime: spent });
}

const noKit = (err) => Object.assign(new Error(`${err.message}, so no kit was made. ${err.outOfTime ? "Try again, or give it more time with --timeout." : "Try again."}`), { outOfTime: err.outOfTime });

// The folders browsers of Chrome's kind make in the temp folder, by the
// name each one gives them: the one that holds the socket that makes a
// browser one per profile, and those its component updater downloads and
// unpacks into in the browser's first seconds. A browser that ends then
// leaves those, empty or with what it was fetching.
const TEMP_NAME = /^\.?(com\.google\.Chrome|org\.chromium\.Chromium|com\.microsoft\.Edge|com\.brave\.Browser)\./;
const FETCHING = /(url_fetcher_|Unpacker_BeginUnzipping)\./;

function tempNames(temp) {
  try {
    return new Set(fs.readdirSync(temp).filter((name) => TEMP_NAME.test(name)));
  } catch {
    return new Set();
  }
}

// Once a browser has ended: the folders of this user's that came in the
// temp folder while it ran. A browser that ends while its component updater
// fetches or unpacks something leaves those folders with what is in them,
// whether it was killed or quit when asked, so they go with their files.
// Any other folder goes only when it is empty, so one that another browser
// is using, like the one that holds its socket, keeps its files. Another
// browser that fetched a component at that moment loses only that
// download; its pages are not touched.
function removeTemps({ temp, before }) {
  const uid = process.getuid ? process.getuid() : null;
  for (const name of tempNames(temp)) {
    if (before.has(name)) continue;
    const at = path.join(temp, name);
    try {
      const stat = fs.lstatSync(at);
      if (!stat.isDirectory() || (uid !== null && stat.uid !== uid)) continue;
      if (FETCHING.test(name)) fs.rmSync(at, { recursive: true, force: true });
      else fs.rmdirSync(at);
    } catch {
      // Not empty, or gone.
    }
  }
}

// When a process started, on Linux, from /proc/<pid>/stat, so that a pid
// that has come round again on another process is not taken for it: null
// once it has ended (a zombie has ended too).
function startOf(pid) {
  try {
    const stat = fs.readFileSync(`/proc/${pid}/stat`, "utf8");
    const fields = stat.slice(stat.lastIndexOf(")") + 2).split(" ");
    return fields[0] === "Z" || fields[0] === "X" ? null : fields[19];
  } catch {
    return null;
  }
}

// The processes that run on Linux, but this one: the parent of each, and,
// given a tag, those whose command line holds it.
function scan(tag = "") {
  const parentOf = new Map();
  const named = [];
  let names = [];
  try {
    names = fs.readdirSync("/proc");
  } catch {
    return { parentOf, named };
  }
  for (const name of names) {
    const pid = Number(name);
    if (!/^\d+$/.test(name) || pid === process.pid) continue;
    try {
      const stat = fs.readFileSync(`/proc/${pid}/stat`, "utf8");
      const [state, ppid] = stat.slice(stat.lastIndexOf(")") + 2).split(" ");
      if (state === "Z" || state === "X") continue;
      parentOf.set(pid, Number(ppid));
      if (tag && fs.readFileSync(`/proc/${pid}/cmdline`, "utf8").includes(tag)) named.push(pid);
    } catch {
      // Gone already.
    }
  }
  return { parentOf, named };
}

// A browser's processes on Linux: the browser and those that descend from
// it. Other systems give none, and so does a browser that has ended, whose
// pid can be another process's by now: its helpers are found by the profile
// they name (see endAll).
function processesOf(child) {
  if (process.platform !== "linux" || !child.pid || child.exitCode !== null || child.signalCode !== null) return [];
  const { parentOf } = scan();
  const found = new Set([child.pid]);
  for (let grew = true; grew; ) {
    grew = false;
    for (const [pid, ppid] of parentOf) {
      if (!found.has(pid) && found.has(ppid)) {
        found.add(pid);
        grew = true;
      }
    }
  }
  return [...found].map((pid) => ({ pid, start: startOf(pid) })).filter(({ start }) => start !== null);
}

// The crash handler a browser's processes name, on Linux, which Chrome starts
// apart from them: it is no child of theirs, so it is found by the pid
// their --crashpad-handler-pid gives. Since its reports go into the profile,
// its --database names the profile too, and so endAll, which looks for the
// processes that name the profile, also finds it and the process that
// watches it. Ctrl-\ reaches the browser's helpers too, each of them asks
// it for a crash report, and it takes hold of each one to write it. A
// helper killed while it is held stays until the handler lets go of it,
// which it can fail to do for good. So it goes with them: the one named,
// only when it is a crash handler by the name /proc gives it (the first 15
// characters of its program's name, chrome_crashpad or msedge_crashpad)
// and it started with them or after them. Chrome rewrites a helper's
// command line with spaces between its arguments. null when none is named.
function crashHandlerOf(processes) {
  if (process.platform !== "linux" || !processes.length) return null;
  const oldest = Math.min(...processes.map(({ start }) => Number(start)));
  for (const { pid } of processes) {
    let line = "";
    try {
      line = fs.readFileSync(`/proc/${pid}/cmdline`, "utf8");
    } catch {
      continue;
    }
    const named = /(?:^|[\0 ])--crashpad-handler-pid=(\d+)(?=[\0 ]|$)/.exec(line);
    if (!named) continue;
    // 0 where Chrome runs without one.
    const handler = Number(named[1]);
    if (handler <= 1 || handler === process.pid) return null;
    try {
      if (!/crashpad/.test(fs.readFileSync(`/proc/${handler}/comm`, "utf8"))) return null;
    } catch {
      return null;
    }
    const start = startOf(handler);
    return start === null || Number(start) < oldest ? null : { pid: handler, start };
  }
  return null;
}

// A browser's processes and its crash handler, known from its launch or
// named by them now.
function withCrashHandler(entry, processes) {
  const handler = entry.crashHandler || crashHandlerOf(processes);
  return handler && !processes.some(({ pid }) => pid === handler.pid) ? [...processes, handler] : processes;
}

// Each of them that still runs, killed.
function killAll(processes) {
  for (const { pid, start } of processes) {
    if (startOf(pid) !== start) continue;
    try {
      process.kill(pid, "SIGKILL");
    } catch {
      // Gone already.
    }
  }
}
const allGone = (processes) => processes.every(({ pid, start }) => startOf(pid) !== start);

const pause = (ms) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);

// Each of a browser's processes that still runs, killed, and then each
// process whose command line names its profile, as Chrome's helpers do:
// they are found that way also once the browser has ended and they belong
// to no one, and one of them can start another a moment before it is
// killed, which would write into the profile after it was removed. Looked
// for again until a look finds none and all have ended, a second at most.
// Chrome's network service writes into the profile as it ends, so the
// profile can be removed for good only once they are all gone. Gives back
// every process it killed.
function endAll(processes, profile) {
  const ended = [...processes];
  killAll(ended);
  if (process.platform !== "linux") return ended;
  const tag = path.basename(profile);
  for (let waited = 0; waited < 1_000; waited += 20) {
    const late = scan(tag)
      .named.map((pid) => ({ pid, start: startOf(pid) }))
      .filter(({ pid, start }) => start !== null && !ended.some((known) => known.pid === pid && known.start === start));
    if (!late.length && allGone(ended)) break;
    killAll(late);
    ended.push(...late);
    pause(20);
  }
  return ended;
}

// What fs says of a write that found no room: a full disk, or a user's quota
// used up.
const NO_ROOM = new Set(["ENOSPC", "EDQUOT"]);
// A disk with less room than this left has none for a browser's profile.
const ROOM = 64 * 1024;

// Whether the disk that holds the profile takes ROOM more bytes, asked by
// writing them: the error of a write that found no room, with the path
// written, or null. A full disk and a quota used up look the same to the
// browser, and only a write tells them apart.
function noRoomIn(profile) {
  const probe = path.join(profile, "easybrandkit-room");
  try {
    fs.writeFileSync(probe, Buffer.alloc(ROOM));
    return null;
  } catch (err) {
    return NO_ROOM.has(err.code) ? Object.assign(err, { path: err.path || probe }) : null;
  } finally {
    try {
      fs.rmSync(probe, { force: true });
    } catch {
      // Removed with the profile.
    }
  }
}

// Whether the disk that holds the temp folder shows next to no room.
function lowOnRoom(temp) {
  try {
    const { bavail, bsize } = fs.statfsSync(temp);
    return bavail * bsize < ROOM;
  } catch {
    return false;
  }
}

// How long a browser is given to quit when asked, its answers included,
// while the run still has time.
const QUIT_WAIT = 9_000;
// How long a browser asked to quit has to say that it heard: one that does
// not is killed then.
const HEARD_WAIT = 2_000;
// A disk that shows next to no room this long has none for a profile.
const LOW_WAIT = 3_000;

// --use-mock-keychain and --password-store=basic keep Chrome on macOS from
// asking for the login keychain, which it does for a fresh profile. The
// profile is a temp folder; the user's own home and browser are untouched.
// guard is the run's rule for the addresses the browser may open and ask
// for (see address.js guardFor, holdDocuments below and proxy.js); a
// browser started without one opens no web page.
async function launch({ width, height }, { guard = null } = {}) {
  // A browser that cannot be started is told before anything is made.
  const place = browserPlace();
  // The temp folder by its full path, which the browser is given as its
  // TMPDIR too: from a relative one, the profile, the download folder its
  // Preferences name, its stand-ins, its bus and its display would all be
  // relative, and the browser takes no relative download folder, so it
  // saved into the Downloads folder of the user it runs as.
  const temp = path.resolve(os.tmpdir());
  // The folders of PATH are parted by its delimiter, so a folder of stand-ins
  // in a temp folder whose path has one in it could not come first on the
  // browser's PATH (see below), and the browser would find the real programs.
  if (STAND_INS && temp.includes(path.delimiter)) {
    throw new Error(`${place.name} was not started: the path of the temp folder, ${temp}, has a ${path.delimiter} in it, which parts the folders of PATH, so the stand-ins that keep a site from starting a program of this machine could not come first on the browser's PATH. Set TMPDIR to a folder whose path has none.`);
  }
  const before = tempNames(temp);
  const profile = fs.mkdtempSync(path.join(temp, "easybrandkit-chrome-"));
  // The links made in its config folder (see downloadsIn).
  const linked = [];
  // What is made in the profile before the browser starts: on a disk with
  // no room for it, the browser would have none for its own files either,
  // and would wait for the run's whole time.
  const room = (err, at) => {
    dropProfile();
    return NO_ROOM.has(err.code) ? Object.assign(err, { path: err.path || at }) : null;
  };
  // The profile removed. With no file left to open, a folder cannot be
  // listed, so what was made in it is removed by name.
  const dropProfile = () => {
    try {
      fs.rmSync(profile, { recursive: true, force: true });
      return;
    } catch {
      // Too short of files to list it.
    }
    const stands = path.join(profile, "stand-ins");
    const config = path.join(profile, "config");
    for (const file of [path.join(profile, "Default", "Preferences"), path.join(profile, "Local State"), path.join(profile, "easybrandkit-output"), ...HANDLERS.map((name) => path.join(stands, name)), ...linked.map((name) => path.join(config, name)), path.join(config, "user-dirs.dirs")]) {
      try {
        fs.unlinkSync(file);
      } catch {
        // Not made.
      }
    }
    for (const dir of [path.join(profile, "Default"), stands, config, path.join(profile, "Downloads"), profile]) {
      try {
        fs.rmdirSync(dir);
      } catch {
        // Not made, or left for the system's temp clean-up.
      }
    }
  };
  // A download that starts while the browser takes no refusal (see below)
  // goes into the throwaway profile and is removed with it, not into the
  // Downloads folder of the user the browser runs as. The browser also
  // makes no connection ahead of a request and preloads no page
  // (network_prediction_options 2, never): with its default, it connected to
  // the address of a page's frame or of a page's move before the kit had
  // judged that address, and the address refused there still got the
  // connection, with no request in it, and a page's speculation rules had it
  // fetch an address ahead of the page's move there. The kit's proxy holds
  // each of those requests to the rule now (see proxy.js), but a move served
  // from such a copy is still no document the rule for pages holds, which
  // tells where a page led: each tab the kit reads pages in asks the browser
  // whether it took that (see noPreloading). It takes no signed exchange
  // either (web_package.signed_exchange.enabled): with its default, a page,
  // a frame or a prefetch that answered with one had the browser fetch the
  // certificate the exchange names, at any https address and port the site
  // wrote there, a request of its own that is no document, which the proxy
  // holds to the rule now as well, and show what the exchange holds under
  // another address than the one it came from. A browser that asks for them
  // all the same is told by the first document it asks for (see
  // holdDocuments). Its WebRTC sends UDP to a proxy's alone
  // (webrtc.ip_handling_policy, as the switch below says too), and has no
  // handling of its own for any site (webrtc.ip_handling_url, an empty
  // list): a Chrome policy that recommends WebRTC's handling for some sites
  // alone (WebRtcIPHandlingUrl) comes before the switch for those sites, so
  // a page of such a site had the browser send UDP to any address, past the
  // proxy and past the kit's check of its WebRTC, which asks at an address
  // of its own (see udpPastProxy). A user's own setting, which this profile
  // is, comes before a recommended policy; a managed one comes before it,
  // which the README says.
  const preferences = path.join(profile, "Default", "Preferences");
  try {
    fs.mkdirSync(path.join(profile, "Default"));
    fs.writeFileSync(preferences, JSON.stringify({ download: { default_directory: path.join(profile, "Downloads"), prompt_for_download: false }, net: { network_prediction_options: 2 }, web_package: { signed_exchange: { enabled: false } }, webrtc: { ip_handling_policy: "disable_non_proxied_udp", ip_handling_url: [] } }));
  } catch (err) {
    // For anything but no room, the refusal still holds.
    if (NO_ROOM.has(err.code)) throw room(err, preferences);
  }
  // The browser asks no DNS over HTTPS server of its own (dns_over_https.mode
  // off, in its Local State, where Chrome keeps it): with its default, where
  // the system's resolver is one Chrome takes as a provider of DNS over
  // HTTPS, as 8.8.8.8, 1.1.1.1 or 9.9.9.9 are, it asked the resolver for
  // that provider's server, as dns.google, and connected to it on port 443
  // itself, as Chrome sends what it asks such a server past any proxy, the
  // kit's too. No page chooses that server. The browser's own lookup, which
  // fails every name but 127.0.0.1 (see --host-resolver-rules below), holds
  // that as well: a Chrome policy (DnsOverHttpsMode), which can turn it on
  // again and which the kit cannot tell, has the browser reach its server
  // only where the policy names it at 127.0.0.1. No check of the kit's
  // tells the setting, so a browser whose Local State could not be written
  // is not started: one that failed in another way than for room, as on a
  // failing disk, started the browser with Chrome's default.
  const localState = path.join(profile, "Local State");
  try {
    fs.writeFileSync(localState, JSON.stringify({ dns_over_https: { mode: "off" } }));
  } catch (err) {
    const full = room(err, localState);
    if (full) throw full;
    throw new Error(`${place.name} was not started: easybrandkit could not write the browser's Local State, which turns its own DNS over HTTPS off, in ${temp}: ${systemWords(err)}.${moreFiles(err)}`);
  }
  // Chrome on Linux has its crash handler write the reports of its processes
  // into the user's own browser's folder (~/.config/google-chrome/Crash
  // Reports), where nothing removes them; Ctrl-\ asks for one from each of
  // its helpers. BREAKPAD_DUMP_LOCATION puts them in the throwaway profile.
  const env = { ...process.env, TMPDIR: temp, BREAKPAD_DUMP_LOCATION: path.join(profile, "Crash Reports") };
  // A site can send the browser to mailto:, news: or snews:, which Chrome
  // on Linux hands on without asking: over the session bus to the desktop's
  // portal, which starts the user's own mail program with the site's
  // address, and with no session bus, to a program of the machine it finds
  // through PATH, as the user who runs the kit. So the browser gets a
  // session bus where nothing listens, a socket in its profile that is never
  // made (left unset, libdbus can look for the desktop's own bus in
  // XDG_RUNTIME_DIR), no display, which a headless browser does not use and
  // a program it starts could open a window on, and the stand-ins first on
  // its PATH, the rest as it was. No display is DISPLAY unset and
  // WAYLAND_DISPLAY another socket in its profile that is never made, which
  // libwayland, as the path starts with /, takes as the socket itself: left
  // unset, it looks for the desktop's own wayland-0 in XDG_RUNTIME_DIR. A
  // WAYLAND_SOCKET would name a connection it has open already. On macOS
  // and Windows the browser asks the system instead, and the guard in each
  // page (openPage) is what holds there.
  if (STAND_INS) {
    try {
      env.PATH = [standIns(profile), process.env.PATH || "/usr/local/bin:/usr/bin:/bin"].join(path.delimiter);
    } catch (err) {
      const full = room(err, path.join(profile, "stand-ins"));
      if (full) throw full;
      throw new Error(`${place.name} was not started: easybrandkit could not make the stand-ins it starts the browser with in ${temp}, which keep a site from starting a program of this machine: ${systemWords(err)}.${moreFiles(err)}`);
    }
    try {
      env.XDG_CONFIG_HOME = downloadsIn(profile, linked);
    } catch (err) {
      const full = room(err, path.join(profile, "config"));
      if (full) throw full;
      throw new Error(`${place.name} was not started: easybrandkit could not make the folder the browser's downloads go into in ${temp}, which keeps the first bytes of a download out of your Downloads folder: ${systemWords(err)}.${moreFiles(err)}`);
    }
    env.DBUS_SESSION_BUS_ADDRESS = `unix:path=${busPath(path.join(profile, "no-bus"))}`;
    env.WAYLAND_DISPLAY = path.join(profile, "no-display");
    delete env.WAYLAND_SOCKET;
    delete env.DISPLAY;
  }
  // What the browser prints, in one file in the profile, in the order it
  // printed it: its first line says why one that ends before it answers
  // did, and nothing has to read it while the browser runs.
  const output = path.join(profile, "easybrandkit-output");
  let printing;
  try {
    printing = fs.openSync(output, "a", 0o600);
  } catch (err) {
    const full = room(err, output);
    if (full) throw full;
    throw new Error(couldNotStart(place, err));
  }
  // The proxy every request of the browser goes through (see proxy.js),
  // on a port of 127.0.0.1 the system picks, for as long as the browser
  // runs.
  let proxy;
  try {
    proxy = await startProxy(guard);
  } catch (err) {
    fs.closeSync(printing);
    dropProfile();
    throw new Error(`${place.name} was not started: easybrandkit could not start the proxy that every request of the browser goes through, on 127.0.0.1: ${systemWords(err)}.${moreFiles(err)}`);
  }
  // --remote-debugging-pipe: the browser takes the DevTools protocol on its
  // file descriptors 3 and 4, which only this process holds, and opens no
  // port for it.
  let child;
  try {
    child = spawn(
      place.file,
      [
        "--headless=new",
        "--remote-debugging-pipe",
        `--user-data-dir=${profile}`,
        `--window-size=${width},${height}`,
        "--hide-scrollbars",
        "--mute-audio",
        // No sound output either, which on Linux has the browser play a
        // page's sound into nothing, so it reaches no sound server or sound
        // device of this machine. With --mute-audio alone, a page that made
        // an AudioContext had the browser connect to the sound server in
        // XDG_RUNTIME_DIR, the desktop's own, and where XDG_RUNTIME_DIR is
        // unset, as in a container, a cron job or a CI box, PulseAudio's
        // client made a folder for it in the temp folder, pulse- and 12
        // letters or digits, and kept its link to that folder in pulse/ of
        // the config folder, which is in the profile (see downloadsIn) and
        // goes with it: each such run left one more empty folder there.
        "--disable-audio-output",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-sync",
        "--use-mock-keychain",
        "--password-store=basic",
        // No HTTP/3: with it, a site's Alt-Svc answer sends the browser's
        // next requests for an address of the site to another port, or to
        // another host, over UDP, past the address the run's rule judged
        // (see holdDocuments); over TCP each goes to the host and port its
        // address names.
        "--disable-quic",
        // An http address is asked for over http, as it is written: Chrome
        // tries one over https first by itself (HTTPS-Upgrades, and on
        // Chrome 157 HTTPS-First, which then refuses a site that answers on
        // no https), at an address on port 443 that the run was not given,
        // so a site of this machine or of a private network by a name under
        // a public suffix was refused before the browser tried http. It also
        // moves one to https without asking http at all when the name's DNS
        // gives an HTTPS record (UseDnsHttpsSvcb), as every name behind
        // Cloudflare does, and then a site of this machine or of a private
        // network by such a name was refused the same way. A site that wants
        // https sends its visitors there itself, and a name the browser
        // takes only over https (HSTS), as every .dev and .app name, is
        // still asked for over https (see address.js guardFor). Without the
        // HTTPS record, the browser gives up only Encrypted Client Hello and
        // the record's ALPN, and HTTP/3 is off already.
        //
        // No Reporting API and no Web Payments either: the browser itself
        // sent a page's reports (Reporting-Endpoints with a policy's
        // report-to, Report-To with NEL) and fetched a payment method's
        // manifest (PaymentRequest's canMakePayment) at any https address
        // and port the page named, past the rule (see holdDocuments) and
        // past Chrome's own refusal of a public page's requests to this
        // machine, so a site sent a CORS preflight or a HEAD, with a path
        // of its choosing, to another program of this machine or of its
        // network whose certificate the machine trusts. The kit's proxy
        // holds those requests now as well.
        //
        // No media router either (MediaRouter): a page that asks whether a
        // cast device is there (the Presentation API) had the browser search
        // this machine's networks for one, over SSDP and mDNS multicast,
        // which goes past any proxy. Nor WebRTC's mDNS names for this
        // machine's own addresses (WebRtcHideLocalIpsWithMdns), for which
        // the browser joined the mDNS group on each of this machine's
        // networks as a page made a connection, though its WebRTC gathers no
        // address of this machine (see --webrtc-ip-handling-policy below).
        "--disable-features=HttpsUpgrades,HttpsFirstBalancedModeAutoEnable,UseDnsHttpsSvcb,Reporting,WebPayments,MediaRouter,WebRtcHideLocalIpsWithMdns",
        // The browser looks no name up itself: every request it makes goes
        // through the kit's proxy, which looks each name up with the run's
        // own lookup (see address.js), so every name fails in the browser
        // but 127.0.0.1, the proxy's own address. With its own lookup, a
        // page's WebRTC had it look up the names the page gave as the
        // remote addresses of a connection, past the proxy: a name under
        // .local by mDNS on each of this machine's networks, in a packet of
        // the page's choosing, and any other by the system's resolver. The
        // server of DNS over HTTPS a Chrome policy names fails the same way,
        // by its name or its address, unless that is 127.0.0.1.
        // ^NOTFOUND fails a name; ~NOTFOUND only changes it, which still had
        // the browser ask the network for ~NOTFOUND.
        "--host-resolver-rules=MAP * ^NOTFOUND, EXCLUDE 127.0.0.1",
        // Every request through the kit's proxy, this machine's own
        // addresses' too, which the browser otherwise sends past a proxy
        // (<-loopback> takes them off its list of addresses that go past
        // it). WebRTC sends UDP around a proxy, so it may send none that
        // does not go through one, and this proxy takes none: the switch
        // and the profile's webrtc settings (see Preferences above) hold
        // that, as the kit checks before any page is opened (see
        // udpPastProxy), but for a site a managed Chrome policy sets
        // WebRTC's handling for, and its TURN over TCP goes through the
        // proxy.
        `--proxy-server=http://127.0.0.1:${proxy.port}`,
        "--proxy-bypass-list=<-loopback>",
        "--webrtc-ip-handling-policy=disable_non_proxied_udp",
        // The browser's own push channel (GCM), which no page needs, checks
        // in and then connects to mtalk.google.com on port 5228, which the
        // proxy refuses: its addresses are the proxy's own name, which the
        // proxy answers itself (see proxy.js).
        `--gcm-checkin-url=https://${OWN_NAME}/checkin`,
        `--gcm-mcs-endpoint=https://${OWN_NAME}/`,
        `--gcm-registration-url=https://${OWN_NAME}/register`,
        // Chrome refuses to start as root without it (a container, a CI box).
        ...(process.getuid && process.getuid() === 0 ? ["--no-sandbox"] : []),
        "about:blank",
      ],
      { stdio: ["ignore", printing, printing, "pipe", "pipe"], env },
    );
  } catch (err) {
    // A program the system will not start in a way Node does not hand back
    // as an event.
    fs.closeSync(printing);
    proxy.close();
    room(err, output);
    throw new Error(couldNotStart(place, err));
  }
  fs.closeSync(printing);
  // How the browser ended, and the error the system gave if it could not
  // start it at all.
  let exited = false;
  let ending = { code: null, signal: null };
  let notStarted = null;
  // Out of files to start it with, the system gives no pipe at all, and its
  // error comes a moment later.
  if (!(child.stdio && child.stdio[3])) {
    const err = await new Promise((resolve) => child.once("error", resolve));
    proxy.close();
    room(err, output);
    throw new Error(couldNotStart(place, err));
  }
  const pipe = pipeOf(child.stdio[3], child.stdio[4]);
  const ended = () => {
    exited = true;
    pipe.end();
  };
  child.on("exit", (code, signal) => {
    ending = { code, signal };
    ended();
  });
  child.on("error", (err) => {
    notStarted = err;
    ended();
  });
  const entry = { child, profile, temp, before, proxy };
  open.add(entry);
  // Whether the browser has answered on its pipe: one that never has is not
  // asked to quit.
  let answered = false;
  // Chrome is asked to quit first: killed outright, its helper processes go
  // on writing to the profile for a while. Those still there once it has
  // quit are killed, and the profile is removed once they are gone. A
  // profile that still cannot be removed is left in the temp folder; the
  // kit is not lost over it. A browser that does not say that it heard
  // within 2 s is killed then. Asking it and waiting for it to end take a
  // second in all once the run's time is up, or when the browser has just
  // not answered (hurry), so that one that does not quit is killed then and
  // does not keep the run going past its limit.
  const close = async ({ hurry = false } = {}) => {
    // The browser's processes as they are now, with its crash handler; its
    // helpers, which name the profile, are found also once it has ended, as
    // one that could not start has.
    const processes = withCrashHandler(entry, processesOf(child));
    if (answered && !exited && !pipe.ended()) {
      const until = Date.now() + (hurry || outOfTime() ? 1_000 : QUIT_WAIT);
      let heard = null;
      pipe.send("Browser.close", {}, Math.max(1, Math.min(HEARD_WAIT, until - Date.now()))).then(
        () => (heard = true),
        () => (heard = false),
      );
      while (!exited && heard !== false && Date.now() < until) await sleep(50);
    }
    if (!exited) child.kill("SIGKILL");
    for (let i = 0; i < 20 && !exited; i++) await sleep(100);
    pipe.end();
    proxy.close();
    endAll(processes, profile);
    open.delete(entry);
    removeSingleton(profile, entry.singleton);
    try {
      fs.rmSync(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
    } catch {
      // Left for the system's temp clean-up.
    }
    removeTemps(entry);
  };
  // Whether the browser still runs: one that was killed or crashed has
  // ended, and its pipe with it. One that is slow to answer, on a busy
  // machine, still runs, and so does one that has not ended when it is not
  // asked (ms 0).
  const alive = async (ms = 5_000) => {
    if (exited || pipe.ended()) return false;
    if (!ms) return true;
    try {
      await pipe.send("Browser.getVersion", {}, ms);
      return !exited;
    } catch (err) {
      return !exited && Boolean(err.timedOut);
    }
  };
  // A new tab, waited for ms at most: its id. One opened in the background
  // leaves the tab in front as it was: a page there is not told that it is
  // hidden, which it can answer by moving on. One opened in a window of its
  // own (window) is the tab in front of that window, which the browser draws
  // as it draws any tab in front; with background, the window in front
  // stays so.
  const newTab = async (ms, { background = false, window = false } = {}) => {
    try {
      const { targetId } = await pipe.send("Target.createTarget", { url: "about:blank", ...(background ? { background: true } : {}), ...(window ? { newWindow: true } : {}) }, ms);
      return targetId;
    } catch (err) {
      if (err.timedOut) throw noAnswer("The browser did not open a tab", ms);
      if (err.closed) throw err;
      throw browserSaid("The browser refused to open a tab");
    }
  };
  // A tab closed, waited for ms at most; the browser goes on.
  const closeTab = (targetId, ms = 5_000) => pipe.send("Target.closeTarget", { targetId }, ms).then(
    () => {},
    () => {},
  );
  // The browser answers on its pipe once it has started, which a busy
  // machine can keep it from doing for a while: that is waited for as long
  // as the run has left, also when CHROME_PATH names a program that takes
  // long before it starts the browser. Looked at once a second, a browser
  // that never will is told before then: one with no room for its profile
  // in the temp folder.
  const wait = browserWait();
  let said = null;
  pipe.send("Browser.getVersion", {}, wait).then(
    (version) => (said = { version }),
    (err) => (said = { err }),
  );
  let lowSince = 0;
  for (let looked = Date.now(); !said && !exited; ) {
    await sleep(100);
    if (Date.now() - looked < 1_000) continue;
    looked = Date.now();
    lowSince = lowOnRoom(temp) ? lowSince || looked : 0;
    if (lowSince && looked - lowSince >= LOW_WAIT) {
      const full = noRoomIn(profile);
      if (full) {
        await close();
        throw full;
      }
      lowSince = 0;
    }
  }
  if (said && !said.err) {
    answered = true;
    // Known from the start: by the time the browser is stopped, its
    // helpers can have ended, and its link to the folder of its socket
    // can be gone.
    entry.crashHandler = crashHandlerOf(processesOf(child));
    entry.singleton = singletonOf(profile, temp);
    // A site can make a browser save a file, into the Downloads folder of
    // the user it runs as, where nothing removes it. This browser saves none:
    // said once to the whole browser over its pipe, the refusal holds for as
    // long as the browser runs, for every tab, and before any page is
    // opened. A browser too busy to answer it in the time the run has left
    // ends the run, as one that does not start does: let go on, it would read
    // the site with nothing refused. One that answers that it does not take
    // it goes on: a download then lands in the throwaway profile.
    const refusal = browserWait();
    try {
      await pipe.send("Browser.setDownloadBehavior", { behavior: "deny" }, refusal);
    } catch (err) {
      if (err.timedOut) {
        await close({ hurry: true });
        throw noKit(noAnswer("The browser did not answer the kit's request to refuse downloads", refusal));
      }
    }
    // Every request goes through the kit's proxy, as the browser is started
    // to: asked before any page is opened. A browser that sends one past it
    // or elsewhere, or does not answer, ends the run.
    const probing = browserWait();
    let missed;
    try {
      missed = await throughProxy(pipe, proxy, probing);
    } catch (err) {
      await close({ hurry: Boolean(err.timedOut || err.noAnswer) });
      if (err.timedOut || err.noAnswer) throw noKit(noAnswer("The browser did not answer the kit's check that it sends its requests through the kit's proxy", probing));
      if (err.closed) throw noKit(browserSaid("The browser ended before it took the kit's check that it sends its requests through the kit's proxy"));
      // The same browser refuses it again: another one is what helps.
      throw new Error(`The browser refused the kit's check that it sends its requests through the kit's proxy (${plainWords(err.message)}), so no kit was made: point CHROME_PATH at another browser, such as Google Chrome.`);
    }
    if (missed) {
      await close();
      throw new Error(missedProxy(missed, proxy));
    }
    // Every document the browser loads is judged by the run's rule before
    // it is asked for, also for the whole browser and before any page is
    // opened. A browser that does not take that, in the time the run has
    // left or at all, ends the run: let go on, it would open any address a
    // site leads it to.
    const tabs = new Map();
    const holding = browserWait();
    try {
      await holdDocuments(pipe, tabs, guard ? guard.judge : null, holding);
    } catch (err) {
      await close({ hurry: Boolean(err.timedOut) });
      if (err.timedOut) throw noKit(noAnswer("The browser did not answer the kit's request to judge the pages it opens", holding));
      if (err.closed) throw noKit(browserSaid("The browser ended before it took the kit's request to judge the pages it opens"));
      // The same browser refuses it again: another one is what helps.
      throw new Error("The browser refused the kit's request to judge the pages it opens, so no kit was made. It cannot hold its pages to the kit's rule for the addresses they open: point CHROME_PATH at another browser, such as Google Chrome.");
    }
    // sandboxed: a browser installed as a snap or a Flatpak, in whose
    // sandbox the stand-ins and the bus may not be the ones it finds. tabs:
    // the tabs the kit reads pages in, by their ids (see openPage). proxy:
    // the one its requests go through, with what it refused (see
    // proxyNotes).
    return { close, alive, newTab, closeTab, attach: (targetId, ms) => pipe.attach(targetId, ms), sandboxed: ownSandbox(place.file), tabs, proxy };
  }
  // A browser's pipe closes as it ends, and can close a moment before the
  // system tells that it has ended: one whose pipe has closed is given a
  // second to end, so that it is told by how it ended. One that still runs
  // then has closed the pipe itself, as a program that starts the browser
  // without handing it the pipe does.
  const pipeClosed = Boolean(said && said.err && said.err.closed);
  for (let waited = 0; pipeClosed && !exited && waited < 1_000; waited += 50) await sleep(50);
  const running = !exited;
  // Told before close, which removes the folder the browser made and the
  // profile: a browser that ended at once can have found no room either.
  const tooLong = exited ? socketTooLong(temp, before) : 0;
  const full = exited && !tooLong ? noRoomIn(profile) : null;
  const printed = (exited && !notStarted) || pipeClosed ? firstBytes(output) : "";
  await close();
  if (tooLong) {
    throw new Error(`${place.name} did not start: the path of the temp folder, ${temp}, is too long for the socket the browser makes in it, whose path would be ${tooLong} bytes where Linux allows ${SOCKET_MAX}. Set TMPDIR to a folder whose path is at least ${tooLong - SOCKET_MAX} ${tooLong - SOCKET_MAX === 1 ? "byte" : "bytes"} shorter.`);
  }
  if (full) throw full;
  if (running && pipeClosed) throw new Error(closedEarly(place, { output: printed }));
  if (running) {
    const late = noKit(noAnswer(`${place.name} was started but did not answer`, wait));
    throw Object.assign(late, { message: `${late.message} If it happens again, point CHROME_PATH at another browser.` });
  }
  if (notStarted) throw new Error(couldNotStart(place, notStarted));
  throw new Error(endedEarly(place, { output: printed, ...ending }));
}

// A text of the browser's own, on one line, cut to 200 characters.
const plainWords = (text) => String(text || "").replace(/[\u0000-\u001f\u007f-\u009f]+/g, " ").slice(0, 200);

// The browser sends its requests through the kit's proxy, as it is started
// to (see launch): asked before any page is opened, in a tab of its own,
// with four addresses the proxy answers itself, by a word of its own in
// their paths: a name under .invalid, which no DNS answers, and this
// machine's 127.0.0.1, localhost and [::1] on the proxy's own port. Each
// has to come to the proxy as a request for the whole address, as a
// browser sends a proxy. One that comes to the proxy's port as an address
// of its own came past the proxy, and one that does not come went
// elsewhere: a Chrome policy (ProxyMode, ProxySettings, ProxyBypassList) or
// a program that starts the browser with switches of its own can make it do
// that. Then, in the same tab, the browser's WebRTC is to send no UDP (see
// udpPastProxy). null when all of it holds, else the first that did not:
// its number and what the browser said of it, { udp }, or { deaf } for a
// check of the browser's WebRTC that could not be made.
async function throughProxy(pipe, proxy, ms) {
  const addresses = [`http://${OWN_NAME}/${proxy.token}/1`, `http://127.0.0.1:${proxy.port}/${proxy.token}/2`, `http://localhost:${proxy.port}/${proxy.token}/3`, `http://[::1]:${proxy.port}/${proxy.token}/4`];
  let targetId;
  try {
    ({ targetId } = await pipe.send("Target.createTarget", { url: "about:blank", background: true }, ms));
  } catch (err) {
    if (err.timedOut) throw Object.assign(err, { noAnswer: true });
    throw err;
  }
  let cdp;
  try {
    cdp = await pipe.attach(targetId, ms);
  } catch (err) {
    pipe.send("Target.closeTarget", { targetId }, 5_000).catch(() => {});
    throw err;
  }
  try {
    // A browser whose connection to the proxy gets no answer, as behind a
    // firewall that drops it, waits for as long as the system tries, two
    // minutes and more on Linux: once it has asked for the first address,
    // a proxy that has taken no connection at all in 15 s is one it cannot
    // reach.
    let asked = null;
    const askedFirst = new Promise((resolve) => (asked = resolve));
    cdp.on("Network.requestWillBeSent", ({ request }) => request && request.url === addresses[0] && asked());
    await cdp.send("Network.enable", { maxTotalBufferSize: 0, maxResourceBufferSize: 0 }, ms);
    for (const [at, address] of addresses.entries()) {
      const n = at + 1;
      const navigating = cdp.send("Page.navigate", { url: address }, ms);
      let timer;
      const unreached = n === 1 ? askedFirst.then(() => new Promise((resolve) => (timer = setTimeout(() => resolve(!proxy.accepted), PROXY_CONNECT_WAIT)))) : new Promise(() => {});
      const told = await Promise.race([navigating.then((answer) => ({ answer })), unreached.then((none) => (none ? { none } : navigating.then((answer) => ({ answer }))))]).finally(() => clearTimeout(timer));
      if (told.none) {
        navigating.catch(() => {});
        return { n, errorText: "", unanswered: PROXY_CONNECT_WAIT };
      }
      if (!proxy.through.has(n)) return { n, errorText: told.answer.errorText || "" };
    }
    return await udpPastProxy(cdp, ms);
  } finally {
    cdp.close();
  }
}

// How long the browser is given to make its first connection to the proxy,
// once it has asked for the first address of the kit's check.
const PROXY_CONNECT_WAIT = 15_000;

// How long a datagram the kit sends its own STUN port is waited for: one on
// this machine's loopback comes at once.
const OWN_DATAGRAM_WAIT = 2_000;

// Whether the browser's WebRTC sends UDP, which goes around a proxy: asked
// in the tab of throughProxy, with a STUN server of this machine that the
// kit listens for itself, for as long as the browser gathers its ways to
// reach a peer, 1.5 s at most, and a moment after. Started as the kit
// starts it, the browser sends none, and gathers in a fraction of a second;
// a Chrome policy (WebRtcIPHandling) or a program that starts it with
// switches of its own can turn that back, and then its first STUN packet
// comes at once, and it gathers until its STUN request runs out, as the
// kit does not answer it. The check hears only what reaches that port, so
// a datagram of the kit's own is sent there first, from a socket of its
// own: one that does not come, as behind a firewall that drops UDP to
// 127.0.0.1, would leave it deaf to the browser's packets too, where it
// told nothing and the browser was used. A Chrome policy that sets
// WebRTC's handling for some sites alone (WebRtcIPHandlingUrl) holds for a
// tab while it shows a page of such a site, not this page of the kit's own,
// so the check does not tell it: the profile comes before such a policy set
// as a recommendation (see Preferences), and a managed one is named in the
// README's Limits. { udp } for a browser that sends UDP, { deaf } for a
// check that could not be made, the error of a socket that could not listen
// or true, else null.
async function udpPastProxy(cdp, ms) {
  const udp = dgram.createSocket("udp4");
  const mark = crypto.randomBytes(16);
  let packets = 0;
  let own = false;
  let came;
  const ownCame = new Promise((resolve) => (came = resolve));
  udp.on("message", (message) => {
    if (message.equals(mark)) {
      own = true;
      came();
    } else packets++;
  });
  try {
    await new Promise((resolve, reject) => {
      udp.once("error", reject);
      udp.bind(0, "127.0.0.1", resolve);
    });
  } catch (err) {
    udp.close();
    return { deaf: err };
  }
  udp.on("error", () => {});
  try {
    if (!(await ownDatagram(udp.address().port, mark, ownCame, () => own, Math.min(OWN_DATAGRAM_WAIT, ms)))) return { deaf: true };
    const expression = `(async () => {
      if (typeof RTCPeerConnection === "undefined") return "none";
      const peer = new RTCPeerConnection({ iceServers: [{ urls: "stun:127.0.0.1:${udp.address().port}" }] });
      peer.createDataChannel("easybrandkit");
      await peer.setLocalDescription(await peer.createOffer());
      await new Promise((done) => {
        if (peer.iceGatheringState === "complete") return done();
        peer.onicegatheringstatechange = () => peer.iceGatheringState === "complete" && done();
        setTimeout(done, 1500);
      });
      peer.close();
      return "asked";
    })()`;
    await cdp.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true }, ms);
    if (!packets) await sleep(50);
    return packets > 0 ? { udp: true } : null;
  } finally {
    udp.close();
  }
}

// Whether mark, sent to port on 127.0.0.1 from a socket of its own, came
// (came resolves then, and own() says so) within ms. A datagram that has
// come by the time ms runs out is read before that is decided: on a busy
// machine the timer and the datagram can be due at once, and the timer's
// turn comes first.
function ownDatagram(port, mark, came, own, ms) {
  const sender = dgram.createSocket("udp4");
  sender.on("error", () => {});
  let timer;
  const late = new Promise((resolve) => (timer = setTimeout(resolve, ms))).then(() => new Promise((resolve) => setImmediate(resolve)));
  const sent = new Promise((resolve) => sender.send(mark, port, "127.0.0.1", (err) => (err ? resolve() : null)));
  return Promise.race([came, late, sent]).then(() => {
    clearTimeout(timer);
    sender.close();
    return own();
  });
}

// The end of a run whose browser does not send a request of the kit's
// check through the kit's proxy, or whose WebRTC the kit could not check
// (see throughProxy).
function missedProxy({ n, errorText, udp, deaf, unanswered }, proxy) {
  const helps = "Lift that policy, or point CHROME_PATH at the browser's own program or at another browser.";
  if (deaf === true) return "easybrandkit could not check that the browser's WebRTC sends no UDP past its proxy, as a datagram it sent to a port of its own on 127.0.0.1 did not come there, as a firewall of this machine that drops UDP to 127.0.0.1 makes it do, so no kit was made: a browser whose WebRTC sends UDP, as a Chrome policy (WebRtcIPHandling) or a program that starts it with switches of its own can make it do, could have a page send UDP to an address easybrandkit does not open without easybrandkit judging that address. Let this machine's programs send UDP to 127.0.0.1.";
  if (deaf) return `easybrandkit could not check that the browser's WebRTC sends no UDP past its proxy, as it could not listen for UDP on 127.0.0.1: ${systemWords(deaf)}, so no kit was made.${moreFiles(deaf) || " Try again."}`;
  if (udp) return `The browser's WebRTC sends UDP past easybrandkit's proxy, as a Chrome policy (WebRtcIPHandling) or a program that starts it with switches of its own makes it do, so no kit was made: a page could have it send UDP to an address easybrandkit does not open without easybrandkit judging that address. ${helps}`;
  // One that gave up on its connection to the proxy, as a browser can on
  // one that gets no answer, before any reached the proxy, could not
  // connect to it either.
  if (errorText === "net::ERR_PROXY_CONNECTION_FAILED" || unanswered || (!proxy.accepted && (errorText === "net::ERR_TIMED_OUT" || errorText === "net::ERR_CONNECTION_TIMED_OUT"))) {
    const why = unanswered ? `its connection to 127.0.0.1:${proxy.port} got no answer in ${Math.round(unanswered / 1_000)} s` : errorText;
    return `The browser could not connect to the proxy its requests go through (${why}), so no kit was made. easybrandkit gives it a proxy of its own at 127.0.0.1:${proxy.port}: let the browser connect to 127.0.0.1, which a firewall of this machine can keep it from, and if a Chrome policy or a program that starts it gives it another proxy, lift that policy or point CHROME_PATH at the browser's own program.`;
  }
  const risk = "so no kit was made: a page could have it reach an address easybrandkit does not open without easybrandkit judging that address.";
  if (n === 1) return `The browser does not send its requests through easybrandkit's proxy, as a Chrome policy (ProxyMode, ProxySettings or ProxyBypassList) or a program that starts it with switches of its own makes it do, ${risk} ${helps}`;
  return `The browser sends its requests for this machine's own addresses past easybrandkit's proxy, as a Chrome policy (ProxyMode, ProxySettings or ProxyBypassList) or a program that starts it with switches of its own makes it do, ${risk} ${helps}`;
}

// The first bytes of a file the browser printed into, as text: "" when it
// cannot be read.
function firstBytes(file, most = 8_192) {
  let fd;
  try {
    fd = fs.openSync(file, "r");
    const bytes = Buffer.alloc(most);
    return bytes.subarray(0, fs.readSync(fd, bytes, 0, most, 0)).toString("utf8");
  } catch {
    return "";
  } finally {
    if (fd !== undefined) fs.closeSync(fd);
  }
}

// A socket's path on Linux holds 108 bytes, the last of them a zero.
const SOCKET_MAX = 107;

// Chrome on Linux makes the folder that holds its socket in the temp folder
// as it starts, and ends at once when the socket's path in it is longer
// than a socket's path can be. The length of that path, for a folder of
// Chrome's kind that came while the browser started, when it is too long;
// 0 when it is not, or when no such folder came.
function socketTooLong(temp, before) {
  if (process.platform !== "linux") return 0;
  const made = [...tempNames(temp)].filter((name) => !before.has(name) && !FETCHING.test(name));
  const longest = Math.max(0, ...made.map((name) => Buffer.byteLength(path.join(temp, name, "SingletonSocket"))));
  return longest > SOCKET_MAX ? longest : 0;
}

// Chrome keeps the socket that makes it one browser per profile in a folder
// of its own in the temp folder, linked from the profile, and removes it
// only when it quits. Killed, it leaves it: removed here, those two names
// only. As it quits, as Ctrl-C makes it do, it removes the profile's links
// first and the folder a moment later, so a browser killed in between
// leaves the folder with nothing that leads to it: the folder named as the
// browser started is used then.
function removeSingleton(profile, known = "") {
  let folder = known;
  try {
    folder = path.dirname(fs.readlinkSync(path.join(profile, "SingletonSocket")));
  } catch {
    // No link any more.
  }
  if (!folder) return;
  try {
    for (const name of ["SingletonSocket", "SingletonCookie"]) fs.rmSync(path.join(folder, name), { force: true });
    fs.rmdirSync(folder);
  } catch {
    // Gone already, as Chrome removed it as it quit.
  }
}

// The folder of a browser's socket, as the profile's link names it while
// the browser runs: "" when there is none, or when it is not a folder of
// Chrome's kind right in the temp folder.
function singletonOf(profile, temp) {
  try {
    const folder = path.dirname(fs.readlinkSync(path.join(profile, "SingletonSocket")));
    return path.isAbsolute(folder) && TEMP_NAME.test(path.basename(folder)) && fs.realpathSync(path.dirname(folder)) === fs.realpathSync(temp) ? folder : "";
  } catch {
    return "";
  }
}

// Every browser still open, killed at once with its helpers and its crash
// handler, and its profile and temp folders removed: for a process that is
// being stopped and has no time to ask them to quit. It never throws.
function killBrowsers() {
  const ending = [...open];
  open.clear();
  for (const entry of ending) {
    if (entry.proxy) entry.proxy.close();
    entry.processes = withCrashHandler(entry, processesOf(entry.child));
    try {
      entry.child.kill("SIGKILL");
    } catch {
      // Gone already.
    }
    killAll(entry.processes);
  }
  // Until they are gone, with any they started, a second at most each.
  for (const entry of ending) entry.processes = endAll(entry.processes, entry.profile);
  for (const { profile, singleton } of ending) removeSingleton(profile, singleton);
  // Once its processes are gone, nothing writes into a profile again. Where
  // they cannot be told, helpers can still write into it for a moment as
  // they end: it is removed until it stays gone, half a second at most.
  for (let round = 0; round < 5; round++) {
    for (const { profile } of ending) {
      try {
        fs.rmSync(profile, { recursive: true, force: true, maxRetries: 2, retryDelay: 20 });
      } catch {
        // Tried again in the next round.
      }
    }
    if (ending.every(({ processes }) => processes.length && allGone(processes))) break;
    pause(100);
    if (!ending.some(({ profile }) => fs.existsSync(profile))) break;
  }
  for (const entry of ending) removeTemps(entry);
}

// An error about a page and not about the run. Its pageFailed holds what the
// page did, in words that can follow its address or "it", for a run that goes
// on without a page it chose to read. Its outOfTime says the page got no more
// of the run's time, where more of it can help: such a run does not go on.
const pageFailed = (message, what, spent = false) => Object.assign(new Error(message), { pageFailed: what, outOfTime: spent });

// A call on a connection that has closed, marked closed: a tab that has
// closed while the browser runs, or a browser that has ended.
const connectionClosed = () => Object.assign(new Error("The browser connection closed."), { closed: true });

// The largest message taken from the browser. The snapshot of a very large
// page can be bigger, and read whole it would take more memory than a run
// has on the hosted worker: Node 22.23's WebSocket, which the kit used
// before the pipe, took none larger either.
const MESSAGE_MOST = 128 * 1024 * 1024;

// The answer to a call that was larger than the kit takes, marked tooLarge.
// The connection goes on: only that call fails.
const tooLargeAnswer = () => Object.assign(new Error("The browser's answer was too large to take."), { tooLarge: true });

// The DevTools protocol over a browser's pipe: each message is JSON ended by
// a zero byte, the kit's written to input and the browser's read from output.
// The browser's own calls go without a session. Each tab the kit uses is a
// session of its own on the pipe (attach), with send, on and closed as a
// connection of its own had. A message over most bytes is not kept: its
// first bytes name the call it answers (an answer starts {"id":<n>,), and
// that call fails as too large; anything else that large is dropped.
function pipeOf(input, output, most = MESSAGE_MOST) {
  const pending = new Map();
  const listeners = new Map();
  const sessions = new Map();
  let nextId = 0;
  let over = false;
  let markOver;
  const closed = new Promise((done) => (markOver = done));
  const settle = (id, err, result) => {
    const waiter = pending.get(id);
    if (!waiter) return;
    pending.delete(id);
    clearTimeout(waiter.timer);
    if (err) waiter.reject(err);
    else waiter.resolve(result);
  };
  // A tab's session that has ended, as when its tab closed: its calls fail as
  // on a closed connection.
  const endSession = (session) => {
    const mark = sessions.get(session);
    if (!mark) return;
    sessions.delete(session);
    for (const [id, waiter] of [...pending]) if (waiter.session === session) settle(id, connectionClosed());
    mark();
  };
  // The pipe closed, as when the browser ends: every call fails at once.
  const end = () => {
    if (over) return;
    over = true;
    for (const id of [...pending.keys()]) settle(id, connectionClosed());
    for (const session of [...sessions.keys()]) endSession(session);
    markOver();
    input.destroy();
    output.destroy();
  };
  const take = (bytes) => {
    let msg;
    try {
      msg = JSON.parse(bytes.toString("utf8"));
    } catch {
      return;
    }
    if (!msg || typeof msg !== "object") return;
    if (typeof msg.method === "string") {
      if (msg.method === "Target.detachedFromTarget" && msg.params) endSession(msg.params.sessionId);
      for (const listener of listeners.get(`${msg.sessionId || ""} ${msg.method}`) || []) listener(msg.params || {});
      return;
    }
    if (msg.error) settle(msg.id, new Error(msg.error.message || "DevTools protocol error"));
    else settle(msg.id, null, msg.result || {});
  };
  // The first bytes of a message, from its parts.
  const startOf = (list) => {
    const head = [];
    let size = 0;
    for (const part of list) {
      head.push(part);
      size += part.length;
      if (size >= 64) break;
    }
    return Buffer.concat(head).subarray(0, 64).toString("latin1");
  };
  let parts = [];
  let size = 0;
  // The start of a message too large to keep, while the rest of it goes by.
  let dropping = null;
  output.on("data", (chunk) => {
    for (let at = 0; at < chunk.length; ) {
      const zero = chunk.indexOf(0, at);
      const piece = chunk.subarray(at, zero === -1 ? chunk.length : zero);
      at = zero === -1 ? chunk.length : zero + 1;
      if (dropping === null && size + piece.length > most) {
        dropping = startOf([...parts, piece]);
        parts = [];
        size = 0;
      }
      if (dropping !== null) {
        if (zero === -1) continue;
        const id = /^\{"id":(\d+)[,}]/.exec(dropping);
        if (id) settle(Number(id[1]), tooLargeAnswer());
        dropping = null;
        continue;
      }
      parts.push(piece);
      size += piece.length;
      if (zero === -1) continue;
      const whole = parts.length === 1 ? parts[0] : Buffer.concat(parts, size);
      parts = [];
      size = 0;
      take(whole);
    }
  });
  output.on("end", end);
  output.on("close", end);
  output.on("error", end);
  input.on("error", end);
  // A call, waited for timeoutMs at most and no longer than the run has left,
  // a second at least.
  const send = (method, params = {}, timeoutMs = 30_000, session = "") => {
    if (over || (session && !sessions.has(session))) return Promise.reject(connectionClosed());
    const id = ++nextId;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(Object.assign(new Error(`${method} timed out`), { timedOut: true }));
      }, Math.max(1_000, Math.min(timeoutMs, timeLeft())));
      pending.set(id, { resolve, reject, timer, session });
      input.write(`${JSON.stringify(session ? { id, method, params, sessionId: session } : { id, method, params })}\0`);
    });
  };
  // The kit's connection to a tab, waited for ms at most.
  const attach = async (targetId, ms) => {
    let session;
    try {
      ({ sessionId: session } = await send("Target.attachToTarget", { targetId, flatten: true }, ms));
    } catch (err) {
      if (err.timedOut) throw noAnswer("The browser did not answer the kit's connection to its tab", ms);
      if (err.closed) throw err;
      throw browserSaid("The browser refused the kit's connection to its tab");
    }
    if (over) throw connectionClosed();
    let mark;
    const tabClosed = new Promise((done) => (mark = done));
    sessions.set(session, mark);
    return {
      // Settles once the tab has closed, or the browser has ended.
      closed: tabClosed,
      send: (method, params = {}, timeoutMs = 30_000) => send(method, params, timeoutMs, session),
      on(method, listener) {
        const key = `${session} ${method}`;
        listeners.set(key, [...(listeners.get(key) || []), listener]);
      },
      // The tab closed, not waited for; the browser goes on.
      close() {
        if (sessions.has(session)) send("Target.closeTarget", { targetId }, 5_000).catch(() => {});
      },
    };
  };
  // What the browser itself tells, past every tab.
  const on = (method, listener) => {
    const key = ` ${method}`;
    listeners.set(key, [...(listeners.get(key) || []), listener]);
  };
  return { send, attach, on, closed, end, ended: () => over };
}

// How long the kit waits for the browser to take its answer to a document
// the browser holds for it.
const HELD_ANSWER = 10_000;

// The longest address kept for what is told of one.
const LONG_ADDRESS = 300;

// The rule for the run's pages held for the whole browser, on its own
// connection, which sees the requests of every tab, frame and window: each
// document the browser loads, the page, each hop of its redirects, a move
// of the page, a frame in it, of another site too, and a window it opens,
// is held before the browser asks for it (Fetch at its Request stage) and
// judged by judge, the run's rule (see address.js guardFor). One the rule
// takes goes on; one it refuses is not asked for. A frame or a window is
// then given up as if the page had stopped it, and stays empty. The tab's
// own page ends on the browser's error page: given up the same way, a move
// the page made before its load event left the tab taking no more input
// (Chrome 155), so the page could not be read anyway. The refusal is kept
// with the tab it came from, in its refused list (see keepRefused): the tab
// whose page it was, by the page's id, marked main, else the tab opened
// last, whose frame or window it was, as the kit reads in one tab at a time
// and the card's tab asks for nothing (see navigate, takeMove and
// refusedNotes). With no rule, no web page is opened. A page's pictures,
// styles, scripts and data are no documents: the kit's proxy judges them,
// as every request of the browser (see proxy.js and proxyNotes).
//
// A document asked for with signed exchanges in its Accept header comes from
// a browser that takes them though its profile asks it not to (see launch),
// as a Chrome policy (SignedHTTPExchangeEnabled) makes it do: it is not
// asked for, and its tab is marked signedExchanges, so that the run ends
// there (see navigate). The first document a browser asks for is the page
// the kit opens, so nothing of the site has been asked for by then.
async function holdDocuments(pipe, tabs, judge, ms) {
  pipe.on("Fetch.requestPaused", async (paused) => {
    const url = String((paused.request && paused.request.url) || "");
    const page = tabs.get(paused.frameId);
    const tab = page || [...tabs.values()].pop();
    const fail = () => pipe.send("Fetch.failRequest", { requestId: paused.requestId, errorReason: page ? "BlockedByClient" : "Aborted" }, HELD_ANSWER).catch(() => {});
    let why = "";
    if (/^https?:/i.test(url)) {
      if (asksSignedExchanges(paused.request)) {
        if (tab) tab.signedExchanges = true;
        return void fail();
      }
      try {
        why = judge ? await judge(url) : "is not opened by a browser the kit gave no rule for the addresses it opens";
      } catch {
        why = "could not be judged";
      }
    }
    if (!why) return void pipe.send("Fetch.continueRequest", { requestId: paused.requestId }, HELD_ANSWER).catch(() => {});
    if (tab) keepRefused(tab, { page: tab.page || "", url: url.slice(0, LONG_ADDRESS), why, main: Boolean(page) });
    fail();
  });
  await pipe.send("Fetch.enable", { patterns: [{ urlPattern: "*", resourceType: "Document", requestStage: "Request" }] }, ms);
}

// Whether a request the browser holds asks for signed exchanges, by its
// Accept header, as Chrome's documents do while it takes them.
const asksSignedExchanges = (request) => Object.entries((request && request.headers) || {}).some(([name, value]) => name.toLowerCase() === "accept" && /application\/signed-exchange/i.test(String(value)));

// The end of a run whose browser takes signed exchanges (see holdDocuments).
const SIGNED_EXCHANGES = "The browser takes signed exchanges though its profile asks it not to, as a Chrome policy (SignedHTTPExchangeEnabled) or a program that starts it with a profile of its own makes it do, so no kit was made: a page could have it show what a signed exchange holds under another address than the one it came from, past easybrandkit's rule for the pages it opens, which tells where a page led. Lift that policy, or point CHROME_PATH at the browser's own program or at another browser.";

// The browser preloads nothing, as its profile asks (see launch): asked in
// each tab the kit reads pages in, before it opens one there.
// Preload.enable has it tell the state of its preloading
// (Preload.preloadEnabledStateUpdated), whose disabledByPreference is the
// profile's setting as the browser holds it: a Chrome policy
// (NetworkPredictionOptions) holds it in the profile's place, and a program
// that starts the browser with a profile of its own gives it that one's. A
// browser that says it preloads, or cannot say, as one that refuses to be
// asked or tells no state, is not used: a page's speculation rules would
// have it prefetch or prerender an address and serve the page's move there
// from that copy, which is no document it holds for the rule (see
// holdDocuments).
async function noPreloading(cdp) {
  let state = null;
  cdp.on("Preload.preloadEnabledStateUpdated", (said) => (state = state || said));
  const wait = browserWait();
  const notUsed = (what, helps = "Point CHROME_PATH at another browser, such as Google Chrome.") => new Error(`The browser ${what}, so no kit was made: a page could have it fetch a page ahead of the page's move there, past easybrandkit's rule for the pages it opens, which tells where a page led. ${helps}`);
  try {
    await cdp.send("Preload.enable", {}, wait);
  } catch (err) {
    if (err.timedOut) throw noAnswer("The browser did not say whether it preloads pages", wait);
    if (err.closed) throw err;
    throw notUsed(`cannot say whether it preloads pages (${String(err.message || err).replace(/[\u0000-\u001f\u007f-\u009f]+/g, " ").slice(0, 200)})`);
  }
  // Told before the answer; a moment more for a browser that tells it
  // after.
  for (let waited = 0; !state && waited < 1_000; waited += 50) await sleep(50);
  await cdp.send("Preload.disable", {}, 5_000).catch(() => {});
  if (!state) throw notUsed("does not say whether it preloads pages");
  if (state.disabledByPreference !== true) {
    throw notUsed("preloads pages though its profile asks it not to, as a Chrome policy (NetworkPredictionOptions) or a program that starts it with a profile of its own makes it do", "Lift that policy, or point CHROME_PATH at the browser's own program or at another browser.");
  }
}

// A document the run's rule refused, kept in the tab's refused list (see
// holdDocuments): a move of the tab's own page always, to be told as where
// the page led, the list holding 100 at most; a frame's or a window's once
// for each address, the first 50 addresses, past which the tab's
// refusedMore says that there were more.
function keepRefused(tab, one) {
  const list = tab.refused;
  if (one.main) {
    if (list.length < 100) list.push(one);
    return;
  }
  const others = list.filter((kept) => !kept.main);
  if (others.some((kept) => kept.url === one.url)) return;
  if (others.length < 50) list.push(one);
  else if (!list.some((kept) => kept.url === one.url)) tab.refusedMore = true;
}

// The move to an address the run's rule refused that the tab's page made
// since navigate opened it, taken out of the tab's refused list to be told
// as where the page led (see holdDocuments), or null.
function takeMove(cdp) {
  const refused = cdp.refused || [];
  const at = refused.findIndex((one, i) => one.main && i >= (cdp.movedFrom || 0));
  return at === -1 ? null : refused.splice(at, 1)[0];
}

// The notes on the addresses the run's rule did not let the pages open
// (tab.refused, see holdDocuments): a frame, a window, or a page's own move
// that was not told as where the page led, each named once, the first three
// of them, and how many more there were: at least that many when the list
// did not keep them all (tab.refusedMore, see keepRefused).
function refusedNotes(refused = [], past = false) {
  const byAddress = new Map();
  for (const one of refused) if (!byAddress.has(one.url)) byAddress.set(one.url, one);
  const list = [...byAddress.values()];
  const notes = list.slice(0, 3).map(({ page, url, why }) => `${page || "The page"} tried to open ${url}, which ${why}: it was not opened.`);
  const more = Math.max(0, list.length - 3) + (past ? 1 : 0);
  if (more > 0) notes.push(`${past ? "At least " : ""}${more} more ${more === 1 ? "address the pages tried to open was" : "addresses the pages tried to open were"} not opened either.`);
  return notes;
}

// What OK gives a dialog a page opens, given in the page's own world before
// its scripts run (see openPage): alert() does nothing, confirm() gives true
// and prompt() the text it offers, "" when it offers none. Each wraps the
// browser's own function: it keeps that function's name, its length and its
// want of a prototype, and its code reads as native code, though without the
// function's name, where a function of the kit's would show its source.
const ANSWERED_DIALOGS = `(() => {
  const answer = (name, given) => {
    window[name] = new Proxy(window[name], { apply: (own, self, args) => given(args) });
  };
  answer("alert", () => undefined);
  answer("confirm", () => true);
  answer("prompt", ([, text]) => (text === undefined ? "" : String(text)));
})();`;

// A new tab, set to a desktop screen of the given size. Headless Chrome says
// "HeadlessChrome" in its user agent, and some sites answer that with a
// stripped page; the tab says "Chrome", as the same browser with a window
// would. The tab and the kit's connection to it have what the run has left.
async function openPage(chrome, { width, height }) {
  const targetId = await chrome.newTab(browserWait());
  const cdp = await chrome.attach(targetId, browserWait());
  // The documents the run's rule did not let this tab's pages open (see
  // holdDocuments), with the tab's page, by its id, the id of its page.
  cdp.refused = [];
  // The proxy the browser's requests go through, which is told the page
  // the tab reads (see navigate).
  cdp.proxy = chrome.proxy || null;
  if (chrome.tabs) chrome.tabs.set(targetId, cdp);
  await noPreloading(cdp);
  // A dialog a page opens with alert(), confirm() or prompt(), as it loads
  // or on the kit's first turn of the wheel, holds the tab until someone
  // answers it, and nothing else does. The page's own, and those of its
  // frames of the same site, are given what OK gives in the page's own
  // world (ANSWERED_DIALOGS), so they never reach the browser: there, one
  // that came as a frame of another site asked its own was answered with
  // Cancel and the other was held, the page's own holding its tab until
  // the run failed. A frame of another site runs apart, and the browser
  // tells its dialogs: each is answered with OK, a prompt() with the text
  // it offers. Two such frames that ask at once can still have one held and
  // the other given Cancel, or have one given the answer meant for the
  // other's dialog, as "" for a prompt() where the other's was an alert().
  // A frame held so holds itself alone, and the page's load is waited for
  // no longer than its time.
  cdp.on("Page.javascriptDialogOpening", ({ defaultPrompt = "" }) => cdp.send("Page.handleJavaScriptDialog", { accept: true, promptText: defaultPrompt }).catch(() => {}));
  await cdp.send("Page.enable");
  await cdp.send("Page.addScriptToEvaluateOnNewDocument", { source: ANSWERED_DIALOGS });
  await guard(cdp);
  cdp.answer = await watchAnswer(cdp);
  await cdp.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
  const { userAgent = "" } = await cdp.send("Browser.getVersion").catch(() => ({}));
  if (userAgent.includes("HeadlessChrome")) {
    await cdp.send("Emulation.setUserAgentOverride", { userAgent: userAgent.replace("HeadlessChrome", "Chrome") });
  }
  return cdp;
}

// The kinds of address a page may go to: web pages, and the browser's own
// documents, which no program of the machine opens.
const WEB_SCHEME = /^(https?|data|blob|about|javascript|chrome-error):$/i;
const webAddress = (raw) => {
  try {
    return WEB_SCHEME.test(new URL(raw).protocol);
  } catch {
    return true;
  }
};

// The world each document of a tab's pages gets before its own scripts run,
// and the guard it runs there: a page's move to an address that is not a
// web address, by its script, a refresh, a form or a link, in the page or a
// frame of the same site, is cancelled before the browser acts on it, on
// every system, and the address is kept for the kit's notes. The page's own
// scripts cannot reach this world. A frame's first address, a redirect, a
// frame of another site, which runs apart, and a frame still on its first
// about:blank, where the browser tells no move, reach the browser: on Linux
// the cut session bus and the stand-ins take those (see launch).
const GUARD_WORLD = "easybrandkit-guard";
const GUARD = `(() => {
  if (typeof navigation === "undefined") return;
  const tried = (globalThis.easybrandkitTried = []);
  const web = ${WEB_SCHEME};
  navigation.addEventListener("navigate", (event) => {
    let scheme = "";
    try {
      scheme = new URL(event.destination.url).protocol;
    } catch {}
    if (web.test(scheme) || !event.cancelable) return;
    event.preventDefault();
    if (tried.length < 20) tried.push(String(event.destination.url).slice(0, 300));
  });
})();`;

// The guard in each new document of the tab, and what the tab says of the
// rest: an address that is not a web address that the browser began to go
// to in the page or a frame, one a document's redirect led to, in a frame of
// another site too, and a window a page asked for with one, which the
// browser does not open without a click. Each is kept in cdp.tried with the
// page the kit had opened (cdp.page), the address and how it came.
async function guard(cdp) {
  cdp.tried = [];
  const keep = (url, how) => {
    if (!webAddress(url) && cdp.tried.length < 50) cdp.tried.push({ page: cdp.page || "", url: String(url).slice(0, 300), how });
  };
  cdp.on("Page.frameStartedNavigating", ({ url }) => keep(url, "started"));
  cdp.on("Page.windowOpen", ({ url }) => keep(url, "window"));
  // A redirect's new address comes as the next request of the same document.
  cdp.on("Network.requestWillBeSent", ({ type, request }) => {
    if (type === "Document" && request) keep(request.url, "started");
  });
  await cdp.send("Page.addScriptToEvaluateOnNewDocument", { source: GUARD, worldName: GUARD_WORLD });
}

// The addresses the guard cancelled in the tab's page so far, in its frames
// too, taken out of their worlds into cdp.tried. Called before the kit
// leaves a page, and once it has read the last one. A frame that cannot be
// asked, as one of another site that runs apart, keeps its own. It takes a
// few seconds at most, and stops at a call the tab does not answer: a page
// whose own script keeps its thread busy answers none of them.
async function triedSoFar(cdp) {
  if (!cdp.tried) return [];
  const until = Date.now() + Math.min(3_000, Math.max(1_000, timeLeft()));
  const waitLeft = () => Math.max(1, until - Date.now());
  const ask = (method, params) => cdp.send(method, params, waitLeft());
  try {
    const { frameTree } = await ask("Page.getFrameTree", {});
    const frames = [];
    for (let next = [frameTree]; next.length && frames.length < 20; ) {
      const node = next.shift();
      frames.push(node.frame.id);
      next.push(...(node.childFrames || []));
    }
    for (const frameId of frames) {
      if (Date.now() >= until) break;
      let cancelled = [];
      try {
        const { executionContextId } = await ask("Page.createIsolatedWorld", { frameId, worldName: GUARD_WORLD });
        const { result } = await ask("Runtime.evaluate", { expression: "(globalThis.easybrandkitTried || []).splice(0, 20)", contextId: executionContextId, returnByValue: true });
        if (Array.isArray(result && result.value)) cancelled = result.value;
      } catch (err) {
        if (err.timedOut || err.closed) break;
        // A frame between two documents, or gone.
      }
      for (const url of cancelled) if (typeof url === "string" && cdp.tried.length < 50) cdp.tried.push({ page: cdp.page || "", url: url.slice(0, 300), how: "cancelled" });
    }
  } catch {
    // A tab that does not answer, or has closed.
  }
  return cdp.tried;
}

// The notes on the addresses that are not web addresses the pages tried to
// open (cdp.tried), the first three of them. The page's guard cancels a
// page's own move and the browser opens no window without a click, on every
// system; where the browser gets stand-ins (standIns), its cut session bus
// and its stand-ins also take what it went on to, unless it runs in a
// sandbox of its own (sandboxed), as one installed as a snap or a Flatpak,
// where it can find others. An address tried in more than one way is told
// by one of them: where what reached the browser may have reached the
// system too, by the way that reached it.
function triedNotes(tried = [], { sandboxed = false, standIns = STAND_INS } = {}) {
  const stopped = standIns && !sandboxed;
  const told = (one) => (stopped ? one.how !== "started" : one.how === "started");
  const byAddress = new Map();
  for (const one of tried) {
    const known = byAddress.get(one.url);
    if (!known || (told(one) && !told(known))) byAddress.set(one.url, one);
  }
  const list = [...byAddress.values()];
  const notes = list.slice(0, 3).map(({ page, url, how }) => {
    const who = page || "The page";
    if (how !== "started" || stopped) return `${who} tried to open ${url}, which is not a web address: it was not opened.`;
    return `${who} tried to open ${url}, which is not a web address, in a way easybrandkit ${standIns ? "may not stop in a browser installed as a snap or a Flatpak" : "stops only on Linux"}.`;
  });
  const more = list.length - 3;
  if (more > 0) notes.push(`${more} more ${more === 1 ? "address that is not a web address was" : "addresses that are not web addresses were"} tried as well.`);
  return notes;
}

// What the tab's own page came from, kept up to date as the page moves on:
// the status the server last answered its document with and that address,
// after any redirect, the address of a page the browser could not open and
// shows its own error page for, and whether the page has moved on to
// about:blank, as scripts that guard against DevTools make it do. And hop,
// the address a redirect led the document to, the last one, which the
// browser tells as the next request of the same document, as the
// redirect's answer gets no event of its own. Frames inside the page do not
// count. The bodies of the responses are not wanted, so little of them is
// kept. Where the browser got a document says nothing of the page: every
// answer comes through the kit's proxy, which connected only to an address
// the run's rule took (see proxy.js).
async function watchAnswer(cdp) {
  const { frameTree } = await cdp.send("Page.getFrameTree");
  const main = frameTree.frame.id;
  const answer = { status: 0, url: "", unreachable: "", blank: false, leftTo: "", hop: "" };
  // The main frame's document request.
  let request = "";
  cdp.on("Network.requestWillBeSent", ({ requestId, type, frameId, request: asked, redirectResponse }) => {
    if (type !== "Document" || frameId !== main) return;
    if (requestId === request) {
      if (redirectResponse && asked) answer.hop = String(asked.url || "").slice(0, LONG_ADDRESS);
      return;
    }
    request = requestId;
  });
  cdp.on("Network.responseReceivedExtraInfo", ({ requestId, statusCode, headers }) => {
    if (requestId !== request) return;
    // A redirect to an address that is not a web address, which the browser
    // hands to the system: the navigation ends there, with no answer of its
    // own.
    if (statusCode >= 300 && statusCode < 400 && headers) {
      const location = Object.entries(headers).find(([key]) => key.toLowerCase() === "location");
      if (location && /^[a-z][a-z0-9+.-]*:/i.test(String(location[1])) && !webAddress(String(location[1]).trim())) answer.leftTo = String(location[1]).trim().slice(0, 300);
    }
  });
  cdp.on("Network.responseReceived", ({ type, frameId, response }) => {
    if (type !== "Document" || frameId !== main || !response) return;
    Object.assign(answer, { status: response.status, url: response.url });
  });
  cdp.on("Page.frameNavigated", ({ frame }) => {
    if (frame.parentId) return;
    answer.unreachable = /^chrome-error:/.test(frame.url) ? frame.unreachableUrl || frame.url : "";
    answer.blank = frame.url === "about:blank";
  });
  await cdp.send("Network.enable", { maxTotalBufferSize: 1_000_000, maxResourceBufferSize: 100_000 });
  return answer;
}

// What Chrome says of a connection that cannot be made, by the system's
// word for it, as it says it of one of its own: the kit's proxy makes the
// browser's connections (see proxy.js), and the browser tells one the
// proxy could not make only as an empty answer or a tunnel that failed.
const NET_WORDS = {
  ECONNREFUSED: "net::ERR_CONNECTION_REFUSED",
  ECONNRESET: "net::ERR_CONNECTION_RESET",
  ECONNABORTED: "net::ERR_CONNECTION_ABORTED",
  ETIMEDOUT: "net::ERR_CONNECTION_TIMED_OUT",
  EHOSTUNREACH: "net::ERR_ADDRESS_UNREACHABLE",
  ENETUNREACH: "net::ERR_ADDRESS_UNREACHABLE",
  EHOSTDOWN: "net::ERR_ADDRESS_UNREACHABLE",
  EADDRNOTAVAIL: "net::ERR_ADDRESS_INVALID",
  ENOTFOUND: "net::ERR_NAME_NOT_RESOLVED",
};

// What the browser says of a page the kit's proxy could not reach.
const PROXY_SAID = new Set(["net::ERR_EMPTY_RESPONSE", "net::ERR_TUNNEL_CONNECTION_FAILED"]);

// Chrome's word for the connection to at that the kit's proxy could not
// make since it had failed made ones (cdp.proxy), "" when it made it. An
// answer that is not HTTP as the proxy reads one (an error of Node's
// parser, HPE_...), which the browser was told nothing of, is told as
// Chrome tells such an answer of its own: the server answered.
function proxyFailure(cdp, at, made) {
  if (!cdp.proxy) return "";
  let key;
  try {
    key = keyOf(new URL(at));
  } catch {
    return "";
  }
  const one = cdp.proxy.failed.filter((failed) => failed.n > made && failed.key === key).pop();
  if (!one) return "";
  return NET_WORDS[one.code] || (/^HPE_/.test(one.code) ? "net::ERR_INVALID_HTTP_RESPONSE" : "net::ERR_CONNECTION_FAILED");
}

// The notes on the requests the kit's proxy refused while the kit read its
// pages (proxy.refused, see proxy.js): each address once, the first three of
// them, and how many more there were, at least that many when the proxy did
// not keep them all (past). One refused because its name was not found is
// left out: a browser of its own would not have reached it either, and the
// browser's own requests, as for its updates, ask for names a machine with
// no DNS cannot look up. So are those made before the kit had opened a page,
// which are the browser's own.
function proxyNotes(refused = [], past = false) {
  const list = refused.filter(({ why, page }) => page && why !== UNRESOLVED);
  const notes = list.slice(0, 3).map(({ page, what, why }) => `While easybrandkit read ${page}, the browser asked for ${what}, which ${why}: it was not reached.`);
  const more = Math.max(0, list.length - 3) + (past ? 1 : 0);
  if (more > 0) notes.push(`${past ? "At least " : ""}${more} more ${more === 1 ? "address the browser asked for was" : "addresses the browser asked for were"} not reached either.`);
  return notes;
}

// What the browser says of a page to which it made no connection, or whose
// server closed the connection without an answer.
const NO_CONNECTION = new Set(["net::ERR_CONNECTION_REFUSED", "net::ERR_CONNECTION_RESET", "net::ERR_CONNECTION_CLOSED", "net::ERR_CONNECTION_ABORTED", "net::ERR_CONNECTION_FAILED", "net::ERR_CONNECTION_TIMED_OUT", "net::ERR_TIMED_OUT", "net::ERR_EMPTY_RESPONSE"]);

// Opens the address and waits for its load event, at most 30 s: a page that
// never finishes loading (a stuck tracking script) is read as it stands.
// Returns the address the tab ended on, after any redirects; cdp.answer says
// what the server answered. An error status with no page of its own makes
// Chrome give a net:: code, which says less than the status, so that is left
// to cdp.answer too. Only a web page is opened: a link a site gives can name a
// file on this machine (file://localhost/...), which Chrome would show. A
// page that gave no answer in its time, while the run has time left, or to
// which the browser made no connection, fails with silent, what it did in
// words that can follow its address (see kit.js readPage). One that
// answered with a redirect did answer: where that led and failed is told by
// its address (cdp.answer.hop), with no silent.
async function navigate(cdp, url) {
  let web = false;
  try {
    web = /^https?:$/.test(new URL(url).protocol);
  } catch {
    // Not an address at all.
  }
  if (!web) throw pageFailed(`${url} is not a web address, so no kit was made.`, "is not a web address");
  // What the guard cancelled in the page the tab leaves now.
  if (cdp.page) await triedSoFar(cdp);
  cdp.page = url;
  // The page the kit reads, for what the proxy refuses while it does, and
  // how many connections the proxy had failed to make.
  const made = cdp.proxy ? cdp.proxy.failedCount : 0;
  if (cdp.proxy) cdp.proxy.reading = url;
  const loaded = new Promise((resolve) => cdp.on("Page.loadEventFired", resolve));
  Object.assign(cdp.answer, { status: 0, url: "", unreachable: "", blank: false, space: "", ip: "", leftTo: "", hop: "" });
  // The documents the run's rule refuses from here on (see holdDocuments):
  // in the tab's page, a hop of this navigation, else a move of the page it
  // opened (see takeMove).
  const refused = cdp.refused || [];
  const since = refused.length;
  cdp.movedFrom = since;
  // A site gets 30 s to answer, or what the run has left: one the kit chose
  // to read that never answers leaves the run time to go on without it.
  const limit = Math.max(1_000, Math.min(30_000, timeLeft()));
  let errorText;
  try {
    ({ errorText } = await cdp.send("Page.navigate", { url }, limit));
  } catch (err) {
    if (!err.timedOut) throw err;
    // Where a redirect led, which did not answer: the address asked for did.
    const led = cdp.answer.hop ? `led to ${cdp.answer.hop}, which ` : "";
    if (outOfTime()) throw pageFailed(`${url} ${led}did not answer before the run's time ran out, so no kit was made. Try again, or give it more time with --timeout.`, `${led}did not answer`, true);
    const said = `did not answer in ${Math.round(limit / 1_000)} s`;
    const failed = pageFailed(`${url} ${led}${said}, so no kit was made. The site may be down or slow: try again later.`, `${led}did not answer`);
    throw led ? failed : Object.assign(failed, { silent: said });
  }
  // A browser that takes signed exchanges, told by the page's own document,
  // which it was not let ask for (see holdDocuments).
  if (cdp.signedExchanges) throw new Error(SIGNED_EXCHANGES);
  if (errorText) {
    // A connection the kit's proxy could not make, to the address or to a
    // hop of its redirects, told as Chrome tells one of its own.
    if (PROXY_SAID.has(errorText)) errorText = proxyFailure(cdp, cdp.answer.hop || url, made) || errorText;
    // The address, or a hop of its redirects, that the run's rule refused,
    // which the browser then did not ask for: told by the address and why,
    // where the browser says only that the navigation was aborted.
    const barred = refused.slice(since).find((one) => one.main);
    if (barred) {
      refused.splice(refused.indexOf(barred), 1);
      if (barred.url === url.split("#")[0].slice(0, LONG_ADDRESS)) throw pageFailed(`${url} ${barred.why}, so no kit was made.`, barred.why);
      throw pageFailed(`${url} led to ${barred.url}, which ${barred.why}, so no kit was made.`, `led to ${barred.url}, which ${barred.why}`);
    }
    if (cdp.answer.status >= 400) return url;
    // A redirect to an address that is not a web address ends the
    // navigation as aborted, and what the redirect said can come a moment
    // after the browser's answer.
    for (let waited = 0; errorText === "net::ERR_ABORTED" && !cdp.answer.leftTo && waited < 1_000; waited += 50) await sleep(50);
    if (cdp.answer.leftTo) throw pageFailed(`${url} led to ${cdp.answer.leftTo}, which is not a web address, so no kit was made.`, `led to ${cdp.answer.leftTo}, which is not a web address`);
    // A redirect's address that could not be opened, told by that address:
    // the address asked for answered.
    if (cdp.answer.hop) throw pageFailed(`${url} led to ${cdp.answer.hop}, which could not be opened (${errorText}), so no kit was made.`, `led to ${cdp.answer.hop}, which could not be opened (${errorText})`);
    const failed = pageFailed(`Could not open ${url}: ${errorText}`, `could not be opened (${errorText})`);
    throw NO_CONNECTION.has(errorText) ? Object.assign(failed, { silent: failed.pageFailed }) : failed;
  }
  // The timer goes once the page has loaded, so it does not keep the
  // process up after the kit is done.
  let timer;
  const late = new Promise((resolve) => (timer = setTimeout(resolve, Math.max(1_000, Math.min(30_000, timeLeft() - 60_000)))));
  // A browser that ends while the page loads sends no load event: the calls
  // that follow find the connection closed and say so at once.
  await Promise.race([loaded, late, cdp.closed]);
  clearTimeout(timer);
  try {
    const { currentIndex, entries } = await cdp.send("Page.getNavigationHistory");
    return (entries[currentIndex] || {}).url || url;
  } catch {
    return url;
  }
}

// A JavaScript world of the kit's own in the tab's main frame. It sees the
// page's document but none of what the page's scripts have done to their own
// world, so what runs in it has the browser's own URL, String.prototype.replace
// and XMLSerializer. A navigation destroys it with its document. Each process
// of the browser numbers its worlds afresh, so the number of a world that has
// gone can come to name another one, the page's own among them: it is forgotten
// the moment the main frame has moved on.
async function ownWorld(cdp) {
  if (cdp.world) return cdp.world;
  if (!cdp.worldWatched) {
    cdp.worldWatched = true;
    cdp.on("Page.frameNavigated", ({ frame }) => {
      if (!frame.parentId) cdp.world = 0;
    });
  }
  const { frameTree } = await cdp.send("Page.getFrameTree");
  const { executionContextId } = await cdp.send("Page.createIsolatedWorld", { frameId: frameTree.frame.id, worldName: "easybrandkit" });
  cdp.world = executionContextId;
  return cdp.world;
}

// What Chrome says when the world a call names has gone with its document,
// which the call can learn before the tab's event about the move arrives.
const WORLD_GONE = /Cannot find context|does not belong to the document|navigated or closed/;

// Calls use with the number of the kit's own world, in a new world when a
// navigation has destroyed the last one. What the page's scripts can change
// is never run instead: a world that cannot be made fails the call.
async function inOwnWorld(cdp, use) {
  for (let tries = 1; ; tries++) {
    try {
      return await use(await ownWorld(cdp));
    } catch (err) {
      if (tries === 3 || !WORLD_GONE.test(err.message)) throw err;
      cdp.world = 0;
    }
  }
}

module.exports = { findChrome, launch, killBrowsers, removeTemps, pipeOf, browserWait, openPage, navigate, triedSoFar, triedNotes, refusedNotes, proxyNotes, takeMove, holdDocuments, inOwnWorld, pageFailed, noKit, busPath, HANDLERS, STAND_INS };
