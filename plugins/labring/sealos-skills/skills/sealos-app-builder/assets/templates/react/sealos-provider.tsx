'use client';

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { EVENT_NAME, type SessionV1 } from '@labring/sealos-desktop-sdk';
import { createSealosApp, sealosApp } from '@labring/sealos-desktop-sdk/app';

type SealosContextValue = {
  session: SessionV1 | null;
  language: string;
  loading: boolean;
  error: string | null;
  isInSealosDesktop: boolean;
};

const SealosContext = createContext<SealosContextValue>({
  session: null,
  language: 'en',
  loading: true,
  error: null,
  isInSealosDesktop: false
});

export function useSealos() {
  return useContext(SealosContext);
}

export function SealosProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<SessionV1 | null>(null);
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInSealosDesktop, setIsInSealosDesktop] = useState(false);

  useEffect(() => {
    const cleanupApp = createSealosApp();
    let cleanupEvent: (() => void) | undefined;
    let mounted = true;

    const bootstrap = async () => {
      try {
        const [nextSession, nextLanguage] = await Promise.all([
          sealosApp.getSession(),
          sealosApp.getLanguage()
        ]);

        if (!mounted) return;

        setSession(nextSession);
        setLanguage(nextLanguage.lng || 'en');
        setIsInSealosDesktop(true);
        setLoading(false);

        cleanupEvent = sealosApp.addAppEventListen(
          EVENT_NAME.CHANGE_I18N,
          (data: { currentLanguage?: string }) => {
            setLanguage(data.currentLanguage || 'en');
          }
        );
      } catch {
        if (!mounted) return;

        setError('This page is not running inside Sealos Desktop.');
        setIsInSealosDesktop(false);
        setLoading(false);
      }
    };

    bootstrap();

    return () => {
      mounted = false;
      cleanupEvent?.();
      cleanupApp?.();
    };
  }, []);

  return (
    <SealosContext.Provider
      value={{
        session,
        language,
        loading,
        error,
        isInSealosDesktop
      }}
    >
      {children}
    </SealosContext.Provider>
  );
}
