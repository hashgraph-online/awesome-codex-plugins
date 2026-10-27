// node tools/og.js [base] —— 截每张模板海报做分享卡（1200×630），写到 public/assets/og/。需要本地先跑 npm run dev。
// puppeteer 借用 tutti-applemg/tools 里装好的那份，用系统 Chrome。
const path = require('path'), fs = require('fs');
const puppeteer = require(process.env.HOME + '/Desktop/vibecoding/tutti-applemg/tools/node_modules/puppeteer');
const base = process.argv[2] || 'http://localhost:8788';
const LANGS = { 'zh-hans': '/', 'zh-hant': '/zh-hant/', ja: '/ja/', ko: '/ko/', vi: '/vi/', en: '/en/' };
const SLUGS = ['cover-star', 'star-punch', 'only-me-color', 'white-outline', 'red-special', 'mirrored-sparkles'];
const out = path.join(__dirname, '..', 'public/assets/og');
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await puppeteer.launch({ headless: 'new', executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
  const p = await b.newPage();
  await p.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });
  await p.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  await p.evaluateOnNewDocument(() => { try { localStorage.setItem('tutti_lang', 'pinned'); } catch (e) {} }); // 不让根路径按浏览器语言跳走
  for (const [lang, lp] of Object.entries(LANGS)) {
    fs.mkdirSync(path.join(out, lang), { recursive: true });
    for (const [i, slug] of SLUGS.entries()) {
      await p.goto(`${base}${lp}?og=${i}`, { waitUntil: 'networkidle0' });
      await new Promise(r => setTimeout(r, 900));
      const f = path.join(out, lang, `${slug}.jpg`);
      await p.screenshot({ path: f, type: 'jpeg', quality: 80 });
      if (i === 0) fs.copyFileSync(f, path.join(out, lang, 'home.jpg'));
    }
  }
  await b.close();
  console.log('og', Object.keys(LANGS).length * (SLUGS.length + 1), 'images →', out);
})();
