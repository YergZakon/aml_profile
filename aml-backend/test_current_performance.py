import sqlite3
import time
import os
from datetime import datetime

# Импортируем функции профилирования
try:
    from customer_profile_afm import CustomerProfile
    from geographic_profile_afm import GeographicProfile
    from transaction_profile_afm import TransactionProfile
    from behavioral_profile_afm import BehavioralProfile
    from network_profile_afm import NetworkProfile
    print("✅ Все модули профилирования загружены успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    exit(1)

def get_available_databases():
    """Получение списка доступных баз данных"""
    db_files = []
    for file in os.listdir('.'):
        if file.endswith('.db'):
            db_files.append(file)
    return db_files

def test_database_content(db_path):
    """Тестирование содержимого базы данных"""
    print(f"\n🔍 Тестирование базы данных: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Таблицы: {', '.join(tables)}")
        
        # Ищем таблицы с клиентами
        client_tables = ['clients', 'customer_profiles', 'customers']
        client_table = None
        client_count = 0
        
        for table in client_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    client_table = table
                    client_count = count
                    break
        
        # Ищем таблицы с транзакциями
        tx_tables = ['transactions', 'transaction_data', 'tx']
        tx_table = None
        tx_count = 0
        
        for table in tx_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    tx_table = table
                    tx_count = count
                    break
        
        print(f"👥 Клиенты: {client_count} записей в таблице '{client_table}'")
        print(f"💸 Транзакции: {tx_count} записей в таблице '{tx_table}'")
        
        if client_table and client_count > 0:
            # Получаем примеры клиентов
            cursor.execute(f"SELECT * FROM {client_table} LIMIT 5")
            columns = [description[0] for description in cursor.description]
            clients = cursor.fetchall()
            
            print(f"\n👤 Структура таблицы клиентов:")
            print(f"Столбцы: {', '.join(columns)}")
            
            # Возвращаем информацию для тестирования
            conn.close()
            return {
                'client_table': client_table,
                'client_count': client_count,
                'tx_table': tx_table,
                'tx_count': tx_count,
                'sample_clients': [dict(client) for client in clients]
            }
        
        conn.close()
        return None
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def analyze_single_client_current(client_data, db_path):
    """Текущий метод анализа одного клиента (последовательный)"""
    
    # Создаем подключение к БД
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # Получаем ID клиента
        client_id = client_data.get('client_id') or client_data.get('customer_id') or client_data.get('id')
        
        if not client_id:
            print("❌ Не найден ID клиента")
            return None
        
        # Создаем экземпляры профилей
        customer_profile = CustomerProfile()
        geographic_profile = GeographicProfile(None)
        transaction_profile = TransactionProfile()
        behavioral_profile = BehavioralProfile(client_id)
        network_profile = NetworkProfile()
        
        # Создаем mock транзакцию для анализа
        mock_transaction = {
            'client_id': client_id,
            'sender_id': client_id,
            'beneficiary_id': 'MOCK_BENEFICIARY',
            'amount': 1000000,
            'currency': 'KZT',
            'date': datetime.now(),
            'country': 'KZ'
        }
        
        # Выполняем анализ (симуляция)
        start_time = time.time()
        
        # 1. Клиентский профиль
        customer_result = customer_profile.analyze_customer_data(mock_transaction)
        
        # 2. Географический профиль
        geographic_result = geographic_profile.analyze_transaction_geography(mock_transaction)
        
        # 3. Транзакционный профиль
        transaction_result = transaction_profile.analyze_transaction(mock_transaction)
        
        # 4. Поведенческий профиль
        behavioral_result = behavioral_profile.analyze_transaction(mock_transaction)
        
        # 5. Сетевой профиль
        network_result = network_profile.analyze_transaction_network(mock_transaction)
        
        end_time = time.time()
        analysis_time = end_time - start_time
        
        # Расчет общего риск-скора
        total_risk_score = (
            customer_result.get('risk_score', 0) +
            geographic_result.get('total_risk_score', 0) +
            transaction_result.get('final_risk_score', 0) +
            behavioral_result.get('risk_score', 0) +
            network_result.get('risk_score', 0)
        )
        
        conn.close()
        
        return {
            'client_id': client_id,
            'analysis_time': analysis_time,
            'total_risk_score': total_risk_score,
            'is_suspicious': total_risk_score > 10
        }
        
    except Exception as e:
        print(f"❌ Ошибка анализа клиента {client_id}: {e}")
        conn.close()
        return None

def test_current_performance():
    """Тестирование текущей производительности"""
    print("🚀 ТЕСТИРОВАНИЕ ТЕКУЩЕЙ ПРОИЗВОДИТЕЛЬНОСТИ AML-АНАЛИЗА")
    print("=" * 60)
    
    # Находим подходящую базу данных
    databases = get_available_databases()
    print(f"📁 Найдено баз данных: {len(databases)}")
    
    # Тестируем базы данных
    suitable_db = None
    db_info = None
    
    for db in databases:
        print(f"\n🔍 Проверяем {db}...")
        info = test_database_content(db)
        if info and info['client_count'] > 0:
            suitable_db = db
            db_info = info
            break
    
    if not suitable_db:
        print("❌ Не найдена подходящая база данных с клиентами")
        return
    
    print(f"\n✅ Используем базу данных: {suitable_db}")
    print(f"👥 Клиентов для анализа: {db_info['client_count']}")
    
    # Тестируем анализ разного количества клиентов
    test_sizes = [1, 5, 10, 50]
    
    for test_size in test_sizes:
        if test_size > db_info['client_count']:
            continue
            
        print(f"\n🧪 Тестирование анализа {test_size} клиентов:")
        print("-" * 40)
        
        # Берем первых N клиентов
        test_clients = db_info['sample_clients'][:test_size]
        
        start_time = time.time()
        successful_analyses = 0
        
        for i, client in enumerate(test_clients, 1):
            print(f"  Анализируем клиента {i}/{test_size}...", end=" ")
            
            result = analyze_single_client_current(client, suitable_db)
            if result:
                successful_analyses += 1
                print(f"✅ ({result['analysis_time']:.2f}с, риск: {result['total_risk_score']:.1f})")
            else:
                print("❌")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n📊 Результаты для {test_size} клиентов:")
        print(f"  ⏱️  Общее время: {total_time:.2f} секунд")
        print(f"  ⚡ Время на клиента: {total_time/test_size:.2f} секунд")
        print(f"  ✅ Успешно проанализировано: {successful_analyses}/{test_size}")
        
        if test_size > 1:
            print(f"  🔮 Прогноз для 1000 клиентов: {(total_time/test_size)*1000:.0f} секунд ({(total_time/test_size)*1000/60:.1f} минут)")
            print(f"  🚀 Потенциальное ускорение с 24 ядрами: {((total_time/test_size)*1000/60)/24:.1f} минут")

if __name__ == "__main__":
    test_current_performance() 