# Детальный анализ подозрительных клиентов
# analyze_suspicious_clients.py

import sqlite3
import json
from datetime import datetime

def analyze_top_suspicious_client(db_path: str, client_id: str):
    """Детальный анализ конкретного подозрительного клиента"""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ КЛИЕНТА: {client_id}")
    print("="*60)
    
    # 1. Информация о клиенте
    cursor.execute('''
    SELECT * FROM customer_profiles WHERE customer_id = ?
    ''', (client_id,))
    
    client = cursor.fetchone()
    if client:
        print(f"\n👤 ПРОФИЛЬ КЛИЕНТА:")
        print(f"├── Имя: {client['full_name']}")
        print(f"├── Тип: {'Физлицо' if client['is_individual'] else 'Юрлицо'}")
        print(f"├── Резидентство: {client['residence_country']}")
        print(f"├── Риск-скор: {client['overall_risk_score']}")
        print(f"└── СПО в истории: {client['str_count']}")
    
    # 2. Все транзакции клиента
    cursor.execute('''
    SELECT * FROM transactions 
    WHERE sender_id = ? OR beneficiary_id = ?
    ORDER BY transaction_date DESC
    ''', (client_id, client_id))
    
    transactions = cursor.fetchall()
    print(f"\n💸 ТРАНЗАКЦИИ ({len(transactions)} шт.):")
    
    total_sent = 0
    total_received = 0
    suspicious_count = 0
    
    for tx in transactions:
        is_sender = tx['sender_id'] == client_id
        amount = tx['amount_kzt']
        
        if is_sender:
            total_sent += amount
        else:
            total_received += amount
            
        if tx['is_suspicious']:
            suspicious_count += 1
            print(f"\n  🚨 Подозрительная транзакция {tx['transaction_id']}:")
            print(f"     Сумма: {amount:,.0f} тенге")
            print(f"     Дата: {tx['transaction_date']}")
            print(f"     Направление: {'Отправка' if is_sender else 'Получение'}")
            
            # Коды подозрительности
            indicators = json.loads(tx['risk_indicators'])
            if indicators.get('suspicion_codes'):
                print(f"     Коды: {indicators['suspicion_codes']}")
    
    print(f"\n📊 ФИНАНСОВАЯ СТАТИСТИКА:")
    print(f"├── Отправлено: {total_sent:,.0f} тенге")
    print(f"├── Получено: {total_received:,.0f} тенге")
    print(f"├── Баланс: {total_received - total_sent:,.0f} тенге")
    print(f"└── Подозрительных операций: {suspicious_count} из {len(transactions)}")
    
    # 3. Связанные лица
    cursor.execute('''
    SELECT 
        CASE 
            WHEN sender_id = ? THEN beneficiary_id 
            ELSE sender_id 
        END as counterparty,
        COUNT(*) as tx_count,
        SUM(amount_kzt) as total_amount
    FROM transactions
    WHERE sender_id = ? OR beneficiary_id = ?
    GROUP BY counterparty
    ORDER BY total_amount DESC
    LIMIT 10
    ''', (client_id, client_id, client_id))
    
    print(f"\n🔗 ОСНОВНЫЕ КОНТРАГЕНТЫ:")
    for row in cursor.fetchall():
        # Получаем имя контрагента
        cursor.execute('SELECT full_name FROM customer_profiles WHERE customer_id = ?', 
                      (row['counterparty'],))
        name_row = cursor.fetchone()
        name = name_row['full_name'] if name_row else 'Неизвестный'
        
        print(f"├── {name} ({row['counterparty']})")
        print(f"│   Операций: {row['tx_count']}, Сумма: {row['total_amount']:,.0f} тенге")
    
    conn.close()

def find_network_schemes(db_path: str):
    """Поиск сетевых схем в загруженных данных"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🕸️ ПОИСК СЕТЕВЫХ СХЕМ:")
    print("="*60)
    
    # 1. Поиск круговых переводов
    cursor.execute('''
    WITH RECURSIVE paths AS (
        -- Начальные пути
        SELECT 
            sender_id as start,
            beneficiary_id as finish,
            sender_id || '->' || beneficiary_id as path,
            amount_kzt,
            1 as depth
        FROM transactions
        WHERE is_suspicious = 1
        
        UNION ALL
        
        -- Рекурсивное построение путей
        SELECT 
            p.start,
            t.beneficiary_id,
            p.path || '->' || t.beneficiary_id,
            p.amount_kzt,
            p.depth + 1
        FROM paths p
        JOIN transactions t ON p.finish = t.sender_id
        WHERE p.depth < 5
          AND p.path NOT LIKE '%' || t.beneficiary_id || '%'
          AND t.is_suspicious = 1
    )
    SELECT path, amount_kzt, depth
    FROM paths
    WHERE start = finish AND depth > 2
    ''')
    
    circles = cursor.fetchall()
    if circles:
        print("\n🔄 ОБНАРУЖЕНЫ КРУГОВЫЕ СХЕМЫ:")
        for circle in circles:
            print(f"├── {circle[0]}")
            print(f"│   Сумма: {circle[1]:,.0f} тенге, Глубина: {circle[2]}")
    else:
        print("✓ Круговых схем не обнаружено")
    
    # 2. Поиск схем дробления
    cursor.execute('''
    SELECT 
        sender_id,
        COUNT(DISTINCT beneficiary_id) as recipients,
        COUNT(*) as tx_count,
        SUM(amount_kzt) as total,
        AVG(amount_kzt) as avg_amount
    FROM transactions
    WHERE transaction_date >= date('now', '-7 days')
    GROUP BY sender_id
    HAVING recipients >= 5 AND avg_amount < 2000000
    ORDER BY tx_count DESC
    ''')
    
    smurfing = cursor.fetchall()
    if smurfing:
        print("\n💰 ВОЗМОЖНОЕ ДРОБЛЕНИЕ (СМУРФИНГ):")
        for row in smurfing:
            print(f"├── Отправитель: {row[0]}")
            print(f"│   Получателей: {row[1]}, Операций: {row[2]}")
            print(f"│   Общая сумма: {row[3]:,.0f}, Средняя: {row[4]:,.0f}")
    
    conn.close()

def generate_str_report(db_path: str, threshold_score: float = 7.0):
    """Генерация отчета СПО для АФМ"""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n📄 ГЕНЕРАЦИЯ СПО (СООБЩЕНИЯ О ПОДОЗРИТЕЛЬНЫХ ОПЕРАЦИЯХ)")
    print("="*60)
    
    # Выбираем транзакции для СПО
    cursor.execute('''
    SELECT 
        t.*,
        c1.full_name as sender_name,
        c2.full_name as beneficiary_name
    FROM transactions t
    LEFT JOIN customer_profiles c1 ON t.sender_id = c1.customer_id
    LEFT JOIN customer_profiles c2 ON t.beneficiary_id = c2.customer_id
    WHERE t.is_suspicious = 1 
      AND t.final_risk_score >= ?
    ORDER BY t.final_risk_score DESC
    LIMIT 20
    ''', (threshold_score,))
    
    str_transactions = cursor.fetchall()
    
    if str_transactions:
        print(f"\n📋 ТРАНЗАКЦИИ ДЛЯ СПО ({len(str_transactions)} шт.):")
        
        for i, tx in enumerate(str_transactions, 1):
            print(f"\n{i}. СПО #{tx['transaction_id']}")
            print(f"   Дата: {tx['transaction_date']}")
            print(f"   Сумма: {tx['amount_kzt']:,.0f} тенге")
            print(f"   Плательщик: {tx['sender_name']} ({tx['sender_id']})")
            print(f"   Получатель: {tx['beneficiary_name']} ({tx['beneficiary_id']})")
            print(f"   Риск-скор: {tx['final_risk_score']}")
            
            # Коды подозрительности
            indicators = json.loads(tx['risk_indicators'])
            if indicators.get('suspicion_codes'):
                print(f"   Коды АФМ: {', '.join(map(str, indicators['suspicion_codes']))}")
        
        # Сохраняем в файл
        with open('str_report.txt', 'w', encoding='utf-8') as f:
            f.write("СООБЩЕНИЕ О ПОДОЗРИТЕЛЬНЫХ ОПЕРАЦИЯХ\n")
            f.write(f"Дата формирования: {datetime.now()}\n")
            f.write(f"Количество операций: {len(str_transactions)}\n")
            f.write("="*60 + "\n")
            
            for tx in str_transactions:
                f.write(f"\nТранзакция: {tx['transaction_id']}\n")
                f.write(f"Сумма: {tx['amount_kzt']:,.0f} KZT\n")
                f.write(f"Плательщик: {tx['sender_name']}\n")
                f.write(f"Получатель: {tx['beneficiary_name']}\n")
                indicators = json.loads(tx['risk_indicators'])
                if indicators.get('suspicion_codes'):
                    f.write(f"Коды: {indicators['suspicion_codes']}\n")
                f.write("-"*40 + "\n")
        
        print(f"\n✅ Отчет сохранен в файл: str_report.txt")
    
    conn.close()

# Главная функция
def main():
    db_path = "aml_system.db"
    
    # 1. Анализируем топового подозрительного клиента
    top_client = "221140045516"  # КОРЕАН КАПИТАЛ
    analyze_top_suspicious_client(db_path, top_client)
    
    # 2. Ищем схемы
    find_network_schemes(db_path)
    
    # 3. Генерируем СПО
    generate_str_report(db_path, threshold_score=5.0)

if __name__ == "__main__":
    main()
