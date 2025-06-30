# ⚡ Быстрый старт единого пайплайна AML

## 🎯 В двух словах

Единый пайплайн AML - это комплексное решение для запуска backend + frontend + мультипроцессорной обработки JSON файлов АФМ РК в одной команде.

## 🚀 Мгновенный запуск

### Linux/macOS:
```bash
python start_aml_system.py
```

### Windows:
```cmd
start_aml_system.bat
```

### Или напрямую:
```bash
python aml_unified_launcher.py
```

## 📱 Доступ к системе

После запуска:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Логи**: папка `logs/`

## 📁 Обработка файлов

### Автоматическая обработка:
1. Поместите JSON файлы в папку `uploads/`
2. Система автоматически их обработает

### Ручная обработка:
```bash
python aml_unified_launcher.py --json-files data/transactions.json
```

## ⚙️ Основные команды

```bash
# Полный запуск
python aml_unified_launcher.py

# Только обработка файлов (без веб-интерфейса)
python aml_unified_launcher.py --no-services

# Высокопроизводительная обработка
python aml_unified_launcher.py --workers 16 --batch-size 500

# Тестирование системы
python test_unified_pipeline.py

# Управление процессами
python aml_process_manager.py monitor

# Статус системы
python aml_process_manager.py status
```

## 🛠️ Настройка производительности

### Автоматическая (рекомендуется):
Система автоматически определяет оптимальные настройки на основе вашего железа.

### Ручная настройка:
```bash
# Для мощных серверов
python aml_unified_launcher.py --workers 20 --batch-size 1000

# Для слабых машин
python aml_unified_launcher.py --workers 2 --batch-size 50
```

## 📊 Мониторинг

### Web Dashboard:
- Перейдите на http://localhost:3000
- Вкладка "Мониторинг" или "Dashboard"

### Консольный мониторинг:
```bash
python aml_process_manager.py monitor
```

### Логи:
```bash
tail -f logs/aml_system.log      # Общий лог
tail -f logs/processor.log       # Обработка данных
tail -f logs/errors.log          # Только ошибки
```

## 🚨 Устранение проблем

### Backend не запускается:
```bash
cd aml-backend
python app.py  # Запуск в отладочном режиме
```

### Frontend не компилируется:
```bash
cd aml-monitoring-frontend
rm -rf node_modules
npm install
```

### Проблемы с производительностью:
```bash
# Проверка ресурсов
python -c "import psutil; print(f'CPU: {psutil.cpu_count()}, RAM: {psutil.virtual_memory().total//1024**3}GB')"

# Уменьшение нагрузки
python aml_unified_launcher.py --workers 2 --batch-size 50
```

### Полное тестирование:
```bash
python test_unified_pipeline.py
```

## 📋 Требования

- **Python**: 3.8+
- **Node.js**: 16+
- **RAM**: 4+ GB
- **CPU**: 4+ ядра

## 🎁 Готовые сценарии

### 1. Разработчик (разработка/отладка):
```bash
python aml_process_manager.py start --process aml-backend
# Работа с кодом...
python aml_process_manager.py start --process aml-frontend
```

### 2. Аналитик (ежедневная работа):
```bash
python start_aml_system.py
# Открыть http://localhost:3000
# Загрузить файлы через веб-интерфейс
```

### 3. Системный администратор (обработка больших объемов):
```bash
python aml_unified_launcher.py \
  --no-services \
  --workers 16 \
  --batch-size 1000 \
  --json-files /data/large_dataset/*.json
```

### 4. DevOps (мониторинг и управление):
```bash
python aml_process_manager.py monitor
# Отслеживание статуса всех процессов
```

## 💡 Полезные советы

1. **Используйте мониторинг** - система показывает реальную производительность
2. **Настройте под свое железо** - больше CPU = больше workers
3. **Следите за логами** - они покажут все проблемы
4. **Тестируйте регулярно** - `python test_unified_pipeline.py`
5. **Backup настроек** - файл `aml_config.json` содержит всю конфигурацию

---

🎉 **Готово!** Ваша AML система запущена и готова к работе.