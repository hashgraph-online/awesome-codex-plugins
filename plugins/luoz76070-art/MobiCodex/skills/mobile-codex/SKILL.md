---
name: mobile-codex
description: 管理 Mobile Codex 本地网关、手机配对和设备撤销；用于连接手机、查看网关状态或迁移旧 Relay，不用于发送模型任务。
---

使用本插件自带的 CLI，命令为 `node "<当前 SKILL.md 所在目录>/scripts/mobile-codex.mjs" <命令>`（插件根目录的 `scripts/mobile-codex.mjs` 是同一个入口）。需要 Node.js 20 或更高版本。若当前 SKILL.md 所在目录下没有 `lib/gateway.mjs`，这是未构建的源码目录，先在工程根目录执行 `corepack pnpm build:plugin`，使用 dist-plugin/mobile-codex 下的完整插件。

加载技能不启动服务。根据用户要求调用命令；所有结果为 JSON，失败以非零退出。必要选择直接在聊天正文用编号表达，手机未必能显示宿主选择面板。

- `status`：只读被动状态；不连接 Codex 或运行模型。优先核对现有状态。
- `init --workspace <项目绝对路径> [--codex-home <路径>] [--port <端口>] [--import-legacy <旧配置文件>]`：创建独立配置，默认路径为 macOS 的 `~/Library/Application Support/Mobile Codex Gateway/gateway.json`。workspace 决定设备哈希和上传目录，迁移时沿用旧工程路径。已有配置不会覆盖。显式导入旧配置才复用旧token、端口和公网隧道；不在聊天中输出配置内容或凭证。
- `start`：一个后台进程同时承担Relay和Tunnel；端口被旧Relay/未知进程占用时停止本次操作并报告，不自动杀进程或卸载App。用户已要求启动/迁移时按已授权范围执行。
- `pair`：公网隧道连接后生成 `{endpoint,code,expiresAt}`，用户复制到手机“设置 → 连接电脑”。仅此短效配对信息可展示；不要展示管理员token/管理密钥。五分钟一次性，断线结果未知时不重放，核对设备后由用户明确再次生成。
- `devices` / `revoke --device <UUID>`：列出或撤销设备；撤销会立即使该设备失去连接，按用户指定设备操作。
- `stop`：仅停止当前管理的实例，不按PID杀进程。用户要求停止时执行。
- `service status`：macOS用户级托管的只读注册/加载状态，和网关普通status的running/tunnel分开判断。未知状态不能当未安装。
- `service install`：仅在用户明确要求开机自启或异常退出恢复时启用；先核对普通status并安排停止同配置旧进程，旧Relay登录项冲突不得擅自卸载。固定复制bundle、保留原配置/设备，再安装LaunchAgent；需要普通macOS登录会话，不使用sudo。普通start不能被扩大为安装登录项的授权。
- `service uninstall`：用户要求卸载后台托管时执行；只移除自己的job/receipt/plist，配置与设备继续保留。正常stop会保持停止，再start复用已注册托管。更新托管程序或Node路径时显式卸载后重新安装；插件更新不会替换已固定运行程序。

全部命令支持 `--config <绝对路径>`。新建无公网配置时，用户在本地私有配置文件填写 tunnel 的 brokerUrl/relayId/relaySecret；公网必须TLS，不通过命令行参数、聊天或日志收集密钥。完整配置和迁移说明见插件根目录 README.md。

管理网关不等于同会话控制已验收。当前managed模式使用native，不需要Swift输入helper；真实Desktop应答/发送/中断/审批仍需单独验证。不能创建新CLI会话代替原会话验收，不自动修改Codex安装目录、辅助功能权限或生产服务。自启动只按用户明确的托管要求启用，安装插件本身不注册；真实登录/崩溃恢复仍须单独验收。
