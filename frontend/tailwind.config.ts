import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        petrol: "#1F7A8C",
        "petrol-oscuro": "#155E6D",
        "petrol-tint": "#E6F0F2",
        carbon: "#3D3D3D",
        "carbon-suave": "#4A5A62",
        fondo: "#F2F4F1",
        superficie: "#FFFFFF",
        linea: "#DEE5E2",
        firmado: "#2F7D57",
        "en-firma": "#B97514",
        borrador: "#5B6A72",
        rechazado: "#B23A48",
        archivado: "#8A979D",
        controlado: "#155E6D",
        cwl: "#2F6B4F",
        amarena: "#8A4F5E",
        oxigen: "#3B8EA5",
        ojochal: "#6E7F3A",
      },
    },
  },
  plugins: [],
} satisfies Config;
