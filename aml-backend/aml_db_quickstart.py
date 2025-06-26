# Быстрый старт работы с базой данных AML
from datetime import datetime

# ШАГ 1: СОЗДАНИЕ БАЗЫ ДАННЫХ
# Просто импортируйте и создайте объект - база создастся автоматически
from aml_database_setup import AMLDatabaseManager

# Создаем менеджер БД (файл создастся в текущей папке)
db = AMLDatabaseManager("my_aml_system.db")
print("✅ База данных создана!")

# ШАГ 2: СОХРАНЕНИЕ КЛИЕНТА
# Минимальный набор данных для клиента
new_customer = {
    'customer_id': 'CL_12345',  # Уникальный ID
    'full_name': 'Петров Петр Петрович',
    'iin': '850115301234',  # ИИН
    'overall_risk_score': 3.5  # Риск-скор
}

db.save_customer_profile(new_customer)
print("✅ Клиент сохранен!")

# ШАГ 3: СОХРАНЕНИЕ ТРАНЗАКЦИИ
# Минимальные данные для транзакции
new_transaction = {
    'transaction_id': 'TX_2024_001',
    'amount': 5000000,  # 5 млн тенге
    'amount_kzt': 5000000,
    'transaction_date': datetime.now(),
    'sender_id': 'CL_12345',
    'beneficiary_id': 'CL_67890',
    'final_risk_score': 4.2
}

db.save_transaction(new_transaction)
print("✅ Транзакция сохранена!")

# ШАГ 4: ПОЛУЧЕНИЕ ДАННЫХ
# Получить профиль клиента
profile = db.get_customer_profile('CL_12345')
if profile:
    print(f"\n📋 Профиль клиента {profile['full_name']}:")
    print(f"   Риск: {profile['overall_risk_score']}")
    print(f"   Транзакций: {profile['total_transaction_count']}")

# ШАГ 5: АНАЛИТИКА
# Получить клиентов высокого риска
high_risk_customers = db.get_high_risk_customers(limit=10)
print(f"\n⚠️ Найдено клиентов высокого риска: {len(high_risk_customers)}")

# Получить подозрительные транзакции за последние 7 дней
suspicious = db.get_recent_suspicious_transactions(days=7)
print(f"🔍 Подозрительных транзакций за неделю: {len(suspicious)}")

# Получить общую статистику
stats = db.get_system_statistics()
print(f"\n📊 Статистика системы:")
print(f"   Всего клиентов: {stats['customers']['total_customers']}")
print(f"   Всего транзакций: {stats['transactions']['total_transactions']}")

# ШАГ 6: СОЗДАНИЕ АЛЕРТА
# Когда обнаружили что-то подозрительное
alert = {
    'transaction_id': 'TX_2024_001',
    'alert_type': 'TRANSACTION',
    'severity': 'HIGH',
    'title': 'Превышение порога',
    'risk_score': 7.5
}

alert_id = db.create_alert(alert)
print(f"\n⚠️ Создан алерт #{alert_id}")

# НЕ ЗАБУДЬТЕ ЗАКРЫТЬ СОЕДИНЕНИЕ!
db.close()

# ===============================================
# ПОЛЕЗНЫЕ ПРИМЕРЫ ЗАПРОСОВ
# ===============================================

def useful_queries():
    """Примеры полезных запросов к базе"""
    db = AMLDatabaseManager("my_aml_system.db")
    
    # 1. Найти все транзакции клиента
    cursor = db.connection.cursor()
    cursor.execute('''
    SELECT * FROM transactions 
    WHERE sender_id = ? OR beneficiary_id = ?
    ORDER BY transaction_date DESC
    ''', ('CL_12345', 'CL_12345'))
    
    transactions = cursor.fetchall()
    print(f"Транзакций клиента: {len(transactions)}")
    
    # 2. Найти связанных клиентов
    cursor.execute('''
    SELECT DISTINCT 
        CASE 
            WHEN sender_id = ? THEN beneficiary_id
            ELSE sender_id
        END as connected_customer
    FROM transactions
    WHERE sender_id = ? OR beneficiary_id = ?
    ''', ('CL_12345', 'CL_12345', 'CL_12345'))
    
    connected = cursor.fetchall()
    print(f"Связанных клиентов: {len(connected)}")
    
    # 3. Транзакции в офшоры
    cursor.execute('''
    SELECT t.*, c.full_name as beneficiary_name
    FROM transactions t
    LEFT JOIN customer_profiles c ON t.beneficiary_id = c.customer_id
    WHERE t.beneficiary_country IN ('KY', 'VG', 'BS', 'BZ', 'SC')
    ORDER BY t.amount_kzt DESC
    ''')
    
    offshore_tx = cursor.fetchall()
    print(f"Транзакций в офшоры: {len(offshore_tx)}")
    
    db.close()

# ===============================================
# РАБОТА С НАСТРОЙКАМИ
# ===============================================

def work_with_settings():
    """Пример работы с настройками системы"""
    db = AMLDatabaseManager("my_aml_system.db")
    
    # Получить настройку
    cursor = db.connection.cursor()
    cursor.execute('''
    SELECT setting_value FROM system_settings 
    WHERE setting_key = ?
    ''', ('threshold_cash',))
    
    threshold = cursor.fetchone()
    if threshold:
        print(f"Текущий порог для наличных: {threshold[0]} тенге")
    
    # Изменить настройку
    cursor.execute('''
    UPDATE system_settings 
    SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
    WHERE setting_key = ?
    ''', ('3000000', 'threshold_cash'))
    
    db.connection.commit()
    print("Порог обновлен до 3 млн тенге")
    
    # Получить все настройки
    cursor.execute('SELECT * FROM system_settings')
    all_settings = cursor.fetchall()
    
    print("\n📋 Все настройки системы:")
    for setting in all_settings:
        print(f"  • {setting['setting_key']}: {setting['setting_value']}")
    
    db.close()

# ===============================================
# ИНТЕГРАЦИЯ С ПРОФИЛЯМИ
# ===============================================

def integrate_with_profiles():
    """Пример интеграции БД с профилями"""
    from customer_profile import CustomerProfile
    from transaction_profile import TransactionProfile
    
    db = AMLDatabaseManager("my_aml_system.db")
    
    # Создаем профиль в коде
    profile = CustomerProfile("CL_99999")
    profile.update_personal_info(
        full_name="Тестовый Клиент",
        iin="990101501234"
    )
    profile.calculate_risk_score()
    
    # Сохраняем в БД
    profile_data = {
        'customer_id': profile.customer_id,
        'full_name': profile.personal_info['full_name'],
        'iin': profile.personal_info['iin'],
        'overall_risk_score': profile.risk_factors['overall_risk_score'],
        'base_risk_level': profile.risk_factors['base_risk_level'],
        'behavior_patterns': profile.behavior_patterns,
        'typical_counterparties': profile.transaction_stats['typical_counterparties']
    }
    
    db.save_customer_profile(profile_data)
    print("✅ Профиль из кода сохранен в БД")
    
    # Загружаем обратно
    loaded_data = db.get_customer_profile("CL_99999")
    if loaded_data:
        # Восстанавливаем профиль
        restored_profile = CustomerProfile(loaded_data['customer_id'])
        restored_profile.personal_info['full_name'] = loaded_data['full_name']
        restored_profile.risk_factors['overall_risk_score'] = loaded_data['overall_risk_score']
        print(f"✅ Профиль загружен: {restored_profile.personal_info['full_name']}")
    
    db.close()

# ===============================================
# РЕЗЕРВНОЕ КОПИРОВАНИЕ
# ===============================================

def backup_database():
    """Создание резервной копии БД"""
    import shutil
    from datetime import datetime
    
    source_db = "my_aml_system.db"
    backup_name = f"backup_aml_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    shutil.copy2(source_db, backup_name)
    print(f"✅ Резервная копия создана: {backup_name}")

# Для запуска примеров раскомментируйте нужные строки:
# useful_queries()
# work_with_settings()
# integrate_with_profiles()
# backup_database()
