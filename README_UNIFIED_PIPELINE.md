# 🚀 Единый пайплайн AML системы

Комплексное решение для запуска и управления системой мониторинга финансовых транзакций с поддержкой мультипроцессорной обработки JSON файлов АФМ РК.

## 📋 Содержание

- [Обзор системы](#обзор-системы)
- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
- [Компоненты системы](#компоненты-системы)
- [Конфигурация](#конфигурация)
- [Использование](#использование)
- [Мониторинг](#мониторинг)
- [Устранение неполадок](#устранение-неполадок)

## 🎯 Обзор системы

Единый пайплайн AML представляет собой интегрированное решение, включающее:

- **Backend**: Flask API сервер с расширенными возможностями анализа
- **Frontend**: React SPA для мониторинга и управления
- **Обработчик данных**: Мультипроцессорная система обработки JSON файлов
- **Мониторинг**: Система метрик, логирования и алертов
- **Менеджер процессов**: Автоматическое управление жизненным циклом сервисов

### ⚡ Ключевые возможности

- 🔄 **Мультипроцессорная обработка**: До 20 параллельных процессов
- 📊 **Real-time мониторинг**: Системные метрики и алерты
- 🔧 **Автоматическое управление**: Запуск/остановка/перезапуск сервисов
- 📈 **Высокая производительность**: До 34+ транзакций/секунду
- 🛡️ **Отказоустойчивость**: Автоматический перезапуск при сбоях
- 📱 **Web интерфейс**: Современный dashboard для аналитиков

## 📋 Требования

### Системные требования

- **OS**: Linux, Windows, macOS
- **CPU**: 4+ ядра (рекомендуется 8+)
- **RAM**: 4+ GB (рекомендуется 8+ GB)
- **Диск**: 10+ GB свободного места

### Программное обеспечение

- **Python**: 3.8+
- **Node.js**: 16+
- **npm**: 8+

### Python зависимости

```bash
pip install flask flask-cors psutil requests numpy pandas networkx sqlite3 scikit-learn
```

### Проверка зависимостей

```bash
python test_unified_pipeline.py
```

## 🚀 Быстрый старт

### 1. Клонирование и настройка

```bash
# Переход в директорию проекта
cd /path/to/aml-project

# Проверка структуры файлов
ls -la aml_unified_launcher.py aml_config.py aml_process_manager.py
```

### 2. Установка зависимостей frontend

```bash
cd aml-monitoring-frontend
npm install
cd ..
```

### 3. Запуск полного пайплайна

```bash
# Полный запуск системы
python aml_unified_launcher.py

# Или с дополнительными параметрами
python aml_unified_launcher.py --workers 8 --batch-size 200
```

### 4. Запуск только с обработкой файлов

```bash
# Только обработка JSON файлов (без web интерфейса)
python aml_unified_launcher.py --no-services --json-files data/transactions.json
```

### 5. Управление процессами

```bash
# Запуск менеджера процессов
python aml_process_manager.py monitor

# Проверка статуса
python aml_process_manager.py status

# Остановка всех процессов
python aml_process_manager.py stop
```

## 🔧 Компоненты системы

### 1. Единый лаунчер (`aml_unified_launcher.py`)

Главный компонент для запуска всей системы.

```bash
# Основные параметры
python aml_unified_launcher.py \
  --backend-port 5000 \
  --frontend-port 3000 \
  --workers 8 \
  --batch-size 100 \
  --db-path aml_system.db \
  --uploads-path uploads
```

**Доступные опции:**

- `--backend-port`: Порт backend сервера (по умолчанию: 5000)
- `--frontend-port`: Порт frontend сервера (по умолчанию: 3000)
- `--workers`: Количество рабочих процессов (авто-определение)
- `--batch-size`: Размер батча для обработки (по умолчанию: 100)
- `--no-services`: Не запускать web сервисы
- `--no-processing`: Не обрабатывать файлы
- `--json-files`: Конкретные JSON файлы для обработки
- `--log-level`: Уровень логирования (DEBUG, INFO, WARNING, ERROR)

### 2. Конфигурация (`aml_config.py`)

Централизованная конфигурация системы.

```python
from aml_config import get_config

config = get_config()

# Настройка обработки
config.processing.max_workers = 8
config.processing.batch_size = 200

# Настройка анализа
config.analysis.thresholds['cash_operations'] = 2_000_000

# Сохранение конфигурации
config.save_to_file()
```

### 3. Менеджер процессов (`aml_process_manager.py`)

Управление жизненным циклом процессов.

```bash
# Команды управления
python aml_process_manager.py start          # Запуск всех процессов
python aml_process_manager.py stop           # Остановка всех процессов
python aml_process_manager.py restart        # Перезапуск всех процессов
python aml_process_manager.py status         # Статус процессов
python aml_process_manager.py monitor        # Режим мониторинга

# Управление конкретным процессом
python aml_process_manager.py start --process aml-backend
python aml_process_manager.py restart --process aml-frontend
```

### 4. Система мониторинга (`aml_monitoring.py`)

Сбор метрик и алерты.

```python
from aml_monitoring import get_monitor

monitor = get_monitor()

# Запуск мониторинга
monitor.start_monitoring()

# Запись метрик
monitor.record_processing_metric('transactions_processed', 100)
monitor.record_analysis_metric('transaction', 50, 2.5)

# Получение dashboard данных
dashboard = monitor.get_dashboard_data()
```

### 5. Тестирование (`test_unified_pipeline.py`)

Комплексное тестирование системы.

```bash
# Полное тестирование
python test_unified_pipeline.py

# Результат показывает статус всех компонентов
```

## ⚙️ Конфигурация

### Файл конфигурации (aml_config.json)

Система автоматически создает файл конфигурации при первом запуске:

```json
{
  "processing": {
    "max_workers": 8,
    "batch_size": 100,
    "max_memory_gb": 4.0,
    "timeout_seconds": 300
  },
  "analysis": {
    "profile_weights": {
      "transaction": 0.40,
      "network": 0.30,
      "customer": 0.15,
      "behavioral": 0.10,
      "geographic": 0.05
    },
    "thresholds": {
      "cash_operations": 2000000,
      "international_transfers": 1000000,
      "domestic_transfers": 7000000
    }
  }
}
```

### Переменные окружения

```bash
# Backend настройки
export FLASK_ENV=development
export FLASK_DEBUG=1
export PORT=5000

# Frontend настройки
export VITE_BACKEND_URL=http://localhost:5000

# Обработка данных
export AML_MAX_WORKERS=8
export AML_BATCH_SIZE=100
```

## 🎮 Использование

### Сценарий 1: Полный запуск системы

```bash
# 1. Запуск полной системы
python aml_unified_launcher.py

# 2. Доступ к интерфейсам
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000/api

# 3. Загрузка JSON файлов через веб-интерфейс
# Или размещение файлов в папке uploads/

# 4. Мониторинг через веб-интерфейс или логи
```

### Сценарий 2: Пакетная обработка файлов

```bash
# Обработка конкретных файлов без запуска веб-интерфейса
python aml_unified_launcher.py \
  --no-services \
  --json-files data/transactions_2024_01.json data/transactions_2024_02.json \
  --workers 10 \
  --batch-size 200
```

### Сценарий 3: Разработка и отладка

```bash
# Запуск только backend для разработки
python aml_process_manager.py start --process aml-backend

# Запуск только frontend
python aml_process_manager.py start --process aml-frontend

# Мониторинг в реальном времени
python aml_process_manager.py monitor
```

### Сценарий 4: Высокопроизводительная обработка

```bash
# Максимальная производительность
python aml_unified_launcher.py \
  --workers 16 \
  --batch-size 500 \
  --no-services \
  --json-files /data/large_dataset/*.json
```

## 📊 Мониторинг

### Веб-интерфейс мониторинга

Доступен по адресу: `http://localhost:3000`

**Основные метрики:**
- CPU и память системы
- Скорость обработки транзакций
- Количество ошибок
- Статус процессов
- Активные алерты

### Логи

Логи сохраняются в папке `logs/`:

```
logs/
├── aml_system.log          # Общий лог системы
├── backend.log             # Лог backend сервера
├── frontend.log            # Лог frontend
├── processor.log           # Лог обработки данных
├── analyzer.log            # Лог анализа транзакций
├── errors.log              # Только ошибки
└── audit.log               # Аудит операций
```

### Метрики

```bash
# Просмотр dashboard данных
curl http://localhost:5000/api/metrics/dashboard

# Системные метрики
curl http://localhost:5000/api/metrics/system

# Метрики обработки
curl http://localhost:5000/api/metrics/processing
```

### Алерты

Система автоматически создает алерты при:
- Высокой загрузке CPU (>80%)
- Высоком использовании памяти (>85%)
- Заполнении диска (>90%)
- Высоком уровне ошибок (>10%)
- Сбоях процессов

## 🚨 Устранение неполадок

### Проблема: Backend не запускается

```bash
# Проверка портов
netstat -an | grep 5000

# Проверка зависимостей
python -c "import flask, flask_cors, psutil; print('OK')"

# Запуск в режиме отладки
cd aml-backend
python app.py
```

### Проблема: Frontend не компилируется

```bash
# Переустановка зависимостей
cd aml-monitoring-frontend
rm -rf node_modules package-lock.json
npm install

# Проверка Node.js версии
node --version  # Должно быть 16+
```

### Проблема: Низкая производительность

```bash
# Проверка ресурсов
python -c "import psutil; print(f'CPU: {psutil.cpu_count()}, RAM: {psutil.virtual_memory().total//1024**3}GB')"

# Оптимизация настроек
python aml_unified_launcher.py --workers 4 --batch-size 50
```

### Проблема: Ошибки обработки JSON

```bash
# Валидация JSON файла
python -c "import json; json.load(open('your_file.json'))"

# Проверка формата данных
python test_unified_pipeline.py
```

### Проблема: Переполнение памяти

```bash
# Уменьшение размера батча
python aml_unified_launcher.py --batch-size 50 --workers 4

# Мониторинг памяти
python aml_process_manager.py monitor
```

### Логи для диагностики

```bash
# Основные логи
tail -f logs/aml_system.log

# Ошибки
tail -f logs/errors.log

# Производительность
grep "transactions/sec" logs/processor.log
```

## 📚 Дополнительные ресурсы

### API Документация

- **Health Check**: `GET /api/health`
- **Dashboard**: `GET /api/analytics/dashboard`
- **Transactions**: `GET /api/transactions`
- **Risk Analysis**: `GET /api/analytics/risk-analysis`
- **Metrics**: `GET /api/metrics/*`

### Структура данных JSON АФМ

Система обрабатывает JSON файлы в формате АФМ РК:

```json
[
  {
    "row_to_json": {
      "gmess_id": "123456789",
      "goper_trans_date": "2024-01-15T14:30:00",
      "goper_tenge_amount": "1500000.00",
      "gmember1_maincode": "CLIENT001",
      "gmember1_ur_name": "ТОО КОМПАНИЯ",
      ...
    }
  }
]
```

### Производительность

Типичные показатели производительности:

- **Загрузка данных**: 1000+ записей/сек
- **Анализ транзакций**: 34+ транзакций/сек
- **Потребление памяти**: <2GB для 100K транзакций
- **Время отклика API**: <100ms

### Поддержка

Для получения поддержки:

1. Проверьте [устранение неполадок](#устранение-неполадок)
2. Запустите тестирование: `python test_unified_pipeline.py`
3. Изучите логи в папке `logs/`
4. Проверьте системные требования

---

**© 2024 AML Transaction Monitoring System v3.0**