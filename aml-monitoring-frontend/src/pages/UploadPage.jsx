import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FileUploader from '../components/FileUploader'

const UploadPage = () => {
  const navigate = useNavigate()
  const [uploadHistory, setUploadHistory] = useState([])
  const [showSuccessMessage, setShowSuccessMessage] = useState(false)

  // Обработка успешной загрузки
  const handleUploadComplete = (fileInfo) => {
    console.log('Файл загружен:', fileInfo)
    
    // Добавляем в историю
    setUploadHistory(prev => [{
      ...fileInfo,
      status: 'processing',
      timestamp: new Date().toISOString()
    }, ...prev])

    setShowSuccessMessage(true)
    
    // Автоматический переход к результатам через 3 секунды
    setTimeout(() => {
      navigate('/analysis', { state: { fileId: fileInfo.fileId } })
    }, 3000)
  }

  // Обработка ошибки загрузки
  const handleUploadError = (error) => {
    console.error('Ошибка при загрузке:', error)
  }

  return (
    <div className="space-y-8">
      {/* Заголовок страницы */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Загрузка файлов транзакций
        </h1>
        <p className="mt-2 text-gray-600">
          Загрузите JSON файл с транзакциями для анализа на предмет подозрительной активности
        </p>
      </div>

      {/* Сообщение об успешной загрузке */}
      {showSuccessMessage && (
        <div className="alert alert-success animate-fade-in">
          <div className="flex items-center">
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Файл успешно загружен! Перенаправление к результатам анализа...</span>
          </div>
        </div>
      )}

      {/* Компонент загрузки */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <FileUploader 
          onUploadComplete={handleUploadComplete}
          onUploadError={handleUploadError}
        />
      </div>

      {/* Последние загрузки */}
      {uploadHistory.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Последние загрузки в этой сессии
          </h3>
          <div className="space-y-3">
            {uploadHistory.map((file, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{file.fileName}</p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(file.fileSize)} • {formatTime(file.timestamp)}
                    </p>
                  </div>
                </div>
                <span className={`status-${file.status}`}>
                  {file.status === 'processing' ? 'Обрабатывается' : 'Завершено'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Информационный блок */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Безопасная загрузка</h3>
          </div>
          <p className="text-sm text-gray-600">
            Файлы загружаются частями с возможностью возобновления при сбоях соединения
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Защита данных</h3>
          </div>
          <p className="text-sm text-gray-600">
            Все данные передаются по защищенному каналу и обрабатываются локально
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Быстрый анализ</h3>
          </div>
          <p className="text-sm text-gray-600">
            Автоматический анализ начинается сразу после загрузки файла
          </p>
        </div>
      </div>
    </div>
  )
}

// Вспомогательные функции
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Б'
  const k = 1024
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('ru-RU', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

export default UploadPage