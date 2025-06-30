#!/usr/bin/env python3
"""
⚙️ Менеджер процессов AML системы
Версия: 3.0

Функции:
- Управление жизненным циклом процессов
- Мониторинг состояния сервисов
- Автоматический перезапуск при сбоях
- Балансировка нагрузки
- Graceful shutdown
"""

import os
import sys
import time
import json
import signal
import psutil
import logging
import threading
import subprocess
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

# Импорт конфигурации
try:
    from aml_config import get_config
except ImportError:
    print("⚠️ Модуль aml_config не найден, используются дефолтные настройки")
    get_config = lambda: None


class ProcessState(Enum):
    """Состояния процесса"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    RESTARTING = "restarting"


@dataclass
class ProcessInfo:
    """Информация о процессе"""
    name: str
    command: List[str]
    cwd: str
    env: Dict[str, str] = field(default_factory=dict)
    
    # Состояние
    state: ProcessState = ProcessState.STOPPED
    pid: Optional[int] = None
    process: Optional[subprocess.Popen] = None
    
    # Статистика
    start_time: Optional[datetime] = None
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    
    # Настройки перезапуска
    auto_restart: bool = True
    max_restarts: int = 5
    restart_delay: float = 10.0
    
    # Мониторинг
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    last_heartbeat: Optional[datetime] = None


class ProcessManager:
    """Менеджер процессов AML системы"""
    
    def __init__(self):
        self.processes: Dict[str, ProcessInfo] = {}
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.shutdown_requested = False
        
        # Настройка логирования
        self.setup_logging()
        
        # Загрузка конфигурации
        self.config = get_config()
        
        # Обработчики событий
        self.event_handlers: Dict[str, List[Callable]] = {
            'process_started': [],
            'process_stopped': [],
            'process_failed': [],
            'process_restarted': []
        }
        
        # Регистрация обработчиков сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def setup_logging(self):
        """Настройка логирования"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Создаем папку для логов
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(f'logs/process_manager_{datetime.now().strftime("%Y%m%d")}.log')
            ]
        )
        
        self.logger = logging.getLogger('ProcessManager')
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов завершения"""
        self.logger.info(f"Получен сигнал {signum}, начинаю корректное завершение...")
        self.shutdown_requested = True
        self.stop_all_processes()
    
    def register_process(self, 
                        name: str,
                        command: List[str],
                        cwd: str = ".",
                        env: Dict[str, str] = None,
                        auto_restart: bool = True,
                        max_restarts: int = 5,
                        restart_delay: float = 10.0) -> ProcessInfo:
        """Регистрация процесса"""
        
        if name in self.processes:
            raise ValueError(f"Процесс {name} уже зарегистрирован")
        
        process_info = ProcessInfo(
            name=name,
            command=command,
            cwd=cwd,
            env=env or {},
            auto_restart=auto_restart,
            max_restarts=max_restarts,
            restart_delay=restart_delay
        )
        
        self.processes[name] = process_info
        self.logger.info(f"Зарегистрирован процесс: {name}")
        
        return process_info
    
    def start_process(self, name: str) -> bool:
        """Запуск процесса"""
        if name not in self.processes:
            self.logger.error(f"Процесс {name} не найден")
            return False
        
        process_info = self.processes[name]
        
        if process_info.state == ProcessState.RUNNING:
            self.logger.warning(f"Процесс {name} уже запущен")
            return True
        
        try:
            self.logger.info(f"Запуск процесса: {name}")
            process_info.state = ProcessState.STARTING
            
            # Подготовка окружения
            env = os.environ.copy()
            env.update(process_info.env)
            
            # Запуск процесса
            process = subprocess.Popen(
                process_info.command,
                cwd=process_info.cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Обновление информации
            process_info.process = process
            process_info.pid = process.pid
            process_info.state = ProcessState.RUNNING
            process_info.start_time = datetime.now()
            process_info.last_heartbeat = datetime.now()
            
            self.logger.info(f"Процесс {name} запущен (PID: {process.pid})")
            
            # Запуск мониторинга вывода
            self._start_output_monitor(process_info)
            
            # Уведомление о событии
            self._trigger_event('process_started', process_info)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска процесса {name}: {e}")
            process_info.state = ProcessState.FAILED
            self._trigger_event('process_failed', process_info)
            return False
    
    def stop_process(self, name: str, timeout: float = 30.0) -> bool:
        """Остановка процесса"""
        if name not in self.processes:
            self.logger.error(f"Процесс {name} не найден")
            return False
        
        process_info = self.processes[name]
        
        if process_info.state != ProcessState.RUNNING:
            self.logger.warning(f"Процесс {name} не запущен")
            return True
        
        try:
            self.logger.info(f"Остановка процесса: {name}")
            process_info.state = ProcessState.STOPPING
            
            process = process_info.process
            if process:
                # Graceful shutdown
                process.terminate()
                
                # Ждем завершения
                try:
                    process.wait(timeout=timeout)
                    self.logger.info(f"Процесс {name} завершен корректно")
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Принудительное завершение процесса {name}")
                    process.kill()
                    process.wait()
            
            # Обновление состояния
            process_info.state = ProcessState.STOPPED
            process_info.process = None
            process_info.pid = None
            
            # Уведомление о событии
            self._trigger_event('process_stopped', process_info)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка остановки процесса {name}: {e}")
            return False
    
    def restart_process(self, name: str) -> bool:
        """Перезапуск процесса"""
        if name not in self.processes:
            self.logger.error(f"Процесс {name} не найден")
            return False
        
        process_info = self.processes[name]
        
        self.logger.info(f"Перезапуск процесса: {name}")
        process_info.state = ProcessState.RESTARTING
        
        # Останавливаем
        self.stop_process(name)
        
        # Пауза перед перезапуском
        time.sleep(process_info.restart_delay)
        
        # Запускаем
        success = self.start_process(name)
        
        if success:
            process_info.restart_count += 1
            process_info.last_restart = datetime.now()
            self._trigger_event('process_restarted', process_info)
            self.logger.info(f"Процесс {name} перезапущен (попытка {process_info.restart_count})")
        
        return success
    
    def start_monitoring(self, interval: float = 5.0):
        """Запуск мониторинга процессов"""
        if self.monitoring:
            self.logger.warning("Мониторинг уже запущен")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.info("Мониторинг процессов запущен")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        self.logger.info("Мониторинг процессов остановлен")
    
    def _monitor_loop(self, interval: float):
        """Цикл мониторинга"""
        while self.monitoring and not self.shutdown_requested:
            try:
                self._check_processes()
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Ошибка в мониторинге: {e}")
    
    def _check_processes(self):
        """Проверка состояния процессов"""
        for name, process_info in self.processes.items():
            if process_info.state == ProcessState.RUNNING:
                self._update_process_stats(process_info)
                
                # Проверка на зависание
                if self._is_process_alive(process_info):
                    process_info.last_heartbeat = datetime.now()
                else:
                    self.logger.warning(f"Процесс {name} завис или завершился")
                    self._handle_process_failure(process_info)
    
    def _update_process_stats(self, process_info: ProcessInfo):
        """Обновление статистики процесса"""
        try:
            if process_info.pid:
                proc = psutil.Process(process_info.pid)
                process_info.cpu_percent = proc.cpu_percent()
                process_info.memory_mb = proc.memory_info().rss / (1024 * 1024)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    def _is_process_alive(self, process_info: ProcessInfo) -> bool:
        """Проверка жизнеспособности процесса"""
        if not process_info.process:
            return False
        
        # Проверка статуса процесса
        if process_info.process.poll() is not None:
            return False
        
        # Проверка через psutil
        try:
            if process_info.pid:
                proc = psutil.Process(process_info.pid)
                return proc.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
        
        return True
    
    def _handle_process_failure(self, process_info: ProcessInfo):
        """Обработка сбоя процесса"""
        process_info.state = ProcessState.FAILED
        self._trigger_event('process_failed', process_info)
        
        # Автоматический перезапуск
        if (process_info.auto_restart and 
            process_info.restart_count < process_info.max_restarts):
            
            self.logger.info(f"Автоматический перезапуск процесса: {process_info.name}")
            threading.Thread(
                target=self.restart_process,
                args=(process_info.name,),
                daemon=True
            ).start()
        else:
            self.logger.error(f"Процесс {process_info.name} не может быть перезапущен")
    
    def _start_output_monitor(self, process_info: ProcessInfo):
        """Запуск мониторинга вывода процесса"""
        def monitor_output():
            try:
                for line in iter(process_info.process.stdout.readline, ''):
                    if line:
                        line = line.strip()
                        if line and not self._should_filter_log(line):
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"[{timestamp}] {process_info.name}: {line}")
            except Exception as e:
                self.logger.error(f"Ошибка мониторинга вывода {process_info.name}: {e}")
        
        threading.Thread(target=monitor_output, daemon=True).start()
    
    def _should_filter_log(self, line: str) -> bool:
        """Фильтрация шумных логов"""
        filters = [
            'webpack compiled',
            'Local:', 'Network:',
            '[HMR]', 'ready in',
            '✓ built in'
        ]
        return any(filter_text in line for filter_text in filters)
    
    def _trigger_event(self, event_name: str, process_info: ProcessInfo):
        """Триггер события"""
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                try:
                    handler(process_info)
                except Exception as e:
                    self.logger.error(f"Ошибка в обработчике события {event_name}: {e}")
    
    def add_event_handler(self, event_name: str, handler: Callable):
        """Добавление обработчика события"""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
    
    def get_process_status(self, name: str = None) -> Dict[str, Any]:
        """Получение статуса процессов"""
        if name:
            if name in self.processes:
                return self._process_info_to_dict(self.processes[name])
            else:
                return {}
        
        return {
            name: self._process_info_to_dict(info)
            for name, info in self.processes.items()
        }
    
    def _process_info_to_dict(self, process_info: ProcessInfo) -> Dict[str, Any]:
        """Преобразование ProcessInfo в словарь"""
        return {
            'name': process_info.name,
            'state': process_info.state.value,
            'pid': process_info.pid,
            'start_time': process_info.start_time.isoformat() if process_info.start_time else None,
            'restart_count': process_info.restart_count,
            'last_restart': process_info.last_restart.isoformat() if process_info.last_restart else None,
            'cpu_percent': process_info.cpu_percent,
            'memory_mb': process_info.memory_mb,
            'last_heartbeat': process_info.last_heartbeat.isoformat() if process_info.last_heartbeat else None,
            'auto_restart': process_info.auto_restart,
            'max_restarts': process_info.max_restarts
        }
    
    def start_all_processes(self) -> Dict[str, bool]:
        """Запуск всех процессов"""
        results = {}
        for name in self.processes:
            results[name] = self.start_process(name)
        return results
    
    def stop_all_processes(self) -> Dict[str, bool]:
        """Остановка всех процессов"""
        results = {}
        for name in self.processes:
            results[name] = self.stop_process(name)
        return results
    
    def print_status(self):
        """Вывод статуса всех процессов"""
        print(f"\n📊 СТАТУС ПРОЦЕССОВ AML СИСТЕМЫ")
        print(f"{'='*70}")
        
        if not self.processes:
            print("Нет зарегистрированных процессов")
            return
        
        for name, info in self.processes.items():
            state_icon = {
                ProcessState.STOPPED: "⏹️",
                ProcessState.STARTING: "🔄",
                ProcessState.RUNNING: "✅",
                ProcessState.STOPPING: "⏸️",
                ProcessState.FAILED: "❌",
                ProcessState.RESTARTING: "🔃"
            }.get(info.state, "❓")
            
            uptime = ""
            if info.start_time and info.state == ProcessState.RUNNING:
                delta = datetime.now() - info.start_time
                uptime = f"({delta.total_seconds():.0f}s)"
            
            restart_info = ""
            if info.restart_count > 0:
                restart_info = f" (перезапусков: {info.restart_count})"
            
            resource_info = ""
            if info.state == ProcessState.RUNNING:
                resource_info = f" [CPU: {info.cpu_percent:.1f}%, RAM: {info.memory_mb:.1f}MB]"
            
            print(f"{state_icon} {name:<15} {info.state.value:<10} "
                  f"PID: {info.pid or 'N/A':<6} {uptime:<8} "
                  f"{restart_info}{resource_info}")
    
    def save_state(self, filepath: str = "process_manager_state.json"):
        """Сохранение состояния в файл"""
        try:
            state_data = {
                'timestamp': datetime.now().isoformat(),
                'processes': {
                    name: {
                        'command': info.command,
                        'cwd': info.cwd,
                        'env': info.env,
                        'auto_restart': info.auto_restart,
                        'max_restarts': info.max_restarts,
                        'restart_delay': info.restart_delay,
                        'restart_count': info.restart_count
                    }
                    for name, info in self.processes.items()
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Состояние сохранено в {filepath}")
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения состояния: {e}")
    
    def load_state(self, filepath: str = "process_manager_state.json"):
        """Загрузка состояния из файла"""
        try:
            if not os.path.exists(filepath):
                self.logger.info(f"Файл состояния {filepath} не найден")
                return
            
            with open(filepath, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            for name, proc_data in state_data.get('processes', {}).items():
                self.register_process(
                    name=name,
                    command=proc_data['command'],
                    cwd=proc_data.get('cwd', '.'),
                    env=proc_data.get('env', {}),
                    auto_restart=proc_data.get('auto_restart', True),
                    max_restarts=proc_data.get('max_restarts', 5),
                    restart_delay=proc_data.get('restart_delay', 10.0)
                )
                
                # Восстанавливаем счетчик перезапусков
                self.processes[name].restart_count = proc_data.get('restart_count', 0)
            
            self.logger.info(f"Состояние загружено из {filepath}")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки состояния: {e}")


def create_aml_process_manager() -> ProcessManager:
    """Создание предконфигурированного менеджера процессов для AML"""
    manager = ProcessManager()
    
    # Регистрация AML backend
    manager.register_process(
        name="aml-backend",
        command=[sys.executable, "app.py"],
        cwd="aml-backend",
        env={
            'FLASK_ENV': 'development',
            'FLASK_DEBUG': '1',
            'PORT': '5000'
        }
    )
    
    # Регистрация AML frontend
    manager.register_process(
        name="aml-frontend",
        command=["npm", "run", "dev"],
        cwd="aml-monitoring-frontend",
        env={
            'PORT': '3000',
            'VITE_BACKEND_URL': 'http://localhost:5000'
        }
    )
    
    return manager


if __name__ == "__main__":
    # Пример использования
    import argparse
    
    parser = argparse.ArgumentParser(description='Менеджер процессов AML системы')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'monitor'],
                       help='Действие')
    parser.add_argument('--process', help='Имя конкретного процесса')
    parser.add_argument('--save-state', action='store_true', help='Сохранить состояние')
    parser.add_argument('--load-state', action='store_true', help='Загрузить состояние')
    
    args = parser.parse_args()
    
    # Создаем менеджер
    manager = create_aml_process_manager()
    
    # Загружаем состояние если нужно
    if args.load_state:
        manager.load_state()
    
    try:
        if args.action == 'start':
            if args.process:
                manager.start_process(args.process)
            else:
                manager.start_all_processes()
                manager.start_monitoring()
        
        elif args.action == 'stop':
            if args.process:
                manager.stop_process(args.process)
            else:
                manager.stop_all_processes()
        
        elif args.action == 'restart':
            if args.process:
                manager.restart_process(args.process)
            else:
                manager.stop_all_processes()
                time.sleep(2)
                manager.start_all_processes()
        
        elif args.action == 'status':
            manager.print_status()
        
        elif args.action == 'monitor':
            manager.start_all_processes()
            manager.start_monitoring()
            
            print("🎯 Мониторинг запущен. Нажмите Ctrl+C для выхода.")
            try:
                while True:
                    time.sleep(5)
                    manager.print_status()
                    print(f"\n{'-'*70}")
            except KeyboardInterrupt:
                print("\n⚠️ Завершение мониторинга...")
        
        # Сохраняем состояние если нужно
        if args.save_state:
            manager.save_state()
            
    except KeyboardInterrupt:
        print("\n⚠️ Получен сигнал завершения...")
    finally:
        manager.stop_all_processes()
        manager.stop_monitoring()