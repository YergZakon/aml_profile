import { useState, useEffect, useCallback } from 'react'
import { transactionAPI, utils } from '../services/api'
import TransactionDetailsModal from '../components/TransactionDetailsModal'

const TransactionsPage = () => {
  // Состояние данных
  const [transactions, setTransactions] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Состояние модального окна
  const [selectedTransaction, setSelectedTransaction] = useState(null)
  const [showDetails, setShowDetails] = useState(false)
  
  // Параметры таблицы
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [sortBy, setSortBy] = useState('date')
  const [sortOrder, setSortOrder] = useState('desc')
  
  // Фильтры
  const [filters, setFilters] = useState({
    riskLevel: '',
    startDate: '',
    endDate: '',
    minAmount: '',
    maxAmount: '',
    search: ''
  })
  
  // Временные значения для фильтров (до применения)
  const [tempFilters, setTempFilters] = useState(filters)

  // Загрузка транзакций
  const loadTransactions = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const params = {
        page: currentPage,
        limit: pageSize,
        sortBy,
        sortOrder,
        ...filters
      }
      
      const response = await transactionAPI.getTransactions(params)
      console.log('Loaded transactions:', response.transactions) // Для отладки
      setTransactions(response.transactions || [])
      setTotalCount(response.total || 0)
    } catch (err) {
      console.error('Ошибка загрузки транзакций:', err)
      setError('Не удалось загрузить транзакции')
    } finally {
      setLoading(false)
    }
  }, [currentPage, pageSize, sortBy, sortOrder, filters])

  // Загружаем данные при изменении параметров
  useEffect(() => {
    loadTransactions()
  }, [loadTransactions])

  // Обработчики фильтров
  const handleFilterChange = (name, value) => {
    setTempFilters(prev => ({ ...prev, [name]: value }))
  }

  const applyFilters = () => {
    setFilters(tempFilters)
    setCurrentPage(1) // Сбрасываем на первую страницу
  }

  const resetFilters = () => {
    const emptyFilters = {
      riskLevel: '',
      startDate: '',
      endDate: '',
      minAmount: '',
      maxAmount: '',
      search: ''
    }
    setTempFilters(emptyFilters)
    setFilters(emptyFilters)
    setCurrentPage(1)
  }

  // Сортировка
  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  // Экспорт в Excel
  const handleExport = async () => {
    try {
      const blob = await transactionAPI.exportTransactions({
        ...filters,
        sortBy,
        sortOrder
      })
      utils.downloadFile(blob, `transactions_${new Date().toISOString().split('T')[0]}.xlsx`)
    } catch (err) {
      console.error('Ошибка экспорта:', err)
      alert('Не удалось экспортировать транзакции')
    }
  }

  // Детали транзакции
  const showTransactionDetails = async (transaction) => {
    setSelectedTransaction(transaction)
    setShowDetails(true)
  }

  // Пагинация
  const totalPages = Math.ceil(totalCount / pageSize)
  const startItem = (currentPage - 1) * pageSize + 1
  const endItem = Math.min(currentPage * pageSize, totalCount)

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Транзакции</h1>
          <p className="mt-1 text-sm text-gray-600">
            Всего найдено: {totalCount.toLocaleString('ru-RU')} транзакций
          </p>
        </div>
        <button
          onClick={handleExport}
          disabled={loading || totalCount === 0}
          className="btn-secondary flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>Экспорт в Excel</span>
        </button>
      </div>

      {/* Панель фильтров */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {/* Уровень риска */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Уровень риска
            </label>
            <select
              value={tempFilters.riskLevel}
              onChange={(e) => handleFilterChange('riskLevel', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Все уровни</option>
              <option value="high">Высокий</option>
              <option value="medium">Средний</option>
              <option value="low">Низкий</option>
            </select>
          </div>

          {/* Дата начала */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Дата с
            </label>
            <input
              type="date"
              value={tempFilters.startDate}
              onChange={(e) => handleFilterChange('startDate', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Дата конца */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Дата по
            </label>
            <input
              type="date"
              value={tempFilters.endDate}
              onChange={(e) => handleFilterChange('endDate', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Минимальная сумма */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Сумма от
            </label>
            <input
              type="number"
              value={tempFilters.minAmount}
              onChange={(e) => handleFilterChange('minAmount', e.target.value)}
              placeholder="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Максимальная сумма */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Сумма до
            </label>
            <input
              type="number"
              value={tempFilters.maxAmount}
              onChange={(e) => handleFilterChange('maxAmount', e.target.value)}
              placeholder="999999999"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Поиск */}
          <div className="lg:col-span-2 xl:col-span-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Поиск
            </label>
            <input
              type="text"
              value={tempFilters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              placeholder="Имя, счет, банк..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Кнопки действий */}
          <div className="flex items-end space-x-2">
            <button
              onClick={applyFilters}
              className="btn-primary flex-1"
            >
              Применить
            </button>
            <button
              onClick={resetFilters}
              className="btn-secondary"
            >
              Сбросить
            </button>
          </div>
        </div>
      </div>

      {/* Таблица транзакций */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600">Загрузка транзакций...</p>
            </div>
          </div>
        ) : error ? (
          <div className="p-6">
            <div className="alert alert-error">
              <p>{error}</p>
              <button onClick={loadTransactions} className="btn-secondary btn-sm mt-2">
                Повторить
              </button>
            </div>
          </div>
        ) : transactions.length === 0 ? (
          <div className="p-12 text-center">
            <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-gray-500">Транзакции не найдены</p>
            <p className="text-sm text-gray-400 mt-2">Попробуйте изменить параметры фильтров</p>
          </div>
        ) : (
          <>
            {/* Таблица */}
            <div className="overflow-x-auto custom-scrollbar">
              <table className="data-table">
                <thead>
                  <tr>
                    <SortableHeader
                      field="reference_id"
                      label="ID транзакции"
                      sortBy={sortBy}
                      sortOrder={sortOrder}
                      onSort={handleSort}
                    />
                    <SortableHeader
                      field="date"
                      label="Дата"
                      sortBy={sortBy}
                      sortOrder={sortOrder}
                      onSort={handleSort}
                    />
                    <th>Отправитель</th>
                    <th>Получатель</th>
                    <SortableHeader
                      field="amount"
                      label="Сумма"
                      sortBy={sortBy}
                      sortOrder={sortOrder}
                      onSort={handleSort}
                    />
                    <SortableHeader
                      field="risk_level"
                      label="Риск"
                      sortBy={sortBy}
                      sortOrder={sortOrder}
                      onSort={handleSort}
                    />
                    <th>Индикаторы</th>
                    <th className="text-right">Действия</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((transaction) => (
                    <TransactionRow
                      key={transaction.id || transaction.transaction_id || transaction.reference_id}
                      transaction={transaction}
                      onViewDetails={showTransactionDetails}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Пагинация */}
            <div className="px-6 py-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Показано <span className="font-medium">{startItem}</span> - <span className="font-medium">{endItem}</span> из{' '}
                  <span className="font-medium">{totalCount.toLocaleString('ru-RU')}</span> транзакций
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="p-2 text-gray-600 hover:text-gray-900 disabled:text-gray-300 disabled:cursor-not-allowed"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  
                  <div className="flex items-center space-x-1">
                    {generatePageNumbers(currentPage, totalPages).map((page, index) => (
                      <button
                        key={index}
                        onClick={() => page !== '...' && setCurrentPage(page)}
                        disabled={page === '...'}
                        className={`px-3 py-1 text-sm rounded ${
                          page === currentPage
                            ? 'bg-primary-600 text-white'
                            : page === '...'
                            ? 'text-gray-400 cursor-default'
                            : 'text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        {page}
                      </button>
                    ))}
                  </div>
                  
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="p-2 text-gray-600 hover:text-gray-900 disabled:text-gray-300 disabled:cursor-not-allowed"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Модальное окно деталей */}
      {showDetails && selectedTransaction && (
        <TransactionDetailsModal
          transaction={selectedTransaction}
          onClose={() => {
            setShowDetails(false)
            setSelectedTransaction(null)
          }}
        />
      )}
    </div>
  )
}

// Компонент сортируемого заголовка
const SortableHeader = ({ field, label, sortBy, sortOrder, onSort }) => {
  const isActive = sortBy === field
  
  return (
    <th
      onClick={() => onSort(field)}
      className="cursor-pointer hover:bg-gray-100 transition-colors"
    >
      <div className="flex items-center space-x-1">
        <span>{label}</span>
        <div className="flex flex-col">
          <svg
            className={`w-3 h-3 ${isActive && sortOrder === 'asc' ? 'text-primary-600' : 'text-gray-400'}`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M10 3l7 7H3l7-7z" />
          </svg>
          <svg
            className={`w-3 h-3 -mt-1 ${isActive && sortOrder === 'desc' ? 'text-primary-600' : 'text-gray-400'}`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M10 17l-7-7h14l-7 7z" />
          </svg>
        </div>
      </div>
    </th>
  )
}

// Компонент строки транзакции
const TransactionRow = ({ transaction, onViewDetails }) => {
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: transaction.currency || 'KZT',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(amount)
  }

  const riskColors = {
    high: 'risk-indicator-high',
    medium: 'risk-indicator-medium',
    low: 'risk-indicator-low'
  }

  const riskLabels = {
    high: 'Высокий',
    medium: 'Средний',
    low: 'Низкий'
  }

  // Определяем уровень риска на основе данных из БД
  const getRiskLevel = () => {
    if (transaction.is_suspicious || transaction.final_risk_score > 7) return 'high'
    if (transaction.final_risk_score > 4) return 'medium'
    return 'low'
  }

  const riskLevel = transaction.risk_level || getRiskLevel()

  // Парсим risk_indicators если это строка JSON
  const getRiskIndicators = () => {
    if (Array.isArray(transaction.risk_indicators)) {
      return transaction.risk_indicators
    }
    if (typeof transaction.risk_indicators === 'string' && transaction.risk_indicators.trim() !== '') {
      try {
        const parsed = JSON.parse(transaction.risk_indicators)
        return Array.isArray(parsed) ? parsed : []
      } catch {
        return []
      }
    }
    if (Array.isArray(transaction.risk_reasons)) {
      return transaction.risk_reasons
    }
    // Проверяем, есть ли объект risk_indicators с ключами
    if (transaction.risk_indicators && typeof transaction.risk_indicators === 'object') {
      // Если это объект с булевыми флагами, преобразуем в массив
      const indicators = []
      for (const [key, value] of Object.entries(transaction.risk_indicators)) {
        if (value === true) {
          indicators.push(key)
        }
      }
      return indicators
    }
    return []
  }

  const riskIndicators = getRiskIndicators()

  return (
    <tr className="hover:bg-gray-50">
      <td className="font-mono text-xs">{transaction.reference_id || transaction.transaction_id || transaction.id}</td>
      <td className="text-sm">{formatDate(transaction.date || transaction.transaction_date)}</td>
      <td>
        <div>
          <p className="text-sm font-medium text-gray-900">
            {transaction.sender?.name || transaction.sender_name || 'Н/Д'}
          </p>
          <p className="text-xs text-gray-500">
            {transaction.sender?.bank || transaction.sender_bank_bic || 'Н/Д'}
          </p>
        </div>
      </td>
      <td>
        <div>
          <p className="text-sm font-medium text-gray-900">
            {transaction.receiver?.name || transaction.beneficiary_name || 'Н/Д'}
          </p>
          <p className="text-xs text-gray-500">
            {transaction.receiver?.bank || transaction.beneficiary_bank_bic || 'Н/Д'}
          </p>
        </div>
      </td>
      <td className="text-sm font-medium">{formatAmount(transaction.amount || transaction.amount_kzt)}</td>
      <td>
        <span className={riskColors[riskLevel]}>
          {riskLabels[riskLevel]}
        </span>
      </td>
      <td>
        <div className="flex flex-wrap gap-1">
          {riskIndicators && Array.isArray(riskIndicators) && riskIndicators.length > 0 ? (
            <>
              {riskIndicators.slice(0, 2).map((indicator, index) => (
                <span key={index} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                  {typeof indicator === 'object' ? indicator.name || indicator.code : indicator}
                </span>
              ))}
              {riskIndicators.length > 2 && (
                <span className="text-xs text-gray-500">
                  +{riskIndicators.length - 2}
                </span>
              )}
            </>
          ) : (
            <span className="text-xs text-gray-400">Нет индикаторов</span>
          )}
        </div>
      </td>
      <td className="text-right">
        <button
          onClick={() => onViewDetails(transaction)}
          className="text-primary-600 hover:text-primary-700 text-sm font-medium"
        >
          Детали
        </button>
      </td>
    </tr>
  )
}

// Функция генерации номеров страниц для пагинации
const generatePageNumbers = (current, total) => {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  
  if (current <= 3) {
    return [1, 2, 3, 4, '...', total]
  }
  
  if (current >= total - 2) {
    return [1, '...', total - 3, total - 2, total - 1, total]
  }
  
  return [1, '...', current - 1, current, current + 1, '...', total]
}

export default TransactionsPage