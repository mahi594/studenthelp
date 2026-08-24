"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { CurrentUser, getCurrentUser, isLoggedIn, logout as apiLogout } from "./api";

type AuthState = {
  user: CurrentUser | null;
  // True until the initial /auth/me check (or the "no token" short-circuit)
  // has resolved. Guards should not redirect while this is true, or a
  // logged-in user would get bounced to /login on every hard refresh.
  loading: boolean;
  isAdmin: boolean;
  isTpoOrAdmin: boolean;
  refresh: () => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  isAdmin: false,
  isTpoOrAdmin: false,
  refresh: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!isLoggedIn()) {
      setUser(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const me = await getCurrentUser();
      setUser(me);
    } catch {
      // Token missing/expired/invalid - treat as logged out rather than
      // leaving stale user state around.
      apiLogout();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  function logout() {
    apiLogout();
    setUser(null);
  }

  const isAdmin = user?.role === "admin";
  const isTpoOrAdmin = user?.role === "admin" || user?.role === "tpo_admin";

  return (
    <AuthContext.Provider value={{ user, loading, isAdmin, isTpoOrAdmin, refresh, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
