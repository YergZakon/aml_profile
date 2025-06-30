#!/usr/bin/env python3
"""
🚀 Простой запуск AML системы
Упрощенная версия без дополнительных зависимостей
"""

import os
import sys
import time
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path

def print_banner():
    print("🚀 ПРОСТОЙ ЗАПУСК AML СИСТЕМЫ")
    print("=" * 50)
    print(f"🕒 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Директория: {os.getcwd()}")

def check_files():
    """Проверка необходимых файлов"""
    print("\n🔍 Проверка файлов...")
    
    required_files = [
        'aml-backend/app.py',
        'aml-monitoring-frontend/package.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print("❌ Отсутствуют файлы:")
        for file in missing_files:
            print(f"   • {file}")
        return False
    
    return True

def check_dependencies():
    """Проверка зависимостей"""
    print("\n🔍 Проверка зависимостей...")
    
    # Проверка Python модулей
    try:
        import sqlite3
        print("✅ sqlite3")
    except ImportError:
        print("❌ sqlite3")
        return False
    
    # Проверка Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()}")
        else:
            print("❌ Node.js не найден")
            return False
    except:
        print("❌ Node.js не найден")
        return False
    
    # Проверка npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ npm {result.stdout.strip()}")
        else:
            print("❌ npm не найден")
            return False
    except:
        print("❌ npm не найден")
        return False
    
    return True

def install_frontend_deps():
    """Установка зависимостей frontend"""
    node_modules = Path('aml-monitoring-frontend/node_modules')
    if node_modules.exists():
        print("✅ Frontend зависимости уже установлены")
        return True
    
    print("\n📦 Установка зависимостей frontend...")
    try:
        process = subprocess.Popen(
            ['npm', 'install'],
            cwd='aml-monitoring-frontend',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Показываем прогресс
        for line in process.stdout:
            if 'npm WARN' not in line:
                print(f"   {line.strip()}")
        
        process.wait()
        
        if process.returncode == 0:
            print("✅ Зависимости frontend установлены")
            return True
        else:
            print("❌ Ошибка установки зависимостей")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def start_backend():
    """Запуск backend"""
    print("\n🔧 Запуск backend сервера...")
    
    try:
        # Проверяем наличие app.py
        app_py = Path('aml-backend/app.py')
        if not app_py.exists():
            print("❌ Backend app.py не найден")
            return None
        
        # Запускаем backend
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'
        env['FLASK_DEBUG'] = '1'
        
        process = subprocess.Popen(
            [sys.executable, 'app.py'],
            cwd='aml-backend',
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        print(f"✅ Backend запущен (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Ошибка запуска backend: {e}")
        return None

def start_frontend():
    """Запуск frontend"""
    print("\n⚛️ Запуск frontend сервера...")
    
    try:
        env = os.environ.copy()
        env['PORT'] = '3000'
        env['VITE_BACKEND_URL'] = 'http://localhost:5000'
        
        process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd='aml-monitoring-frontend',
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        print(f"✅ Frontend запущен (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Ошибка запуска frontend: {e}")
        return None

def monitor_process(process, name):
    """Мониторинг вывода процесса"""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                line = line.strip()
                # Фильтруем шумные логи
                if not any(noise in line for noise in ['webpack compiled', 'Local:', '[HMR]']):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] {name}: {line}")
    except Exception as e:
        print(f"Ошибка мониторинга {name}: {e}")

def wait_for_services():
    """Ожидание готовности сервисов"""
    print("\n⏳ Ожидание готовности сервисов...")
    time.sleep(10)  # Даем время на запуск
    
    # Здесь можно добавить проверку доступности через HTTP запросы
    # Но для простоты просто ждем
    
    print("🎉 Сервисы должны быть готовы!")
    print(f"📱 Frontend: http://localhost:3000")
    print(f"🔗 Backend API: http://localhost:5000")

def main():
    """Главная функция"""
    print_banner()
    
    # Проверки
    if not check_files():
        print("\n❌ Проверка файлов не пройдена")
        return False
    
    if not check_dependencies():
        print("\n❌ Проверка зависимостей не пройдена")
        return False
    
    # Установка зависимостей frontend
    if not install_frontend_deps():
        print("\n❌ Не удалось установить зависимости frontend")
        return False
    
    # Запуск сервисов
    backend_process = start_backend()
    if not backend_process:
        print("\n❌ Не удалось запустить backend")
        return False
    
    time.sleep(5)  # Даем backend время на запуск
    
    frontend_process = start_frontend()
    if not frontend_process:
        print("\n❌ Не удалось запустить frontend")
        if backend_process:
            backend_process.terminate()
        return False
    
    # Запуск мониторинга в отдельных потоках
    backend_monitor = threading.Thread(
        target=monitor_process,
        args=(backend_process, "BACKEND"),
        daemon=True
    )
    backend_monitor.start()
    
    frontend_monitor = threading.Thread(
        target=monitor_process,
        args=(frontend_process, "FRONTEND"),
        daemon=True
    )
    frontend_monitor.start()
    
    # Ожидание готовности
    wait_for_services()
    
    print("\n💡 Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    try:
        # Ждем завершения
        while True:
            time.sleep(1)
            
            # Проверяем, что процессы еще живы
            if backend_process.poll() is not None:
                print("⚠️ Backend завершился неожиданно")
                break
            
            if frontend_process.poll() is not None:
                print("⚠️ Frontend завершился неожиданно")
                break
    
    except KeyboardInterrupt:
        print("\n⚠️ Получен сигнал завершения...")
    
    finally:
        # Корректное завершение
        print("🛑 Завершение процессов...")
        
        if backend_process and backend_process.poll() is None:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=10)
                print("✅ Backend завершен")
            except:
                backend_process.kill()
                print("🔨 Backend принудительно завершен")
        
        if frontend_process and frontend_process.poll() is None:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=10)
                print("✅ Frontend завершен")
            except:
                frontend_process.kill()
                print("🔨 Frontend принудительно завершен")
        
        print("🎉 Система остановлена")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)