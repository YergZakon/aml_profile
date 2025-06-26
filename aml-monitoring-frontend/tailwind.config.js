/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Цвета для системы АФМ РК
      colors: {
        // Основные цвета
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        // Цвета для индикации рисков
        risk: {
          high: '#dc2626',      // Красный - высокий риск
          medium: '#ea580c',    // Оранжевый - средний риск
          low: '#facc15',       // Желтый - низкий риск
          safe: '#16a34a',      // Зеленый - безопасно
          unknown: '#6b7280',   // Серый - не определено
        },
        // Цвета для статусов
        status: {
          pending: '#3b82f6',   // Синий - ожидание
          processing: '#8b5cf6', // Фиолетовый - обработка
          completed: '#10b981',  // Зеленый - завершено
          error: '#ef4444',     // Красный - ошибка
          warning: '#f59e0b',   // Желтый - предупреждение
        },
        // Цвета для государственной символики РК
        kz: {
          blue: '#00AED6',      // Голубой флага РК
          gold: '#FEC50C',      // Золотой флага РК
        }
      },
      // Настройка шрифтов
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'Arial', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      // Анимации для индикаторов загрузки
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'progress': 'progress 1s ease-in-out infinite',
      },
      keyframes: {
        progress: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        }
      },
      // Размеры для дашборда
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      // Настройка теней для карточек
      boxShadow: {
        'risk-high': '0 0 0 3px rgba(220, 38, 38, 0.2)',
        'risk-medium': '0 0 0 3px rgba(234, 88, 12, 0.2)',
        'risk-low': '0 0 0 3px rgba(250, 204, 21, 0.2)',
        'risk-safe': '0 0 0 3px rgba(22, 163, 74, 0.2)',
      }
    },
  },
  plugins: [
    // Плагины можно добавить позже при необходимости
    // require('@tailwindcss/forms'),
    // require('@tailwindcss/typography'),
  ],
}