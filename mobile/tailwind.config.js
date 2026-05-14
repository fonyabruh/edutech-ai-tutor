/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        primary: "#2D6CDF",
        accent: "#FFB020",
        success: "#2DBE6C",
        danger: "#E5484D",
        surface: "#F7F8FA",
        ink: "#0F172A",
      },
    },
  },
  plugins: [],
};
