/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        brand: {
          'blue-900': '#001060',
          'blue-700': '#104080',
          'blue-500': '#1a4382',
          'blue-50':  '#eef3fb',
          'yellow-500': '#FFCE22',
          'yellow-600': '#f0c020',
          'yellow-700': '#d9a800',
          'ink': '#0a1733',
          'paper': '#f8f9fb',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'sans-serif',
        ],
      },
      fontSize: {
        'hero': ['clamp(2.25rem, 5vw, 4rem)', { lineHeight: '1.05', letterSpacing: '-0.02em', fontWeight: '900' }],
        'h2':   ['clamp(1.5rem, 3vw, 2.5rem)', { lineHeight: '1.15', letterSpacing: '-0.015em', fontWeight: '800' }],
        'h3':   ['clamp(1.25rem, 2vw, 1.625rem)', { lineHeight: '1.3', fontWeight: '700' }],
      },
      boxShadow: {
        'brand': '0 12px 32px -8px rgba(16, 64, 128, 0.25)',
        'fab':   '0 8px 24px -4px rgba(0, 16, 96, 0.45)',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      maxWidth: {
        'content': '76rem',
      },
    },
  },
  plugins: [],
};
