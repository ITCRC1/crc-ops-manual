import type { Metadata } from "next";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "CRC Operations Manual Hub",
  description:
    "Procedimientos Operativos Estándar, Descriptores de Puesto y Políticas — The Costa Rica Collection",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className="bg-fondo text-carbon antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
