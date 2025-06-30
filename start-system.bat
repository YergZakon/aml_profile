@echo off
echo ====================================================
echo           АФМ РК - Система мониторинга транзакций
echo ====================================================
echo.

echo Запуск системы мониторинга...
echo.

echo [1/3] Активация виртуального окружения...
cd aml-backend
call venv\Scripts\activate.bat

echo [2/3] Запуск Backend сервера (порт 8000)...
start "AML Backend" cmd /k "python app.py"

echo [3/3] Запуск Frontend сервера (порт 3000)...
cd ..\aml-monitoring-frontend
start "AML Frontend" cmd /k "npm run dev"

echo.
echo ====================================================
echo Система запущена!
echo.
echo Backend API:  http://localhost:8000
echo Frontend:     http://localhost:3000
echo.
echo Для остановки закройте окна серверов
echo ====================================================
echo.

timeout /t 5 /nobreak >nul
echo Открываем браузер...
start http://localhost:3000

pause 