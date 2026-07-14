"use client";

import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { api } from "./api";
import { clearTokens, getAccess, setTokens } from "./tokens";
import type { Me, Tokens } from "./types";

interface AuthContextValue {
  user: Me | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient();
  const [user, setUser] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let vivo = true;
    (async () => {
      if (!getAccess()) {
        setLoading(false);
        return;
      }
      try {
        const me = await api<Me>("/api/auth/me");
        if (vivo) setUser(me);
      } catch {
        clearTokens();
      } finally {
        if (vivo) setLoading(false);
      }
    })();
    return () => {
      vivo = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const t = await api<Tokens>("/api/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    setTokens(t.access_token, t.refresh_token);
    // Descartar cualquier dato cacheado de una sesión anterior antes de cargar al nuevo
    // usuario (si no, un usuario vería datos del usuario previo — fuga de aislamiento).
    qc.clear();
    setUser(await api<Me>("/api/auth/me"));
  }, [qc]);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
    qc.clear();
  }, [qc]);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}

// Helpers de roles (§14).
export function tieneRol(user: Me | null, ...roles: string[]): boolean {
  if (!user) return false;
  return user.roles.some((r) => roles.includes(r.rol));
}

export const ROL_LABEL: Record<string, string> = {
  super_admin: "Super administrador",
  editor_corporativo: "Editor corporativo",
  editor_propiedad: "Editor de propiedad",
  custodio_documental: "Custodio documental",
  lector: "Lector",
};
