# Accessibility — WCAG 2.1 AA Content Guide

## Text Content
- [ ] Reading level appropriate for audience (B2C: grade 6-8, B2B: grade 10-12)
- [ ] Plain language used (avoid jargon without explanation)
- [ ] Sentences average <20 words
- [ ] Paragraphs are short (2-4 sentences)
- [ ] Instructions don't rely solely on color, shape, or location ("click the red button")
- [ ] Abbreviations are explained on first use

## Images
- [ ] All informative images have descriptive alt text
- [ ] Alt text conveys the meaning/purpose of the image, not just description
- [ ] Decorative images have empty alt attributes (`alt=""`)
- [ ] Complex images (charts, infographics) have long descriptions
- [ ] Text is not embedded in images without an accessible alternative
- [ ] Images have sufficient contrast

### Alt Text Writing Guide
- **Informative image**: Describe what it shows and why it matters — "Bar chart showing email open rates declining from 22% to 18% over 6 months"
- **Functional image (button/link)**: Describe the action — "Submit contact form"
- **Decorative image**: Leave alt empty — `alt=""`
- **Complex image**: Provide long description nearby or via link — "See detailed data table below"

## Links
- [ ] Link text is descriptive (NOT "click here" or "read more")
- [ ] Links are distinguishable from surrounding text (not just by color)
- [ ] Links opening in new windows/tabs are indicated
- [ ] Links are keyboard-navigable

## Color & Contrast
- [ ] Text has minimum 4.5:1 contrast ratio against background (AA standard)
- [ ] Large text (18px+ or 14px+ bold) has minimum 3:1 contrast ratio
- [ ] Information is not conveyed by color alone
- [ ] UI components have minimum 3:1 contrast ratio

## Headings & Structure
- [ ] Heading hierarchy is logical (H1 → H2 → H3, no skipped levels)
- [ ] Only one H1 per page
- [ ] Headings describe the content that follows
- [ ] Lists use proper HTML list elements

## Video & Audio
- [ ] Videos have accurate captions (auto-captions reviewed for errors)
- [ ] Pre-recorded audio has transcripts available
- [ ] Video descriptions available for visual-only information
- [ ] Auto-play is avoided; if used, can be paused/stopped

## Email Accessibility
- [ ] Single-column layout (no multi-column that breaks on screen readers)
- [ ] Font size minimum 14px for body text
- [ ] CTA buttons have descriptive text (not just "Click Here")
- [ ] Alt text on all images (email clients block images by default)
- [ ] Plain-text version available
- [ ] Preheader text is meaningful
- [ ] Tables used for layout have `role="presentation"`

## Social Media Accessibility
- [ ] **Instagram/Facebook**: Alt text added to images (use built-in tool)
- [ ] **Twitter/X**: Image descriptions enabled and used
- [ ] **Video**: Captions on all video content (especially TikTok, Reels)
- [ ] **Hashtags**: CamelCase for multi-word tags (#DigitalMarketing not #digitalmarketing)
- [ ] **Emoji**: Used sparingly, not replacing words, not clustered

## Inclusive Language
- [ ] Disability: Use person-first or identity-first per community preference
- [ ] Gender: Use inclusive terms unless specifically relevant
- [ ] Age: Avoid ageist assumptions or stereotypes
- [ ] Culture: Avoid idioms that don't translate across cultures
- [ ] Socioeconomic: Don't assume access to specific technology or resources

## Testing
- **Contrast checker**: WebAIM Contrast Checker
- **Screen reader testing**: NVDA (Windows, free), VoiceOver (Mac/iOS, built-in)
- **Readability**: Hemingway Editor, textstat library
- **Full audit**: WAVE, axe DevTools, Lighthouse accessibility score
