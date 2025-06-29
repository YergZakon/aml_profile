#!/usr/bin/env python3
"""
Параллельный анализ AML для JSON файлов
Обрабатывает входящие JSON файлы с транзакциями используя мультипроцессинг
"""

import json
import time
import psutil
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import os
import sys

# Добавляем путь к модулям профилирования
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from customer_profile_afm import CustomerProfile
    from transaction_profile_afm import TransactionProfile
    from behavioral_profile_afm import BehavioralProfile
    from geographic_profile_afm import GeographicProfile
    from network_profile_afm import NetworkProfile
    print("✅ Все модули профилирования загружены успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта модулей: {e}")
    sys.exit(1)

def _calculate_simple_geographic_risk(transaction: Dict) -> float:
    """Простой расчет географического риска"""
    country = transaction.get('country', 'Kazakhstan').lower()
    
    # Риск-карта стран (упрощенная)
    risk_map = {
        'kazakhstan': 1.0,
        'russia': 2.0,
        'china': 2.5,
        'usa': 1.5,
        'germany': 1.0,
        'switzerland': 3.0,
        'offshore': 8.0,
        'unknown': 5.0
    }
    
    return risk_map.get(country, 3.0)  # По умолчанию средний риск

def _calculate_simple_network_risk(transaction: Dict) -> float:
    """Простой расчет сетевого риска"""
    amount = transaction.get('amount', 0)
    operation_type = transaction.get('operation_type', '').lower()
    
    risk = 1.0
    
    # Риск по типу операции
    if 'cash' in operation_type:
        risk += 1.0
    if 'international' in operation_type:
        risk += 1.5
    if 'investment' in operation_type:
        risk += 0.5
        
    # Риск по сумме
    if amount > 10000000:  # > 10 млн
        risk += 2.0
    elif amount > 1000000:  # > 1 млн
        risk += 1.0
        
    return min(risk, 10.0)  # Максимум 10

def analyze_transaction_batch(transactions_batch: List[Dict]) -> List[Dict]:
    """
    Анализирует батч транзакций в отдельном процессе
    """
    try:
        # Инициализируем профили в каждом процессе
        customer_profile = CustomerProfile()
        transaction_profile = TransactionProfile()
        
        results = []
        
        for transaction in transactions_batch:
            try:
                # Преобразуем дату из строки в datetime если нужно
                if 'date' in transaction and isinstance(transaction['date'], str):
                    try:
                        transaction['date'] = datetime.fromisoformat(transaction['date'])
                    except:
                        transaction['date'] = datetime.now()
                
                # Анализируем транзакцию доступными профилями
                customer_analysis = customer_profile.analyze_customer_data(transaction)
                transaction_analysis = transaction_profile.analyze_transaction(transaction)
                
                # Создаем behavioral_profile для каждого клиента отдельно
                customer_id = transaction.get('customer_id', 'unknown')
                behavioral_profile = BehavioralProfile(customer_id)
                behavioral_analysis = behavioral_profile.analyze_transaction(transaction)
                
                # Извлекаем риск-скоры
                customer_risk = customer_analysis.get('risk_score', 0)
                transaction_risk = transaction_analysis.get('risk_score', 0)
                behavioral_risk = behavioral_analysis.get('risk_score', 0)
                
                # Простые географические и сетевые риски
                geographic_risk = _calculate_simple_geographic_risk(transaction)
                network_risk = _calculate_simple_network_risk(transaction)
                
                # Суммарный риск-скор
                total_risk = (customer_risk + transaction_risk + behavioral_risk + 
                            geographic_risk + network_risk)
                
                # Определяем подозрительность
                is_suspicious = total_risk > 5.0
                
                result = {
                    'transaction_id': transaction.get('transaction_id', 'unknown'),
                    'customer_id': transaction.get('customer_id', 'unknown'),
                    'amount': float(transaction.get('amount', 0)),
                    'currency': transaction.get('currency', 'KZT'),
                    'date': transaction.get('date', ''),
                    'operation_type': transaction.get('operation_type', ''),
                    'country': transaction.get('country', ''),
                    'risks': {
                        'customer_risk': customer_risk,
                        'transaction_risk': transaction_risk,
                        'behavioral_risk': behavioral_risk,
                        'geographic_risk': geographic_risk,
                        'network_risk': network_risk
                    },
                    'total_risk_score': total_risk,
                    'is_suspicious': is_suspicious,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
                results.append(result)
                
            except Exception as e:
                print(f"❌ Ошибка анализа транзакции: {e}")
                continue
                
        return results
        
    except Exception as e:
        print(f"❌ Ошибка в процессе анализа батча: {e}")
        return []

def load_json_file(file_path: str) -> List[Dict]:
    """
    Загружает JSON файл с транзакциями
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Поддерживаем разные форматы JSON
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Если это объект с массивом транзакций
            if 'transactions' in data:
                return data['transactions']
            elif 'data' in data:
                return data['data']
            else:
                # Возможно, это одна транзакция
                return [data]
        else:
            print(f"❌ Неподдерживаемый формат JSON: {type(data)}")
            return []
            
    except FileNotFoundError:
        print(f"❌ Файл не найден: {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return []
    except Exception as e:
        print(f"❌ Ошибка загрузки файла: {e}")
        return []

def analyze_json_parallel(input_file: str,
                         output_file: str = None,
                         max_workers: int = None,
                         batch_size: int = 100) -> Dict:
    """
    Главная функция для параллельного анализа JSON файла
    """
    
    print("🔍 ПАРАЛЛЕЛЬНЫЙ АНАЛИЗ JSON ФАЙЛА")
    print("=" * 50)
    
    # Информация о системе
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    if max_workers is None:
        max_workers = min(cpu_count - 4, 20)  # Оставляем 4 ядра для системы
    
    print(f"💻 Система:")
    print(f"   CPU: Intel Core Ultra 9 275HX ({cpu_count} ядер)")
    print(f"   RAM: {memory_gb:.1f} GB")
    print(f"   Входной файл: {input_file}")
    print(f"   Рабочих процессов: {max_workers}")
    print(f"   Размер батча: {batch_size}")
    print()
    
    # Загружаем JSON файл
    print("📂 Загрузка JSON файла...")
    transactions = load_json_file(input_file)
    
    if not transactions:
        print("❌ Транзакции не найдены!")
        return {}
    
    print(f"✅ Загружено транзакций: {len(transactions):,}")
    print()
    
    # Разбиваем на батчи
    batches = [transactions[i:i + batch_size] 
              for i in range(0, len(transactions), batch_size)]
    
    print(f"🚀 Запуск параллельного анализа:")
    print(f"   📦 Транзакций для анализа: {len(transactions):,}")
    print(f"   ⚡ Рабочих процессов: {max_workers}")
    print(f"   📊 Размер батча: {batch_size}")
    print(f"   🔄 Батчей для обработки: {len(batches)}")
    print()
    
    # Мониторинг ресурсов
    initial_memory = psutil.virtual_memory().percent
    start_time = time.time()
    
    all_results = []
    failed_batches = 0
    
    # Параллельная обработка батчей
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Отправляем батчи на обработку
        future_to_batch = {
            executor.submit(analyze_transaction_batch, batch): i 
            for i, batch in enumerate(batches)
        }
        
        # Собираем результаты
        for future in concurrent.futures.as_completed(future_to_batch):
            batch_num = future_to_batch[future]
            try:
                batch_results = future.result(timeout=60)  # 60 секунд таймаут
                all_results.extend(batch_results)
                
                # Прогресс
                processed_batches = len([f for f in future_to_batch if f.done()])
                print(f"  ✅ Батч {batch_num + 1}/{len(batches)} завершен "
                      f"({len(batch_results)} транзакций)")
                
                if processed_batches % 5 == 0:  # Каждые 5 батчей
                    current_time = time.time() - start_time
                    processed_transactions = len(all_results)
                    speed = processed_transactions / current_time if current_time > 0 else 0
                    print(f"  📈 Обработано: {processed_transactions:,}/{len(transactions):,} "
                          f"({speed:.1f} тр/сек)")
                
            except concurrent.futures.TimeoutError:
                print(f"  ⏰ Таймаут для батча {batch_num + 1}")
                failed_batches += 1
            except Exception as e:
                print(f"  ❌ Ошибка в батче {batch_num + 1}: {e}")
                failed_batches += 1
    
    end_time = time.time()
    total_time = end_time - start_time
    final_memory = psutil.virtual_memory().percent
    
    # Анализ результатов
    suspicious_transactions = [r for r in all_results if r['is_suspicious']]
    high_risk_transactions = [r for r in all_results if r['total_risk_score'] > 15]
    
    # Статистика по клиентам
    clients_analysis = {}
    for result in all_results:
        client_id = result['customer_id']
        if client_id not in clients_analysis:
            clients_analysis[client_id] = {
                'total_transactions': 0,
                'suspicious_transactions': 0,
                'total_amount': 0,
                'max_risk_score': 0
            }
        
        clients_analysis[client_id]['total_transactions'] += 1
        clients_analysis[client_id]['total_amount'] += result['amount']
        clients_analysis[client_id]['max_risk_score'] = max(
            clients_analysis[client_id]['max_risk_score'],
            result['total_risk_score']
        )
        
        if result['is_suspicious']:
            clients_analysis[client_id]['suspicious_transactions'] += 1
    
    # Подозрительные клиенты
    suspicious_clients = [
        {'client_id': cid, **data} 
        for cid, data in clients_analysis.items() 
        if data['suspicious_transactions'] > 0
    ]
    
    # Статистика
    stats = {
        'analysis_timestamp': datetime.now().isoformat(),
        'input_file': input_file,
        'total_time': total_time,
        'total_transactions': len(transactions),
        'processed_transactions': len(all_results),
        'failed_batches': failed_batches,
        'success_rate': len(all_results) / len(transactions) * 100,
        'transactions_per_second': len(all_results) / total_time,
        'memory_usage_change': final_memory - initial_memory,
        'max_workers_used': max_workers,
        'batch_size': batch_size,
        'batches_processed': len(batches),
        'suspicious_transactions': len(suspicious_transactions),
        'high_risk_transactions': len(high_risk_transactions),
        'unique_clients': len(clients_analysis),
        'suspicious_clients': len(suspicious_clients)
    }
    
    # Вывод результатов
    print("\n📈 РЕЗУЛЬТАТЫ АНАЛИЗА:")
    print("=" * 40)
    print(f"⏱️  Общее время: {total_time:.2f} секунд")
    print(f"⚡ Скорость: {stats['transactions_per_second']:.1f} транзакций/сек")
    print(f"✅ Обработано: {len(all_results):,}/{len(transactions):,} "
          f"({stats['success_rate']:.1f}%)")
    print(f"❌ Неудачных батчей: {failed_batches}")
    print(f"💾 Изменение памяти: {stats['memory_usage_change']:+.1f}%")
    print()
    
    print("🚨 АНАЛИЗ ПОДОЗРИТЕЛЬНОСТИ:")
    print("=" * 30)
    print(f"🔴 Подозрительных транзакций: {len(suspicious_transactions):,}")
    print(f"🟠 Высокого риска (>15): {len(high_risk_transactions):,}")
    print(f"👥 Уникальных клиентов: {len(clients_analysis):,}")
    print(f"🎯 Подозрительных клиентов: {len(suspicious_clients):,}")
    if len(all_results) > 0:
        suspicious_percentage = len(suspicious_transactions)/len(all_results)*100
        print(f"📊 Процент подозрительных транзакций: {suspicious_percentage:.1f}%")
    else:
        print("📊 Процент подозрительных транзакций: 0.0%")
    print()
    
    # Топ подозрительных клиентов
    if suspicious_clients:
        print("🔝 ТОП-10 ПОДОЗРИТЕЛЬНЫХ КЛИЕНТОВ:")
        print("-" * 50)
        top_clients = sorted(suspicious_clients, 
                           key=lambda x: x['max_risk_score'], 
                           reverse=True)[:10]
        
        for i, client in enumerate(top_clients, 1):
            print(f"{i:2d}. Клиент {client['client_id']}")
            print(f"    Макс. риск-скор: {client['max_risk_score']:.1f}")
            print(f"    Всего транзакций: {client['total_transactions']:,}")
            print(f"    Подозрительных: {client['suspicious_transactions']:,}")
            print(f"    Общая сумма: {client['total_amount']:,.0f} тенге")
            print()
    
    # Сохранение результатов
    if output_file:
        print(f"💾 Сохранение результатов в {output_file}...")
        
        output_data = {
            'analysis_metadata': stats,
            'transaction_results': all_results,
            'client_analysis': clients_analysis,
            'suspicious_transactions': suspicious_transactions,
            'suspicious_clients': suspicious_clients
        }
        
        try:
            # Преобразуем datetime объекты в строки для JSON
            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2, default=convert_datetime)
            print("✅ Результаты сохранены!")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
    
    print("\n🎉 Анализ завершен!")
    
    return {
        'stats': stats,
        'results': all_results,
        'suspicious_transactions': suspicious_transactions,
        'suspicious_clients': suspicious_clients,
        'client_analysis': clients_analysis
    }

def main():
    """Основная функция с примером использования"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Параллельный анализ JSON файла с транзакциями')
    parser.add_argument('input_file', help='Путь к входному JSON файлу')
    parser.add_argument('-o', '--output', help='Путь к выходному JSON файлу')
    parser.add_argument('-w', '--workers', type=int, help='Количество рабочих процессов')
    parser.add_argument('-b', '--batch-size', type=int, default=100, 
                       help='Размер батча (по умолчанию: 100)')
    
    args = parser.parse_args()
    
    print("🚀 Запуск параллельного анализа JSON файла")
    print()
    
    # Проверяем существование файла
    if not Path(args.input_file).exists():
        print(f"❌ Файл не найден: {args.input_file}")
        return
    
    # Генерируем имя выходного файла если не указано
    output_file = args.output
    if not output_file:
        input_path = Path(args.input_file)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"aml_analysis_{input_path.stem}_{timestamp}.json"
    
    # Запускаем анализ
    results = analyze_json_parallel(
        input_file=args.input_file,
        output_file=output_file,
        max_workers=args.workers,
        batch_size=args.batch_size
    )

if __name__ == "__main__":
    main() 