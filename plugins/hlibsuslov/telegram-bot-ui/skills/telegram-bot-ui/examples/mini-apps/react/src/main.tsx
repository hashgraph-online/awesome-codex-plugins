// Entry: initialise @tma.js/sdk once, mount the features we use, bind theme CSS variables, then render.
// Outside Telegram (a plain browser) init() throws: render an explanation instead of a broken screen.
import { createRoot } from 'react-dom/client';
import { StrictMode } from 'react';
import { backButton, hapticFeedback, init, isTMA, mainButton, miniApp, retrieveLaunchParams, themeParams, viewport } from '@tma.js/sdk-react';
import '../../_kit/tma.css';
import { App } from './App';

const root = createRoot(document.getElementById('root')!);

if (!isTMA()) {
  root.render(
    <main className="tma-page"><div className="tma-placeholder">
      <p className="tma-placeholder__title">Open this in Telegram</p>
      <p className="tma-placeholder__text">This page is a Telegram Mini App. Open it from the bot's menu button.</p>
    </div></main>,
  );
} else {
  init();
  // Each feature is mounted only where the client supports it (the SDK checks versions).
  if (backButton.mount.isAvailable()) backButton.mount();
  if (mainButton.mount.isAvailable()) mainButton.mount();
  if (miniApp.mount.isAvailable()) miniApp.mount();
  if (themeParams.mount.isAvailable()) themeParams.mount();
  // themeParams.bindCssVars() sets --tg-theme-*; the kit maps them to its roles.
  if (themeParams.bindCssVars.isAvailable()) themeParams.bindCssVars();
  if (miniApp.setHeaderColor.isAvailable()) miniApp.setHeaderColor('secondary_bg_color');
  if (miniApp.setBgColor.isAvailable()) miniApp.setBgColor('secondary_bg_color');
  document.documentElement.dataset.tmaScheme = themeParams.isDark() ? 'dark' : 'light';
  // Launch: the expanded sheet everywhere, fullscreen on iOS / Android where the client has it (8.0+). A refusal
  // (UNSUPPORTED, ALREADY_FULLSCREEN) keeps the expanded sheet. telegram-web-app.js sets --tg-safe-area-inset-* and
  // --tg-content-safe-area-inset-*, which the kit's --tma-safe-* add (references/mini-apps/launch-and-lifecycle.md).
  if (viewport.mount.isAvailable()) {
    void viewport.mount().then(() => {
      if (viewport.expand.isAvailable()) viewport.expand();
      const phone = ['ios', 'android'].includes(retrieveLaunchParams().tgWebAppPlatform);
      if (phone && viewport.requestFullscreen.isAvailable() && !viewport.isFullscreen()) {
        viewport.requestFullscreen().catch(() => {});
      }
    }).catch(() => {});
  }
  root.render(<StrictMode><App haptic={hapticFeedback} /></StrictMode>);
  miniApp.ready(); // the first screen renders synchronously: hide Telegram's loading screen
}
