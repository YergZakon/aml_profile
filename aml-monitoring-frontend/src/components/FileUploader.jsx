import React, { useState, useEffect } from 'react'
import Uppy from '@uppy/core'
import { Dashboard } from '@uppy/react'
import Tus from '@uppy/tus'
import russianLocale from '@uppy/locales/lib/ru_RU'

// CSS для Uppy компонентов
import '@uppy/core/dist/style.min.css'
import '@uppy/dashboard/dist/style.min.css'

const FileUploader = ({ onUploadComplete, onUploadError }) => {
  const [uppy, setUppy] = useState(null)
  const [uploadStatus, setUploadStatus] = useState('idle') // idle, uploading, processing, completed, error
  const [uploadProgress, setUploadProgress] = useState(0)
  const [processingStatus, setProcessingStatus] = useState('')

  useEffect(() => {
    const uppyInstance = new Uppy({
      id: 'aml-uploader',
      autoProceed: true, // Начинаем загрузку сразу после выбора файла
      restrictions: {
        maxFileSize: 1024 * 1024 * 1024, // 1 GB
        allowedFileTypes: ['.json'],
        maxNumberOfFiles: 1, // Разрешаем загружать только один файл за раз
      },
      locale: russianLocale,
    })

    uppyInstance.use(Tus, {
      endpoint: 'http://127.0.0.1:8000/upload', // ИЗМЕНЕНО: Указываем правильный порт 8000
      retryDelays: [0, 1000, 3000, 5000],
      chunkSize: 5 * 1024 * 1024, // 5 MB чанки
      resume: false, // ИЗМЕНЕНО: Отключаем возобновление загрузки
    })

    // Обработчик завершения загрузки
    uppyInstance.on('complete', (result) => {
      console.log('Загрузка завершена!', result)
      if (onUploadComplete) {
        onUploadComplete(result)
      }
      
      const successfulUploads = result.successful
      if (successfulUploads.length > 0) {
        // Извлекаем ID файла из ответа сервера
        const fileId = successfulUploads[0].response.uploadURL.split('/').pop()
        // Можно выполнить перенаправление на страницу статуса
        // Например: window.location.href = `/status/${fileId}`
        console.log(`Файл загружен. ID для проверки статуса: ${fileId}`)
      }
    })

    // Обработчик ошибок
    uppyInstance.on('upload-error', (file, error, response) => {
      console.error('Ошибка загрузки:', error)
      if (onUploadError) {
        onUploadError(error)
      }
    })

    setUppy(uppyInstance)

    // Очистка при размонтировании компонента
    return () => {
      uppyInstance.close()
    }
  }, [onUploadComplete, onUploadError])

  if (!uppy) {
    return <div>Загрузка компонента...</div>
  }

  return (
    <div className="uppy-container">
      <Dashboard
        uppy={uppy}
        height={300}
        theme="light"
        proudlyDisplayPoweredByUppy={false}
        note="Поддерживаемые форматы: JSON. Максимальный размер: 1 ГБ."
      />
      
      {/* Статус обработки */}
      {uploadStatus !== 'idle' && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              {processingStatus}
            </span>
            <span className="text-sm text-gray-500">
              {uploadProgress}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default FileUploader