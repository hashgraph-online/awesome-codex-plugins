# Theming — CSS variables, brand, light/dark

## How the kit is themed
Everything is CSS custom properties, prefixed `--cometchat-`. Override them anywhere that cascades to the kit — usually `styles.css`.

```css
/* styles.css */
:root {
  --cometchat-primary-color: #6851D6;
  --cometchat-neutral-color-300: #E8E8E8;
  --cometchat-border-color-default: #DCDCDC;
}
```
Register the kit stylesheet first (`angular.json` → `styles`), or there is nothing to override. Full token list: `{DOCS_BASE}/ui-kit/angular/customization/theming.md`.

## Light / dark — ThemeService applies, but does NOT persist
`ThemeService` (injectable, `providedIn: 'root'`) owns applying the theme: it sets a `currentTheme` signal, writes `data-theme` on `<html>` through the `DOCUMENT` token (SSR-safe), reads the OS `prefers-color-scheme` on construction, and keeps its own `matchMedia` listener so the UI follows the OS live.

> ⚠️ **Its docstrings are wrong about persistence — verified against the shipped 5.1.0 code.** `initFromPreference()` claims to read `localStorage` first; `setTheme()` and `toggleTheme()` claim to persist. **The class never touches `localStorage` at all** — `applyTheme()` only sets the signal and the attribute. A manual toggle is therefore **lost on reload**. Do not repeat the docstring's claim to the developer.

Follow the OS — this part works, one line at app start:
```ts
import { Component, inject } from '@angular/core';
import { ThemeService } from '@cometchat/chat-uikit-angular';

@Component({ selector: 'app-root', standalone: true, template: '<router-outlet />' })
export class AppComponent {
  constructor() { inject(ThemeService).initFromPreference(); }
}
```

### If the user needs a manual toggle that survives reload
Add **only** the missing persistence. Let the kit keep applying themes and watching the OS — a second `matchMedia` listener will drift from `currentTheme()`.

```ts
import { Injectable, inject, effect } from '@angular/core';
import { ThemeService } from '@cometchat/chat-uikit-angular';

const KEY = 'app.theme';

@Injectable({ providedIn: 'root' })
export class ThemePreference {
  private theme = inject(ThemeService);

  restore() {
    const saved = localStorage.getItem(KEY);
    if (saved === 'light' || saved === 'dark') this.theme.setTheme(saved);
  }
  set(next: 'light' | 'dark') {
    localStorage.setItem(KEY, next);
    this.theme.setTheme(next);
  }
  toggle() { this.set(this.theme.currentTheme() === 'dark' ? 'light' : 'dark'); }
}
```
Call `restore()` once at app start, **after** `initFromPreference()`, so a stored choice wins over the OS default. Route every user-facing toggle through `set()`/`toggle()` rather than `ThemeService` directly, or the write is skipped.

**Known residual, accepted:** if the OS theme changes while the app is open, the kit's own listener applies it and overrides a stored manual choice until the next reload — its "only follow system changes if the user has not set a manual preference" comment describes a check the code does not have. Fixing that from outside means racing the kit's listener, which is worse than the bug. Leave it.

`CometChatUIKit.themeMode` (`'light' | 'dark'`) still exists for a one-off set without DI, but `ThemeService` is the supported path.

## Scoping a theme to part of the app
Set the variables on a wrapper rather than `:root`:
```css
.cc-brand-dark { --cometchat-primary-color: #1B1B1B; }
```

## Do not
- Do not restyle kit internals with descendant selectors keyed on generated class names — they change between releases. Use the variables.
- Do not use `!important` to win against the kit; if a variable is not taking effect, the stylesheet is not registered or your rule is not in the cascade path.
