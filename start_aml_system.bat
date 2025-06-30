@echo off
chcp 65001 > nul
echo 🚀 БЫСТРЫЙ ЗАПУСК AML СИСТЕМЫ
echo ================================

REM Проверка наличия Python
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.8+
    pause
    exit /b 1
)

REM Проверка наличия Node.js
node --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js не найден. Установите Node.js 16+
    pause
    exit /b 1
)

REM Проверка файлов
if not exist "aml_unified_launcher.py" (
    echo ❌ Файл aml_unified_launcher.py не найден
    pause
    exit /b 1
)

if not exist "aml-backend\app.py" (
    echo ❌ Backend не найден
    pause
    exit /b 1
)

if not exist "aml-monitoring-frontend\package.json" (
    echo ❌ Frontend не найден
    pause
    exit /b 1
)

echo ✅ Проверки пройдены

REM Установка зависимостей frontend если нужно
if not exist "aml-monitoring-frontend\node_modules" (
    echo 📦 Установка зависимостей frontend...
    cd aml-monitoring-frontend
    call npm install
    if errorlevel 1 (
        echo ❌ Ошибка установки зависимостей
        pause
        exit /b 1
    )
    cd ..
    echo ✅ Зависимости установлены
)

echo.
echo 🔧 Запуск единого пайплайна...
echo 📱 Frontend: http://localhost:3000
echo 🔗 Backend API: http://localhost:5000
echo 💡 Для остановки нажмите Ctrl+C
echo --------------------------------

python aml_unified_launcher.py

pause