"use client";

import { createContext, useCallback, useContext, useState } from "react";

type Tipo = "ok" | "error";
interface Toast {
  id: number;
  msg: string;
  tipo: Tipo;
}

const ToastContext = createContext<{ notify: (msg: string, tipo?: Tipo) => void } | null>(null);

let contador = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const notify = useCallback((msg: string, tipo: Tipo = "ok") => {
    const id = ++contador;
    setToasts((t) => [...t, { id, msg, tipo }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ notify }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={`rounded-md border px-4 py-2 text-sm shadow-md ${
              t.tipo === "ok"
                ? "border-firmado/30 bg-white text-firmado"
                : "border-rechazado/30 bg-white text-rechazado"
            }`}
          >
            {t.msg}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const c = useContext(ToastContext);
  if (!c) throw new Error("useToast debe usarse dentro de <ToastProvider>");
  return c;
}
