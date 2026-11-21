"use strict";

// What a kit's folder holds, and whether a run may put a kit there: read
// before a run starts and again as its files go in, without changing
// anything. A folder that holds someone else's files is refused, and so is
// one that a run killed outright left without the earlier kit's brand.json,
// with what to do about it.

const fs = require("fs");
const path = require("path");
const { FACT_FILES } = require("./facts");
const { PART, KEPT, COMING, isRunName, swapping, shownFrom } = require("./run");

// The files an earlier kit lists, by name only: a brand.json someone edited
// cannot point a new kit's move outside the folder, or at a hidden file.
function kitFiles(kit) {
  const files = [
    ...[].concat(kit.logos || []).flatMap((logo) => [logo && logo.file, logo && logo.svg]),
    ...[].concat(kit.screenshots || []).map((shot) => shot && shot.file),
    kit.card && kit.card.file,
    ...[].concat(kit.stores || []).flatMap((source) => [].concat((source && source.assets) || []).map((asset) => asset && asset.file)),
  ];
  return files.filter((file) => typeof file === "string" && file).map((file) => path.basename(file)).filter((file) => !file.startsWith("."));
}

// The names every kit writes, whatever its brand.json lists.
const KIT_NAMES = ["brand.json", "BRAND.md", "_brand.yml", ...FACT_FILES];

function readKit(dir) {
  try {
    const kit = JSON.parse(fs.readFileSync(path.join(dir, "brand.json"), "utf8"));
    return kit && kit.version === 1 ? kit : null;
  } catch {
    return null;
  }
}

// Where the brand.json of an earlier kit waits when a run did not finish
// putting its own kit in the folder: in the .earlier of that run's part
// folder, when the run was killed while its files moved, or in the folder
// its error named, when the moves could not be undone. Only those in the
// kit's folder are looked at: one next to it could be another folder's.
function earlierAside(target) {
  let names = [];
  try {
    names = fs.readdirSync(target).sort();
  } catch {
    return "";
  }
  for (const name of names) {
    const at = PART.test(name) ? path.join(target, name, ".earlier") : KEPT.test(name) ? path.join(target, name) : "";
    if (at && readKit(at)) return at;
  }
  return "";
}

// What a run killed while its files moved in had brought into the folder
// under names the folder did not hold before: moving the earlier kit's
// files back leaves these, and a later run would take them for the user's
// own. The run wrote those names down in its part folder before its first
// move, so a file of the earlier kit's or of the user's is never among
// them, also once some were moved back by hand: those named are the ones
// that are in the folder and no longer in the part folder, "pages/" for a
// pages folder that moved in whole.
function broughtIn(target, aside) {
  if (path.basename(aside) !== ".earlier") return [];
  const part = path.dirname(aside);
  let names;
  try {
    names = JSON.parse(fs.readFileSync(path.join(part, COMING), "utf8"));
  } catch {
    return [];
  }
  const there = (at) => {
    try {
      return Boolean(fs.lstatSync(at, { throwIfNoEntry: false }));
    } catch {
      return false;
    }
  };
  // Only names of the kind a run writes down, none that leads out of the
  // folder.
  const plain = (name) => typeof name === "string" && (name === "pages/" || /^(pages\/)?[^./\\][^/\\]*$/.test(name));
  return [].concat(names).filter((name, i, all) => plain(name) && all.indexOf(name) === i && there(path.join(target, name)) && !there(path.join(part, name)));
}

// What a run killed while its files moved in left behind in a folder that
// held no kit, so that it moved nothing aside: the names its part folder
// wrote down, as in broughtIn.
function leftByKilled(target) {
  let names = [];
  try {
    names = fs.readdirSync(target).filter((name) => PART.test(name)).sort();
  } catch {
    return [];
  }
  for (const name of names) {
    const theirs = broughtIn(target, path.join(target, name, ".earlier"));
    if (theirs.length) return theirs;
  }
  return [];
}

// Whether a folder holds a file.
function holdsFile(at) {
  try {
    return fs.readdirSync(at, { withFileTypes: true }).some((entry) => !entry.isDirectory());
  } catch {
    return false;
  }
}

// "a", "a and b", "a, b and c".
const listed = (names) => (names.length < 2 ? names.join("") : `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`);

const mayNotOpen = (dir, at, code) => new Error(`This user may not open ${shownFrom(dir, at)} (${code}). Pick a folder you can write in with --out.`);

// lstat, with a folder this user may not look into told plainly: the first
// one up the path whose own entry this user can see.
function look(at, dir) {
  try {
    return fs.lstatSync(at, { throwIfNoEntry: false });
  } catch (err) {
    // Below a file, or below a link that leads nowhere: checkDir finds which
    // one on its way up the path.
    if (err.code === "ENOTDIR" || err.code === "ELOOP") return undefined;
    if (err.code !== "EACCES" && err.code !== "EPERM") throw err;
    let shut = path.dirname(at);
    for (;;) {
      try {
        fs.lstatSync(shut);
        break;
      } catch {
        if (path.dirname(shut) === shut) break;
        shut = path.dirname(shut);
      }
    }
    throw mayNotOpen(dir, shut, err.code);
  }
}

// What the kit's folder holds, read before a run and again as its files go
// in: nothing (null), when it is not there or empty, or an earlier
// easybrandkit kit, whose file names come back: the files its brand.json
// lists, by name only, and the fixed names a kit writes. A folder that holds
// anything else is refused, so a run never mixes into or overwrites
// someone's own files, and so is a path that is not a folder or below a
// file; the refusal of a folder whose earlier kit a run left in pieces says
// where its brand.json and its page texts are, and which files that run
// brought in. A link to a folder counts as that folder, and a link to
// nothing is refused. The part folders and the lock of runs do not count,
// and nothing is changed. With facts, a pages there that is not a folder is
// refused, since the kit does not write through it. A folder whose
// brand.json is away while another run puts its kit in counts as a kit
// (saving is false before a run, when the folder is read again under the
// run's own lock).
function checkDir(dir, { facts = false, saving = false } = {}) {
  const target = path.resolve(dir);
  for (let at = target; ; at = path.dirname(at)) {
    const stat = look(at, dir);
    if (stat) {
      let real = stat;
      if (stat.isSymbolicLink()) {
        try {
          real = fs.statSync(at);
        } catch (err) {
          if (err.code === "ENOENT" || err.code === "ENOTDIR") throw new Error(`${shownFrom(dir, at)} is a link to ${fs.readlinkSync(at)}, which is not there. Pick a folder with --out.`);
          if (err.code === "ELOOP") throw new Error(`${shownFrom(dir, at)} is a link that does not lead to a folder. Pick a folder with --out.`);
          throw err;
        }
      }
      if (!real.isDirectory()) throw new Error(`${shownFrom(dir, at)} is a file, not a folder. Pick a folder with --out.`);
      // A folder up the path: the run makes the rest.
      if (at !== target) return null;
      break;
    }
    if (path.dirname(at) === at) return null;
  }
  // A folder this user may list but not open: nothing in it can be read or
  // moved. Windows has no such folder.
  try {
    fs.accessSync(target, fs.constants.X_OK);
  } catch (err) {
    if (err.code === "EACCES" || err.code === "EPERM") throw mayNotOpen(dir, target, err.code);
    throw err;
  }
  let names;
  try {
    names = fs.readdirSync(target).filter((name) => !isRunName(name));
  } catch (err) {
    if (err.code === "EACCES" || err.code === "EPERM") throw new Error(`This user may not read ${dir} (${err.code}). Pick a folder you can write in with --out.`);
    throw err;
  }
  let old = names.length ? readKit(target) : null;
  if (!old && !saving) {
    // Another run may be putting its kit in place right now, with brand.json
    // or every file of the earlier kit aside: this run reads the folder
    // again when it saves. Or it was done between two looks, and the next
    // run has just begun, so the folder counts as left in pieces only when
    // two reads find no brand.json and no lock is seen around them.
    for (let reads = 0; !old && reads < 2; reads++) {
      if (swapping(target)) return [...KIT_NAMES];
      old = readKit(target);
    }
    if (!old && swapping(target)) return [...KIT_NAMES];
  }
  if (!old) {
    // A run killed while its files moved can leave the earlier kit aside,
    // with some of its own files in the folder or none: another folder
    // would leave that kit in pieces for good.
    const aside = earlierAside(target);
    if (aside) {
      const shown = shownFrom(dir, aside);
      const theirs = broughtIn(target, aside);
      const remove = theirs.length ? `remove ${listed(theirs)}, which that run brought in too, ` : "";
      // The earlier kit's page texts wait in a pages folder of their own: a
      // folder cannot be moved over the kit's pages folder, which holds that
      // run's page texts or the user's files.
      const back = holdsFile(path.join(aside, "pages"))
        ? `Move the files in ${path.join(shown, "pages")} back into ${path.join(dir, "pages")}, and the other files in ${shown} back into ${dir}`
        : `Move them back into ${dir}`;
      throw new Error(`${dir} holds no brand.json: a run that did not finish putting its kit in place left the earlier kit's brand.json in ${shown}, with the files it had moved aside. ${back}, replacing any files of the same name there, which are that run's, ${remove}and run again.`);
    }
    if (names.length === 0) return null;
    const theirs = leftByKilled(target);
    if (theirs.length) throw new Error(`${dir} holds no earlier brand kit, only what a run that did not finish putting its kit in place left there: ${listed(theirs)}. Remove ${theirs.length === 1 ? "it" : "them"} and run again, or pick another folder with --out.`);
    throw new Error(`${dir} is not empty and holds no earlier brand kit. Pick another folder with --out.`);
  }
  const pages = facts && fs.lstatSync(path.join(target, "pages"), { throwIfNoEntry: false });
  if (pages && !pages.isDirectory()) {
    throw Object.assign(new Error(`${path.join(dir, "pages")} is ${pages.isSymbolicLink() ? "a link" : "a file"}, and --facts saves the text of each page it reads in a folder by that name. Move it away, or pick another folder with --out.`), { earlierKit: dir });
  }
  return [...new Set([...kitFiles(old), ...KIT_NAMES])];
}

module.exports = { checkDir };
