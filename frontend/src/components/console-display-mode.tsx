"use client";

import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "fraudchecker.console.showAdvanced";

type ConsoleDisplayModeContextValue = {
  showAdvanced: boolean;
  setShowAdvanced: (value: boolean) => void;
  toggleShowAdvanced: () => void;
};

const ConsoleDisplayModeContext = createContext<ConsoleDisplayModeContextValue | null>(null);

type ConsoleDisplayModeProviderProps = {
  children: ReactNode;
  initialShowAdvanced?: boolean;
};

export function ConsoleDisplayModeProvider({
  children,
  initialShowAdvanced,
}: ConsoleDisplayModeProviderProps) {
  const [showAdvanced, setShowAdvanced] = useState(initialShowAdvanced ?? false);
  const [hydrated, setHydrated] = useState(initialShowAdvanced !== undefined);

  useEffect(() => {
    if (initialShowAdvanced !== undefined) {
      return;
    }
    try {
      setShowAdvanced(window.localStorage.getItem(STORAGE_KEY) === "true");
    } catch {
      setShowAdvanced(false);
    } finally {
      setHydrated(true);
    }
  }, [initialShowAdvanced]);

  useEffect(() => {
    if (!hydrated || initialShowAdvanced !== undefined) {
      return;
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, showAdvanced ? "true" : "false");
    } catch {
      // Ignore storage errors and keep the in-memory preference.
    }
  }, [hydrated, initialShowAdvanced, showAdvanced]);

  const value = useMemo<ConsoleDisplayModeContextValue>(
    () => ({
      showAdvanced,
      setShowAdvanced,
      toggleShowAdvanced: () => setShowAdvanced((current) => !current),
    }),
    [showAdvanced],
  );

  return <ConsoleDisplayModeContext.Provider value={value}>{children}</ConsoleDisplayModeContext.Provider>;
}

export function useConsoleDisplayMode() {
  return (
    useContext(ConsoleDisplayModeContext) ?? {
      showAdvanced: false,
      setShowAdvanced: () => undefined,
      toggleShowAdvanced: () => undefined,
    }
  );
}
