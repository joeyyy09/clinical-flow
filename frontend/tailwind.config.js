
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#f8fafc', // slate-50
        sidebar: '#0f172a', // slate-900
        primary: '#0ea5e9', // sky-500
        secondary: '#64748b', // slate-500
        accent: '#f43f5e', // rose-500
        success: '#10b981', // emerald-500
        card: '#ffffff',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
