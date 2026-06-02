import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Paleta data-intelligence / sports analytics
        pitch: "#0a0e1a",
        panel: "#111726",
        panel2: "#161d30",
        line: "#243049",
        brand: "#e10600",      // rojo Mundial
        gold: "#f2b705",
        live: "#2bd576",
        muted: "#7a87a3",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
