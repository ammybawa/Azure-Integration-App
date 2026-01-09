/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        azure: {
          50: '#eff8ff',
          100: '#def0ff',
          200: '#b6e3ff',
          300: '#75cfff',
          400: '#2cb8ff',
          500: '#00a1f1',
          600: '#0080cd',
          700: '#0066a6',
          800: '#005689',
          900: '#064871',
          950: '#042d4b',
        },
        midnight: {
          50: '#f4f6fb',
          100: '#e8ecf6',
          200: '#ccd7eb',
          300: '#a0b5da',
          400: '#6d8ec4',
          500: '#4a70ae',
          600: '#385891',
          700: '#2e4776',
          800: '#293d62',
          900: '#1a2744',
          950: '#0f172a',
        }
      },
      fontFamily: {
        sans: ['Outfit', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-subtle': 'bounce-subtle 1s ease-in-out infinite',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'typing': 'typing 1.5s steps(3) infinite',
      },
      keyframes: {
        'bounce-subtle': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        typing: {
          '0%': { content: '"."' },
          '33%': { content: '".."' },
          '66%': { content: '"..."' },
        }
      },
    },
  },
  plugins: [],
}

