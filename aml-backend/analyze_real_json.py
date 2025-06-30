#!/usr/bin/env python3
"""
Анализ реальной структуры JSON файлов АФМ РК
"""

import json
import sys

def analyze_real_json(file_path):
    """Анализирует реальную структуру JSON файла АФМ"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📁 Файл: {file_path}")
        print(f"📦 Количество записей: {len(data):,}")
        
        if len(data) > 0:
            # Берем первую запись для анализа
            first_record = data[0]
            tx_data = first_record.get('row_to_json', {})
            
            print(f"\n🔍 СТРУКТУРА ЗАПИСИ:")
            print(f"   Основной ключ: 'row_to_json'")
            print(f"   Полей в транзакции: {len(tx_data)}")
            
            print(f"\n💰 КЛЮЧЕВЫЕ ПОЛЯ ТРАНЗАКЦИИ:")
            print(f"   ID сообщения: {tx_data.get('gmess_id')}")
            print(f"   Номер операции: {tx_data.get('goper_number')}")
            print(f"   Дата транзакции: {tx_data.get('goper_trans_date')}")
            print(f"   Сумма в тенге: {tx_data.get('goper_tenge_amount'):,}")
            print(f"   Валютная сумма: {tx_data.get('goper_currency_amount'):,}")
            print(f"   Статус операции: {tx_data.get('gmess_oper_status')}")
            print(f"   Код причины: {tx_data.get('gmess_reason_code')}")
            
            print(f"\n🚨 ПОЛЯ ПОДОЗРИТЕЛЬНОСТИ:")
            print(f"   Первый признак: {tx_data.get('goper_susp_first')}")
            print(f"   Второй признак: {tx_data.get('goper_susp_second')}")
            print(f"   Третий признак: {tx_data.get('goper_susp_third')}")
            
            print(f"\n👤 УЧАСТНИКИ ТРАНЗАКЦИИ:")
            
            # Участник 1
            member1_id = tx_data.get('gmember1_maincode')
            member1_type = tx_data.get('gmember1_member_type')
            if member1_id:
                if tx_data.get('gmember1_ur_name'):
                    member1_name = tx_data.get('gmember1_ur_name')
                    entity_type = "Юридическое лицо"
                else:
                    parts = []
                    if tx_data.get('gmember1_ac_secondname'): parts.append(tx_data.get('gmember1_ac_secondname'))
                    if tx_data.get('gmember1_ac_firstname'): parts.append(tx_data.get('gmember1_ac_firstname'))
                    if tx_data.get('gmember1_ac_middlename'): parts.append(tx_data.get('gmember1_ac_middlename'))
                    member1_name = ' '.join(parts)
                    entity_type = "Физическое лицо"
                
                print(f"   Участник 1:")
                print(f"     ID: {member1_id}")
                print(f"     Имя: {member1_name}")
                print(f"     Тип: {entity_type} ({member1_type})")
            
            # Участник 2
            member2_id = tx_data.get('gmember2_maincode')
            member2_type = tx_data.get('gmember2_member_type')
            if member2_id:
                if tx_data.get('gmember2_ur_name'):
                    member2_name = tx_data.get('gmember2_ur_name')
                    entity_type = "Юридическое лицо"
                else:
                    parts = []
                    if tx_data.get('gmember2_ac_secondname'): parts.append(tx_data.get('gmember2_ac_secondname'))
                    if tx_data.get('gmember2_ac_firstname'): parts.append(tx_data.get('gmember2_ac_firstname'))
                    if tx_data.get('gmember2_ac_middlename'): parts.append(tx_data.get('gmember2_ac_middlename'))
                    member2_name = ' '.join(parts)
                    entity_type = "Физическое лицо"
                
                print(f"   Участник 2:")
                print(f"     ID: {member2_id}")
                print(f"     Имя: {member2_name}")
                print(f"     Тип: {entity_type} ({member2_type})")
            
            print(f"\n📋 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:")
            dopinfo = tx_data.get('goper_dopinfo')
            if dopinfo:
                print(f"   Описание операции: {dopinfo[:200]}{'...' if len(dopinfo) > 200 else ''}")
            
            difficulties = tx_data.get('goper_difficulties')
            if difficulties:
                print(f"   Сложности/Подозрения: {difficulties[:200]}{'...' if len(difficulties) > 200 else ''}")
            
            print(f"\n🎯 СПИСОК ПРОВЕРОК (GIS):")
            gis_fields = [k for k in tx_data.keys() if k.startswith('gis_')]
            active_checks = []
            for field in gis_fields:
                if tx_data.get(field) == 1:
                    active_checks.append(field)
            
            if active_checks:
                print(f"   Активные проверки: {len(active_checks)}")
                for check in active_checks[:5]:  # Показываем первые 5
                    print(f"     • {check}")
                if len(active_checks) > 5:
                    print(f"     ... и еще {len(active_checks) - 5}")
            else:
                print(f"   Активных проверок нет")
            
            # Статистика по файлу
            print(f"\n📊 СТАТИСТИКА ПО ФАЙЛУ:")
            suspicious_count = 0
            total_amount = 0
            unique_members = set()
            
            for record in data[:1000]:  # Анализируем первые 1000 записей для скорости
                tx = record.get('row_to_json', {})
                if tx.get('goper_susp_first'):
                    suspicious_count += 1
                
                amount = tx.get('goper_tenge_amount', 0)
                if amount:
                    total_amount += amount
                
                if tx.get('gmember1_maincode'):
                    unique_members.add(tx.get('gmember1_maincode'))
                if tx.get('gmember2_maincode'):
                    unique_members.add(tx.get('gmember2_maincode'))
            
            sample_size = min(1000, len(data))
            print(f"   Образец: {sample_size:,} записей из {len(data):,}")
            print(f"   Подозрительных операций: {suspicious_count} ({suspicious_count/sample_size*100:.1f}%)")
            print(f"   Общая сумма (образец): {total_amount:,} тенге")
            print(f"   Уникальных участников: {len(unique_members):,}")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        analyze_real_json(file_path)
    else:
        # Анализируем реальные файлы
        files_to_analyze = [
            "uploads/do_range.json",
            "uploads/converted_data3.json"
        ]
        
        for file_path in files_to_analyze:
            print("="*80)
            analyze_real_json(file_path)
            print() 