/* hyper-report runtime.
 *
 * Distributes the authored block stream over fixed-size pages, resolves the
 * table of contents against the pages the headings actually landed on, and
 * writes a measurement record onto <html data-report-state> so a headless
 * browser can read it back with --dump-dom.
 *
 * Query contract with the render commands in rules/render-pipeline.md:
 *   (none)     every page stacked, one printed page each
 *   ?page=N    only page N is visible and carries the URL's title for capture
 *   ?check=1   mark the run as a check-only pass
 */
(function () {
  'use strict';

  var params = new URLSearchParams(window.location.search);
  var pageParam = parseInt(params.get('page') || '', 10);

  var root = document.querySelector('[data-report-pages]');
  if (!root) return;

  var footerLeft = root.getAttribute('data-footer-left') || '';
  var seed = document.querySelector('[data-report-flow]');
  if (!seed) return;

  var blocks = Array.prototype.slice.call(seed.children);

  /* Images have no height until they load, so paginating before they arrive
   * places a figure that grows afterwards and clips at the page fold. Wait for
   * every image, then measure. A broken image resolves too (naturalWidth 0), so
   * a missing file cannot hang the run. */
  function whenImagesReady(done) {
    var pending = Array.prototype.filter.call(document.images, function (img) {
      return !img.complete;
    });
    if (pending.length === 0) {
      done();
      return;
    }
    var left = pending.length;
    var settle = function () {
      left -= 1;
      if (left === 0) done();
    };
    pending.forEach(function (img) {
      img.addEventListener('load', settle);
      img.addEventListener('error', settle);
    });
  }

  function layout() {
  seed.parentNode.removeChild(seed);

  var pages = [];
  var current = null;

  function newPage() {
    var page = document.createElement('section');
    page.className = 'page';
    var flow = document.createElement('div');
    flow.className = 'page-flow';
    page.appendChild(flow);
    var foot = document.createElement('footer');
    foot.className = 'page-foot';
    var left = document.createElement('span');
    left.className = 'page-foot-left';
    left.textContent = footerLeft;
    var num = document.createElement('span');
    num.className = 'page-foot-right';
    foot.appendChild(left);
    foot.appendChild(num);
    page.appendChild(foot);
    root.appendChild(page);
    var entry = { page: page, flow: flow, num: num, index: pages.length + 1 };
    pages.push(entry);
    current = entry;
    return entry;
  }

  function overflows(flow) {
    return flow.scrollHeight > flow.clientHeight + 1;
  }

  function isHeading(node) {
    return /^H[1-6]$/.test(node.tagName);
  }

  /* The table of contents is sized before pagination: its item count comes from
   * the headings, so building it later would change the page count it reports. */
  var tocNode = null;
  var tocItems = [];
  var tocEntries = [];
  var tocHeads = [];

  blocks.forEach(function (node) {
    if (!tocNode && node.matches && node.matches('[data-toc]')) tocNode = node;
  });

  if (tocNode) {
    blocks.forEach(function (node) {
      if (!node.matches || !node.matches('h1, h2')) return;
      if (node.closest && node.closest('[data-toc]')) return;
      /* The source list is a reference annex, not a section the reader jumps to. */
      var headingText = (node.textContent || '').trim();
      if (/^(sources|출처|참고\s*자료)$/i.test(headingText)) return;
      tocHeads.push(node);
      var level = node.tagName === 'H2' ? 2 : 1;
      var item = document.createElement('li');
      item.className = level === 2 ? 'toc-l2' : 'toc-l1';
      var title = document.createElement('span');
      title.className = 'toc-title';
      title.textContent = node.textContent;
      var page = document.createElement('span');
      page.className = 'toc-page';
      page.textContent = '';
      item.appendChild(title);
      item.appendChild(page);
      tocEntries.push(page);
      tocItems.push(item);
    });
    var list = document.createElement('ol');
    tocItems.forEach(function (item) {
      list.appendChild(item);
    });
    tocNode.textContent = '';
    tocNode.appendChild(list);
  }

  newPage();

  blocks.forEach(function (node) {
    current.flow.appendChild(node);
    if (!overflows(current.flow) || current.flow.children.length === 1) return;
    current.flow.removeChild(node);
    newPage();
    current.flow.appendChild(node);
  });

  /* A heading must not be the last thing on a page: pull it forward so it sits
   * with the body it introduces. Runs after the first pass so the pull cannot
   * cascade into a second reflow loop. */
  pages.forEach(function (entry) {
    var kids = entry.flow.children;
    var last = kids[kids.length - 1];
    if (!last || !isHeading(last) || kids.length === 1) return;
    var next = pages[entry.index];
    if (!next) return;
    next.flow.insertBefore(last, next.flow.firstChild);
    entry.page.classList.add('page-short');
  });

  /* Drop a trailing page that ended up empty. */
  while (pages.length > 1 && pages[pages.length - 1].flow.children.length === 0) {
    var last = pages.pop();
    last.page.parentNode.removeChild(last.page);
  }

  pages.forEach(function (entry, index) {
    entry.index = index + 1;
    entry.num.textContent = String(index + 1) + ' / ' + String(pages.length);
  });

  /* Resolve the TOC now that every heading has a page. */
  tocHeads.forEach(function (node, index) {
    var owner = node.closest('.page');
    var at = pages.filter(function (entry) {
      return entry.page === owner;
    })[0];
    if (tocEntries[index]) tocEntries[index].textContent = at ? String(at.index) : '';
  });

  var state = {
    pages: pages.length,
    pageWidth: 0,
    pageHeight: 0,
    overflow: [],
    wide: [],
    empty: [],
    images: [],
    toc: tocHeads.length,
    words: 0
  };

  var box = pages[0].page.getBoundingClientRect();
  state.pageWidth = Math.round(box.width);
  state.pageHeight = Math.round(box.height);

  pages.forEach(function (entry) {
    if (entry.flow.children.length === 0) state.empty.push(entry.index);
    if (overflows(entry.flow)) state.overflow.push(entry.index);
    Array.prototype.forEach.call(entry.flow.children, function (kid) {
      if (kid.getBoundingClientRect().width > entry.flow.clientWidth + 1) {
        state.wide.push({ page: entry.index, tag: kid.tagName.toLowerCase() });
      }
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll('img'), function (img) {
    state.images.push({
      src: img.getAttribute('src') || '',
      ok: !!(img.complete && img.naturalWidth > 0)
    });
  });

  state.words = (document.body.textContent || '').trim().split(/\s+/).filter(Boolean).length;

  root.setAttribute('data-report-state', JSON.stringify(state));
  document.documentElement.setAttribute('data-report-state', JSON.stringify(state));

  if (!isNaN(pageParam) && pageParam > 0) {
    pages.forEach(function (entry) {
      if (entry.index !== pageParam) entry.page.style.display = 'none';
    });
    document.documentElement.setAttribute('data-report-single', '1');
  }

  root.setAttribute('data-report-ready', '1');
  }

  whenImagesReady(layout);
})();
