"use strict";

// Text a site wrote, as the kit keeps it and prints it. A control character
// can clear a terminal, set its title or hide lines, so none is kept. And a
// long run of one character can hold a pattern for minutes on the one thread
// that answers Ctrl-C, so such text is cut to a sensible length where it is
// read, before any pattern meets it.

// C0 and C1 controls, but for the line break.
const CONTROLS = /[\u0000-\u0009\u000b-\u001f\u007f-\u009f]+/g;

// Text with its control characters out and its line breaks kept.
const noControls = (text) => String(text === undefined || text === null ? "" : text).replace(CONTROLS, " ");

// One line, at most max characters, with single spaces between its words.
const plainText = (text, max = 300) => noControls(text).replace(/\s+/g, " ").trim().slice(0, max).trim();

// A path without the slashes at its end. A pattern for it starts over at each
// slash of a run, so a link with a long run in it costs the square of the run.
function noEndSlashes(text) {
  let end = text.length;
  while (end > 0 && text.charCodeAt(end - 1) === 47) end--;
  return text.slice(0, end);
}

module.exports = { noControls, plainText, noEndSlashes };
