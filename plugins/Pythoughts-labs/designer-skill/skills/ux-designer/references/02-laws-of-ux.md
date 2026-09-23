# Laws of UX

Psychological principles that inform user experience design, collected and popularized by Jon Yablonski.

---

## Fitts's Law

> The time to acquire a target is a function of the distance to and size of the target.

**Formulated by:** Paul Fitts (1954)

### Key Implications

1. **Make important targets large** - Buttons, links, and interactive elements should be big enough to click/tap easily
2. **Reduce distance to targets** - Place frequently used actions near common cursor/finger positions
3. **Use screen edges and corners** - These are effectively infinite in size (cursor stops at edge)

### Application in UX

```
Good:
- Large, prominent CTAs
- Sticky navigation bars
- Context menus near cursor
- Floating action buttons on mobile

Avoid:
- Tiny click targets
- Important actions far from content
- Small close buttons on modals
```

### Minimum Target Sizes
- **Touch (mobile):** 44×44px (Apple) / 48×48dp (Material Design)
- **Mouse (desktop):** 24×24px minimum, 44×44px recommended
- **Spacing between targets:** 8px minimum

---

## Hick's Law (Hick-Hyman Law)

> The time it takes to make a decision increases with the number and complexity of choices.

**Formulated by:** William Edmund Hick & Ray Hyman (1952)

### Key Implications

1. **Limit choices** - Fewer options = faster decisions
2. **Group and categorize** - Break complex choices into simpler steps
3. **Highlight recommendations** - Guide users toward optimal choices
4. **Progressive disclosure** - Show only necessary options initially

### Application in UX

```
Good:
- "Top 10" lists on Netflix
- 3-4 pricing tiers
- Stepped forms/wizards
- Clear default selections

Avoid:
- Overwhelming dropdown menus
- Too many navigation items
- Endless feature lists
- Choice paralysis situations
```

### The Magic Number
Navigation menus should typically have **7±2 items** at the top level, though research suggests **4-5 items** may be optimal for quick scanning.

---

## Miller's Law

> The average person can only keep about 7 (±2) items in their working memory.

**Formulated by:** George A. Miller (1956)

### Key Implications

1. **Chunk information** - Group related items into meaningful units
2. **Limit simultaneous elements** - Don't overwhelm working memory
3. **Use recognizable patterns** - Familiar structures reduce memory load
4. **Provide external memory aids** - Let the interface remember for users

### Application in UX

```
Good:
- Phone numbers: (555) 123-4567
- Credit cards: 1234 5678 9012 3456
- Step indicators: Step 2 of 4
- Breadcrumb navigation

Avoid:
- Long strings of numbers/codes
- Too many form fields visible at once
- Complex multi-step processes without progress indication
```

---

## Jakob's Law

> Users spend most of their time on other sites. This means that users prefer your site to work the same way as all the other sites they already know.

**Named after:** Jakob Nielsen

### Key Implications

1. **Follow conventions** - Use established patterns users expect
2. **Don't reinvent the wheel** - Standard UI patterns exist for good reason
3. **Meet expectations** - Cart icon, hamburger menu, search bar placement
4. **Innovate carefully** - Novel interactions require learning investment

### Application in UX

```
Conventional Patterns:
- Logo in top-left links to home
- Shopping cart in top-right
- Search bar in header
- Footer contains legal/contact links
- Underlined text = hyperlink
- Blue links (or clearly styled alternatives)

Risky Innovations:
- Non-standard navigation placement
- Unusual scroll behaviors
- Custom cursor styles
- Non-standard form controls
```

---

## Peak-End Rule

> People judge an experience largely based on how they felt at its most intense point (peak) and at its end, rather than based on the sum of every moment.

**Formulated by:** Daniel Kahneman

### Key Implications

1. **Design memorable moments** - Create positive peaks in the experience
2. **End on a high note** - Final impressions disproportionately matter
3. **Manage low points** - Minimize negative peaks in user journeys
4. **Focus on key moments** - Not every interaction needs equal polish

### Application in UX

```
Positive Peaks:
- Delightful animations on success
- Personalized welcome messages
- Achievement celebrations
- Surprise and delight moments

Strong Endings:
- Clear confirmation of completed tasks
- Helpful "what's next" suggestions
- Thank you messages
- Easy save/export of results
```

---

## Tesler's Law (Law of Conservation of Complexity)

> For any system there is a certain amount of complexity which cannot be reduced. The question is: who deals with it—the user or the designer?

**Formulated by:** Larry Tesler

### Key Implications

1. **Absorb complexity** - Move complexity from users to the system
2. **Don't oversimplify** - Some complexity is inherent and necessary
3. **Smart defaults** - Handle common cases automatically
4. **Progressive disclosure** - Hide complexity until needed

### Application in UX

```
System absorbs complexity:
- Auto-detecting location
- Pre-filling forms with known data
- Smart suggestions and autocomplete
- Automatic formatting (dates, phone numbers)
- Intelligent defaults

Don't remove necessary complexity:
- Tax filing requires certain information
- Medical forms need complete details
- Security requires authentication steps
```

---

## Gestalt Principles

Principles of visual perception that explain how humans group visual elements.

### Proximity
Elements close together are perceived as related.

```
Use for:
- Grouping form fields
- Organizing navigation
- Creating visual sections
- Associating labels with inputs
```

### Similarity
Elements that look similar are perceived as related.

```
Use for:
- Consistent button styles
- Icon families
- Color coding categories
- Typography indicating function
```

### Continuity
Elements arranged in a line or curve are perceived as related.

```
Use for:
- Progress indicators
- Timelines
- Navigation flows
- Reading direction
```

### Closure
The mind fills in missing information to complete shapes.

```
Use for:
- Minimalist icons
- Loading indicators
- Implied boundaries
- Logo design
```

### Common Region
Elements within a boundary are perceived as grouped.

```
Use for:
- Card designs
- Form sections
- Modal dialogs
- Feature groupings
```

### Figure-Ground
The mind separates foreground from background.

```
Use for:
- Modal overlays
- Focus states
- Dropdown menus
- Image/text relationships
```

---

## Additional Important Laws

### Aesthetic-Usability Effect
Users often perceive aesthetically pleasing designs as more usable, even when they're not.

### Doherty Threshold
Productivity increases when computer and user interact at a pace (< 400ms) that ensures neither has to wait on the other.

### Law of Common Region
Elements tend to be perceived as groups if they share an enclosed area.

### Law of Prägnanz
People interpret ambiguous images as simple and complete.

### Mere Exposure Effect
The more exposure people have to something, the more they prefer it.

### Occam's Razor
Among competing hypotheses, the one with the fewest assumptions should be selected.

### Pareto Principle (80/20 Rule)
Roughly 80% of effects come from 20% of causes. Focus on the vital few features/screens.

### Postel's Law
Be liberal in what you accept and conservative in what you send.

### Serial Position Effect
Users best remember the first and last items in a series.

### Von Restorff Effect (Isolation Effect)
Items that stand out are more likely to be remembered.

### Zeigarnik Effect
People remember uncompleted tasks better than completed ones.

---

## Sources

- Yablonski, J. (2020). "Laws of UX: Using Psychology to Design Better Products & Services"
- [lawsofux.com](https://lawsofux.com/)
- Nielsen Norman Group research
- Kahneman, D. (2011). "Thinking, Fast and Slow"
