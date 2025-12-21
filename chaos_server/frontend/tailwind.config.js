/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Pitch black theme colors
        "pitch-black": "#000000",
        "accent-cyan": "#9333ea",
        "accent-blue": "#9333ea",
        "text-primary": "rgba(255, 255, 255, 0.95)",
        "text-secondary": "rgba(255, 255, 255, 0.8)",
        "text-muted": "rgba(255, 255, 255, 0.6)",
        "border-light": "rgba(255, 255, 255, 0.08)",
        "card-bg": "rgba(255, 255, 255, 0.02)",
        // Opacity variants for white
        white: {
          2: "rgba(255, 255, 255, 0.02)",
          5: "rgba(255, 255, 255, 0.05)",
          6: "rgba(255, 255, 255, 0.06)",
          8: "rgba(255, 255, 255, 0.08)",
          10: "rgba(255, 255, 255, 0.1)",
          12: "rgba(255, 255, 255, 0.12)",
          15: "rgba(255, 255, 255, 0.15)",
          20: "rgba(255, 255, 255, 0.2)",
          30: "rgba(255, 255, 255, 0.3)",
          40: "rgba(255, 255, 255, 0.4)",
          60: "rgba(255, 255, 255, 0.6)",
          95: "rgba(255, 255, 255, 0.95)",
        },
        // Opacity variants for black
        black: {
          30: "rgba(0, 0, 0, 0.3)",
          40: "rgba(0, 0, 0, 0.4)",
        },
        // Opacity variants for accent-cyan
        "accent-cyan": {
          10: "rgba(147, 51, 234, 0.1)",
          15: "rgba(147, 51, 234, 0.15)",
          20: "rgba(147, 51, 234, 0.2)",
          30: "rgba(147, 51, 234, 0.3)",
        },
        // Opacity variants for red
        red: {
          400: "#f87171",
          500: "#ef4444",
        },
      },
      backgroundColor: {
        "pitch-black": "#000000",
      },
      fontFamily: {
        sans: [
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
