@echo off
echo === Инициализация Git репозитория ===

REM Инициализация репозитория
git init

REM Добавление удаленного репозитория
git remote add origin https://github.com/YergZakon/aml_profile.git

REM Добавление всех файлов
git add .

REM Первый коммит
git commit -m "Initial commit: AML Transaction Monitoring System

- Backend: Flask API with SQLite database
- Frontend: React/Vite application
- 5 analysis profiles (partially implemented)
- TUS file upload support
- Complete documentation"

REM Переименование ветки в main
git branch -M main

echo.
echo === Готово к push ===
echo Выполните следующую команду для загрузки в GitHub:
echo git push -u origin main
echo.
pause 