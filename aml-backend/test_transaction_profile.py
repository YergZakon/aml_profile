#!/usr/bin/env python3
"""
Тестирование улучшенного транзакционного профиля
"""

from datetime import datetime, timedelta
from transaction_profile_afm import TransactionProfile
import json

def test_round_amounts():
    """Тестирование проверки круглых сумм"""
    print("\n=== ТЕСТ: Проверка круглых сумм ===")
    
    profile = TransactionProfile()
    test_amounts = [
        1_000_000,    # Ровно миллион
        999_000,      # Почти миллион (структурирование)
        1_001_000,    # Чуть больше миллиона
        555_555,      # Повторяющиеся цифры
        1_999_000,    # Чуть ниже порога 2М
        1_234_567,    # Обычная сумма
        50_000,       # Круглая сумма 50к
        49_999,       # Не круглая
    ]
    
    for amount in test_amounts:
        is_round, round_type = profile.is_round_amount(amount)
        print(f"Сумма {amount:,} KZT: {'КРУГЛАЯ' if is_round else 'обычная'} - {round_type or 'N/A'}")

def test_time_analysis():
    """Тестирование анализа времени операций"""
    print("\n=== ТЕСТ: Анализ времени операций ===")
    
    profile = TransactionProfile()
    test_times = [
        datetime(2025, 1, 15, 3, 30),   # Ночь среда
        datetime(2025, 1, 15, 10, 0),   # Утро среда
        datetime(2025, 1, 15, 23, 30),  # Поздний вечер среда
        datetime(2025, 1, 18, 14, 0),   # День суббота
        datetime(2025, 1, 1, 15, 0),    # Новый год
        datetime(2025, 3, 8, 10, 0),    # 8 марта
    ]
    
    for dt in test_times:
        is_unusual, reason = profile.is_unusual_time(dt)
        risk_level = profile.risk_indicators.get('time_risk_level', 'N/A')
        print(f"{dt.strftime('%Y-%m-%d %H:%M %A')}: {'НЕОБЫЧНОЕ' if is_unusual else 'обычное'} - {reason} (Риск: {risk_level})")

def test_full_analysis():
    """Тестирование полного анализа транзакций"""
    print("\n=== ТЕСТ: Полный анализ транзакций ===")
    
    profile = TransactionProfile()
    
    # Тестовые транзакции
    test_transactions = [
        {
            'transaction_id': 'TEST_001',
            'amount': 2_000_000,
            'currency': 'KZT',
            'date': datetime(2025, 1, 15, 3, 30),  # Ночная операция
            'channel': 'cash',
            'sender_id': 'CLIENT_001',
            'sender_country': 'KZ',
            'beneficiary_id': 'OFFSHORE_001',
            'beneficiary_country': 'KY',  # Каймановы острова
            'purpose_text': 'Благотворительность'
        },
        {
            'transaction_id': 'TEST_002',
            'amount': 999_000,
            'currency': 'KZT',
            'date': datetime(2025, 1, 15, 14, 0),
            'channel': 'transfer',
            'sender_id': 'CLIENT_002',
            'sender_country': 'KZ',
            'beneficiary_id': 'CLIENT_003',
            'beneficiary_country': 'KZ',
            'purpose_text': 'Оплата за товар по договору №12345'
        },
        {
            'transaction_id': 'TEST_003',
            'amount': 8_500_000,
            'currency': 'KZT',
            'date': datetime(2025, 1, 18, 23, 45),  # Поздний вечер суббота
            'channel': 'instant',
            'sender_id': 'CLIENT_004',
            'sender_country': 'KZ',
            'beneficiary_id': 'CLIENT_005',
            'beneficiary_country': 'IR',  # Иран
            'purpose_text': 'Консультационные услуги'
        }
    ]
    
    for tx in test_transactions:
        result = profile.analyze_transaction(tx)
        
        print(f"\n--- Транзакция {result['transaction_id']} ---")
        print(f"Сумма: {tx['amount']:,} {tx['currency']}")
        print(f"Маршрут: {tx['sender_country']} -> {tx['beneficiary_country']}")
        print(f"Время: {tx['date'].strftime('%Y-%m-%d %H:%M')}")
        print(f"Риск-скор: {result['risk_score']:.2f}/10")
        print(f"Подозрительная: {'ДА' if result['is_suspicious'] else 'НЕТ'}")
        print(f"Рекомендация: {result['recommendation']}")
        print(f"Уверенность: {result['confidence_level']:.0%}")
        
        print("\nКомпоненты риска:")
        for component, value in result['risk_components'].items():
            print(f"  - {component}: {value:.1f}")
        
        print("\nПричины:")
        for reason in result['reasons']:
            print(f"  - {reason}")
        
        print("\nИндикаторы риска:")
        for indicator, value in result['risk_indicators'].items():
            print(f"  - {indicator}: {value}")
        
        if result['detailed_analysis']['behavioral_flags']:
            print("\nПоведенческие флаги:")
            for flag in result['detailed_analysis']['behavioral_flags']:
                print(f"  - {flag}")

def test_structuring_detection():
    """Тестирование обнаружения структурирования"""
    print("\n=== ТЕСТ: Обнаружение структурирования ===")
    
    profile = TransactionProfile()
    
    # Создаем историю транзакций для анализа структурирования
    base_time = datetime(2025, 1, 15, 10, 0)
    transaction_history = []
    
    # Добавляем несколько транзакций в течение часа
    for i in range(3):
        transaction_history.append({
            'transaction_id': f'HIST_{i}',
            'amount': 700_000,
            'date': base_time + timedelta(minutes=i*20),
            'sender_id': 'CLIENT_001'
        })
    
    # Тестовая транзакция
    current_transaction = {
        'transaction_id': 'CURRENT_001',
        'amount': 700_000,
        'currency': 'KZT',
        'date': base_time + timedelta(minutes=45),
        'channel': 'transfer',
        'sender_id': 'CLIENT_001',
        'sender_country': 'KZ',
        'beneficiary_id': 'CLIENT_002',
        'beneficiary_country': 'KZ',
        'purpose_text': 'Перевод'
    }
    
    result = profile.analyze_transaction(current_transaction, transaction_history)
    
    print(f"Транзакция: {result['transaction_id']}")
    print(f"Обнаружено структурирование: {'ДА' if 'is_structuring' in result['risk_indicators'] and result['risk_indicators']['is_structuring'] else 'НЕТ'}")
    print(f"Риск-скор: {result['risk_score']:.2f}")
    print(f"Поведенческие флаги: {result['detailed_analysis']['behavioral_flags']}")

def main():
    """Запуск всех тестов"""
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ УЛУЧШЕННОГО ТРАНЗАКЦИОННОГО ПРОФИЛЯ")
    print("=" * 60)
    
    test_round_amounts()
    test_time_analysis()
    test_full_analysis()
    test_structuring_detection()
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)

if __name__ == "__main__":
    main() 