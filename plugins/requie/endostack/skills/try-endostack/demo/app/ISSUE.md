# Downloads fail for files with spaces in the name

Reported by: support queue

Steps:

1. Start the server with `node server.mjs`.
2. Open `http://localhost:3000/`. The list includes `meeting notes.txt` and its link `/files/meeting%20notes.txt`.
3. Open that link.

Expected: the file downloads.

Actual: `404 not found`. Files without spaces, such as `roadmap.txt`, download fine.

Several customers name files with spaces, so this blocks them from getting their own uploads back.
