# Information Architecture

Information Architecture (IA) is the structural design of shared information environments—how content is organized, labeled, and navigated.

---

## IA Fundamentals

### What is Information Architecture?

IA is the blueprint of a digital product, defining:
- How content is organized and categorized
- How users navigate between sections
- How information is labeled and described
- How users find what they're looking for

### Core Components

1. **Organization Systems** - How content is grouped
2. **Labeling Systems** - How content is named
3. **Navigation Systems** - How users move through content
4. **Search Systems** - How users find specific content

---

## Organization Structures

### Hierarchical (Tree)
Most common structure. Content flows from broad to specific.

```
Home
├── Products
│   ├── Category A
│   │   ├── Product 1
│   │   └── Product 2
│   └── Category B
├── About
└── Contact
```

**Best for:** E-commerce, documentation, corporate sites

### Sequential (Linear)
Content follows a specific order.

```
Step 1 → Step 2 → Step 3 → Step 4 → Done
```

**Best for:** Onboarding flows, tutorials, checkout processes

### Matrix
Multiple navigation paths to the same content.

```
Products can be accessed by:
- Category
- Brand
- Price range
- New arrivals
```

**Best for:** E-commerce, catalogs, databases

### Network (Web)
No fixed hierarchy; content interconnects freely.

```
Page A ←→ Page B
   ↕        ↕
Page C ←→ Page D
```

**Best for:** Wikis, knowledge bases, blogs

---

## Navigation Patterns

### Global Navigation

Consistent navigation across all pages.

```
Horizontal Navigation Bar:
┌────────────────────────────────────────┐
│ Logo   Home   Products   About   Contact│
└────────────────────────────────────────┘

Best for:
- Sites with 5-7 top-level sections
- Desktop-first designs
- Corporate/marketing sites
```

### Local Navigation

Section-specific navigation.

```
Sidebar Navigation:
┌──────────┬─────────────────┐
│ Section  │                 │
│ ├─ Page 1│    Content      │
│ ├─ Page 2│                 │
│ └─ Page 3│                 │
└──────────┴─────────────────┘

Best for:
- Documentation sites
- Admin dashboards
- Settings panels
```

### Contextual Navigation

Related content links within the page.

```
"Related Articles"
"Customers Also Bought"
"See Also"
```

### Utility Navigation

Functional links (login, cart, search, settings).

```
┌─────────────────────────────────────────┐
│                    Search 🔍  Cart 🛒  👤│
└─────────────────────────────────────────┘
```

### Hamburger Menu

Hidden navigation behind an icon (☰).

```
Pros:
- Saves space
- Clean interface
- Mobile-friendly

Cons:
- Reduces discoverability
- Adds interaction step
- Less suitable for desktop
```

### Bottom Navigation (Mobile)

Tab bar at bottom of screen.

```
┌─────────────────────────────────────┐
│                                     │
│              Content                │
│                                     │
├─────────────────────────────────────┤
│  🏠    🔍    ➕    ❤️    👤        │
│ Home  Search Add  Saved  Profile   │
└─────────────────────────────────────┘

Best for:
- Mobile apps
- 3-5 primary destinations
- Frequent navigation actions
```

### Breadcrumbs

Show the user's location in the hierarchy.

```
Home > Products > Electronics > Phones > iPhone

Best for:
- Deep hierarchies
- E-commerce
- When users may enter via search
```

---

## Labeling Best Practices

### Clarity Over Cleverness
```
Good: "Pricing"
Bad: "Investment Levels"

Good: "Contact Us"
Bad: "Let's Chat"

Good: "Settings"
Bad: "Command Center"
```

### Consistency
```
Consistent verb forms:
- Create Project
- Edit Project
- Delete Project

Not:
- New Project
- Edit Project
- Remove
```

### User Language
- Use terms users understand
- Test labels with real users
- Avoid internal jargon
- Research common search terms

### Scannability
- Front-load important words
- Keep labels short (1-3 words)
- Use parallel structure
- Differentiate clearly

---

## Search Design

### Search Box Best Practices

```html
<!-- Prominent, always visible -->
<form role="search">
  <label for="search" class="sr-only">Search</label>
  <input
    type="search"
    id="search"
    placeholder="Search products..."
    aria-label="Search products"
  />
  <button type="submit">
    <span class="sr-only">Search</span>
    🔍
  </button>
</form>
```

**Guidelines:**
- Place in expected location (header, top-right)
- Make it large enough to see query
- Use placeholder text to indicate scope
- Support autocomplete/suggestions
- Show recent searches

### Search Results

```
Essential elements:
- Number of results
- Sorting options
- Filters/facets
- Clear result snippets
- Query highlighting
- Pagination or infinite scroll
- "No results" helpful message
```

### Zero Results Page
```
"No results for 'xyz'"
- Check spelling
- Try different keywords
- Browse categories
- Contact support
```

---

## IA Research Methods

### Card Sorting

Users organize content into groups that make sense to them.

**Open Card Sort:**
- Users create their own category names
- Reveals mental models
- Good for new products

**Closed Card Sort:**
- Users sort into predefined categories
- Tests existing structure
- Good for validation

**Tools:** OptimalSort, Maze, physical cards

### Tree Testing

Test if users can find items in your proposed structure.

```
Task: "Find the return policy"

Structure:
- Home
  - Shop
  - Account
  - Help Center ← Target
    - Shipping
    - Returns ← Success
    - Contact
```

**Metrics:**
- Success rate
- Directness (first click correct)
- Time to complete

**Tools:** Treejack, UserZoom

### First-Click Testing

Measure where users first click to complete a task.

**Insight:** If the first click is wrong, only 46% eventually succeed.

---

## 2026 Trends

### AI-Powered IA
- Dynamic categorization based on user behavior
- Personalized navigation paths
- Predictive search and recommendations
- Auto-tagging and organization

### Voice and Conversational IA
- Structure content for voice interfaces
- Natural language navigation
- Question-based organization
- Conversational menus

### Zero UI
- Interfaces that anticipate needs
- Reduce navigation through prediction
- Ambient computing integration
- Context-aware content delivery

---

## IA Documentation

### Sitemap

Visual representation of page hierarchy.

```
Homepage
├── Products
│   ├── Category A
│   ├── Category B
│   └── All Products
├── About
│   ├── Our Story
│   ├── Team
│   └── Careers
├── Blog
│   ├── Article List
│   └── Single Article
└── Contact
```

**Tools:** Figma, XMind, Lucidchart, Slickplan

### Content Inventory

Spreadsheet of all existing content.

| URL | Title | Type | Owner | Last Updated | Action |
|-----|-------|------|-------|--------------|--------|
| /about | About Us | Page | Marketing | 2024-06 | Keep |
| /old-promo | Summer Sale | Landing | Marketing | 2023-08 | Delete |

### User Flow Diagrams

Map the paths users take through your product.

```
Entry → Landing Page → Product List → Product Detail
                ↓                         ↓
            Search          →      Add to Cart → Checkout → Success
                                       ↓
                                   Continue Shopping
```

---

## Common IA Mistakes

1. **Organizing by org structure** - Users don't know your departments
2. **Too deep** - More than 3-4 levels becomes unwieldy
3. **Too wide** - Too many top-level options overwhelms
4. **Duplicate content** - Same info in multiple places
5. **Vague labels** - "Resources," "Solutions," "Services"
6. **No search** - Users often prefer search
7. **Breaking conventions** - Cart not in top-right
8. **Mobile afterthought** - IA must work for all devices

---

## Sources

- Rosenfeld, L., Morville, P., & Arango, J. (2015). "Information Architecture: For the Web and Beyond"
- [Nielsen Norman Group - IA](https://www.nngroup.com/topic/information-architecture/)
- [Interaction Design Foundation - IA](https://www.interaction-design.org/literature/topics/information-architecture)
- [A List Apart - IA](https://alistapart.com/)
