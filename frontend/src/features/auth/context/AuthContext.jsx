
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getCurrentUser,
  loginAccount,
  logoutAccount,
} from "../api/authApi";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const result = await getCurrentUser();
      setUser(result.user);
      return result.user;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    let active = true;

    getCurrentUser()
      .then((result) => {
        if (active) setUser(result.user);
      })
      .catch(() => {
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setChecking(false);
      });

    return () => {
      active = false;
    };
  }, []);

  // Remove the local authenticated view when SQL session expires.
  // The real authorization decision remains on the Backend.
  useEffect(() => {
    if (!user?.expiresAt) return;

    const remaining = Date.parse(user.expiresAt) - Date.now();

    if (!Number.isFinite(remaining)) return;

    const timeoutId = window.setTimeout(() => {
      setUser(null);
    }, Math.max(0, remaining));

    return () => window.clearTimeout(timeoutId);
  }, [user?.expiresAt]);

  const signIn = useCallback(async (credentials) => {
    const result = await loginAccount(credentials);
    setUser(result.user);
    return result.user;
  }, []);

  const signOut = useCallback(async () => {
    await logoutAccount();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      checking,
      signIn,
      signOut,
      refreshUser,
    }),
    [user, checking, signIn, signOut, refreshUser]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}
