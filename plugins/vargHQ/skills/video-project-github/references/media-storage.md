# Where the media goes

Checked on 2026-11-03 against GitHub's docs. Limits change; check the linked page if one looks wrong.

## The default: Releases of the same private repo

`repo.py` uploads each media file to a release called `media-store-001`, named by its hash, and lists it in `media.lock.jsonl`. Why this over the others:

- One login. No second account, card or tool for a person who has never used any of this.
- No quota to run out. GitHub's [Releases page](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases): each file "must be under 2 GiB", up to 1,000 assets per release, and "no limit on the total size of a release, nor bandwidth usage".
- Same hash, one upload. A take copied into the edit is stored once, and old versions stay downloadable.
- `.git` stays small, so cloning takes seconds and any agent can read the whole history.

## The options

| Option | Free limit | When it runs out | Fit |
|---|---|---|---|
| **Releases + hash list** (default) | Under 2 GiB per file, 1,000 files per release, no stated total | `repo.py` opens the next release | Best for one person or a small team |
| Plain git | Warns at 50 MiB, blocks at 100 MiB. Repo "ideally less than 1 GB" | Push refused. History can't shrink without rewriting it | Never for media |
| [Git LFS](https://docs.github.com/en/billing/concepts/product-billing/git-lfs) | 10 GiB storage + 10 GiB download per month, 2 GB per file | Storage over: clones get pointer files instead of your video. Download over: disabled until next month | Short projects with few versions |
| [Cloudflare R2](https://developers.cloudflare.com/r2/pricing/) + hash list | 10 GB, then $0.015/GB-month, free download | You pay cents | Large or team projects. Needs a Cloudflare account |
| Synced drive (Dropbox, Syncthing) | Your plan | Your plan | Teams already on one. [Blender Studio](https://studio.blender.org/tools/td-guide/folder_structure_overview) keeps its `shared/` folder this way |
| DVC, git-annex, git-xet | Varies | Varies | None of the 91 repos we checked use DVC or git-annex. Xet moves the repo off GitHub |

LFS has a trap for video. Every changed file counts in full, so a 500 MB master changed once is 1 GB stored, and the only way to free space is [deleting the repo](https://docs.github.com/en/repositories/working-with-files/managing-large-files/removing-files-from-git-large-file-storage). Ten re-renders of a 1 GB master fill the free tier.

## Be straight about the risk

GitHub does not forbid this, but it also does not promise it. Its docs say "Git is not designed to serve as a backup tool" and point large files to releases. Its [Acceptable Use section 9](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) lets it throttle or limit accounts with "significantly excessive" bandwidth. A film project is modest use. Using a repo as a personal cloud for years of photos is what people get warned about.

So for client work or anything you could not afford to lose, keep a second copy too: an external drive, or a synced folder. `media.lock.jsonl` tells you what should be there, and `media verify` checks it.

## When to move off the default

- A single file over 2 GiB: make a smaller master, or store it elsewhere and record it: `media note <file> --url <link>`. `pull` checks the hash whatever the source.
- More than about 50 GB, or several people downloading all day: move to R2. Upload with `rclone copy <file> r2:<bucket>/ --s3-upload-cutoff=100M --s3-chunk-size=100M` and record each with `media note <file> --url <link>`. Use links that do not expire: R2 presigned links last at most 7 days.
- A team already using LFS: keep it. Take the layout and naming from `layout.md` and skip the media list.

## Generator links are not storage

Download a generated file as soon as it is done. Veo [removes videos after 2 days](https://aistudio.google.com/docs/veo), and Volcengine's Seedance task IDs last 7 days. A provider link in `--url` is a convenience, never the only copy.

## Private means private, with limits

Only people you invite can see the repo. GitHub says private repo content "at rest" is not used to train Copilot, but [code processed while you actively use Copilot](https://github.blog/news-insights/company-news/updates-to-github-copilot-interaction-data-usage-policy/) on Free, Pro or Pro+ can be, unless you opt out in Copilot's privacy settings.

Free private repos also have [no secret scanning, no push protection](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection) and [no protected branches](https://docs.github.com/en/get-started/learning-about-github/githubs-plans). That is why the checks run on your computer as hooks. They do not come along with a clone until `restore` installs them, which is why every new copy starts with `restore`.
