# The prompt to paste

For an agent that does not have the `video-project-github` skill. Paste this as it is.

```text
Keep this project in a private GitHub repo. I am not technical and have never used git, so do everything yourself and talk to me
in plain words: "saved", "version", "go back". Never move, rename or delete my files.

1. Check that git and the GitHub CLI (gh) work and install what is missing. If `gh auth status` fails, run
   `gh auth login --web --git-protocol https` and give me the one-time code. Never ask me for a password or a token.

2. Before the first `git add`, write .gitignore with: .env .env.* !.env.example *.pem *.key credentials* node_modules/ .hyperframes/
   renders/ tmp/ .DS_Store, and every media type in upper and lower case: mp4 mov m4v webm mkv mxf wav mp3 m4a aac flac png jpg jpeg
   webp gif tif exr heic psd blend glb fbx zip.

3. Search every text file for API keys, tokens and passwords. Move each value to .env, read it from the environment in that file,
   and write .env.example with the names only. Tell me which keys you found.

4. Git holds text only. Media goes in Releases of the same repo, so one login covers everything:
   - Write media.lock.jsonl: one JSON line per media file, sorted by path, with path, sha256 and bytes, plus prompt, model, seed and cost if you can tell them.
   - Upload each file named as the first 32 characters of its sha256 plus its extension, to a release called media-store-001 created
     with --latest=false. One file must be under 2 GB (if not, stop and tell me). A release holds at most 1000 files; start media-store-002 after that.
   - Write tools/restore.py using only the Python standard library and gh: it downloads every file in media.lock.jsonl to its path and checks the hash.

5. Create the repo with `gh repo create <name> --private --source . --remote origin --push`, then check that `gh repo view --json visibility`
   says PRIVATE. If it does not, stop and tell me.

6. Prove it: clone the repo into a temporary folder, run tools/restore.py, compare every hash, then delete the folder. Tell me the result.

7. Write AGENTS.md with these rules for every later session: save a version after each finished step; update media.lock.jsonl and
   upload new media before saving; never overwrite a take; keys only in .env; never `git reset --hard`, `git clean`, `git push --force`
   or `git rebase`; to go back, run `git restore --source=<version> -- <path>` and save that as a new version.

8. At the end tell me in five lines: the link, that only I can see it, what is not in GitHub and why, how I get it all back on a new
   laptop, and how to undo something.
```
