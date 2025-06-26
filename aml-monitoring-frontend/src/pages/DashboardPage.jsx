import { useState, useEffect } from 'react'
import { analyticsAPI } from '../services/api'

const DashboardPage = () => {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await analyticsAPI.getDashboardData()
      setDashboardData(data)
    } catch (err) {
      console.error('Ошибка загрузки данных дашборда:', err)
      setError('Не удалось загрузить данные дашборда')
    } finally {
      setLoading(false)
    }
  }

  // Форматирование числа с разделителями тысяч
  const formatNumber = (num) => {
    if (num === null || num === undefined) return '0'
    return num.toLocaleString('ru-RU')
  }

  // Форматирование суммы в тенге
  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '0 ₸'
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'KZT',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  // Форматирование даты
  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Получение цвета для уровня риска
  const getRiskColor = (level) => {
    switch(level) {
      case 'high': return 'text-red-600 bg-red-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'low': return 'text-green-600 bg-green-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  // Получение названия уровня риска на русском
  const getRiskLabel = (level) => {
    switch(level) {
      case 'high': return 'Высокий'
      case 'medium': return 'Средний'
      case 'low': return 'Низкий'
      default: return 'Неизвестный'
    }
  }

  // Отображение состояния загрузки
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка данных дашборда...</p>
        </div>
      </div>
    )
  }

  // Отображение ошибки
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Ошибка загрузки данных</h3>
          <p className="mt-1 text-sm text-gray-500">{error}</p>
          <button onClick={loadDashboardData} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
            Повторить попытку
          </button>
        </div>
      </div>
    )
  }

  // Проверка наличия данных
  if (!dashboardData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Нет данных для отображения</p>
      </div>
    )
  }

  // Безопасное извлечение данных с значениями по умолчанию
  const summary = dashboardData.summary || {}
  const riskDistribution = dashboardData.risk_distribution || {}
  const recentAlerts = dashboardData.recent_alerts || []
  const trends = dashboardData.trends || {}
  const dailyVolumes = trends.daily_volumes || []

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Заголовок страницы */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Дашборд мониторинга</h1>
          <p className="mt-2 text-sm text-gray-600">
            Последнее обновление: {formatDate(dashboardData.last_updated)}
          </p>
        </div>

        {/* Карточки со статистикой */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 bg-blue-100 rounded-lg">
                <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="ml-5">
                <p className="text-sm font-medium text-gray-600">Всего транзакций</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatNumber(summary.total_transactions)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 bg-red-100 rounded-lg">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-5">
                <p className="text-sm font-medium text-gray-600">Подозрительных</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatNumber(summary.flagged_transactions)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 bg-green-100 rounded-lg">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-5">
                <p className="text-sm font-medium text-gray-600">Общая сумма</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatCurrency(summary.total_amount)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 bg-yellow-100 rounded-lg">
                <svg className="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <div className="ml-5">
                <p className="text-sm font-medium text-gray-600">Ожидают проверки</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatNumber(summary.alerts_pending)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Распределение по уровням риска и последние алерты */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Распределение по рискам */}
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Распределение по рискам</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Высокий риск</span>
                <span className="text-sm font-semibold text-red-600">
                  {formatNumber(riskDistribution.high || 0)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Средний риск</span>
                <span className="text-sm font-semibold text-yellow-600">
                  {formatNumber(riskDistribution.medium || 0)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Низкий риск</span>
                <span className="text-sm font-semibold text-green-600">
                  {formatNumber(riskDistribution.low || 0)}
                </span>
              </div>
            </div>
          </div>

          {/* Последние алерты */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Последние алерты</h3>
            <div className="space-y-3">
              {recentAlerts.length > 0 ? (
                recentAlerts.slice(0, 3).map((alert, index) => (
                  <div key={alert.id || index} className="border-b border-gray-200 pb-3 last:border-0">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{alert.type}</p>
                        <p className="text-sm text-gray-500">
                          {formatCurrency(alert.amount)} • {formatDate(alert.date)}
                        </p>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRiskColor(alert.risk_level)}`}>
                        {getRiskLabel(alert.risk_level)}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">Нет последних алертов</p>
              )}
            </div>
          </div>
        </div>

        {/* График трендов */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Объем транзакций за последние 7 дней</h3>
          {dailyVolumes.length > 0 ? (
            <div className="overflow-x-auto">
              <div className="flex space-x-4 min-w-max">
                {dailyVolumes.map((day, index) => (
                  <div key={index} className="text-center">
                    <div className="bg-blue-100 rounded px-3 py-2 mb-2">
                      <p className="text-xs font-medium text-blue-800">
                        {formatNumber(day.count)}
                      </p>
                    </div>
                    <p className="text-xs text-gray-600">
                      {new Date(day.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Нет данных о трендах</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default DashboardPage