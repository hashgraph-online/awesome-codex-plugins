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

When asked for a pull request or change description, write what the diff
cannot show. Take the outcome from the whole range: read the commit list
against the final diff, drop commits that only repair earlier ones in the
range, and give peer outcomes equal weight. The latest commit, the branch name
and the incident that started the work are origins, not the outcome. Lead with
what is now different for someone using the code, and why, rather than what was
edited; keep a mechanism only when it is what they get, such as an atomicity or
API guarantee. Cut sentences a reviewer could rebuild from the diff.

Then show the smallest evidence that makes the point: a before and after
(output, failing then passing test, screenshot for a visual change), a short
diff-shaped sketch of the call path or file layout (for a UI change, the
component tree with its state and module boundaries), or a few lines of
pseudocode. Use one view when one view suffices. Show the whole block instead
of a sketch when most of it is new, when trimming would hide what owns it or
what runs first, or when the reader needs the exact shape to copy.

When the change brings in a technique, library or domain idea the repository
did not use before (search the base to confirm), explain it briefly: what it
does, why this change needed it over the usual approach, and where it would be
the wrong choice. Skip patterns the repository already uses and ordinary
renames, refactors or dependency bumps. When context already in hand (the
request, a plan, an existing description or the commit messages) shows the
change is one step of a larger piece of work, say what the whole delivers and
what came before or remains, as far as known, and name any choice that plan
attributes to the caller so reviewers do not reopen it. Never infer a series or
go looking for a plan to fill this in.

State reversibility and reach plainly: can the change be undone by reverting,
or does it migrate data, delete state or alter a public contract; and which
consumers, platforms or workflows could notice. Name what was tested and what
was not, and the review findings or judgment calls the change leaves open, so
they sit beside the diff instead of leaving with the session. Size the
description by what the reviewer still has to work out, not by line count or
file type: a few lines of ranking logic or an edited skill file may need a
sharp risk statement, a large mechanical rename two sentences. Open with one
idea in a sentence or two, not a template of empty sections.
When the repository has a pull request template, fill it: its required lines
(trailers, checklists) may be what a merge or squash keeps.

Some words in a title or description are tool actions. Link the issue or
report the change addresses. Add a closing keyword such as `Fixes #123` only
when the change fully resolves the item, targets the branch where the tracker
acts on it, and the caller owns that close; put it where that tracker reads it,
since some read the description and some only commit messages. Cite partial,
follow-up or uncertain items as related references in their own sentence, away
from fix or close wording, and keep the references an existing description
already carries. Follow the repository's title convention (its instructions,
then recent history). Where commit types drive versioning, prefer fix over feat
when either fits, and add a breaking-change marker only on the caller's
confirmation: it chooses a version.

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
