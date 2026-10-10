import { NextRequest, NextResponse } from "next/server";

// Puerta SSO corporativa (UX). Si el navegador no trae la cookie `crc_sso`, mandamos al
// usuario al portal para que inicie/refresque sesión y vuelva a donde estaba (?next=...).
// El portal, tras autenticar, setea la cookie sobre .thecostaricacollection.com y redirige
// de vuelta; entonces esta app ya la ve y el proxy /api la reenvía al backend.
// Override por env solo para desarrollo local (portal en localhost).
const PORTAL =
  process.env.NEXT_PUBLIC_SSO_PORTAL_URL || "https://apps.thecostaricacollection.com";
const PORTAL_REFRESH = `${PORTAL.replace(/\/$/, "")}/api/sso/refresh`;
const COOKIE_NAME = "crc_sso";

export function middleware(req: NextRequest) {
  if (req.cookies.has(COOKIE_NAME)) return NextResponse.next();

  // URL pública real a la que volver (respeta el host/proto de detrás del proxy de Railway).
  const host =
    req.headers.get("x-forwarded-host") ?? req.headers.get("host") ?? req.nextUrl.host;
  const proto = req.headers.get("x-forwarded-proto") ?? req.nextUrl.protocol.replace(":", "");
  const actual = `${proto}://${host}${req.nextUrl.pathname}${req.nextUrl.search}`;

  return NextResponse.redirect(`${PORTAL_REFRESH}?next=${encodeURIComponent(actual)}`);
}

export const config = {
  // Protegemos toda página del frontend EXCEPTO:
  //  - /api/*      → el proxy; su seguridad la impone el guardia SSO del backend (evita que un
  //                  fetch reciba un 307 HTML en vez de un 401 limpio).
  //  - _next/*     → assets/o build de Next.
  //  - favicon.ico y cualquier archivo con extensión (imágenes de /public, etc.).
  // Esta app NO tiene páginas públicas de producto; si en el futuro se agregara alguna
  // (p. ej. una vista pública por QR), hay que exceptuarla aquí explícitamente.
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\.[^/]+$).*)"],
};
