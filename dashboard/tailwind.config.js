/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        serif: ['var(--font-playfair)', 'serif'],
        sans: ['var(--font-dm-sans)', 'sans-serif'],
      },
      colors: {
        brand: {
          fuchsia: '#d946ef',
          purple: '#a855f7',
          indigo: '#6366f1',
        },
        editorial: {
          bg: '#05050A', // Almost black, hint of indigo
          card: '#0F1016', // Darker card
          surface: '#181824', // Lighter surface
          text: '#E2E2E2',
          muted: '#888899',
        }
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(to right, #d946ef, #a855f7, #6366f1)',
        'gradient-editorial': 'linear-gradient(to bottom right, #0F1016, #05050A)',
      },
      animation: {
        'fade-in': 'fadeIn 0.7s ease-out',
        'slide-up': 'slideUp 0.7s cubic-bezier(0.16, 1, 0.3, 1)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
