# Core UX Principles & Usability Heuristics

## Nielsen's 10 Usability Heuristics

Jakob Nielsen's heuristics are fundamental principles for interaction design, refined over decades of usability research.

### 1. Visibility of System Status
The design should always keep users informed about what is going on, through appropriate feedback within a reasonable amount of time.

**Implementation:**
- Show loading states and progress indicators
- Confirm successful actions (saves, submissions)
- Display current location in navigation
- Show real-time status of processes

### 2. Match Between System and the Real World
The design should speak the users' language. Use words, phrases, and concepts familiar to the user, rather than internal jargon.

**Implementation:**
- Use plain language, not technical terms
- Follow real-world conventions (calendar layouts, folder metaphors)
- Order information logically (chronological, alphabetical)
- Use familiar icons and symbols

### 3. User Control and Freedom
Users often perform actions by mistake. They need a clearly marked "emergency exit" to leave the unwanted action without having to go through an extended process.

**Implementation:**
- Provide undo/redo functionality
- Include clear cancel buttons
- Allow easy navigation back
- Support exiting flows at any point
- Auto-save work when possible

### 4. Consistency and Standards
Users should not have to wonder whether different words, situations, or actions mean the same thing. Follow platform and industry conventions.

**Implementation:**
- Use consistent terminology throughout
- Maintain uniform visual design (colors, fonts, spacing)
- Follow platform conventions (iOS, Android, Web)
- Reuse the same components for similar functions

### 5. Error Prevention
Good error messages are important, but the best designs carefully prevent problems from occurring in the first place.

**Implementation:**
- Use constraints to prevent invalid input
- Provide confirmation dialogs for destructive actions
- Offer suggestions and autocomplete
- Disable unavailable options rather than showing errors after
- Use sensible defaults

### 6. Recognition Rather Than Recall
Minimize the user's memory load by making elements, actions, and options visible. Users should not have to remember information from one part of the interface to another.

**Implementation:**
- Show recently used items
- Provide contextual help and hints
- Display options visibly instead of requiring memorization
- Use descriptive labels, not codes
- Maintain visible navigation breadcrumbs

### 7. Flexibility and Efficiency of Use
Shortcuts—hidden from novice users—can speed up the interaction for expert users. Allow users to tailor frequent actions.

**Implementation:**
- Provide keyboard shortcuts
- Allow customization of interface
- Support both simple and advanced modes
- Remember user preferences
- Enable batch operations

### 8. Aesthetic and Minimalist Design
Interfaces should not contain information which is irrelevant or rarely needed. Every extra unit of information competes with relevant information and diminishes visibility.

**Implementation:**
- Remove unnecessary elements
- Use progressive disclosure
- Prioritize important content
- Use whitespace effectively
- Avoid decorative clutter

### 9. Help Users Recognize, Diagnose, and Recover from Errors
Error messages should be expressed in plain language (no error codes), precisely indicate the problem, and constructively suggest a solution.

**Implementation:**
- Write human-readable error messages
- Explain what went wrong specifically
- Suggest how to fix the problem
- Avoid technical jargon and error codes
- Place errors near the relevant field

### 10. Help and Documentation
It's best if the system doesn't need any additional explanation. However, it may be necessary to provide documentation to help users complete their tasks.

**Implementation:**
- Provide contextual help (tooltips, inline hints)
- Make help searchable
- Focus documentation on user tasks
- List concrete steps
- Keep help concise and scannable

---

## Core Design Principles

### Clarity
Users should never have to stop and think about what something means or how to use it.

- Use clear, descriptive labels
- Avoid ambiguous icons without labels
- Make clickable elements look clickable
- Distinguish between primary and secondary actions

### Simplicity
Remove everything that isn't essential to the user's goal.

- Start with the minimum viable interface
- Add complexity only when proven necessary
- Hide advanced features behind progressive disclosure
- One primary action per screen

### Consistency
Predictability reduces cognitive load and learning time.

- Visual consistency (colors, typography, spacing)
- Functional consistency (same gestures = same results)
- Internal consistency (within your product)
- External consistency (with platform conventions)

### Feedback
Every user action should have an immediate, visible response.

- Instant feedback (< 100ms) for direct manipulation
- Progress indicators for operations > 1 second
- Clear success and error states
- Confirmation for important actions

### Hierarchy
Guide users' attention to what matters most.

- Visual weight indicates importance
- Size, color, and position create hierarchy
- Group related items together
- Separate distinct sections clearly

---

## User-Centered Design Fundamentals

### The UX Design Process

1. **Research** - Understand users, their goals, and context
2. **Define** - Synthesize findings into problems to solve
3. **Ideate** - Generate multiple possible solutions
4. **Prototype** - Create testable representations
5. **Test** - Validate with real users
6. **Implement** - Build the solution
7. **Iterate** - Continuously improve based on feedback

### Understanding Users

**User Research Methods:**
- User interviews
- Contextual inquiry
- Surveys and questionnaires
- Analytics analysis
- Usability testing
- A/B testing

**Key Questions:**
- Who are the users?
- What are their goals?
- What are their pain points?
- What is their context of use?
- What do they already know?

### Mental Models
Users approach your interface with expectations based on prior experience. Design should align with these mental models.

- Research how users think about the domain
- Use familiar patterns and metaphors
- When introducing new concepts, bridge from known ones
- Test assumptions about user understanding

---

## Visual Hierarchy Techniques

### Size
Larger elements attract more attention. Use size to indicate importance.

```
Heading 1 (32-48px) - Most important
Heading 2 (24-32px) - Section titles
Heading 3 (18-24px) - Subsections
Body text (16px) - Content
Small text (12-14px) - Metadata, captions
```

### Color
Color draws attention and conveys meaning.

- Use accent colors sparingly for important elements
- Maintain sufficient contrast (4.5:1 minimum)
- Don't rely on color alone to convey information
- Consider cultural color associations

### Position
Eye-tracking studies show predictable scanning patterns.

- F-pattern for text-heavy pages
- Z-pattern for minimal content
- Top-left receives most attention (LTR languages)
- Place critical elements in natural focal points

### Contrast
Difference creates emphasis.

- High contrast for important elements
- Low contrast for secondary information
- Use contrast in typography (bold, italic, size)
- Combine multiple contrast techniques

### Whitespace
Empty space is a design element, not wasted space.

- Creates breathing room
- Groups related elements
- Separates distinct sections
- Improves readability and comprehension

---

## Anti-Pattern Index

1. **Dark patterns** - Deceptive UI that tricks users → see [15-ethical-design.md](15-ethical-design.md)
2. **Infinite scroll without context** - No sense of progress → see [21-data-tables.md](21-data-tables.md)
3. **Hidden navigation** - Hamburger menus on desktop → see [05-information-architecture.md](05-information-architecture.md)
4. **Autoplaying media** - Unexpected sound/video → see [03-accessibility.md](03-accessibility.md)
5. **Disabled buttons without explanation** - Confusing blocked states → see [06-interaction-design.md](06-interaction-design.md)
6. **Walls of text** - No visual hierarchy or chunking → see [04-visual-design.md](04-visual-design.md)
7. **Color-only feedback** - Excludes colorblind users → see [03-accessibility.md](03-accessibility.md)
8. **Tiny touch targets** - Frustrating on mobile → see [08-mobile-ux.md](08-mobile-ux.md)
9. **No loading states** - Users think system is broken → see [22-performance-ux.md](22-performance-ux.md)
10. **Popup/modal overuse** - Interrupts user flow → see [06-interaction-design.md](06-interaction-design.md)
11. **No presence indicators** - Users don't know who else is working → see [12a-presence-awareness.md](12a-presence-awareness.md)
12. **Silent sync failures** - Data loss without warning → see [12b-conflict-resolution-sync.md](12b-conflict-resolution-sync.md)
13. **Cursor overload** - Too many live cursors create visual noise → see [12a-presence-awareness.md](12a-presence-awareness.md)
14. **Screen-center zoom** - Disorienting; zoom at cursor instead → see [13a-canvas-navigation.md](13a-canvas-navigation.md)
15. **No offline indication** - Users think they're connected when not → see [12b-conflict-resolution-sync.md](12b-conflict-resolution-sync.md)
16. **Hidden AI** - Users should always know when interacting with AI → see [14-ai-ux-patterns.md](14-ai-ux-patterns.md)
17. **Over-automation** - AI changes applied without user awareness or consent → see [14-ai-ux-patterns.md](14-ai-ux-patterns.md)
18. **No AI undo** - AI-applied changes must be reversible → see [14-ai-ux-patterns.md](14-ai-ux-patterns.md)
19. **Confirmshaming** - Guilt-laden language on decline buttons → see [15-ethical-design.md](15-ethical-design.md)
20. **Asymmetric consent** - Big "Accept" button, tiny "Reject" link → see [15-ethical-design.md](15-ethical-design.md)
21. **Mandatory lengthy tours** - Forcing users through 10+ onboarding steps → see [16-onboarding.md](16-onboarding.md)
22. **Notification carpet bombing** - Every event as a push notification → see [17-notifications.md](17-notifications.md)
23. **Permission on first visit** - Asking for push permission before user sees value → see [17-notifications.md](17-notifications.md)
24. **Hardcoded/untranslatable strings** - Text baked into code/images, fixed-width containers, LTR-only layout → see [23-internationalization.md](23-internationalization.md)
25. **Voice-only flows / hidden mic** - No fallback modality, no recognition feedback, buried voice entry → see [24-voice-and-multimodal.md](24-voice-and-multimodal.md)

## Sources

- Nielsen, J. (1994, 2020). "10 Usability Heuristics for User Interface Design"
- Norman, D. (2013). "The Design of Everyday Things"
- Krug, S. (2014). "Don't Make Me Think, Revisited"
- Nielsen Norman Group research articles
- [Laws of UX](https://lawsofux.com/) - Jon Yablonski
- [Nielsen Norman Group](https://www.nngroup.com/) - Usability research
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) - Accessibility guidelines
- [Material Design](https://m3.material.io/) - Google's design system
- [Human Interface Guidelines](https://developer.apple.com/design/) - Apple
- [Interaction Design Foundation](https://www.interaction-design.org/)
- [Liveblocks](https://liveblocks.io/) - Real-time collaboration patterns
- [Figma Engineering Blog](https://www.figma.com/blog/category/engineering/) - Multiplayer & canvas
- [Ably](https://ably.com/blog/collaborative-ux-best-practices) - Collaborative UX
- [Google PAIR Guidebook](https://pair.withgoogle.com/guidebook) - AI design patterns
- [Microsoft HAX Toolkit](https://www.microsoft.com/en-us/haxtoolkit/) - Human-AI interaction
- [Deceptive Design](https://www.deceptive.design/) - Dark pattern catalog
- [EU Digital Services Act](https://digital-strategy.ec.europa.eu/en/policies/digital-services-act-package) - Platform regulation
- [EU Accessibility Act](https://ec.europa.eu/social/main.jsp?catId=1202) - EN 301 549 / WCAG 2.1 AA mandate
- [W3C Internationalization (i18n) Activity](https://www.w3.org/International/) - i18n/l10n standards
- [Baymard Institute](https://baymard.com/) - E-commerce UX research
- [Edward Tufte](https://www.edwardtufte.com/) - Data visualization
- [ColorBrewer](https://colorbrewer2.org/) - Colorblind-safe palettes
- [The A11y Project](https://www.a11yproject.com/) - Accessibility community resource
- [web.dev](https://web.dev/) - Core Web Vitals and performance UX
- [Smashing Magazine](https://www.smashingmagazine.com/) - Practical UX/UI patterns
