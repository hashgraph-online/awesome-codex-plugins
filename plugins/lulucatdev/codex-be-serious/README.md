# codex-be-serious

一个 Codex 插件，使 agent 以严肃学者的方式讲话：正式、克制、概念清楚，接近大学出版社教材或学术专著的书面语体。它抑制俚语、谄媚表达、填充词、emoji、营销形容词、强制非正式化、拟人化描述，以及中文互联网口语。

A Codex plugin that makes the agent speak in the manner of a serious scholar: formal, restrained, conceptually ordered, and close to the prose of a university-press textbook or academic monograph. It suppresses slang, sycophancy, filler, emoji, marketing adjectives, forced informality, anthropomorphization, and Chinese internet vernacular.

## 前提条件 / Prerequisites

- Codex CLI with plugin and hook support.
- Git, for cloning or updating this repository.
- POSIX `sh` and `awk`, for the bundled hook. No Python runtime is required.
- Node.js is used only by the optional local verification script.

## 安装 / Installation

Recommended path:

```bash
git clone https://github.com/lulucatdev/codex-be-serious.git ~/plugins/be-serious
```

Create or update the personal marketplace file at `~/.agents/plugins/marketplace.json`. If the file already exists, append only the plugin entry instead of overwriting the file.

```json
{
  "name": "personal",
  "interface": {
    "displayName": "Personal"
  },
  "plugins": [
    {
      "name": "be-serious",
      "source": {
        "source": "local",
        "path": "./plugins/be-serious"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

Install the plugin from the personal marketplace:

```bash
codex plugin add be-serious@personal
```

Start a new Codex thread. Plugin-bundled hooks are not trusted automatically; open `/hooks`, review the Be Serious hook, and trust it before expecting automatic enforcement.

If hooks were explicitly disabled in `~/.codex/config.toml`, re-enable the canonical feature key:

```toml
[features]
hooks = true
```

## 行为 / Behavior

The plugin has two enforcement layers.

1. `SessionStart` hook: `hooks/hooks.json` injects the register constraint on `startup`, `resume`, `clear`, and `compact`. This means the policy is refreshed after automatic context compaction, not only at the beginning of a thread.
2. Active skill: `skills/be-serious/SKILL.md` defines the explicit `be-serious` skill. Invoking `be-serious`, `$be-serious`, or `@be-serious` activates the same scholarly register for the current session, even when the hook was not the trigger.
3. Review skill: `skills/be-serious-review/SKILL.md` audits and rewrites prose against the same register.
4. Examples: `skills/be-serious/examples.md` contains the core imitation corpus. `skills/be-serious/examples-extended.md` contains additional cases for active skill and review use. The hook inserts the core corpus after `SKILL.md` and `style-profile.md`.

The hook command uses `PLUGIN_ROOT`, so it does not depend on the current project directory:

```json
"command": "/bin/sh \"${PLUGIN_ROOT}/hooks/session_start_inject.sh\""
```

The hook script is shell plus `awk`. It reads `skills/be-serious/SKILL.md`, removes YAML frontmatter, appends `skills/be-serious/style-profile.md` and `skills/be-serious/examples.md`, prepends an enforcement preamble, JSON-escapes the result, and writes `hookSpecificOutput.additionalContext` for `SessionStart`.

## 语体约束 / Register Constraint

Required prose:

- serious scholarly voice
- complete declarative sentences
- precise vocabulary
- explicit logical transitions
- no affective performance
- no customer-support friendliness
- no influencer, marketing, or casual coding-assistant persona

Prohibited patterns include:

| Category | Examples |
| --- | --- |
| Slang | `ngl`, `lowkey`, `vibe`, `ship it`, `gonna`, `wanna`, `tbh` |
| Sycophancy | "Great question!", "Happy to help!", "Absolutely!" |
| Enthusiasm markers | emoji, exclamation marks for enthusiasm, "awesome", "amazing" |
| Filler | "Let's go ahead and", "To be honest", "At the end of the day" |
| Anthropomorphization | "the compiler is happy", "the function wants X" |
| Forced informality | opening with "So, ...", casual contractions in expository prose |
| Chinese vernacular | 闭环, 痛点, 砍一刀, 揪出来, 拍板, 稳稳接住, 说人话就是, 一句话总结, 不踩坑, 收口, 狠狠干 |

The constraint applies to natural-language output: explanations, plans, reviews, status updates, commit messages, and PR descriptions. It does not apply to generated code, logs, error messages, or quoted user text.

## 验证 / Verification

Run the hook smoke test:

```bash
/bin/sh tests/check-hook.sh
```

Run the style-contract test:

```bash
/bin/sh tests/check-style-contract.sh
```

Or inspect the hook output directly:

```bash
PLUGIN_ROOT="$PWD" /bin/sh hooks/session_start_inject.sh
```

The output should be valid JSON with `hookSpecificOutput.hookEventName` set to `SessionStart` and `additionalContext` containing the register policy.

## 更新 / Updating

Update the source repository, then reinstall from the same marketplace so Codex refreshes its installed copy:

```bash
cd ~/plugins/be-serious
git pull
codex plugin add be-serious@personal
```

Use a new Codex thread after reinstalling. A new thread is the reliable boundary for picking up revised skills and hook definitions.

## 结构 / Structure

```text
codex-be-serious/
├── .codex-plugin/
│   └── plugin.json
├── hooks/
│   ├── hooks.json
│   └── session_start_inject.sh
├── skills/
│   └── be-serious/
│       ├── agents/
│       │   └── openai.yaml
│       ├── SKILL.md
│       ├── examples.md
│       ├── examples-extended.md
│       └── style-profile.md
│   └── be-serious-review/
│       ├── agents/
│       │   └── openai.yaml
│       └── SKILL.md
├── assets/
│   ├── icon.png
│   └── logo.png
├── tests/
│   ├── check-hook.sh
│   └── test-results-v0.2.0.md
├── README.md
└── LICENSE
```

## 测试记录 / Test Record

The historical model-behavior test log is in `tests/test-results-v0.2.0.md`. Version `0.4.0` adds a style profile, splits core and extended examples, adds the `be-serious-review` skill, and adds deterministic style-contract tests.

## 官方文档 / Official Documentation

- [Codex Hooks](https://developers.openai.com/codex/hooks)
- [Build Codex plugins](https://developers.openai.com/codex/plugins/build)
- [Codex Plugins](https://developers.openai.com/codex/plugins)

## License

MIT
