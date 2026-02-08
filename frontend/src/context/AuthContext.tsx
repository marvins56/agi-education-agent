"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { User } from "@/lib/types/api";
import * as authApi from "@/lib/api/auth";
import { clearTokens, getAccessToken } from "@/lib/api/client";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  });

  const verify = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setState({ user: null, loading: false, error: null });
      return;
    }

    try {
      const user = await authApi.getMe();
      setState({ user, loading: false, error: null });
    } catch {
      clearTokens();
      setState({ user: null, loading: false, error: null });
    }
  }, []);

  useEffect(() => {
    verify();
  }, [verify]);

  const login = async (email: string, password: string) => {
    setState((s) => ({ ...s, error: null, loading: true }));
    try {
      await authApi.login({ email, password });
      const user = await authApi.getMe();
      setState({ user, loading: false, error: null });
    } catch (err) {
      setState({
        user: null,
        loading: false,
        error: err instanceof Error ? err.message : "Login failed",
      });
      throw err;
    }
  };

  const register = async (email: string, password: string, name: string) => {
    setState((s) => ({ ...s, error: null, loading: true }));
    try {
      await authApi.register({ email, password, name });
      await authApi.login({ email, password });
      const user = await authApi.getMe();
      setState({ user, loading: false, error: null });
    } catch (err) {
      setState({
        user: null,
        loading: false,
        error: err instanceof Error ? err.message : "Registration failed",
      });
      throw err;
    }
  };

  const logout = async () => {
    await authApi.logout();
    setState({ user: null, loading: false, error: null });
  };

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
