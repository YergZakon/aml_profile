import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import React from 'react'
import FileUploader from './components/FileUploader'
import './index.css'

// Импорт страниц
import UploadPage from './pages/UploadPage'
import Dashboard from './pages/DashboardPage'
import TransactionsPage from './pages/TransactionsPage'
import AnalysisPage from './pages/AnalysisPage'
import NetworkPage from './pages/NetworkPage'
import HistoryPage from './pages/HistoryPage'
import SettingsPage from './pages/SettingsPage'
import TransactionDetailsPage from './pages/TransactionDetailsPage'

function App() {
  const [user, setUser] = useState(null)
  const [notifications, setNotifications] = useState([])
  const [isSidebarOpen, setSidebarOpen] = useState(true)

  // Имитация загрузки данных пользователя
  useEffect(() => {
    // В реальном приложении здесь будет запрос к API
    setTimeout(() => {
      setUser({
        name: 'Сотрудник АФМ',
        role: 'Аналитик',
        department: 'Отдел мониторинга'
      })
    }, 500)
  }, [])

  const handleUploadComplete = (result) => {
    console.log('App: Upload complete', result)
    // Здесь можно будет обновить состояние приложения или перенаправить пользователя
  }

  const handleUploadError = (error) => {
    console.error('App: Upload error', error)
    // Здесь можно показать уведомление об ошибке
  }

  // Навигационные ссылки
  const navLinks = [
    { path: '/upload', label: 'Загрузка файлов', icon: '📤' },
    { path: '/dashboard', label: 'Дашборд', icon: '📊' },
    { path: '/transactions', label: 'Транзакции', icon: '💳' },
    { path: '/analysis', label: 'Анализ рисков', icon: '⚠️' },
    { path: '/network', label: 'Сетевой анализ', icon: '🕸️' },
    { path: '/history', label: 'История', icon: '📁' },
    { path: '/settings', label: 'Настройки', icon: '⚙️' },
  ]

  return (
    <div className={`app-container ${isSidebarOpen ? '' : 'sidebar-closed'}`}>
      {/* Шапка приложения */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Логотип и название */}
            <div className="flex items-center">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-kz-blue rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">АФМ</span>
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-gray-900">
                    Система мониторинга транзакций
                  </h1>
                  <p className="text-xs text-gray-500">
                    Агентство по финансовому мониторингу РК
                  </p>
                </div>
              </div>
            </div>

            {/* Информация о пользователе */}
            {user && (
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{user.name}</p>
                  <p className="text-xs text-gray-500">{user.department}</p>
                </div>
                <button className="btn-secondary text-sm">
                  Выход
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Навигация */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {navLinks.map((link) => (
              <NavLink
                key={link.path}
                to={link.path}
                className={({ isActive }) =>
                  `flex items-center space-x-2 py-4 px-1 border-b-2 text-sm font-medium transition-colors duration-200 ${
                    isActive
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`
                }
              >
                <span>{link.icon}</span>
                <span>{link.label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </nav>

      {/* Основной контент */}
      <main className="main-content">
        <div className="p-8">
          <Routes>
            <Route path="/" element={<Navigate to="/upload" replace />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/network" element={<NetworkPage />} />
            <Route path="/transaction/:id" element={<TransactionDetailsPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </main>

      {/* Футер */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center text-sm text-gray-500">
            <div>
              © 2024 Агентство по финансовому мониторингу Республики Казахстан
            </div>
            <div className="flex items-center space-x-4">
              <span>Версия: 1.0.0</span>
              <span>•</span>
              <a href="#" className="hover:text-gray-700">Поддержка</a>
              <span>•</span>
              <a href="#" className="hover:text-gray-700">Документация</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App