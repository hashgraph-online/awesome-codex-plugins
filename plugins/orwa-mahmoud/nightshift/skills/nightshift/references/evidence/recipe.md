# Adding an evidence kind

An evidence kind is markdown, not code. It tells the agent how to capture one kind of evidence.
It touches no hooks and changes no gate, which is why the catalog can grow without the product
growing.

**Adding one is one new file and no edits to shared files:**

```text
skills/nightshift/references/evidence/kinds/<key>.md
```

The file name is the key. Nothing shared changes — not the index, not a test file someone else
is also editing — so two contributors can add a kind the same week and never meet in a diff.
`ns catalog-index --catalog evidence` lists the directory, so a new file is offered the moment
it lands.

Copy `skills/nightshift/references/templates/evidence-kind.md` and fill it. The structural rules
in `tests/evidence-catalog.bats` glob the directory and already cover the new file.

## Shape

The H1 is `# <Title> — <which items this kind fits>`. The body is five sections, in this order:

1. **When it applies.** Which items take this kind.
2. **Evidence lines.** The `Evidence:` lines to suggest, with a concrete width, command, figure, or file name.
3. **How to generate.** The steps, tools, and settings that produce each piece, and the file name it gets in the item's evidence folder, `receipts/<NN>-<slug>-<id>/`.
4. **How to verify.** What to check when reviewing the evidence. For screenshots: the named widths, both themes, no overflow, and no placeholder text.
5. **Never.** What must not appear. Secrets, tokens, and personal data are never in a screenshot, a recording, or a log.

## The evidence-check block

Add one fenced `evidence-check` block, anywhere in the kind, when a file can be counted. With
`check: block`, the gate then holds the tick until those files exist. A kind with nothing mechanical
to check, such as a refactor note, has no block, and that is valid: the gate holds only the files an
item names, and `--check-draft` says so.

Both runtimes read the same three lines and no others:

```evidence-check
files: *.png
min: 1
type: image
```

- `files:` a file-name pattern.
- `min:` how many matching files must exist, a positive integer.
- `type:` `image`, `text`, `json`, or `any`.

An unknown key, a missing key, or any other `type:` is rejected. The block says a file is present. It does not say the work is right.

## Owner kinds

An owner adds a kind without a pull request: in this project's `.nightshift/catalogs/evidence/`,
in the user folder for every project (`$XDG_CONFIG_HOME/nightshift/catalogs/evidence` on POSIX,
`%APPDATA%\nightshift\catalogs\evidence` on Windows), or in a folder named by
`catalogs.evidence.paths`. `ns catalog-new --catalog evidence --key <key>` starts one from the
template in force, `catalogs.evidence.template` names the owner's own template, and
`ns catalog-index --catalog evidence --check-draft FILE` checks what Nightshift reads from a draft.
[Owner knobs](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/knobs.md#catalogs) lists the precedence.
A project kind wins over a configured folder, which wins over a user kind, which wins over the
shipped kind of the same key. Owner kinds stay on the machine. Purge removes the project folder
with the rest of `.nightshift/` and does not touch the user folder. Reset and Archive leave both.
Every catalog works the same way: [Add to a catalog](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/add-to-a-catalog.md).

## Concrete lines

A kind that names no concrete file, command, or figure is followed literally, and a model produces exactly the vague line it was given.
