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

An owner adds a pack without a pull request. One file in the project is used only there. One file
in the user folder is used in every project on the machine. Further folders are named with
`edgeCases.packsPaths`. The project folder is the path `ns path edge-case-packs` prints
(`edge-cases/packs` inside `.nightshift` on the current layout).

POSIX:

```bash
project_packs="$(ns path edge-case-packs)"
mkdir -p "$project_packs"
cp plugins/nightshift/skills/nightshift/references/templates/edge-case-pack.md "$project_packs/<key>.md"
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/nightshift/edge-cases/packs"
cp plugins/nightshift/skills/nightshift/references/templates/edge-case-pack.md "${XDG_CONFIG_HOME:-$HOME/.config}/nightshift/edge-cases/packs/<key>.md"
```

PowerShell:

```powershell
$projectPacks = ns path edge-case-packs
New-Item -ItemType Directory -Force $projectPacks
Copy-Item plugins/nightshift/skills/nightshift/references/templates/edge-case-pack.md (Join-Path $projectPacks '<key>.md')
New-Item -ItemType Directory -Force "$env:APPDATA\nightshift\edge-cases\packs"
Copy-Item plugins/nightshift/skills/nightshift/references/templates/edge-case-pack.md (Join-Path $env:APPDATA "nightshift\edge-cases\packs\<key>.md")
```

`edgeCases.packTemplatePath` names the owner's own template. Empty uses the shipped one.
`ns catalog-index --catalog edge-cases --template` prints the path in force, and
`--check-draft FILE` names each required section a draft lacks.
