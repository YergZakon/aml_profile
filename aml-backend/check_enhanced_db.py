import sqlite3
import json

# Подключаемся к новой базе данных
conn = sqlite3.connect('aml_system_enhanced_1750918593.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Проверяем общую статистику
cursor.execute('SELECT COUNT(*) as total FROM transactions')
total = cursor.fetchone()['total']

cursor.execute('SELECT COUNT(*) as suspicious FROM transactions WHERE is_suspicious = 1')
suspicious = cursor.fetchone()['suspicious']

print(f"=== СТАТИСТИКА НОВОЙ БАЗЫ ДАННЫХ ===")
print(f"Всего транзакций: {total}")
print(f"Подозрительных транзакций: {suspicious} ({suspicious/total*100:.1f}%)")

# Показываем примеры подозрительных транзакций
print(f"\n=== ПРИМЕРЫ ПОДОЗРИТЕЛЬНЫХ ТРАНЗАКЦИЙ ===")
cursor.execute('''
    SELECT transaction_id, sender_name, beneficiary_name, amount_kzt, 
           final_risk_score, suspicious_reasons, transaction_date
    FROM transactions 
    WHERE is_suspicious = 1 
    ORDER BY final_risk_score DESC
    LIMIT 5
''')

for row in cursor.fetchall():
    print(f"\nID: {row['transaction_id']}")
    print(f"Отправитель: {row['sender_name']} → Получатель: {row['beneficiary_name']}")
    print(f"Сумма: {row['amount_kzt']:,.0f} KZT")
    print(f"Риск-скор: {row['final_risk_score']:.2f}/10")
    print(f"Дата: {row['transaction_date']}")
    
    # Парсим причины
    try:
        reasons = json.loads(row['suspicious_reasons'])
        if isinstance(reasons, list):
            print("Причины:")
            for reason in reasons[:5]:  # Показываем первые 5 причин
                print(f"  - {reason}")
    except:
        print(f"Причины: {row['suspicious_reasons'][:200]}...")

# Проверяем, есть ли новые поля от улучшенного профиля
print(f"\n=== ПРОВЕРКА УЛУЧШЕННОГО АНАЛИЗА ===")
cursor.execute('''
    SELECT COUNT(*) as count 
    FROM transactions 
    WHERE suspicious_reasons LIKE '%Круглая сумма%' 
       OR suspicious_reasons LIKE '%Ночная операция%'
       OR suspicious_reasons LIKE '%структурирование%'
''')
enhanced_count = cursor.fetchone()['count']
print(f"Транзакций с новыми индикаторами риска: {enhanced_count}")

conn.close() 