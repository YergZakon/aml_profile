import sqlite3
import time
import psutil
from datetime import datetime

def analyze_single_client_simple(client_id, db_path):
    """Упрощенный анализ одного клиента"""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
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
        
        # 3. Простой анализ транзакций
        total_sent = 0
        total_received = 0
        suspicious_count = 0
        countries = set()
        
        for tx in transactions:
            if tx['sender_id'] == client_id:
                total_sent += tx['amount_kzt']
            else:
                total_received += tx['amount_kzt']
                
            if tx['is_suspicious']:
                suspicious_count += 1
                
            # Простая география
            countries.add('KZ')  # Упрощаем для теста
        
        # 4. Расчет риск-скора
        base_risk = client_profile['overall_risk_score'] if client_profile['overall_risk_score'] else 0
        
        # Простые дополнительные риски
        tx_risk = 3 if len(transactions) > 50 else 0
        behavior_risk = min(suspicious_count * 2, 10)
        
        total_risk_score = base_risk + tx_risk + behavior_risk
        
        end_time = time.time()
        analysis_time = end_time - start_time
        
        conn.close()
        
        return {
            'client_id': client_id,
            'analysis_time': analysis_time,
            'total_risk_score': total_risk_score,
            'transactions_count': len(transactions),
            'countries_count': len(countries),
            'is_suspicious': total_risk_score > 10
        }
        
    except Exception as e:
        print(f"❌ Ошибка анализа клиента {client_id}: {e}")
        conn.close()
        return None

def get_client_list(db_path, limit=1000):
    """Получение списка клиентов для анализа"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT customer_id FROM customer_profiles 
        ORDER BY overall_risk_score DESC
        LIMIT ?
    ''', (limit,))
    
    client_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return client_ids

def test_simple_performance():
    """Простое тестирование производительности"""
    print("🚀 ТЕСТИРОВАНИЕ ПРОИЗВОДИТЕЛЬНОСТИ AML-АНАЛИЗА")
    print("=" * 55)
    
    db_path = 'aml_system.db'
    
    # Получаем информацию о системе
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    print(f"💻 Система:")
    print(f"   CPU ядер: {cpu_count} (Intel Core Ultra 9 275HX)")
    print(f"   RAM: {memory_gb:.1f} GB")
    
    # Получаем список клиентов
    print(f"\n📊 Получаем список клиентов...")
    client_ids = get_client_list(db_path, 1000)
    print(f"✅ Найдено клиентов: {len(client_ids)}")
    
    # Тестируем разные размеры выборок
    test_sizes = [1, 5, 10, 25, 50, 100, 200, 500]
    
    results = []
    
    for test_size in test_sizes:
        if test_size > len(client_ids):
            continue
            
        print(f"\n🧪 Тестирование анализа {test_size} клиентов:")
        print("-" * 50)
        
        # Берем первых N клиентов
        test_clients = client_ids[:test_size]
        
        start_time = time.time()
        successful_analyses = 0
        total_transactions = 0
        suspicious_clients = 0
        
        for i, client_id in enumerate(test_clients, 1):
            if i <= 5 or i % 50 == 0 or test_size <= 10:
                print(f"  📋 Анализируем клиента {i}/{test_size}...", end=" ")
            
            result = analyze_single_client_simple(client_id, db_path)
            if result:
                successful_analyses += 1
                total_transactions += result['transactions_count']
                if result['is_suspicious']:
                    suspicious_clients += 1
                    
                if i <= 5 or i % 50 == 0 or test_size <= 10:
                    print(f"✅ ({result['analysis_time']:.3f}с, риск: {result['total_risk_score']:.1f})")
            else:
                if i <= 5 or i % 50 == 0 or test_size <= 10:
                    print("❌")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Сохраняем результаты
        result_data = {
            'test_size': test_size,
            'total_time': total_time,
            'avg_time_per_client': total_time / test_size if test_size > 0 else 0,
            'successful_analyses': successful_analyses,
            'total_transactions': total_transactions,
            'suspicious_clients': suspicious_clients,
            'success_rate': (successful_analyses / test_size * 100) if test_size > 0 else 0
        }
        results.append(result_data)
        
        print(f"\n📊 Результаты для {test_size} клиентов:")
        print(f"  ⏱️  Общее время: {total_time:.2f} секунд")
        print(f"  ⚡ Время на клиента: {total_time/test_size:.3f} секунд")
        print(f"  ✅ Успешно проанализировано: {successful_analyses}/{test_size} ({result_data['success_rate']:.1f}%)")
        print(f"  💸 Обработано транзакций: {total_transactions:,}")
        print(f"  🚨 Подозрительных клиентов: {suspicious_clients}")
        
        # Прогнозы для успешных тестов
        if successful_analyses >= 5:
            avg_time_per_successful = total_time / successful_analyses
            time_for_1000 = avg_time_per_successful * 1000
            time_for_all_clients = avg_time_per_successful * len(client_ids)
            
            print(f"\n🔮 Прогнозы (последовательная обработка):")
            print(f"  📈 1000 клиентов: {time_for_1000:.0f} сек ({time_for_1000/60:.1f} мин)")
            print(f"  📈 Все {len(client_ids)} клиентов: {time_for_all_clients:.0f} сек ({time_for_all_clients/60:.1f} мин)")
            
            # Прогноз с параллелизацией на 24 ядрах
            parallel_time_1000 = time_for_1000 / cpu_count
            parallel_time_all = time_for_all_clients / cpu_count
            
            print(f"\n🚀 С параллелизацией на {cpu_count} ядрах:")
            print(f"  ⚡ 1000 клиентов: {parallel_time_1000:.0f} сек ({parallel_time_1000/60:.1f} мин)")
            print(f"  ⚡ Все {len(client_ids)} клиентов: {parallel_time_all:.0f} сек ({parallel_time_all/60:.1f} мин)")
            
            # Ускорение
            speedup = time_for_1000 / parallel_time_1000
            print(f"  🎯 Теоретическое ускорение: {speedup:.1f}x")
            print(f"  🎯 Реальное ускорение (85% эффективность): {speedup * 0.85:.1f}x")
    
    # Итоговый анализ
    print(f"\n📈 ИТОГОВЫЙ АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ:")
    print("=" * 55)
    
    successful_results = [r for r in results if r['success_rate'] > 80]
    
    if len(successful_results) >= 2:
        # Анализируем масштабируемость
        large_result = successful_results[-1]
        small_result = successful_results[0]
        
        scaling_factor = large_result['test_size'] / small_result['test_size']
        time_scaling = large_result['avg_time_per_client'] / small_result['avg_time_per_client']
        
        print(f"📊 Масштабируемость:")
        print(f"  Размер выборки увеличен в {scaling_factor:.1f} раз")
        print(f"  Время на клиента изменилось в {time_scaling:.2f} раз")
        
        if time_scaling < 1.2:
            print("  ✅ Отличная масштабируемость!")
        elif time_scaling < 2.0:
            print("  ⚠️ Умеренное замедление при росте нагрузки")
        else:
            print("  ❌ Значительное замедление - нужна оптимизация")
        
        # Рекомендации
        best_result = min(successful_results, key=lambda x: x['avg_time_per_client'])
        print(f"\n💡 Рекомендации для параллелизации:")
        print(f"  🎯 Оптимальный размер батча: {best_result['test_size']} клиентов")
        print(f"  ⚡ Рекомендуемое количество процессов: {min(cpu_count, 20)}")
        print(f"  📦 Размер очереди задач: {min(cpu_count * 2, 50)}")
        
        # Финальные прогнозы для всей базы
        best_time_per_client = best_result['avg_time_per_client']
        total_clients = len(client_ids)
        
        print(f"\n🎯 ФИНАЛЬНЫЕ ПРОГНОЗЫ для {total_clients} клиентов:")
        print(f"  🐌 Последовательно: {(best_time_per_client * total_clients)/60:.1f} минут")
        print(f"  🚀 Параллельно (24 ядра): {(best_time_per_client * total_clients)/(cpu_count * 0.85)/60:.1f} минут")
        print(f"  ⚡ Ускорение: {(cpu_count * 0.85):.1f}x")
    else:
        print("❌ Недостаточно успешных тестов для анализа масштабируемости")
        
    print(f"\n🔧 Готов к созданию параллельной версии!")

if __name__ == "__main__":
    test_simple_performance() 