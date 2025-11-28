/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/src/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        // DSAT SCHOOL Brand Colors
        primary: '#9967b9',      // Primary Purple
        secondary: '#fdcc4c',    // Secondary Yellow
        dark: '#262632',         // Dark Gray
        // Color variations for different use cases
        'brand-purple': {
          DEFAULT: '#9967b9',
          light: '#b389cb',
          dark: '#7e4fa7',
        },
        'brand-yellow': {
          DEFAULT: '#fdcc4c',
          light: '#fdd970',
          dark: '#e6b831',
        },
        'brand-dark': {
          DEFAULT: '#262632',
          light: '#3a3a4a',
          dark: '#1a1a24',
        },
      },
      fontFamily: {
        sans: ['Montserrat', 'system-ui', 'sans-serif'],
        heading: ['Montserrat', 'sans-serif'],
        title: ['Built Titling', 'Montserrat', 'sans-serif'],
      },
      fontWeight: {
        'extra-bold': '800',
        'semi-bold': '600',
      },
      borderRadius: {
        'brand': '0.5rem',      // Standard brand border radius
        'brand-lg': '1rem',     // Large brand border radius
      },
      borderWidth: {
        'brand': '1px',         // Standard brand border
        'brand-thick': '2px',   // Thick brand border
      },
    },
  },
  plugins: [],
}
