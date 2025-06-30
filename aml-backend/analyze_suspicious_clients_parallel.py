import sqlite3
import concurrent.futures
import time
import psutil
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Импортируем функции анализа
try:
    from customer_profile_afm import CustomerProfile
    from geographic_profile_afm import GeographicProfile
    from transaction_profile_afm import TransactionProfile
    from behavioral_profile_afm import BehavioralProfile
    from network_profile_afm import NetworkProfile
    print("✅ Все модули профилирования загружены успешно")
except ImportError as e:
    print(f"⚠️ Некоторые модули недоступны, используем упрощенный анализ: {e}")

def analyze_single_client(client_id: str, db_path: str = 'aml_system.db') -> Optional[Dict]:
    """
    Анализирует одного клиента и возвращает результат.
    Эта функция выполняется в отдельном процессе.
    """
    conn = None
    try:
        # Каждый процесс должен иметь свое подключение к БД
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        start_time = time.time()
        
        # 1. Получаем профиль клиента
        cursor.execute('''
            SELECT * FROM customer_profiles 
            WHERE customer_id = ?
        ''', (client_id,))
        client_profile = cursor.fetchone()
        
        if not client_profile:
            return None
        
        # 2. Получаем транзакции клиента
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE sender_id = ? OR beneficiary_id = ?
            ORDER BY transaction_date DESC
            LIMIT 100
        ''', (client_id, client_id))
        transactions = cursor.fetchall()
        
        # 3. Анализируем транзакционные паттерны
        total_sent = 0
        total_received = 0
        suspicious_count = 0
        countries = set()
        counterparties = set()
        
        for tx in transactions:
            if tx['sender_id'] == client_id:
                total_sent += tx['amount_kzt']
                counterparties.add(tx['beneficiary_id'])
            else:
                total_received += tx['amount_kzt']
                counterparties.add(tx['sender_id'])
                
            if tx['is_suspicious']:
                suspicious_count += 1
                
            # Собираем географию
            countries.add('KZ')  # Упрощаем для стабильности
        
        # 4. Расчет риск-скора
        base_risk = client_profile['overall_risk_score'] if client_profile['overall_risk_score'] else 0
        
        # Дополнительные риски
        tx_risk = 3 if len(transactions) > 50 else 0
        behavior_risk = min(suspicious_count * 2, 10)
        volume_risk = 2 if (total_sent + total_received) > 50000000 else 0  # > 50 млн тенге
        network_risk = 1 if len(counterparties) > 20 else 0
        
        total_risk_score = base_risk + tx_risk + behavior_risk + volume_risk + network_risk
        
        end_time = time.time()
        analysis_time = end_time - start_time
        
        return {
            'client_id': client_id,
            'analysis_time': analysis_time,
            'total_risk_score': total_risk_score,
            'transactions_count': len(transactions),
            'counterparties_count': len(counterparties),
            'total_volume': total_sent + total_received,
            'suspicious_transactions': suspicious_count,
            'is_suspicious': total_risk_score > 10,
            'risk_factors': {
                'base_risk': base_risk,
                'transaction_risk': tx_risk,
                'behavior_risk': behavior_risk,
                'volume_risk': volume_risk,
                'network_risk': network_risk
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка анализа клиента {client_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_client_list(db_path: str = 'aml_system.db', limit: int = None) -> List[str]:
    """Получение списка клиентов для анализа"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if limit:
        cursor.execute('''
            SELECT customer_id FROM customer_profiles 
            ORDER BY overall_risk_score DESC
            LIMIT ?
        ''', (limit,))
    else:
        cursor.execute('''
            SELECT customer_id FROM customer_profiles 
            ORDER BY overall_risk_score DESC
        ''')
    
    client_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return client_ids

def analyze_batch_parallel(client_ids: List[str], 
                          max_workers: int = None, 
                          batch_size: int = 500,
                          db_path: str = 'aml_system.db',
                          show_progress: bool = True) -> Tuple[List[Dict], Dict]:
    """
    Параллельный анализ списка клиентов с оптимизацией для 24-ядерного процессора
    """
    
    if max_workers is None:
        # Оптимально для Intel Core Ultra 9 275HX
        max_workers = min(20, len(client_ids))
    
    print(f"🚀 Запуск параллельного анализа:")
    print(f"   👥 Клиентов для анализа: {len(client_ids):,}")
    print(f"   ⚡ Рабочих процессов: {max_workers}")
    print(f"   📦 Размер батча: {batch_size}")
    
    start_time = time.time()
    results = []
    failed_analyses = []
    
    # Мониторинг ресурсов
    initial_memory = psutil.virtual_memory().percent
    initial_cpu = psutil.cpu_percent()
    
    # Разбиваем клиентов на батчи для лучшего контроля памяти
    batches = [client_ids[i:i + batch_size] for i in range(0, len(client_ids), batch_size)]
    
    print(f"   🔄 Батчей для обработки: {len(batches)}")
    print()
    
    total_processed = 0
    
    for batch_num, batch in enumerate(batches, 1):
        batch_start_time = time.time()
        
        print(f"📊 Батч {batch_num}/{len(batches)} ({len(batch)} клиентов):")
        
        # Используем ProcessPoolExecutor для CPU-интенсивных задач
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Отправляем задачи в пул процессов
            future_to_client = {
                executor.submit(analyze_single_client, client_id, db_path): client_id 
                for client_id in batch
            }
            
            # Собираем результаты по мере готовности
            for future in concurrent.futures.as_completed(future_to_client):
                client_id = future_to_client[future]
                try:
                    result = future.result(timeout=30)  # 30 секунд таймаут
                    if result:
                        results.append(result)
                        if show_progress and len(results) % 50 == 0:
                            print(f"  ✅ Обработано: {len(results)}/{len(client_ids)}")
                    else:
                        failed_analyses.append(client_id)
                        
                except concurrent.futures.TimeoutError:
                    print(f"  ⏰ Таймаут для клиента {client_id}")
                    failed_analyses.append(client_id)
                except Exception as e:
                    print(f"  ❌ Ошибка для клиента {client_id}: {e}")
                    failed_analyses.append(client_id)
        
        batch_time = time.time() - batch_start_time
        total_processed += len(batch)
        
        print(f"  ⏱️  Батч завершен за {batch_time:.2f} сек")
        print(f"  📈 Скорость: {len(batch)/batch_time:.1f} клиентов/сек")
        print()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Финальная статистика
    final_memory = psutil.virtual_memory().percent
    
    stats = {
        'total_time': total_time,
        'total_clients': len(client_ids),
        'successful_analyses': len(results),
        'failed_analyses': len(failed_analyses),
        'success_rate': len(results) / len(client_ids) * 100,
        'avg_time_per_client': total_time / len(client_ids),
        'clients_per_second': len(client_ids) / total_time,
        'memory_usage_change': final_memory - initial_memory,
        'max_workers_used': max_workers,
        'batches_processed': len(batches)
    }
    
    return results, stats

def analyze_suspicious_clients_parallel(db_path: str = 'aml_system.db', 
                                      limit: int = None,
                                      max_workers: int = None,
                                      output_file: str = None) -> Dict:
    """
    Главная функция для параллельного анализа подозрительных клиентов
    """
    
    print("🔍 ПАРАЛЛЕЛЬНЫЙ АНАЛИЗ ПОДОЗРИТЕЛЬНЫХ КЛИЕНТОВ")
    print("=" * 60)
    
    # Информация о системе
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    print(f"💻 Система:")
    print(f"   CPU: Intel Core Ultra 9 275HX ({cpu_count} ядер)")
    print(f"   RAM: {memory_gb:.1f} GB")
    print(f"   База данных: {db_path}")
    print()
    
    # Получаем список клиентов
    print("📊 Получение списка клиентов...")
    client_ids = get_client_list(db_path, limit)
    print(f"✅ Найдено клиентов: {len(client_ids):,}")
    print()
    
    if not client_ids:
        print("❌ Клиенты не найдены!")
        return {}
    
    # Запускаем параллельный анализ
    results, stats = analyze_batch_parallel(
        client_ids=client_ids,
        max_workers=max_workers,
        db_path=db_path
    )
    
    # Анализируем результаты
    print("📈 РЕЗУЛЬТАТЫ АНАЛИЗА:")
    print("=" * 40)
    print(f"⏱️  Общее время: {stats['total_time']:.2f} секунд")
    print(f"⚡ Скорость: {stats['clients_per_second']:.1f} клиентов/сек")
    print(f"✅ Успешно проанализировано: {stats['successful_analyses']:,}/{stats['total_clients']:,} ({stats['success_rate']:.1f}%)")
    print(f"❌ Неудачных анализов: {stats['failed_analyses']:,}")
    print(f"💾 Изменение памяти: {stats['memory_usage_change']:+.1f}%")
    print()
    
    # Анализ подозрительных клиентов
    suspicious_clients = [r for r in results if r['is_suspicious']]
    high_risk_clients = [r for r in results if r['total_risk_score'] > 15]
    
    print("🚨 АНАЛИЗ ПОДОЗРИТЕЛЬНОСТИ:")
    print("=" * 30)
    print(f"🔴 Подозрительных клиентов: {len(suspicious_clients):,}")
    print(f"🟠 Высокого риска (>15): {len(high_risk_clients):,}")
    print(f"📊 Процент подозрительных: {len(suspicious_clients)/len(results)*100:.1f}%")
    print()
    
    # Топ-10 самых подозрительных
    if suspicious_clients:
        print("🔝 ТОП-10 САМЫХ ПОДОЗРИТЕЛЬНЫХ КЛИЕНТОВ:")
        print("-" * 50)
        top_suspicious = sorted(suspicious_clients, key=lambda x: x['total_risk_score'], reverse=True)[:10]
        
        for i, client in enumerate(top_suspicious, 1):
            print(f"{i:2d}. Клиент {client['client_id']}")
            print(f"    Риск-скор: {client['total_risk_score']:.1f}")
            print(f"    Транзакций: {client['transactions_count']:,}")
            print(f"    Объем: {client['total_volume']:,.0f} тенге")
            print(f"    Подозрительных операций: {client['suspicious_transactions']}")
            print()
    
    # Статистика производительности
    theoretical_speedup = cpu_count
    actual_speedup = 1 / stats['avg_time_per_client'] if stats['avg_time_per_client'] > 0 else 0
    efficiency = (actual_speedup / theoretical_speedup) * 100 if theoretical_speedup > 0 else 0
    
    print("🚀 ЭФФЕКТИВНОСТЬ ПАРАЛЛЕЛИЗАЦИИ:")
    print("=" * 35)
    print(f"🎯 Теоретическое ускорение: {theoretical_speedup}x")
    print(f"⚡ Фактическая скорость: {stats['clients_per_second']:.1f} кл/сек")
    print(f"📊 Эффективность: {efficiency:.1f}%")
    print()
    
    # Сохранение результатов
    if output_file:
        print(f"💾 Сохранение результатов в {output_file}...")
        save_results_to_file(results, stats, output_file)
        print("✅ Результаты сохранены!")
    
    return {
        'results': results,
        'stats': stats,
        'suspicious_clients': suspicious_clients,
        'high_risk_clients': high_risk_clients
    }

def save_results_to_file(results: List[Dict], stats: Dict, filename: str):
    """Сохранение результатов в файл"""
    import json
    
    output_data = {
        'analysis_timestamp': datetime.now().isoformat(),
        'statistics': stats,
        'results': results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # Пример использования
    print("🚀 Запуск параллельного анализа AML-системы")
    print()
    
    # Можно настроить параметры
    results = analyze_suspicious_clients_parallel(
        db_path='aml_system.db',
        limit=None,  # Анализировать всех клиентов
        max_workers=20,  # Оптимально для 24-ядерного процессора
        output_file='aml_analysis_results.json'
    )
    
    print("�� Анализ завершен!") 