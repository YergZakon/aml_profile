import React, { useState } from 'react';

const SettingsPage = () => {
  const [settings, setSettings] = useState({
    maxFileSize: 1000,
    notificationEmail: 'aml@bank.kz',
    autoReports: true,
    emailNotifications: true,
    transactionThreshold: 10000000,
    mediumRiskThreshold: 1000000,
    retentionPeriod: 2555
  });

  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState('general');

  const saveSettings = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
    console.log('Настройки сохранены:', settings);
  };

  const resetSettings = () => {
    if (window.confirm('Вы уверены, что хотите сбросить настройки к значениям по умолчанию?')) {
      setSettings({
        maxFileSize: 1000,
        notificationEmail: 'aml@bank.kz',
        autoReports: true,
        emailNotifications: true,
        transactionThreshold: 10000000,
        mediumRiskThreshold: 1000000,
        retentionPeriod: 2555
      });
    }
  };

  const tabs = [
    { id: 'general', label: 'Общие', icon: '⚙️' },
    { id: 'analysis', label: 'Анализ', icon: '🔍' },
    { id: 'notifications', label: 'Уведомления', icon: '📧' }
  ];

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Настройки системы</h1>
        <p className="text-gray-600">Конфигурация параметров системы мониторинга</p>
      </div>

      {/* Уведомление о сохранении */}
      {saved && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          ✅ Настройки успешно сохранены!
        </div>
      )}

      {/* Основная панель настроек */}
      <div className="bg-white shadow rounded-lg">
        {/* Табы */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Содержимое табов */}
        <div className="p-6">
          {/* Общие настройки */}
          {activeTab === 'general' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Основные параметры</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Максимальный размер файла (МБ)
                  </label>
                  <input
                    type="number"
                    value={settings.maxFileSize}
                    onChange={(e) => setSettings({...settings, maxFileSize: parseInt(e.target.value)})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Максимальный размер загружаемого файла</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Период хранения данных (дни)
                  </label>
                  <input
                    type="number"
                    value={settings.retentionPeriod}
                    onChange={(e) => setSettings({...settings, retentionPeriod: parseInt(e.target.value)})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Срок хранения результатов анализа</p>
                </div>
              </div>
            </div>
          )}

          {/* Настройки анализа */}
          {activeTab === 'analysis' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Параметры анализа</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Порог высокого риска (тенге)
                  </label>
                  <input
                    type="number"
                    value={settings.transactionThreshold}
                    onChange={(e) => setSettings({...settings, transactionThreshold: parseInt(e.target.value)})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Сумма транзакции для классификации как высокий риск</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Порог среднего риска (тенге)
                  </label>
                  <input
                    type="number"
                    value={settings.mediumRiskThreshold}
                    onChange={(e) => setSettings({...settings, mediumRiskThreshold: parseInt(e.target.value)})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Сумма транзакции для классификации как средний риск</p>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <span className="text-blue-400">ℹ️</span>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800">Информация</h3>
                    <div className="mt-2 text-sm text-blue-700">
                      <p>Пороговые значения используются всеми профилями анализа для классификации уровня риска транзакций.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Настройки уведомлений */}
          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900">Уведомления</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email для уведомлений
                </label>
                <input
                  type="email"
                  value={settings.notificationEmail}
                  onChange={(e) => setSettings({...settings, notificationEmail: e.target.value})}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="email@afm.kz"
                />
                <p className="text-xs text-gray-500 mt-1">Адрес для получения системных уведомлений</p>
              </div>

              <div className="space-y-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="autoReports"
                    checked={settings.autoReports}
                    onChange={(e) => setSettings({...settings, autoReports: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="autoReports" className="ml-2 block text-sm text-gray-900">
                    Автоматическое создание отчетов
                  </label>
                </div>
                <p className="text-xs text-gray-500 ml-6">Автоматически создавать отчеты после завершения анализа</p>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="emailNotifications"
                    checked={settings.emailNotifications}
                    onChange={(e) => setSettings({...settings, emailNotifications: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="emailNotifications" className="ml-2 block text-sm text-gray-900">
                    Email уведомления
                  </label>
                </div>
                <p className="text-xs text-gray-500 ml-6">Отправлять уведомления о подозрительных транзакциях</p>
              </div>
            </div>
          )}
        </div>

        {/* Кнопки действий */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-between">
          <button
            onClick={resetSettings}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
          >
            Сбросить к умолчанию
          </button>
          
          <div className="space-x-3">
            <button
              onClick={saveSettings}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Сохранить настройки
            </button>
          </div>
        </div>
      </div>

      {/* Информационная панель */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Системная информация</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-gray-500">Версия системы</div>
            <div className="text-lg font-semibold text-gray-900">1.0.0</div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-gray-500">Последнее обновление</div>
            <div className="text-lg font-semibold text-gray-900">26.01.2024</div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-gray-500">Статус</div>
            <div className="text-lg font-semibold text-green-600">Активна</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage; 