# Collaborative UX: Presence & Awareness

Real-time collaboration UX focuses on enabling multiple users to work together seamlessly in shared digital spaces. Good collaborative UX creates "social translucence"—the ability to see and feel others' activities within digital environments.

---

## Presence & Awareness

Awareness is "an understanding of the activities of others, which provides a context for your own activity" (Dourish & Bellotti, 1992).

### Live Cursors

Live cursors show the real-time pointer position of collaborators, creating a sense of shared presence.

```css
/* Live cursor component */
.live-cursor {
  position: absolute;
  pointer-events: none;
  z-index: 1000;
  transition: transform 50ms linear; /* Smooth interpolation */
}

.live-cursor__pointer {
  width: 20px;
  height: 20px;
  /* Each user gets unique color */
}

.live-cursor__label {
  position: absolute;
  left: 16px;
  top: 16px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  color: white;
  /* Background matches cursor color */
}
```

#### Best Practices

| Aspect | Recommendation |
|--------|---------------|
| Label length | Max 12 characters, truncate with ellipsis |
| Color assignment | Unique per user, consistent across session |
| Update frequency | 50-100ms for smooth movement |
| Visibility | Hide after 30-60s of inactivity |
| Scaling | Consider hiding cursors at extreme zoom levels |

#### When Cursors Become Too Many

```
1-5 users    → Show all cursors with labels
6-10 users   → Show cursors, abbreviated labels
11-20 users  → Show cursors without labels
20+ users    → Consider hiding distant cursors or showing only nearby
```

### Avatar Stacks

Show who's currently viewing or editing a document.

```html
<div class="avatar-stack">
  <div class="avatar" style="background: #e63946;" title="Alice">A</div>
  <div class="avatar" style="background: #2a9d8f;" title="Bob">B</div>
  <div class="avatar" style="background: #e9c46a;" title="Carol">C</div>
  <div class="avatar-overflow">+3</div>
</div>
```

```css
.avatar-stack {
  display: flex;
  flex-direction: row-reverse; /* Newest on left */
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid white;
  margin-left: -8px; /* Overlap */
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.avatar-overflow {
  background: #6b7280;
  /* Same styling as .avatar */
}
```

#### Guidelines

- Show 3-5 avatars maximum before overflow
- Use "+N" pattern for additional users
- Clicking should reveal full list
- Consider adding online/away status indicators

### Typing Indicators

Show when collaborators are actively editing.

```javascript
// Typing indicator with debounce
let typingTimeout;

function handleInput() {
  broadcastTyping(true);
  clearTimeout(typingTimeout);
  typingTimeout = setTimeout(() => {
    broadcastTyping(false);
  }, 2000); // Stop after 2s of inactivity
}
```

```css
/* Typing indicator animation */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
}

.typing-indicator__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6b7280;
  animation: typing-bounce 1.4s infinite ease-in-out both;
}

.typing-indicator__dot:nth-child(1) { animation-delay: 0s; }
.typing-indicator__dot:nth-child(2) { animation-delay: 0.16s; }
.typing-indicator__dot:nth-child(3) { animation-delay: 0.32s; }

@keyframes typing-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}
```

### Activity Feeds

Show recent changes and who made them.

```
┌─────────────────────────────────────────────────────┐
│ Activity                                            │
├─────────────────────────────────────────────────────┤
│ 🟢 Alice edited "Header component"          2m ago  │
│ 🔵 Bob added comment on "Login flow"        5m ago  │
│ 🟡 Carol joined the document               12m ago  │
│ 🟢 Alice created "Footer component"        15m ago  │
└─────────────────────────────────────────────────────┘
```

---

## Communication Features

### Threaded Comments

```css
/* Comment thread styling */
.comment-thread {
  border-left: 3px solid #3b82f6;
  padding-left: 12px;
  margin: 8px 0;
}

.comment {
  padding: 8px;
  margin-bottom: 4px;
  background: #f3f4f6;
  border-radius: 8px;
}

.comment__header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.comment__reply-form {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e5e7eb;
}
```

### Contextual Comments (Annotations)

Pin comments to specific elements or canvas positions.

```javascript
// Attach comment to element
const annotation = {
  id: "comment-123",
  targetElement: "component-456",
  position: { x: 100, y: 50 }, // Relative to target
  thread: [
    { author: "alice", text: "Should this be blue?", timestamp: "..." },
    { author: "bob", text: "Good idea, updating now", timestamp: "..." }
  ],
  resolved: false
};
```

### Emoji Reactions

Quick feedback without requiring a full comment.

```html
<div class="reaction-bar">
  <button class="reaction" data-emoji="👍">👍 <span>3</span></button>
  <button class="reaction" data-emoji="❤️">❤️ <span>1</span></button>
  <button class="reaction" data-emoji="🎉">🎉 <span>2</span></button>
  <button class="reaction reaction--add">+</button>
</div>
```

### @Mentions

Notify specific collaborators.

```javascript
// Mention autocomplete
function handleMentionTrigger(text) {
  if (text.includes('@')) {
    const query = text.split('@').pop();
    const matches = collaborators.filter(c =>
      c.name.toLowerCase().includes(query.toLowerCase())
    );
    showMentionSuggestions(matches);
  }
}
```

### Anonymous Voting

Prevent groupthink by hiding voter identity.

```
┌───────────────────────────────────────────┐
│ Vote: Which design direction?             │
├───────────────────────────────────────────┤
│ Option A: Bold colors      ████████░░ 4   │
│ Option B: Minimal          ██████████ 5   │
│ Option C: Playful          ████░░░░░░ 2   │
├───────────────────────────────────────────┤
│ 11 votes total • Voting ends in 5:00      │
│ Your vote: Option B                       │
└───────────────────────────────────────────┘
```

---

## Viewport Coordination

### Follow Mode

Lock your viewport to follow another user's view.

```javascript
// Follow mode implementation
class ViewportFollower {
  constructor() {
    this.following = null;
  }

  follow(userId) {
    this.following = userId;
    this.showFollowingIndicator(userId);

    // Subscribe to their viewport changes
    subscribeToViewport(userId, (viewport) => {
      animateToViewport(viewport, { duration: 300 });
    });
  }

  stopFollowing() {
    this.following = null;
    this.hideFollowingIndicator();
    unsubscribeFromViewport();
  }
}
```

```css
/* Following indicator */
.viewport--following {
  border: 3px solid var(--user-color);
  border-radius: 8px;
}

.following-banner {
  position: fixed;
  top: 60px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 16px;
  background: var(--user-color);
  color: white;
  border-radius: 20px;
  font-size: 14px;
}
```

### Spotlight / Presenter Mode

Present to collaborators by controlling their view.

```
┌─────────────────────────────────────────────────────────┐
│ 🎯 Alice is presenting                                  │
│ Following her view • Click anywhere to stop    [Stop]   │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
1. Presenter clicks "Spotlight me"
2. All viewers receive notification
3. Viewers have 3-5 seconds to opt out
4. Non-opted-out viewers' viewports lock to presenter
5. Presenter's cursor becomes more prominent

### Jump to User

Navigate to where a collaborator is working.

```javascript
function jumpToUser(userId) {
  const userViewport = getUserViewport(userId);
  animateToViewport(userViewport, {
    duration: 500,
    easing: 'ease-out'
  });
  highlightUserCursor(userId, { duration: 2000 });
}
```

---

## Key Metrics

| Metric | Value | Context |
|--------|-------|---------|
| Cursor update rate | 50-100ms | Smooth movement perception |
| Typing indicator timeout | 2-3s | After last keystroke |
| Avatar stack max | 3-5 visible | Before "+N" overflow |
| Cursor label max | 12 chars | Truncate longer names |

---

## Anti-Patterns

1. **No presence indicators** - Users feel alone, cause conflicts
2. **Cursor overload** - Too many cursors create visual noise
3. **Forced following** - Lock users to presenter without consent
4. **Comment spam** - No way to resolve or archive discussions

---

## Sources

- [Liveblocks - Presence Documentation](https://liveblocks.io/presence)
- [Ably - Collaborative UX Best Practices](https://ably.com/blog/collaborative-ux-best-practices)
- [Figma - How Multiplayer Technology Works](https://www.figma.com/blog/how-figmas-multiplayer-technology-works/)
- Dourish, P. & Bellotti, V. (1992). "Awareness and Coordination in Shared Workspaces"
