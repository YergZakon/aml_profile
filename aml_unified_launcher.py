#!/usr/bin/env python3
"""
🚀 Единый пайплайн запуска AML системы
Версия: 3.0

Поддерживает:
- Одновременный запуск backend и frontend
- Мультипроцессорную обработку JSON файлов
- Параллельный анализ транзакций
- Мониторинг процессов и ресурсов
- Автоматическое управление жизненным циклом
"""

import os
import sys
import json
import time
import signal
import psutil
import logging
import argparse
import subprocess
import threading
import multiprocessing
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

# Добавляем путь к AML модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'aml-backend'))

@dataclass
class SystemConfig:
    """Конфигурация системы"""
    # Пути к компонентам
    backend_path: str = "aml-backend"
    frontend_path: str = "aml-monitoring-frontend"
    uploads_path: str = "uploads"
    database_path: str = "aml_system.db"
    
    # Настройки сервера
    backend_port: int = 5000
    frontend_port: int = 3000
    host: str = "localhost"
    
    # Настройки обработки
    max_workers: int = None
    batch_size: int = 100
    max_memory_mb: int = 4096
    
    # Настройки мониторинга
    log_level: str = "INFO"
    enable_monitoring: bool = True
    monitoring_interval: int = 5
    
    def __post_init__(self):
        if self.max_workers is None:
            self.max_workers = min(20, max(1, multiprocessing.cpu_count() - 2))

class SystemMonitor:
    """Монитор системных ресурсов и процессов"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.processes = {}
        self.monitoring = False
        self.stats = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'network_io': {'bytes_sent': 0, 'bytes_recv': 0},
            'processes_count': 0,
            'uptime': 0
        }
        
        # Настройка логирования
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(f'aml_system_{datetime.now().strftime("%Y%m%d")}.log')
            ]
        )
        self.logger = logging.getLogger('AMLMonitor')
    
    def start_monitoring(self):
        """Запуск мониторинга"""
        self.monitoring = True
        self.start_time = time.time()
        
        def monitor_loop():
            while self.monitoring:
                try:
                    self._update_stats()
                    time.sleep(self.config.monitoring_interval)
                except Exception as e:
                    self.logger.error(f"Ошибка мониторинга: {e}")
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        self.logger.info("Мониторинг системы запущен")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring = False
        self.logger.info("Мониторинг системы остановлен")
    
    def _update_stats(self):
        """Обновление статистики"""
        try:
            # CPU и память
            self.stats['cpu_usage'] = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            self.stats['memory_usage'] = memory.percent
            
            # Диск
            disk = psutil.disk_usage('/')
            self.stats['disk_usage'] = disk.percent
            
            # Сеть
            network = psutil.net_io_counters()
            self.stats['network_io'] = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv
            }
            
            # Процессы
            self.stats['processes_count'] = len([p for p in self.processes.values() if p and p.poll() is None])
            self.stats['uptime'] = time.time() - self.start_time
            
        except Exception as e:
            self.logger.warning(f"Ошибка обновления статистики: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Получение текущего статуса"""
        return {
            'stats': self.stats.copy(),
            'processes': {
                name: {
                    'pid': proc.pid if proc and proc.poll() is None else None,
                    'status': 'running' if proc and proc.poll() is None else 'stopped'
                }
                for name, proc in self.processes.items()
            },
            'config': {
                'max_workers': self.config.max_workers,
                'batch_size': self.config.batch_size,
                'max_memory_mb': self.config.max_memory_mb
            }
        }
    
    def print_status(self):
        """Вывод статуса в консоль"""
        status = self.get_status()
        
        print(f"\n📊 СТАТУС AML СИСТЕМЫ")
        print(f"{'='*60}")
        print(f"⏱️  Время работы: {status['stats']['uptime']:.1f} сек")
        print(f"💻 CPU: {status['stats']['cpu_usage']:.1f}%")
        print(f"🧠 RAM: {status['stats']['memory_usage']:.1f}%")
        print(f"💽 Диск: {status['stats']['disk_usage']:.1f}%")
        print(f"🔄 Активных процессов: {status['stats']['processes_count']}")
        
        print(f"\n🔧 ПРОЦЕССЫ:")
        for name, info in status['processes'].items():
            status_icon = "✅" if info['status'] == 'running' else "❌"
            pid_info = f"(PID: {info['pid']})" if info['pid'] else ""
            print(f"  {status_icon} {name}: {info['status']} {pid_info}")

class AMLUnifiedLauncher:
    """Главный класс единого пайплайна запуска"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.monitor = SystemMonitor(config)
        self.running = False
        self.shutdown_requested = False
        
        # Настройка обработчиков сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов завершения"""
        print(f"\n⚠️ Получен сигнал {signum}, начинаю корректное завершение...")
        self.shutdown_requested = True
        self.shutdown()
    
    def start_backend(self) -> subprocess.Popen:
        """Запуск backend сервера"""
        print(f"🔧 Запуск backend сервера на порту {self.config.backend_port}...")
        
        backend_dir = Path(self.config.backend_path)
        if not backend_dir.exists():
            raise FileNotFoundError(f"Backend директория не найдена: {backend_dir}")
        
        app_py = backend_dir / "app.py"
        if not app_py.exists():
            raise FileNotFoundError(f"app.py не найден: {app_py}")
        
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'
        env['FLASK_DEBUG'] = '1'
        env['PORT'] = str(self.config.backend_port)
        
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=backend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        self.monitor.processes['backend'] = process
        self.monitor.logger.info(f"Backend запущен (PID: {process.pid})")
        
        # Запускаем мониторинг вывода backend
        threading.Thread(
            target=self._monitor_process_output,
            args=(process, "BACKEND"),
            daemon=True
        ).start()
        
        return process
    
    def start_frontend(self) -> subprocess.Popen:
        """Запуск frontend сервера"""
        print(f"⚛️ Запуск frontend сервера на порту {self.config.frontend_port}...")
        
        frontend_dir = Path(self.config.frontend_path)
        if not frontend_dir.exists():
            raise FileNotFoundError(f"Frontend директория не найдена: {frontend_dir}")
        
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            raise FileNotFoundError(f"package.json не найден: {package_json}")
        
        # Проверяем наличие node_modules
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            print("📦 Установка зависимостей frontend...")
            npm_install = subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            if npm_install.returncode != 0:
                raise RuntimeError(f"Ошибка установки зависимостей: {npm_install.stderr}")
        
        env = os.environ.copy()
        env['PORT'] = str(self.config.frontend_port)
        env['VITE_BACKEND_URL'] = f"http://{self.config.host}:{self.config.backend_port}"
        
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        self.monitor.processes['frontend'] = process
        self.monitor.logger.info(f"Frontend запущен (PID: {process.pid})")
        
        # Запускаем мониторинг вывода frontend
        threading.Thread(
            target=self._monitor_process_output,
            args=(process, "FRONTEND"),
            daemon=True
        ).start()
        
        return process
    
    def _monitor_process_output(self, process: subprocess.Popen, name: str):
        """Мониторинг вывода процесса"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    # Фильтруем и форматируем вывод
                    line = line.strip()
                    if line and not self._should_filter_log(line):
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] {name}: {line}")
        except Exception as e:
            self.monitor.logger.error(f"Ошибка мониторинга {name}: {e}")
    
    def _should_filter_log(self, line: str) -> bool:
        """Фильтрация логов для уменьшения шума"""
        filters = [
            'webpack compiled',
            'Local:',
            'Network:',
            '[HMR]',
            'ready in',
            '✓ built in'
        ]
        return any(filter_text in line for filter_text in filters)
    
    def wait_for_services(self, timeout: int = 60):
        """Ожидание готовности сервисов"""
        print("⏳ Ожидание готовности сервисов...")
        
        import requests
        
        backend_ready = False
        frontend_ready = False
        start_time = time.time()
        
        while time.time() - start_time < timeout and not (backend_ready and frontend_ready):
            if not backend_ready:
                try:
                    response = requests.get(f"http://{self.config.host}:{self.config.backend_port}/api/health", timeout=1)
                    if response.status_code == 200:
                        backend_ready = True
                        print("✅ Backend готов")
                except:
                    pass
            
            if not frontend_ready:
                try:
                    response = requests.get(f"http://{self.config.host}:{self.config.frontend_port}", timeout=1)
                    if response.status_code == 200:
                        frontend_ready = True
                        print("✅ Frontend готов")
                except:
                    pass
            
            if not (backend_ready and frontend_ready):
                time.sleep(2)
        
        if backend_ready and frontend_ready:
            print("🎉 Все сервисы готовы!")
            return True
        else:
            print("⚠️ Некоторые сервисы не готовы в течение timeout")
            return False
    
    def process_json_files(self, json_files: List[str] = None, auto_discover: bool = True) -> Dict[str, Any]:
        """Обработка JSON файлов с мультипроцессорной поддержкой"""
        
        if not json_files and auto_discover:
            uploads_dir = Path(self.config.uploads_path)
            if uploads_dir.exists():
                json_files = list(uploads_dir.glob("*.json"))
                json_files = [str(f) for f in json_files]
        
        if not json_files:
            print("📁 JSON файлы не найдены для обработки")
            return {}
        
        print(f"\n🔍 ОБРАБОТКА JSON ФАЙЛОВ")
        print(f"{'='*60}")
        print(f"📁 Файлов найдено: {len(json_files)}")
        print(f"👥 Рабочих процессов: {self.config.max_workers}")
        print(f"📦 Размер батча: {self.config.batch_size}")
        
        try:
            # Импортируем пайплайн
            from aml_pipeline_enhanced import AMLPipelineEnhanced
            
            # Создаем пайплайн
            pipeline = AMLPipelineEnhanced(self.config.database_path)
            
            # Обрабатываем файлы
            results = pipeline.process_json_files(
                json_files=json_files,
                parallel_analysis=True,
                save_to_db=True
            )
            
            # Генерируем отчет
            if results:
                report_file = pipeline.generate_report(results)
                print(f"📄 Отчет сохранен: {report_file}")
            
            return results
            
        except Exception as e:
            self.monitor.logger.error(f"Ошибка обработки JSON: {e}")
            return {}
    
    def run_full_pipeline(self, 
                         start_services: bool = True,
                         process_files: bool = True,
                         json_files: List[str] = None) -> Dict[str, Any]:
        """Запуск полного пайплайна"""
        
        print(f"🚀 ЗАПУСК ЕДИНОГО AML ПАЙПЛАЙНА")
        print(f"{'='*60}")
        print(f"🕒 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💻 Система: {psutil.cpu_count()} CPU, {psutil.virtual_memory().total // (1024**3)} GB RAM")
        print(f"⚙️ Конфигурация:")
        print(f"   Backend: {self.config.host}:{self.config.backend_port}")
        print(f"   Frontend: {self.config.host}:{self.config.frontend_port}")
        print(f"   База данных: {self.config.database_path}")
        print(f"   Рабочих процессов: {self.config.max_workers}")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'services_started': False,
            'files_processed': False,
            'processing_results': {},
            'errors': []
        }
        
        try:
            self.running = True
            
            # Запускаем мониторинг
            if self.config.enable_monitoring:
                self.monitor.start_monitoring()
            
            # Запускаем сервисы
            if start_services:
                backend_process = self.start_backend()
                time.sleep(3)  # Даем backend время на запуск
                
                frontend_process = self.start_frontend()
                time.sleep(3)  # Даем frontend время на запуск
                
                # Ждем готовности сервисов
                if self.wait_for_services():
                    results['services_started'] = True
                    print(f"\n🌐 Система доступна:")
                    print(f"   Frontend: http://{self.config.host}:{self.config.frontend_port}")
                    print(f"   Backend API: http://{self.config.host}:{self.config.backend_port}/api")
                else:
                    results['errors'].append("Сервисы не готовы")
            
            # Обрабатываем файлы
            if process_files:
                processing_results = self.process_json_files(json_files)
                if processing_results:
                    results['files_processed'] = True
                    results['processing_results'] = processing_results
                    print("\n✅ Обработка файлов завершена успешно")
                else:
                    results['errors'].append("Ошибка обработки файлов")
            
            # Выводим итоговый статус
            if self.config.enable_monitoring:
                self.monitor.print_status()
            
            print(f"\n🎉 Пайплайн запущен успешно!")
            print(f"💡 Для остановки нажмите Ctrl+C")
            
            return results
            
        except Exception as e:
            error_msg = f"Критическая ошибка пайплайна: {e}"
            self.monitor.logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
    
    def shutdown(self):
        """Корректное завершение работы"""
        if not self.running:
            return
        
        print("\n🛑 Завершение работы AML системы...")
        self.running = False
        
        # Останавливаем мониторинг
        if self.config.enable_monitoring:
            self.monitor.stop_monitoring()
        
        # Завершаем процессы
        for name, process in self.monitor.processes.items():
            if process and process.poll() is None:
                print(f"⏹️ Завершение {name} (PID: {process.pid})...")
                try:
                    process.terminate()
                    process.wait(timeout=10)
                    print(f"✅ {name} завершен")
                except subprocess.TimeoutExpired:
                    print(f"⚠️ Принудительное завершение {name}")
                    process.kill()
                except Exception as e:
                    print(f"❌ Ошибка завершения {name}: {e}")
        
        print("🎉 Система остановлена")
    
    def interactive_mode(self):
        """Интерактивный режим управления"""
        try:
            while self.running and not self.shutdown_requested:
                time.sleep(1)
                
                # Проверяем состояние процессов
                for name, process in self.monitor.processes.items():
                    if process and process.poll() is not None:
                        print(f"⚠️ Процесс {name} завершился неожиданно")
                        self.monitor.logger.warning(f"Процесс {name} завершился с кодом {process.returncode}")
        
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()


def create_health_endpoint():
    """Создание health endpoint для backend"""
    health_code = """
@app.route('/api/health')
def health_check():
    '''Health check endpoint'''
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0'
    })
"""
    
    # Добавляем в app.py если его нет
    app_py_path = Path("aml-backend/app.py")
    if app_py_path.exists():
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '/api/health' not in content:
            # Находим место для вставки (после импортов)
            lines = content.split('\n')
            insert_pos = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('app = Flask'):
                    insert_pos = i + 1
                    break
            
            if insert_pos > 0:
                lines.insert(insert_pos, health_code)
                with open(app_py_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Единый пайплайн запуска AML системы')
    parser.add_argument('--backend-port', type=int, default=5000, help='Порт backend сервера')
    parser.add_argument('--frontend-port', type=int, default=3000, help='Порт frontend сервера')
    parser.add_argument('--workers', type=int, help='Количество рабочих процессов')
    parser.add_argument('--batch-size', type=int, default=100, help='Размер батча для обработки')
    parser.add_argument('--db-path', default='aml_system.db', help='Путь к базе данных')
    parser.add_argument('--uploads-path', default='uploads', help='Папка с JSON файлами')
    parser.add_argument('--no-services', action='store_true', help='Не запускать web сервисы')
    parser.add_argument('--no-processing', action='store_true', help='Не обрабатывать файлы')
    parser.add_argument('--json-files', nargs='+', help='Конкретные JSON файлы для обработки')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    parser.add_argument('--no-monitoring', action='store_true', help='Отключить мониторинг')
    
    args = parser.parse_args()
    
    # Создаем конфигурацию
    config = SystemConfig(
        backend_port=args.backend_port,
        frontend_port=args.frontend_port,
        max_workers=args.workers,
        batch_size=args.batch_size,
        database_path=args.db_path,
        uploads_path=args.uploads_path,
        log_level=args.log_level,
        enable_monitoring=not args.no_monitoring
    )
    
    # Создаем health endpoint
    create_health_endpoint()
    
    # Создаем и запускаем лаунчер
    launcher = AMLUnifiedLauncher(config)
    
    try:
        results = launcher.run_full_pipeline(
            start_services=not args.no_services,
            process_files=not args.no_processing,
            json_files=args.json_files
        )
        
        if results.get('services_started') and not args.no_services:
            # Интерактивный режим - ждем завершения
            launcher.interactive_mode()
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        launcher.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()