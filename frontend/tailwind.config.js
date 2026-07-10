/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        im3: {
          DEFAULT: "#1f6feb",
          dark: "#0b4fc4",
        },
      },
    },
  },
  plugins: [],
};
