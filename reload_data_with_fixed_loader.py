#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'aml-backend'))

from aml_integration_system import AMLDatabaseManager, AMLJSONDataLoader

def reload_data():
    """Перезагружаем данные с исправленным загрузчиком"""
    
    # Удаляем старую базу данных
    db_path = "aml-backend/aml_system_e840b2937714940f.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️ Удалена старая база данных: {db_path}")
    
    # Создаем новую базу данных
    db_manager = AMLDatabaseManager(db_path)
    print("✅ Создана новая база данных")
    
    # Загружаем данные с исправленным загрузчиком
    loader = AMLJSONDataLoader(db_manager)
    success = loader.load_and_process_json("do_range.json")
    
    if success:
        # Проверяем результат
        cursor = db_manager.get_db_cursor()
        
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_tx = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE beneficiary_name IS NOT NULL AND beneficiary_name != ''")
        with_beneficiary = cursor.fetchone()[0]
        
        cursor.execute("SELECT transaction_id, sender_name, beneficiary_name, amount_kzt FROM transactions WHERE beneficiary_name IS NOT NULL AND beneficiary_name != '' LIMIT 5")
        examples = cursor.fetchall()
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ПЕРЕЗАГРУЗКИ:")
        print(f"├── Всего транзакций: {total_tx}")
        print(f"├── С получателями: {with_beneficiary}")
        print(f"└── Процент полных: {(with_beneficiary/total_tx*100):.1f}%")
        
        if examples:
            print("\n🔍 ПРИМЕРЫ ТРАНЗАКЦИЙ С ПОЛУЧАТЕЛЯМИ:")
            for ex in examples:
                print(f"  {ex[0]}: {ex[1]} → {ex[2]} ({ex[3]:,.0f} KZT)")
        
        return with_beneficiary > 0
    else:
        print("❌ Ошибка при загрузке данных")
        return False

if __name__ == "__main__":
    success = reload_data()
    if success:
        print("\n✅ Данные успешно перезагружены! Теперь сетевой анализ должен работать.")
    else:
        print("\n❌ Не удалось перезагрузить данные.") 