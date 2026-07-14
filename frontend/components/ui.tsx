"use client";

import Link from "next/link";
import { forwardRef } from "react";
import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" }) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50";
  const variants = {
    primary: "bg-petrol text-white hover:bg-petrol-oscuro",
    secondary: "border border-linea bg-superficie text-carbon hover:bg-petrol-tint",
    ghost: "text-petrol-oscuro hover:bg-petrol-tint",
  };
  return <button className={cx(base, variants[variant], className)} {...props} />;
}

// forwardRef en Input/Textarea/Select: react-hook-form registra los campos por `ref`.
// Sin esto React descarta el ref, el formulario nunca recibe los valores y abre en blanco.
export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return (
      <input
        ref={ref}
        className={cx(
          "w-full rounded-md border border-linea bg-superficie px-3 py-2 text-sm text-carbon placeholder:text-carbon-suave/60",
          className,
        )}
        {...props}
      />
    );
  },
);

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className, ...props }, ref) {
  return (
    <textarea
      ref={ref}
      className={cx(
        "w-full rounded-md border border-linea bg-superficie px-3 py-2 text-sm text-carbon placeholder:text-carbon-suave/60",
        className,
      )}
      {...props}
    />
  );
});

export function Etiqueta({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) {
  return (
    <label htmlFor={htmlFor} className="mb-1 block text-sm font-medium text-carbon">
      {children}
    </label>
  );
}

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className, children, ...props }, ref) {
    return (
      <select
        ref={ref}
        className={cx(
          "w-full rounded-md border border-linea bg-superficie px-3 py-2 text-sm text-carbon",
          className,
        )}
        {...props}
      >
        {children}
      </select>
    );
  },
);

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cx(
        "rounded-lg border border-linea bg-superficie shadow-sm",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function PageHeader({
  titulo,
  descripcion,
  accion,
}: {
  titulo: string;
  descripcion?: string;
  accion?: ReactNode;
}) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        <h1 className="text-xl font-semibold text-petrol-oscuro">{titulo}</h1>
        {descripcion && <p className="mt-1 text-sm text-carbon-suave">{descripcion}</p>}
      </div>
      {accion}
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      role="status"
      aria-label="Cargando"
      className={cx(
        "h-5 w-5 animate-spin rounded-full border-2 border-petrol-tint border-t-petrol",
        className,
      )}
    />
  );
}

export function CargandoBloque({ texto = "Cargando…" }: { texto?: string }) {
  return (
    <div className="flex items-center gap-3 py-12 text-sm text-carbon-suave">
      <Spinner />
      {texto}
    </div>
  );
}

export function EstadoVacio({
  titulo,
  descripcion,
}: {
  titulo: string;
  descripcion?: string;
}) {
  return (
    <div className="rounded-lg border border-dashed border-linea bg-superficie px-6 py-12 text-center">
      <p className="text-sm font-medium text-carbon">{titulo}</p>
      {descripcion && <p className="mt-1 text-sm text-carbon-suave">{descripcion}</p>}
    </div>
  );
}

export function EstadoError({ mensaje }: { mensaje?: string }) {
  return (
    <div className="rounded-lg border border-rechazado/30 bg-rechazado/5 px-6 py-8 text-center">
      <p className="text-sm font-medium text-rechazado">No se pudo cargar la información</p>
      {mensaje && <p className="mt-1 text-sm text-carbon-suave">{mensaje}</p>}
    </div>
  );
}

export function Chip({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-full border border-linea bg-petrol-tint px-2 py-0.5 text-xs font-medium text-petrol-oscuro",
        className,
      )}
    >
      {children}
    </span>
  );
}

// Campo etiqueta/valor para vistas de detalle (formato único).
export function Campo({
  etiqueta,
  children,
}: {
  etiqueta: string;
  children: ReactNode;
}) {
  return (
    <div className="border-t border-linea py-4 first:border-t-0">
      <dt className="text-xs font-semibold uppercase tracking-wide text-carbon-suave">
        {etiqueta}
      </dt>
      <dd className="mt-1.5 text-sm leading-relaxed text-carbon">{children}</dd>
    </div>
  );
}

export function Vacio({ children = "—" }: { children?: ReactNode }) {
  return <span className="text-carbon-suave/70">{children}</span>;
}

export { Link, cx };
