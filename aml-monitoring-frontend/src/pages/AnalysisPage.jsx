import React, { useState, useEffect } from 'react';
import { analyticsAPI } from '../services/api';

const AnalysisPage = () => {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    riskLevel: 'all',
    dateRange: '30',
    analysisType: 'all'
  });
  const [selectedTransaction, setSelectedTransaction] = useState(null);

  useEffect(() => {
    fetchAnalysisData();
  }, [filters]);

  const fetchAnalysisData = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getRiskAnalysis(filters);
      setAnalysisData(response);
    } catch (error) {
      console.error('Ошибка загрузки данных анализа:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'KZT',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-lg">Загрузка данных анализа...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Анализ рисков</h1>
        <p className="text-gray-600">
          Комплексный анализ транзакций по всем профилям риска
        </p>
      </div>

      {/* Фильтры */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Фильтры анализа</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Уровень риска
            </label>
            <select
              value={filters.riskLevel}
              onChange={(e) => setFilters({...filters, riskLevel: e.target.value})}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="all">Все уровни</option>
              <option value="high">Высокий</option>
              <option value="medium">Средний</option>
              <option value="low">Низкий</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Период
            </label>
            <select
              value={filters.dateRange}
              onChange={(e) => setFilters({...filters, dateRange: e.target.value})}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="7">Последние 7 дней</option>
              <option value="30">Последние 30 дней</option>
              <option value="90">Последние 90 дней</option>
              <option value="365">Последний год</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тип анализа
            </label>
            <select
              value={filters.analysisType}
              onChange={(e) => setFilters({...filters, analysisType: e.target.value})}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="all">Все типы</option>
              <option value="transactional">Транзакционный</option>
              <option value="customer">Клиентский</option>
              <option value="network">Сетевой</option>
              <option value="behavioral">Поведенческий</option>
              <option value="geographic">Географический</option>
            </select>
          </div>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-red-600 font-bold">⚠️</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Высокий риск</p>
              <p className="text-2xl font-bold text-gray-900">
                {analysisData?.risk_summary?.high || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-yellow-600 font-bold">⚡</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Средний риск</p>
              <p className="text-2xl font-bold text-gray-900">
                {analysisData?.risk_summary?.medium || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 font-bold">✅</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Низкий риск</p>
              <p className="text-2xl font-bold text-gray-900">
                {analysisData?.risk_summary?.low || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-bold">📊</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Всего проанализировано</p>
              <p className="text-2xl font-bold text-gray-900">
                {analysisData?.risk_summary?.total || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Разбивка по типам анализа */}
      {analysisData?.analysis_type_breakdown && filters.analysisType === 'all' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Разбивка по типам анализа</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">
                {analysisData.analysis_type_breakdown.transactional || 0}
              </p>
              <p className="text-sm text-gray-600">Транзакционный</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {analysisData.analysis_type_breakdown.customer || 0}
              </p>
              <p className="text-sm text-gray-600">Клиентский</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">
                {analysisData.analysis_type_breakdown.network || 0}
              </p>
              <p className="text-sm text-gray-600">Сетевой</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">
                {analysisData.analysis_type_breakdown.behavioral || 0}
              </p>
              <p className="text-sm text-gray-600">Поведенческий</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">
                {analysisData.analysis_type_breakdown.geographic || 0}
              </p>
              <p className="text-sm text-gray-600">Географический</p>
            </div>
          </div>
        </div>
      )}

      {/* Топ индикаторов риска */}
      {analysisData?.top_risk_indicators && analysisData.top_risk_indicators.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Топ индикаторов риска</h2>
          <div className="space-y-3">
            {analysisData.top_risk_indicators.map((indicator, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm text-gray-700">{indicator.name}</span>
                <span className="text-sm font-medium text-gray-900">{indicator.count} транзакций</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Последние подозрительные операции */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Подозрительные операции
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID операции
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Дата
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Отправитель
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Получатель
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Сумма
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Риск
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Тип анализа
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Действия
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analysisData?.suspicious_transactions?.map((transaction, index) => {
                // Определяем типы анализа из suspicious_reasons
                const getAnalysisTypes = (reasons) => {
                  if (!reasons) return [];
                  const types = [];
                  if (reasons.includes('[ТРАНЗ]')) types.push('Т');
                  if (reasons.includes('[КЛИЕНТ]')) types.push('К');
                  if (reasons.includes('[СЕТЬ]')) types.push('С');
                  if (reasons.includes('[ПОВЕД]')) types.push('П');
                  if (reasons.includes('[ГЕО]')) types.push('Г');
                  return types;
                };
                
                const analysisTypes = getAnalysisTypes(transaction.suspicious_reasons);
                
                return (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {transaction.transaction_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(transaction.transaction_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transaction.sender_name || 'Н/Д'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {transaction.beneficiary_name || 'Н/Д'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatAmount(transaction.amount_kzt)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        transaction.final_risk_score > 7 ? 'text-red-600 bg-red-100' : 'text-yellow-600 bg-yellow-100'
                      }`}>
                        {transaction.final_risk_score.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex space-x-1">
                        {analysisTypes.map((type, i) => (
                          <span key={i} className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-700">
                            {type}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => setSelectedTransaction(transaction)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Подробнее
                      </button>
                    </td>
                  </tr>
                );
              })}
              {(!analysisData?.suspicious_transactions || analysisData.suspicious_transactions.length === 0) && (
                <tr>
                  <td colSpan="8" className="px-6 py-4 text-center text-sm text-gray-500">
                    Подозрительные транзакции не найдены
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Модальное окно детальной информации */}
      {selectedTransaction && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Детали операции {selectedTransaction.transaction_id}
                </h3>
                <button
                  onClick={() => setSelectedTransaction(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <span className="sr-only">Закрыть</span>
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Сумма</p>
                    <p className="text-lg font-semibold">{formatAmount(selectedTransaction.amount_kzt)}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Уровень риска</p>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      selectedTransaction.final_risk_score > 7 ? 'text-red-600 bg-red-100' : 'text-yellow-600 bg-yellow-100'
                    }`}>
                      {selectedTransaction.final_risk_score.toFixed(2)}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Отправитель</p>
                    <p className="text-sm text-gray-900">{selectedTransaction.sender_name || 'Н/Д'}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Получатель</p>
                    <p className="text-sm text-gray-900">{selectedTransaction.beneficiary_name || 'Н/Д'}</p>
                  </div>
                </div>
                
                {selectedTransaction.risk_indicators && (
                  <div>
                    <p className="text-sm font-medium text-gray-500 mb-2">Индикаторы риска</p>
                    <div className="space-y-1">
                      {Object.entries(selectedTransaction.risk_indicators).map(([key, value]) => 
                        value && (
                          <p key={key} className="text-sm text-gray-900">• {key}</p>
                        )
                      )}
                    </div>
                  </div>
                )}
                
                {selectedTransaction.suspicious_reasons && (
                  <div>
                    <p className="text-sm font-medium text-gray-500 mb-2">Причины подозрительности</p>
                    <div className="space-y-1">
                      {(() => {
                        try {
                          // Пытаемся распарсить как JSON
                          const reasons = typeof selectedTransaction.suspicious_reasons === 'string' 
                            ? JSON.parse(selectedTransaction.suspicious_reasons)
                            : selectedTransaction.suspicious_reasons;
                          
                          if (Array.isArray(reasons)) {
                            return reasons.map((reason, idx) => (
                              <p key={idx} className="text-sm text-gray-900">• {reason}</p>
                            ));
                          } else {
                            // Если не массив, обрабатываем как строку
                            return selectedTransaction.suspicious_reasons.split(';').map((reason, idx) => 
                              reason.trim() && (
                                <p key={idx} className="text-sm text-gray-900">• {reason.trim()}</p>
                              )
                            );
                          }
                        } catch (e) {
                          // Если парсинг не удался, обрабатываем как строку
                          return selectedTransaction.suspicious_reasons.split(';').map((reason, idx) => 
                            reason.trim() && (
                              <p key={idx} className="text-sm text-gray-900">• {reason.trim()}</p>
                            )
                          );
                        }
                      })()}
                    </div>
                  </div>
                )}
                
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    onClick={() => setSelectedTransaction(null)}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                  >
                    Закрыть
                  </button>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                    Создать СПО
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisPage; 