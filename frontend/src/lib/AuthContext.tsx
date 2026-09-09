import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { setAccessToken } from "./api";
import { authApi, type TokenPair } from "./auth";

const REFRESH_TOKEN_KEY = "quotify-refresh-token";

type AuthState = {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (fields: { email: string; password: string; name: string }) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

function persistSession(tokens: TokenPair) {
  setAccessToken(tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

function clearSession() {
  setAccessToken(null);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // On load, trade a stored refresh token for a fresh session instead of forcing re-login.
  useEffect(() => {
    const stored = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!stored) {
      setIsLoading(false);
      return;
    }
    authApi
      .refresh(stored)
      .then((tokens) => {
        persistSession(tokens);
        setIsAuthenticated(true);
      })
      .catch(clearSession)
      .finally(() => setIsLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const tokens = await authApi.login(email, password);
    persistSession(tokens);
    setIsAuthenticated(true);
  }

  async function register(fields: { email: string; password: string; name: string }) {
    await authApi.register(fields);
    await login(fields.email, fields.password);
  }

  async function logout() {
    const stored = localStorage.getItem(REFRESH_TOKEN_KEY);
    clearSession();
    setIsAuthenticated(false);
    if (stored) await authApi.logout(stored).catch(() => {});
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
