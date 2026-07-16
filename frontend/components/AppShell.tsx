"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { AUTH_HABILITADA, ROL_LABEL, tieneRol, useAuth } from "@/lib/auth";
import { confirmarSalida } from "@/lib/cambios-sin-guardar";

const NAV: { href: string; label: string; exact?: boolean; roles?: string[] }[] = [
  { href: "/", label: "Inicio", exact: true },
  { href: "/biblioteca", label: "Librería maestra" },
  {
    // La marca de origen es curaduría interna: mismo permiso que el tab "Por Origen".
    href: "/amarena",
    label: "SOPs de Amarena",
    roles: ["super_admin", "editor_corporativo"],
  },
  {
    href: "/intake",
    label: "Laboratorio de intake",
    roles: ["super_admin", "editor_corporativo"],
  },
  { href: "/firmas", label: "Centro de firmas" },
  { href: "/descriptores", label: "Descriptores de puesto" },
  {
    href: "/armador",
    label: "Armador por propiedad",
    roles: ["super_admin", "editor_corporativo", "editor_propiedad"],
  },
  { href: "/capacitacion", label: "Capacitación" },
  { href: "/calendario", label: "Calendario" },
  { href: "/organigrama", label: "Organigrama" },
  { href: "/busqueda", label: "Búsqueda global" },
  {
    href: "/auditoria",
    label: "Auditoría y custodia",
    roles: ["super_admin", "editor_corporativo", "custodio_documental"],
  },
  { href: "/usuarios", label: "Usuarios", roles: ["super_admin"] },
];

function activo(pathname: string, href: string, exact?: boolean): boolean {
  if (exact) return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const rolPrincipal = user?.roles[0]?.rol;

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-64 shrink-0 flex-col border-r border-linea bg-superficie">
        <div className="border-b border-linea px-5 py-4">
          <p className="text-sm font-semibold leading-tight text-petrol-oscuro">
            CRC Operations Manual
          </p>
          <p className="mt-0.5 text-xs text-carbon-suave">The Costa Rica Collection</p>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {NAV.filter((item) => !item.roles || tieneRol(user, ...item.roles)).map((item) => {
            const on = activo(pathname, item.href, item.exact);
            return (
              <Link
                key={item.href}
                href={item.href}
                // Salir del menú con un editor abierto perdía todo lo escrito, sin aviso.
                onClick={(e) => {
                  if (!confirmarSalida()) e.preventDefault();
                }}
                aria-current={on ? "page" : undefined}
                className={`block rounded-md px-3 py-2 text-sm transition-colors ${
                  on
                    ? "bg-petrol-tint font-medium text-petrol-oscuro"
                    : "text-carbon-suave hover:bg-petrol-tint/50 hover:text-petrol-oscuro"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-linea p-3 text-xs text-carbon-suave">
          Etapa 5 — solo lectura
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-linea bg-superficie px-6 py-3">
          <div />
          <div className="flex items-center gap-4">
            {user && (
              <div className="text-right">
                <p className="text-sm font-medium text-carbon">{user.nombre}</p>
                <p className="text-xs text-carbon-suave">
                  {rolPrincipal ? (ROL_LABEL[rolPrincipal] ?? rolPrincipal) : user.email}
                </p>
              </div>
            )}
            {AUTH_HABILITADA && (
              <button
                onClick={logout}
                className="rounded-md border border-linea px-3 py-1.5 text-sm text-carbon-suave hover:bg-petrol-tint hover:text-petrol-oscuro"
              >
                Salir
              </button>
            )}
          </div>
        </header>
        <main className="flex-1 overflow-x-auto p-6">{children}</main>
      </div>
    </div>
  );
}
