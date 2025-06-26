import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Конфигурация Vite для системы мониторинга АФМ
export default defineConfig({
  // Подключаем плагин React для поддержки JSX и Fast Refresh
  plugins: [react()],
  
  // Настройка алиасов для удобного импорта
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@services': path.resolve(__dirname, './src/services'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@assets': path.resolve(__dirname, './src/assets')
    }
  },
  
  // Настройка сервера разработки
  server: {
    port: 3000, // Порт для фронтенда
    open: true, // Автоматически открывать браузер
    
    // Настройка прокси для API запросов к Python бэкенду
    proxy: {
      // Проксируем все API запросы
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // НЕ убираем /api из пути - наш бэкенд ожидает /api в маршрутах
        // rewrite убран!
      },
      
      // Отдельный прокси для загрузки файлов (TUS протокол)
      '/upload': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // Увеличиваем таймаут для больших файлов
        timeout: 300000, // 5 минут
        // Важно для TUS протокола - сохраняем все заголовки
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // Логируем TUS запросы для отладки
            if (req.headers['tus-resumable']) {
              console.log('TUS Request:', req.method, req.url);
              console.log('TUS Headers:', req.headers);
            }
          });
        }
      },
      
      // Проксируем запросы к статусу обработки
      '/processing-status': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      
      // Проксируем запросы к файлам
      '/files': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      
      // Проксируем транзакции
      '/transactions': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      
      // Проксируем аналитику
      '/analytics': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      
      // Проксируем health check
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  
  // Настройки сборки
  build: {
    // Папка для собранных файлов
    outDir: 'dist',
    
    // Создаем отдельные чанки для vendor библиотек
    rollupOptions: {
      output: {
        manualChunks: {
          // Выносим React в отдельный чанк
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // Выносим Uppy в отдельный чанк  
          'uppy-vendor': ['@uppy/core', '@uppy/react', '@uppy/dashboard', '@uppy/tus'],
          // Выносим axios в отдельный чанк
          'axios-vendor': ['axios']
        }
      }
    },
    
    // Показывать размеры файлов после сборки
    reportCompressedSize: true,
    
    // Размер чанков (500kb)
    chunkSizeWarningLimit: 500
  },
  
  // Оптимизация зависимостей
  optimizeDeps: {
    // Эти пакеты будут предварительно обработаны
    include: ['react', 'react-dom', 'axios', '@uppy/core', '@uppy/react']
  }
})