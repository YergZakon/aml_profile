import axios from 'axios'

// Базовая конфигурация axios
const api = axios.create({
  // Убираем baseURL - будем использовать полные пути
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Интерсептор для добавления токена авторизации (если будет нужен)
api.interceptors.request.use(
  (config) => {
    // Логируем все запросы для отладки
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    
    // Здесь можно добавить токен из localStorage
    // const token = localStorage.getItem('auth_token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Интерсептор для обработки ошибок
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`)
    return response
  },
  (error) => {
    if (error.response) {
      // Сервер ответил с ошибкой
      console.error('API Error Response:', {
        url: error.config?.url,
        status: error.response.status,
        data: error.response.data
      })
      
      // Обработка специфичных кодов ошибок
      switch (error.response.status) {
        case 401:
          // Неавторизован
          console.error('Необходима авторизация')
          // Можно добавить редирект на страницу входа
          // window.location.href = '/login'
          break
        case 403:
          console.error('Доступ запрещен')
          break
        case 404:
          console.error('Ресурс не найден')
          break
        case 500:
          console.error('Ошибка сервера')
          break
      }
    } else if (error.request) {
      // Запрос был отправлен, но ответа не получено
      console.error('Нет ответа от сервера:', error.request)
    } else {
      // Что-то пошло не так при настройке запроса
      console.error('Ошибка запроса:', error.message)
    }
    
    return Promise.reject(error)
  }
)

// API методы для работы с файлами
export const fileAPI = {
  // Получить статус обработки файла
  getProcessingStatus: async (fileId) => {
    try {
      const response = await api.get(`/api/processing-status/${fileId}`)
      return response.data
    } catch (error) {
      console.error('Error getting processing status:', error)
      throw error
    }
  },

  // Получить список загруженных файлов
  getUploadedFiles: async (params = {}) => {
    try {
      const response = await api.get('/api/files', { 
        params: {
          limit: params.limit,
          offset: params.offset,
          status: params.status
        }
      })
      return response.data
    } catch (error) {
      console.error('Error getting uploaded files:', error)
      throw error
    }
  },

  // Удалить файл
  deleteFile: async (fileId) => {
    try {
      const response = await api.delete(`/api/files/${fileId}`)
      return response.data
    } catch (error) {
      console.error('Error deleting file:', error)
      throw error
    }
  },
}

// API методы для работы с транзакциями
export const transactionAPI = {
  // Получить список транзакций
  getTransactions: async (params = {}) => {
    try {
      const response = await api.get('/api/transactions', {
        params: {
          page: params.page || 1,
          limit: params.limit || 50,
          risk_level: params.riskLevel,
          start_date: params.startDate,
          end_date: params.endDate,
          search: params.search,
          sort_by: params.sortBy,
          sort_order: params.sortOrder,
        }
      })
      return response.data
    } catch (error) {
      console.error('Error getting transactions:', error)
      throw error
    }
  },

  // Получить детали транзакции
  getTransactionDetails: async (transactionId) => {
    try {
      const response = await api.get(`/api/transactions/${transactionId}`)
      return response.data
    } catch (error) {
      console.error('Error getting transaction details:', error)
      throw error
    }
  },

  // Отметить транзакцию как проверенную
  markAsReviewed: async (transactionId, reviewData) => {
    try {
      const response = await api.post(`/api/transactions/${transactionId}/review`, reviewData)
      return response.data
    } catch (error) {
      console.error('Error marking transaction as reviewed:', error)
      throw error
    }
  },

  // Экспорт транзакций
  exportTransactions: async (params = {}) => {
    try {
      const response = await api.get('/api/transactions/export', {
        params,
        responseType: 'text', // Для CSV
      })
      return response.data
    } catch (error) {
      console.error('Error exporting transactions:', error)
      throw error
    }
  },
}

// API методы для работы с клиентами
export const clientAPI = {
  // Получить список клиентов
  getClients: async (params = {}) => {
    try {
      const response = await api.get('/api/clients', { params })
      return response.data
    } catch (error) {
      console.error('Error getting clients:', error)
      throw error
    }
  },

  // Получить профиль клиента
  getClientProfile: async (clientId) => {
    try {
      const response = await api.get(`/api/clients/${clientId}`)
      return response.data
    } catch (error) {
      console.error('Error getting client profile:', error)
      throw error
    }
  },

  // Получить транзакции клиента
  getClientTransactions: async (clientId, params = {}) => {
    try {
      const response = await api.get(`/api/clients/${clientId}/transactions`, { params })
      return response.data
    } catch (error) {
      console.error('Error getting client transactions:', error)
      throw error
    }
  },

  // Получить сетевой профиль клиента
  getClientNetwork: async (clientId) => {
    try {
      const response = await api.get(`/api/clients/${clientId}/network`)
      return response.data
    } catch (error) {
      console.error('Error getting client network:', error)
      throw error
    }
  },
}

// API методы для аналитики
export const analyticsAPI = {
  // Получить статистику по рискам
  getRiskStatistics: async (params = {}) => {
    try {
      const response = await api.get('/api/analytics/risks', { params })
      return response.data
    } catch (error) {
      console.error('Error getting risk statistics:', error)
      throw error
    }
  },

  // Получить данные анализа рисков
  getRiskAnalysis: async (params = {}) => {
    try {
      const response = await api.get('/api/analytics/risk-analysis', { params })
      return response.data
    } catch (error) {
      console.error('Error getting risk analysis:', error)
      throw error
    }
  },

  // Получить дашборд данные
  getDashboardData: async () => {
    try {
      const response = await api.get('/api/analytics/dashboard')
      return response.data
    } catch (error) {
      console.error('Error getting dashboard data:', error)
      throw error
    }
  },

  // Получить топ рисковых клиентов
  getTopRiskClients: async (limit = 10) => {
    try {
      const response = await api.get('/api/analytics/top-risk-clients', {
        params: { limit }
      })
      return response.data
    } catch (error) {
      console.error('Error getting top risk clients:', error)
      throw error
    }
  },

  // Получить тренды
  getTrends: async (params = {}) => {
    try {
      const response = await api.get('/api/analytics/trends', { params })
      return response.data
    } catch (error) {
      console.error('Error getting trends:', error)
      throw error
    }
  },
}

// API методы для отчетов
export const reportAPI = {
  // Создать отчет
  generateReport: async (reportData) => {
    try {
      const response = await api.post('/api/reports/generate', reportData)
      return response.data
    } catch (error) {
      console.error('Error generating report:', error)
      throw error
    }
  },

  // Получить список отчетов
  getReports: async (params = {}) => {
    try {
      const response = await api.get('/api/reports', { params })
      return response.data
    } catch (error) {
      console.error('Error getting reports:', error)
      throw error
    }
  },

  // Скачать отчет
  downloadReport: async (reportId) => {
    try {
      const response = await api.get(`/api/reports/${reportId}/download`, {
        responseType: 'blob',
      })
      return response.data
    } catch (error) {
      console.error('Error downloading report:', error)
      throw error
    }
  },
}

// API методы для системы
export const systemAPI = {
  // Проверка здоровья системы
  healthCheck: async () => {
    try {
      const response = await api.get('/api/health')
      return response.data
    } catch (error) {
      console.error('Error checking system health:', error)
      throw error
    }
  },

  // Получить информацию об API
  getApiInfo: async () => {
    try {
      const response = await api.get('/api/')
      return response.data
    } catch (error) {
      console.error('Error getting API info:', error)
      throw error
    }
  },
}

// Утилитарные функции
export const utils = {
  // Функция для скачивания файла
  downloadFile: (data, filename) => {
    // Проверяем, является ли data blob или строкой
    const blob = data instanceof Blob ? data : new Blob([data], { type: 'text/csv;charset=utf-8;' })
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },

  // Функция для форматирования ошибок
  formatError: (error) => {
    if (error.response?.data?.message) {
      return error.response.data.message
    }
    if (error.response?.data?.error) {
      return error.response.data.error
    }
    if (error.message) {
      return error.message
    }
    return 'Произошла неизвестная ошибка'
  },

  // Функция для форматирования даты
  formatDate: (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  },

  // Функция для форматирования суммы
  formatAmount: (amount, currency = 'KZT') => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(amount)
  },
}

export default api