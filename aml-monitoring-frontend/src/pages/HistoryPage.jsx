import React, { useState, useEffect } from 'react';
import axios from 'axios';

const HistoryPage = () => {
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUpload, setSelectedUpload] = useState(null);
  const [filters, setFilters] = useState({
    status: 'all',
    dateFrom: '',
    dateTo: '',
    searchTerm: ''
  });

  useEffect(() => {
    fetchUploadHistory();
  }, []);

  const fetchUploadHistory = async () => {
    try {
      setLoading(true);
      // В реальном приложении здесь будет API для получения истории
      // Пока создадим моковые данные
      const mockData = [
        {
          id: 'upload_001',
          filename: 'transactions_2024_01.json',
          uploadDate: '2024-01-15T10:30:00Z',
          status: 'completed',
          totalTransactions: 1000,
          processedTransactions: 1000,
          highRiskCount: 15,
          mediumRiskCount: 45,
          lowRiskCount: 940,
          fileSize: '3.2 MB',
          processingTime: '00:02:15'
        },
        {
          id: 'upload_002',
          filename: 'do_range.json',
          uploadDate: '2024-01-14T14:22:00Z',
          status: 'completed',
          totalTransactions: 500,
          processedTransactions: 500,
          highRiskCount: 8,
          mediumRiskCount: 22,
          lowRiskCount: 470,
          fileSize: '1.8 MB',
          processingTime: '00:01:45'
        },
        {
          id: 'upload_003',
          filename: 'monthly_report.json',
          uploadDate: '2024-01-13T09:15:00Z',
          status: 'failed',
          totalTransactions: 0,
          processedTransactions: 0,
          highRiskCount: 0,
          mediumRiskCount: 0,
          lowRiskCount: 0,
          fileSize: '2.1 MB',
          processingTime: '00:00:30',
          errorMessage: 'Неверный формат файла'
        }
      ];
      setUploads(mockData);
    } catch (error) {
      console.error('Ошибка загрузки истории:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'processing': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Завершено';
      case 'processing': return 'Обрабатывается';
      case 'failed': return 'Ошибка';
      case 'pending': return 'Ожидает';
      default: return 'Неизвестно';
    }
  };

  const filteredUploads = uploads.filter(upload => {
    if (filters.status !== 'all' && upload.status !== filters.status) return false;
    if (filters.searchTerm && !upload.filename.toLowerCase().includes(filters.searchTerm.toLowerCase())) return false;
    if (filters.dateFrom && new Date(upload.uploadDate) < new Date(filters.dateFrom)) return false;
    if (filters.dateTo && new Date(upload.uploadDate) > new Date(filters.dateTo)) return false;
    return true;
  });

  const deleteUpload = async (uploadId) => {
    if (window.confirm('Вы уверены, что хотите удалить эту запись?')) {
      try {
        setUploads(uploads.filter(upload => upload.id !== uploadId));
        // В реальном приложении здесь будет API вызов
        console.log('Удаление записи:', uploadId);
      } catch (error) {
        console.error('Ошибка удаления:', error);
      }
    }
  };

  const downloadResults = async (uploadId) => {
    try {
      // В реальном приложении здесь будет скачивание результатов
      console.log('Скачивание результатов для:', uploadId);
      alert('Функция скачивания результатов будет реализована');
    } catch (error) {
      console.error('Ошибка скачивания:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-lg">Загрузка истории...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">История загрузок</h1>
        <p className="text-gray-600">
          Просмотр всех загруженных файлов и результатов их анализа
        </p>
      </div>

      {/* Фильтры */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Фильтры</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Статус
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="all">Все статусы</option>
              <option value="completed">Завершено</option>
              <option value="processing">Обрабатывается</option>
              <option value="failed">Ошибка</option>
              <option value="pending">Ожидает</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Поиск по имени файла
            </label>
            <input
              type="text"
              value={filters.searchTerm}
              onChange={(e) => setFilters({...filters, searchTerm: e.target.value})}
              placeholder="Введите имя файла..."
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Дата от
            </label>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => setFilters({...filters, dateFrom: e.target.value})}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Дата до
            </label>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => setFilters({...filters, dateTo: e.target.value})}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
        </div>

        <div className="mt-4 flex justify-between items-center">
          <p className="text-sm text-gray-500">
            Найдено записей: {filteredUploads.length}
          </p>
          <button
            onClick={() => setFilters({status: 'all', dateFrom: '', dateTo: '', searchTerm: ''})}
            className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Сбросить фильтры
          </button>
        </div>
      </div>

      {/* Таблица истории */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Файл
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Дата загрузки
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Статус
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Транзакции
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Высокий риск
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Время обработки
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Действия
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUploads.map((upload) => (
                <tr key={upload.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {upload.filename}
                      </div>
                      <div className="text-sm text-gray-500">
                        {upload.fileSize}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(upload.uploadDate).toLocaleString('ru-RU')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(upload.status)}`}>
                      {getStatusText(upload.status)}
                    </span>
                    {upload.status === 'failed' && (
                      <div className="text-xs text-red-600 mt-1">
                        {upload.errorMessage}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {upload.processedTransactions} / {upload.totalTransactions}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-medium text-red-600">
                      {upload.highRiskCount}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {upload.processingTime}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => setSelectedUpload(upload)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Подробнее
                    </button>
                    {upload.status === 'completed' && (
                      <button
                        onClick={() => downloadResults(upload.id)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Скачать
                      </button>
                    )}
                    <button
                      onClick={() => deleteUpload(upload.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Удалить
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Модальное окно детальной информации */}
      {selectedUpload && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Детали загрузки: {selectedUpload.filename}
                </h3>
                <button
                  onClick={() => setSelectedUpload(null)}
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
                    <p className="text-sm font-medium text-gray-500">ID загрузки</p>
                    <p className="text-sm text-gray-900">{selectedUpload.id}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Размер файла</p>
                    <p className="text-sm text-gray-900">{selectedUpload.fileSize}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Дата загрузки</p>
                    <p className="text-sm text-gray-900">
                      {new Date(selectedUpload.uploadDate).toLocaleString('ru-RU')}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Время обработки</p>
                    <p className="text-sm text-gray-900">{selectedUpload.processingTime}</p>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h4 className="text-md font-medium text-gray-900 mb-3">Результаты анализа</h4>
                  <div className="grid grid-cols-4 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-gray-900">{selectedUpload.totalTransactions}</p>
                      <p className="text-sm text-gray-500">Всего транзакций</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-red-600">{selectedUpload.highRiskCount}</p>
                      <p className="text-sm text-gray-500">Высокий риск</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-yellow-600">{selectedUpload.mediumRiskCount}</p>
                      <p className="text-sm text-gray-500">Средний риск</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-green-600">{selectedUpload.lowRiskCount}</p>
                      <p className="text-sm text-gray-500">Низкий риск</p>
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    onClick={() => setSelectedUpload(null)}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                  >
                    Закрыть
                  </button>
                  {selectedUpload.status === 'completed' && (
                    <button
                      onClick={() => downloadResults(selectedUpload.id)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Скачать результаты
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HistoryPage; 