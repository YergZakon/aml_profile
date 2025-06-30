#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Комплексный тест сетевого анализа с большим набором данных
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'aml-backend'))

from datetime import datetime
from aml_integration_system import AMLDatabaseManager
from network_profile_afm import NetworkProfile

def test_comprehensive_network_analysis():
    """Комплексное тестирование сетевого анализа"""
    
    # Подключаемся к базе данных
    db_manager = AMLDatabaseManager("aml-backend/aml_system_e840b2937714940f.db")
    
    # Получаем все транзакции с полными данными
    cursor = db_manager.get_db_cursor()
    cursor.execute("""
        SELECT * FROM transactions 
        WHERE beneficiary_name IS NOT NULL 
        AND beneficiary_name != '' 
        AND sender_name IS NOT NULL 
        AND sender_name != ''
        AND amount_kzt > 0
        ORDER BY amount_kzt DESC
    """)
    
    all_transactions = [dict(row) for row in cursor.fetchall()]
    print(f"📊 Найдено {len(all_transactions)} транзакций с полными данными и суммой > 0")
    
    if len(all_transactions) < 10:
        print("❌ Недостаточно данных для комплексного анализа")
        return
    
    # Создаем один большой сетевой профиль со всеми транзакциями
    network_profile = NetworkProfile(db_manager)
    
    print("🔄 Добавляем все транзакции в сеть...")
    
    # Добавляем все транзакции в сеть
    for tx in all_transactions:
        try:
            network_profile.add_transaction(
                sender=tx['sender_id'],
                beneficiary=tx['beneficiary_id'],
                amount=tx['amount_kzt'],
                date=datetime.fromisoformat(tx['transaction_date']) if tx['transaction_date'] else datetime.now(),
                transaction_id=tx['transaction_id'],
                sender_type='individual' if len(tx['sender_id']) == 12 and tx['sender_id'].isdigit() else 'company',
                beneficiary_type='individual' if len(tx['beneficiary_id']) == 12 and tx['beneficiary_id'].isdigit() else 'company'
            )
        except Exception as e:
            print(f"⚠️ Ошибка добавления транзакции {tx['transaction_id']}: {e}")
    
    # Обновляем статистику
    network_profile._update_stats()
    
    print(f"📈 Построена сеть:")
    print(f"   Участников: {network_profile.network_stats['total_participants']}")
    print(f"   Связей: {network_profile.network_stats['total_connections']}")
    print(f"   Общая сумма: {network_profile.network_stats['total_amount']:,.0f} KZT")
    print(f"   Средняя транзакция: {network_profile.network_stats['avg_transaction']:,.0f} KZT")
    
    # Запускаем обнаружение схем
    print("\n🕵️ Ищем схемы отмывания денег...")
    schemes = network_profile.detect_money_laundering_schemes()
    
    print(f"\n🎯 ОБНАРУЖЕНО СХЕМ: {len(schemes)}")
    
    if schemes:
        scheme_types = {}
        for scheme in schemes:
            scheme_type = scheme['type']
            if scheme_type not in scheme_types:
                scheme_types[scheme_type] = []
            scheme_types[scheme_type].append(scheme)
        
        for scheme_type, type_schemes in scheme_types.items():
            print(f"\n📋 {scheme_type}: {len(type_schemes)} схем")
            for i, scheme in enumerate(type_schemes[:3], 1):  # Показываем первые 3
                print(f"   {i}. Риск: {scheme['risk_score']:.1f}/10")
                print(f"      {scheme['description']}")
                
                # Детали схемы
                if scheme_type == 'CIRCULAR_SCHEME':
                    print(f"      Участники: {' → '.join(scheme['participants'])}")
                elif scheme_type == 'STAR_SCHEME':
                    print(f"      Центр: {scheme['center']}")
                    print(f"      Связанных: {len(scheme['satellites'])}")
                elif scheme_type == 'SMURFING':
                    print(f"      Источник: {scheme['source']}")
                    print(f"      Получателей: {len(scheme['destinations'])}")
    else:
        print("   Схемы не обнаружены")
    
    # Анализируем топ участников по активности
    print(f"\n👥 ТОП УЧАСТНИКОВ ПО АКТИВНОСТИ:")
    
    # Подсчитываем активность участников
    participant_activity = {}
    for sender, beneficiaries in network_profile.connections.items():
        if sender not in participant_activity:
            participant_activity[sender] = {'outgoing': 0, 'incoming': 0}
        participant_activity[sender]['outgoing'] += len(beneficiaries)
        
        for beneficiary in beneficiaries:
            if beneficiary not in participant_activity:
                participant_activity[beneficiary] = {'outgoing': 0, 'incoming': 0}
            participant_activity[beneficiary]['incoming'] += 1
    
    # Сортируем по общей активности
    sorted_participants = sorted(
        participant_activity.items(),
        key=lambda x: x[1]['outgoing'] + x[1]['incoming'],
        reverse=True
    )
    
    for i, (participant, activity) in enumerate(sorted_participants[:10], 1):
        total_activity = activity['outgoing'] + activity['incoming']
        risk_score = network_profile.get_participant_risk_score(participant)
        
        # Получаем имя участника
        cursor.execute("""
            SELECT sender_name FROM transactions 
            WHERE sender_id = ? AND sender_name IS NOT NULL 
            LIMIT 1
        """, (participant,))
        name_result = cursor.fetchone()
        if not name_result:
            cursor.execute("""
                SELECT beneficiary_name FROM transactions 
                WHERE beneficiary_id = ? AND beneficiary_name IS NOT NULL 
                LIMIT 1
            """, (participant,))
            name_result = cursor.fetchone()
        
        name = name_result[0] if name_result else "Неизвестно"
        
        print(f"   {i}. {name[:50]}...")
        print(f"      ID: {participant}")
        print(f"      Активность: {total_activity} (исх: {activity['outgoing']}, вх: {activity['incoming']})")
        print(f"      Риск: {risk_score:.1f}/10")
    
    # Проверяем, есть ли циклы в сети
    print(f"\n🔄 АНАЛИЗ ЦИКЛОВ:")
    if hasattr(network_profile, 'graph') and network_profile.graph.nodes():
        try:
            import networkx as nx
            cycles = list(nx.simple_cycles(network_profile.graph))
            print(f"   Найдено циклов: {len(cycles)}")
            
            if cycles:
                for i, cycle in enumerate(cycles[:5], 1):  # Показываем первые 5
                    print(f"   Цикл {i}: {' → '.join(cycle)} → {cycle[0]}")
        except Exception as e:
            print(f"   Ошибка анализа циклов: {e}")
    
    return network_profile, schemes

if __name__ == "__main__":
    network_profile, schemes = test_comprehensive_network_analysis()
    
    print(f"\n✅ ИТОГИ КОМПЛЕКСНОГО АНАЛИЗА:")
    print(f"   Участников в сети: {network_profile.network_stats['total_participants']}")
    print(f"   Связей: {network_profile.network_stats['total_connections']}")
    print(f"   Обнаружено схем: {len(schemes)}")
    print(f"   Общий объем: {network_profile.network_stats['total_amount']:,.0f} KZT") 