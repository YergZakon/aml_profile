#!/usr/bin/env python3
"""
🚀 Быстрый запуск AML системы
Простой скрипт для мгновенного запуска всей системы
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def main():
    print("🚀 БЫСТРЫЙ ЗАПУСК AML СИСТЕМЫ")
    print("=" * 50)
    
    # Проверка наличия основных файлов
    required_files = [
        'aml_unified_launcher.py',
        'aml-backend/app.py',
        'aml-monitoring-frontend/package.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Отсутствуют необходимые файлы:")
        for file in missing_files:
            print(f"   • {file}")
        return
    
    print("✅ Проверка файлов завершена")
    
    # Установка зависимостей frontend если нужно
    node_modules = Path('aml-monitoring-frontend/node_modules')
    if not node_modules.exists():
        print("📦 Установка зависимостей frontend...")
        try:
            subprocess.run(
                ['npm', 'install'],
                cwd='aml-monitoring-frontend',
                check=True,
                capture_output=True
            )
            print("✅ Зависимости установлены")
        except subprocess.CalledProcessError:
            print("❌ Ошибка установки зависимостей")
            return
    
    # Запуск единого пайплайна
    print("\n🔧 Запуск единого пайплайна...")
    print("📱 Frontend: http://localhost:3000")
    print("🔗 Backend API: http://localhost:5000")
    print("💡 Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, 'aml_unified_launcher.py'
        ])
    except KeyboardInterrupt:
        print("\n⚠️ Остановка системы...")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    main()