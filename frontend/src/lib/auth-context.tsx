"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, RegisterInput, User } from "./api";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterInput) => Promise<void>;
  verifyEmail: (email: string, code: string) => Promise<void>;
  resetPassword: (email: string, code: string, newPassword: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const STORAGE_KEY = "ygt_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function restoreSession() {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) {
        setLoading(false);
        return;
      }
      setToken(stored);
      try {
        setUser(await api.me(stored));
      } catch {
        localStorage.removeItem(STORAGE_KEY);
        setToken(null);
      } finally {
        setLoading(false);
      }
    }
    restoreSession();
  }, []);

  async function login(email: string, password: string) {
    const { access_token } = await api.login(email, password);
    localStorage.setItem(STORAGE_KEY, access_token);
    setToken(access_token);
    setUser(await api.me(access_token));
  }

  async function register(data: RegisterInput) {
    await api.register(data);
  }

  async function verifyEmail(email: string, code: string) {
    const { access_token } = await api.verifyEmail(email, code);
    localStorage.setItem(STORAGE_KEY, access_token);
    setToken(access_token);
    setUser(await api.me(access_token));
  }

  async function resetPassword(email: string, code: string, newPassword: string) {
    const { access_token } = await api.resetPassword(email, code, newPassword);
    localStorage.setItem(STORAGE_KEY, access_token);
    setToken(access_token);
    setUser(await api.me(access_token));
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, verifyEmail, resetPassword, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
