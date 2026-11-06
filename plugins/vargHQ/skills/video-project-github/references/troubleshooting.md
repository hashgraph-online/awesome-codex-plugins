# If something fails

Run `python3 tools/repo.py status` first. A version is safe once it says "Backed up to GitHub".

| What you see | What it means | Do this |
|---|---|---|
| `gh: command not found`, `git: command not found` | Tool missing | `python3 <skill>/scripts/repo.py doctor` prints the exact install command for this computer |
| `xcrun: error: invalid active developer path` | Mac without command line tools | `xcode-select --install`, click Install, wait, retry |
| `python3` not found on Windows | Named differently | Use `python`, or `winget install Python.Python.3.12` |
| `gh auth status` fails | Not signed in | `gh auth login --web --git-protocol https`. The code lasts 15 minutes. Never paste a token into chat |
| `STOP. <file>:<line> looks like a ...` | A key inside a file | Move the value to `.env` and read it from the environment. If it is not a secret, add `repo:allow` in a comment on that line |
| `STOP. <file> is media and would bloat git` | A media type the ignore list lacks | Add the type to `.gitignore` and `save` again. Never use `git add -f` |
| `STOP. ... is PUBLIC` | The repo is visible to anyone | `gh repo edit --visibility private --accept-visibility-change-consequences`. If keys were in it, replace them at the provider, since they count as leaked |
| `remote: error: GH001: Large files detected` | A file over 100 MB got into a version | See "A big file got into git" below |
| `GH007: Your push would publish a private email address` | Commit email is your real one | `git config user.email <id>+<login>@users.noreply.github.com`. `repo.py` sets this for new projects |
| `.git: Operation not permitted` on `git init`, in Codex | Codex's default sandbox never allows writes inside `.git`, in any project | Approve the command when Codex asks, or give that session write access. Do not let the agent work around it by copying the project to a temp folder: the backup then lives apart from your real folder and the next save has nothing to connect to |
| `NOT BACKED UP YET` | No internet or GitHub trouble | Your version is safe on this computer. Run `save` again later |
| `STOP. This would overwrite versions` | A force push was tried | Do not bypass it. `save` merges both sides |
| `Both versions changed the same lines` | Two copies edited one line | Open each listed file, keep the right lines, run `save`. To cancel: `git merge --abort` |
| `MISSING <file>` after `restore` | Not uploaded from the other computer, or the store release was deleted | On that computer run `media push`, then `save`. `media verify` lists what is not backed up |
| `CHANGED <file>` in `media verify` | The file differs from the list | Run `save` to record it. The old bytes stay in the store and earlier versions still point at them |
| `... is over the 2 GB limit` | Too big for one stored file | Make a smaller master, or see `media-storage.md` |
| HyperFrames: `Directory already exists and is not empty` | `init` needs a new folder | From the root: `npx hyperframes init edit --non-interactive --skip-transcribe` |
| HyperFrames: `missing_local_asset` | Media outside the project folder | Copy the file into `edit/assets/` |
| Agent says a safety rule blocked the upload | Its permission mode is cautious about uploads | Say so in your own words: "Yes, upload this project to my private GitHub repo." Do not turn off its safety settings |
| Reverted something in Claude Code, but the render did not come back | `/rewind` [does not track files changed by shell commands](https://code.claude.com/docs/en/checkpointing), so ffmpeg output is not covered | Use `back <version>` |

## A big file got into git

Files go in versions before they go to GitHub, so the fix depends on how far it got. Tell the person first, and make a copy of the folder before any of this.

- **Only in the last version, not on GitHub yet:** `git reset --soft @{u}` (or `git reset --soft HEAD~1`), add the type to `.gitignore`, `git rm --cached <file>`, then `save`.
- **Deeper in history, repo is yours alone:** `git filter-repo --strip-blobs-bigger-than 50M` in the copy, then check the project opens and connect the copy to a new private repo. Rewriting is the one thing that needs the person's explicit yes.
- **Simplest, when history does not matter:** a new repo from the current files with `adopt --apply`.

## A key got into a version

Replace the key at its provider first. That is what actually fixes it: GitHub says "revoke and/or rotate that secret" first, and "You cannot remove sensitive data from other users' clones". Even in a private repo, assume anyone with access has it. Afterwards, clean the history the same way as a big file (`git filter-repo --replace-text`) or start a new repo.

`repo.py check --history` scans every version for keys and big files. Run it on any project that existed before this skill.

## Is it really safe?

Run `python3 tools/repo.py proof`. It makes a fresh copy from GitHub, restores everything and compares every hash. If that passes, a new laptop will work too.
