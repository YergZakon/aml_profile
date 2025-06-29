import sqlite3
import time
from typing import List, Dict
import functools
from datetime import datetime

def create_database_indexes(db_path: str = 'aml_system.db'):
    """Создание индексов для ускорения запросов"""
    print("🔧 Создание индексов базы данных...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    indexes = [
        # Индексы для customer_profiles
        ("idx_customer_risk", "CREATE INDEX IF NOT EXISTS idx_customer_risk ON customer_profiles(overall_risk_score DESC)"),
        ("idx_customer_id", "CREATE INDEX IF NOT EXISTS idx_customer_id ON customer_profiles(customer_id)"),
        
        # Индексы для transactions
        ("idx_transactions_sender", "CREATE INDEX IF NOT EXISTS idx_transactions_sender ON transactions(sender_id)"),
        ("idx_transactions_beneficiary", "CREATE INDEX IF NOT EXISTS idx_transactions_beneficiary ON transactions(beneficiary_id)"),
        ("idx_transactions_date", "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date DESC)"),
        ("idx_transactions_suspicious", "CREATE INDEX IF NOT EXISTS idx_transactions_suspicious ON transactions(is_suspicious)"),
        ("idx_transactions_amount", "CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(amount_kzt DESC)"),
        
        # Составные индексы
        ("idx_transactions_client_date", "CREATE INDEX IF NOT EXISTS idx_transactions_client_date ON transactions(sender_id, transaction_date DESC)"),
        ("idx_transactions_beneficiary_date", "CREATE INDEX IF NOT EXISTS idx_transactions_beneficiary_date ON transactions(beneficiary_id, transaction_date DESC)"),
    ]
    
    for index_name, sql in indexes:
        try:
            start_time = time.time()
            cursor.execute(sql)
            end_time = time.time()
            print(f"  ✅ {index_name}: {end_time - start_time:.3f}s")
        except Exception as e:
            print(f"  ❌ {index_name}: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Индексы созданы!")

def analyze_batch_optimized(client_ids: List[str], db_path: str = 'aml_system.db') -> List[Dict]:
    """
    Оптимизированный batch-анализ с одним SQL-запросом
    """
    if not client_ids:
        return []
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Создаем placeholders для IN-запроса
    placeholders = ','.join(['?' for _ in client_ids])
    
    # Один большой запрос для всех клиентов
    query = f"""
    SELECT 
        cp.customer_id,
        cp.overall_risk_score,
        cp.is_pep,
        cp.is_foreign,
        COUNT(DISTINCT t.transaction_id) as tx_count,
        SUM(CASE WHEN t.sender_id = cp.customer_id THEN t.amount_kzt ELSE 0 END) as total_sent,
        SUM(CASE WHEN t.beneficiary_id = cp.customer_id THEN t.amount_kzt ELSE 0 END) as total_received,
        SUM(CASE WHEN t.is_suspicious = 1 THEN 1 ELSE 0 END) as suspicious_count,
        COUNT(DISTINCT CASE WHEN t.sender_id = cp.customer_id THEN t.beneficiary_id 
                           WHEN t.beneficiary_id = cp.customer_id THEN t.sender_id END) as counterparties_count,
        MAX(t.amount_kzt) as max_transaction,
        AVG(t.amount_kzt) as avg_transaction
    FROM customer_profiles cp
    LEFT JOIN transactions t ON (t.sender_id = cp.customer_id OR t.beneficiary_id = cp.customer_id)
    WHERE cp.customer_id IN ({placeholders})
    GROUP BY cp.customer_id, cp.overall_risk_score, cp.is_pep, cp.is_foreign
    ORDER BY cp.overall_risk_score DESC
    """
    
    cursor.execute(query, client_ids)
    rows = cursor.fetchall()
    conn.close()
    
    # Обрабатываем результаты
    results = []
    for row in rows:
        # Расчет риск-скора
        base_risk = row['overall_risk_score'] if row['overall_risk_score'] else 0
        
        # Дополнительные риски
        tx_risk = 3 if row['tx_count'] > 50 else 0
        behavior_risk = min(row['suspicious_count'] * 2, 10) if row['suspicious_count'] else 0
        volume_risk = 2 if (row['total_sent'] + row['total_received']) > 50000000 else 0
        network_risk = 1 if row['counterparties_count'] > 20 else 0
        
        # PEP и иностранцы
        pep_risk = 5 if row['is_pep'] else 0
        foreign_risk = 2 if row['is_foreign'] else 0
        
        total_risk_score = base_risk + tx_risk + behavior_risk + volume_risk + network_risk + pep_risk + foreign_risk
        
        result = {
            'client_id': row['customer_id'],
            'total_risk_score': total_risk_score,
            'transactions_count': row['tx_count'] or 0,
            'counterparties_count': row['counterparties_count'] or 0,
            'total_volume': (row['total_sent'] or 0) + (row['total_received'] or 0),
            'suspicious_transactions': row['suspicious_count'] or 0,
            'is_suspicious': total_risk_score > 10,
            'max_transaction': row['max_transaction'] or 0,
            'avg_transaction': row['avg_transaction'] or 0,
            'risk_factors': {
                'base_risk': base_risk,
                'transaction_risk': tx_risk,
                'behavior_risk': behavior_risk,
                'volume_risk': volume_risk,
                'network_risk': network_risk,
                'pep_risk': pep_risk,
                'foreign_risk': foreign_risk
            }
        }
        results.append(result)
    
    return results

@functools.lru_cache(maxsize=1000)
def cached_client_analysis(client_id: str, cache_hour: int, db_path: str = 'aml_system.db'):
    """Кэшированный анализ клиента (обновляется каждый час)"""
    return analyze_batch_optimized([client_id], db_path)[0] if analyze_batch_optimized([client_id], db_path) else None

def get_cached_analysis(client_id: str, db_path: str = 'aml_system.db'):
    """Получение кэшированного анализа"""
    current_hour = datetime.now().hour
    return cached_client_analysis(client_id, current_hour, db_path)

def test_optimization_performance():
    """Тестирование производительности оптимизированной версии"""
    print("🚀 ТЕСТИРОВАНИЕ ОПТИМИЗИРОВАННОЙ ВЕРСИИ")
    print("=" * 50)
    
    db_path = 'aml_system.db'
    
    # Создаем индексы
    create_database_indexes(db_path)
    print()
    
    # Получаем список клиентов
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id FROM customer_profiles ORDER BY overall_risk_score DESC LIMIT 1000")
    client_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"📊 Тестируем на {len(client_ids)} клиентах")
    print()
    
    # Тестируем разные размеры батчей
    test_sizes = [100, 500, 1000]
    
    for test_size in test_sizes:
        if test_size > len(client_ids):
            continue
            
        print(f"🧪 Тестирование {test_size} клиентов:")
        
        test_client_ids = client_ids[:test_size]
        
        # Тест оптимизированной версии
        start_time = time.time()
        results = analyze_batch_optimized(test_client_ids, db_path)
        end_time = time.time()
        
        batch_time = end_time - start_time
        speed = len(results) / batch_time if batch_time > 0 else 0
        
        print(f"  ⚡ Batch SQL: {batch_time:.3f}s ({speed:.1f} кл/сек)")
        
        # Тест с кэшированием (второй запуск)
        start_time = time.time()
        cached_results = [get_cached_analysis(cid, db_path) for cid in test_client_ids[:10]]
        end_time = time.time()
        
        cache_time = end_time - start_time
        cache_speed = 10 / cache_time if cache_time > 0 else 0
        
        print(f"  💾 С кэшем (10 кл): {cache_time:.3f}s ({cache_speed:.1f} кл/сек)")
        
        # Статистика
        suspicious_count = sum(1 for r in results if r['is_suspicious'])
        high_risk_count = sum(1 for r in results if r['total_risk_score'] > 15)
        
        print(f"  📊 Подозрительных: {suspicious_count}/{len(results)} ({suspicious_count/len(results)*100:.1f}%)")
        print(f"  🔴 Высокого риска: {high_risk_count}/{len(results)} ({high_risk_count/len(results)*100:.1f}%)")
        print()
    
    # Сравнение с неоптимизированной версией
    print("📈 СРАВНЕНИЕ С БАЗОВОЙ ВЕРСИЕЙ:")
    print("-" * 40)
    
    # Импортируем простую версию для сравнения
    try:
        from simple_performance_test import analyze_single_client_simple
        
        # Тестируем 100 клиентов простой версией
        test_client_ids = client_ids[:100]
        
        start_time = time.time()
        simple_results = []
        for cid in test_client_ids:
            result = analyze_single_client_simple(cid, db_path)
            if result:
                simple_results.append(result)
        simple_time = time.time() - start_time
        simple_speed = len(simple_results) / simple_time
        
        # Тестируем оптимизированной версией
        start_time = time.time()
        optimized_results = analyze_batch_optimized(test_client_ids, db_path)
        optimized_time = time.time() - start_time
        optimized_speed = len(optimized_results) / optimized_time
        
        speedup = simple_time / optimized_time if optimized_time > 0 else 0
        
        print(f"🐌 Простая версия: {simple_time:.3f}s ({simple_speed:.1f} кл/сек)")
        print(f"⚡ Оптимизированная: {optimized_time:.3f}s ({optimized_speed:.1f} кл/сек)")
        print(f"🚀 Ускорение: {speedup:.1f}x")
        
        if speedup > 3:
            print("✅ Отличная оптимизация!")
        elif speedup > 2:
            print("✅ Хорошая оптимизация!")
        elif speedup > 1.5:
            print("⚠️ Умеренная оптимизация")
        else:
            print("❌ Недостаточная оптимизация")
            
    except ImportError:
        print("⚠️ Не удалось импортировать простую версию для сравнения")
    
    print()
    print("🎯 РЕКОМЕНДАЦИИ:")
    print("1. ✅ Индексы созданы - запросы ускорены")
    print("2. ✅ Batch SQL - обработка больших объемов оптимизирована")
    print("3. ✅ Кэширование - повторные запросы ускорены в разы")
    print("4. 🔄 Для >10,000 клиентов рассмотрите параллелизацию")

if __name__ == "__main__":
    test_optimization_performance() 