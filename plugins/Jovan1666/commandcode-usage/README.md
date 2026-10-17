# Command Code 额度 —— Codex CLI 插件

每轮对话在 Codex 的 TUI 里显示一行额度，外加一个 `/quota` 命令。

## 安装

```
codex plugin marketplace add Jovan1666/commandcode-usage
codex plugin install commandcode-usage
```

装完 Codex 会提示这个插件的钩子需要**信任**——同意了才会执行。这跟 Claude Code 的钩子
是一回事：钩子能跑任意命令，所以默认不信任。

## 为什么是每轮一行，而不是常驻

**Codex 没有可以塞自定义脚本的常驻状态栏。** `tui.status_line` 是一组封闭的内置项
（`branch` / `cwd` / `context-used` / `five-hour-limit` …），不接受外部命令——配置里写
`{type="command"}` 会被 serde 直接拒掉（`invalid type: map, expected a string`）。

所以这里用 `UserPromptSubmit` 钩子：每次发消息时把额度作为 `systemMessage` 弹出来。

用 `systemMessage` 而不是 `additionalContext` 是刻意的——前者**只显示给用户看，不进模型上下文**，
所以每轮弹一次也不会烧 token。额度本来就是要省着用的，用它自己的额度去查它自己很荒唐。

## 它会自己决定要不要出现

如果你切换到了不是 Command Code 的模型，这一行就不会弹。

判据按可靠性排：

1. **本地路由的环境变量映射**（cc-switch 之类）——最硬
2. **宿主直接给的模型名**。Codex 的钩子把 `model` 作为字符串放在 stdin 里
   （实测 `"gpt-5.6-terra"`），这是 Codex 特有的便利：它不像 Claude Code 那样给一个
   本地别名，给的直接就是真实模型名
3. **账号用量活跃度**——兜底

前两条拿到的模型名会去对照 Command Code 的公开模型目录（`/provider/v1/models`，免鉴权）。
不在目录里就保持沉默。

## 选项

钩子的命令可以带参数（改 `hooks/hooks.json` 里的 `command`）：

| 参数 | 作用 |
|---|---|
| `--threshold 70` | 只在某个窗口超过 70% 时才弹，平时完全安静 |
| `--model <子串>` | 手工指定「哪些模型名算在用」，可重复 |
| `--always` | 不做判定，每轮都弹 |
| `--why` | 解释「为什么现在没显示」，输出到 stderr |

## 已知边界

- **每次都要经过钩子**：Codex 的钩子是同步执行的，脚本约 90ms（命中快照）+ 进程启动。
- **`transcript_path` 是空的**：Codex 会带上这个字段但不填值，所以走不了「读会话记录」
  那条判据——这就是为什么要专门认 `model` 字符串。
- **`codex exec` 会读 stdin**：非交互调用时如果 stdin 不关会一直挂着（`Reading additional
  input from stdin...`）。脚本里跑测试记得 `< /dev/null`。

MIT 许可——见仓库根的 [LICENSE](../../LICENSE)。
