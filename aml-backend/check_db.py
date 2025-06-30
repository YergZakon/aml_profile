import sqlite3
import os

def check_database():
    db_path = 'aml_system.db'  # Изменяем на правильное имя базы данных
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return
    
    print(f"✅ База данных {db_path} найдена")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📊 Таблицы в базе данных ({len(tables)} шт.):")
        for table in tables:
            table_name = table[0]
            print(f"- {table_name}")
            
            # Получаем количество записей в таблице
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  Записей: {count:,}")
            except Exception as e:
                print(f"  Ошибка подсчета: {e}")
        
        # Проверим, есть ли клиенты (проверим разные возможные названия таблиц)
        client_tables = ['customer_profiles', 'clients', 'customers']
        clients_count = 0
        
        for table_name in client_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                clients_count = cursor.fetchone()[0]
                print(f"\n🏢 Клиентов в таблице {table_name}: {clients_count:,}")
                
                if clients_count > 0:
                    # Получим несколько примеров клиентов
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    columns = [description[0] for description in cursor.description]
                    sample_clients = cursor.fetchall()
                    
                    print(f"\n👥 Примеры клиентов из {table_name}:")
                    print(f"Столбцы: {', '.join(columns)}")
                    for i, client in enumerate(sample_clients, 1):
                        print(f"{i}. {client}")
                break
            except Exception:
                continue
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")

if __name__ == "__main__":
    check_database() 