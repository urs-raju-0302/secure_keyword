/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f1c2e",
        slate: {
          panel: "#1a2b3f",
        },
        accent: {
          DEFAULT: "#2dd4bf",
          dim: "#0f766e",
        },
        warn: "#f59e0b",
      },
      fontFamily: {
        display: ["\"IBM Plex Sans\"", "system-ui", "sans-serif"],
        mono: ["\"IBM Plex Mono\"", "ui-monospace", "monospace"],
      },
      backgroundImage: {
        mesh: "radial-gradient(ellipse at 20% 20%, rgba(45,212,191,0.18), transparent 50%), radial-gradient(ellipse at 80% 0%, rgba(59,130,246,0.15), transparent 45%), linear-gradient(160deg, #0b1524 0%, #122033 45%, #0f1c2e 100%)",
      },
    },
  },
  plugins: [],
};
