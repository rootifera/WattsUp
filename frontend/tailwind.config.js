/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0a0f1c",
        panel: "#111827",
        electric: "#67e8f9",
      },
    },
  },
  plugins: [],
};
