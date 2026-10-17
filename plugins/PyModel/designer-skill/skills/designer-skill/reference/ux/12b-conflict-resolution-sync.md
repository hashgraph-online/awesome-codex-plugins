# Collaborative UX: Conflict Resolution & Sync

This reference covers the technical and UX aspects of concurrent editing, conflict resolution, version control, sharing permissions, and offline synchronization in collaborative applications.

---

## Concurrent Editing

### Conflict Resolution Approaches

#### Operational Transformation (OT)

Used by Google Docs. Server-centric, transforms operations to maintain consistency.

```
User A types "Hello" at position 0
User B types "World" at position 0 (simultaneously)

Server transforms B's operation:
- B intended position 0
- A inserted 5 chars before B's cursor
- B's operation becomes: insert "World" at position 5

Result: "HelloWorld" (consistent for both)
```

**UX Implications:**
- Low-latency feel with optimistic updates
- Requires constant server connection
- Complex to implement correctly for rich content

#### CRDTs (Conflict-free Replicated Data Types)

Used by Figma, Notion. Mathematically guaranteed to converge.

```
Benefits:
- Works offline (sync when reconnected)
- No central server required
- Automatic conflict resolution

UX Benefits:
- True offline-first capability
- Peer-to-peer collaboration possible
- Seamless reconnection experience
```

### Component Locking

Prevent simultaneous edits on the same element.

```css
/* Locked component indicator */
.component--locked {
  outline: 2px dashed #6b7280;
  pointer-events: none;
  position: relative;
}

.component--locked::after {
  content: "🔒 Editing: " attr(data-locked-by);
  position: absolute;
  top: -24px;
  left: 0;
  background: #374151;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
```

#### Lock Timeout Pattern

```javascript
// Auto-release lock after inactivity
const LOCK_TIMEOUT = 60000; // 60 seconds
let lockTimer;

function refreshLock() {
  clearTimeout(lockTimer);
  lockTimer = setTimeout(() => {
    showDialog("Are you still editing? Lock will release in 30 seconds.");
    // If no response, release lock
  }, LOCK_TIMEOUT);
}
```

### Optimistic Updates

Apply changes locally before server confirmation.

```javascript
async function updateDocument(change) {
  // 1. Apply immediately (optimistic)
  applyLocalChange(change);
  updateUI();

  try {
    // 2. Send to server
    await sendToServer(change);
  } catch (error) {
    // 3. Rollback if failed
    revertLocalChange(change);
    showError("Failed to save. Your change was reverted.");
  }
}
```

### Merge Conflict UI

When automatic resolution isn't possible, provide clear conflict resolution.

```
┌─────────────────────────────────────────────────────────────┐
│ Conflict Detected                                           │
├─────────────────────────────────────────────────────────────┤
│ Your version          │ Server version      │ Merged        │
│ ─────────────────────│────────────────────│───────────────│
│ The quick brown fox  │ The slow brown fox │               │
│         ↓            │         ↓          │       ↓       │
│     [Accept]         │     [Accept]       │  [Edit & Save]│
└─────────────────────────────────────────────────────────────┘
```

**Best Practice:** Show differences side-by-side with accept/reject buttons for each conflicting section.

---

## Version Control & History

### Version History UI

```
┌──────────────────────────────────────────────────────────┐
│ Version History                                    [x]   │
├──────────────────────────────────────────────────────────┤
│ Current version                                          │
│ ├── Today, 3:45 PM - Alice (auto-saved)                 │
│ ├── Today, 2:30 PM - Bob "Added new section"            │
│ ├── Today, 11:00 AM - Alice "Initial draft"             │
│ ├── Yesterday, 4:00 PM - Carol (auto-saved)             │
│ └── Dec 15, 2024 - Document created                     │
│                                                          │
│ [Restore Selected]  [Compare with Current]               │
└──────────────────────────────────────────────────────────┘
```

### Multiplayer Undo/Redo

In collaborative environments, undo must be client-specific.

```javascript
// Each user has their own undo stack
class CollaborativeUndoManager {
  constructor(userId) {
    this.userId = userId;
    this.undoStack = [];
    this.redoStack = [];
  }

  execute(action) {
    // Record only this user's actions
    if (action.userId === this.userId) {
      this.undoStack.push(action);
      this.redoStack = []; // Clear redo on new action
    }
  }

  undo() {
    const action = this.undoStack.pop();
    if (action) {
      const inverseAction = action.inverse();
      this.redoStack.push(action);
      return inverseAction; // Apply to document
    }
  }
}
```

**Key Principle:** Users can only undo their own actions, not others'.

### Change Attribution

Show who changed what and when.

```css
/* Inline attribution on hover */
.text-block[data-author]::before {
  content: attr(data-author) " • " attr(data-edited);
  position: absolute;
  top: -20px;
  left: 0;
  font-size: 11px;
  color: #6b7280;
  opacity: 0;
  transition: opacity 150ms;
}

.text-block:hover::before {
  opacity: 1;
}

/* Author highlight colors */
.text-block[data-author="alice"] { border-left: 3px solid #e63946; }
.text-block[data-author="bob"] { border-left: 3px solid #2a9d8f; }
```

---

## Sharing & Permissions

### Invite Flow Patterns

#### Email Invitation

```
┌─────────────────────────────────────────────────────┐
│ Invite people                                       │
├─────────────────────────────────────────────────────┤
│ Email address                                       │
│ ┌─────────────────────────────────────────────────┐ │
│ │ alice@example.com                               │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Permission level                                    │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Can edit                              ▼         │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Add a message (optional)                            │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Here's the project we discussed...              │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│                              [Cancel] [Send Invite] │
└─────────────────────────────────────────────────────┘
```

#### Link Sharing

```
┌─────────────────────────────────────────────────────┐
│ Share via link                                      │
├─────────────────────────────────────────────────────┤
│ Anyone with the link                                │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Can view                              ▼         │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ https://app.example.com/doc/abc123...  [Copy]   │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ⚠️ Anyone with this link can access the document    │
└─────────────────────────────────────────────────────┘
```

### Permission Levels

| Level | Capabilities |
|-------|-------------|
| Owner | Full control, transfer ownership, delete |
| Admin | Manage members, edit settings, edit content |
| Editor | Edit content, add comments |
| Commenter | View content, add comments |
| Viewer | View only |

### Permission Dialog Pattern

```
┌─────────────────────────────────────────────────────────────┐
│ Share "Project Alpha"                                       │
├─────────────────────────────────────────────────────────────┤
│ People with access                                          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 👤 Alice (you)                     Owner           │   │ │
│ │ 👤 Bob                             Editor      [▼] │   │ │
│ │ 👤 Carol                           Viewer      [▼] │   │ │
│ │ 🔗 Anyone with link                Viewer      [▼] │   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [+ Add people]                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Offline & Sync

### Connection Status Indicators

```css
/* Connection status banner */
.connection-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  padding: 8px 16px;
  text-align: center;
  font-size: 14px;
  z-index: 9999;
}

.connection-banner--offline {
  background: #fef3c7;
  color: #92400e;
}

.connection-banner--syncing {
  background: #dbeafe;
  color: #1e40af;
}

.connection-banner--error {
  background: #fee2e2;
  color: #991b1b;
}
```

### Offline State Communication

```
┌─────────────────────────────────────────────────────────┐
│ ⚠️ You're offline                                        │
│ Changes will sync when you reconnect.                   │
│ Last synced: 2 minutes ago                    [Dismiss] │
└─────────────────────────────────────────────────────────┘
```

**Key Principles:**
- Avoid technical jargon ("no network connection" vs "offline")
- Show last sync time
- Indicate that work is safe
- Provide manual sync option when reconnected

### Sync Queue Visualization

```
┌─────────────────────────────────────────────────────────┐
│ Syncing 3 changes...                                    │
│ ████████████░░░░░░░░░░░░░░░░░░░                        │
│                                                         │
│ ✓ "Header updated"                                      │
│ ⟳ "Added new section"                                   │
│ ○ "Changed footer color"                                │
└─────────────────────────────────────────────────────────┘
```

### Reconnection Flow

```javascript
// Graceful reconnection
async function handleReconnection() {
  showBanner("Reconnecting...");

  try {
    // 1. Fetch remote changes
    const remoteChanges = await fetchChanges(lastSyncTimestamp);

    // 2. Merge with local changes
    const merged = mergeChanges(localQueue, remoteChanges);

    // 3. Apply merged state
    applyChanges(merged);

    // 4. Push local changes
    await pushLocalChanges(localQueue);

    showBanner("You're back online!", { duration: 3000 });
  } catch (error) {
    showBanner("Reconnection failed. Retrying...");
    scheduleRetry();
  }
}
```

---

## Key Metrics

| Metric | Value | Context |
|--------|-------|---------|
| Lock inactivity timeout | 60s | Before prompting release |
| Reconnection retry | 1s, 2s, 4s, 8s... | Exponential backoff |
| Optimistic timeout | 5-10s | Before showing sync error |

---

## Anti-Patterns

1. **No conflict prevention** - Simultaneous edits overwrite each other
2. **Silent failures** - Sync errors without user notification
3. **No offline indication** - Users think they're connected
4. **Permission confusion** - Unclear what each role can do
5. **Blocking on sync** - UI freezes during synchronization
6. **No undo attribution** - Users undo others' work accidentally

---

## Sources

- [Figma - Multiplayer Editing](https://www.figma.com/blog/multiplayer-editing-in-figma/)
- [CKEditor - Real-Time Collaboration Lessons](https://ckeditor.com/blog/lessons-learned-from-creating-a-rich-text-editor-with-real-time-collaboration/)
- [DEV - Building Collaborative Interfaces: OT vs CRDTs](https://dev.to/puritanic/building-collaborative-interfaces-operational-transforms-vs-crdts-2obo)
- [Liveblocks - Undo/Redo in Multiplayer](https://liveblocks.io/blog/how-to-build-undo-redo-in-a-multiplayer-environment)
- [A List Apart - Designing Offline-First](https://alistapart.com/article/offline-first/)
