# Edge-case catalog

Read this only after the owner says yes to an edge-case pass. List the packs with
`ns catalog-index --catalog edge-cases` and read only the packs that fit the drafted items.
An owner's pack of the same key replaces the shipped one, and the index names the source.
For each drafted item, pick the cases that the item can actually meet, never every case for every
item, and turn each into one WHEN/THEN line a test could fail on. The owner keeps, edits or drops
each line; only the kept ones reach the drafting table. Suggest from the owner's packs where they
fit, and offer once to draft a new pack from the template when none fits, written only after the
owner says yes.

A case becomes a line by naming the concrete situation and the observable result:

```text
    - WHEN the config file is empty THEN the loader names the file and the key it expected
    - WHEN the import is run twice THEN the second run adds no rows and says so
```

"Handles errors" or "works on Windows" is not a line. Name the input, the state or the platform,
and what someone would see.

## Adding a pack

A pack is markdown, not code. One new file, and the index lists it.

```text
skills/nightshift/references/plan/edge-cases/<key>.md
```

Copy `skills/nightshift/references/templates/edge-case-pack.md`. The file name is the key. The H1 is
`# <Pack> — <which items it fits>`. The body is When it applies, Cases, and Example lines, in that
order. Cases are named cases. Example lines has at least one WHEN/THEN line.

An owner adds a pack without a pull request: in this project's `.nightshift/catalogs/edge-cases/`,
in the user folder for every project (`$XDG_CONFIG_HOME/nightshift/catalogs/edge-cases` on POSIX,
`%APPDATA%\nightshift\catalogs\edge-cases` on Windows), or in a folder named by
`catalogs.edge-cases.paths`. `ns catalog-new --catalog edge-cases --key <key>` starts one from the
template in force, `catalogs.edge-cases.template` names the owner's own template, and
`ns catalog-index --catalog edge-cases --check-draft FILE` checks what Nightshift reads from a draft.
[Owner knobs](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/knobs.md#catalogs) lists the precedence.
Every catalog works the same way: [Add to a catalog](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/add-to-a-catalog.md).
