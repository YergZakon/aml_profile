#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'aml-backend'))

from aml_integration_system import AMLDatabaseManager

def check_db_data():
    db = AMLDatabaseManager('aml-backend/aml_system_e840b2937714940f.db')
    cursor = db.get_db_cursor()
    
    cursor.execute('SELECT COUNT(*) FROM transactions')
    total = cursor.fetchone()[0]
    print(f'Всего транзакций: {total}')

    cursor.execute('SELECT COUNT(*) FROM transactions WHERE beneficiary_name IS NULL OR beneficiary_name = ""')
    empty_ben = cursor.fetchone()[0]
    print(f'С пустым получателем: {empty_ben}')

    cursor.execute('SELECT COUNT(*) FROM transactions WHERE amount_kzt = 0 OR amount_kzt IS NULL')
    zero_amount = cursor.fetchone()[0]
    print(f'С нулевой суммой: {zero_amount}')

    cursor.execute('SELECT transaction_id, sender_name, beneficiary_name, amount_kzt FROM transactions LIMIT 5')
    print('\nПример транзакций:')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]} -> {row[2]}, {row[3]} KZT')

if __name__ == "__main__":
    check_db_data() 