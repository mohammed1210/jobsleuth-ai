/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#ecfeff',
          100: '#cffafe',
          200: '#a5f3fc',
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63',
          950: '#083344',
        },
        ai: {
          gradient: {
            from: '#0f172a',
            via: '#0891b2',
            to: '#059669',
          },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-ai': 'linear-gradient(135deg, #0f172a 0%, #0891b2 55%, #059669 100%)',
        'gradient-ai-soft': 'linear-gradient(135deg, rgba(15, 23, 42, 0.06) 0%, rgba(8, 145, 178, 0.08) 55%, rgba(5, 150, 105, 0.08) 100%)',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(8, 145, 178, 0.22)',
        'glow-lg': '0 0 40px rgba(8, 145, 178, 0.28)',
        'ai': '0 4px 20px rgba(15, 23, 42, 0.1)',
        'ai-hover': '0 8px 30px rgba(15, 23, 42, 0.15)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'gradient': 'gradient 8s ease infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
    },
  },
  plugins: [],
}
