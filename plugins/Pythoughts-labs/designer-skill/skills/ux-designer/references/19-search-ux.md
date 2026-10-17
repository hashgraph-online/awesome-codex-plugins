# Search UX

Search is a critical navigation pattern that goes beyond basic text matching. This reference covers search input design, autocomplete, faceted filtering, results display, and emerging AI-powered search patterns.

---

## Search Box Design

### Placement & Sizing

```
Top navigation (most common):
┌─────────────────────────────────────────────────────┐
│  Logo    [🔍 Search...                    ]   [User]│
└─────────────────────────────────────────────────────┘

Centered hero (landing pages / search-first apps):
┌─────────────────────────────────────────────────────┐
│                                                     │
│           What are you looking for?                 │
│     [🔍 Search products, brands, categories... ]    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Guidelines:**
- Minimum width: 300px (desktop), full-width on mobile
- Visible by default (not hidden behind an icon on desktop)
- Magnifying glass icon on the left (universal affordance)
- Clear/reset button (✕) appears when text is entered
- Search on Enter or with a submit button
- Consistent location across all pages

### Input Behavior

```html
<div class="search-container" role="search">
  <label for="search" class="sr-only">Search</label>
  <span class="search-icon" aria-hidden="true">🔍</span>
  <input
    id="search"
    type="search"
    placeholder="Search..."
    autocomplete="off"
    aria-expanded="false"
    aria-controls="search-results"
    aria-autocomplete="list"
  />
  <button class="clear-btn" aria-label="Clear search" hidden>✕</button>
</div>
```

- `type="search"` for native clear button on some browsers
- `role="search"` on the container for screen readers
- Focus on keyboard shortcut (/ or Ctrl+K is common)
- Show shortcut hint in the placeholder: "Search... (⌘K)"
- Debounce input: 200-300ms before triggering search
- Preserve query on back navigation

### Placeholder Text

```
❌ "Search..."  (too vague)
❌ "Type here to search for products, articles, help topics, and more..."  (too long)

✅ "Search products and articles..."  (specific, concise)
✅ "Search by name, email, or ID..."  (tells user what's searchable)
```

- Indicate what types of content are searchable
- Keep under 40 characters
- Don't rely on placeholder alone for labeling (accessibility)

---

## Autocomplete

### Suggestion Types

```
┌─────────────────────────────────────────┐
│  🔍  "react hook"                   [✕] │
├─────────────────────────────────────────┤
│  Recent searches                        │
│  🕐 react hooks tutorial                │
│  🕐 react context api                   │
├─────────────────────────────────────────┤
│  Suggestions                            │
│  🔍 react hooks best practices          │
│  🔍 react hook form                     │
│  🔍 react hooks vs classes              │
├─────────────────────────────────────────┤
│  Products                               │
│  📦 React Hook Form (library)     4.9★  │
│  📦 useHooks (collection)         4.7★  │
└─────────────────────────────────────────┘
```

**Suggestion categories:**
- **Recent searches**: User's own history (with clear history option)
- **Popular/trending**: Common searches from all users
- **Predictive**: Completions based on typing so far
- **Entity matches**: Direct links to specific results (products, people, pages)
- **Category suggestions**: "Search in Documentation" or "Search in Products"

### Keyboard Navigation

```
Tab / ↓     Move to suggestions dropdown
↑ / ↓       Navigate between suggestions
Enter       Select highlighted suggestion / submit search
Esc         Close dropdown, keep query text
→           Complete highlighted suggestion in input (Google-style)
```

- Highlight active suggestion visually
- Arrow keys should not move cursor in input while dropdown is open
- First suggestion can be auto-highlighted (or not — be consistent)
- Screen reader announcement of current suggestion

### Highlighting Matches

```
Searching for "des"
┌──────────────────────────┐
│ 🔍 **des**ign system      │   ← Bold matching portion
│ 🔍 **des**ktop app        │
│ 🔍 ui **des**ign patterns │
└──────────────────────────┘
```

- Bold or highlight the matching text portion
- Works with mid-word and multi-word matches
- Match highlighting in both suggestion text and description

### Performance

- Show suggestions after 1-2 characters minimum
- Debounce: 150-300ms after last keystroke
- Show loading indicator if search takes >300ms
- Cache recent suggestion results
- Maximum 7-10 suggestions visible (scroll for more)

---

## Faceted Search & Filters

### Filter Panel Layout

```
Desktop — Side panel:                Mobile — Bottom sheet:
┌──────────┬──────────────────┐     ┌──────────────────────┐
│ Filters  │ Results           │     │  Results (23)        │
│          │                   │     │  [🔽 Filter & Sort]  │
│ Category │                   │     └──────────────────────┘
│ ☑ Books  │ 23 results        │            ↓ (tap)
│ ☐ Video  │                   │     ┌──────────────────────┐
│ ☐ Audio  │ ┌──────────────┐  │     │  ── Filters ──       │
│          │ │ Result 1     │  │     │  Category ▾           │
│ Price    │ │ Result 2     │  │     │  Price Range ▾        │
│ $0-$25   │ │ Result 3     │  │     │  Rating ▾             │
│ $25-$50  │ └──────────────┘  │     │                      │
│          │                   │     │ [Reset] [Apply (23)] │
└──────────┴──────────────────┘     └──────────────────────┘
```

### Active Filter Chips

```
┌─────────────────────────────────────────────────────┐
│  Active: [Category: Books ✕] [Price: $0-$25 ✕]     │
│          [Rating: 4+ stars ✕]   [Clear all filters]  │
├─────────────────────────────────────────────────────┤
│  23 results for "design patterns"                   │
```

- Show all active filters as removable chips above results
- Individual remove (✕) on each chip
- "Clear all filters" link when multiple are active
- Update result count in real-time as filters change
- Persist filter selections on back navigation

### Filter UX Patterns

| Filter Type | UI Pattern | Best For |
|-------------|-----------|----------|
| **Single select** | Radio buttons / dropdown | Category, sort order |
| **Multi select** | Checkboxes | Tags, sizes, colors |
| **Range** | Slider or min/max inputs | Price, date range |
| **Boolean** | Toggle switch | "In stock", "Free shipping" |
| **Text** | Search within filter | Long category lists |
| **Color** | Color swatches | Product colors |
| **Rating** | Star row (clickable) | Minimum rating |

### Filter Counts

```
Category
☐ Books (156)
☐ Video (43)
☐ Audio (12)
☐ Courses (0)    ← Gray out or hide zero-count options
```

- Show result count per filter option
- Update counts as other filters are applied
- Gray out (don't hide) zero-count options to prevent layout shift
- Option: hide zero-count in secondary/collapsed filters

---

## Search Results

### Result Layout

```
┌─────────────────────────────────────────────────────┐
│  About 23 results for "design patterns" (0.12s)     │
│  Showing results from: [All ▾]                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  📄 Design Patterns: Elements of Reusable Software  │
│  www.example.com/books/design-patterns              │
│  The definitive guide to **design** **patterns**    │
│  in object-oriented programming. Covers 23          │
│  fundamental **patterns**...                        │
│  ⭐⭐⭐⭐⭐ (2,341 reviews)  •  Books  •  $45.99     │
│                                                     │
│  📄 UI Design Patterns — Best Practices             │
│  www.example.com/articles/ui-patterns               │
│  A collection of common UI **design** **patterns**  │
│  for web and mobile applications...                 │
│  Articles  •  Free  •  Updated 2 days ago           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Result item components:**
- Title (linked, keyword-highlighted)
- URL/breadcrumb path
- Snippet with highlighted matching terms
- Metadata (rating, category, date, price)
- Thumbnail image (when available)

### Result Sorting

```
Sort by: [Relevance ▾]
  • Relevance (default)
  • Newest first
  • Oldest first
  • Price: Low to High
  • Price: High to Low
  • Rating: High to Low
  • Most Popular
```

- Default to relevance for text searches
- Default to newest for browsing/feed contexts
- Show current sort prominently
- Changing sort should not clear filters

### Result Grouping

```
All (23) | Articles (12) | Products (8) | People (3)

─── Articles ───────────────────
  📄 UI Design Patterns...
  📄 Design Thinking...

─── Products ──────────────────
  📦 Design Patterns Book...
  📦 Pattern Library Tool...
```

- Group by content type when searching across multiple types
- Tab navigation between groups
- Show count per group
- "All" tab shows mixed results with type indicators

---

## Zero Results

### Helpful Messaging

```
┌─────────────────────────────────────────┐
│  No results for "dezign paterns"        │
│                                         │
│  Did you mean: design patterns?         │
│                                         │
│  Suggestions:                           │
│  • Check your spelling                  │
│  • Try more general keywords            │
│  • Try fewer keywords                   │
│                                         │
│  Popular searches:                      │
│  [UX design] [Typography] [Color theory]│
│                                         │
│  Or browse categories:                  │
│  [Books] [Articles] [Courses]           │
└─────────────────────────────────────────┘
```

**Zero results checklist:**
- [ ] Spelling suggestion ("Did you mean...?")
- [ ] Actionable tips (fewer keywords, check spelling)
- [ ] Alternative queries or popular searches
- [ ] Category browsing links
- [ ] Contact support or request option
- [ ] Never show a completely blank page

---

## Advanced Search

### Query Syntax

```
Common query operators (if supported, document them):
  "exact phrase"     — Match exact phrase
  term1 AND term2    — Both terms required
  term1 OR term2     — Either term
  -excluded          — Exclude term
  field:value        — Search specific field
  type:article       — Filter by content type
```

- Don't require advanced syntax — it should enhance, not replace basic search
- Show syntax guide as a help tooltip or link
- Parse common natural language queries intelligently

### Saved Searches

```
┌─ Saved Searches ────────────────────────┐
│  🔖 "react hooks" in:docs               │
│  🔖 "bugs" type:issue status:open        │
│  🔖 author:me modified:last-week         │
│                                          │
│  [+ Save current search]                 │
└──────────────────────────────────────────┘
```

- Allow saving complex filter + query combinations
- Accessible from search interface
- Named searches with optional notifications (alert on new results)
- Shareable search links

---

## Voice Search

### Microphone Button

```
┌─────────────────────────────────────────┐
│  🔍  Search...                    [🎤]  │
└─────────────────────────────────────────┘
           ↓ (tap microphone)
┌─────────────────────────────────────────┐
│  🎤  Listening...                       │
│       🔴 ∿∿∿∿∿∿∿∿∿∿                    │
│            [Cancel]                      │
└─────────────────────────────────────────┘
           ↓ (speech detected)
┌─────────────────────────────────────────┐
│  🔍  "best design patterns for"  [✕]   │
│       Transcribing...                   │
└─────────────────────────────────────────┘
```

- Show waveform or animation during listening
- Display transcription in real-time
- Allow editing before submitting
- "Cancel" to stop without searching
- Handle no-speech-detected timeout gracefully

---

## AI-Powered Search

### Natural Language Queries

```
Traditional search:      "return policy days limit"
AI-powered search:       "How many days do I have to return an item?"
                              ↓
┌─────────────────────────────────────────┐
│  📍 Quick Answer                        │
│  You have 30 days from purchase to      │
│  return most items for a full refund.   │
│  Exceptions apply for electronics (15   │
│  days) and final sale items.            │
│                                         │
│  Source: Return Policy FAQ              │
│  [View full policy]                     │
├─────────────────────────────────────────┤
│  Related results:                       │
│  📄 Return Policy...                    │
│  📄 How to Start a Return...            │
│  📄 Refund Processing Times...          │
└─────────────────────────────────────────┘
```

### AI Search Patterns

- **Direct answer**: Synthesized answer at top, traditional results below
- **Source attribution**: Every AI answer links to source documents
- **Confidence**: Only show direct answer when confidence is high
- **Follow-up**: "Ask a follow-up question" for conversational refinement
- **Fallback**: If AI can't answer, show traditional search results gracefully
- **Transparency**: "AI-generated answer" label clearly visible

### Semantic Search UX

- Understand synonyms and related concepts automatically
- "Showing results for X" when query is reinterpreted
- Allow explicit override: "Search instead for [exact query]"
- Explain why results are relevant when not keyword-obvious

---

## Key Metrics

| Metric | Target | Context |
|--------|--------|---------|
| Search success rate | > 70% | Users who find what they need |
| Zero results rate | < 10% | Queries returning nothing |
| Click-through rate | > 40% | Clicks on search results |
| Time to first click | < 10s | Speed of finding relevant result |
| Search exit rate | < 30% | Users who leave after searching |
| Refinement rate | < 30% | Users who modify their query |
| Autocomplete usage | > 30% | Suggestions selected |
| Queries per session | < 2 | Finding it on first try |

---

## Anti-Patterns

1. **Hidden search** — Search behind an icon on content-heavy sites
2. **No autocomplete** — Missing the most basic search enhancement
3. **Search that ignores typos** — No fuzzy matching or spell correction
4. **Results with no snippets** — Just titles with no context
5. **No empty state guidance** — "No results" with no help
6. **Filter clearing on new search** — Losing filter context on new query
7. **Slow autocomplete** — Suggestions that appear after the user finishes typing
8. **Non-persistent queries** — Search term cleared on back navigation
9. **Search that only matches titles** — Missing full-text search
10. **No result count** — Users can't gauge if their query is too broad or narrow

---

## Sources

- [Nielsen Norman Group: Search UX](https://www.nngroup.com/topic/search/) — Usability research
- [Baymard Institute: Search UX](https://baymard.com/blog/categories/search) — E-commerce search patterns
- [Algolia: Search UX Best Practices](https://www.algolia.com/blog/) — Search implementation
- [Google Search Central: Search Guidelines](https://developers.google.com/search) — Search quality
- [WAI-ARIA: Combobox Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/) — Accessible autocomplete
- [Elasticsearch: Search UI](https://www.elastic.co/search-labs) — Search technology patterns
