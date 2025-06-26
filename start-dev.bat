@echo off
echo ====================================================
echo   АФМ РК - Запуск системы мониторинга транзакций
echo ====================================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)

REM Проверяем наличие Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Node.js не найден! Установите Node.js 16+
    pause
    exit /b 1
)

echo [1/4] Установка зависимостей Python...
cd backend
pip install flask flask-cors >nul 2>&1
cd ..

echo [2/4] Установка зависимостей Frontend...
cd frontend
call npm install >nul 2>&1

echo [3/4] Запуск Backend сервера...
start cmd /k "cd backend && echo Backend запущен на http://localhost:8000 && python app.py"

echo [4/4] Запуск Frontend сервера...
timeout /t 3 /nobreak >nul
start cmd /k "cd frontend && echo Frontend запущен на http://localhost:3000 && npm run dev"

echo.
echo ====================================================
echo   Система успешно запущена!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo ====================================================
echo.
echo Нажмите любую клавишу для закрытия этого окна...
pause >nul