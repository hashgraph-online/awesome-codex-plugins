// node tools/build.js —— 从 src/index.html + src/strings.json 生成六语页面、404、_redirects，并把字体按每种语言实际用到的字子集化成 woff2。
// 需要 pyftsubset（fontTools + brotli）。大字体原文件在 fonts-src/（不进 git，缺了会提示下载地址）。
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const ROOT = path.join(__dirname, '..'), PUB = path.join(ROOT, 'public'), APP_FONTS = path.join(ROOT, '..', 'Tutti', 'Fonts');
const tpl = fs.readFileSync(path.join(ROOT, 'src/index.html'), 'utf8');
const all = JSON.parse(fs.readFileSync(path.join(ROOT, 'src/strings.json'), 'utf8'));
const LANGS = Object.keys(all).filter(k => !k.startsWith('_'));
const NAMES = { 'zh-Hans': '简体', 'zh-Hant': '繁體', ja: '日本語', ko: '한국어', vi: 'Tiếng Việt', en: 'English' };
const FONTS = {
  marker: path.join(APP_FONTS, 'LXGWMarkerGothic-Regular.ttf'),
  shantell: path.join(APP_FONTS, 'ShantellDoodle-Bold.ttf'),
  wenkai: path.join(ROOT, 'fonts-src/LXGWWenKaiTC-Bold.ttf'),     // https://github.com/google/fonts/raw/main/ofl/lxgwwenkaitc/LXGWWenKaiTC-Bold.ttf
  hansans: path.join(ROOT, 'fonts-src/BlackHanSans-Regular.ttf'), // https://github.com/google/fonts/raw/main/ofl/blackhansans/BlackHanSans-Regular.ttf
};
const ASCII = Array.from({ length: 95 }, (_, i) => String.fromCharCode(32 + i)).join('') + '·→…＋×#?？！。，、「」';
const SITE = 'https://tutti.pics';

function subset(src, text, out) {
  if (!fs.existsSync(src)) throw new Error(`缺字体 ${src}（见 build.js 顶部的下载地址）`);
  const tmp = path.join(ROOT, '.subset.txt');
  fs.writeFileSync(tmp, [...new Set(text)].join(''));
  execFileSync('pyftsubset', [src, `--text-file=${tmp}`, '--flavor=woff2', `--output-file=${out}`, '--layout-features=*', '--no-hinting']);
  fs.unlinkSync(tmp);
  return fs.statSync(out).size;
}
const esc = s => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
const strings = L => Object.values(all[L]).flat(2).filter(v => typeof v === 'string').join('');

fs.mkdirSync(path.join(PUB, 'assets/fonts'), { recursive: true });
const sizes = {};
sizes.logo = subset(FONTS.shantell, 'tutti' + ASCII, path.join(PUB, 'assets/fonts/logo.woff2'));

const alternates = LANGS.map(L => `<link rel="alternate" hreflang="${all[L].hreflang}" href="${SITE}${all[L].path}">`).join('\n')
  + `\n<link rel="alternate" hreflang="x-default" href="${SITE}/">`;
const langlinks = LANGS.map(L => `<a href="${all[L].path}" onclick="try{localStorage.setItem('tutti_lang','${L}')}catch(e){}">${NAMES[L]}</a>`).join(' · ');
// 只在根路径的首页、码页、海报页按浏览器语言跳一次；选过语言就不再跳
const MAP = { 'zh-tw': 'zh-Hant', 'zh-hk': 'zh-Hant', 'zh-mo': 'zh-Hant', 'zh-hant': 'zh-Hant', zh: 'zh-Hans', ja: 'ja', ko: 'ko', vi: 'vi', en: 'en' };
const PATHS = Object.fromEntries(LANGS.map(L => [L, all[L].path]));
const redirect = `<script>(function(){try{if(localStorage.getItem('tutti_lang'))return}catch(e){}var p=location.pathname;if(!(p==='/'||/^\\/(c|p)\\//.test(p)))return;
var M=${JSON.stringify(MAP)},P=${JSON.stringify(PATHS)};var ls=navigator.languages||[navigator.language||''];
for(var i=0;i<ls.length;i++){var l=(ls[i]||'').toLowerCase(),k=M[l]||M[l.split('-')[0]];if(k){if(k!=='zh-Hans')location.replace(P[k]+p.slice(1)+location.search+location.hash);return}}})();</script>`;

const redirects = [];
for (const L of LANGS) {
  const S = all[L];
  const fontFile = `brand-${L.toLowerCase()}.woff2`;
  sizes[L] = subset(FONTS[S.font], strings(L) + ASCII, path.join(PUB, 'assets/fonts', fontFile));
  const vars = {
    ...Object.fromEntries(Object.entries(S).map(([k, v]) => [k, typeof v === 'string' ? (k === 'sheet_h2' ? v : esc(v)) : v])),
    slogan: esc(S.title.replace(/^Tutti · /, '')),
    fonturl: `/assets/fonts/${fontFile}`, alternates, langlinks,
    i18n: JSON.stringify(S).replace(/</g, '\\u003c'),
    langredirect: L === 'zh-Hans' ? redirect : '',
  };
  let html = tpl.replace('/assets/og/home.jpg', `/assets/og/${L.toLowerCase()}/home.jpg`).replace(/\{\{(\w+)\}\}/g, (m, k) => (k in vars ? vars[k] : (console.warn('missing', L, k), m)));
  html = html.replace("src: url(/assets/fonts/ShantellDoodle-Bold.ttf)", "src: url(/assets/fonts/logo.woff2) format('woff2')");
  const dir = path.join(PUB, S.path);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'index.html'), html);
  // 模板页 /t/<slug>/：标题用 App 里的模板名，分享卡用这张模板的截图
  for (const [slug, name] of Object.entries(S.tnames)) {
    const tdir = path.join(dir, 't', slug);
    fs.mkdirSync(tdir, { recursive: true });
    fs.writeFileSync(path.join(tdir, 'index.html'), html
      .replace(/<title>.*?<\/title>/, `<title>${esc(name)} · Tutti</title>`)
      .replace(/(property="og:title" content=")[^"]*/, `$1${esc(name)} · Tutti`)
      .replace(`/assets/og/${L.toLowerCase()}/home.jpg`, `/assets/og/${L.toLowerCase()}/${slug}.jpg`)
      .replace(/hreflang="([^"]+)" href="https:\/\/tutti\.pics([^"]*)"/g, (m, h, p) => `hreflang="${h}" href="${SITE}${p}t/${slug}/"`));
  }
  if (L === 'zh-Hans') fs.writeFileSync(path.join(PUB, '404.html'), html.replace('<body>', '<body data-page="404">').replace(/<title>.*?<\/title>/, '<title>404 · Tutti</title>'));
  for (const seg of ['c', 'p']) redirects.push(`${S.path}${seg}/*  ${S.path}  200`);
}
fs.writeFileSync(path.join(PUB, '_redirects'), redirects.join('\n') + '\n');
console.log('built', LANGS.join(' '), '· font KB', Object.fromEntries(Object.entries(sizes).map(([k, v]) => [k, Math.round(v / 1024)])));
