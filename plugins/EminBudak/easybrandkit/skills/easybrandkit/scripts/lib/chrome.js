"use strict";

// The browser: a Chrome, Chromium, Edge or Brave already on this machine,
// started headless with a throwaway profile and driven over the DevTools
// protocol through a pipe of its own. It opens no port, so no other program
// on the machine, another user's run among them, can reach it. Nothing is
// downloaded.

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");
const { timeLeft, outOfTime, sleep, LONGEST_TIMER } = require("./time");
const { browserPlace, wrongWith, couldNotStart, endedEarly, closedEarly, systemWords, ownSandbox } = require("./program");

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
async function launch({ width, height }) {
  // A browser that cannot be started is told before anything is made.
  const place = browserPlace();
  const temp = os.tmpdir();
  // The folders of PATH are parted by its delimiter, so a folder of stand-ins
  // in a temp folder whose path has one in it could not come first on the
  // browser's PATH (see below), and the browser would find the real programs.
  if (STAND_INS && temp.includes(path.delimiter)) {
    throw new Error(`${place.name} was not started: the path of the temp folder, ${temp}, has a ${path.delimiter} in it, which parts the folders of PATH, so the stand-ins that keep a site from starting a program of this machine could not come first on the browser's PATH. Set TMPDIR to a folder whose path has none.`);
  }
  const before = tempNames(temp);
  const profile = fs.mkdtempSync(path.join(temp, "easybrandkit-chrome-"));
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
    for (const file of [path.join(profile, "Default", "Preferences"), path.join(profile, "easybrandkit-output"), ...HANDLERS.map((name) => path.join(stands, name))]) {
      try {
        fs.unlinkSync(file);
      } catch {
        // Not made.
      }
    }
    for (const dir of [path.join(profile, "Default"), stands, profile]) {
      try {
        fs.rmdirSync(dir);
      } catch {
        // Not made, or left for the system's temp clean-up.
      }
    }
  };
  // A download that starts while the browser takes no refusal (see below)
  // goes into the throwaway profile and is removed with it, not into the
  // Downloads folder of the user the browser runs as.
  const preferences = path.join(profile, "Default", "Preferences");
  try {
    fs.mkdirSync(path.join(profile, "Default"));
    fs.writeFileSync(preferences, JSON.stringify({ download: { default_directory: path.join(profile, "Downloads"), prompt_for_download: false } }));
  } catch (err) {
    // For anything but no room, the refusal still holds.
    if (NO_ROOM.has(err.code)) throw room(err, preferences);
  }
  // Chrome on Linux has its crash handler write the reports of its processes
  // into the user's own browser's folder (~/.config/google-chrome/Crash
  // Reports), where nothing removes them; Ctrl-\ asks for one from each of
  // its helpers. BREAKPAD_DUMP_LOCATION puts them in the throwaway profile.
  const env = { ...process.env, BREAKPAD_DUMP_LOCATION: path.join(profile, "Crash Reports") };
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
      throw new Error(`${place.name} was not started: easybrandkit could not make the stand-ins it starts the browser with in ${temp}, which keep a site from starting a program of this machine: ${systemWords(err)}.`);
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
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-sync",
        "--use-mock-keychain",
        "--password-store=basic",
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
  const entry = { child, profile, temp, before };
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
  // hidden, which it can answer by moving on.
  const newTab = async (ms, { background = false } = {}) => {
    try {
      const { targetId } = await pipe.send("Target.createTarget", { url: "about:blank", ...(background ? { background: true } : {}) }, ms);
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
    // sandboxed: a browser installed as a snap or a Flatpak, in whose
    // sandbox the stand-ins and the bus may not be the ones it finds.
    return { close, alive, newTab, closeTab, attach: (targetId, ms) => pipe.attach(targetId, ms), sandboxed: ownSandbox(place.file) };
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
  return { send, attach, closed, end, ended: () => over };
}

// A new tab, set to a desktop screen of the given size. Headless Chrome says
// "HeadlessChrome" in its user agent, and some sites answer that with a
// stripped page; the tab says "Chrome", as the same browser with a window
// would. The tab and the kit's connection to it have what the run has left.
async function openPage(chrome, { width, height }) {
  const cdp = await chrome.attach(await chrome.newTab(browserWait()), browserWait());
  await cdp.send("Page.enable");
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
// about:blank, as scripts that guard against DevTools make it do. Also where
// the browser got the document: the address it connected to (ip) and the IP
// address space Chrome gave that answer (space), which is Unknown when it
// went through a proxy, whose address ip is then. Frames inside the page do
// not count. The bodies of the responses are not wanted, so little of them
// is kept.
async function watchAnswer(cdp) {
  const { frameTree } = await cdp.send("Page.getFrameTree");
  const main = frameTree.frame.id;
  const answer = { status: 0, url: "", unreachable: "", blank: false, space: "", ip: "", leftTo: "" };
  // The main frame's document request, and the space of each answer to it,
  // its redirects' first: each comes apart from the answer it belongs to,
  // before it or after it.
  let request = "";
  let spaces = [];
  let answered = "";
  cdp.on("Network.requestWillBeSent", ({ requestId, type, frameId }) => {
    if (type !== "Document" || frameId !== main || requestId === request) return;
    request = requestId;
    spaces = [];
  });
  cdp.on("Network.responseReceivedExtraInfo", ({ requestId, statusCode, headers, resourceIPAddressSpace }) => {
    if (requestId !== request) return;
    spaces.push({ status: statusCode, space: resourceIPAddressSpace || "" });
    // A redirect to an address that is not a web address, which the browser
    // hands to the system: the navigation ends there, with no answer of its
    // own.
    if (statusCode >= 300 && statusCode < 400 && headers) {
      const location = Object.entries(headers).find(([key]) => key.toLowerCase() === "location");
      if (location && /^[a-z][a-z0-9+.-]*:/i.test(String(location[1])) && !webAddress(String(location[1]).trim())) answer.leftTo = String(location[1]).trim().slice(0, 300);
    }
    if (requestId === answered && statusCode === answer.status) answer.space = resourceIPAddressSpace || "";
  });
  cdp.on("Network.responseReceived", ({ requestId, type, frameId, response }) => {
    if (type !== "Document" || frameId !== main || !response) return;
    const known = requestId === request ? spaces.filter(({ status }) => status === response.status).pop() : null;
    answered = requestId;
    Object.assign(answer, { status: response.status, url: response.url, ip: String(response.remoteIPAddress || "").replace(/^\[|\]$/g, ""), space: known ? known.space : "" });
  });
  cdp.on("Page.frameNavigated", ({ frame }) => {
    if (frame.parentId) return;
    answer.unreachable = /^chrome-error:/.test(frame.url) ? frame.unreachableUrl || frame.url : "";
    answer.blank = frame.url === "about:blank";
  });
  await cdp.send("Network.enable", { maxTotalBufferSize: 1_000_000, maxResourceBufferSize: 100_000 });
  return answer;
}

// What the browser said of where it got the tab's document (cdp.answer), for
// an address of that document: nothing for one of another origin, whose
// document has not come yet or has gone.
function seenOf(cdp, at) {
  try {
    return new URL(at).origin === new URL(cdp.answer.url).origin ? { space: cdp.answer.space || "", ip: cdp.answer.ip || "" } : {};
  } catch {
    return {};
  }
}

// Opens the address and waits for its load event, at most 30 s: a page that
// never finishes loading (a stuck tracking script) is read as it stands.
// Returns the address the tab ended on, after any redirects; cdp.answer says
// what the server answered. An error status with no page of its own makes
// Chrome give a net:: code, which says less than the status, so that is left
// to cdp.answer too. Only a web page is opened: a link a site gives can name a
// file on this machine (file://localhost/...), which Chrome would show.
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
  const loaded = new Promise((resolve) => cdp.on("Page.loadEventFired", resolve));
  Object.assign(cdp.answer, { status: 0, url: "", unreachable: "", blank: false, space: "", ip: "", leftTo: "" });
  // A site gets 30 s to answer, or what the run has left: one the kit chose
  // to read that never answers leaves the run time to go on without it.
  const limit = Math.max(1_000, Math.min(30_000, timeLeft()));
  let errorText;
  try {
    ({ errorText } = await cdp.send("Page.navigate", { url }, limit));
  } catch (err) {
    if (!err.timedOut) throw err;
    if (outOfTime()) throw pageFailed(`${url} did not answer before the run's time ran out, so no kit was made. Try again, or give it more time with --timeout.`, "did not answer", true);
    throw pageFailed(`${url} did not answer in ${Math.round(limit / 1_000)} s, so no kit was made. The site may be down or slow: try again later.`, "did not answer");
  }
  if (errorText) {
    if (cdp.answer.status >= 400) return url;
    // A redirect to an address that is not a web address ends the
    // navigation as aborted, and what the redirect said can come a moment
    // after the browser's answer.
    for (let waited = 0; errorText === "net::ERR_ABORTED" && !cdp.answer.leftTo && waited < 1_000; waited += 50) await sleep(50);
    if (cdp.answer.leftTo) throw pageFailed(`${url} led to ${cdp.answer.leftTo}, which is not a web address, so no kit was made.`, `led to ${cdp.answer.leftTo}, which is not a web address`);
    throw pageFailed(`Could not open ${url}: ${errorText}`, `could not be opened (${errorText})`);
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

module.exports = { findChrome, launch, killBrowsers, removeTemps, pipeOf, browserWait, openPage, navigate, triedSoFar, triedNotes, seenOf, inOwnWorld, pageFailed, noKit, busPath, HANDLERS, STAND_INS };
