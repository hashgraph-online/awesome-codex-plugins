# Change-driven documentation

Load this when a finished or proposed change may have made documentation
wrong, or when a reviewer needs a description of the change. It adds no
release, version or delivery authority to [Doc](../SKILL.md).

## Find what the change touched

Start from the exact change: a commit range, branch against its merge base, or
the caller's named working-tree files. List the public surface it adds, alters,
renames or removes: commands and flags, configuration keys and environment
variables, endpoints, exported types, skills, defaults, limits and error
messages. Internal refactors with no visible effect usually need no document
change; say so instead of editing.

For each surface item, search the documents that mention it, including
examples, tables, counts, diagrams and instruction files such as `AGENTS.md`.
Name the search terms and paths you checked; an unsearched area is a gap, not
a clean result.

## Check each reader need

Readers arrive with different questions. For each changed item, check whether
the documentation still answers the ones that apply:

| Reader is | Needs | Typical home |
|---|---|---|
| Learning the tool | A first working path from a clean start | Getting started, README quick start |
| Doing a task | The steps for one goal, with real commands | How-to sections, CONTRIBUTING |
| Looking something up | Exact names, options, defaults, limits | Reference tables, `--help`, API docs |
| Deciding or debugging | Why it works this way and what it trades away | Architecture notes, ADRs |

Not every item needs all four. A frequent gap is reference-only coverage: the
option is listed, but no document shows how to accomplish the task it exists
for. Report missing coverage as a finding; write new pages only within the
authorized request.

## Apply factual updates; ask about judgment calls

Correct what the change proves wrong: paths, names, counts, defaults, examples
and stale cross-references. These follow from the diff and need no extra
approval inside an authorized documentation task.

Stop and ask before rewriting positioning or narrative, removing a section,
choosing a version number, or resolving two documents that disagree about
intent rather than fact. Preserve changelog and release-note history: correct
wording in place and never regenerate or drop existing entries.

Re-run an example or command you changed when it is read-only, or in the
disposable environment the [developer journey](developer-journey.md) uses;
otherwise say it was not run. A diagram that still names a removed or renamed
component is a finding even when you cannot redraw it.

## Describe a change for reviewers

When asked for a pull request or change description, lead with what changed
for the reader of the code and why. Then show the smallest evidence that makes
the point: a before and after (output, failing then passing test, screenshot
for a visual change), a short diff-shaped sketch of the call path or file
layout, or a few lines of pseudocode. Use one view when one view suffices.

State reversibility and reach plainly: can the change be undone by reverting,
or does it migrate data, delete state or alter a public contract; and which
consumers, platforms or workflows could notice. Name what was tested and what
was not. A small change gets a few sentences, not a template of empty sections.
When the repository has a pull request template, fill it: its required lines
(trailers, checklists) may be what a merge or squash keeps.

## Release notes for a range

For changelog or release-note entries, list the commits or merged changes in
the exact range, then group them by what a user notices, not by commit. Leave
out changes with no visible effect. Write each entry from the diff rather than
the commit subject, and cite the commits or pull requests it covers so a
reader can check it. Choosing a version number or publishing stays with the
caller.

## Return

Changed paths with a one-line reason each, coverage findings left unfixed,
questions that need the owner, and the checks you ran.
