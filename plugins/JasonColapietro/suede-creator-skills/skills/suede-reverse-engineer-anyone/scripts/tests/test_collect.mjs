import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  main, createClient, parseRobots, robotsAllows, parseSitemap, pageFamily, parseCdx, detectTools, extractHero,
  parseCertificates, mapDns, normalizeJobs, tagChannels, classifyRole, parseAppleReviews, reviewSummary, npmChunks,
  monthlyTotals, starsByMonth, parseYoutubeFeed, parsePodcastFeed, appendMoves, adLibraryLinks, USER_AGENT, BlockedError,
} from '../collect.mjs';
import { parseCsv } from '../timeline.mjs';

// Any real network call fails the run.
globalThis.fetch = async (url) => {
  throw new Error(`real network call attempted: ${url}`);
};

const NOW = new Date('2026-11-12T12:00:00Z');

/** Route table fetch mock. Each route: [match (string prefix, RegExp or fn), response (object or fn)]. */
function mockFetch(routes) {
  const calls = [];
  const impl = async (url, init) => {
    calls.push({ url, init });
    const hit = routes.find(([m]) => (typeof m === 'string' ? url === m || url.startsWith(m) : m instanceof RegExp ? m.test(url) : m(url)));
    if (!hit) throw new Error(`unmocked fetch: ${url}`);
    const r = typeof hit[1] === 'function' ? hit[1](url, calls) : hit[1];
    if (r instanceof Error) throw r;
    const body = r.json !== undefined ? JSON.stringify(r.json) : r.body ?? '';
    return new Response(r.status === 204 || r.status === 304 ? null : body, { status: r.status ?? 200, headers: r.headers ?? {} });
  };
  return { impl, calls };
}

async function run(args, { routes = [], dns, sleep } = {}) {
  const out = [];
  const err = [];
  const f = mockFetch(routes);
  const sleeps = [];
  const code = await main(args, {
    log: (s) => out.push(s),
    error: (s) => err.push(s),
    fetchImpl: f.impl,
    sleep: sleep ?? (async (ms) => sleeps.push(ms)),
    dns: dns ?? { resolveTxt: async () => [], resolveMx: async () => [], resolveCname: async () => [] },
    now: () => NOW,
  });
  return { code, out: out.join('\n'), err: err.join('\n'), calls: f.calls, sleeps };
}

function withTmp(fn) {
  const dir = mkdtempSync(join(tmpdir(), 'collect-test-'));
  return Promise.resolve(fn(dir)).finally(() => rmSync(dir, { recursive: true, force: true }));
}

const cdx = (rows, withDigest = true) => ({
  json: [withDigest ? ['timestamp', 'original', 'digest'] : ['timestamp', 'original'], ...rows],
});
const page = (head, body = '') => ({ body: `<html><head>${head}</head><body>${body}</body></html>` });

// ---------- site ----------

test('site follows a sitemap index, classifies families, respects robots Disallow and stays on the domain', async () => {
  await withTmp(async (dir) => {
    const out = join(dir, 'urls.csv');
    const routes = [
      ['https://acme.com/robots.txt', { body: 'User-agent: *\nDisallow: /private/\nAllow: /private/ok\n\nSitemap: https://acme.com/sitemap_index.xml\nSitemap: https://cdn.other.net/sitemap.xml\n' }],
      ['https://acme.com/sitemap_index.xml', { body: '<?xml version="1.0"?><sitemapindex><sitemap><loc>https://acme.com/pages.xml</loc></sitemap><sitemap><loc>https://acme.com/blog.xml</loc></sitemap><sitemap><loc>https://acme.com/private/sitemap.xml</loc></sitemap></sitemapindex>' }],
      ['https://acme.com/pages.xml', { body: '<urlset><url><loc>https://acme.com/</loc></url><url><loc>https://acme.com/templates/invoice</loc><lastmod>2026-03-04T10:00:00Z</lastmod></url><url><loc>https://acme.com/de/templates/rechnung</loc></url><url><loc>https://acme.com/pricing</loc></url></urlset>' }],
      ['https://acme.com/blog.xml', { body: '<urlset><url><loc>https://acme.com/blog/launch-day</loc></url><url><loc>https://acme.com/blog/guides/seo-basics</loc></url><url><loc>https://acme.com/blog/guides/ads-101</loc></url><url><loc>https://acme.com/blog/2024/05/old-post</loc></url></urlset>' }],
    ];
    const r = await run(['site', 'acme.com', '--out', out], { routes });
    assert.equal(r.code, 0, r.err);
    assert.ok(!r.calls.some((c) => c.url.includes('/private/')), 'disallowed sitemap must not be fetched');
    assert.ok(!r.calls.some((c) => c.url.includes('other.net')), 'off-domain sitemap must not be fetched');
    assert.match(r.out, /blocked by acme\.com \(robots\.txt\): use an archived copy or a manual export/);
    assert.match(r.out, /skipped off-domain sitemap cdn\.other\.net/);
    assert.ok(r.calls.every((c) => c.init.headers['user-agent'] === USER_AGENT));
    const { headers, rows } = parseCsv(readFileSync(out, 'utf8'));
    assert.deepEqual(headers, ['url', 'family', 'lastmod']);
    const fam = Object.fromEntries(rows.map((x) => [x.url, x.family]));
    assert.equal(fam['https://acme.com/'], '/');
    assert.equal(fam['https://acme.com/templates/invoice'], '/templates');
    assert.equal(fam['https://acme.com/de/templates/rechnung'], '/templates');
    assert.equal(fam['https://acme.com/blog/launch-day'], '/blog');
    assert.equal(fam['https://acme.com/blog/guides/seo-basics'], '/blog/guides');
    assert.equal(fam['https://acme.com/blog/2024/05/old-post'], '/blog');
    assert.equal(rows.find((x) => x.url.endsWith('invoice')).lastmod, '2026-03-04');
    assert.match(r.out, /\/templates\s+2/);
  });
});

test('site falls back to /sitemap.xml when robots has no Sitemap line and handles a missing robots.txt', async () => {
  const r = await run(['site', 'acme.com'], {
    routes: [
      ['https://acme.com/robots.txt', { status: 404 }],
      ['https://acme.com/sitemap.xml', { body: '<urlset><url><loc>https://acme.com/a</loc></url></urlset>' }],
    ],
  });
  assert.equal(r.code, 0, r.err);
  assert.match(r.out, /1 URLs from 1 sitemap/);
});

test('robots parsing: own group wins over *, longest match, wildcards and $', () => {
  const { rules, sitemaps } = parseRobots('User-agent: *\nDisallow: /\n\nUser-agent: suede-collect\nDisallow: /x/*.xml$\nAllow: /x/keep.xml$\nSitemap: https://a.com/s.xml');
  assert.deepEqual(sitemaps, ['https://a.com/s.xml']);
  assert.equal(robotsAllows(rules, '/sitemap.xml'), true);
  assert.equal(robotsAllows(rules, '/x/a.xml'), false);
  assert.equal(robotsAllows(rules, '/x/keep.xml'), true);
  assert.equal(robotsAllows(parseRobots('User-agent: *\nDisallow: /').rules, '/sitemap.xml'), false);
  assert.equal(robotsAllows(parseRobots('User-agent: *\nDisallow:').rules, '/sitemap.xml'), true);
  assert.equal(parseSitemap('https://a.com/1\nhttps://a.com/2').entries.length, 2);
  assert.equal(pageFamily('not a url'), '(invalid)');
});

// ---------- stack (and the Wayback delay) ----------

const months4 = [['20260115000000', 'https://acme.com/', 'D1'], ['20260210000000', 'https://acme.com/', 'D2'], ['20260305000000', 'https://acme.com/', 'D3'], ['20260401000000', 'https://acme.com/', 'D4']];
const GA = '<script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC123"></script>';
const META = '<script>!function(f,b,e,v){}(window,document,"script","https://connect.facebook.net/en_US/fbevents.js");fbq("init","123");</script>';
const HUBSPOT = '<script id="hs-script-loader" src="//js.hs-scripts.com/123.js"></script>';

test('stack reports first-seen months, a mid-window pixel as ad-start Inferred, and honors the Wayback delay', async () => {
  await withTmp(async (dir) => {
    const movesPath = join(dir, 'moves.csv');
    const snap = { '20260115000000': GA, '20260210000000': GA, '20260305000000': GA + META, '20260401000000': GA + META + HUBSPOT };
    const routes = [
      ['https://web.archive.org/cdx/search/cdx?', cdx(months4)],
      [/web\.archive\.org\/web\/(\d+)id_\//, (url) => page(snap[url.match(/web\/(\d+)id_/)[1]], '<a href="https://js.stripe.com/v3">a link is not an install</a><script type="application/ld+json">{"x":"cdn.segment.com/analytics.js"}</script>')],
    ];
    const r = await run(['stack', 'acme.com', '--months', '12', '--moves', movesPath], { routes });
    assert.equal(r.code, 0, r.err);
    assert.equal(r.calls.length, 5);
    assert.deepEqual(r.sleeps, [1500, 1500, 1500, 1500], 'one 1500 ms pause before every archive.org request after the first');
    const cdxCall = new URL(r.calls[0].url);
    assert.equal(cdxCall.searchParams.get('collapse'), 'timestamp:6');
    assert.equal(cdxCall.searchParams.get('from'), '202512');
    assert.ok(r.calls[1].url.includes('20260115000000id_/https://acme.com/'));
    const moves = parseCsv(readFileSync(movesPath, 'utf8')).rows;
    assert.equal(moves.length, 2, 'GA was present at the window start, so it is not a move');
    const meta = moves.find((m) => m.move.startsWith('Meta Pixel'));
    assert.deepEqual([meta.date, meta.channel, meta.kind, meta.evidence], ['2026-03-05', 'paid', 'ad-start', 'Inferred']);
    assert.equal(meta.link, 'https://web.archive.org/web/20260305000000/https://acme.com/');
    const hs = moves.find((m) => m.move.startsWith('HubSpot'));
    assert.deepEqual([hs.date, hs.channel, hs.kind, hs.evidence], ['2026-04-01', 'lifecycle', 'tool-added', 'Observed']);
    assert.match(r.out, /Google Analytics 4\s+analytics\s+2026-01\s+2026-04\s+yes/);
    assert.doesNotMatch(r.out, /Stripe|Segment/);
  });
});

test('stack stops at --max-requests and reports partial results', async () => {
  const routes = [
    ['https://web.archive.org/cdx/search/cdx?', cdx(months4)],
    [/id_\//, page(GA)],
  ];
  const r = await run(['stack', 'acme.com', '--max-requests', '3'], { routes });
  assert.equal(r.code, 0, r.err);
  assert.equal(r.calls.length, 3);
  assert.match(r.out, /2 of 4 monthly homepage captures read/);
  assert.match(r.out, /request cap reached \(3\)/);
});

test('detectTools ignores links and JSON data, finds inline pixels', () => {
  assert.deepEqual(detectTools('<a href="https://cdn.shopify.com/x">shop</a>'), []);
  assert.deepEqual(detectTools(META), ['Meta Pixel']);
  assert.deepEqual(detectTools('<img src="https://bat.bing.com/bat.js">'), ['Microsoft Advertising']);
});

// ---------- history ----------

test('history flags months whose content digest changed', async () => {
  await withTmp(async (dir) => {
    const movesPath = join(dir, 'moves.csv');
    const rows = [['20260101000000', 'https://acme.com/pricing', 'A'], ['20260201000000', 'https://acme.com/pricing', 'A'], ['20260301000000', 'https://acme.com/pricing', 'B'], ['20260401000000', 'https://acme.com/pricing', 'B'], ['20260501000000', 'https://acme.com/pricing', 'C']];
    const r = await run(['history', 'https://acme.com/pricing', '--moves', movesPath], { routes: [['https://web.archive.org/cdx/search/cdx?', cdx(rows)]] });
    assert.equal(r.code, 0, r.err);
    assert.equal(r.calls.length, 1);
    assert.equal(new URL(r.calls[0].url).searchParams.get('url'), 'acme.com/pricing');
    const moves = parseCsv(readFileSync(movesPath, 'utf8')).rows;
    assert.deepEqual(moves.map((m) => m.date), ['2026-03-01', '2026-05-01']);
    assert.ok(moves.every((m) => m.kind === 'page-change' && m.evidence === 'Observed' && m.channel === 'pricing'));
    assert.equal(moves[0].link, 'https://web.archive.org/web/20260301000000/https://acme.com/pricing');
  });
});

test('parseCdx keeps one row per month and tolerates an empty result', () => {
  assert.deepEqual(parseCdx([]), []);
  const s = parseCdx([['timestamp', 'original'], ['20260101000000', 'a'], ['20260115000000', 'a'], ['20260201000000', 'a']]);
  assert.deepEqual(s.map((x) => x.month), ['2026-01', '2026-02']);
});

// ---------- hero ----------

test('hero detects headline changes and ignores text inside scripts', async () => {
  await withTmp(async (dir) => {
    const movesPath = join(dir, 'moves.csv');
    const html = {
      '20260115000000': page('<title>Acme | Invoices</title><meta name="description" content="Send invoices fast">', '<script>document.write("<h1>Injected</h1>")</script><h1>Invoices in <em>one</em> click</h1>'),
      '20260210000000': page('<title>Acme | Invoices</title><meta name="description" content="Send invoices fast">', '<h1>Invoices in <em>one</em> click</h1>'),
      '20260305000000': page('<title>Acme | AI bookkeeping</title><meta content="Books that close themselves" name="description">', '<h1>Bookkeeping on autopilot</h1>'),
      '20260401000000': page('<title>Acme | AI bookkeeping</title><meta content="Books that close themselves" name="description">', '<h1>Bookkeeping on autopilot</h1>'),
    };
    const routes = [['https://web.archive.org/cdx/search/cdx?', cdx(months4)], [/id_\//, (url) => html[url.match(/web\/(\d+)id_/)[1]]]];
    const r = await run(['hero', 'acme.com', '--moves', movesPath], { routes });
    assert.equal(r.code, 0, r.err);
    const moves = parseCsv(readFileSync(movesPath, 'utf8')).rows;
    assert.equal(moves.length, 1);
    assert.equal(moves[0].date, '2026-03-05');
    assert.equal(moves[0].kind, 'positioning-change');
    assert.match(moves[0].move, /H1: "Bookkeeping on autopilot"/);
    assert.match(moves[0].move, /title: "Acme \| AI bookkeeping"/);
    assert.doesNotMatch(r.out, /Injected/);
  });
  assert.deepEqual(extractHero('<title>A &amp; B</title><h1>Hi</h1>'), { title: 'A & B', h1: 'Hi', description: '' });
});

// ---------- subdomains ----------

const CRT = [
  { name_value: 'shop.acme.com\nwww.acme.com', not_before: '2024-06-01T00:00:00' },
  { name_value: 'shop.acme.com', not_before: '2023-02-10T00:00:00' },
  { name_value: '*.acme.com', not_before: '2022-01-01T00:00:00' },
  { name_value: 'staging.acme.com', not_before: '2022-05-01T00:00:00' },
  { name_value: 'pr-123.preview.acme.com', not_before: '2022-05-01T00:00:00' },
  { name_value: 'creators.acme.com', not_before: '2026-09-20T00:00:00' },
  { name_value: 'acme.com', not_before: '2021-01-01T00:00:00' },
  { name_value: 'evilacme.com', not_before: '2021-01-01T00:00:00' },
];

test('parseCertificates dedupes names, keeps the earliest date and drops noise', () => {
  const { subdomains, dropped } = parseCertificates(CRT, 'acme.com');
  assert.deepEqual(subdomains.map((s) => [s.subdomain, s.first_seen, s.certificates]), [
    ['shop.acme.com', '2023-02-10', 2],
    ['www.acme.com', '2024-06-01', 1],
    ['creators.acme.com', '2026-09-20', 1],
  ]);
  assert.equal(dropped, 2);
});

test('subdomains writes moves and appending twice does not duplicate them', async () => {
  await withTmp(async (dir) => {
    const movesPath = join(dir, 'moves.csv');
    writeFileSync(movesPath, 'date,channel,kind,move,reach,link,evidence\n2026-01-01,x,launch,"Launch, day one",,,Observed');
    const routes = [['https://crt.sh/?q=%25.acme.com&output=json', { json: CRT }]];
    const first = await run(['subdomains', 'www.acme.com', '--moves', movesPath], { routes });
    assert.equal(first.code, 0, first.err);
    assert.match(first.out, /moves: 3 added/);
    const second = await run(['subdomains', 'acme.com', '--moves', movesPath], { routes });
    assert.match(second.out, /moves: 0 added .* 3 already there/);
    const { headers, rows } = parseCsv(readFileSync(movesPath, 'utf8'));
    assert.deepEqual(headers, ['date', 'channel', 'kind', 'move', 'reach', 'link', 'evidence']);
    assert.equal(rows.length, 4);
    assert.equal(rows[0].move, 'Launch, day one');
    assert.deepEqual(rows[1], { date: '2023-02-10', channel: 'infrastructure', kind: 'subdomain', move: 'New subdomain shop.acme.com (first certificate)', reach: '', link: 'https://crt.sh/?q=shop.acme.com', evidence: 'Observed' });
  });
});

test('subdomains explains a crt.sh HTML error page and a timeout', async () => {
  const html = await run(['subdomains', 'acme.com'], { routes: [['https://crt.sh/', { body: '<html><body>502 Bad Gateway... please try later</body></html>' }]] });
  assert.equal(html.code, 1);
  assert.match(html.err, /^collect: crt\.sh returned an HTML error page instead of JSON/);
  const timeout = Object.assign(new Error('The operation was aborted due to timeout'), { name: 'TimeoutError' });
  const slow = await run(['subdomains', 'acme.com'], { routes: [['https://crt.sh/', timeout]] });
  assert.equal(slow.code, 1);
  assert.equal(slow.calls.length, 2, 'one retry on a network error');
  assert.match(slow.err, /crt\.sh did not answer \(crt\.sh did not respond \(timed out after 20s\)\)/);
});

// ---------- blocking and retries ----------

test('403 stops the source with the blocked message and no retry', async () => {
  const r = await run(['subdomains', 'acme.com'], { routes: [['https://crt.sh/', { status: 403 }]] });
  assert.equal(r.code, 1);
  assert.equal(r.calls.length, 1);
  assert.equal(r.err, 'collect: blocked by crt.sh (403): use an archived copy or a manual export');
});

test('the client retries a 5xx once, stops on 429, checks hosts and every redirect hop', async () => {
  let n = 0;
  const f = mockFetch([
    ['https://crt.sh/a', () => (++n === 1 ? { status: 503 } : { body: 'ok' })],
    ['https://crt.sh/b', { status: 429 }],
    ['https://crt.sh/c', { status: 302, headers: { location: 'https://evil.example/x' } }],
    ['https://crt.sh/d', { status: 500 }],
  ]);
  const client = createClient({ fetchImpl: f.impl, sleep: async () => {} });
  assert.equal(await client.text('https://crt.sh/a'), 'ok');
  await assert.rejects(client.text('https://crt.sh/b'), BlockedError);
  await assert.rejects(client.text('https://crt.sh/c'), /evil\.example is not an allowed source/);
  await assert.rejects(client.text('https://example.org/'), /not an allowed source/);
  await assert.rejects(client.text('https://crt.sh/d'), /crt\.sh returned 500/);
  assert.equal(f.calls.filter((c) => c.url === 'https://crt.sh/b').length, 1);
  assert.equal(f.calls.filter((c) => c.url === 'https://crt.sh/d').length, 2);
  assert.ok(!f.calls.some((c) => c.url.includes('evil.example')));
  assert.ok(f.calls.every((c) => c.init.signal instanceof AbortSignal && c.init.redirect === 'manual'));
});

// ---------- dns ----------

test('dns maps TXT verifications, SPF includes, MX and CNAMEs through a stubbed resolver', async () => {
  await withTmp(async (dir) => {
    const movesPath = join(dir, 'moves.csv');
    const resolver = {
      resolveTxt: async (n) => (n === 'acme.com' ? [['v=spf1 include:_spf.google.com include:sendgrid.net ', 'include:servers.mcsv.net include:amazonses.com ~all'], ['google-site-verification=abc123'], ['facebook-domain-verification=zzz'], ['atlassian-domain-verification=q'], ['some-unknown-verification=1']] : []),
      resolveMx: async () => [{ exchange: 'aspmx.l.google.com', priority: 1 }],
      resolveCname: async (n) => {
        if (n === 'go.acme.com') return ['acme.hs-sites.com'];
        if (n === 'help.acme.com') return ['acme.zendesk.com'];
        throw Object.assign(new Error('nodata'), { code: 'ENODATA' });
      },
    };
    const r = await run(['dns', 'acme.com', '--moves', movesPath], { dns: resolver });
    assert.equal(r.code, 0, r.err);
    assert.equal(r.calls.length, 0, 'dns makes no HTTP calls');
    for (const t of ['SendGrid', 'Mailchimp', 'Amazon SES', 'Google Workspace', 'Meta Business', 'Atlassian', 'HubSpot', 'Zendesk']) assert.match(r.out, new RegExp(t));
    assert.doesNotMatch(r.out, /abc123/, 'verification tokens are reduced to their prefix');
    const moves = parseCsv(readFileSync(movesPath, 'utf8')).rows;
    assert.ok(moves.every((m) => m.date === '2026-11-12' && m.kind === 'tool-verified' && m.evidence === 'Observed'));
    assert.ok(moves.some((m) => m.move === 'go.acme.com points to HubSpot'));
    assert.ok(moves.some((m) => m.move === 'Meta Business domain verification on acme.com'));
  });
  const rows = mapDns('a.com', { txt: ['v=spf1 include:spf.mtasv.net include:customeriomail.com include:_spf.klaviyo.com -all', 'apple-domain-verification=x', 'stripe-verification=y'] });
  assert.deepEqual(rows.map((x) => x.tool), ['Postmark', 'Customer.io', 'Klaviyo', 'Apple', 'Stripe']);
});

// ---------- jobs ----------

const GH = { jobs: [
  { title: 'Senior SEO Manager', departments: [{ name: 'Marketing' }], location: { name: 'Remote' }, first_published: '2026-10-01T10:00:00-04:00', absolute_url: 'https://boards.greenhouse.io/acme/jobs/1', content: '&lt;p&gt;Own organic search and our AI search (AEO) program. Contact jane.doe@example.com or @janedoe.&lt;/p&gt;' },
  { title: 'Account Executive', departments: [{ name: 'Sales' }], location: { name: 'NYC' }, updated_at: '2026-09-01T00:00:00Z', absolute_url: 'https://boards.greenhouse.io/acme/jobs/2', content: 'Close deals.' },
] };
const LEVER = [{ text: 'Lifecycle Marketing Lead', categories: { team: 'Growth', location: 'London' }, createdAt: Date.UTC(2026, 8, 15), hostedUrl: 'https://jobs.lever.co/acme/1', descriptionPlain: 'Own email marketing and influencer partnerships.', lists: [{ text: 'You will', content: '<li>Run paid social tests</li>' }] }];
const ASHBY = { jobs: [{ title: 'Product Marketing Manager', department: 'Marketing', location: 'SF', publishedAt: '2026-08-20T00:00:00Z', jobUrl: 'https://jobs.ashbyhq.com/acme/1', descriptionPlain: 'Launches, go-to-market, community.' }, { title: 'Hidden', isListed: false }] };

test('normalizeJobs parses all three boards and tags channels without keeping personal details', () => {
  const g = normalizeJobs('greenhouse', GH);
  assert.equal(g[0].posted, '2026-10-01');
  assert.equal(g[0].channels, 'seo ai-search');
  assert.equal(g[0].function, 'marketing');
  assert.equal(g[1].posted, '2026-09-01');
  assert.equal(g[1].function, 'sales');
  assert.ok(!JSON.stringify(g).includes('jane'));
  const l = normalizeJobs('lever', LEVER);
  assert.deepEqual([l[0].department, l[0].location, l[0].posted], ['Growth', 'London', '2026-09-15']);
  assert.equal(l[0].channels, 'paid lifecycle partnerships influencer');
  const a = normalizeJobs('ashby', ASHBY);
  assert.equal(a.length, 1);
  assert.equal(a[0].channels, 'community product-marketing');
  assert.deepEqual(tagChannels('Head of Growth, PR and content marketing'), ['content', 'pr', 'growth']);
  assert.equal(classifyRole('Developer Advocate'), 'marketing');
  assert.equal(classifyRole('Staff Engineer'), 'engineering');
});

test('jobs tries Greenhouse, Lever and Ashby, writes jobs.csv and summarizes by function', async () => {
  await withTmp(async (dir) => {
    const out = join(dir, 'jobs.csv');
    const r = await run(['jobs', 'Acme', '--out', out], {
      routes: [
        ['https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true', { json: GH }],
        ['https://api.lever.co/v0/postings/acme?mode=json', { status: 404, json: { ok: false } }],
        ['https://api.ashbyhq.com/posting-api/job-board/acme', { json: ASHBY }],
      ],
    });
    assert.equal(r.code, 0, r.err);
    assert.match(r.out, /3 open role/);
    assert.match(r.out, /lever\s+no board/);
    assert.match(r.out, /marketing\s+2\s+/);
    const { headers, rows } = parseCsv(readFileSync(out, 'utf8'));
    assert.deepEqual(headers.slice(0, 6), ['title', 'department', 'location', 'posted', 'url', 'channels']);
    assert.equal(rows.length, 3);
    assert.ok(!readFileSync(out, 'utf8').includes('jane'));
  });
});

// ---------- reviews ----------

const review = (date, rating, title, text, author) => ({ author: { name: { label: author }, uri: { label: `https://itunes.apple.com/us/reviewer/${author}` } }, updated: { label: date }, 'im:rating': { label: String(rating) }, title: { label: title }, content: { label: text }, id: { label: '1' } });

test('reviews aggregates by month, finds complaint terms and never outputs reviewer names', async () => {
  await withTmp(async (dir) => {
    const out = join(dir, 'reviews.csv');
    const p1 = { feed: { entry: [
      { 'im:name': { label: 'Acme App' } },
      review('2026-10-30T10:00:00-07:00', 1, 'Crashes constantly', 'The app crashes on login. Subscription too pricey.', 'ReviewerAlice'),
      review('2026-10-12T10:00:00-07:00', 5, 'Love it', 'Great', 'ReviewerBob'),
      review('2026-09-03T10:00:00-07:00', 2, 'Login broken', 'Login crashes after update, subscription renewal confusing', 'ReviewerCarol'),
    ] } };
    const p2 = { feed: { entry: review('2026-09-01T10:00:00-07:00', 4, 'Fine', 'Works', 'ReviewerDan') } };
    const r = await run(['reviews', 'id284882215', '--pages', '3', '--out', out, '--json'], {
      routes: [
        ['https://itunes.apple.com/us/rss/customerreviews/page=1/id=284882215/sortby=mostrecent/json', { json: p1 }],
        ['https://itunes.apple.com/us/rss/customerreviews/page=2/id=284882215/sortby=mostrecent/json', { json: p2 }],
        ['https://itunes.apple.com/us/rss/customerreviews/page=3/', { json: { feed: {} } }],
      ],
    });
    assert.equal(r.code, 0, r.err);
    const csv = readFileSync(out, 'utf8');
    assert.deepEqual(parseCsv(csv).rows, [
      { month: '2026-09', count: '2', avg_rating: '3', low_count: '1' },
      { month: '2026-10', count: '2', avg_rating: '3', low_count: '1' },
    ]);
    const json = JSON.parse(r.out);
    assert.deepEqual(json.complaint_terms.map((t) => t.term).slice(0, 3), ['crashes', 'login', 'subscription']);
    for (const s of [r.out, csv]) assert.doesNotMatch(s, /Reviewer(Alice|Bob|Carol|Dan)/);
  });
  assert.equal(parseAppleReviews({ feed: { entry: [review('2026-01-01', 3, 't', 'x', 'Zed')] } })[0].author, undefined);
  assert.deepEqual(reviewSummary([]).rows, []);
});

// ---------- adoption ----------

test('npmChunks splits the window into ranges of at most 18 months', () => {
  assert.deepEqual(npmChunks(24, NOW), [{ from: '2024-11-01', to: '2026-04-30' }, { from: '2026-05-01', to: '2026-10-31' }]);
  assert.deepEqual(npmChunks(40, NOW).map((c) => c.from), ['2023-07-01', '2025-01-01', '2026-07-01']);
  assert.equal(npmChunks(6, NOW).length, 1);
});

function days(fromYm, n, perDay) {
  const out = [];
  const start = Date.UTC(+fromYm.slice(0, 4), +fromYm.slice(5, 7) - 1, 1);
  for (let i = 0; i < n; i++) out.push({ day: new Date(start + i * 86400000).toISOString().slice(0, 10), downloads: perDay });
  return out;
}

test('adoption builds a curve.csv from chunked npm ranges with GitHub stars as secondary', async () => {
  await withTmp(async (dir) => {
    const out = join(dir, 'curve.csv');
    const routes = [
      ['https://api.npmjs.org/downloads/range/2025-03-01:2026-08-31/@acme/sdk', { json: { downloads: [...days('2025-03', 31 + 30, 0), ...days('2025-05', 365 + 120, 10)] } }],
      ['https://api.npmjs.org/downloads/range/2026-09-01:2026-10-31/@acme/sdk', { json: { downloads: days('2026-09', 30 + 31, 20) } }],
      ['https://api.github.com/repos/acme/sdk/stargazers', (url) => {
        const p = Number(new URL(url).searchParams.get('page'));
        return { json: [{ starred_at: p === 1 ? '2025-01-01T00:00:00Z' : '2026-01-01T00:00:00Z' }] };
      }],
      ['https://api.github.com/repos/acme/sdk', { json: { stargazers_count: 250 } }],
    ];
    const r = await run(['adoption', '--npm', '@acme/sdk', '--github', 'acme/sdk', '--months', '20', '--star-pages', '2', '--out', out], { routes });
    assert.equal(r.code, 0, r.err);
    const npmCalls = r.calls.filter((c) => c.url.includes('npmjs'));
    assert.equal(npmCalls.length, 2);
    const star = r.calls.find((c) => c.url.includes('stargazers'));
    assert.equal(star.init.headers.accept, 'application/vnd.github.star+json');
    assert.ok(r.calls.every((c) => !c.init.headers.authorization), 'no credentials are sent');
    const { headers, rows } = parseCsv(readFileSync(out, 'utf8'));
    assert.deepEqual(headers, ['month', 'primary', 'secondary']);
    assert.equal(rows[0].month, '2025-05', 'leading zero months before the package existed are dropped');
    assert.equal(rows[0].primary, '310');
    assert.equal(rows.at(-1).month, '2026-10');
    assert.equal(rows.at(-1).primary, '620');
    assert.ok(Number(rows.at(-1).secondary) > Number(rows[0].secondary));
  });
});

test('adoption keeps the star count when the stargazer list is blocked', async () => {
  const r = await run(['adoption', '--github', 'acme/sdk', '--months', '6'], {
    routes: [
      ['https://api.github.com/repos/acme/sdk/stargazers', { status: 403 }],
      ['https://api.github.com/repos/acme/sdk', { json: { stargazers_count: 5000 } }],
    ],
  });
  assert.equal(r.code, 0, r.err);
  assert.match(r.out, /acme\/sdk has 5000 stars now/);
  assert.match(r.out, /blocked by api\.github\.com \(403\): use an archived copy or a manual export/);
  assert.equal(r.calls.filter((c) => c.url.includes('stargazers')).length, 1);
});

test('monthlyTotals drops incomplete months and starsByMonth interpolates', () => {
  const t = monthlyTotals([...days('2026-01', 31, 1), ...days('2026-02', 10, 1)], ['2026-01', '2026-02']);
  assert.deepEqual(t, { '2026-01': 31 });
  const s = starsByMonth([{ index: 1, date: '2026-01-01T00:00:00Z' }, { index: 101, date: '2026-03-01T00:00:00Z' }], ['2025-12', '2026-01', '2026-02'], 101, new Date('2026-03-01T00:00:00Z'));
  assert.equal(s['2025-12'], 0);
  assert.ok(s['2026-01'] > 40 && s['2026-01'] < 60);
});

// ---------- youtube and podcast ----------

const YT = `<?xml version="1.0"?><feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/">
<title>Acme</title>
<entry><yt:videoId>abc</yt:videoId><title>How we grew &amp; why</title><link rel="alternate" href="https://www.youtube.com/watch?v=abc"/><published>2026-10-20T15:00:00+00:00</published><media:group><media:community><media:statistics views="12345"/></media:community></media:group></entry>
<entry><yt:videoId>def</yt:videoId><title>Second</title><published>2026-10-13T15:00:00+00:00</published></entry>
<entry><yt:videoId>ghi</yt:videoId><title>Third</title><link rel="alternate" href="https://www.youtube.com/watch?v=ghi"/><published>2026-09-29T15:00:00+00:00</published><media:statistics views="10"/></entry>
</feed>`;

test('youtube parses the channel feed into posts-youtube.csv with cadence', async () => {
  const posts = parseYoutubeFeed(YT);
  assert.deepEqual(posts[0], { channel: 'youtube', date: '2026-10-20', url: 'https://www.youtube.com/watch?v=abc', views: 12345, title: 'How we grew & why' });
  assert.equal(posts[1].url, 'https://www.youtube.com/watch?v=def');
  assert.equal(posts[1].views, '');
  await withTmp(async (dir) => {
    const out = join(dir, 'posts-youtube.csv');
    const id = 'UC' + 'a'.repeat(22);
    const r = await run(['youtube', id, '--out', out], { routes: [[`https://www.youtube.com/feeds/videos.xml?channel_id=${id}`, { body: YT }]] });
    assert.equal(r.code, 0, r.err);
    assert.match(r.out, /3 recent upload\(s\).*median 10\.5 days/);
    assert.match(r.out, /latest ~15 uploads/);
    assert.deepEqual(parseCsv(readFileSync(out, 'utf8')).headers, ['channel', 'date', 'url', 'views', 'title']);
  });
  assert.equal((await run(['youtube', 'acme'])).code, 1);
});

const RSS = `<?xml version="1.0"?><rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"><channel><title>Show</title>
<item><title><![CDATA[Ep 2: Growth loops]]></title><pubDate>Tue, 03 Nov 2026 08:00:00 GMT</pubDate><link>https://show.example/2</link><enclosure url="https://cdn.show.example/2.mp3" type="audio/mpeg" length="1"/><itunes:duration>45:10</itunes:duration><itunes:title>ignored</itunes:title></item>
<item><title>Ep 1: Start</title><pubDate>Tue, 20 Oct 2026 08:00:00 GMT</pubDate><enclosure url="https://cdn.show.example/1.mp3"/></item>
</channel></rss>`;

test('podcast parses RSS items, writes episodes and release moves, and only fetches the feed host', async () => {
  const eps = parsePodcastFeed(RSS);
  assert.deepEqual(eps[0], { date: '2026-11-03', title: 'Ep 2: Growth loops', url: 'https://show.example/2', enclosure: 'https://cdn.show.example/2.mp3', duration: '45:10' });
  assert.equal(eps[1].url, 'https://cdn.show.example/1.mp3');
  await withTmp(async (dir) => {
    const movesPath = join(dir, 'moves.csv');
    const out = join(dir, 'episodes.csv');
    const r = await run(['podcast', 'https://feeds.show.example/rss', '--out', out, '--moves', movesPath], { routes: [['https://feeds.show.example/rss', { body: RSS }]] });
    assert.equal(r.code, 0, r.err);
    assert.match(r.out, /2 episode\(s\).*median 14\.0 days/);
    const moves = parseCsv(readFileSync(movesPath, 'utf8')).rows;
    assert.deepEqual(moves.map((m) => [m.date, m.channel, m.kind, m.evidence]), [['2026-11-03', 'podcast', 'release', 'Observed'], ['2026-10-20', 'podcast', 'release', 'Observed']]);
    const moved = await run(['podcast', 'https://feeds.show.example/rss'], { routes: [['https://feeds.show.example/rss', { status: 301, headers: { location: 'https://other-host.example/rss' } }]] });
    assert.equal(moved.code, 1);
    assert.match(moved.err, /other-host\.example is not an allowed source/);
  });
});

// ---------- moves helper, ads, CLI ----------

test('appendMoves creates the file with a header, respects existing column order and dedupes', async () => {
  await withTmp((dir) => {
    const p = join(dir, 'm.csv');
    const row = { date: '2026-01-02', channel: 'paid', kind: 'ad-start', move: 'X', reach: '', link: 'l', evidence: 'Inferred' };
    assert.deepEqual(appendMoves(p, [row, row]), { added: 1, skipped: 1 });
    assert.equal(readFileSync(p, 'utf8').split('\n')[0], 'date,channel,kind,move,reach,link,evidence');
    const q = join(dir, 'q.csv');
    writeFileSync(q, 'channel,date,kind,move,evidence\npaid,2026-01-02,ad-start,X,Inferred\n');
    assert.deepEqual(appendMoves(q, [row, { ...row, move: 'Y' }]), { added: 1, skipped: 1 });
    assert.equal(readFileSync(q, 'utf8').trim().split('\n')[2], 'paid,2026-01-02,ad-start,Y,Inferred');
    writeFileSync(join(dir, 'bad.csv'), 'a,b\n1,2\n');
    assert.throws(() => appendMoves(join(dir, 'bad.csv'), [row]), /missing column/);
  });
});

test('ads prints library links without fetching anything', async () => {
  await withTmp(async (dir) => {
    const out = join(dir, 'ads.csv');
    const r = await run(['ads', 'Acme Co', '--domain', 'https://www.acme.com/', '--out', out]);
    assert.equal(r.code, 0, r.err);
    assert.equal(r.calls.length, 0);
    assert.match(r.out, /facebook\.com\/ads\/library\/.*q=Acme%20Co/);
    assert.match(r.out, /adstransparency\.google\.com\/\?region=anywhere&domain=acme\.com/);
    assert.equal(parseCsv(readFileSync(out, 'utf8')).rows.length, 4);
  });
  assert.equal(adLibraryLinks('A', '').length, 4);
});

test('CLI rejects bad input with collect: messages and exit 1', async () => {
  const cases = [
    [['nope'], /unknown command "nope"/],
    [['site'], /site needs a domain/],
    [['site', 'not a domain!'], /is not a domain/],
    [['stack', 'acme.com', '--months', '0'], /--months must be a whole number/],
    [['jobs', 'acme', '--moves', 'm.csv'], /jobs does not produce moves/],
    [['reviews', 'abc'], /numeric App Store app id/],
    [['adoption'], /adoption needs --npm/],
    [['adoption', '--npm', 'a', '--pypi', 'b'], /pick one registry/],
    [['site', 'acme.com', '--bogus'], /Unknown option/],
  ];
  for (const [args, re] of cases) {
    const r = await run(args);
    assert.equal(r.code, 1, args.join(' '));
    assert.match(r.err, /^collect: /);
    assert.match(r.err, re);
    assert.equal(r.calls.length, 0);
  }
  const help = await run(['--help']);
  assert.equal(help.code, 0);
  assert.match(help.out, /node collect\.mjs site <domain>/);
  assert.ok(!existsSync('m.csv'));
});
