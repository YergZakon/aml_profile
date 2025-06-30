import sqlite3
import json
import os

def check_network_analysis():
    db_path = 'aml-backend/aml_system_e840b2937714940f.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы
        cursor.execute('PRAGMA table_info(transactions)')
        columns = [col[1] for col in cursor.fetchall()]
        print("📋 Колонки в таблице transactions:")
        for col in columns:
            print(f"  - {col}")
        
        # Проверяем есть ли сетевые поля
        network_columns = [col for col in columns if 'network' in col.lower()]
        print(f"\n🔗 Колонки связанные с сетевым анализом: {network_columns}")
        
        # Проверяем suspicious_reasons на наличие сетевых меток
        cursor.execute("""
        SELECT COUNT(*) FROM transactions 
        WHERE suspicious_reasons LIKE '%сеть%' 
           OR suspicious_reasons LIKE '%схем%'
           OR suspicious_reasons LIKE '%цепочк%'
           OR suspicious_reasons LIKE '%циркуляр%'
        """)
        network_mentions = cursor.fetchone()[0]
        print(f"🕸️ Транзакций с упоминанием сетевых паттернов: {network_mentions}")
        
        # Проверяем примеры suspicious_reasons с сетевыми признаками
        cursor.execute("""
        SELECT transaction_id, suspicious_reasons FROM transactions 
        WHERE suspicious_reasons LIKE '%сеть%' 
           OR suspicious_reasons LIKE '%схем%'
           OR suspicious_reasons LIKE '%цепочк%'
           OR suspicious_reasons LIKE '%циркуляр%'
        LIMIT 5
        """)
        
        network_examples = cursor.fetchall()
        if network_examples:
            print("\n🔍 Примеры сетевых паттернов:")
            for tx_id, reasons in network_examples:
                try:
                    parsed_reasons = json.loads(reasons)
                    print(f"  {tx_id}: {parsed_reasons}")
                except:
                    print(f"  {tx_id}: {reasons}")
        
        # Проверяем есть ли отдельная таблица для сетевого анализа
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📊 Таблицы в базе данных: {tables}")
        
        network_tables = [table for table in tables if 'network' in table.lower()]
        print(f"🔗 Таблицы сетевого анализа: {network_tables}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_network_analysis() 