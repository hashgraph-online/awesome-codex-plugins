# Homie plugin

The Homie plugin for Claude Code, Codex and Grok: a studio in a box for your AI. It makes games,
music and video, and publishes them from a studio that runs on your own Cloudflare account,
on the free plan.

- **Skills** (`skills/`): `studio-setup`, `plan`, `parallel`, `game`, `port`, `publish`,
  `office`, `servers`, `shop`, `sound`, `music`, `art`, `style`, `models`, `video`, `playtest`, `perf`, `lab`,
  `parts` and `standalone` (a game as a desktop app or a phone app: the files Steam and the app stores accept
  for upload).
- **MCP server** (`.mcp.json`): the Homie MCP server at `https://homie.rocks/mcp`, which has
  creator tools only. Nothing in this folder runs a command on install.
- **The Homie mod** (`hooks/`, `mod/`): a Claude Code mod (Claude Code 2.1.287 or later, the CLI and
  the desktop app's Code tab). Below: what it adds, and everything it does.
- **Homie's hooks for Codex** (`hooks/codex.json`, `hooks/codex.mjs`): the mod's holds, refusals and
  secret redaction as Codex lifecycle hooks, decided by the same module (`hooks/lib/holds.mjs`). See
  "Homie's holds in Codex" below for what Codex can and cannot do.
- **Homie's hooks for Grok** (`hooks/grok.json`, `hooks/grok.mjs`): the same holds, decided by the same
  module (`hooks/lib/holds.mjs`, through `hooks/codex.mjs`), so Claude Code, Codex and Grok cannot drift.
  Grok Build answers allow or deny; a hold denies the call until the person says `proceed <code>`.
  Grok runs them once the plugin is trusted. It reads the hooks file the plugin's ROOT `plugin.json` names
  (`"hooks": "./hooks/grok.json"`), and with none named it loads `hooks/hooks.json`, which here is the
  Claude Code mod's file and holds no hooks for Grok. Before the root manifest named it,
  Grok registered nothing from this plugin (`total_hooks=0` in its log) and a deploy ran unheld. 0.30.2 read
  that as "Grok runs no plugin's hooks", which was wrong: it was this plugin's layout. PostToolUse replaces
  what Grok reads (`updatedToolOutput`), so a secret is out of the model's copy and still on the person's
  screen. `homie-studio setup status --client grok` reads the hooks' own mark and says whether they ran just
  now; while it says off, the `studio-setup` skill tells Grok to ask the person itself.
  In Grok Build the plugin installs with `grok plugin install homie-rocks/homie#plugins/homie` (checked on
  1.0.41; Grok asks whether to trust it, or takes `--trust`, and loads its skills, MCP server and hooks only
  once you do). Grok Bot installs Homie itself when told to read https://homie.rocks/install.md (checked
  2026-10-04, as far as the Cloudflare approval); Grok chat with only the connector is not tested by us.
- **Tell Homie** (the Homie MCP's `homie_feedback`, the mod's `/feedback`): a short note to the people who make
  Homie, which the person sees word for word and sends only with their yes. See "Tell Homie" below.
- **The providers' own tools** (`providers.json`): see below.
- **Manifests:** `.claude-plugin/plugin.json` (Claude Code), `.codex-plugin/plugin.json`
  (Codex), `.grok-plugin/plugin.json` (Grok Build: the same skills, the Homie MCP server and
  `hooks/grok.json`), and `plugin.json` (the agent-plugins standard). They say the same thing, and
  `test/manifests.test.mjs` checks that they do. Codex reads the skills, the MCP server and Homie's
  hooks from `.codex-plugin/plugin.json`, and ignores the mod. `plugin.json` declares no `$schema`:
  Codex (0.156.1 to 0.160.0, tested) reads a root `plugin.json` only when it declares the Agent
  Plugins schema, and then runs none of the plugin's hooks. Its top-level `"hooks"` is for Grok Build,
  which takes a plugin's hooks file from the root `plugin.json` and from nowhere else (above).

Install it, and read what a studio is and what it costs, in the
[repository's README](https://github.com/homie-rocks/homie#readme). In short:

- **Claude Code**, inside a session (2.1.275 or later): `/plugin install homie --marketplace homie-rocks/homie`.
  It asks you to confirm the marketplace, then opens the plugin's details, where you pick a scope. From a
  terminal: `claude plugin marketplace add homie-rocks/homie`, then `claude plugin install homie@homie` (the
  terminal's `install` takes no `--marketplace`).
- **Codex**: `codex plugin marketplace add homie-rocks/homie`, then `codex plugin add homie@homie`, a new session,
  and `/hooks` to trust Homie's three hooks.
- **Grok Build**: `grok plugin install homie-rocks/homie#plugins/homie`, then a new session.
- **The Claude app** (web, desktop, phone), the connector alone:
  [add Homie as a connector](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Homie&connectorUrl=https%3A%2F%2Fhomie.rocks%2Fmcp)
  (the link opens "Add custom connector" with Homie filled in, and you confirm), or by hand Settings →
  Connectors → Add custom connector → `https://homie.rocks/mcp`.

Report a vulnerability as [SECURITY.md](SECURITY.md) says.

## The providers' own tools

Homie works through each provider's own CLI, plugin, MCP server and skills, on the creator's own
account, and keeps only its own layer on top: budgets and receipts, the kids rules, secrets never in the
chat, the owner's one-tap asks, phone budgets, and the rights and licence notes. Nothing here installs by
itself. `providers.json` lists each provider's tools (checked 2026-10-03), the skills that use them, and
what stays Homie's; `plugin.json` points at it (`extensions["rocks.homie"].providers`). Each skill names
its providers in its own frontmatter (`metadata.providers`, and `compatibility` in words), and a skill
that uses a provider's MCP server declares it for Codex in `agents/openai.yaml`, so Codex can wire it
when the skill is used. A skill offers a provider's tool only when the person wants what it unlocks; the
person approves every install and signs in on the provider's own page.

| Provider | What Homie's skills use | Offered when the person wants it |
| --- | --- | --- |
| Cloudflare | Wrangler, pinned in the studio (`login`, `--device` where no browser opens; `deploy`, D1, R2, secrets, `ai models list`) | Cloudflare's plugin (`cloudflare/skills`: its skills and API MCP server), its docs MCP server |
| ElevenLabs | ElevenLabs' CLI (`elevenlabs auth login`; music, stems, speech to text, the subscription) | ElevenLabs' plugin (`elevenlabs/plugin`: its skills and hosted MCP server), `npx skills add elevenlabs/skills` |
| fal | fal's MCP server to find models and read schemas and prices; the skills' scripts for paid runs (priced, capped, receipted, resumable) | fal's CLI (`fal auth login`, `fal keys create`) to make the key |
| Tripo | Tripo's models on fal (`tripo3d/...`) | none: Tripo's own CLI and MCP server bill a separate account |
| GitHub | the GitHub CLI (`gh auth login --web`, `gh pr create`) | GitHub's MCP server (`github@claude-plugins-official`) |
| Stripe | Stripe's MCP server (the shop's catalog, tax settings and sales, as the owner signed it in, a sandbox first); the shop's key only through `homie-studio shop connect` | Stripe's agent plugin (`stripe agent setup`: its MCP server and skills) once a studio sells; Stripe Projects (`setup --via stripe-projects`) as an option for Cloudflare and ElevenLabs |
| Ollama | Clef on the person's own computer, when Ollama already has `clef-flash`: `dev`'s AI guides, chat review and game decisions, and `agents sit --brain local`, free (detection reads `/api/version` and `/api/tags`, loopback only) | `ollama pull clef-flash` (about 11 GB), only after the person's yes to that size |

Stripe is the `shop` skill's, with its own rules for Stripe's tools: never a webhook or an API key through the MCP
(the mod refuses a write that would hand a signing secret back), Stripe's own confirmation link for a refund it
holds, and live mode only when the owner says so.

The AI guides think with Cloudflare's Clef decision model on the studio's own Workers AI (the `servers` skill), and a
game may ask it for its own decisions (`net.decide`, the `game` skill). Under `dev`, Clef can run on the person's own
computer through Ollama instead; nothing downloads it by itself, and the mod holds a pull until the person says yes.

## The Homie mod

Inside a studio (a folder with `studio.json` at or above where Claude Code runs):

- **The band above the prompt:** `◆ Night Owls · Owl Rush · Checks ▰▰▰▰▱▱ 62% · 4/5 checks ·
  3 playing now · ▶ Play`. One row; parts drop from the end on a narrow terminal. Nothing outside
  a studio.
- **The Studio pane** (`/studio`). It opens by itself when a build starts, where the terminal is
  wide enough for a pane nobody asked for (Claude Code places one from 144 columns, 110 once you
  have opened it yourself); otherwise a toast says `/studio` shows it.
  - **Build:** the build's progress feed: Plan → Build → Checks → Deploy, each check going
    green, the latest check frame (coloured cells in the terminal, a picture on the desktop),
    ▶ Play and ◉ Watch links, Stop the build, and **Watch it live**, a live view of a room of the
    game being built, drawn in the tab.
  - **Rooms:** every live room on the live site and on this computer's dev site, with players and
    AI, Watch and Join links, and **Watch in the pane**. The owner view (`o`) lists who is in each
    room, with **Mute**, **Kick** and **Announce** through the studio's own back office
    (`homie-studio office`). A kick or a mute is only *asked for*: the office answers with a
    one-time link, the pane shows it under "Waiting for your tap", and nothing happens until you
    confirm in your own browser. The mod cannot confirm an ask; no key or command can.
  - **Games:** each game's launch state (private, invite-only beta, public),
    changed the same asked-for way.
  - **Stats:** the studio's own counts (visits, plays, rounds, peak players, where people came
    from), read on request.
  - **Codex:** each Game Codex at a glance (sections filled, open questions, milestones, latest
    lines) and a private link to its page.
  - **Lab:** the Game Lab (the `lab` skill, studio 0.20.0 and later): whether its page is running
    on this computer, with its link, and each game's last lab check: the take, New's phases beside
    Today's, whether each build replays the same frames, and the game's JavaScript per frame in
    both. Read from `.studio/lab/`; nothing is run.
  - **Parts:** see below.
  - **Art:** art direction (the `style` and `models` skills), per game, newest first: the phase
    strip (`Style ✓ → Cast 3/7 → Rigs → Animations → In game`), the look line, the style
    decisions with their state (`·` auto, `~` steered, `●` pinned by use, `■` locked) and who set
    them, a palette's colours, the cast (route, licence, state, cost, **STALE** when made under an
    older decision), the scene budgets as bars (draw calls, triangles, picture memory, shipped
    payload: the asset check's inventory estimate; red when over), the spend against the art budget, and licence problems with their
    fix. **Lock** on a decision is your word (`homie-studio style lock`); **Unlock** first asks,
    with what goes stale and what remaking it costs (`style blast`), and unlocks only on Proceed.
    Its Characters section lists each rigged character with its skeleton family, bones and clips (how many
    retargeted onto it, which verbs it lacks) and a skinning bar: a full room's skinned vertices a frame on
    a phone. Read from `.studio/art/<game>/latest.json`, which the studio's toolkit writes after every
    `style`, `assets` and `anim` command; the tab rereads it while it is open.
- **The parts pane** (`/parts`): when Claude builds in parallel (the `parallel` skill), each agent
  with its time, tool calls, files changed and last step, and the build feed's checks for each
  part. It opens by itself when two agents run at once.
- **The arcade** (`/arcade [game]`): play a real Homie game while Claude works, in a public room
  with strangers and bots: Homie Arcade's games, or your studio's own. Click the pad line, then
  the arrow keys or WASD; space acts; Esc gives the keys back to Claude. See "The game bridge".
- **Instant commands** (no Claude turn; they print links or open a pane, and never open a
  browser): `/studio [tab]`, `/play [game]`, `/watch [room|game]`, `/rooms`, `/build`,
  `/codex [game]`, `/deploy-status`, `/perf-numbers [game]` (the perf skill owns `/perf`),
  `/parts`, `/arcade [game]`, and for art direction `/look [game]` (the look and the style
  decisions; it opens the Art tab, since the style skill owns `/style`), `/lock <decision> [game]`
  (your typed words lock it), `/assets [game]` (the cast, the spend, licence problems),
  `/cast [game]` (the characters: skeleton, bones, source, clips, and what skinning a full room costs on a
  phone), `/clips [game]` (each character's clips against the verbs the game needs, and the command that adds
  what is missing), `/lineup [game]` (the last lineup's flags and where its pictures are; it never renders one) and
  `/rights [game]` (licence problems with their fixes, and the game's `RIGHTS.md`), and `/feedback [your words |
  send | cancel]` (Tell Homie, below).
- **Tell Homie** (`/feedback`, or **Tell Homie** in the Studio pane's header, `t`): a pane with a note to the
  people who make Homie, exactly as it would go: its kind, the words (your own, after keys, paths, emails and
  code are taken out), and what goes with it (the step, the studio's and the plugin's versions, the app).
  Change the kind, the words or add a reply address, then **Send** (`s`) or **Don't send** (`n`). `/feedback`
  alone opens it to write one, or **Ask Claude to draft it from this session** puts that ask in the prompt box
  for you to send. Where no pane draws, `/feedback <words>` prints the note and `/feedback send` (typed by you;
  never by Claude) sends it. It posts only to `homie.rocks/api/feedback/tell` (or the studio's own directory),
  and only on your Send.
- **Guards:** a call is held in Claude Code's own question dialog (Proceed or Cancel), with what
  would change drawn above it and in full in the Hold pane:
  - an edit (Edit, Write, MultiEdit, NotebookEdit) to a file `studio.json` `"protect"` lists, with
    its diff;
  - a production deploy (`homie-studio deploy`, `npm run deploy`, `wrangler deploy`,
    `studio_deploy`, a song or video `publish`), with where it goes, what it creates, the commits
    and files since the last deploy, uncommitted changes, new games, the last checks and who is
    playing;
  - a paid media call (fal, ElevenLabs, Tripo: the skills' `gen`, `render` and `stems` with `--yes`,
    the models skill's `prop` and `mood` with `--yes`, a request straight at their APIs, a
    generating command of the provider's own CLI (`elevenlabs music compose`, `elevenlabs
    text-to-speech`, `fal api`, `genmedia run`, `tripo make` and the like; their help, `--dry-run`,
    sign-in, pricing and listings are free), a generating tool of their own MCP server or a
    connector (a run or a job; finding a model, its schema or its price, and an ElevenLabs
    `estimate_only`, are free)) that would pass `studio.json` `"budget"`, the build's budget or the
    job's cap (a game's models share `art/<game>-models/budget.json`), or whose cost cannot be read
    first, with the estimate from the skill's own `--dry-run`;
  - a change to the studio's Cloudflare account outside its deploy, inside a studio: Wrangler
    deleting something (a Worker, a D1 database, an R2 bucket or object, a KV namespace or key, a
    queue, a secret), a `secret put` or `bulk` (to Cloudflare, a secret put is a deployment), a
    version rolled out or rolled back by hand, a migration applied or SQL that writes, on the live
    database (`--remote`); and the same through Cloudflare's own MCP servers or a claude.ai
    Cloudflare connector (the API server's `execute` sending anything but a GET or a GraphQL read;
    a tool that deletes, updates, edits, puts, deploys or rolls back; a database query that
    writes). The studio's deploy records what it creates in `studio.json` and never touches what it
    did not create; these go around that record. The hold names the studio's own Worker, database
    or bucket when the change does. Creating something new and reading anything are not held, and
    `--local` never is;
  - a Clef model downloaded through Ollama (`ollama pull clef-flash`, about 11 GB; `clef`, the 27B,
    about 18 GB; a request at Ollama's `/api/pull` naming one), with its size, anywhere: Homie never
    downloads a model by itself. `ollama run` of a Clef model is held only when Ollama's own list on
    this computer (`/api/tags`) does not have it yet. Other models and Ollama's other commands are not
    held.
  - a note to Homie from Claude (the Homie MCP's `homie_feedback` with `action: "send"`, local or remote): asked
    with **Send** / **Don't send** and the note's exact words (all of them in the Hold pane). A draft is not
    held (it sends nothing); the mod fills in the studio's and the plugin's versions and the app, and tells
    Claude that Claude Code asks. Once you have sent or declined a note in a session, another offer from Claude is
    refused (you can still ask for one). This hold has no switch.
  Cancel, a dismissed question, and a run with nobody to ask (`claude -p`) all refuse the call,
  with a reason Claude can act on. The guards hold even in bypass-permissions mode. What each guard
  holds or refuses, and its words, are decided in `hooks/lib/holds.mjs`, which Homie's hooks for Codex
  share (see "Homie's holds in Codex").
- **Refused outright** (nobody is asked; the reason says what to do instead):
  - an Edit, Write or MultiEdit to `games/<id>/codex/decisions.json` that changes the value or the
    state of a decision the person locked, or leaves the file unreadable while one is locked: a
    locked decision changes only through `homie-studio style set … --unlock --reason`, after the
    person saw what goes stale (`style blast`);
  - a production deploy while a public game (not private or invite-only)
    ships an asset whose `assets/manifest.json` entry has no licence, a kind the studio does not
    know, TurboSquid's licence, or CC BY without an attribution line. When every asset is licensed, the deploy's hold says so;
  - a `git add` or `git commit` that would put a file over 5 MB under `games/` into git (what is
    staged is read from git itself), naming each file and its size: big files go to the studio's
    R2, raw models stay in `art/<slug>/raw/`;
  - a write through Stripe's MCP (`stripe_api_write`, from Stripe's plugin, `claude mcp add` or the
    Claude app's connector) that makes a webhook endpoint, or an event destination with its signing
    secret included: Stripe answers the secret in that call, so it would land in the conversation.
    `homie-studio shop connect` makes the shop's webhook instead, and the secret goes straight to the
    Worker. Reads, the catalog's writes and turning an endpoint off go through.
- **Secrets out of tool output:** before Claude reads any tool's result, keys and tokens come
  out: office and stats keys (`hsk_`), progress keys (`hbk_`), agent passes (`hap_…`, whose public
  id stays), Cloudflare tokens and keys, fal, ElevenLabs, Anthropic, OpenAI, GitHub, npm, Stripe
  keys and webhook signing secrets, AWS and Google keys, bearer tokens, private keys, and any `NAME=value` whose name says key,
  token or secret and whose value looks like one. A one-time owner link goes to the person in
  the Studio pane (Rooms, "Links for you"); Claude reads that it is there.
- **Homie's results, drawn:** the setup status as a checklist with what to do now, a check's and
  a port check's rows, a playtest's verdicts with the weakest first, a deploy with its live link
  and each game's Play, a note to Homie in its frame, and the Homie MCP's cards; each Homie command's row says what it is in
  words, with the command beside it.

### Studio settings it reads

```json
{
  "protect": ["games/*/game.json", "site/theme.json"],
  "budget": { "usd": 10, "credits": 2000 }
}
```

- `protect`: globs, relative to the studio (`*` within a folder, `**` across folders, a folder
  for everything under it).
- `budget`: the most the studio's media jobs spend in all, per unit: dollars (fal) and credits
  (ElevenLabs), counted from every job's `budget.json`. Each job's own cap still applies; the
  skills refuse past it.

### Its own settings (`/config`, or `pluginConfigs` in settings.json)

| Option | Default | What it turns on |
| --- | --- | --- |
| `paneAutoOpen` | on | The Studio pane when a build starts, the parts pane for two agents |
| `band` | on | The band above the prompt |
| `guardFiles` | on | Holding edits to protected files; refusing changes to locked art decisions and files over 5 MB under `games/` into git |
| `guardDeploys` | on | Holding production deploys, and changes to the studio's Cloudflare account outside its deploy (deletes, secrets, hand rollouts, writes to the live database, by Wrangler or Cloudflare's MCP); refusing a deploy that ships an asset with no allowed licence |
| `guardSpend` | on | Holding paid media calls past the budget (the models skill's too), and the ones whose cost cannot be read first (a provider's own CLI, MCP server or API); and holding a Clef model download through Ollama (about 11 GB) |
| `redactSecrets` | on | Taking secrets out of tool output |
| `renderResults` | on | Homie's results and command rows drawn natively |
| `arcade` | on | `/arcade` and the live Watch views |
| `pictures` | `blocks` | `blocks`: frames as coloured cells (any truecolor terminal); `image`: real pixels where the terminal draws images (kitty, Ghostty, iTerm2, WezTerm) |

### Where it draws

| Where | What you get |
| --- | --- |
| `claude` in a terminal | Everything. Pictures are coloured cells (`▀`, two pixels a cell), or real pixels with `pictures: image` |
| The desktop app's Code tab | Everything; pictures are drawn as images (`Svg`), refreshed up to four times a second |
| VS Code's chat panel, `claude -p`, the Agent SDK, cloud sessions | The guards and secret redaction run; nothing draws. The commands print text instead of opening panes, and a held call is refused when nobody can be asked |

## What the Homie mod does

`claude plugin validate plugins/homie` lists what Claude Code reads from the mod (Claude Code
2.1.287):

```text
❯ ./homie.mjs hooks: session.start, session.end, command.run{command=studio}, command.run{command=build},
  command.run{command=rooms}, command.run{command=play}, command.run{command=watch}, command.run{command=codex},
  command.run{command=deploy-status}, command.run{command=perf-numbers}, command.run{command=parts},
  command.run{command=arcade}, command.run{command=look}, command.run{command=lock}, command.run{command=assets},
  command.run{command=cast}, command.run{command=clips}, command.run{command=lineup}, command.run{command=rights},
  command.run{command=feedback}, tool.call, tool.call{tool=Edit|Write|MultiEdit|NotebookEdit}, tool.call{tool=Bash},
  tool.call{tool=/"^mcp__.+__studio_deploy$"/}, tool.call{tool=/"^mcp__.*homie.*__homie_feedback$"/},
  tool.call{tool=/"^mcp__.*stripe.*__stripe_api_write$"/i}, tool.call{tool=/"^mcp__.*(?:fal|eleven|tripo).*__"/i},
  tool.call{tool=/"^mcp__.*cloudflare.*__"/i}, turn.complete,
  ui.render{component=AbovePrompt}, ui.render{component=Pane}, ui.render{component=AskUserQuestion},
  ui.render{component=ToolUse}, ui.render{component=ToolResult}, ui.render{component=ToolGroup}, ui.message, ui.close
❯ ./homie.mjs calls: $.agent.list, $.clock.every, $.command.register, $.fs.exists, $.fs.list, $.fs.read, $.fs.stat,
  $.http.fetch, $.process.run, $.process.spawn, $.prompt.fill, $.session.cwd, $.session.surfaces, $.store.get, $.store.set,
  $.ui.ask, $.ui.blit, $.ui.close, $.ui.invalidate, $.ui.log, $.ui.open, $.ui.panes, $.ui.resolve, $.ui.toast
❯ ./homie.mjs surface modules: hooks/lib/arcade-pad.mjs
```

**The events it handles:**

- `session.start` / `session.end`: find the studio, register the commands, start a 2-second
  timer that rereads the studio's files; end any game bridge.
- `command.run` (its eighteen commands only).
- `tool.call` (every tool): after the tool ran, take secrets out of its result; note which Homie
  command ran (for drawing it) and which agent ran what (for the parts). It never changes a tool's
  input.
- `tool.call` on Edit, Write, MultiEdit, NotebookEdit (protected files, locked art decisions); on
  Bash (big files into git, deploys and their licences, Cloudflare changes, paid calls, Clef model
  downloads); on
  `studio_deploy` (a deploy and its licences); on the Homie MCP's `homie_feedback` (a note's send waits for your
  Send; a draft gets the studio's facts); on Stripe's `stripe_api_write` (a webhook secret); on fal, ElevenLabs and
  Tripo MCP tools (paid calls); on Cloudflare MCP tools (account changes): the guards. They hold or
  refuse; they never approve. The mod has no `tool.check` hook, so it cannot approve a call a
  permission rule would ask about or deny.
- `turn.complete`: a part (a subagent) ended; reread the build after a turn.
- `ui.render` on the band, its panes, the question dialog (only for its own holds), and the rows
  and results of Homie commands. Every other site is left to Claude Code.
- `ui.message`: the arcade pad's keys. `ui.close`: a pane closed, so its game bridge ends.

**Its calls, and what each reaches:**

| Call | What for | What it reaches |
| --- | --- | --- |
| `$.fs.exists`, `$.fs.list`, `$.fs.read`, `$.fs.stat` | The studio's own files | `studio.json`, `.studio/` (the build feed, `local.json`, the Game Lab's `server.json` and last checks, art direction's `art/<game>/latest.json`), `games/*/game.json`, `CODEX.md`, `codex/decisions.json` (an edit to it), `assets/manifest.json` (before a deploy) and whether `assets/RIGHTS.md` exists, media jobs' `budget.json`, `.perf/`, `.wrangler/homie-dev.json`, the file a held edit names, and the size of a file a `git add` or `git commit` would stage. Never a key file, the keychain or the environment. It writes no file (no `$.fs.write`) |
| `$.http.fetch` | Live rooms, games and the arcade's list; whether the Game Lab answers; the game bridge; whether Ollama already has a Clef model, before a download is held; a note you pressed Send on | Only the studio's own live site, this computer's dev site and Game Lab (`127.0.0.1`), Ollama's model list on this computer (`127.0.0.1:11434/api/tags`, or a loopback `OLLAMA_HOST` the command sets), `*.homie.rocks` (a note: one POST to `homie.rocks/api/feedback/tell`, only on your Send), and the bridge's private Unix socket. Any other address is refused in the code |
| `$.process.run` | The back office, stats and codex links; Lock and Unlock (and Unlock's blast radius); deploy summaries; what a commit would stage; prices | Only `node` with the studio's own pinned `homie-studio` (`--json`), `git -C <studio or a folder in it>` (read-only: `rev-parse`, `log`, `status`, `diff`, `diff --cached`), and a media skill's own `--dry-run` (free; it asks the provider's price list). No shell |
| `$.process.spawn` | The game bridge (`mod/bridge.mjs`), only while the arcade or a live Watch is open | One headless Chrome on this computer (below) |
| `$.store.get`, `$.store.set` | The commit of the last deploy, per studio | Claude Code's own store for this plugin, nothing else |
| `$.agent.list` | The parts | The session's subagents (names and states) |
| `$.session.cwd`, `$.session.surfaces` | Which studio; whether anything draws | |
| `$.ui.*` | Its band, panes, toasts, dim transcript lines, holds | |
| `$.clock.every`, `$.command.register` | Its timer and commands | |
| `$.prompt.fill` | Tell Homie's **Ask Claude to draft it**: the ask goes into the prompt box | Your prompt box only; you send it (or not) with Enter |

It never calls a model (`$.model`), submits a prompt (Tell Homie's ask only fills the box), messages another session, reads settings or
environment variables (`$.settings`, `$.env`), or approves a permission. A test
(`test/mod-lib.test.mjs`) fails if the hooks module calls anything this README does not name.

### The game bridge

A mod has no sockets and no browser, so a pane cannot sit in a netplay room by itself.
`mod/bridge.mjs` does it the way a person's browser does: it starts one headless Chrome on this
computer, opens the game's own page (`/<game>/play`, or `/<game>/watch?room=<id>`), and the game
runs there for real: a seat in a public room with strangers and bots, hosting the room when nobody
else can. The bridge sends the mod what Chrome shows (a screenshot a frame, scaled down) and takes
the keys you press. It needs Node 22 and Google Chrome (or `CHROME_PATH`), and nothing else.

- **Cost, measured on an Apple M4:** about a quarter of one core while you play (Chrome, at the
  lowest priority the computer gives, `nice 15`), and none while the pane is hidden: the page is
  frozen (no JavaScript, no frames). It ends when you leave, when the pane closes, when the mod
  stops pinging it for 45 s, or when Claude Code goes away.
- **Frame rate:** 8 frames a second in the terminal, 4 on the desktop (Claude Code redraws a
  pane up to ten times a second, thirty in the terminal for the shown pane). The picture is
  as many cells as the pane has, two pixels a cell: a 90-column pane is 90×110 pixels.
- **Keys:** a terminal sends no key-up, so a press holds the key for a moment and the terminal's
  own repeat keeps it held.
- **Network:** the bridge talks to Chrome on this computer; Chrome talks to the game's site.

### Limits and what mods cannot do (Claude Code 2.1.287)

- The question dialog takes at most 12 rows of a mod's drawing above it, and counts a row as
  about 38 cells whatever the terminal's width, so a hold's panel there is short; the Hold pane
  has the whole story, and in a terminal too narrow for a pane nobody asked for, dim transcript
  lines do.
- A pane Claude Code opens for a build or a hold, unasked, appears only from 144 columns (110
  once you have opened it yourself).
- The guards read shell text: `$(...)`, aliases, `eval`, `bash -c "..."` and scripts that run a
  deploy or a paid call are not seen. They are a net, not a sandbox; use permission rules for a
  hard block. A shell command that writes a protected file or a locked decision (`sed -i`, `>`)
  is not held, and a big file staged by a script is not seen.
- A mod cannot draw in claude.ai or the Claude app's Chat tab; the Homie MCP's cards (MCP Apps)
  stay the way there.
- Secret patterns are patterns: a key in a format they do not know passes, and a long random
  value after a name like `SOMETHING_KEY=` is hidden even when it is not a secret.

Tested with Claude Code 2.1.287: `claude plugin test plugins/homie` (the mod's tests, every hook,
command and drawing on the terminal and the desktop surface) and
`node --test plugins/homie/test/mod-lib.test.mjs`.

## Homie's holds in Codex

Codex has no mods, but it runs a plugin's lifecycle hooks. `hooks/codex.json` runs `hooks/codex.mjs` on
three of them, and every decision comes from `hooks/lib/holds.mjs`, the module the mod asks too, so the
two apps hold the same calls with the same words:

- **PreToolUse** (shell commands, `apply_patch` edits and MCP tools): holds and refusals.
- **UserPromptSubmit**: the person's own answer to a hold.
- **PostToolUse**: secrets out of what the model reads, and the commit a deploy shipped.

**Turning them on.** Codex runs a plugin's hooks only after the person trusts them: after installing Homie,
open `/hooks` and trust Homie's three. Until then Codex skips them without a word, and so does `codex exec`.
They need Node 22 (`node` on the path of a login shell), which a studio needs anyway.

**Knowing whether they are on.** Because Codex says nothing when it skips them, the hooks say it themselves:
each time one runs (a message, a tool call) it leaves a dated mark, `codex.json` (`grok.json` in Grok Build),
in `.cache/homie-studio/holds/` of the home folder: the app, the time and which hook, nothing about the
folder, the session or the call. `homie-studio setup status --client codex` (or `grok`; in Codex the
toolkit also reads the app from its environment) reads it as a row, **Homie's holds**: on when the mark is
from the last ten minutes, off otherwise, with how to turn them on (in Grok Build: trust the plugin, which
`grok plugin install … --trust` does, and start a new session). The `studio-setup` skill passes it on: one
sentence in the first reply when they are off, and from then on the AI asks before a deploy, a Cloudflare
change, a paid call or a model download itself. When they are on nothing changes. The row is a report, not
a lock: a mark can be forged like any file, and nothing reads it to let a call through.

**How a hold is answered.** A Codex hook can refuse a call or let it through, but it cannot ask the
person: Codex refuses `permissionDecision: "ask"` as unsupported, and then runs the call. So a held call is
refused with a short code, and the person sees in Codex what it holds (the same lines as the mod's Hold
pane). Then:

1. They answer in their own message: `proceed H7K2` lets exactly that call through once, in that session,
   within an hour; `cancel H7K2` refuses it. A bare `proceed` or `cancel` answers the one hold waiting, when
   only one is.
2. Only a message the person sends reaches the prompt hook, so the model cannot answer for them.
3. After a `proceed`, Codex runs the same call again.
4. In `codex exec`, where nobody can answer mid-run, a hold refuses. `codex exec resume <session>
   "proceed H7K2"` answers it.

Codex's own approval prompts, sandbox and rules still apply on top.

| | Claude Code (the mod) | Codex (Homie's hooks) |
| --- | --- | --- |
| An edit to a file `studio.json` `"protect"` lists | Held, with its diff (Edit, Write, MultiEdit, NotebookEdit) | Held, with its diff (`apply_patch`, also through the shell); every protected file in one patch is named |
| A change to a locked art decision | Refused | Refused (a patch that deletes `decisions.json` too) |
| A production deploy | Held: where, what it creates, commits and files since the last deploy, uncommitted files, new games, the last checks, licences, who is playing | Held, with the same facts. Commits are counted since the last deploy made through Codex, or since `.studio/local.json`'s deploy time. New games and players come from the live site, read by the hook |
| An unlicensed asset in a public game's deploy | Refused | Refused |
| A Cloudflare change outside the deploy (Wrangler, Cloudflare's MCP servers) | Held, naming the studio's own Worker, database or bucket | Held, the same |
| A paid call (fal, ElevenLabs, Tripo; the skills, the providers' CLIs, MCP servers and APIs) | Held past a budget or when it cannot be priced first; a toast with the price when inside | Held the same; inside the budget, a line with the price for the person |
| A Clef model download (Ollama) | Held, with its size | Held, with its size |
| A file over 5 MB under `games/` into git | Refused | Refused |
| A Stripe MCP write that would hand back a webhook's signing secret | Refused | Refused |
| A note to Homie (`homie_feedback` send) | Held with the note's exact words: **Send** / **Don't send**; a draft is not held | Held with the note's exact words; `proceed <code>` sends exactly that note, once |
| Secrets in a tool's result | Taken out before Claude reads it. The transcript keeps the redacted copy. A one-time owner link goes to the Studio pane | Taken out before the model reads it. Codex's own screen and its session file keep the raw output, and a one-time owner link stays there for the person |
| Asking | Claude Code's question dialog (Proceed / Cancel) and the Hold pane | The person's own `proceed <code>` / `cancel <code>` |
| Nobody to ask (`claude -p`, `codex exec`) | Refused | Refused, and `codex exec resume` can answer it |
| Settings | `/config`: `guardFiles`, `guardDeploys`, `guardSpend`, `redactSecrets` | The same names as environment variables set to `off`: `HOMIE_GUARD_FILES`, `HOMIE_GUARD_DEPLOYS`, `HOMIE_GUARD_SPEND`, `HOMIE_REDACT_SECRETS` |
| When a check itself fails | The call is refused | The call is refused. Codex runs it anyway if the hook cannot start at all (no `node`) or takes longer than its timeout (90 s for a hold, which can wait on a skill's own `--dry-run` price) |

**Not in Codex:**

- The band, the panes, the instant commands, the arcade and the drawn results (Codex has no mods).
- A question dialog: Codex has no ask from a hook.
- Redaction of what the person's own screen and Codex's session file keep.
- Hosted tools such as web search, which no hook sees.

**Where the holds are a net, not a lock.** Hooks are a net, as the mod is:

- They read shell text, so `$(...)`, `bash -c "..."` and scripts are not seen (the same as in Claude Code).
- A shell command that writes a protected file is not held.
- A hold's answer lives in the plugin's data folder (`PLUGIN_DATA`). Codex's sandbox keeps the model out of
  that folder, but under full access a model could forge an answer there.
- **Another MCP server named `homie`** in Codex's own configuration (`config.toml`) keeps the name, and the
  plugin's connector (`.mcp.json`, also `homie`) then does not load. The hooks still run. `homie-studio setup
  status --client codex` says so (it reads only whether that entry is an address or a command, never the
  command), and `codex mcp add homie-rocks --url https://homie.rocks/mcp` adds Homie's connector under its
  own name; the holds match a Homie tool under either name.

For a hard block, use Codex's own rules (`prefix_rule(..., decision="forbidden")` in the `rules/` folder of
Codex's home, `$CODEX_HOME`); a plugin cannot ship those.

`node <this plugin>/hooks/codex.mjs check -- <command>` says what Homie would do with a command, and runs
nothing.

Tested with Codex 0.156.1 and 0.160.0, each in a throwaway `CODEX_HOME` with a stand-in model and no
sign-in:

- An `apply_patch` to a protected file was held, then let through by `proceed`.
- A fal call past a job's cap was held at the skill's own price, then let through by `proceed`.
- `wrangler d1 delete` of the studio's database was held, then refused by `cancel`. It never ran.
- `npm run deploy` was held, then let through by `proceed`.
- A fal key was taken out of a command's output.

`test/codex-hooks.test.mjs` runs the hook script on a real studio folder with the JSON Codex sends, and
checks every answer against the fields Codex accepts. Codex refuses an answer with a field it does not
know, and then runs the call.

## Tell Homie

The people who make Homie read every note, and someone who is stuck rarely writes to a forum. So when a person is
stuck, confused or frustrated, after an error Claude could not fix, or at the end of a first studio setup or first
publish, Claude may offer, once in a session, to send a short note about it. It never sends one without their yes:

- **The tool** is `homie_feedback`, the same on the Homie MCP at homie.rocks (claude.ai, and this plugin in Claude
  Code, Codex and Grok Build) and on the local Homie MCP (`homie-studio mcp`, Homie for Claude Desktop). `action: "draft"` (the
  default) sends nothing: it answers with the note exactly as it would go, a card where the app shows cards (Send,
  Edit, Don't send), and the same text for the chat. `action: "send"` sends only that draft (its `draft` id, with the
  same fields; any change is refused), and `action: "decline"` records a no.
- **The yes** is the person's own: the card's Send; in Claude Code, Send in Claude Code's own question (the mod
  holds every send); in Codex, `proceed <code>` (Homie's hooks hold every send); elsewhere, Grok included, their yes in the chat.
  A no is final for the session. The skills (`studio-setup`, `publish`) and the studio's `AGENTS.md` say when to
  offer, and that help never depends on it.
- **What a note is:** its kind (stuck, confusing, idea, praise, bug), the words, the step or skill it is about, the
  studio's and the plugin's versions, the app, whether Claude offered it or the person asked, how they said yes,
  and a reply address only if they typed one. Before anyone sees it, the mod's own redaction (keys, tokens,
  private keys, owner links) and a note's own (code, home folders, email addresses, a workers.dev address's account
  name, network addresses, long opaque strings) take things out, and the note says what was taken. homie.rocks
  takes them out again when it arrives. No file, log, screenshot or studio content is ever attached.
- **Where it goes:** homie.rocks's private feedback store, with the website's Feedback & help reports, read only by
  the people who make Homie. A studio.json can name only Homie's own directory (or this computer, for tests), so a
  studio borrowed from somebody else cannot send notes anywhere else. [homie.rocks/privacy](https://homie.rocks/privacy/)
  says what is kept.
- **Once, and no nagging:** an offer that was sent or declined ends offers for the session; an offer nobody
  answered may be reworded three times and no more. The person asking to tell Homie something is never refused.
  "Offered" and how the yes was given are the tool's own word, kept as a label for reading the notes.

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
