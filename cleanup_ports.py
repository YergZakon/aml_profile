#!/usr/bin/env python3
"""
🧹 Очистка портов AML системы
Останавливает все процессы на портах 3000 и 5000
"""

import os
import signal
import subprocess
import time

def find_process_on_port(port):
    """Найти процесс на указанном порту"""
    try:
        # Используем ss для поиска процесса
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if f':{port}' in line and 'LISTEN' in line:
                # Извлекаем PID из строки вида "users:(("python3",pid=12345,fd=3))"
                if 'users:' in line:
                    users_part = line.split('users:')[1]
                    if 'pid=' in users_part:
                        pid_str = users_part.split('pid=')[1].split(',')[0]
                        try:
                            return int(pid_str)
                        except ValueError:
                            pass
        return None
    except Exception as e:
        print(f"Ошибка поиска процесса на порту {port}: {e}")
        return None

def kill_process(pid):
    """Остановить процесс по PID"""
    try:
        # Сначала пробуем мягкое завершение
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        
        # Проверяем, завершился ли процесс
        try:
            os.kill(pid, 0)  # Проверка существования процесса
            print(f"Процесс {pid} не завершился, применяю SIGKILL...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
        except ProcessLookupError:
            print(f"✅ Процесс {pid} успешно завершен")
            return True
            
    except ProcessLookupError:
        print(f"✅ Процесс {pid} уже завершен")
        return True
    except PermissionError:
        print(f"❌ Нет прав для завершения процесса {pid}")
        return False
    except Exception as e:
        print(f"❌ Ошибка при завершении процесса {pid}: {e}")
        return False
    
    return True

def cleanup_aml_ports():
    """Очистка портов AML системы"""
    ports_to_clean = [3000, 5000]
    
    print("🧹 ОЧИСТКА ПОРТОВ AML СИСТЕМЫ")
    print("=" * 40)
    
    for port in ports_to_clean:
        print(f"\n🔍 Проверка порта {port}...")
        pid = find_process_on_port(port)
        
        if pid:
            print(f"📍 Найден процесс {pid} на порту {port}")
            if kill_process(pid):
                print(f"✅ Порт {port} освобожден")
            else:
                print(f"❌ Не удалось освободить порт {port}")
        else:
            print(f"✅ Порт {port} свободен")
    
    # Дополнительно убиваем все процессы python3 app.py
    print(f"\n🔍 Поиск процессов python3 app.py...")
    try:
        result = subprocess.run(['pgrep', '-f', 'python3 app.py'], capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        
        for pid_str in pids:
            if pid_str:
                try:
                    pid = int(pid_str)
                    print(f"📍 Найден процесс python3 app.py: {pid}")
                    kill_process(pid)
                except ValueError:
                    pass
    except Exception as e:
        print(f"Ошибка поиска процессов: {e}")
    
    print(f"\n🎉 Очистка завершена!")

if __name__ == "__main__":
    cleanup_aml_ports()