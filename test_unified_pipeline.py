#!/usr/bin/env python3
"""
🧪 Тестирование единого пайплайна AML системы
Версия: 3.0

Комплексное тестирование:
- Проверка всех компонентов системы
- Тестирование мультипроцессорной обработки
- Проверка производительности
- Валидация результатов анализа
"""

import os
import sys
import time
import json
import psutil
import requests
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
import tempfile

# Добавляем пути для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from aml_unified_launcher import AMLUnifiedLauncher, SystemConfig
    from aml_process_manager import ProcessManager, create_aml_process_manager
    from aml_monitoring import get_monitor
    from aml_config import get_config
except ImportError as e:
    print(f"❌ Ошибка импорта модулей: {e}")
    print("Убедитесь, что все файлы находятся в правильных директориях")
    sys.exit(1)


class AMLPipelineTest:
    """Класс для тестирования AML пайплайна"""
    
    def __init__(self):
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'overall_success': False,
            'summary': {}
        }
        self.config = get_config()
        self.monitor = get_monitor()
        self.temp_files = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Запуск всех тестов"""
        print("🧪 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ AML ПАЙПЛАЙНА")
        print("=" * 70)
        
        tests = [
            ('configuration_test', self.test_configuration),
            ('dependencies_test', self.test_dependencies),
            ('file_structure_test', self.test_file_structure),
            ('backend_launch_test', self.test_backend_launch),
            ('frontend_launch_test', self.test_frontend_launch),
            ('json_processing_test', self.test_json_processing),
            ('multiprocessing_test', self.test_multiprocessing),
            ('monitoring_test', self.test_monitoring),
            ('api_endpoints_test', self.test_api_endpoints),
            ('performance_test', self.test_performance)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Выполняется тест: {test_name}")
            print("-" * 50)
            
            try:
                start_time = time.time()
                result = test_func()
                end_time = time.time()
                
                self.test_results['tests'][test_name] = {
                    'success': result.get('success', False),
                    'duration': end_time - start_time,
                    'details': result.get('details', {}),
                    'message': result.get('message', ''),
                    'timestamp': datetime.now().isoformat()
                }
                
                if result.get('success', False):
                    print(f"✅ {test_name}: ПРОЙДЕН")
                    passed_tests += 1
                else:
                    print(f"❌ {test_name}: ПРОВАЛЕН - {result.get('message', 'Неизвестная ошибка')}")
                    
            except Exception as e:
                print(f"💥 {test_name}: КРИТИЧЕСКАЯ ОШИБКА - {e}")
                self.test_results['tests'][test_name] = {
                    'success': False,
                    'duration': 0,
                    'details': {'error': str(e)},
                    'message': f'Критическая ошибка: {e}',
                    'timestamp': datetime.now().isoformat()
                }
        
        # Общий результат
        self.test_results['overall_success'] = passed_tests == total_tests
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests) * 100,
            'end_time': datetime.now().isoformat()
        }
        
        self.cleanup()
        self.print_final_report()
        
        return self.test_results
    
    def test_configuration(self) -> Dict[str, Any]:
        """Тест конфигурации"""
        try:
            # Проверка загрузки конфигурации
            if not self.config:
                return {
                    'success': False,
                    'message': 'Конфигурация не загружена'
                }
            
            # Валидация конфигурации
            if not self.config.validate_configuration():
                return {
                    'success': False,
                    'message': 'Конфигурация не прошла валидацию'
                }
            
            details = {
                'max_workers': self.config.processing.max_workers,
                'batch_size': self.config.processing.batch_size,
                'database_path': self.config.database.database_path
            }
            
            return {
                'success': True,
                'message': 'Конфигурация корректна',
                'details': details
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка конфигурации: {e}'
            }
    
    def test_dependencies(self) -> Dict[str, Any]:
        """Тест зависимостей"""
        try:
            missing_deps = []
            
            # Проверка Python модулей
            required_modules = [
                'flask', 'flask_cors', 'psutil', 'requests', 'numpy', 
                'pandas', 'networkx', 'sqlite3'
            ]
            
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_deps.append(f"Python: {module}")
            
            # Проверка системных команд
            system_commands = ['npm', 'node']
            for cmd in system_commands:
                try:
                    result = subprocess.run([cmd, '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode != 0:
                        missing_deps.append(f"System: {cmd}")
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    missing_deps.append(f"System: {cmd}")
            
            if missing_deps:
                return {
                    'success': False,
                    'message': f'Отсутствуют зависимости: {", ".join(missing_deps)}',
                    'details': {'missing': missing_deps}
                }
            
            return {
                'success': True,
                'message': 'Все зависимости установлены',
                'details': {'checked_modules': required_modules, 'checked_commands': system_commands}
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка проверки зависимостей: {e}'
            }
    
    def test_file_structure(self) -> Dict[str, Any]:
        """Тест структуры файлов"""
        try:
            required_files = [
                'aml_unified_launcher.py',
                'aml_config.py',
                'aml_process_manager.py',
                'aml_monitoring.py',
                'aml-backend/app.py',
                'aml-backend/aml_database_setup.py',
                'aml-backend/aml_integration_system.py',
                'aml-backend/aml_pipeline_enhanced.py',
                'aml-monitoring-frontend/package.json',
                'aml-monitoring-frontend/src/app.jsx'
            ]
            
            missing_files = []
            for file_path in required_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            required_dirs = [
                'aml-backend',
                'aml-monitoring-frontend',
                'aml-monitoring-frontend/src'
            ]
            
            missing_dirs = []
            for dir_path in required_dirs:
                if not Path(dir_path).exists():
                    missing_dirs.append(dir_path)
            
            if missing_files or missing_dirs:
                return {
                    'success': False,
                    'message': 'Отсутствуют необходимые файлы или директории',
                    'details': {
                        'missing_files': missing_files,
                        'missing_dirs': missing_dirs
                    }
                }
            
            return {
                'success': True,
                'message': 'Структура файлов корректна',
                'details': {
                    'checked_files': len(required_files),
                    'checked_dirs': len(required_dirs)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка проверки структуры: {e}'
            }
    
    def test_backend_launch(self) -> Dict[str, Any]:
        """Тест запуска backend"""
        try:
            # Создаем процесс-менеджер
            manager = create_aml_process_manager()
            
            # Запускаем backend
            if not manager.start_process('aml-backend'):
                return {
                    'success': False,
                    'message': 'Не удалось запустить backend'
                }
            
            # Ждем запуска
            time.sleep(5)
            
            # Проверяем доступность
            try:
                response = requests.get('http://localhost:5000/api/health', timeout=10)
                if response.status_code == 200:
                    manager.stop_process('aml-backend')
                    return {
                        'success': True,
                        'message': 'Backend запущен и отвечает',
                        'details': {'response_time': response.elapsed.total_seconds()}
                    }
                else:
                    manager.stop_process('aml-backend')
                    return {
                        'success': False,
                        'message': f'Backend вернул код {response.status_code}'
                    }
                    
            except requests.RequestException as e:
                manager.stop_process('aml-backend')
                return {
                    'success': False,
                    'message': f'Backend недоступен: {e}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка тестирования backend: {e}'
            }
    
    def test_frontend_launch(self) -> Dict[str, Any]:
        """Тест запуска frontend"""
        try:
            # Проверяем наличие package.json
            package_json = Path('aml-monitoring-frontend/package.json')
            if not package_json.exists():
                return {
                    'success': False,
                    'message': 'package.json не найден'
                }
            
            # Проверяем node_modules
            node_modules = Path('aml-monitoring-frontend/node_modules')
            if not node_modules.exists():
                print("📦 Установка зависимостей frontend...")
                result = subprocess.run(
                    ['npm', 'install'],
                    cwd='aml-monitoring-frontend',
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode != 0:
                    return {
                        'success': False,
                        'message': f'Ошибка установки зависимостей: {result.stderr}'
                    }
            
            return {
                'success': True,
                'message': 'Frontend готов к запуску',
                'details': {'dependencies_installed': True}
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка тестирования frontend: {e}'
            }
    
    def test_json_processing(self) -> Dict[str, Any]:
        """Тест обработки JSON файлов"""
        try:
            # Создаем тестовый JSON файл
            test_data = self.create_test_json_data()
            test_file = self.save_test_json(test_data)
            
            # Импортируем пайплайн
            from aml_pipeline_enhanced import AMLPipelineEnhanced
            
            # Создаем пайплайн
            pipeline = AMLPipelineEnhanced('test_aml_system.db')
            
            # Обрабатываем файл
            transactions = pipeline.load_json_file(test_file)
            
            if not transactions:
                return {
                    'success': False,
                    'message': 'Не удалось загрузить транзакции из JSON'
                }
            
            # Тестируем анализ
            results = pipeline._analyze_transactions_sequential(transactions[:10])
            
            if not results.get('total_processed', 0) > 0:
                return {
                    'success': False,
                    'message': 'Анализ транзакций не дал результатов'
                }
            
            return {
                'success': True,
                'message': 'JSON обработка работает корректно',
                'details': {
                    'transactions_loaded': len(transactions),
                    'transactions_analyzed': results.get('total_processed', 0),
                    'processing_time': results.get('processing_time', 0)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка тестирования JSON: {e}'
            }
    
    def test_multiprocessing(self) -> Dict[str, Any]:
        """Тест мультипроцессорной обработки"""
        try:
            # Создаем больше тестовых данных
            test_data = []
            for i in range(500):  # 500 транзакций
                test_data.extend(self.create_test_json_data())
            
            test_file = self.save_test_json(test_data)
            
            # Импортируем пайплайн
            from aml_pipeline_enhanced import AMLPipelineEnhanced
            
            # Создаем пайплайн
            pipeline = AMLPipelineEnhanced('test_aml_system_mp.db')
            
            # Тестируем параллельную обработку
            start_time = time.time()
            results = pipeline.process_json_files(
                json_files=[test_file],
                parallel_analysis=True,
                save_to_db=False
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            if not results.get('total_processed', 0) > 0:
                return {
                    'success': False,
                    'message': 'Параллельная обработка не дала результатов'
                }
            
            # Проверяем скорость
            transactions_per_second = results.get('transactions_per_second', 0)
            if transactions_per_second < 1:
                return {
                    'success': False,
                    'message': f'Слишком низкая скорость обработки: {transactions_per_second:.2f} тр/сек'
                }
            
            return {
                'success': True,
                'message': 'Мультипроцессорная обработка работает',
                'details': {
                    'total_processed': results.get('total_processed', 0),
                    'processing_time': processing_time,
                    'transactions_per_second': transactions_per_second,
                    'workers_used': self.config.processing.max_workers if self.config else 'unknown'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка тестирования мультипроцессинга: {e}'
            }
    
    def test_monitoring(self) -> Dict[str, Any]:
        """Тест системы мониторинга"""
        try:
            # Запускаем мониторинг
            self.monitor.start_monitoring(interval=1.0)
            
            # Записываем тестовые метрики
            self.monitor.record_processing_metric('test_metric', 100)
            self.monitor.record_analysis_metric('test_analysis', 50, 2.5)
            
            # Ждем сбора метрик
            time.sleep(3)
            
            # Проверяем dashboard
            dashboard_data = self.monitor.get_dashboard_data()
            
            if not dashboard_data:
                return {
                    'success': False,
                    'message': 'Dashboard не возвращает данные'
                }
            
            # Проверяем наличие системных метрик
            system_metrics = dashboard_data.get('system_metrics', {})
            if not system_metrics:
                return {
                    'success': False,
                    'message': 'Системные метрики не собираются'
                }
            
            # Останавливаем мониторинг
            self.monitor.stop_monitoring()
            
            return {
                'success': True,
                'message': 'Система мониторинга работает',
                'details': {
                    'system_metrics_count': len(system_metrics),
                    'has_cpu_metric': 'system.cpu_percent' in system_metrics,
                    'has_memory_metric': 'system.memory_percent' in system_metrics
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка тестирования мониторинга: {e}'
            }
    
    def test_api_endpoints(self) -> Dict[str, Any]:
        """Тест API endpoints"""
        try:
            # Запускаем backend
            manager = create_aml_process_manager()
            if not manager.start_process('aml-backend'):
                return {
                    'success': False,
                    'message': 'Не удалось запустить backend для тестирования API'
                }
            
            time.sleep(5)
            
            # Тестируем endpoints
            endpoints_to_test = [
                '/api/health',
                '/api/analytics/dashboard',
                '/api/transactions'
            ]
            
            results = {}
            all_passed = True
            
            for endpoint in endpoints_to_test:
                try:
                    url = f'http://localhost:5000{endpoint}'
                    response = requests.get(url, timeout=10)
                    
                    results[endpoint] = {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'success': response.status_code == 200
                    }
                    
                    if response.status_code != 200:
                        all_passed = False
                        
                except requests.RequestException as e:
                    results[endpoint] = {
                        'error': str(e),
                        'success': False
                    }
                    all_passed = False
            
            manager.stop_process('aml-backend')
            
            return {
                'success': all_passed,
                'message': 'Все API endpoints работают' if all_passed else 'Некоторые API endpoints недоступны',
                'details': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка тестирования API: {e}'
            }
    
    def test_performance(self) -> Dict[str, Any]:
        """Тест производительности"""
        try:
            # Измеряем использование ресурсов
            initial_memory = psutil.virtual_memory().percent
            initial_cpu = psutil.cpu_percent(interval=1)
            
            # Запускаем нагрузочный тест
            test_data = []
            for i in range(100):  # 100 транзакций
                test_data.extend(self.create_test_json_data())
            
            test_file = self.save_test_json(test_data)
            
            from aml_pipeline_enhanced import AMLPipelineEnhanced
            pipeline = AMLPipelineEnhanced('test_performance.db')
            
            start_time = time.time()
            start_memory = psutil.virtual_memory().percent
            
            results = pipeline.process_json_files(
                json_files=[test_file],
                parallel_analysis=True,
                save_to_db=False
            )
            
            end_time = time.time()
            end_memory = psutil.virtual_memory().percent
            
            processing_time = end_time - start_time
            memory_usage = end_memory - start_memory
            
            # Критерии производительности
            min_speed = 10  # транзакций в секунду
            max_memory_increase = 20  # процентов
            max_processing_time = 60  # секунд
            
            speed = results.get('transactions_per_second', 0)
            
            performance_issues = []
            if speed < min_speed:
                performance_issues.append(f"Низкая скорость: {speed:.2f} тр/сек")
            if memory_usage > max_memory_increase:
                performance_issues.append(f"Высокое потребление памяти: +{memory_usage:.1f}%")
            if processing_time > max_processing_time:
                performance_issues.append(f"Долгая обработка: {processing_time:.1f}сек")
            
            success = len(performance_issues) == 0
            
            return {
                'success': success,
                'message': 'Производительность в норме' if success else f"Проблемы: {'; '.join(performance_issues)}",
                'details': {
                    'processing_time': processing_time,
                    'transactions_per_second': speed,
                    'memory_usage_increase': memory_usage,
                    'total_processed': results.get('total_processed', 0),
                    'performance_issues': performance_issues
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка тестирования производительности: {e}'
            }
    
    def create_test_json_data(self) -> List[Dict]:
        """Создание тестовых JSON данных"""
        return [
            {
                "row_to_json": {
                    "gmess_id": f"TEST_{int(time.time() * 1000)}",
                    "goper_trans_date": datetime.now().isoformat(),
                    "goper_tenge_amount": "1500000.00",
                    "goper_dopinfo": "Тестовая транзакция",
                    "gmember1_maincode": "TEST001",
                    "gmember1_ur_name": "ТОО ТЕСТОВАЯ КОМПАНИЯ 1",
                    "gmember1_bank_address": "Алматы",
                    "gmember_residence_pol1": "KZ",
                    "gmember2_maincode": "TEST002", 
                    "gmember2_ur_name": "ТОО ТЕСТОВАЯ КОМПАНИЯ 2",
                    "gmember2_bank_address": "Нур-Султан",
                    "gmember_residence_pl2": "KZ",
                    "goper_susp_first": None,
                    "goper_susp_second": None,
                    "goper_susp_third": None,
                    "gmess_oper_status": "COMPLETED",
                    "gmess_reason_code": "001"
                }
            }
        ]
    
    def save_test_json(self, data: List[Dict]) -> str:
        """Сохранение тестовых данных в файл"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            temp_file = f.name
        
        self.temp_files.append(temp_file)
        return temp_file
    
    def cleanup(self):
        """Очистка временных файлов"""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        
        # Удаление тестовых БД
        test_dbs = ['test_aml_system.db', 'test_aml_system_mp.db', 'test_performance.db']
        for db_file in test_dbs:
            try:
                if os.path.exists(db_file):
                    os.unlink(db_file)
            except OSError:
                pass
    
    def print_final_report(self):
        """Вывод финального отчета"""
        print("\n" + "=" * 70)
        print("📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 70)
        
        summary = self.test_results['summary']
        
        # Общая статистика
        print(f"📊 Общая статистика:")
        print(f"   Всего тестов: {summary['total_tests']}")
        print(f"   Пройдено: {summary['passed_tests']}")
        print(f"   Провалено: {summary['failed_tests']}")
        print(f"   Процент успеха: {summary['success_rate']:.1f}%")
        
        # Статус
        if self.test_results['overall_success']:
            print(f"\n🎉 РЕЗУЛЬТАТ: ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print(f"✅ Система готова к использованию")
        else:
            print(f"\n⚠️ РЕЗУЛЬТАТ: ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
            print(f"❌ Необходимо исправить ошибки перед использованием")
        
        # Детали по каждому тесту
        print(f"\n📝 Детали тестов:")
        for test_name, test_result in self.test_results['tests'].items():
            status_icon = "✅" if test_result['success'] else "❌"
            duration = test_result['duration']
            message = test_result['message']
            print(f"   {status_icon} {test_name:<25} ({duration:.2f}с) - {message}")
        
        # Сохранение отчета
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n💾 Детальный отчет сохранен: {report_file}")
        except Exception as e:
            print(f"\n⚠️ Не удалось сохранить отчет: {e}")


def main():
    """Главная функция"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ЕДИНОГО ПАЙПЛАЙНА AML")
    print(f"🕒 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💻 Система: {psutil.cpu_count()} CPU, {psutil.virtual_memory().total // (1024**3)} GB RAM")
    
    # Создаем и запускаем тесты
    tester = AMLPipelineTest()
    
    try:
        results = tester.run_all_tests()
        
        # Возвращаем код выхода в зависимости от результата
        if results['overall_success']:
            print(f"\n🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
            sys.exit(0)
        else:
            print(f"\n⚠️ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Тестирование прервано пользователем")
        tester.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка тестирования: {e}")
        tester.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()