import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './app.jsx'
import './index.css'

// Импорт стилей Uppy
import '@uppy/core/dist/style.min.css'
import '@uppy/dashboard/dist/style.min.css'
import '@uppy/status-bar/dist/style.min.css'
import '@uppy/progress-bar/dist/style.min.css'

// Создаем корневой элемент React
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)

// Удаляем loader после загрузки React
window.addEventListener('load', () => {
  const loader = document.getElementById('app-loader')
  if (loader) {
    setTimeout(() => {
      loader.style.opacity = '0'
      loader.style.transition = 'opacity 0.3s ease-out'
      setTimeout(() => loader.remove(), 300)
    }, 100)
  }
})

// Обработка ошибок для production
if (import.meta.env.PROD) {
  window.addEventListener('error', (event) => {
    console.error('Глобальная ошибка:', event.error)
    // Здесь можно добавить отправку ошибок в систему мониторинга
  })

  window.addEventListener('unhandledrejection', (event) => {
    console.error('Необработанный промис:', event.reason)
    // Здесь можно добавить отправку ошибок в систему мониторинга
  })
}