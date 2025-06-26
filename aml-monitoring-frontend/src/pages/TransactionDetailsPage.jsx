import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const TransactionDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [transaction, setTransaction] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Имитация загрузки данных транзакции
    setTimeout(() => {
      const mockTransaction = {
        id: id,
        date: '2024-01-15T10:30:00Z',
        amount: 5000000,
        currency: 'KZT',
        sender: 'ТОО "Компания А"',
        receiver: 'ИП Иванов И.И.',
        purpose: 'Оплата за товары',
        channel: 'Банковский перевод',
        riskLevel: 'medium',
        riskScore: 65,
        riskReasons: [
          'Крупная сумма операции',
          'Новый получатель средств',
          'Операция в выходной день'
        ],
        profiles: {
          transaction: { score: 70, status: 'medium' },
          customer: { score: 60, status: 'medium' },
          network: { score: 40, status: 'low' },
          behavioral: { score: 80, status: 'high' },
          geographic: { score: 30, status: 'low' }
        }
      };
      setTransaction(mockTransaction);
      setLoading(false);
    }, 1000);
  }, [id]);

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-lg">Загрузка данных транзакции...</span>
      </div>
    );
  }

  if (!transaction) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Транзакция не найдена</h2>
        <button
          onClick={() => navigate('/transactions')}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Вернуться к списку транзакций
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Транзакция #{transaction.id}
            </h1>
            <p className="text-gray-600">
              Детальная информация и анализ рисков
            </p>
          </div>
          <button
            onClick={() => navigate('/transactions')}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            ← Назад к списку
          </button>
        </div>
      </div>

      {/* Основная информация */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Основная информация</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Дата операции:</span>
              <span className="font-medium">
                {new Date(transaction.date).toLocaleString('ru-RU')}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Сумма:</span>
              <span className="font-medium text-lg">
                {formatAmount(transaction.amount)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Отправитель:</span>
              <span className="font-medium">{transaction.sender}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Получатель:</span>
              <span className="font-medium">{transaction.receiver}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Назначение:</span>
              <span className="font-medium">{transaction.purpose}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Канал:</span>
              <span className="font-medium">{transaction.channel}</span>
            </div>
          </div>
        </div>

        {/* Оценка рисков */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Оценка рисков</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-500">Общий уровень риска:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(transaction.riskLevel)}`}>
                {transaction.riskLevel}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-500">Риск-скор:</span>
              <span className="font-bold text-lg">{transaction.riskScore}/100</span>
            </div>
            <div>
              <span className="text-gray-500 block mb-2">Причины риска:</span>
              <ul className="space-y-1">
                {transaction.riskReasons.map((reason, index) => (
                  <li key={index} className="text-sm text-gray-700 flex items-start">
                    <span className="text-red-500 mr-2">•</span>
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Анализ по профилям */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Анализ по профилям</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {Object.entries(transaction.profiles).map(([profileName, profile]) => (
            <div key={profileName} className="text-center p-4 border rounded-lg">
              <h3 className="text-sm font-medium text-gray-900 mb-2">
                {profileName === 'transaction' && 'Транзакционный'}
                {profileName === 'customer' && 'Клиентский'}
                {profileName === 'network' && 'Сетевой'}
                {profileName === 'behavioral' && 'Поведенческий'}
                {profileName === 'geographic' && 'Географический'}
              </h3>
              <div className="text-2xl font-bold text-gray-900 mb-1">
                {profile.score}
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getRiskColor(profile.status)}`}>
                {profile.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Действия */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Действия</h2>
        <div className="flex space-x-4">
          <button className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">
            Создать СТР
          </button>
          <button className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700">
            Отметить для мониторинга
          </button>
          <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
            Подтвердить легитимность
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
            Экспорт отчета
          </button>
        </div>
      </div>
    </div>
  );
};

export default TransactionDetailsPage; 