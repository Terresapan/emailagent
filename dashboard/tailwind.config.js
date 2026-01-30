/** @type {import('tailwindcss').Config} */
module.exports = {
	content: [
		'./src/pages/**/*.{js,ts,jsx,tsx,mdx}',
		'./src/components/**/*.{js,ts,jsx,tsx,mdx}',
		'./src/app/**/*.{js,ts,jsx,tsx,mdx}',
	],
	darkMode: ['class', 'class'],
	theme: {
		extend: {
			fontFamily: {
				serif: [
					'var(--font-playfair)',
					'serif'
				],
				sans: [
					'var(--font-dm-sans)',
					'sans-serif'
				]
			},
			fontSize: {
				'10xl': '10rem',
				'11xl': '11rem',
				'12xl': '12rem',
				'huge': '14rem',
			},
			colors: {
				brand: {
					fuchsia: '#d946ef', // Legacy
					purple: '#a855f7',  // Legacy
					indigo: '#6366f1',  // Legacy
					orange: '#d76c14',  // Custom accent
					obsidian: '#050505' // Monolith Background
				},
				editorial: {
					bg: '#0F0F16',
					card: '#1A1A24',
					surface: '#252533',
					'surface-alt': '#12121C', // New darker surface
					text: '#F2E9E4',
					muted: '#888899'
				},
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				success: {
					DEFAULT: '#047857',
					foreground: '#A7F3D0'
				},
				warning: {
					DEFAULT: '#B45309',
					foreground: '#FEF3C7'
				},
				ai: {
					DEFAULT: '#6D28D9',
					foreground: '#DDD6FE'
				},
				trigger: {
					DEFAULT: '#C2410C',
					foreground: '#FED7AA'
				},
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				chart: {
					'1': 'hsl(var(--chart-1))',
					'2': 'hsl(var(--chart-2))',
					'3': 'hsl(var(--chart-3))',
					'4': 'hsl(var(--chart-4))',
					'5': 'hsl(var(--chart-5))'
				}
			},
			backgroundImage: {
				'gradient-brand': 'linear-gradient(to right, #d946ef, #a855f7, #6366f1)',
				'gradient-editorial': 'linear-gradient(to bottom right, #0F1016, #05050A)'
			},
			animation: {
				'fade-in': 'fadeIn 0.7s ease-out',
				'slide-up': 'slideUp 0.7s cubic-bezier(0.16, 1, 0.3, 1)',
				'float': 'float 6s ease-in-out infinite',
				'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
				'shimmer': 'shimmer 2s linear infinite',
			},
			keyframes: {
				fadeIn: {
					'0%': { opacity: '0' },
					'100%': { opacity: '1' }
				},
				slideUp: {
					'0%': { opacity: '0', transform: 'translateY(20px)' },
					'100%': { opacity: '1', transform: 'translateY(0)' }
				},
				float: {
					'0%, 100%': { transform: 'translateY(0)' },
					'50%': { transform: 'translateY(-10px)' },
				},
				'glow-pulse': {
					'0%, 100%': { boxShadow: '0 0 5px rgba(136, 224, 239, 0.3)' },
					'50%': { boxShadow: '0 0 20px rgba(136, 224, 239, 0.6)' },
				},
				shimmer: {
					'0%': { backgroundPosition: '-200% 0' },
					'100%': { backgroundPosition: '200% 0' },
				},
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			}
		}
	},
	plugins: [
		require('@tailwindcss/typography'),
		require("tailwindcss-animate")
	],
}
