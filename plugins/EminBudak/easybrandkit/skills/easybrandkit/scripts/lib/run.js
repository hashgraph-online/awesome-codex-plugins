"use strict";

// Where a run makes its files, and how they take the place of an earlier
// kit. A run writes into a part folder of its own, named
// .easybrandkit-part-<pid>-<8 hex>: inside the kit's folder when that is
// there already, and next to it when the run makes it. So the files are made
// on the same disk and get the mode, the group and the default ACL they would
// get in place. Only a run that ends well puts them there: the part folder
// becomes the kit's folder, or, moved into the kit's folder first when it
// is not in it, takes the earlier kit's files aside, the new ones are moved
// in, and the part folder is removed with the earlier kit in it. Runs that
// put their kits into the same folder take turns, with a lock file in it. A
// run that fails, is refused or is stopped leaves the folder as it was and
// adds nothing.

const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { sleep, timeLeft } = require("./time");

const PART = /^\.easybrandkit-part-(\d+)-[0-9a-f]{8}$/;
// The folder that keeps an earlier kit's files that a move that failed could
// not put back, which no run removes.
const KEPT = /^easybrandkit-kept-\d+-[0-9a-f]{8}$/;
// The lock, and the marker a waiting run makes to take over a lock that a
// run killed outright left.
const LOCK = ".easybrandkit-swap";
const TAKEOVER = `${LOCK}-takeover`;
// In a part folder, as its files start to move: the names the new kit brings
// into the kit's folder that the folder did not hold then, "pages/" for a
// pages folder that moves in whole.
const COMING = ".coming";
// The names a run makes in a kit's folder and removes again.
const isRunName = (name) => PART.test(name) || name === LOCK || name === TAKEOVER;
// A run killed outright (kill -9, a power cut) cannot remove its part
// folder. A later run that ends well next to it removes it once its process
// is gone and nothing in it has changed for this long.
const STALE = 15 * 60 * 1000;
// A run puts its files in place in a moment, so another one waits for its
// lock this long at most. A lock older than LOCK_STALE was left by a run
// killed outright, whatever process now has its pid.
const LOCK_WAIT = 10_000;
const LOCK_STALE = 2 * 60 * 1000;
const BUSY = ["EPERM", "EACCES", "EBUSY"];

// An error of saveRun, whose message says what the kit's folder holds.
class SaveError extends Error {}

// A path that is not there gives undefined, also when a part of it is a file.
function lstat(at) {
  try {
    return fs.lstatSync(at, { throwIfNoEntry: false });
  } catch (err) {
    if (err.code === "ENOTDIR") return undefined;
    throw err;
  }
}

const pause = (ms) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);

// Windows can refuse a rename for a moment while a virus scanner or the
// search indexer reads a file just written, so there it is tried again for
// up to two seconds, unless something is in the way.
function rename(from, to) {
  for (let waited = 0; ; waited += 50) {
    try {
      return fs.renameSync(from, to);
    } catch (err) {
      if (process.platform !== "win32" || !BUSY.includes(err.code) || waited >= 2_000 || lstat(to)) throw err;
      pause(50);
    }
  }
}

function remove(at) {
  try {
    fs.rmSync(at, { recursive: true, force: true, maxRetries: 3, retryDelay: 50 });
  } catch {
    // Held open on Windows: a later run's sweep removes it.
  }
}

// How a path in or above the kit's folder is shown: as the user gave the
// folder, relative when they gave it so.
function shownFrom(dir, at) {
  if (at === path.resolve(dir)) return dir;
  return path.isAbsolute(dir) ? at : path.relative(process.cwd(), at) || ".";
}

// The first folder up from at that is there.
function firstThere(at) {
  while (!lstat(at) && path.dirname(at) !== at) at = path.dirname(at);
  return at;
}

// Why a folder for the new kit could not be made, told with the folder it
// could not be made in, never with the part folder's name.
function notMade(dir, err) {
  const at = firstThere(path.dirname(path.resolve(err.path || dir)));
  const where = shownFrom(dir, at);
  const so = at === path.resolve(dir) ? "" : `, so ${dir} cannot be made there`;
  const said = {
    EACCES: `This user may not write in ${where} (EACCES)${so}.`,
    EPERM: `${where} may not be written in (EPERM)${so}.`,
    EROFS: `${where} is on a disk that cannot be written (EROFS)${so}.`,
    ENOSPC: `The disk that holds ${where} is full (ENOSPC)${so}.`,
    EDQUOT: `This user has no room left on the disk that holds ${where} (EDQUOT)${so}.`,
  }[err.code];
  return Object.assign(new Error(`${said || `No folder could be made in ${where} (${err.code || err.message})${so}.`} Pick a folder you can write in with --out.`), { code: err.code });
}

// Whether at is folder or a path inside it.
function within(at, folder) {
  const rel = path.relative(folder, at);
  return rel === "" || (rel !== ".." && !rel.startsWith(`..${path.sep}`) && !path.isAbsolute(rel));
}

// An error of a run that did not end well, as the user is told it: never
// with the part folder's name, which is gone by then, and a full disk told
// plainly, as the kit's disk or as the temp folder's, where the browser
// keeps its profile. An error that names no path comes from a write, and a
// run writes only into its part folder.
function toldPlainly(err, run) {
  if (err.code === "ENOSPC" || err.code === "EDQUOT") {
    const at = typeof err.path === "string" ? path.resolve(err.path) : "";
    if (!at || within(at, run.work) || within(at, run.target)) {
      return Object.assign(new Error(`The disk has no room left for the new kit (${err.code}).`), { code: err.code });
    }
    const temp = path.resolve(os.tmpdir());
    if (within(at, temp)) {
      const full = err.code === "ENOSPC" ? `The disk that holds the temp folder, ${temp}, is full (ENOSPC).` : `This user has no room left on the disk that holds the temp folder, ${temp} (EDQUOT).`;
      return Object.assign(new Error(`${full} Free some space on it, or set ${process.platform === "win32" ? "TEMP" : "TMPDIR"} to a folder on another disk.`), { code: err.code });
    }
  }
  if (run.work && String(err.message).includes(run.work)) err.message = String(err.message).split(run.work).join(run.target);
  return err;
}

// A run whose part folder was removed while it went on, as by someone
// cleaning up: a write into it then fails with an error that names a file of
// the part folder and says nothing of the site. What was removed, in words
// for the run's error (said), and whether the kit's folder still holds an
// earlier kit (earlier); null when the part folder is there.
function removedFrom(run) {
  if (!run.work || lstat(run.work)) return null;
  const shown = shownFrom(run.dir, run.home);
  const said = lstat(run.home)
    ? `The hidden folder the new kit was made in was removed from ${shown} while the kit was made, so no kit was saved.`
    : `${shown} was removed while the kit was made, so no kit was saved.`;
  return { said, earlier: run.earlier && Boolean(lstat(path.join(run.target, "brand.json"))) };
}

// The runs of this process that have not ended, and the folders of those
// that were saved.
const runs = new Set();
const saved = [];

// dir is the kit's folder as given, a folder or nothing (checkDir in
// folder.js has refused anything else); earlier says whether it holds an
// earlier kit, for what a stopped run says.
function startRun(dir, earlier) {
  const target = path.resolve(dir);
  // A link to a folder counts as that folder.
  const there = fs.statSync(target, { throwIfNoEntry: false });
  const home = there ? target : path.dirname(target);
  // The folders made for the part folder, removed again when the run does
  // not end well.
  let made;
  const above = firstThere(home);
  try {
    made = there ? undefined : fs.mkdirSync(home, { recursive: true });
  } catch (err) {
    // Made one level at a time: those that came before the one that failed
    // stay unless they are removed, deepest first.
    for (let at = home; at !== above; at = path.dirname(at)) {
      try {
        fs.rmdirSync(at);
      } catch (e) {
        if (e.code !== "ENOENT") break;
      }
    }
    throw notMade(dir, err);
  }
  const run = { dir, target, home, made: made && path.resolve(made), work: "", earlier: Boolean(earlier && earlier.length) };
  try {
    for (;;) {
      // mkdirSync, not mkdtempSync: its mode 0700 would mask a default ACL.
      run.work = path.join(home, `.easybrandkit-part-${process.pid}-${crypto.randomBytes(4).toString("hex")}`);
      try {
        fs.mkdirSync(run.work);
        break;
      } catch (err) {
        if (err.code !== "EEXIST") throw err;
      }
    }
  } catch (err) {
    removeMade(run);
    throw notMade(dir, err);
  }
  runs.add(run);
  return run;
}

function removeMade(run) {
  if (!run.made) return;
  for (let at = run.home; ; at = path.dirname(at)) {
    try {
      fs.rmdirSync(at);
    } catch {
      return;
    }
    if (at === run.made) return;
  }
}

// A run that did not end well: its part folder goes, and so do the folders
// it made while nothing else came into them. It never throws, so the run's
// own error is the one that is told.
function discardRun(run) {
  if (!runs.delete(run)) return;
  remove(run.work);
  removeMade(run);
}

// Every run of this process that has not ended, discarded, for a process
// that is being stopped: each one's folder, and whether it holds an earlier
// kit, which is as it was.
function discardRuns() {
  const stopped = [...runs].map((run) => ({ dir: run.dir, earlier: run.earlier }));
  for (const run of [...runs]) discardRun(run);
  return stopped;
}

// The folders this process has put a kit in, for what a run stopped after
// that says.
const savedRuns = () => [...saved];

function ended(run) {
  runs.delete(run);
  saved.push({ dir: run.dir });
}

// A folder that holds a file, two levels down at most.
function holdsFiles(at, depth = 2) {
  let entries = [];
  try {
    entries = fs.readdirSync(at, { withFileTypes: true });
  } catch {
    return false;
  }
  return entries.some((entry) => !entry.isDirectory() || (depth > 0 && holdsFiles(path.join(at, entry.name), depth - 1)));
}

function running(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (err) {
    return err.code === "EPERM";
  }
}

// The locks this process holds, by their token.
const held = new Set();

// The lock in a kit's folder, a file whose text names the run that holds
// it: null when there is none. It is live while that run may be putting its
// kit in: a run of this process holds it, or its process runs on this
// machine, or, from another machine, it is not old. A lock with no text yet
// is being made, unless it is a few seconds old.
function readLock(file) {
  const stat = lstat(file);
  if (!stat) return null;
  let text = "";
  try {
    text = fs.readFileSync(file, "utf8");
  } catch {
    // Not readable: told by its age alone.
  }
  let holder = {};
  try {
    holder = JSON.parse(text) || {};
  } catch {
    // Being written.
  }
  const age = Date.now() - stat.mtimeMs;
  let live;
  if (held.has(holder.token)) live = true;
  else if (!holder.token) live = age < 5_000;
  else if (holder.host !== os.hostname()) live = age < LOCK_STALE;
  // A lock with this process's pid that this process does not hold was left
  // by an earlier process that had the same pid.
  else live = Number.isInteger(holder.pid) && holder.pid > 0 && holder.pid !== process.pid && running(holder.pid) && age < LOCK_STALE;
  return { text, mtimeMs: stat.mtimeMs, live };
}

// Whether a run is putting its kit in the folder right now.
function swapping(folder) {
  const lock = readLock(path.join(folder, LOCK));
  return Boolean(lock && lock.live);
}

// The lock, made only when there is none: null when another run holds it.
function takeLock(file) {
  const token = crypto.randomBytes(4).toString("hex");
  let fd;
  try {
    fd = fs.openSync(file, "wx");
  } catch (err) {
    if (err.code === "EEXIST") return null;
    throw err;
  }
  try {
    fs.writeSync(fd, JSON.stringify({ pid: process.pid, host: os.hostname(), token }));
  } catch (err) {
    fs.closeSync(fd);
    fs.rmSync(file, { force: true });
    throw err;
  }
  fs.closeSync(fd);
  held.add(token);
  return { file, token };
}

// Removes the lock while it is still this run's.
function letGo(lock) {
  held.delete(lock.token);
  try {
    if (JSON.parse(fs.readFileSync(lock.file, "utf8")).token === lock.token) fs.unlinkSync(lock.file);
  } catch {
    // Gone already.
  }
}

// A lock left by a run killed outright is removed by one waiting run at a
// time: the one that makes the marker removes the lock, and only while it
// is still the one it found. The others find the marker there and wait, so
// two of them never both remove a lock and go on. What stopped the lock or
// an old marker from being removed comes back, as an error whose left names
// the file; null when nothing did.
function takeOver(file, seen) {
  const marker = path.join(path.dirname(file), TAKEOVER);
  const stuck = (err, at) => (err.code === "ENOENT" ? null : Object.assign(err, { left: at }));
  let fd;
  try {
    fd = fs.openSync(marker, "wx");
  } catch (err) {
    // No marker can be made: the lock stays.
    if (err.code !== "EEXIST") return stuck(err, file);
    // Another run is taking it over, or one killed while doing so left the
    // marker, which goes once it is old.
    try {
      if (Date.now() - fs.lstatSync(marker).mtimeMs > LOCK_WAIT) fs.unlinkSync(marker);
    } catch (err) {
      return stuck(err, marker);
    }
    return null;
  }
  try {
    const now = readLock(file);
    if (now && !now.live && now.text === seen.text && now.mtimeMs === seen.mtimeMs) fs.unlinkSync(file);
    return null;
  } catch (err) {
    return stuck(err, file);
  } finally {
    fs.closeSync(fd);
    try {
      fs.unlinkSync(marker);
    } catch {
      // Gone already.
    }
  }
}

// What stopped a file from moving, in words, without the part folder's
// name. Only Windows refuses to move a file that another program holds
// open. A full disk stops the lock, or the folder the earlier kit's files go
// aside into, from being made, or a name from being added to a folder.
function why(err) {
  if (!err.syscall) return err.message;
  if (BUSY.includes(err.code)) {
    return process.platform === "win32" ? `a file there is open in another program, or may not be moved (${err.code})` : `a file there may not be moved, or the folder may not be changed (${err.code})`;
  }
  if (err.code === "ENOENT") return "the folder is not there any more";
  if (err.code === "ENOSPC") return "the disk is full (ENOSPC)";
  if (err.code === "EDQUOT") return "this user has no room left on the disk (EDQUOT)";
  return `${err.moving || "a file"} could not be moved (${err.code})`;
}

// Puts the run's files in place, once no other run is putting its kit in
// the same folder. The moves themselves run at once, so a stop signal is
// handled before them or after them, never in the middle; a run that is
// stopped while it waits for the lock is not saved. earlierOf gives the
// earlier kit's file names as the folder holds them at that moment, or
// throws when the folder now holds something else. A rename that fails puts
// back what had moved, and the error says what the folder holds. The wait
// for the lock ends after LOCK_WAIT whatever holds it, and at once for a
// lock left by a run killed outright that cannot be removed, or for a live
// one once the run's time is up.
async function saveRun(run, earlierOf) {
  const { dir, target, work } = run;
  const file = path.join(target, LOCK);
  const asWas = () => (run.earlier ? "The kit already there is as it was." : "Nothing there was changed.");
  for (let waited = 0; ; waited += 50) {
    if (!runs.has(run)) throw new SaveError(`The new kit was not put in ${dir}: the run was stopped.`);
    if (!lstat(target)) {
      let made = false;
      try {
        rename(work, target);
        made = true;
      } catch (err) {
        // Made meanwhile, by another run or by hand: the files go in one by one.
        if (!lstat(target)) throw new SaveError(`The new kit could not be put in ${dir}: ${why(Object.assign(err, { moving: "its folder" }))}. Nothing there was changed.`);
      }
      // Only the move itself can fail the save: what comes after it is
      // never taken for a folder made meanwhile.
      if (made) {
        ended(run);
        sweep(path.dirname(target));
        return;
      }
    }
    let lock = null;
    try {
      lock = takeLock(file);
    } catch (err) {
      // Removed meanwhile: put in whole, as above.
      if (err.code === "ENOENT" && !lstat(target) && waited < LOCK_WAIT) continue;
      throw new SaveError(`The new kit could not be put in ${dir}: ${why(err)}. ${asWas()}`);
    }
    if (lock) {
      try {
        let earlierNow;
        try {
          earlierNow = earlierOf();
        } catch (err) {
          throw new SaveError(err.message);
        }
        swap(run, earlierNow);
      } finally {
        letGo(lock);
      }
      return;
    }
    const holder = readLock(file);
    const stuck = holder && !holder.live ? takeOver(file, holder) : null;
    // Only Windows lets go of a file a moment later, once a virus scanner
    // has read it.
    const lasting = stuck && !(process.platform === "win32" && BUSY.includes(stuck.code));
    if (lasting || waited >= LOCK_WAIT || (holder && holder.live && timeLeft() <= 0)) {
      if (stuck) throw new SaveError(`The new kit was not put in ${dir}: ${shownFrom(dir, stuck.left)} is a lock left by a run that has ended, and it could not be removed (${stuck.code}). Remove it and run again. ${asWas()}`);
      throw new SaveError(`The new kit was not put in ${dir}: another run is putting its kit there and has not finished. ${asWas()} Try again in a moment.`);
    }
    await sleep(50);
  }
}

// The moves, under the lock.
function swap(run, earlierNow) {
  const { dir, target } = run;
  const asWas = earlierNow.length ? "The kit already there is as it was." : "Nothing there was changed.";
  // A part folder made next to the kit's folder, which came there while the
  // site was read, goes into it first: a run killed in the middle of the
  // moves then leaves the earlier kit's files in the kit's folder, where the
  // next run looks for them. The folders the run made stay as they were.
  if (path.dirname(run.work) !== target) {
    const inside = path.join(target, path.basename(run.work));
    try {
      rename(run.work, inside);
    } catch (err) {
      throw new SaveError(`The new kit could not be put in ${dir}: ${why(Object.assign(err, { moving: "its files" }))}. ${asWas}`);
    }
    run.work = inside;
  }
  const work = run.work;
  const newNames = fs.readdirSync(work).filter((name) => name !== ".earlier" && name !== COMING);
  // pages/ is moved in and out only as a folder of the kit's folder: a link
  // there, say to a folder of the user's elsewhere, is never read or written
  // through, and the earlier kit's page texts are not looked for in it.
  const pagesThere = lstat(path.join(target, "pages"));
  const pagesFolder = Boolean(pagesThere && pagesThere.isDirectory());
  if (newNames.includes("pages") && pagesThere && !pagesFolder) {
    throw new SaveError(`The new kit could not be put in ${dir}: pages there is ${pagesThere.isSymbolicLink() ? "a link" : "a file"}, where the new kit has a folder of page texts. ${asWas}`);
  }
  // What the new kit brings in under names the folder does not hold now,
  // written down in the part folder before the first move. A run killed
  // while its files move leaves the earlier kit's files aside, and the next
  // run names these, and only these, as files to remove (see folder.js):
  // none of them holds a file of the earlier kit or of the user's.
  const bringing = [];
  for (const name of newNames) {
    if (name !== "pages") {
      if (!lstat(path.join(target, name))) bringing.push(name);
    } else if (!pagesThere) bringing.push("pages/");
    else for (const page of fs.readdirSync(path.join(work, "pages"))) if (!lstat(path.join(target, "pages", page))) bringing.push(`pages/${page}`);
  }
  const aside = path.join(work, ".earlier");
  // .earlier holds a pages folder only once a page text goes aside, so that
  // when none does, the earlier kit's files can be moved back in one go.
  const asidePages = path.join(aside, "pages");
  // Each move as [from, to, name, whether it moved a new file in].
  const moved = [];
  const move = (from, to, name, coming) => {
    // rename(2) would replace a file without a word: a file is replaced only
    // by moveIn, which moves it aside first.
    if (lstat(to)) throw new Error(`${name} came there while the new kit was put in`);
    if (path.dirname(to) === asidePages && !lstat(asidePages)) fs.mkdirSync(asidePages);
    try {
      rename(from, to);
    } catch (err) {
      throw Object.assign(err, { moving: name });
    }
    moved.push([from, to, name, coming]);
  };
  // brand.json goes aside first and comes in last, so the folder never
  // holds a brand.json that does not match the files next to it.
  const last = (names) => [...names.filter((name) => name !== "brand.json"), ...names.filter((name) => name === "brand.json")];
  try {
    fs.writeFileSync(path.join(work, COMING), JSON.stringify(bringing.sort()));
    // Not with recursive: a part folder that is gone is not made again.
    fs.mkdirSync(aside);
    for (const name of last(earlierNow).reverse()) {
      if (name.startsWith("pages/") && !pagesFolder) continue;
      const at = lstat(path.join(target, name));
      // A folder under a kit file's name is not the kit's.
      if (at && !at.isDirectory()) move(path.join(target, name), path.join(aside, name), name, false);
    }
    const moveIn = (name) => {
      const at = lstat(path.join(target, name));
      if (at && at.isDirectory()) throw new Error(`${name} is a folder there, where the new kit has a file`);
      // A file of the user's under a name the new kit writes is replaced, as
      // writing the new one in place would.
      if (at) move(path.join(target, name), path.join(aside, name), name, false);
      move(path.join(work, name), path.join(target, name), name, true);
    };
    for (const name of last(newNames)) {
      if (name !== "pages") moveIn(name);
      else if (!pagesThere) move(path.join(work, "pages"), path.join(target, "pages"), "pages", true);
      // A pages/ that is there keeps the files of the user's in it.
      else for (const page of fs.readdirSync(path.join(work, "pages"))) moveIn(`pages/${page}`);
    }
  } catch (err) {
    const leftEarlier = [];
    const leftNew = [];
    for (const [from, to, name, coming] of moved.reverse()) {
      try {
        // Nothing is put back over a file that has taken the old place since.
        if (lstat(from)) throw new Error(`${name} is taken`);
        rename(to, from);
      } catch {
        if (coming) {
          // A new file that will not go back is removed where it is.
          remove(to);
          if (lstat(to)) leftNew.push(name);
        } else {
          leftEarlier.push(name);
        }
      }
    }
    const said = [`The new kit could not be put in ${dir}: ${why(err)}.`];
    if (!leftEarlier.length && !leftNew.length) said.push(asWas);
    if (leftEarlier.length) {
      // What could not be put back stays, in a folder of the kit's folder
      // that no run removes, or else in this part folder, which the sweep
      // then keeps.
      const kept = path.join(target, path.basename(work).replace(/^\.easybrandkit-part-/, "easybrandkit-kept-"));
      let keptAt = kept;
      try {
        rename(aside, kept);
      } catch {
        keptAt = aside;
        runs.delete(run);
      }
      said.push(`Some files of the earlier kit could not be put back; they are in ${shownFrom(dir, keptAt)}.`);
    }
    if (leftNew.length) said.push(`${leftNew.join(", ")} of the new kit could not be taken out of it again.`);
    throw new SaveError(said.join(" "));
  }
  ended(run);
  // pages/ with nothing left in it, from an earlier run with --facts. Only a
  // real folder: on Windows, rmdir removes a link to a folder.
  if (pagesFolder) {
    try {
      fs.rmdirSync(path.join(target, "pages"));
    } catch {
      // Holding files.
    }
  }
  // The earlier kit is to go now: under another name first, since the sweep
  // keeps a part folder whose .earlier holds files, and this one can be left
  // when a file in it is held open.
  try {
    fs.renameSync(aside, path.join(work, ".replaced"));
  } catch {
    // Removed below all the same.
  }
  remove(work);
  sweep(target);
  sweep(path.dirname(target));
}

// The newest change in a folder, two levels down. A folder this user may
// list but not look into counts as changed just now, so it is kept: its
// files could not be removed anyway.
function touched(folder) {
  let newest = 0;
  const look = (at, depth) => {
    let s;
    try {
      s = lstat(at);
    } catch {
      newest = Date.now();
      return;
    }
    if (!s) return;
    newest = Math.max(newest, s.mtimeMs);
    if (depth > 0 && s.isDirectory()) {
      let names = [];
      try {
        names = fs.readdirSync(at);
      } catch {
        return;
      }
      for (const name of names) look(path.join(at, name), depth - 1);
    }
  };
  look(folder, 2);
  return newest;
}

// The part folders of runs killed outright, in folder. One whose .earlier
// holds files is kept: those are an earlier kit that was not put back. It
// runs once a kit is in place, so it never throws: a folder it cannot look
// at stays.
function sweep(folder) {
  let names = [];
  try {
    names = fs.readdirSync(folder);
  } catch {
    return;
  }
  for (const name of names) {
    const part = PART.exec(name);
    if (!part) continue;
    const at = path.join(folder, name);
    try {
      if ([...runs].some((run) => run.work === at)) continue;
      if (running(Number(part[1])) || Date.now() - touched(at) < STALE || holdsFiles(path.join(at, ".earlier"))) continue;
      remove(at);
    } catch {
      // Kept.
    }
  }
}

module.exports = { PART, KEPT, LOCK, COMING, STALE, LOCK_STALE, SaveError, isRunName, swapping, shownFrom, toldPlainly, removedFrom, startRun, discardRun, discardRuns, savedRuns, saveRun, sweep };
