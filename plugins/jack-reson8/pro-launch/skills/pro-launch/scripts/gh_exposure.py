#!/usr/bin/env python3
"""Is anyone actually seeing the open-source repos, and are the lists we PR to alive? (needs `gh` logged in)

  python3 gh_exposure.py repos [owner]                 stars · views (uniques) · clones (uniques) · referrers per public repo
  python3 gh_exposure.py lists owner/repo ...          stars · open PRs · merged in last 14 days · last merge  → ALIVE / DEAD
  python3 gh_exposure.py prs [author]                  my open PRs, each with its target list's liveness

Read it like this: views≈0 with dozens of clones = bots and indexers, not people (no human exposure yet).
A list with <3 merges in 14 days is dead for our purpose: a PR there is never seen. Check `lists` BEFORE writing PRs.
"""
import datetime, json, subprocess, sys


def gh(*a):
    r = subprocess.run(["gh", *a], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def since(days):
    return (datetime.date.today() - datetime.timedelta(days=days)).isoformat()


def repos(owner):
    rows = gh("repo", "list", owner, "--limit", "100", "--json", "name,stargazerCount,isPrivate,isFork") or []
    print(f"{'repo':<28}{'stars':>6}{'views':>12}{'clones':>14}  referrers")
    for r in rows:
        if r["isPrivate"] or r["isFork"]:
            continue
        n = r["name"]
        v = gh("api", f"repos/{owner}/{n}/traffic/views") or {}
        c = gh("api", f"repos/{owner}/{n}/traffic/clones") or {}
        ref = gh("api", f"repos/{owner}/{n}/traffic/popular/referrers") or []
        refs = ",".join(f"{x['referrer']}:{x['count']}" for x in ref) or "-"
        print(f"{n:<28}{r['stargazerCount']:>6}{v.get('count', 0):>6} ({v.get('uniques', 0):>3}){c.get('count', 0):>7} ({c.get('uniques', 0):>3})  {refs}")


def live(repo):
    m = (gh("api", f"search/issues?q=repo:{repo}+is:pr+is:merged+merged:>{since(14)}") or {}).get("total_count", 0)
    o = (gh("api", f"search/issues?q=repo:{repo}+is:pr+is:open") or {}).get("total_count", 0)
    last = gh("pr", "list", "-R", repo, "--state", "merged", "--limit", "1", "--json", "mergedAt") or [{}]
    s = (gh("api", f"repos/{repo}") or {}).get("stargazers_count", 0)
    return s, o, m, (last[0].get("mergedAt") or "-")[:10]


def lists(names):
    print(f"{'list':<48}{'stars':>8}{'open':>7}{'merged14d':>11}  last merge  verdict")
    for n in names:
        s, o, m, last = live(n)
        print(f"{n:<48}{s:>8}{o:>7}{m:>11}  {last:<10}  {'ALIVE' if m >= 3 else 'DEAD'}")


def prs(author):
    rows = gh("search", "prs", "--author", author, "--state", "open", "--limit", "100", "--json", "repository,url,createdAt") or []
    seen = {}
    for p in rows:
        r = p["repository"]["nameWithOwner"]
        if r not in seen:
            seen[r] = live(r)
        s, o, m, last = seen[r]
        print(f"{'ALIVE' if m >= 3 else 'DEAD ':<6} {p['createdAt'][:10]}  {p['url']}  (merged14d={m}, last={last})")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("repos", "lists", "prs"):
        sys.exit(__doc__)
    me = (gh("api", "user") or {}).get("login", "")
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "repos":
        repos(rest[0] if rest else me)
    elif cmd == "lists":
        lists(rest)
    else:
        prs(rest[0] if rest else me)


if __name__ == "__main__":
    main()
