import sqlite3

conn = sqlite3.connect('aml_system_enhanced_1750918593.db')
cursor = conn.cursor()

# Проверяем структуру таблицы
cursor.execute('PRAGMA table_info(transactions)')
columns = cursor.fetchall()

print("Структура таблицы transactions:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

# Проверяем первую транзакцию
cursor.execute('SELECT * FROM transactions LIMIT 1')
row = cursor.fetchone()
if row:
    print("\nПример данных:")
    for i, col in enumerate(columns):
        print(f"  {col[1]}: {row[i]}")

conn.close() 