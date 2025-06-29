import { useState, useEffect } from 'react'
import { analyticsAPI } from '../services/api'
import NetworkGraph from '../components/NetworkGraph'

const NetworkPage = () => {
  const [networkData, setNetworkData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({
    limit: 50,
    minAmount: 100000, // Уменьшили минимальную сумму
    days: 90 // Увеличили период
  })

  useEffect(() => {
    loadNetworkData()
  }, [filters])

  const loadNetworkData = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await analyticsAPI.getNetworkGraph(filters)
      setNetworkData(data)
    } catch (err) {
      console.error('Ошибка загрузки сетевых данных:', err)
      setError('Не удалось загрузить данные сетевого анализа')
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const formatAmount = (amount) => {
    if (amount >= 1000000000) {
      return `${(amount / 1000000000).toFixed(1)} млрд ₸`
    } else if (amount >= 1000000) {
      return `${(amount / 1000000).toFixed(1)} млн ₸`
    } else {
      return `${(amount / 1000).toFixed(0)} тыс ₸`
    }
  }

  const formatNumber = (num) => {
    return new Intl.NumberFormat('ru-RU').format(num)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка сетевого анализа...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Заголовок */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Сетевой анализ</h1>
          <p className="mt-2 text-sm text-gray-600">
            Визуализация связей между клиентами и анализ подозрительных схем
          </p>
        </div>

        {/* Фильтры */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Параметры анализа</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Количество узлов
              </label>
              <select
                value={filters.limit}
                onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={25}>25 узлов</option>
                <option value={50}>50 узлов</option>
                <option value={100}>100 узлов</option>
                <option value={200}>200 узлов</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Минимальная сумма
              </label>
              <select
                value={filters.minAmount}
                onChange={(e) => handleFilterChange('minAmount', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={100000}>100 тыс ₸</option>
                <option value={500000}>500 тыс ₸</option>
                <option value={1000000}>1 млн ₸</option>
                <option value={5000000}>5 млн ₸</option>
                <option value={10000000}>10 млн ₸</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Период
              </label>
              <select
                value={filters.days}
                onChange={(e) => handleFilterChange('days', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={7}>7 дней</option>
                <option value={30}>30 дней</option>
                <option value={60}>60 дней</option>
                <option value={90}>90 дней</option>
                <option value={365}>1 год</option>
              </select>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex">
              <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
                <button 
                  onClick={loadNetworkData}
                  className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                >
                  Повторить попытку
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Статистика */}
        {networkData && networkData.statistics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
              <div className="flex items-center">
                <div className="flex-shrink-0 p-2 bg-blue-100 rounded-lg">
                  <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600">Узлов</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatNumber(networkData.statistics.total_nodes)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
              <div className="flex items-center">
                <div className="flex-shrink-0 p-2 bg-green-100 rounded-lg">
                  <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600">Связей</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatNumber(networkData.statistics.total_edges)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
              <div className="flex items-center">
                <div className="flex-shrink-0 p-2 bg-red-100 rounded-lg">
                  <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600">Высокий риск</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatNumber(networkData.statistics.high_risk_nodes)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
              <div className="flex items-center">
                <div className="flex-shrink-0 p-2 bg-orange-100 rounded-lg">
                  <svg className="h-5 w-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600">Подозрительные</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatNumber(networkData.statistics.suspicious_connections)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
              <div className="flex items-center">
                <div className="flex-shrink-0 p-2 bg-purple-100 rounded-lg">
                  <svg className="h-5 w-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600">Общий объем</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatAmount(networkData.statistics.total_volume)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Сетевой граф */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Граф связей клиентов</h3>
            <div className="text-sm text-gray-500">
              {networkData && networkData.statistics && (
                <span>
                  {networkData.statistics.date_range} • 
                  Мин. сумма: {formatAmount(networkData.statistics.min_amount_filter)}
                </span>
              )}
            </div>
          </div>
          
          <div className="overflow-auto">
            <NetworkGraph 
              data={networkData} 
              width={1000} 
              height={700} 
            />
          </div>
        </div>

        {/* Инструкции */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">Как использовать граф:</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• <strong>Размер узлов</strong> - зависит от количества связей и объема транзакций</li>
            <li>• <strong>Цвет узлов</strong> - показывает уровень риска клиента</li>
            <li>• <strong>Толщина связей</strong> - количество транзакций между клиентами</li>
            <li>• <strong>Красные связи</strong> - подозрительные транзакции</li>
            <li>• <strong>Наведите курсор</strong> на узел для просмотра деталей</li>
            <li>• <strong>Нажмите на узел</strong> для выбора и просмотра подробной информации</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default NetworkPage