---

name: ui-designer/html-prototype
description: 可交互 HTML 原型，生成浏览器可打开的原型页面供用户查看和选择设计方案
version: 1.0.0
agent: ui-designer
type: workflow
user-invocable: false
agent-invocable: true
dependencies:
- ui-designer/design-system
  triggers:
- 用户需要直观看到设计效果而非纯文字描述时
- 存在多个设计变体需要用户对比选择时
- 设计方向存在分歧，需要可视化决策时
  metadata:
  internal: true

---

# 可交互 HTML 原型

## 适用场景

当设计方案需要用户**直观看到**才能决策时，生成可交互的 HTML 原型页面，在浏览器中展示并让用户点击选择。

**适用**：
- 多设计变体需要用户对比选择
- 布局/视觉方向需要用户确认
- 复杂交互流程需要走查

**不适用**：
- 纯后端/API 项目
- 用户已明确指定设计方向
- 简单页面无需可视化确认

## 核心流程

```
1. 征求同意 → 2. 生成原型 HTML → 3. 启动本地服务 → 4. 用户查看/选择 → 5. 读取选择 → 6. 清理
```

### 步骤 1：征求同意

在开始设计前，**单独发一条消息**询问用户：

> 接下来的设计方案如果能在浏览器里直观看到，会比纯文字描述更容易决策。我可以生成可交互的 HTML 原型页面，你打开本地链接就能看到效果并点击选择方案。需要开启吗？

**这条消息必须独立发送**，不要和其他内容混在一起。等待用户回复。
- 用户同意 → 继续步骤 2
- 用户拒绝 → 跳过 HTML 原型，用文字描述 + JSON 交付

### 步骤 2：生成原型 HTML

在 `.boss/<feature>/prototype/` 目录下生成原型文件。

**文件结构**：
```
.boss/<feature>/prototype/
├── index.html          # 主页面：展示所有变体，可点击选择
├── server.cjs          # 本地服务脚本（由 Agent 写入）
└── selections.json     # 用户选择记录（服务运行时生成）
```

#### 2.1 写入服务脚本

将以下代码**原样写入** `.boss/<feature>/prototype/server.cjs`：

```javascript
const http = require('http');
const fs = require('fs');
const path = require('path');

const DIR = __dirname;
const PORT = process.env.PROTO_PORT || 0;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
};

let selections = [];
const selFile = path.join(DIR, 'selections.json');
try {
  selections = JSON.parse(fs.readFileSync(selFile, 'utf-8'));
} catch (e) {}

function saveSelections() {
  fs.writeFileSync(selFile, JSON.stringify(selections, null, 2));
}

const clients = new Set();

const server = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/select') {
    let body = '';
    req.on('data', (c) => (body += c));
    req.on('end', () => {
      try {
        const sel = JSON.parse(body);
        sel.timestamp = Date.now();
        selections.push(sel);
        saveSelections();
        for (const c of clients) {
          try {
            c.write(`data: ${JSON.stringify(sel)}\n\n`);
          } catch (e) {}
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
      } catch (e) {
        res.writeHead(400);
        res.end('Bad request');
      }
    });
    return;
  }

  if (req.url === '/selections') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(selections));
    return;
  }

  if (req.url === '/events') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    });
    clients.add(res);
    req.on('close', () => clients.delete(res));
    return;
  }

  let relPath = req.url === '/' ? '/index.html' : req.url.split('?')[0];
  let filePath = path.join(DIR, relPath);
  if (!filePath.startsWith(DIR)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }
  if (!fs.existsSync(filePath)) {
    res.writeHead(404);
    res.end('Not found');
    return;
  }
  const ext = path.extname(filePath).toLowerCase();
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
  res.end(fs.readFileSync(filePath));
});

server.listen(PORT, '127.0.0.1', () => {
  const port = server.address().port;
  console.log(JSON.stringify({ url: `http://localhost:${port}`, port }));
});
```

#### 2.2 写入原型页面

写 `index.html`，使用以下骨架。**所有 CSS 内联**，不依赖外部资源。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>设计原型 · <feature></title>
<style>
  :root {
    --bg: #f8fafc;
    --card: #ffffff;
    --border: #e2e8f0;
    --text: #0f172a;
    --muted: #64748b;
    --primary: #3b82f6;
    --primary-hover: #2563eb;
    --success: #10b981;
    --radius: 12px;
    --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); padding: 2rem 1rem; }
  .container { max-width: 1200px; margin: 0 auto; }
  .header { text-align: center; margin-bottom: 2rem; }
  .header h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
  .header p { color: var(--muted); font-size: 0.95rem; }
  .variants { display: grid; gap: 1.5rem; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
  .variant {
    background: var(--card); border: 2px solid var(--border); border-radius: var(--radius);
    overflow: hidden; box-shadow: var(--shadow); transition: all 0.2s ease; cursor: pointer;
    display: flex; flex-direction: column;
  }
  .variant:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); border-color: var(--primary); }
  .variant.selected { border-color: var(--success); box-shadow: 0 0 0 3px rgba(16,185,129,0.2); }
  .variant-preview {
    background: #f1f5f9; padding: 1.5rem; min-height: 200px;
    display: flex; align-items: center; justify-content: center;
  }
  .variant-body { padding: 1rem 1.25rem; flex: 1; display: flex; flex-direction: column; }
  .variant-body h3 { font-size: 1.1rem; margin-bottom: 0.5rem; }
  .variant-body .concept { color: var(--muted); font-size: 0.9rem; margin-bottom: 0.75rem; }
  .variant-body .tradeoffs { font-size: 0.85rem; margin-bottom: 1rem; }
  .variant-body .tradeoffs .pros { color: #059669; }
  .variant-body .tradeoffs .cons { color: #dc2626; }
  .select-btn {
    margin-top: auto; padding: 0.6rem 1rem; background: var(--primary); color: #fff;
    border: none; border-radius: 8px; font-size: 0.9rem; font-weight: 500; cursor: pointer;
    transition: background 0.15s;
  }
  .select-btn:hover { background: var(--primary-hover); }
  .variant.selected .select-btn { background: var(--success); }
  .badge {
    display: inline-block; padding: 0.15rem 0.5rem; background: #e0e7ff; color: #4338ca;
    border-radius: 999px; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.5rem;
  }
  .badge.recommended { background: #d1fae5; color: #065f46; }
  /* 原型内部样式 */
  .mockup { width: 100%; }
  .mock-nav { display: flex; gap: 1rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); font-size: 0.8rem; color: var(--muted); }
  .mock-card { background: #fff; border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; margin: 0.5rem 0; }
  .mock-btn { display: inline-block; padding: 0.4rem 0.8rem; background: var(--primary); color: #fff; border-radius: 6px; font-size: 0.8rem; }
  .mock-input { width: 100%; padding: 0.4rem 0.6rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.8rem; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>设计原型 · <feature></h1>
    <p>请查看以下设计方案，点击「选择此方案」确认你的选择</p>
  </div>
  <div class="variants" id="variants">
    <!-- 变体卡片由 Agent 填充 -->
  </div>
</div>
<script>
const es = new EventSource('/events');
es.onmessage = (e) => {
  const sel = JSON.parse(e.data);
  document.querySelectorAll('.variant').forEach(v => v.classList.remove('selected'));
  const card = document.querySelector(`[data-choice="${sel.choice}"]`);
  if (card) card.classList.add('selected');
};
function select(choice, name) {
  fetch('/select', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ choice, name }),
  });
}
</script>
</body>
</html>
```

#### 2.3 变体卡片模板

在 `#variants` 容器内，为每个方案插入一张卡片：

```html
<div class="variant" data-choice="A" onclick="select('A', '方案A: 简约单栏')">
  <div class="variant-preview">
    <!-- 用 mock-* 类绘制线框图，展示布局结构 -->
    <div class="mockup">
      <div class="mock-nav">Logo · 首页 · 关于</div>
      <div class="mock-card"><strong>标题</strong><br><span style="color:var(--muted);font-size:0.8rem">描述文字</span></div>
      <div class="mock-btn">主要操作</div>
    </div>
  </div>
  <div class="variant-body">
    <span class="badge recommended">推荐</span>
    <h3>方案 A：简约单栏</h3>
    <p class="concept">聚焦内容，减少视觉干扰</p>
    <div class="tradeoffs">
      <div class="pros">✓ 阅读体验好<br>✓ 开发成本低</div>
      <div class="cons">✗ 信息密度低</div>
    </div>
    <button class="select-btn" onclick="event.stopPropagation();select('A','方案A: 简约单栏')">选择此方案</button>
  </div>
</div>
```

**线框图绘制原则**：
- 用 `.mock-nav`、`.mock-card`、`.mock-btn`、`.mock-input` 等类搭建布局
- 重点展示**结构和层次**，不需要像素级还原
- 每个变体的预览要能体现出设计差异（布局、密度、导航方式等）
- 用真实文案而非 Lorem ipsum

### 步骤 3：启动本地服务

用 `Bash` 启动服务，端口由系统分配：

```bash
cd .boss/<feature>/prototype && node server.cjs
```

服务启动后会输出一行 JSON：`{"url":"http://localhost:PORT","port":PORT}`。

**必须使用 `run_in_background: true`**，让服务在后台持续运行。

启动后解析输出中的 `url` 字段。

### 步骤 4：引导用户查看

向用户发送：

> 原型已生成，请在浏览器打开：`http://localhost:PORT`
>
> 页面上展示了 N 个设计方案，点击卡片或「选择此方案」按钮即可确认。选好后告诉我即可。

### 步骤 5：读取用户选择

用户回复后，读取 `.boss/<feature>/prototype/selections.json`：

```json
[{ "choice": "A", "name": "方案A: 简约单栏", "timestamp": 1706000101000 }]
```

- 取最后一条记录的 `choice` 作为用户选择
- 如果文件不存在或为空，说明用户未在浏览器操作，以用户文字回复为准

### 步骤 6：清理

设计确认后，停止服务：

```bash
# 查找并停止 server.cjs 进程
pkill -f "server.cjs" 2>/dev/null || true
```

原型文件保留在 `.boss/<feature>/prototype/` 供后续参考。

## 单原型确认模式

如果只有一个设计方案需要用户确认（而非多方案选择），页面结构简化：

```html
<div class="container">
  <div class="header">
    <h1>设计原型 · <feature></h1>
    <p>请确认以下设计方案是否符合预期</p>
  </div>
  <div class="variant" style="max-width:600px;margin:0 auto;cursor:default;">
    <div class="variant-preview"><!-- 线框图 --></div>
    <div class="variant-body">
      <h3>设计方案</h3>
      <p class="concept">设计理念说明</p>
      <button class="select-btn" onclick="select('confirm','确认方案')">确认此方案</button>
    </div>
  </div>
</div>
```

## 注意事项

1. **征得同意后再生成**：不要擅自启动服务或生成 HTML
2. **CSS 全部内联**：不依赖 CDN 或外部样式表，确保离线可用
3. **端口随机**：不要硬编码端口，用 `PORT=0` 让系统分配
4. **后台运行**：服务必须 `run_in_background: true`，否则会阻塞
5. **读取选择后再继续**：必须确认用户选择后才能进入下一步设计
6. **保留原型文件**：`prototype/` 目录作为设计产物保留，不删除
