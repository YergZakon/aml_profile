import React from 'react';
import { useNavigate } from 'react-router-dom';
import FileUploader from '../components/FileUploader';

const UploadPage = () => {
  const navigate = useNavigate();

  const handleUploadComplete = (result) => {
    console.log('Upload complete, navigating...', result);
    const successfulUploads = result.successful;
    if (successfulUploads.length > 0) {
      // Извлекаем ID файла из ответа сервера
      const fileId = successfulUploads[0].response.uploadURL.split('/').pop();
      // Перенаправляем пользователя на страницу статуса
      navigate(`/status/${fileId}`);
    }
  };

  return (
    <div>
      <h2>Загрузка нового файла для анализа</h2>
      <p>Файл будет загружен и поставлен в очередь на обработку.</p>
      <FileUploader onUploadComplete={handleUploadComplete} />
    </div>
  );
};

export default UploadPage; 