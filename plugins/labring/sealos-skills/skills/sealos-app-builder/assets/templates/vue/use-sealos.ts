import { onMounted, onUnmounted, readonly, ref } from 'vue';
import { EVENT_NAME, type SessionV1 } from '@labring/sealos-desktop-sdk';
import { createSealosApp, sealosApp } from '@labring/sealos-desktop-sdk/app';

const session = ref<SessionV1 | null>(null);
const language = ref('en');
const loading = ref(true);
const error = ref<string | null>(null);
const isInSealosDesktop = ref(false);

let cleanupApp: (() => void) | undefined;
let cleanupEvent: (() => void) | undefined;
let initialized = false;

async function bootstrap() {
  try {
    const [nextSession, nextLanguage] = await Promise.all([
      sealosApp.getSession(),
      sealosApp.getLanguage()
    ]);

    session.value = nextSession;
    language.value = nextLanguage.lng || 'en';
    isInSealosDesktop.value = true;
    loading.value = false;

    cleanupEvent = sealosApp.addAppEventListen(
      EVENT_NAME.CHANGE_I18N,
      (data: { currentLanguage?: string }) => {
        language.value = data.currentLanguage || 'en';
      }
    );
  } catch {
    error.value = 'This page is not running inside Sealos Desktop.';
    isInSealosDesktop.value = false;
    loading.value = false;
  }
}

export function useSealos() {
  onMounted(() => {
    if (initialized) return;

    cleanupApp = createSealosApp();
    initialized = true;
    bootstrap();
  });

  onUnmounted(() => {
    cleanupEvent?.();
    cleanupApp?.();
    cleanupEvent = undefined;
    cleanupApp = undefined;
    initialized = false;
  });

  return {
    session: readonly(session),
    language: readonly(language),
    loading: readonly(loading),
    error: readonly(error),
    isInSealosDesktop: readonly(isInSealosDesktop)
  };
}
