import { useState, useEffect } from 'react'
import { transactionAPI } from '../services/api'

const TransactionDetailsModal = ({ transaction, onClose }) => {
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Загружаем полные детали транзакции
    const loadDetails = async () => {
      try {
        const transactionId = transaction.id || transaction.transaction_id || transaction.reference_id
        const data = await transactionAPI.getTransactionDetails(transactionId)
        setDetails(data)
      } catch (error) {
        console.error('Ошибка загрузки деталей:', error)
        // Используем базовые данные если не удалось загрузить детали
        setDetails(transaction)
      } finally {
        setLoading(false)
      }
    }

    loadDetails()
  }, [transaction])

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: details?.currency || 'KZT',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }

  const handleMarkAsReviewed = async () => {
    try {
      const transactionId = transaction.id || transaction.transaction_id || transaction.reference_id
      await transactionAPI.markAsReviewed(transactionId, {
        reviewedBy: 'Сотрудник АФМ',
        reviewedAt: new Date().toISOString(),
        notes: 'Проверено вручную'
      })
      alert('Транзакция отмечена как проверенная')
      onClose()
    } catch (error) {
      console.error('Ошибка при отметке:', error)
      alert('Не удалось отметить транзакцию')
    }
  }

  // Определяем уровень риска на основе данных из БД
  const getRiskLevel = () => {
    if (!details) return 'low'
    if (details.is_suspicious || details.final_risk_score > 7) return 'high'
    if (details.final_risk_score > 4) return 'medium'
    return 'low'
  }

  const riskLevel = details?.risk_level || getRiskLevel()

  const riskColors = {
    high: 'text-red-600 bg-red-50 border-red-200',
    medium: 'text-orange-600 bg-orange-50 border-orange-200',
    low: 'text-yellow-600 bg-yellow-50 border-yellow-200'
  }

  const riskLabels = {
    high: 'Высокий риск',
    medium: 'Средний риск',
    low: 'Низкий риск'
  }

  // Парсим risk_indicators если это строка JSON
  const getRiskIndicators = () => {
    if (!details) return []
    if (Array.isArray(details.risk_indicators)) {
      return details.risk_indicators
    }
    if (typeof details.risk_indicators === 'string') {
      try {
        return JSON.parse(details.risk_indicators)
      } catch {
        return []
      }
    }
    if (details.risk_reasons) {
      return details.risk_reasons
    }
    return []
  }

  const riskIndicators = getRiskIndicators()

  // Парсим rule_triggers если это строка JSON
  const getRuleTriggers = () => {
    if (!details) return []
    if (Array.isArray(details.rule_triggers)) {
      return details.rule_triggers
    }
    if (typeof details.rule_triggers === 'string') {
      try {
        return JSON.parse(details.rule_triggers)
      } catch {
        return []
      }
    }
    if (details.flagged_rules) {
      return details.flagged_rules
    }
    return []
  }

  const ruleTriggers = getRuleTriggers()

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Заголовок */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">
            Детали транзакции
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Содержимое */}
        <div className="px-6 py-4 overflow-y-auto max-h-[calc(90vh-120px)]">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="w-16 h-16 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-gray-600">Загрузка деталей...</p>
              </div>
            </div>
          ) : details ? (
            <div className="space-y-6">
              {/* Основная информация */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ID транзакции
                  </label>
                  <p className="font-mono text-sm bg-gray-50 px-3 py-2 rounded">
                    {details.reference_id || details.transaction_id || details.id}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Дата и время
                  </label>
                  <p className="text-sm bg-gray-50 px-3 py-2 rounded">
                    {formatDate(details.date || details.transaction_date)}
                  </p>
                </div>
              </div>

              {/* Уровень риска */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Оценка риска
                </label>
                <div className={`inline-flex items-center px-4 py-2 rounded-lg border ${riskColors[riskLevel]}`}>
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span className="font-semibold">{riskLabels[riskLevel]}</span>
                  {details.final_risk_score && (
                    <span className="ml-2 text-sm">({details.final_risk_score.toFixed(2)})</span>
                  )}
                </div>
              </div>

              {/* Сумма */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Сумма транзакции
                </label>
                <p className="text-2xl font-bold text-gray-900">
                  {formatAmount(details.amount || details.amount_kzt)}
                </p>
              </div>

              {/* Отправитель */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Отправитель
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-600">Имя</label>
                    <p className="text-sm font-medium">{details.sender?.name || details.sender_name || 'Н/Д'}</p>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600">Счет</label>
                    <p className="text-sm font-mono">{details.sender?.account || details.sender_account || 'Н/Д'}</p>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600">Банк</label>
                    <p className="text-sm">{details.sender?.bank || details.sender_bank_bic || 'Н/Д'}</p>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600">Страна</label>
                    <p className="text-sm">{details.sender?.country || details.sender_country || 'KZ'}</p>
                  </div>
                </div>
              </div>

              {/* Получатель */}
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Получатель
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-600">Имя</label>
                    <p className="text-sm font-medium">{details.receiver?.name || details.beneficiary_name || 'Н/Д'}</p>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600">Счет</label>
                    <p className="text-sm font-mono">{details.receiver?.account || details.beneficiary_account || 'Н/Д'}</p>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600">Банк</label>
                    <p className="text-sm">{details.receiver?.bank || details.beneficiary_bank_bic || 'Н/Д'}</p>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600">Страна</label>
                    <p className="text-sm">{details.receiver?.country || details.beneficiary_country || 'KZ'}</p>
                  </div>
                </div>
              </div>

              {/* Индикаторы риска */}
              {riskIndicators.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Индикаторы риска
                  </h3>
                  <div className="space-y-2">
                    {riskIndicators.map((indicator, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        <svg className="w-5 h-5 text-red-500 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                        <span className="text-sm text-gray-700">
                          {typeof indicator === 'object' ? indicator.name || indicator.code || JSON.stringify(indicator) : indicator}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Сработавшие правила */}
              {ruleTriggers.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Сработавшие правила
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <ul className="list-disc list-inside space-y-1">
                      {ruleTriggers.map((rule, index) => (
                        <li key={index} className="text-sm text-gray-700">
                          {typeof rule === 'object' ? rule.name || rule.code || JSON.stringify(rule) : rule}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Дополнительная информация */}
              {(details.purpose_text || details.additional_info) && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Дополнительная информация
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {details.purpose_text || details.additional_info}
                    </p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">Не удалось загрузить детали транзакции</p>
            </div>
          )}
        </div>

        {/* Действия */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
          <button
            onClick={handleMarkAsReviewed}
            className="btn-primary"
          >
            Отметить как проверенную
          </button>
          <button
            onClick={onClose}
            className="btn-secondary"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  )
}

export default TransactionDetailsModal