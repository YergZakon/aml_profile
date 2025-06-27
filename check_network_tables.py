import sqlite3
import json
import os

def check_network_tables():
    db_path = 'aml-backend/aml_system_e840b2937714940f.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем таблицу network_connections
        print("🔗 Таблица network_connections:")
        cursor.execute('SELECT COUNT(*) FROM network_connections')
        count = cursor.fetchone()[0]
        print(f"  Записей: {count}")
        
        if count > 0:
            cursor.execute('SELECT * FROM network_connections LIMIT 5')
            connections = cursor.fetchall()
            cursor.execute('PRAGMA table_info(network_connections)')
            columns = [col[1] for col in cursor.fetchall()]
            print(f"  Колонки: {columns}")
            print("  Примеры:")
            for conn_row in connections:
                print(f"    {dict(zip(columns, conn_row))}")
        
        # Проверяем таблицу detected_schemes
        print("\n🕸️ Таблица detected_schemes:")
        cursor.execute('SELECT COUNT(*) FROM detected_schemes')
        count = cursor.fetchone()[0]
        print(f"  Записей: {count}")
        
        if count > 0:
            cursor.execute('SELECT * FROM detected_schemes LIMIT 5')
            schemes = cursor.fetchall()
            cursor.execute('PRAGMA table_info(detected_schemes)')
            columns = [col[1] for col in cursor.fetchall()]
            print(f"  Колонки: {columns}")
            print("  Примеры:")
            for scheme_row in schemes:
                scheme_dict = dict(zip(columns, scheme_row))
                print(f"    {scheme_dict}")
        
        # Проверяем связи между таблицами
        print("\n🔍 Проверка связей:")
        cursor.execute("""
        SELECT DISTINCT scheme_type, COUNT(*) as count 
        FROM detected_schemes 
        GROUP BY scheme_type
        """)
        scheme_types = cursor.fetchall()
        if scheme_types:
            print("  Типы обнаруженных схем:")
            for scheme_type, count in scheme_types:
                print(f"    {scheme_type}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_network_tables() 