#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест сетевого анализа напрямую
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'aml-backend'))

from datetime import datetime
from aml_integration_system import AMLDatabaseManager
from network_profile_afm import NetworkProfile

def test_network_analysis():
    """Тестируем сетевой анализ с реальными данными"""
    
    # Подключаемся к базе данных
    db_manager = AMLDatabaseManager("aml-backend/aml_system_e840b2937714940f.db")
    
    # Создаем сетевой профиль
    network_profile = NetworkProfile(db_manager)
    
    # Получаем несколько транзакций из базы
    cursor = db_manager.get_db_cursor()
    cursor.execute("SELECT * FROM transactions LIMIT 10")
    transactions = cursor.fetchall()
    
    print(f"📊 Найдено {len(transactions)} транзакций для анализа")
    
    if not transactions:
        print("❌ Нет транзакций в базе данных")
        return
    
    # Берем первую транзакцию для анализа
    transaction = dict(transactions[0])
    print(f"🔍 Анализируем транзакцию: {transaction['transaction_id']}")
    print(f"   От: {transaction['sender_name']} ({transaction['sender_id']})")
    print(f"   Кому: {transaction['beneficiary_name']} ({transaction['beneficiary_id']})")
    print(f"   Сумма: {transaction['amount_kzt']:,.0f} KZT")
    
    # Получаем историю транзакций для участников
    sender_id = transaction['sender_id']
    beneficiary_id = transaction['beneficiary_id']
    
    cursor.execute("""
        SELECT * FROM transactions 
        WHERE sender_id IN (?, ?) OR beneficiary_id IN (?, ?)
        ORDER BY transaction_date DESC
        LIMIT 50
    """, (sender_id, beneficiary_id, sender_id, beneficiary_id))
    
    history = [dict(row) for row in cursor.fetchall()]
    print(f"📈 Найдено {len(history)} связанных транзакций")
    
    # Запускаем сетевой анализ
    result = network_profile.analyze_transaction_network(transaction, history)
    
    print("\n🕸️ РЕЗУЛЬТАТЫ СЕТЕВОГО АНАЛИЗА:")
    print(f"   Подозрительная: {'ДА' if result['is_suspicious'] else 'НЕТ'}")
    print(f"   Риск-скор: {result['risk_score']:.1f}/10")
    print(f"   Схемы найдены: {len(result.get('schemes_found', []))}")
    
    if result.get('suspicious_reasons'):
        print("   Причины подозрительности:")
        for reason in result['suspicious_reasons']:
            print(f"     • {reason}")
    
    if result.get('detected_schemes'):
        print(f"\n🎯 ДЕТАЛИ ОБНАРУЖЕННЫХ СХЕМ ({len(result['detected_schemes'])}):")
        for i, scheme in enumerate(result['detected_schemes'], 1):
            print(f"   {i}. {scheme['type']} (риск: {scheme['risk_score']:.1f})")
            print(f"      {scheme['description']}")
    
    # Статистика сети
    stats = result.get('network_stats', {})
    print(f"\n📊 СТАТИСТИКА СЕТИ:")
    print(f"   Участников: {stats.get('total_participants', 0)}")
    print(f"   Связей: {stats.get('total_connections', 0)}")
    print(f"   Общая сумма: {stats.get('total_amount', 0):,.0f} KZT")
    
    # Проверим, есть ли данные в таблицах
    cursor.execute("SELECT COUNT(*) FROM network_connections")
    connections_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM detected_schemes")
    schemes_count = cursor.fetchone()[0]
    
    print(f"\n🗄️ ДАННЫЕ В БАЗЕ:")
    print(f"   network_connections: {connections_count} записей")
    print(f"   detected_schemes: {schemes_count} записей")
    
    if connections_count == 0 and schemes_count == 0:
        print("❌ Сетевой анализ не сохраняет результаты в базу данных!")
        print("   Нужно добавить код для сохранения результатов.")
    
    return result

if __name__ == "__main__":
    test_network_analysis() 