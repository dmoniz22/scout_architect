/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        scout: {
          blue: '#1f4e79',
          light: '#2e75b5',
          yellow: '#ffc107',
          green: '#28a745',
          orange: '#fd7e14'
        }
      }
    },
  },
  plugins: [],
}