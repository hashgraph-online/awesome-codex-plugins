# SECURITY

- **零网络请求**:所有代码只读写本地 `~/.claude/tigang-reminder/` 下的
  `stats.json` / `pending.json`(可用 `TIGANG_STATE_DIR` 重定向),不发出任何 HTTP 请求,
  不读取环境中的秘钥,不收集任何数据。
- **零依赖**:核心与全部适配器只依赖 node 内置模块,无供应链面。
- **不阻塞、不注入**:hook 任何异常都静默 exit 0;检测阶段零 stdout,
  不会向模型上下文注入任何内容。
- **外部配置**。Codex 原生安装由其 marketplace 管理。手工配置 Codex 或 dsh 时，
  参见 [安装说明](INSTALL.md)。

发现安全问题时，请联系仓库维护者。如果需要开公开 Issue，请先请求私下沟通。
