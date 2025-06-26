# Быстрый старт - Система мониторинга транзакций АФМ РК

## Требования

- Python 3.8+
- Node.js 16+
- Windows 10/11

## Установка

### 1. Клонирование репозитория
```bash
git clone [repository-url]
cd profile
```

### 2. Установка зависимостей Backend

```bash
cd aml-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 3. Установка зависимостей Frontend

```bash
cd aml-monitoring-frontend
npm install
cd ..
```

## Запуск системы

### Вариант 1: Автоматический запуск (рекомендуется)

Просто запустите:
```bash
start-dev.bat
```

Или:
```bash
node run-dev.js
```

### Вариант 2: Ручной запуск

#### Backend:
```bash
cd aml-backend
venv\Scripts\activate
python app.py
```

#### Frontend (в новом терминале):
```bash
cd aml-monitoring-frontend
npm run dev
```

## Доступ к системе

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API документация**: http://localhost:8000/api/

## Первый запуск

1. Откройте браузер и перейдите на http://localhost:3000
2. Перейдите на страницу "Загрузка файлов"
3. Загрузите файл `do_range.json` (тестовые данные)
4. Дождитесь завершения анализа (2-3 минуты)
5. Просмотрите результаты на дашборде

## Структура данных для загрузки

Система принимает JSON файлы со следующей структурой:
```json
[
  {
    "row_to_json": {
      "gmess_id": "67810658",
      "goper_trans_date": "2025-01-01T10:00:00",
      "goper_tenge_amount": 5000000,
      "gmember_maincode_pl1": "CLIENT001",
      "gmember_name_pl1": "ТОО Альфа",
      "gmember_maincode_pol1": "CLIENT002",
      "gmember_name_pol1": "ИП Бета",
      "goper_susp_first": "1054"
    }
  }
]
```

## Решение проблем

### Backend не запускается
- Убедитесь, что активировано виртуальное окружение
- Проверьте, что порт 8000 свободен
- Установите все зависимости: `pip install -r requirements.txt`

### Frontend не запускается
- Проверьте, что порт 3000 свободен
- Переустановите зависимости: `npm install`
- Очистите кеш: `npm cache clean --force`

### Дашборд показывает пустые данные
- Убедитесь, что файл был загружен и анализ завершен
- Проверьте консоль браузера на наличие ошибок
- Перезагрузите страницу

### PowerShell ошибки с &&
PowerShell не поддерживает оператор &&. Используйте:
- Точку с запятой: `cd aml-backend; python app.py`
- Или запускайте команды по отдельности

## Полезные команды

### Проверка базы данных
```bash
cd aml-backend
python -c "from aml_database_setup import AMLDatabaseManager; db = AMLDatabaseManager('aml_system.db'); print(db.get_system_statistics()); db.close()"
```

### Очистка старых БД
```bash
cd aml-backend
del aml_system_*.db
```

### Просмотр логов
Backend логи выводятся в консоль при запуске `python app.py`

## Контакты и поддержка

При возникновении проблем обращайтесь к документации `PROJECT_DOCUMENTATION.md` 