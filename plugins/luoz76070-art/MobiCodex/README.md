# Mobile Codex 插件（开发预览）

插件提供网关管理技能；不向 Codex 安装目录注入代码，不加载常驻 MCP，不在加载时启动进程。需要本地执行环境、Node.js >=20、正在运行的 Codex Desktop，以及与手机版兼容的 Broker。

在源码工程执行 `corepack pnpm build:plugin`，生成可移走的 `dist-plugin/mobile-codex/`。包内含自包含 Node bundle，不需要 pnpm、工程源码或 node_modules。CLI 和网关放在技能目录里（`skills/mobile-codex/scripts/mobile-codex.mjs`、`skills/mobile-codex/lib/gateway.mjs`），插件根目录的 `scripts/mobile-codex.mjs` 是同一个入口，所以只复制 `skills/` 的插件目录站（例如 awesome-codex-plugins）装上也能直接运行。构建还会从 `plugin.json` 换算出 Codex 读取的 `.codex-plugin/plugin.json`。每次正式发版，构建好的插件会推到仓库的 `codex-plugin` 分支，那个分支只有一个提交，内容就是这个目录。构建同时生成 `dist-plugin/.agents/plugins/marketplace.json`；该marketplace的根目录是 dist-plugin，插件路径为 `./mobile-codex`。按官方本地 marketplace 流程执行 `codex plugin marketplace add <dist-plugin绝对路径>`，再重启桌面客户端，在插件目录中安装 Mobile Codex。不要用临时CLI新会话替代Desktop原会话控制验收。

插件manifest声明`extensions.com.openai.requires_local_executor=true`，因为管理命令需要在运行网关的电脑执行。当前捆绑Codex CLI有plugin管理命令，没有plugin validate；已核对包元数据、技能入口与独立CLI，尚未在用户Codex配置中实际安装。

隐私说明见 [PRIVACY.md](PRIVACY.md)：没有遥测；数据只发往你配置的 Broker、本机 Agent，以及你自己填了密钥的语音服务。

## 初始化与迁移

用 `node <插件目录>/scripts/mobile-codex.mjs help` 查看命令（只含技能目录的插件包里用 `<插件目录>/skills/mobile-codex/scripts/mobile-codex.mjs`，两者相同）。所有命令支持 `--config <文件绝对路径>`。先运行status；首次初始化必须指定workspace绝对路径。macOS配置默认在 `~/Library/Application Support/Mobile Codex Gateway/gateway.json`，权限0600。

```sh
node <插件目录>/scripts/mobile-codex.mjs init --workspace <原工程绝对路径> --import-legacy <旧Relay配置绝对路径>
node <插件目录>/scripts/mobile-codex.mjs status
node <插件目录>/scripts/mobile-codex.mjs start
node <插件目录>/scripts/mobile-codex.mjs pair
```

旧配置一般位于 `~/Library/Application Support/Mobile Codex Relay/config.json`。导入只读旧文件，保留旧token、端口、Broker参数；workspace必须沿用原目录，设备凭证仍在该目录的 `.mobile-codex/devices.json`，不会因插件缓存路径变化而丢失。新网关仅监听127.0.0.1，远程经主动Tunnel。原App占用同一端口时start会报告冲突，需要按迁移安排先停旧服务；不会自动停App、改权限、改签名或注册自启动。

没有旧配置可省略import选项，在本地私有文件补充：

```json
{
  "tunnel": {
    "brokerUrl": "https://broker.example.com",
    "relayId": "my-mac",
    "relaySecret": "<至少32字符的Broker密钥>"
  }
}
```

将tunnel字段合并进init生成的配置，保留其他字段。publicEndpoint可选，用于显式指定代理后的手机入口；默认由Broker地址生成 `/r/<relayId>`。配置中不接受公网明文地址或带query/用户信息的URL。不要在聊天、命令参数或日志中传递密钥。

## 日常操作

`status`仅查看被动网关状态；`pair`在公网Tunnel连接后生成五分钟一次性配对JSON，粘贴到手机设置。`devices`列出设备，`revoke --device <UUID>`立即撤销。`stop`通过管理员凭证、单独管理密钥和实例ID停止自己持有的网关；没有按PID杀进程或凭空回收锁文件。

后台是一个Node进程，Relay端口绑定成功后才连接Broker；并发start最多一个实例。日志只记录稳定错误码，启动时超过1MiB轮换一份；凭证不写日志。status、插件加载、配对不会启动模型。Tunnel复用既有ping/pong、退避和取消，不自动重放写入。

managed模式使用native原生通道，不打包Swift输入helper。默认start创建普通后台进程；需要登录启动与异常恢复时，可显式启用下面的macOS用户级托管。原会话控制、Android、休眠恢复和长期运行仍须实测；关机/休眠期间不能即时控制。

## 可选macOS后台托管（0.2.0）

插件可为已登录的普通Mac用户安装LaunchAgent。启用前先安排停止同配置下正在运行的普通网关；旧Relay App的登录项仍存在时会报冲突，需要单独处理旧登录项。源码开发和安装插件本身都不会启用托管。

```sh
node <插件目录>/scripts/mobile-codex.mjs stop
node <插件目录>/scripts/mobile-codex.mjs service install
node <插件目录>/scripts/mobile-codex.mjs service status
```

配置不在默认位置时，每条命令都加相同的`--config <绝对路径>`。install会固定复制一份独立bundle到`~/Library/Application Support/Mobile Codex Gateway/service/gateway-<sha256>.mjs`，在私有registration.json保存路径/SHA记录，再写`~/Library/LaunchAgents/local.mobile-codex.gateway.plist`并加载。没有复制Token或设备文件，plist/receipt权限0600；插件缓存更新或删除不影响这份固定程序。Node仍使用安装时的绝对路径，需长期保留可执行的Node；更换Node或升级托管程序时先卸载，再使用新插件/Node重新安装。

策略是登录时运行、异常非零退出恢复、正常stop后保持停止，启动频率由15秒ThrottleInterval节流。日常继续用原`start/status/stop`：已托管的start调用launchd，不另外创建detached进程；stop仍按管理员密钥和instanceId停止本工具的网关。`service status`只表明是否已安装/被launchd加载；普通`status`的running和tunnel状态才能证明网关及公网连接情况。

```sh
node <插件目录>/scripts/mobile-codex.mjs stop
node <插件目录>/scripts/mobile-codex.mjs start
node <插件目录>/scripts/mobile-codex.mjs service uninstall
```

uninstall停止并移除自己的LaunchAgent和receipt，保留配置、设备、附件与固定程序以便恢复。已有另一配置注册或文件内容不匹配时不会接管。launchctl超时/未知失败会保留注册记录，先查看service status再处理；激活后的本地网关未就绪会明确返回`GATEWAY_SERVICE_NOT_READY`。托管进程标准输出/错误丢弃，避免无限日志；可在Mac本地用`launchctl print gui/$(id -u)/local.mobile-codex.gateway`查看退出状态，需要前台诊断时先卸载托管，再执行固定bundle的`daemon --config <路径>`，错误仍仅输出稳定码。不能把print失败或loaded=true分别当作服务未安装或公网已连接。

本版本只完成合成launchctl、独立临时profile/真实Node网关与只读plutil检查，未在用户系统注册服务；真实登录、异常重启、休眠唤醒和Android联测仍待验收。

## 可选 OpenCode 接入

在私有`gateway.json`里合并以下字段，保留原有配置；服务必须已由用户启动。固定支持OpenCode v2.0.16的`/api/`协议，列表/历史与新SSE先核验`/api/info`版本，未核验版本明确拒绝，不回退旧版路由。

```json
{
  "opencode": {
    "url": "http://127.0.0.1:4096",
    "directory": "/absolute/project",
    "username": "opencode",
    "password": "<已配置的本机服务密码>"
  }
}
```

url只接受`http://127.0.0.1:<port>`或`http://[::1]:<port>`根地址，不接受`localhost`、额外路径、query或URL内凭证。directory必须为绝对路径；username默认opencode，没有启用Basic Auth时省略password。密码只保存在权限0600的本地配置，切勿提交到仓库或发到聊天。普通Relay入口也支持`MOBILE_CODEX_OPENCODE_URL`、`DIRECTORY`、`USERNAME`和`PASSWORD`四个同前缀环境变量。

配置更改在下一次手动启动网关时生效。手机顶栏“切换Agent”选择OpenCode，再打开该目录中的现有会话。网关不会启动OpenCode，也不会新建或恢复模型会话；会话列表/历史/正文流、发送/追加/排队/中断、问题/审批已完成隔离验证，真实服务和Android仍待验收。暂未提供CLI修改该配置的命令。

普通question工具的string/multiselect表单支持手机选择和文字回答，按原字段key与option.value回复。隐藏/条件/数值/外部认证等尚未适配的复杂表单会显示需电脑处理；不能把所有表单都视为普通选择题。中断返回interrupted=false为明确空闲no-op，true仍等待任务状态确认。

## 可选 Claude Code 接入

同一网关还支持 [Claude Code 原会话桥接预览](../mobile-claude/README.md)。该插件需要宿主支持所用 Mods 契约并在原进程加载；已实现最近文本、实时状态、排队输入、原任务中断，以及已识别的原请求问答和单次工具审批，源码与合成验收通过。本机 CLI 2.1.220 低于Mods宿主下限 2.1.287（固定API声明生成于2.1.277），尚未升级、安装或通过真实宿主验收；原生取消/两端先答及Android仍待核验，不能把独立包可构建当作可直接迁移生产的证明。

## 可选：手机反馈直接提交成 GitHub issue

默认情况下，手机上「反馈问题」的内容只存到网关数据目录里的 `feedback/`，不会离开这台电脑。在 `gateway.json` 里加上 `feedback.github`，手机反馈面板就会多一个「提交到」选项（手机端也要升级到带这个功能的版本）：

```json
"feedback": {
  "github": {
    "repos": [{ "id": "mobicodex", "repo": "luoz76070-art/MobiCodex", "label": "MobiCodex", "public": true }],
    "gh": "/opt/homebrew/bin/gh"
  }
}
```

- `repos`：手机上能选的仓库，最多 10 个。`id` 只用小写字母、数字和连字符；`label` 是手机上显示的名字；`public` 为 `true` 时，预览会提醒“将公开发布”。
- `gh`（可选）：GitHub CLI 的绝对路径。网关在后台运行时可能拿不到登录 shell 的 PATH，建议写上。这台电脑要先 `gh auth login`，账号要能在这些仓库里建 issue 和标签。
- `proxy`（可选）：这台电脑要经代理才能连 GitHub 时填，例如 `"http://127.0.0.1:端口"`，只对 gh 生效。

手机上选好仓库后要先点「预览」：网关生成标题和正文，隐藏本机路径、用户名、电脑名、邮箱、网址、IP 地址、密钥，以及网关自己的令牌和服务器地址；确认后才提交。网关用 gh 建 issue，加 `from-phone` 标签，正文末尾有一行看不见的编号，重试前先按编号查，不会重复建。提交失败每 10 分钟重试一次，手机上「我的反馈」会显示原因；收件箱里人工改过状态的反馈，网关不再动。反馈不带截图。

改完配置，重启网关后生效。

