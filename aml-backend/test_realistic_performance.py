import sqlite3
import time
import os
import psutil
from datetime import datetime

def analyze_single_client_realistic(client_id, db_path):
    """Реалистичный анализ одного клиента с реальными запросами к БД"""
    
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
        
        # 2. Получаем все транзакции клиента
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE sender_id = ? OR beneficiary_id = ?
            ORDER BY transaction_date DESC
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
            else:
                total_received += tx['amount_kzt']
                
            if tx['is_suspicious']:
                suspicious_count += 1
                
            # Собираем географию - исправляем доступ к полям
            sender_country = tx['sender_country'] if 'sender_country' in tx.keys() else 'KZ'
            beneficiary_country = tx['beneficiary_country'] if 'beneficiary_country' in tx.keys() else 'KZ'
            countries.add(sender_country)
            countries.add(beneficiary_country)
            
            # Собираем контрагентов
            if tx['sender_id'] == client_id:
                counterparties.add(tx['beneficiary_id'])
            else:
                counterparties.add(tx['sender_id'])
        
        # 4. Получаем сетевые связи
        cursor.execute('''
            SELECT * FROM network_connections 
            WHERE participant_1 = ? OR participant_2 = ?
            LIMIT 100
        ''', (client_id, client_id))
        network_connections = cursor.fetchall()
        
        # 5. Проверяем историю подозрительных операций
        cursor.execute('''
            SELECT COUNT(*) as alert_count 
            FROM alerts 
            WHERE client_id = ? AND created_at >= date('now', '-90 days')
        ''', (client_id,))
        recent_alerts_row = cursor.fetchone()
        recent_alerts = recent_alerts_row['alert_count'] if recent_alerts_row else 0
        
        # 6. Расчет риск-скора
        base_risk = client_profile['overall_risk_score'] if client_profile['overall_risk_score'] else 0
        
        # Географический риск
        geo_risk = len([c for c in countries if c not in ['KZ', 'RU', 'CN']]) * 2
        
        # Транзакционный риск
        tx_risk = 0
        if len(transactions) > 0:
            avg_amount = (total_sent + total_received) / len(transactions)
            if avg_amount > 5000000:  # > 5 млн тенге
                tx_risk += 3
        
        # Поведенческий риск
        behavior_risk = 0
        if suspicious_count > 0:
            behavior_risk = min(suspicious_count * 2, 10)
        
        # Сетевой риск
        network_risk = min(len(network_connections) * 0.5, 5)
        
        # Общий риск
        total_risk_score = base_risk + geo_risk + tx_risk + behavior_risk + network_risk
        
        end_time = time.time()
        analysis_time = end_time - start_time
        
        conn.close()
        
        return {
            'client_id': client_id,
            'analysis_time': analysis_time,
            'total_risk_score': total_risk_score,
            'transactions_count': len(transactions),
            'network_connections': len(network_connections),
            'countries_count': len(countries),
            'counterparties_count': len(counterparties),
            'is_suspicious': total_risk_score > 10,
            'recent_alerts': recent_alerts
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

def test_realistic_performance():
    """Реалистичное тестирование производительности с реальными данными"""
    print("🎯 РЕАЛИСТИЧНОЕ ТЕСТИРОВАНИЕ ПРОИЗВОДИТЕЛЬНОСТИ AML-АНАЛИЗА")
    print("=" * 65)
    
    db_path = 'aml_system.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return
    
    # Получаем информацию о системе
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    print(f"💻 Система:")
    print(f"   CPU ядер: {cpu_count}")
    print(f"   RAM: {memory_gb:.1f} GB")
    
    # Получаем список клиентов
    print(f"\n📊 Получаем список клиентов...")
    client_ids = get_client_list(db_path, 1000)
    print(f"✅ Найдено клиентов: {len(client_ids)}")
    
    # Тестируем разные размеры выборок
    test_sizes = [1, 5, 10, 25, 50, 100]
    
    results = []
    
    for test_size in test_sizes:
        if test_size > len(client_ids):
            continue
            
        print(f"\n🧪 Тестирование анализа {test_size} клиентов:")
        print("-" * 50)
        
        # Берем первых N клиентов с наивысшим риском
        test_clients = client_ids[:test_size]
        
        start_time = time.time()
        successful_analyses = 0
        total_transactions = 0
        total_connections = 0
        suspicious_clients = 0
        
        # Мониторим использование ресурсов
        initial_memory = psutil.virtual_memory().percent
        
        for i, client_id in enumerate(test_clients, 1):
            if i <= 5 or i % 10 == 0:  # Показываем прогресс
                print(f"  📋 Анализируем клиента {i}/{test_size}...", end=" ")
            
            result = analyze_single_client_realistic(client_id, db_path)
            if result:
                successful_analyses += 1
                total_transactions += result['transactions_count']
                total_connections += result['network_connections']
                if result['is_suspicious']:
                    suspicious_clients += 1
                    
                if i <= 5 or i % 10 == 0:
                    print(f"✅ ({result['analysis_time']:.3f}с, риск: {result['total_risk_score']:.1f})")
            else:
                if i <= 5 or i % 10 == 0:
                    print("❌")
        
        end_time = time.time()
        total_time = end_time - start_time
        final_memory = psutil.virtual_memory().percent
        
        # Сохраняем результаты
        result_data = {
            'test_size': test_size,
            'total_time': total_time,
            'avg_time_per_client': total_time / test_size,
            'successful_analyses': successful_analyses,
            'total_transactions': total_transactions,
            'total_connections': total_connections,
            'suspicious_clients': suspicious_clients,
            'memory_usage_change': final_memory - initial_memory
        }
        results.append(result_data)
        
        print(f"\n📊 Результаты для {test_size} клиентов:")
        print(f"  ⏱️  Общее время: {total_time:.2f} секунд")
        print(f"  ⚡ Время на клиента: {total_time/test_size:.3f} секунд")
        print(f"  ✅ Успешно проанализировано: {successful_analyses}/{test_size}")
        print(f"  💸 Обработано транзакций: {total_transactions:,}")
        print(f"  🕸️  Сетевых связей: {total_connections:,}")
        print(f"  🚨 Подозрительных клиентов: {suspicious_clients}")
        print(f"  💾 Изменение памяти: {final_memory - initial_memory:+.1f}%")
        
        # Прогнозы
        if test_size >= 10 and successful_analyses > 0:
            time_for_1000 = (total_time / successful_analyses) * 1000
            time_for_all_clients = (total_time / successful_analyses) * len(client_ids)
            
            print(f"\n🔮 Прогнозы:")
            print(f"  📈 1000 клиентов: {time_for_1000:.0f} сек ({time_for_1000/60:.1f} мин)")
            print(f"  📈 Все {len(client_ids)} клиентов: {time_for_all_clients:.0f} сек ({time_for_all_clients/60:.1f} мин)")
            
            # Прогноз с параллелизацией
            parallel_time_1000 = time_for_1000 / cpu_count
            parallel_time_all = time_for_all_clients / cpu_count
            
            print(f"\n🚀 С параллелизацией на {cpu_count} ядрах:")
            print(f"  ⚡ 1000 клиентов: {parallel_time_1000:.0f} сек ({parallel_time_1000/60:.1f} мин)")
            print(f"  ⚡ Все {len(client_ids)} клиентов: {parallel_time_all:.0f} сек ({parallel_time_all/60:.1f} мин)")
            
            # Ускорение
            speedup = time_for_1000 / parallel_time_1000
            print(f"  🎯 Ускорение: {speedup:.1f}x")
    
    # Итоговый анализ
    print(f"\n📈 ИТОГОВЫЙ АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ:")
    print("=" * 50)
    
    successful_results = [r for r in results if r['successful_analyses'] > 0]
    
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
        
        # Рекомендации по параллелизации
        best_result = min(successful_results, key=lambda x: x['avg_time_per_client'])
        print(f"\n💡 Рекомендации:")
        print(f"  🎯 Оптимальный размер батча: {best_result['test_size']} клиентов")
        print(f"  ⚡ Рекомендуемое количество процессов: {min(cpu_count, 20)}")
        print(f"  💾 Контроль памяти: {'Требуется' if max(r['memory_usage_change'] for r in results) > 10 else 'Не требуется'}")
    else:
        print("❌ Недостаточно успешных анализов для оценки масштабируемости")

if __name__ == "__main__":
    test_realistic_performance() 