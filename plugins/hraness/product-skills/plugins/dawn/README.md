# Dawn for coding agents

Compose songs in TypeScript, arrange them on a piano roll in DAWN Desktop for Mac and Linux, and render audio or MIDI locally with the DAWN CLI.

This package teaches a coding agent to compose and edit a local Dawn song,
then check it and render audio or MIDI. The included Morning study is an
original eight-bar score made with synthesized instruments.

## Set up Dawn

Dawn is a private preview. You need an authorized installation before using
this skill. Follow the [install guide](https://dawnav.com/install), then check
`dawn --version`. This package supports Dawn 0.67.2 and Bun
1.3.14 or newer. Local composition and rendering work offline.

Install the skill through your agent's skill or plugin installer. The
[agent guide](https://dawnav.com/docs/agents) explains the project layout and edit loop.

## Render a short song

Create a new project in an unused folder:

```sh
mkdir morning-study && cd morning-study && dawn init
```

Ask your agent:

> Copy the supplied Morning study example into this new project's song.ts.
> Check it, then render morning-study.wav and morning-study.mid. Tell me
> what the checks found before suggesting a musical variation.

The example is at [skills/dawn/examples/morning-study.ts](skills/dawn/examples/morning-study.ts).
It uses the project's SDK and needs no recorded samples or model download.
The commands write the two exports in the project. Review unfamiliar song
code before running it; songs are executable TypeScript. Your agent's own
model and data settings determine what it sends to its model.

For commands and score builders, see the [CLI reference](https://dawnav.com/docs/cli)
and [SDK guide](https://dawnav.com/docs/sdk).

## License

The skill, original example and integration files in this package use the
MIT license. Installing the skill does not grant access to the private preview.

## Add the skill to an agent

Set up the product as described above, then install its integration files.

For Codex CLI:

```sh
codex plugin marketplace add https://github.com/hraness/product-skills.git
codex plugin add dawn@hraness-products
```

In Claude Code:

```text
/plugin install dawn --marketplace hraness/product-skills
```

A Cursor team marketplace administrator can import
`https://github.com/hraness/product-skills`, then select this product. See
[Cursor's repository import instructions](https://cursor.com/docs/plugins#add-a-team-marketplace).
These repository installs are separate from public directory approval.
