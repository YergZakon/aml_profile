import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import NetworkGraph from '../components/NetworkGraph';

function ClientDetailsPage() {
  const { id } = useParams();
  const [client, setClient] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [transactionPage, setTransactionPage] = useState(1);
  const [totalTransactions, setTotalTransactions] = useState(0);

  useEffect(() => {
    if (id) {
      fetchClientData();
    }
  }, [id]);

  useEffect(() => {
    if (id && activeTab === 'transactions') {
      fetchTransactions();
    }
  }, [id, activeTab, transactionPage]);

  useEffect(() => {
    if (id && activeTab === 'connections') {
      fetchConnections();
    }
  }, [id, activeTab]);

  const fetchClientData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/clients/${id}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setClient(data);
      setError(null);
    } catch (err) {
      console.error('Ошибка загрузки данных клиента:', err);
      setError('Не удалось загрузить данные клиента');
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/clients/${id}/transactions?page=${transactionPage}&limit=20`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setTransactions(data.transactions || []);
      setTotalTransactions(data.pagination?.total || 0);
    } catch (err) {
      console.error('Ошибка загрузки транзакций:', err);
    }
  };

  const fetchConnections = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/clients/${id}/connections`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setConnections(data.connections || []);
    } catch (err) {
      console.error('Ошибка загрузки связей:', err);
    }
  };

  const getRiskBadge = (riskLevel) => {
    const colors = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800'
    };
    
    const labels = {
      high: 'Высокий',
      medium: 'Средний',
      low: 'Низкий'
    };
    
    return (
      <span className={`px-3 py-1 text-sm font-medium rounded-full ${colors[riskLevel] || colors.low}`}>
        {labels[riskLevel] || 'Неизвестно'}
      </span>
    );
  };

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('ru-KZ', {
      style: 'currency',
      currency: 'KZT',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Н/Д';
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getDirectionBadge = (direction) => {
    const config = {
      outgoing: { color: 'bg-red-100 text-red-800', label: 'Исходящая' },
      incoming: { color: 'bg-green-100 text-green-800', label: 'Входящая' },
      unknown: { color: 'bg-gray-100 text-gray-800', label: 'Неизвестно' }
    };
    
    const { color, label } = config[direction] || config.unknown;
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${color}`}>
        {label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Загрузка данных клиента...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Ошибка загрузки</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
            <div className="mt-4">
              <button
                onClick={fetchClientData}
                className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm mr-3"
              >
                Попробовать снова
              </button>
              <Link
                to="/clients"
                className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-3 py-1 rounded text-sm"
              >
                Вернуться к списку
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!client) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Клиент не найден</p>
        <Link
          to="/clients"
          className="mt-4 inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Вернуться к списку клиентов
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Хлебные крошки */}
      <nav className="flex" aria-label="Breadcrumb">
        <ol className="flex items-center space-x-4">
          <li>
            <Link to="/clients" className="text-gray-400 hover:text-gray-500">
              Клиенты
            </Link>
          </li>
          <li>
            <span className="text-gray-400">/</span>
          </li>
          <li>
            <span className="text-gray-700 font-medium">
              {client.name}
            </span>
          </li>
        </ol>
      </nav>

      {/* Заголовок с основной информацией */}
      <div className="bg-white shadow border rounded-lg p-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{client.name}</h1>
            <p className="text-gray-600">ID: {client.client_id}</p>
            <p className="text-gray-600">Страна: {client.country || 'Не указана'}</p>
          </div>
          <div className="text-right">
            {getRiskBadge(client.risk_level)}
            <p className="text-sm text-gray-600 mt-2">
              Риск-балл: <span className="font-medium">{client.risk_score}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-sm font-medium text-gray-500">Всего операций</h3>
          <p className="text-2xl font-bold text-gray-900">{client.total_transactions}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-sm font-medium text-gray-500">Общая сумма</h3>
          <p className="text-2xl font-bold text-gray-900">{formatAmount(client.total_amount)}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-sm font-medium text-gray-500">Подозрительные операции</h3>
          <p className={`text-2xl font-bold ${client.suspicious_count > 0 ? 'text-red-600' : 'text-green-600'}`}>
            {client.suspicious_count}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-sm font-medium text-gray-500">Период активности</h3>
          <p className="text-sm text-gray-900">
            {formatDate(client.first_transaction)}
            <br />
            <span className="text-gray-500">—</span>
            <br />
            {formatDate(client.last_transaction)}
          </p>
        </div>
      </div>

      {/* Табы */}
      <div className="bg-white shadow border rounded-lg">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Обзор
            </button>
            <button
              onClick={() => setActiveTab('transactions')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'transactions'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Транзакции ({client.total_transactions})
            </button>
            <button
              onClick={() => setActiveTab('connections')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'connections'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Связи
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Профиль клиента</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Основная информация</h4>
                    <dl className="space-y-2">
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-500">Имя:</dt>
                        <dd className="text-sm text-gray-900">{client.name}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-500">ID:</dt>
                        <dd className="text-sm text-gray-900">{client.client_id}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-500">Страна:</dt>
                        <dd className="text-sm text-gray-900">{client.country || 'Не указана'}</dd>
                      </div>
                    </dl>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Риск-анализ</h4>
                    <dl className="space-y-2">
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-500">Уровень риска:</dt>
                        <dd className="text-sm">{getRiskBadge(client.risk_level)}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-500">Риск-балл:</dt>
                        <dd className="text-sm text-gray-900">{client.risk_score}/10</dd>
                      </div>
                    </dl>
                  </div>
                </div>
              </div>

              {client.profile && Object.keys(client.profile).length > 0 && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Дополнительная информация</h3>
                  <div className="bg-gray-50 p-4 rounded-md">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                      {JSON.stringify(client.profile, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'transactions' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">
                  История транзакций ({totalTransactions})
                </h3>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ID операции
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Тип
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Сумма
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Контрагент
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Дата
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Риск
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Действия
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {transactions.length === 0 ? (
                      <tr>
                        <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                          Нет транзакций
                        </td>
                      </tr>
                    ) : (
                      transactions.map((tx) => (
                        <tr key={tx.transaction_id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {tx.transaction_id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {getDirectionBadge(tx.direction)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatAmount(tx.amount_kzt)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {tx.direction === 'outgoing' ? tx.beneficiary_name : tx.sender_name}
                            </div>
                            <div className="text-sm text-gray-500">
                              {tx.direction === 'outgoing' ? tx.beneficiary_country : tx.sender_country}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatDate(tx.transaction_date)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {getRiskBadge(tx.risk_level)}
                            <div className="text-xs text-gray-500 mt-1">
                              {tx.final_risk_score.toFixed(1)}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <Link
                              to={`/transaction/${tx.transaction_id}`}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              Подробнее
                            </Link>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Пагинация */}
              {totalTransactions > 20 && (
                <div className="flex justify-center mt-4">
                  <nav className="flex space-x-2">
                    <button
                      onClick={() => setTransactionPage(Math.max(1, transactionPage - 1))}
                      disabled={transactionPage === 1}
                      className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
                    >
                      Назад
                    </button>
                    <span className="px-3 py-1 text-sm">
                      Страница {transactionPage} из {Math.ceil(totalTransactions / 20)}
                    </span>
                    <button
                      onClick={() => setTransactionPage(transactionPage + 1)}
                      disabled={transactionPage >= Math.ceil(totalTransactions / 20)}
                      className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
                    >
                      Вперед
                    </button>
                  </nav>
                </div>
              )}
            </div>
          )}

          {activeTab === 'connections' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">
                  Сетевые связи ({connections.length})
                </h3>
              </div>
              
              {connections.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  Связи не найдены
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Граф связей */}
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h4 className="text-md font-medium text-gray-900 mb-4">
                      Визуализация связей
                    </h4>
                    <NetworkGraph 
                      data={{
                        nodes: [
                          // Центральный узел (текущий клиент)
                          {
                            id: client.client_id,
                            name: client.name,
                            size: 25,
                            color: '#3b82f6',
                            total_transactions: client.total_transactions,
                            total_volume: client.total_amount,
                            risk_score: client.risk_score,
                            centrality: '★'
                          },
                          // Связанные клиенты
                          ...connections.map(conn => ({
                            id: conn.connected_client_id,
                            name: conn.name,
                            size: Math.min(20, Math.max(8, conn.transaction_count / 2)),
                            color: conn.risk_score >= 7 ? '#ef4444' : 
                                   conn.risk_score >= 4 ? '#f59e0b' : '#10b981',
                            total_transactions: conn.transaction_count,
                            total_volume: conn.total_amount,
                            risk_score: conn.risk_score,
                            centrality: conn.connection_strength
                          }))
                        ],
                        edges: connections.map(conn => ({
                          source: client.client_id,
                          target: conn.connected_client_id,
                          weight: Math.min(5, conn.connection_strength),
                          total_amount: conn.total_amount,
                          is_suspicious: conn.risk_score >= 7
                        }))
                      }}
                      width={700}
                      height={500}
                    />
                  </div>

                  {/* Список связей */}
                  <div>
                    <h4 className="text-md font-medium text-gray-900 mb-4">
                      Детальный список связей
                    </h4>
                    <div className="grid gap-4">
                      {connections.map((connection, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex justify-between items-start">
                            <div>
                              <h5 className="font-medium text-gray-900">
                                {connection.name}
                              </h5>
                              <p className="text-sm text-gray-500">
                                ID: {connection.connected_client_id}
                              </p>
                              <p className="text-sm text-gray-500">
                                Страна: {connection.country}
                              </p>
                            </div>
                            <div className="text-right">
                              <div className="text-sm text-gray-900">
                                Операций: <span className="font-medium">{connection.transaction_count}</span>
                              </div>
                              <div className="text-sm text-gray-900">
                                Сумма: <span className="font-medium">{formatAmount(connection.total_amount)}</span>
                              </div>
                              <div className="text-sm text-gray-500">
                                Сила связи: {connection.connection_strength}/10
                              </div>
                              <div className="text-sm text-gray-500">
                                Риск: {connection.risk_score}
                              </div>
                            </div>
                          </div>
                          <div className="mt-3">
                            <Link
                              to={`/client/${connection.connected_client_id}`}
                              className="text-blue-600 hover:text-blue-900 text-sm"
                            >
                              Перейти к клиенту →
                            </Link>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ClientDetailsPage;