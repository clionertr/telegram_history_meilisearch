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
        'bg-primary': 'rgb(var(--color-bg-primary) / <alpha-value>)',
        'bg-secondary': 'rgb(var(--color-bg-secondary) / <alpha-value>)',
        'bg-tertiary': 'rgb(var(--color-bg-tertiary) / <alpha-value>)',
        
        'text-primary': 'rgb(var(--color-text-primary) / <alpha-value>)',
        'text-secondary': 'rgb(var(--color-text-secondary) / <alpha-value>)',
        'text-tertiary': 'rgb(var(--color-text-tertiary) / <alpha-value>)',
        
        'border-primary': 'rgb(var(--color-border-primary) / <alpha-value>)',
        'border-secondary': 'rgb(var(--color-border-secondary) / <alpha-value>)',
        
        'accent-primary': 'rgb(var(--color-accent-primary) / <alpha-value>)',
        'accent-secondary': 'rgb(var(--color-accent-secondary) / <alpha-value>)',
        'accent-hover': 'rgb(var(--color-accent-hover) / <alpha-value>)',
        
        'success': 'rgb(var(--color-success) / <alpha-value>)',
        'warning': 'rgb(var(--color-warning) / <alpha-value>)',
        'error': 'rgb(var(--color-error) / <alpha-value>)',
        'info': 'rgb(var(--color-info) / <alpha-value>)',
      },
      
      transitionProperty: {
        'theme': 'background-color, border-color, color, fill, stroke',
      },
      
      transitionDuration: {
        'theme': '300ms',
      },
      
      transitionTimingFunction: {
        'theme': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      
      boxShadow: {
        'theme-sm': 'var(--shadow-sm)',
        'theme-md': 'var(--shadow-md)',
        'theme-lg': 'var(--shadow-lg)',
        'theme-xl': 'var(--shadow-xl)',
      },
    },
  },
  plugins: [],
}