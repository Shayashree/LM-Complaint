/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gov: {
          navy: '#0b2240', // Indian Govt Navy Blue
          saffron: '#f58220', // Indian Saffron
          green: '#059669', // Indian Green for compliant
          red: '#dc2626', // Red for non-compliant
          amber: '#d97706', // Amber for manual review
          bg: '#f8fafc', // Light bg
        }
      }
    },
  },
  plugins: [],
}
