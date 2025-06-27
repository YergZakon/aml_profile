#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'aml-backend'))

from aml_integration_system import AMLDatabaseManager

def check_good_transactions():
    """Ищем транзакции с корректными данными для тестирования"""
    
    db = AMLDatabaseManager('aml_system_e840b2937714940f.db')
    cursor = db.get_db_cursor()
    
    # Ищем транзакции с корректными данными
    cursor.execute("""
        SELECT transaction_id, sender_name, beneficiary_name, amount_kzt, sender_id, beneficiary_id
        FROM transactions 
        WHERE beneficiary_name IS NOT NULL 
        AND beneficiary_name != '' 
        AND sender_name IS NOT NULL 
        AND sender_name != ''
        AND amount_kzt > 0
        LIMIT 10
    """)
    
    transactions = cursor.fetchall()
    
    print(f"🔍 Найдено {len(transactions)} транзакций с корректными данными:")
    
    for i, row in enumerate(transactions, 1):
        print(f"\n{i}. ID: {row[0]}")
        print(f"   От: {row[1]} ({row[4]})")
        print(f"   Кому: {row[2]} ({row[5]})")
        print(f"   Сумма: {row[3]:,.0f} KZT")
    
    if transactions:
        print(f"\n✅ Можно использовать транзакцию {transactions[0][0]} для тестирования")
        return transactions[0][0]
    else:
        print("❌ Не найдено подходящих транзакций")
        return None

if __name__ == "__main__":
    check_good_transactions() 