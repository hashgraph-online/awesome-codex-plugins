# Mobbin Skills

A collection of skills for designing and building UI with [Mobbin](https://mobbin.com), the industry standard in UI &amp; UX design references for mobile apps, web apps, and websites

## Installing

Use the native plugin where supported to install both the Mobbin skills and the Mobbin MCP server. Agents that only support the Agent Skills standard can install the skills separately.

On first use your agent opens a browser to sign in to Mobbin. You need a Pro, Team, or Enterprise plan.

### Codex

```sh
codex plugin marketplace add mobbin/skills
codex plugin add mobbin@mobbin
```

### Claude Code

```sh
claude plugin marketplace add mobbin/skills
claude plugin install mobbin@mobbin
```

Or from inside a Claude Code session:

```
/plugin marketplace add mobbin/skills
/plugin install mobbin@mobbin
```

### Antigravity CLI

```sh
agy plugin install https://github.com/mobbin/skills
```

### Kimi Code CLI

```
/plugins install https://github.com/mobbin/skills
```

Run `/reload` afterwards to apply the plugin.

### Gemini CLI

```sh
gemini extensions install https://github.com/mobbin/skills
```

Then run `/mcp auth mobbin` inside Gemini CLI to sign in.

### npx skills

Install using the [`npx skills`](https://skills.sh) CLI:

```
npx skills add mobbin/skills
```

This installs only the skills. Add the MCP server to your agent's MCP config yourself:

```json
{
  "mcpServers": {
    "mobbin": {
      "url": "https://api.mobbin.com/mcp"
    }
  }
}
```

## Skills

Skills are contextual and auto-loaded based on your conversation. When a request matches a skill's triggers, the agent loads and applies the relevant skill.


| Skill           | Useful for                                                                                                                                                                                                                            |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| best-practices  | What Mobbin and the Mobbin MCP can and can't do, and how to use the Mobbin skills together. Read first when the user asks about Mobbin or starts a design task Mobbin could help with                                                 |
| search          | Searching Mobbin well: choosing between screens, flows and sections, picking the mode, writing a query, pulling more results, and recovering when a search falls short                                                                |
| redesign-screen | Redesigning, improving, restyling or rebuilding a screen, section or component from a screenshot, code or a design file, grounded in how real apps on Mobbin handle the same screen or in the screens you saved to Mobbin collections |
| plain-writing   | Writing rules for the text a Mobbin skill hands to a person, such as a redesign report. Loaded by other Mobbin skills, not meant for writing outside them                                                                             |

---

[Terms of Service](https://mobbin.com/terms) · [Privacy Policy](https://mobbin.com/privacy) · [Help Center](https://help.mobbin.com)
