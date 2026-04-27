import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Cowfy / SNT holding palette
        ink: "#1C1C1A",
        steel: {
          50: "#F4F5F6",
          100: "#E4E7E9",
          300: "#A8B0B6",
          500: "#6E7478",
          700: "#3F4448",
        },
        warm: "#EFECE4",
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Helvetica Neue", "Arial"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
