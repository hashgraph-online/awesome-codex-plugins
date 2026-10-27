# web-hero：tutti.pics 被 Jack 接受的官网引擎（2026-10-24）

不是拿来原样套的模板：先走 `references/web-craft.md` 的 W0（参考 → 拆层 → 技法表 → 风格帧），再从这里拷代码，换掉主角照片、`hero.js` 顶部的 LOOKS 表、`src/strings.json` 的字墙用词。

| 文件 | 干什么 |
|---|---|
| `src/index.html` `src/strings.json` | 页面模板与多语文案；`tools/build.js` 生成各语言页面、404、`_redirects`、子集字体 |
| `public/hero.js` | WebGL 液态字墙、抠图主角、闪光换状态、码页 /c/、只印码海报 /p/、模板页 /t/、404 假故障、今日开场、存图分享 |
| `public/try.js` | 用户自己的照片：MediaPipe Selfie Segmenter 本地抠图 |
| `public/join.js` `functions/` `schema.sql` `wrangler.toml` | 内测名单 + 邀请排位（Cloudflare Pages Functions + D1） |
| `public/shortcode.js` | Tutti 专用的 6 位校验码；别的产品换成自己的分享码或删掉 |
| `tools/og.js` | 截每个状态做 1200×630 分享卡 |

原项目：`~/Desktop/vibecoding/Tutti`（分支 claude/site-launch-d0d98c，`site/`、`docs/site/`）。
