/** @type {import('next').NextConfig} */

// El navegador solo habla con ESTE frontend (mismo origen, bajo .thecostaricacollection.com,
// donde vive la cookie `crc_sso`). Next reenvía /api/* al backend como reverse proxy,
// arrastrando las cabeceras entrantes —incluida Cookie— para que el guardia SSO del backend
// valide la sesión. Overridable por env para apuntar a un backend local en desarrollo/pruebas.
const BACKEND_ORIGIN =
  process.env.BACKEND_ORIGIN || "https://backend-production-c4609.up.railway.app";

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // El frontend NO tiene route handlers propios bajo /api, así que no hay colisión.
      { source: "/api/:path*", destination: `${BACKEND_ORIGIN}/api/:path*` },
    ];
  },
};

export default nextConfig;
