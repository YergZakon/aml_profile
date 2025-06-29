#!/usr/bin/env python3
"""
🚀 Главный Пайплайн AML-Анализа
Автоматически выбирает оптимальный метод обработки в зависимости от объема данных
Поддерживает обработку JSON файлов АФМ РК
"""

import time
import sys
import sqlite3
import psutil
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Импорт модулей оптимизации
try:
    from optimize_database import (
        analyze_batch_optimized, 
        create_database_indexes,
        get_cached_analysis
    )
    print("✅ Модуль оптимизации БД загружен")
except ImportError as e:
    print(f"❌ Ошибка загрузки модуля оптимизации: {e}")
    sys.exit(1)

try:
    from analyze_suspicious_clients_parallel import analyze_batch_parallel
    print("✅ Модуль параллельной обработки загружен")
except ImportError as e:
    print(f"⚠️ Модуль параллельной обработки недоступен: {e}")
    analyze_batch_parallel = None

# Импорт модуля для обработки JSON файлов АФМ
try:
    from aml_pipeline_enhanced import AMLPipelineEnhanced
    print("✅ Модуль обработки JSON файлов АФМ загружен")
    JSON_SUPPORT = True
except ImportError as e:
    print(f"⚠️ Модуль JSON файлов недоступен: {e}")
    JSON_SUPPORT = False

class AMLPipeline:
    """Главный класс пайплайна AML-анализа"""
    
    def __init__(self, db_path: str = 'aml_system.db'):
        self.db_path = db_path
        self.system_info = self._get_system_info()
        self.pipeline_stats = {
            'total_runs': 0,
            'total_clients_processed': 0,
            'total_time_saved': 0,
            'optimization_method_used': {}
        }
        
    def _get_system_info(self) -> Dict:
        """Получение информации о системе"""
        return {
            'cpu_cores': psutil.cpu_count(),
            'memory_gb': psutil.virtual_memory().total / (1024**3),
            'cpu_model': 'Intel Core Ultra 9 275HX',
            'timestamp': datetime.now().isoformat()
        }
    
    def setup_database(self) -> bool:
        """Настройка базы данных с индексами"""
        print("🔧 НАСТРОЙКА БАЗЫ ДАННЫХ")
        print("=" * 40)
        
        try:
            # Проверяем существование БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customer_profiles")
            client_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"📊 Найдено клиентов в БД: {client_count:,}")
            
            # Создаем индексы
            create_database_indexes(self.db_path)
            print("✅ База данных настроена!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки БД: {e}")
            return False
    
    def get_client_list(self, limit: Optional[int] = None, 
                       risk_threshold: Optional[float] = None) -> List[str]:
        """Получение списка клиентов для анализа"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT customer_id FROM customer_profiles"
        params = []
        
        if risk_threshold:
            query += " WHERE overall_risk_score >= ?"
            params.append(risk_threshold)
            
        query += " ORDER BY overall_risk_score DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        client_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return client_ids
    
    def choose_optimization_method(self, client_count: int) -> str:
        """Автоматический выбор метода оптимизации"""
        if client_count < 1000:
            return "optimized"  # Оптимизированная версия для малых объемов
        elif client_count < 10000:
            return "optimized_cached"  # С кэшированием для средних объемов
        else:
            return "parallel" if analyze_batch_parallel else "optimized"  # Параллельная для больших
    
    def analyze_clients(self, client_ids: List[str], 
                       method: Optional[str] = None) -> Dict:
        """Анализ клиентов с автоматическим выбором метода"""
        
        if not client_ids:
            return {'error': 'Список клиентов пуст'}
        
        client_count = len(client_ids)
        
        # Автоматический выбор метода
        if method is None:
            method = self.choose_optimization_method(client_count)
        
        print(f"🚀 АНАЛИЗ {client_count:,} КЛИЕНТОВ")
        print(f"⚡ Выбранный метод: {method.upper()}")
        print("=" * 50)
        
        start_time = time.time()
        
        try:
            if method == "optimized":
                results = analyze_batch_optimized(client_ids, self.db_path)
                
            elif method == "optimized_cached":
                # Используем кэширование для повторных запросов
                results = []
                for client_id in client_ids:
                    result = get_cached_analysis(client_id, self.db_path)
                    if result:
                        results.append(result)
                        
            elif method == "parallel" and analyze_batch_parallel:
                results, stats = analyze_batch_parallel(
                    client_ids=client_ids,
                    max_workers=min(20, client_count // 100),
                    db_path=self.db_path,
                    show_progress=False
                )
                
            else:
                # Fallback к оптимизированной версии
                results = analyze_batch_optimized(client_ids, self.db_path)
                method = "optimized"
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            # Статистика
            analysis_stats = self._calculate_stats(results, analysis_time, method)
            
            # Обновляем статистику пайплайна
            self._update_pipeline_stats(client_count, analysis_time, method)
            
            return {
                'success': True,
                'method_used': method,
                'results': results,
                'stats': analysis_stats,
                'system_info': self.system_info
            }
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
            return {'error': str(e)}
    
    def _calculate_stats(self, results: List[Dict], 
                        analysis_time: float, method: str) -> Dict:
        """Расчет статистики анализа"""
        
        if not results:
            return {}
        
        suspicious_clients = [r for r in results if r.get('is_suspicious', False)]
        high_risk_clients = [r for r in results if r.get('total_risk_score', 0) > 15]
        
        return {
            'total_clients': len(results),
            'analysis_time': analysis_time,
            'clients_per_second': len(results) / analysis_time if analysis_time > 0 else 0,
            'method_used': method,
            'suspicious_clients': len(suspicious_clients),
            'high_risk_clients': len(high_risk_clients),
            'suspicious_percentage': len(suspicious_clients) / len(results) * 100,
            'average_risk_score': sum(r.get('total_risk_score', 0) for r in results) / len(results),
            'max_risk_score': max(r.get('total_risk_score', 0) for r in results),
            'total_volume': sum(r.get('total_volume', 0) for r in results),
            'total_transactions': sum(r.get('transactions_count', 0) for r in results)
        }
    
    def _update_pipeline_stats(self, client_count: int, 
                              analysis_time: float, method: str):
        """Обновление статистики пайплайна"""
        self.pipeline_stats['total_runs'] += 1
        self.pipeline_stats['total_clients_processed'] += client_count
        
        # Оценка экономии времени (по сравнению с базовой версией)
        baseline_time = client_count * 0.0005  # ~0.5ms на клиента в базовой версии
        time_saved = max(0, baseline_time - analysis_time)
        self.pipeline_stats['total_time_saved'] += time_saved
        
        # Статистика методов
        if method not in self.pipeline_stats['optimization_method_used']:
            self.pipeline_stats['optimization_method_used'][method] = 0
        self.pipeline_stats['optimization_method_used'][method] += 1
    
    def run_full_analysis(self, limit: Optional[int] = None,
                         risk_threshold: Optional[float] = None,
                         save_results: bool = True) -> Dict:
        """Запуск полного анализа"""
        
        print("🔍 ЗАПУСК ПОЛНОГО AML-АНАЛИЗА")
        print("=" * 60)
        print(f"💻 Система: {self.system_info['cpu_model']} ({self.system_info['cpu_cores']} ядер)")
        print(f"💾 Память: {self.system_info['memory_gb']:.1f} GB")
        print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Настройка БД
        if not self.setup_database():
            return {'error': 'Ошибка настройки базы данных'}
        
        print()
        
        # 2. Получение списка клиентов
        print("📊 ПОЛУЧЕНИЕ СПИСКА КЛИЕНТОВ")
        print("-" * 30)
        
        client_ids = self.get_client_list(limit, risk_threshold)
        
        if not client_ids:
            print("❌ Клиенты не найдены!")
            return {'error': 'Клиенты не найдены'}
        
        print(f"✅ Найдено клиентов: {len(client_ids):,}")
        if risk_threshold:
            print(f"🎯 Фильтр по риску: ≥{risk_threshold}")
        if limit:
            print(f"📋 Лимит: {limit:,}")
        print()
        
        # 3. Анализ клиентов
        analysis_result = self.analyze_clients(client_ids)
        
        if not analysis_result.get('success'):
            return analysis_result
        
        # 4. Отображение результатов
        self._display_results(analysis_result)
        
        # 5. Сохранение результатов
        if save_results:
            filename = f"aml_pipeline_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self._save_results(analysis_result, filename)
            print(f"💾 Результаты сохранены: {filename}")
        
        return analysis_result
    
    def _display_results(self, analysis_result: Dict):
        """Отображение результатов анализа"""
        stats = analysis_result['stats']
        results = analysis_result['results']
        
        print("📈 РЕЗУЛЬТАТЫ АНАЛИЗА:")
        print("=" * 40)
        print(f"⏱️  Время анализа: {stats['analysis_time']:.3f} секунд")
        print(f"⚡ Скорость: {stats['clients_per_second']:,.0f} клиентов/сек")
        print(f"🔧 Метод: {stats['method_used'].upper()}")
        print()
        
        print("🚨 АНАЛИЗ ПОДОЗРИТЕЛЬНОСТИ:")
        print("=" * 30)
        print(f"🔴 Подозрительных клиентов: {stats['suspicious_clients']:,} ({stats['suspicious_percentage']:.1f}%)")
        print(f"🟠 Высокого риска (>15): {stats['high_risk_clients']:,}")
        print(f"📊 Средний риск-скор: {stats['average_risk_score']:.1f}")
        print(f"🎯 Максимальный риск: {stats['max_risk_score']:.1f}")
        print()
        
        print("💰 ФИНАНСОВАЯ СТАТИСТИКА:")
        print("=" * 25)
        print(f"💵 Общий объем: {stats['total_volume']:,.0f} тенге")
        print(f"📊 Всего транзакций: {stats['total_transactions']:,}")
        print(f"💸 Средний объем на клиента: {stats['total_volume']/stats['total_clients']:,.0f} тенге")
        print()
        
        # Топ-5 самых подозрительных
        if stats['suspicious_clients'] > 0:
            suspicious_results = [r for r in results if r.get('is_suspicious', False)]
            top_suspicious = sorted(suspicious_results, 
                                  key=lambda x: x.get('total_risk_score', 0), 
                                  reverse=True)[:5]
            
            print("🔝 ТОП-5 САМЫХ ПОДОЗРИТЕЛЬНЫХ КЛИЕНТОВ:")
            print("-" * 45)
            for i, client in enumerate(top_suspicious, 1):
                print(f"{i}. Клиент {client['client_id']}")
                print(f"   Риск-скор: {client['total_risk_score']:.1f}")
                print(f"   Транзакций: {client['transactions_count']:,}")
                print(f"   Объем: {client['total_volume']:,.0f} тенге")
                print()
    
    def _save_results(self, analysis_result: Dict, filename: str):
        """Сохранение результатов в JSON"""
        # Добавляем статистику пайплайна
        analysis_result['pipeline_stats'] = self.pipeline_stats.copy()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2, default=str)
    
    def process_json_files(self, json_files: List[str] = None, 
                          json_dir: str = "uploads",
                          parallel_analysis: bool = True,
                          save_to_db: bool = True) -> Dict:
        """Обработка JSON файлов АФМ"""
        if not JSON_SUPPORT:
            return {'error': 'Модуль обработки JSON файлов недоступен'}
        
        print(f"\n🚀 ОБРАБОТКА JSON ФАЙЛОВ АФМ")
        print("=" * 50)
        
        # Определяем файлы для обработки
        if not json_files:
            json_dir_path = Path(json_dir)
            if json_dir_path.exists():
                json_files = [str(f) for f in json_dir_path.glob('*.json')]
            else:
                return {'error': f'Папка {json_dir} не найдена'}
        
        if not json_files:
            return {'error': f'JSON файлы не найдены в {json_dir}'}
        
        print(f"📁 Найдено JSON файлов: {len(json_files)}")
        for f in json_files:
            print(f"   • {Path(f).name}")
        
        try:
            # Создаем расширенный пайплайн
            enhanced_pipeline = AMLPipelineEnhanced(self.db_path)
            
            # Обрабатываем файлы
            results = enhanced_pipeline.process_json_files(
                json_files=json_files,
                parallel_analysis=parallel_analysis,
                save_to_db=save_to_db
            )
            
            # Генерируем отчет
            if results:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_file = f"aml_json_results_{timestamp}.json"
                enhanced_pipeline.generate_report(results, report_file)
            
            # Обновляем статистику основного пайплайна
            self.pipeline_stats['total_runs'] += 1
            if results.get('total_processed'):
                self.pipeline_stats['total_clients_processed'] += results['total_processed']
            
            return {
                'success': True,
                'method_used': 'json_processing',
                'files_processed': len(json_files),
                'results': results,
                'enhanced_pipeline_stats': enhanced_pipeline.stats
            }
            
        except Exception as e:
            print(f"❌ Ошибка обработки JSON файлов: {e}")
            return {'error': str(e)}
    
    def detect_json_files(self, directory: str = "uploads") -> List[str]:
        """Автоматическое обнаружение JSON файлов"""
        json_dir = Path(directory)
        if not json_dir.exists():
            return []
        
        json_files = list(json_dir.glob('*.json'))
        return [str(f) for f in json_files]
    
    def run_hybrid_analysis(self, 
                           include_json: bool = True,
                           include_db_clients: bool = True,
                           limit: Optional[int] = None) -> Dict:
        """Гибридный анализ: JSON файлы + клиенты из БД"""
        print(f"\n🔄 ГИБРИДНЫЙ АНАЛИЗ AML")
        print("=" * 40)
        
        results = {
            'json_results': None,
            'db_results': None,
            'combined_stats': {}
        }
        
        # 1. Обработка JSON файлов
        if include_json:
            json_files = self.detect_json_files()
            if json_files:
                print(f"📂 Обрабатываем {len(json_files)} JSON файлов...")
                results['json_results'] = self.process_json_files(json_files)
            else:
                print("📂 JSON файлы не найдены")
        
        # 2. Анализ клиентов из БД
        if include_db_clients:
            print(f"🗄️  Анализируем клиентов из базы данных...")
            client_ids = self.get_client_list(limit=limit)
            if client_ids:
                results['db_results'] = self.analyze_clients(client_ids)
            else:
                print("🗄️  Клиенты в БД не найдены")
        
        # 3. Комбинированная статистика
        results['combined_stats'] = self._combine_analysis_stats(
            results['json_results'], 
            results['db_results']
        )
        
        return results
    
    def _combine_analysis_stats(self, json_results: Dict, db_results: Dict) -> Dict:
        """Объединение статистики из разных источников"""
        combined = {
            'total_sources': 0,
            'total_processed': 0,
            'total_suspicious': 0,
            'processing_methods': []
        }
        
        if json_results and json_results.get('success'):
            combined['total_sources'] += 1
            json_stats = json_results.get('results', {})
            combined['total_processed'] += json_stats.get('total_processed', 0)
            combined['total_suspicious'] += json_stats.get('suspicious_count', 0)
            combined['processing_methods'].append('JSON файлы АФМ')
        
        if db_results and db_results.get('success'):
            combined['total_sources'] += 1
            db_stats = db_results.get('stats', {})
            combined['total_processed'] += db_stats.get('total_clients', 0)
            combined['total_suspicious'] += db_stats.get('suspicious_clients', 0)
            combined['processing_methods'].append('База данных клиентов')
        
        return combined

    def show_pipeline_stats(self):
        """Показать статистику пайплайна"""
        print("📊 СТАТИСТИКА ПАЙПЛАЙНА AML-АНАЛИЗА")
        print("=" * 40)
        print(f"🔄 Всего запусков: {self.pipeline_stats['total_runs']}")
        print(f"👥 Всего клиентов обработано: {self.pipeline_stats['total_clients_processed']:,}")
        print(f"⏰ Общая экономия времени: {self.pipeline_stats['total_time_saved']:.2f} сек")
        print()
        
        if self.pipeline_stats['optimization_method_used']:
            print("🔧 Использованные методы:")
            for method, count in self.pipeline_stats['optimization_method_used'].items():
                print(f"   {method.upper()}: {count} раз")
        
        # Проверяем наличие JSON файлов
        json_files = self.detect_json_files()
        if json_files:
            print(f"\n📂 Доступные JSON файлы ({len(json_files)}):")
            for f in json_files[:5]:  # Показываем первые 5
                print(f"   • {Path(f).name}")
            if len(json_files) > 5:
                print(f"   ... и еще {len(json_files) - 5}")
        else:
            print(f"\n📂 JSON файлы не найдены в папке uploads")


def main():
    """Главная функция для запуска пайплайна"""
    
    print("🚀 AML PIPELINE - СИСТЕМА АНАЛИЗА ПОДОЗРИТЕЛЬНЫХ КЛИЕНТОВ")
    print("=" * 70)
    print()
    
    # Создаем пайплайн
    pipeline = AMLPipeline('aml_system.db')
    
    # Варианты запуска
    print("Выберите режим запуска:")
    print("1. 🚀 Полный анализ всех клиентов")
    print("2. 🎯 Анализ клиентов с высоким риском (>5)")
    print("3. 📊 Тестовый анализ (100 клиентов)")
    print("4. 📂 Обработка JSON файлов АФМ")
    print("5. 🔄 Гибридный анализ (JSON + БД)")
    print("6. 🔧 Только настройка БД")
    print("7. 📈 Показать статистику пайплайна")
    print()
    
    try:
        choice = input("Введите номер (1-7): ").strip()
        
        if choice == "1":
            # Полный анализ
            result = pipeline.run_full_analysis()
            
        elif choice == "2":
            # Анализ высокого риска
            result = pipeline.run_full_analysis(risk_threshold=5.0)
            
        elif choice == "3":
            # Тестовый анализ
            result = pipeline.run_full_analysis(limit=100)
            
        elif choice == "4":
            # Обработка JSON файлов
            result = pipeline.process_json_files()
            
        elif choice == "5":
            # Гибридный анализ
            result = pipeline.run_hybrid_analysis()
            
        elif choice == "6":
            # Только настройка
            pipeline.setup_database()
            print("✅ Настройка завершена!")
            return
            
        elif choice == "7":
            # Статистика
            pipeline.show_pipeline_stats()
            return
            
        else:
            print("❌ Неверный выбор!")
            return
        
        # Обработка результатов
        if hasattr(result, 'get') and result.get('success'):
            print()
            print("🎉 АНАЛИЗ УСПЕШНО ЗАВЕРШЕН!")
            
            # Различная обработка для разных типов результатов
            if choice in ["1", "2", "3"]:
                # Стандартный анализ БД
                print(f"⚡ Обработано {len(result['results']):,} клиентов за {result['stats']['analysis_time']:.3f} сек")
                
            elif choice == "4":
                # JSON обработка
                json_results = result.get('results', {})
                print(f"📂 Обработано {result.get('files_processed', 0)} JSON файлов")
                print(f"⚡ Проанализировано {json_results.get('total_processed', 0):,} транзакций")
                print(f"🚨 Найдено подозрительных: {json_results.get('suspicious_count', 0):,}")
                
            elif choice == "5":
                # Гибридный анализ
                combined_stats = result.get('combined_stats', {})
                print(f"🔄 Источников данных: {combined_stats.get('total_sources', 0)}")
                print(f"⚡ Всего обработано: {combined_stats.get('total_processed', 0):,}")
                print(f"🚨 Всего подозрительных: {combined_stats.get('total_suspicious', 0):,}")
                print(f"📊 Методы: {', '.join(combined_stats.get('processing_methods', []))}")
                
        elif hasattr(result, 'get') and result.get('error'):
            print(f"❌ Ошибка: {result.get('error')}")
        else:
            print("✅ Операция завершена")
    
    except KeyboardInterrupt:
        print("\n⏹️ Анализ прерван пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")


if __name__ == "__main__":
    main() 