import sqlite3
import json

conn = sqlite3.connect('aml_system_with_enhanced_profile.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Проверяем структуру
cursor.execute('PRAGMA table_info(transactions)')
columns = [col[1] for col in cursor.fetchall()]
print("Поля в таблице transactions:")
print(columns)

# Проверяем статистику
cursor.execute('SELECT COUNT(*) as total FROM transactions')
total = cursor.fetchone()['total']

cursor.execute('SELECT COUNT(*) as suspicious FROM transactions WHERE is_suspicious = 1')
suspicious = cursor.fetchone()['suspicious']

print(f"\n=== СТАТИСТИКА ===")
print(f"Всего транзакций: {total}")
print(f"Подозрительных: {suspicious} ({suspicious/total*100:.1f}%)")

# Проверяем наличие поля suspicious_reasons
if 'suspicious_reasons' in columns:
    print("\n✅ Поле suspicious_reasons найдено!")
    
    # Показываем примеры
    cursor.execute('''
        SELECT transaction_id, amount_kzt, suspicious_reasons, final_risk_score
        FROM transactions 
        WHERE is_suspicious = 1 AND suspicious_reasons IS NOT NULL
        ORDER BY final_risk_score DESC
        LIMIT 3
    ''')
    
    print("\n=== ПРИМЕРЫ ПОДОЗРИТЕЛЬНЫХ ТРАНЗАКЦИЙ ===")
    for row in cursor.fetchall():
        print(f"\nID: {row['transaction_id']}")
        print(f"Сумма: {row['amount_kzt']:,.0f} KZT")
        print(f"Риск-скор: {row['final_risk_score']:.2f}")
        try:
            reasons = json.loads(row['suspicious_reasons'])
            print("Причины:")
            for reason in reasons[:5]:
                print(f"  - {reason}")
        except:
            print(f"Причины: {row['suspicious_reasons']}")
            
    # Проверяем новые индикаторы
    cursor.execute('''
        SELECT COUNT(*) as count 
        FROM transactions 
        WHERE suspicious_reasons LIKE '%Круглая сумма%' 
           OR suspicious_reasons LIKE '%Ночная операция%'
           OR suspicious_reasons LIKE '%структурирование%'
    ''')
    enhanced = cursor.fetchone()['count']
    print(f"\n✅ Транзакций с новыми индикаторами: {enhanced}")
else:
    print("\n❌ Поле suspicious_reasons НЕ найдено в базе данных")
    print("Эта база данных не содержит результаты улучшенного анализа")

conn.close() 