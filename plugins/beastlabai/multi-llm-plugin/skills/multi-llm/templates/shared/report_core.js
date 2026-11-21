// The script the three report pages share: report.html (flat and PR styles)
// and consolidated-report.html. The generator inlines it into each page as a
// script element of its own, before the page's script, so a report stays one
// file that loads nothing (docs/development.md#shared-report-code).
//
// It only declares: nothing here runs while the page loads. What it reads
// when called comes from the page's script: `reportData` (the embedded
// payload), and `selections`, `getStorageKey()` and `selectionsFile(now)`
// (see Selections below). A function a page needs differently stays in that
// page's template.

// BEGIN SAFE MARKDOWN
// Model, plan and repository text is untrusted, and so is every field that
// carries it: titles, statuses, importances, model names, ids, paths. Each
// reaches the page one way only (docs/development.md#vendored-report-scripts):
// a markdown body through renderMarkdown; any other text, and every quoted
// attribute value, through escapeHtml (escapeAttr is the same escaper, named
// for attribute sites); a value inside an inline handler's JS string through
// escapeJsAttr. A class name never comes from data: the badge helpers map a
// status or an importance onto a fixed list.
function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function escapeAttr(text) {
  return escapeHtml(text);
}

// A value inside a single-quoted JS string in an inline handler
// (onclick="f('…')"). The browser decodes the attribute's entities before
// the handler runs, so escapeAttr alone would hand a quote back to the JS
// parser: escape for the JS string first, then for the attribute.
function escapeJsAttr(text) {
  if (text === null || text === undefined) return '';
  return escapeAttr(String(text).replace(/\\/g, '\\\\').replace(/'/g, '\\\'')
    .replace(/\r/g, '\\r').replace(/\n/g, '\\n')
    .replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029'));
}

function getImportanceBadgeClass(importance) {
  switch (importance === null || importance === undefined ? '' : String(importance).toUpperCase()) {
    case 'HIGH': return 'badge-importance-high';
    case 'MEDIUM': return 'badge-importance-medium';
    case 'LOW': return 'badge-importance-low';
    default: return 'badge-category';
  }
}

function getValidationBadgeClass(status) {
  switch (status) {
    case 'valid': return 'badge-validation-valid';
    case 'invalid': return 'badge-validation-invalid';
    case 'needs-human-decision': return 'badge-validation-needs-human';
    case 'validation_failed': return 'badge-validation-failed';
    default: return 'badge-category';
  }
}

// marked renders a markdown body, then DOMPurify keeps only the markdown
// vocabulary below: no script, handler, style, image, form control, id,
// class or data attribute, and only safe link URLs. Without both libraries
// the text is escaped instead. The generator inlines them.
function renderMarkdown(text) {
  if (!text) return '';
  if (typeof marked !== 'undefined' && typeof marked.parse === 'function' &&
      typeof DOMPurify !== 'undefined' && typeof DOMPurify.sanitize === 'function' &&
      DOMPurify.isSupported === true) {
    try {
      return DOMPurify.sanitize(marked.parse(String(text), { breaks: true }), {
        ALLOWED_TAGS: ['a', 'abbr', 'b', 'blockquote', 'br', 'code', 'dd', 'del', 'details',
          'div', 'dl', 'dt', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'ins', 'kbd',
          'li', 'mark', 'ol', 'p', 'pre', 'q', 's', 'samp', 'small', 'span', 'strong', 'sub',
          'summary', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'u', 'ul',
          'var'],
        ALLOWED_ATTR: ['align', 'colspan', 'href', 'open', 'rowspan', 'start', 'title'],
        ALLOW_DATA_ATTR: false,
        ALLOW_ARIA_ATTR: false
      });
    } catch (e) { /* fall through to the escaped text */ }
  }
  return '<p>' + escapeHtml(text).replace(/\n/g, '<br>') + '</p>';
}
// END SAFE MARKDOWN

// ================================================================
// Model badges
// ================================================================
function getModelBadgeHtml(modelString) {
  var metadata = reportData && reportData.modelMetadata ? reportData.modelMetadata[modelString] : null;
  if (!metadata) {
    return '<span class="badge badge-model" style="background: #6B7280;">' + escapeHtml(modelString) + '</span>';
  }
  var html = '<span class="model-badge-group">';
  // The provider icon, when it differs from the model's.
  if (metadata.provider_icon) {
    html += '<img class="model-icon" src="' + escapeAttr(metadata.provider_icon) + '" alt="" />';
  }
  if (metadata.icon) {
    html += '<img class="model-icon" src="' + escapeAttr(metadata.icon) + '" alt="" />';
  }
  if (metadata.provider) {
    html += '<span class="badge badge-provider" style="background: ' + escapeAttr(metadata.provider_color) + ';">' +
            escapeHtml(metadata.provider) + '</span>';
  }
  html += '<span class="badge badge-model" style="background: ' + escapeAttr(metadata.model_color || '#6B7280') + ';">' +
          escapeHtml(metadata.model || modelString) + '</span>';
  // What this slot spent, when the adapter reported it. The text is
  // `usage_label`, rendered server-side by the one `describe_usage` the
  // markdown report and the failed-slot log line also use; the pages never
  // re-derive it from `metadata.usage`, so every surface says one cost. A
  // model that reported nothing has no key and renders no badge, never
  // `$0.00`, which would claim a free run.
  if (metadata.usage_label) {
    html += '<span class="badge badge-usage" style="background: #6B7280;" title="Estimated from the CLI\'s own price catalog, not a vendor invoice">' +
            escapeHtml(metadata.usage_label) + '</span>';
  }
  html += '</span>';
  return html;
}

// One `reportData.notices` list renders the same bar on every page.
function renderNotices() {
  if (!reportData) return;
  var container = document.getElementById('report-notices');
  if (!container) return;
  var html = '';
  var notices = reportData.notices || [];
  notices.forEach(function(n) {
    var cls = 'report-notice';
    if (n.type === 'info') cls += ' info';
    else if (n.type === 'warning') cls += ' warning';
    html += '<div class="' + cls + '">' + escapeHtml(n.message) + '</div>';
  });
  container.innerHTML = html;
}

// ================================================================
// Selections: what the reader skipped, overrode, edited and labelled.
// The page declares `selections` (the fields it keeps, with their empty
// values), `getStorageKey()` (its localStorage key) and
// `selectionsFile(now)` (the file name and content Export saves, which its
// apply phase reads). A stored selection restores only the fields the page
// declares, each of the declared kind, and never a scope or policy field
// (stripScopeSelectionFields).
// ================================================================
function migrateLegacyOverrides(overrides) {
  if (!overrides) return;
  Object.keys(overrides).forEach(function(k) {
    if (overrides[k] === 'claude_decide') overrides[k] = 'judge_decide';
  });
}

function loadSelections() {
  var parsed = null;
  try {
    var stored = localStorage.getItem(getStorageKey());
    if (stored) parsed = stripScopeSelectionFields(JSON.parse(stored));
  } catch (e) {
    console.error('Failed to load selections:', e);
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return;
  // A v1 selection listed skipped ids in arrays.
  ['skipped_groups', 'skipped_suggestions'].forEach(function(key) {
    if (!Array.isArray(parsed[key])) return;
    var migrated = {};
    parsed[key].forEach(function(id) { migrated[String(id)] = true; });
    parsed[key] = migrated;
  });
  // A selection saved before the judge rename says 'claude_decide' (utils/judge_vocab.py).
  migrateLegacyOverrides(parsed.validation_overrides);
  Object.keys(selections).forEach(function(key) {
    if (!Object.prototype.hasOwnProperty.call(parsed, key)) return;
    var current = selections[key];
    var value = parsed[key];
    var wantsObject = current !== null && typeof current === 'object';
    if (wantsObject && (value === null || typeof value !== 'object' || Array.isArray(value))) return;
    selections[key] = value;
  });
}

function saveSelections() {
  try {
    localStorage.setItem(getStorageKey(), JSON.stringify(selections));
  } catch (e) {
    console.error('Failed to save selections:', e);
  }
}

function downloadJson(filename, value) {
  var blob = new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function exportSelections() {
  var now = new Date().toISOString();
  selections.last_file_export_at = now;
  var file = selectionsFile(now);
  saveSelections();
  downloadJson(file.name, file.data);
  updateExportIndicator();
}

function timeAgo(isoString) {
  if (!isoString) return '';
  var diff = Date.now() - new Date(isoString).getTime();
  var seconds = Math.floor(diff / 1000);
  if (seconds < 60) return 'just now';
  var minutes = Math.floor(seconds / 60);
  if (minutes < 60) return minutes + 'm ago';
  var hours = Math.floor(minutes / 60);
  if (hours < 24) return hours + 'h ago';
  var days = Math.floor(hours / 24);
  return days + 'd ago';
}

function updateExportIndicator() {
  var el = document.getElementById('export-indicator');
  if (!el) return;
  if (selections.last_file_export_at) {
    el.textContent = '✓ Exported ' + timeAgo(selections.last_file_export_at);
    el.style.display = '';
  } else {
    el.style.display = 'none';
  }
}

// ================================================================
// Card order (the flat and consolidated pages; the PR page orders its own
// views). The group cards in #groups-container go in the generator's order
// ('original') or by priority: validation status, then importance, through
// the generator's rank table (reportData.sortConfig), then the generator's
// order. *first*, when given, compares two cards before the ranks do. The
// choice is saved under *storageKey*.
// ================================================================
function sortRanks() {
  var config = (typeof reportData !== 'undefined' && reportData && reportData.sortConfig) || null;
  if (config && config.validationOrder && config.importanceOrder) {
    return {
      validationOrder: config.validationOrder,
      importanceOrder: config.importanceOrder,
      unknownStatusRank: config.unknownStatusRank || 5,
      unknownImportanceRank: config.unknownImportanceRank || 3
    };
  }
  console.warn('sortConfig missing or malformed, using hardcoded defaults');
  return {
    validationOrder: {"needs-human-decision": 0, "valid": 1, "validation_failed": 2, "invalid": 3, "pending": 4},
    importanceOrder: {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "": 3},
    unknownStatusRank: 5,
    unknownImportanceRank: 3
  };
}

function sortGroupCards(value, storageKey, first) {
  var container = document.getElementById('groups-container') || document.querySelector('.groups-container');
  if (!container) return;
  var cards = Array.from(container.querySelectorAll('.group-card'));
  if (cards.length === 0) return;
  var ranks = sortRanks();
  function rank(table, key, unknown) {
    return (key in table) ? table[key] : unknown;
  }
  function originalIndex(card) {
    return parseInt(card.dataset.originalIndex) || 0;
  }
  cards.sort(function(a, b) {
    if (first) {
      var firstOrder = first(a, b);
      if (firstOrder !== 0) return firstOrder;
    }
    if (value === 'original') return originalIndex(a) - originalIndex(b);
    var byStatus = rank(ranks.validationOrder, a.dataset.validation || '', ranks.unknownStatusRank) -
      rank(ranks.validationOrder, b.dataset.validation || '', ranks.unknownStatusRank);
    if (byStatus !== 0) return byStatus;
    var byImportance = rank(ranks.importanceOrder, a.dataset.importance || '', ranks.unknownImportanceRank) -
      rank(ranks.importanceOrder, b.dataset.importance || '', ranks.unknownImportanceRank);
    if (byImportance !== 0) return byImportance;
    return originalIndex(a) - originalIndex(b);
  });
  cards.forEach(function(card) { container.appendChild(card); });
  try {
    localStorage.setItem(storageKey, value);
  } catch (e) { /* localStorage unavailable */ }
}

// ================================================================
// Commit review (the flat and PR pages; plans/review-commits.md §2.10).
// Everything here reads reportData.commitRange, which the generator
// stores only for a commit review, so a plan's report renders none of it.
// ================================================================
function commitKeyOf(group) {
  return (group && group.introducedBy) ? group.introducedBy : 'unattributed';
}

function commitRankOf(key) {
  var cr = reportData && reportData.commitRange;
  var commits = (cr && cr.commits) || [];
  for (var i = 0; i < commits.length; i++) {
    if (commits[i].sha === key) return i;
  }
  return commits.length + (key === 'unattributed' ? 1 : 0);
}

function introducedByHtml(group) {
  if (!reportData || !reportData.commitRange || !group || !group.introducedBy) return '';
  var source = group.introducedBySource || '';
  if (source === 'none' || !source) return '';
  var html = '<div class="introduced-by">Introduced by <code>' +
    escapeHtml(group.introducedByShort || String(group.introducedBy).substring(0, 7)) + '</code>';
  if (group.introducedBySubject) html += ' — ' + escapeHtml(group.introducedBySubject);
  if (source === 'model' || source === 'model-drifted') {
    html += ' <span class="introduced-by-model" title="The reviewing model named this commit; git blame did not measure it">(model)</span>';
  }
  return html + '</div>';
}

// The distinct file paths a group's suggestions cite, line ranges dropped.
function groupFiles(group) {
  var files = [];
  ((group && group.suggestions) || []).forEach(function(s) {
    var ref = s.fileRef || '';
    var path = ref.replace(/:\d+(-\d+)?$/, '');
    if (path && files.indexOf(path) === -1) files.push(path);
  });
  return files;
}

// A path absent at `head` on a pinned review: its header carries the same
// words as its validation excerpt (plans/review-commits.md §2.5), "deleted
// in <range>", "renamed to <new> in <range>" or "absent at <head7>". The
// generator stores them as fileContexts[path].label; a plan's report has none.
function fileLabelHtml(fileRef) {
  var path = String(fileRef || '').replace(/:\d+(-\d+)?$/, '');
  var entry = ((reportData && reportData.fileContexts) || {})[path];
  var label = (entry && !Array.isArray(entry)) ? entry.label : '';
  if (!label) return '';
  return ' <span class="file-absent-label">(' + escapeHtml(label) + ')</span>';
}

// The badge for *paths* (a group's files, or one file's) when any of them
// differs on disk from the reviewed head.
function driftBadgeHtml(paths) {
  var cr = reportData && reportData.commitRange;
  if (!cr || !cr.drifted || !cr.drifted.length) return '';
  var hit = (paths || []).some(function(path) { return cr.drifted.indexOf(path) !== -1; });
  if (!hit) return '';
  var head7 = String(cr.head || '').substring(0, 7);
  return '<span class="badge badge-drift" title="This file differs on disk from ' + escapeAttr(head7) +
    ': a skip or apply decision on it is skipped anyway by the apply\'s guard">changed on disk since ' +
    escapeHtml(head7) + '</span>';
}

// ================================================================
// Scope tags (plans/scope-policy-and-report-tags.md §6). BEGIN SCOPE TAGS
// Tags describe proposals:
// they never change validity or selection, and no selection — restored
// from localStorage or imported — ever changes a tag. Every word comes
// from reportData (written by the generator); a payload without scope
// data (a legacy report) reads `Scope unclear` throughout.
// ================================================================
var SCOPE_LABELS = { in_scope: 'Within scope', scope_extension: 'Scope extension', unclear: 'Scope unclear' };
var SCOPE_CLASSES = { in_scope: 'scope-in', scope_extension: 'scope-extension', unclear: 'scope-unclear' };
var SCOPE_DEFERRED = 'Deferred: scope preservation requested';
var SCOPE_LEGACY_LINE = 'Scope policy: expand. This report predates scope classification, so every tag reads Scope unclear.';

function scopeAttr(text) {
  if (text === null || text === undefined) return '';
  return escapeHtml(String(text)).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function scopeSelectorValue(text) {
  return String(text === null || text === undefined ? '' : text).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

function scopeRelation(relation) {
  return Object.prototype.hasOwnProperty.call(SCOPE_LABELS, relation) ? relation : 'unclear';
}

function scopeBadgeHtml(relation, qualifier, title) {
  var rel = scopeRelation(relation);
  var text = SCOPE_LABELS[rel] + (qualifier ? ' (' + qualifier + ')' : '');
  return '<span class="badge scope-badge ' + SCOPE_CLASSES[rel] + '" title="' +
    scopeAttr(title || text) + '">' + escapeHtml(text) + '</span>';
}

function scopeDeferredHtml(text, title) {
  return '<span class="badge scope-badge scope-deferred" title="' + scopeAttr(title || text) + '">' +
    escapeHtml(text) + '</span>';
}

// An edited description changes the proposal its classification was made for.
function scopeSuggestionEdited(s) {
  if (!s || !selections || !selections.edited_descriptions) return false;
  var edited = selections.edited_descriptions[s.id];
  return edited !== undefined && edited !== (s.description || s.content || '');
}

function scopeGroupEdited(group) {
  return ((group && group.suggestions) || []).some(scopeSuggestionEdited);
}

// The reviewer's own tag: provisional, never authority.
function scopeMemberBadges(s) {
  var e = (s && s.scope) || {};
  var classified = !!e.classified;
  var qualifier = 'provisional' + (scopeSuggestionEdited(s) ? '; may be stale: description edited' : '');
  var reason = classified ? (e.reason || '') : 'not classified';
  return scopeBadgeHtml(classified ? e.relation : 'unclear', qualifier,
    'Reviewer classification (provisional)' + (reason ? ': ' + reason : ''));
}

function scopeMemberHtml(s) {
  return '<span class="scope-tags" data-scope-suggestion="' + scopeAttr((s && s.id) || '') + '">' +
    scopeMemberBadges(s) + '</span>';
}

// The group's validated tag as this page can vouch for it now.
function scopeGroupView(group) {
  var e = (group && group.scope) || null;
  var edited = scopeGroupEdited(group);
  if (!e) {
    return { relation: 'unclear', qualifier: 'not classified', decision: null,
             title: 'No validated scope classification', reason: 'no validated scope classification' };
  }
  var state = e.authority || 'missing';
  var classifiedLabel = SCOPE_LABELS[scopeRelation(e.classifiedRelation || e.relation)];
  var view = { relation: 'unclear', decision: e.decision || null, reason: e.reason || '' };
  if (state === 'bound' && edited) {
    view.qualifier = 'may be stale: description edited';
    view.reason = 'validated as ' + classifiedLabel + ' before this description was edited' +
      (e.reason ? ': ' + e.reason : '');
    if (view.decision && view.decision.policy === 'preserve') {
      view.decision = { policy: 'preserve', outcome: 'deferred',
                        reason: SCOPE_DEFERRED + ': the proposal changed after its scope was validated' };
    }
  } else if (state === 'bound') {
    view.relation = e.relation;
    view.qualifier = 'validated';
  } else if (state === 'stale') {
    view.qualifier = 'may be stale';
    view.reason = 'validated as ' + classifiedLabel + ' before the proposal changed' +
      (e.classifiedReason ? ': ' + e.classifiedReason : '');
  } else {
    view.qualifier = state === 'missing' ? 'not classified' : 'not bound';
  }
  view.title = 'Group scope (' + view.qualifier + ')' + (view.reason ? ': ' + view.reason : '');
  return view;
}

function scopeGroupBadges(group) {
  var view = scopeGroupView(group);
  var html = scopeBadgeHtml(view.relation, view.qualifier, view.title);
  var d = view.decision;
  // Under preserve a deferral shows whatever the validity is; the
  // selection controls stay usable for a later policy override.
  if (d && d.policy === 'preserve' && d.outcome === 'deferred') {
    html += scopeDeferredHtml(SCOPE_DEFERRED, d.reason || SCOPE_DEFERRED);
  }
  return html;
}

// Keyed by the stable group hash only: a hash-less legacy group is never
// re-rendered in place (no key could tell two of them apart).
function scopeGroupHtml(group) {
  var key = (group && group.groupHash) || '';
  return '<span class="scope-tags"' + (key ? ' data-scope-group="' + scopeAttr(key) + '"' : '') + '>' +
    scopeGroupBadges(group) + '</span>';
}

function scopeDetailBody(group) {
  var view = scopeGroupView(group);
  var e = (group && group.scope) || {};
  var html = '<div class="scope-line"><strong>Scope (' + escapeHtml(view.qualifier) + '):</strong> ' +
    escapeHtml(SCOPE_LABELS[scopeRelation(view.relation)]) +
    (view.reason ? ' &mdash; ' + escapeHtml(view.reason) : '') + '</div>';
  if (e.reference) html += '<div class="scope-line"><strong>Baseline reference:</strong> ' + escapeHtml(e.reference) + '</div>';
  if (e.selectedRemedy && e.authority === 'bound') {
    html += '<div class="scope-line"><strong>Selected remedy:</strong> ' + escapeHtml(e.selectedRemedy) + '</div>';
  }
  var d = view.decision;
  if (d && d.policy === 'preserve') {
    html += '<div class="scope-line"><strong>Scope outcome:</strong> ' +
      escapeHtml(d.outcome === 'deferred' ? (d.reason || SCOPE_DEFERRED) : 'Eligible under scope preservation') + '</div>';
  }
  return html;
}

function scopeDetailHtml(group) {
  var view = scopeGroupView(group);
  return '<details class="scope-section"><summary>Scope: ' +
    escapeHtml(SCOPE_LABELS[scopeRelation(view.relation)] + ' (' + view.qualifier + ')') + '</summary>' +
    '<div class="scope-detail"' + (group && group.groupHash ? ' data-scope-detail="' + scopeAttr(group.groupHash) + '"' : '') + '>' +
    scopeDetailBody(group) + '</div></details>';
}

// An umbrella's tag is derived from its underlying groups; each keeps its own.
function scopeUmbrellaBadges(entry) {
  var e = entry || null;
  if (!e) return scopeBadgeHtml('unclear', 'derived', 'No scope data for this consolidated group');
  var qualifier = 'derived' + (e.mixed ? '; mixed members' : '');
  var html = scopeBadgeHtml(e.relation, qualifier, (e.label || SCOPE_LABELS[scopeRelation(e.relation)]) +
    ': ' + (e.reason || '') + ' (each underlying group keeps its own tag and decision)');
  var deferred = e.deferred || [];
  if (deferred.length) {
    html += scopeDeferredHtml(SCOPE_DEFERRED + ' (' + deferred.length + ' of ' + (e.members || deferred.length) + ')',
      SCOPE_DEFERRED + ': ' + deferred.join(', '));
  }
  return html;
}

function scopeSummaryHtml() {
  var block = (reportData && reportData.scopePolicy) || null;
  var line = block ? (block.policyLine || '') : SCOPE_LEGACY_LINE;
  var html = '<div class="scope-summary"><div class="scope-policy-line">' + escapeHtml(line) + '</div>';
  if (block) {
    var c = block.counts || {};
    html += '<div class="scope-counts">' +
      scopeBadgeHtml('in_scope', '', SCOPE_LABELS.in_scope) + ' ' + (c.in_scope || 0) + ' ' +
      scopeBadgeHtml('scope_extension', '', SCOPE_LABELS.scope_extension) + ' ' + (c.scope_extension || 0) + ' ' +
      scopeBadgeHtml('unclear', '', SCOPE_LABELS.unclear) + ' ' + (c.unclear || 0) +
      ' <span class="scope-count-note">(validated, distinct groups)</span>';
    if (block.effectivePolicy === 'preserve') {
      html += ' ' + scopeDeferredHtml(SCOPE_DEFERRED, SCOPE_DEFERRED) + ' ' + (c.deferred || 0);
    }
    html += '</div><div class="scope-legend">' + escapeHtml(String(block.legend || '').replace(/`/g, '')) + '</div>';
  }
  return html + '</div>';
}

// An edit changes the classification's proposal: re-render its tags in place.
function refreshScopeTags(suggestionId) {
  if (!reportData || !document.querySelectorAll) return;
  var seen = {};
  (reportData.groups || []).forEach(function(group) {
    var member = (group.suggestions || []).filter(function(s) { return s.id === suggestionId; })[0];
    if (!member) return;
    document.querySelectorAll('.scope-tags[data-scope-suggestion="' + scopeSelectorValue(suggestionId) + '"]').forEach(function(el) {
      el.innerHTML = scopeMemberBadges(member);
    });
    var key = group.groupHash || '';
    if (!key || seen[key]) return;
    seen[key] = true;
    document.querySelectorAll('.scope-tags[data-scope-group="' + scopeSelectorValue(key) + '"]').forEach(function(el) {
      el.innerHTML = scopeGroupBadges(group);
    });
    document.querySelectorAll('.scope-detail[data-scope-detail="' + scopeSelectorValue(key) + '"]').forEach(function(el) {
      el.innerHTML = scopeDetailBody(group);
    });
  });
}

// Selection files carry ids and choices only; a scope- or policy-like key
// in a stored or imported selection is dropped, never rendered or exported.
function stripScopeSelectionFields(parsed) {
  if (!parsed || typeof parsed !== 'object') return parsed;
  Object.keys(parsed).forEach(function(k) {
    var key = String(k).replace(/-/g, '_').toLowerCase();
    if (key.indexOf('scope') === 0 || key.indexOf('selected_remedy') === 0 || key.indexOf('selectedremedy') === 0) {
      delete parsed[k];
    }
  });
  return parsed;
}
// END SCOPE TAGS

// The flat and consolidated pages' summary panel.
function renderScopeSummary() {
  var container = document.getElementById('scope-summary');
  if (container) container.innerHTML = scopeSummaryHtml();
}
