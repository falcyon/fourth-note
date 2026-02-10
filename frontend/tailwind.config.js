/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#174590',
          50: '#E8EEF7',
          100: '#C5D4EC',
          200: '#9FB7DE',
          300: '#7A9BD0',
          400: '#4D7BC0',
          500: '#174590',
          600: '#133A78',
          700: '#0F2E60',
          800: '#0B2348',
          900: '#071730',
        },
        accent: {
          DEFAULT: '#A83E6A',
          50: '#F8EBF0',
          100: '#EDCDD9',
          200: '#DFA4BB',
          300: '#D17B9D',
          400: '#BC5782',
          500: '#A83E6A',
          600: '#8A3357',
          700: '#6C2844',
          800: '#4E1D31',
          900: '#30121E',
        },
        background: {
          start: '#292348',
          end: '#19132D',
        },
      },
    },
  },
  plugins: [],
}
