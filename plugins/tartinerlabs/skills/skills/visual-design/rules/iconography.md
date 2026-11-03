---
title: Iconography
impact: LOW
tags: icons, icon-family, stroke, tab-bar, symbols
---

**Rule**: Use one icon family with a consistent stroke weight, fill style, and size steps. Default to the platform's own set.

**Evidence**: Users recognise familiar icons faster than custom ones (Nielsen Norman Group icon usability studies). Mixed stroke weights and styles read as visual noise even when users cannot say why.

### When Building

- **Platform set first**: SF Symbols on Apple platforms, Material Symbols on Android, and one library on the web or React Native (Lucide, Phosphor, Heroicons). Each has a consistent stroke and grid.
- **One style per context**: outline for inactive and filled for active (tab bars), or one weight throughout. Do not mix outline and filled at random.
- **Match icon weight to the text weight next to it.** SF Symbols do this automatically with text styles. Elsewhere, set the stroke so icons do not look thinner or heavier than their labels.
- **Size steps tied to the type scale**, typically two or three sizes.
- **Tinted icon tiles** (an icon on a 12–16% tint of a category colour) are a good way to carry category colour without using it on chrome (`rules/color.md`).
- **Custom icons** follow the chosen set's grid, stroke, and corner style.
- **Label unfamiliar icons.** Only a handful of icons are universally understood without a label.

### When Auditing

- Icons from two or more families on one screen
- Mixed outline and filled icons without a meaning (such as active state)
- Stroke weights visibly different from neighbouring text
- Emoji used as interface icons
- Many icon sizes with no scale

### Incorrect

```tsx
import { Home } from "lucide-react";
import { FaUser } from "react-icons/fa";
import SettingsIcon from "@mui/icons-material/Settings";
```

### Correct

```tsx
import { Home, User, Settings } from "lucide-react";
<Home size={24} strokeWidth={1.75} />
```

### Why This Matters

Icons appear on almost every screen. One consistent family is an easy win, and mismatched icons are an easy giveaway of an assembled UI.

### Alternatives

Character-led and Editorial products may use a custom hand-drawn icon set as part of their identity. Keep it consistent and keep system-level icons (share, back, close) recognisable.
