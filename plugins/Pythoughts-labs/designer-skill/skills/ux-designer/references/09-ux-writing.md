# UX Writing & Microcopy

UX writing is the practice of crafting user-facing text that helps people use digital products. Every word in an interface is designed to enhance the user experience.

---

## What is Microcopy?

Microcopy refers to the small bits of text throughout an interface:
- Button labels
- Error messages
- Form labels and hints
- Tooltips
- Empty states
- Confirmation messages
- Loading text
- Navigation labels
- Onboarding text

### The Impact of Microcopy

Good microcopy:
- Reduces user errors
- Increases conversion rates
- Builds trust and brand personality
- Decreases support requests
- Guides users through complex tasks

---

## Core Principles

### Clarity

Users should instantly understand what they're reading.

```
Good: "Delete this file?"
Bad: "Are you sure you wish to proceed with the deletion of the selected item?"

Good: "Sign up"
Bad: "Get started on your journey"

Good: "Saved"
Bad: "Your changes have been successfully persisted to the database"
```

### Conciseness

Use the fewest words needed to communicate clearly.

```
Good: "Password must be 8+ characters"
Bad: "Please ensure that your password contains a minimum of eight characters"

Good: "Email sent"
Bad: "Your email has been sent successfully"
```

### Usefulness

Every word should help the user accomplish their goal.

```
Good: "Enter the 6-digit code from your authenticator app"
Bad: "Enter code"

Good: "We'll email you a receipt"
Bad: "Transaction complete"
```

### Conversational (But Professional)

Write like you speak, while maintaining appropriateness.

```
Good: "Looks like that email doesn't exist. Want to create an account?"
Bad: "Error 404: User not found in database"

Good: "We couldn't find any results for 'xyz'"
Bad: "Your search query returned zero results"
```

---

## Voice and Tone

### Voice vs. Tone

**Voice** = Your brand's personality (consistent)
**Tone** = How you adapt to context (varies)

```
Voice: Friendly, helpful, professional
Tone varies:
- Onboarding: Welcoming, encouraging
- Errors: Empathetic, solution-focused
- Success: Celebratory (subtly)
- Security: Serious, trustworthy
```

### Developing Brand Voice

Document your voice characteristics:

| Attribute | We are... | We are NOT... |
|-----------|-----------|---------------|
| Friendly | Warm, approachable | Overly casual, unprofessional |
| Helpful | Clear, guiding | Condescending, verbose |
| Confident | Assured, direct | Arrogant, pushy |
| Human | Conversational, real | Robotic, corporate |

### Adapting Tone

```
Context: Error Message
Voice: Helpful
Tone: Empathetic + Solution-focused

"Something went wrong on our end. We're looking into it.
Your work has been saved—you won't lose anything."
```

---

## Writing for Common UI Elements

### Buttons

```
Good Button Labels:
- "Sign up" / "Log in" (standard actions)
- "Add to cart" / "Buy now" (specific actions)
- "Save changes" / "Save" (what happens)
- "Send message" (what it does)
- "Try free for 14 days" (value proposition)

Avoid:
- "Submit" (too generic)
- "Click here" (not descriptive, accessibility issue)
- "Yes" / "No" (require context)
- "OK" (too generic for important actions)
```

### Error Messages

```
Structure: What happened + How to fix it

Good:
"We couldn't log you in. Check your email and password and try again."

"That email is already registered. Log in or reset your password."

"Your card was declined. Try a different payment method."

Avoid:
"Error"
"Invalid credentials"
"Error 422: Unprocessable entity"
```

### Empty States

```
Components:
1. What this area is for
2. Why it's empty
3. How to fill it

Example:
"No projects yet

Projects help you organize your work. Create your first project
to get started.

[Create project]"
```

### Success Messages

```
Good:
"Password updated" ✓
"Order placed! We'll email you when it ships."
"Welcome aboard! Let's set up your workspace."

Keep it brief—user wants to move on.
Provide next steps when helpful.
```

### Loading States

```
Generic:
"Loading..."

Contextual (better):
"Finding nearby restaurants..."
"Saving your changes..."
"Connecting to server..."

Humorous (use carefully):
"Reticulating splines..."
"Convincing pixels to behave..."
```

### Confirmation Dialogs

```
Structure:
- Clear headline stating action
- Brief explanation of consequences
- Actionable button labels

Example:
"Delete this project?

This will permanently delete 'Marketing Q4' and all its files.
This can't be undone.

[Cancel] [Delete project]"

Not:
"Are you sure?"
[Yes] [No]
```

---

## Form Copy

### Labels

```
Good:
"Email address"
"Password"
"First name"

Avoid:
"Your email address"
"Enter your password"
"Please provide first name"
```

### Placeholder Text

```
Use for examples, not labels:
"you@example.com"
"555-123-4567"
"Search products..."

Don't use as the only label (disappears on focus)
```

### Help Text

```
Place below input or as tooltip:
"Password must be at least 8 characters"
"We'll only contact you about your order"
"Optional—for faster shipping estimates"
```

### Validation Messages

```
Specific and helpful:
"Enter a valid email (e.g., name@company.com)"
"Phone number must be 10 digits"
"Passwords don't match"

Not:
"Invalid input"
"Please check this field"
"Error in form"
```

---

## Accessibility in Writing

### Link Text

```
Good:
"Read our privacy policy"
"Download the report (PDF, 2.3 MB)"
"Learn more about pricing"

Avoid:
"Click here"
"Read more"
"Here" (as standalone link)
```

### Alt Text

```
Informative images:
"Bar chart showing 40% increase in sales from Q3 to Q4 2024"

Decorative images:
alt="" (empty)

Functional images (buttons/links):
"Search" (not "magnifying glass icon")
```

### Headings

```
Use logical hierarchy for screen readers:
<h1>Account Settings</h1>
  <h2>Profile</h2>
  <h2>Security</h2>
    <h3>Password</h3>
    <h3>Two-factor authentication</h3>
```

---

## Localization Considerations

### Writing for Translation

```
Avoid idioms:
"Piece of cake" → "Easy"
"Kill two birds" → "Accomplish both"
"Ball is in your court" → "Your turn to decide"

Keep text expandable (30-40% expansion typical):
English: "Settings"
German: "Einstellungen"

Avoid text in images (can't be translated)

Don't embed variables mid-sentence:
"You have 5 messages" (number placement varies by language)
→ "Messages: 5"
```

### Cultural Sensitivity

- Date formats vary (MM/DD/YYYY vs. DD/MM/YYYY)
- Color meanings differ across cultures
- Gestures and icons may have different connotations
- Humor often doesn't translate

---

## AI Tools for UX Writing

### Content Generation

**ChatGPT / Claude:**
- Brainstorm alternative phrasings
- Generate variation options
- Check tone consistency

**Writer / Jasper:**
- Brand voice enforcement
- Style guide compliance
- Terminology consistency

### Quality Checking

**Grammarly:**
- Grammar and spelling
- Clarity suggestions
- Tone detection

**Hemingway Editor:**
- Readability score
- Sentence complexity
- Passive voice detection

### Important Note

AI is a co-pilot, not a replacement. Always:
- Review and edit AI suggestions
- Ensure brand voice consistency
- Test with real users
- Consider context AI might miss

---

## Testing Microcopy

### A/B Testing

Test button text:
```
A: "Sign up free"
B: "Get started"
C: "Create account"
```

Measure: Click-through rate, completion rate

### Usability Testing

- Can users complete the task?
- Do they understand what's happening?
- Any confusion or hesitation?
- What do they expect to happen next?

### Preference Testing

"Which of these messages is clearer?"
"Which feels more appropriate for this situation?"

---

## Content Design Process

### 1. Research
- Understand user needs and language
- Analyze existing content
- Review support tickets and FAQs
- Conduct user interviews

### 2. Strategy
- Define voice and tone
- Create content guidelines
- Map user journeys
- Identify content touchpoints

### 3. Write
- Draft multiple options
- Collaborate with design
- Iterate with feedback
- Consider edge cases

### 4. Validate
- Usability testing
- A/B testing
- Accessibility review
- Stakeholder review

### 5. Maintain
- Update as product evolves
- Track metrics
- Gather ongoing feedback
- Keep guidelines current

---

## Resources

### Books
- "Microcopy: The Complete Guide" - Kinneret Yifrah
- "Strategic Writing for UX" - Torrey Podmajersky
- "Conversational Design" - Erika Hall

### Courses
- UX Content Collective - UX Writing Fundamentals
- UX Writing Hub - UX Writing Academy
- Coursera - Microcopy & UX Writing

### Communities
- UX Writing Hub (Slack)
- Content Design (Slack)
- r/UXWriting (Reddit)

---

## Sources

- [UX Writing Hub](https://uxwritinghub.com/)
- [Nielsen Norman Group - Writing for the Web](https://www.nngroup.com/topic/writing-web/)
- [Google Design - Writing](https://design.google/library/ux-writing)
- [Shopify Polaris - Voice and Tone](https://polaris.shopify.com/foundations/voice-and-tone)
