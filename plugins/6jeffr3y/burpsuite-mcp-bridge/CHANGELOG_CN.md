# 更新日志

## 1.1.0

### 重点更新
- 新增目标视角流量画像：`burp_target_overview`。
- 新增分级 MCP 帮助：`burp_mcp_list`。
- 改写规则动作真正落地：`modify`、`drop`、`spoof`。
- 规则作用面支持：`proxy`、`tool`、`all`。
- 接入 Burp 2026.4.x 运行时检测能力：
  - command palette / HotKey selection 捕获
  - 可用时使用官方 internal-tool request drop/spoof
  - BCheck 导入
  - Bambda 导入
- 增强 Burp UI：自检、命令复制、规则 UX。
- 简化配置：示例直接启动 `wsl-mcp/server.py` 并设置 `BURP_MCP_BRIDGE_URL`；release 包移除 wrapper 脚本。

### 稳定性 / 兼容性
- 编译基线保持 `montoya-api 2025.10`。
- 2026.4.x 可选能力运行时检测。
- JSON 详情接口继续使用 preview-first body；完整原始证据通过 bundle 文件导出。

### 测试基线
- Burp Suite Professional 2026.4.2

## 1.0.0

### 重点更新
- 初始发布，支持 Windows Burp ↔ WSL Codex / Agent AI / MCP CLI / IDE 通信。
- 支持 Burp Proxy 流量与 logger-like 内部工具流量读取。
- 支持重放、改写规则、Repeater 联动和原始包导出。
