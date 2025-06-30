#!/usr/bin/env python3
"""
Реальные тесты всех AML профилей
Проверяет фактическую работу каждого компонента
"""

import sys
import os
import traceback
from datetime import datetime, timedelta

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем все профили
try:
    from transaction_profile_afm import TransactionProfile
    print("✅ TransactionProfile импортирован")
except Exception as e:
    print(f"❌ Ошибка импорта TransactionProfile: {e}")

try:
    from customer_profile_afm import CustomerProfile
    print("✅ CustomerProfile импортирован")
except Exception as e:
    print(f"❌ Ошибка импорта CustomerProfile: {e}")

try:
    from network_profile_afm import NetworkProfile
    print("✅ NetworkProfile импортирован")
except Exception as e:
    print(f"❌ Ошибка импорта NetworkProfile: {e}")

try:
    from behavioral_profile_afm import BehavioralProfile
    print("✅ BehavioralProfile импортирован")
except Exception as e:
    print(f"❌ Ошибка импорта BehavioralProfile: {e}")

try:
    from geographic_profile_afm import GeographicProfile
    print("✅ GeographicProfile импортирован")
except Exception as e:
    print(f"❌ Ошибка импорта GeographicProfile: {e}")

print("\n" + "="*60)
print("🧪 ТЕСТИРОВАНИЕ ВСЕХ AML ПРОФИЛЕЙ")
print("="*60)

# Тестовая транзакция
test_transaction = {
    'transaction_id': 'TEST_001',
    'amount': 1500000.0,  # 1.5M тенге
    'amount_kzt': 1500000.0,
    'currency': 'KZT',
    'transaction_date': '2024-12-01 14:30:00',
    'date': datetime(2024, 12, 1, 14, 30, 0),  # Для BehavioralProfile
    'sender_id': '123456789012',
    'sender_name': 'Тест Отправитель',
    'beneficiary_id': '987654321098',
    'beneficiary_name': 'Тест Получатель',
    'purpose_text': 'Оплата за товар',
    'is_suspicious': False,
    'final_risk_score': 1.0
}

def test_transaction_profile():
    """Тест транзакционного профиля"""
    print("\n🔍 ТЕСТ 1: TransactionProfile")
    print("-" * 40)
    
    try:
        profile = TransactionProfile()
        
        # Проверяем основные методы
        methods_to_test = [
            'analyze_transaction',
            'is_round_amount', 
            'is_unusual_time',
            'calculate_final_score',
            'analyze_transaction_patterns'
        ]
        
        for method_name in methods_to_test:
            if hasattr(profile, method_name):
                print(f"  ✅ Метод {method_name} существует")
            else:
                print(f"  ❌ Метод {method_name} отсутствует")
        
        # Тест анализа транзакции
        print("\n  🧪 Тестируем analyze_transaction:")
        try:
            result = profile.analyze_transaction(test_transaction)
            print(f"  ✅ Результат: risk_score = {result.get('risk_score', 'N/A')}")
            print(f"  ✅ Suspicious flags: {len(result.get('suspicious_flags', []))}")
            return True
        except Exception as e:
            print(f"  ❌ Ошибка analyze_transaction: {e}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Критическая ошибка в TransactionProfile: {e}")
        return False

def test_customer_profile():
    """Тест клиентского профиля"""
    print("\n👤 ТЕСТ 2: CustomerProfile")
    print("-" * 40)
    
    try:
        profile = CustomerProfile()
        
        # Проверяем методы
        methods_to_test = [
            'analyze_customer',
            'analyze_customer_data', 
            'calculate_risk_score',
            'detect_anomalies'
        ]
        
        for method_name in methods_to_test:
            if hasattr(profile, method_name):
                print(f"  ✅ Метод {method_name} существует")
            else:
                print(f"  ❌ Метод {method_name} отсутствует")
        
        # Тест анализа клиента
        if hasattr(profile, 'analyze_customer'):
            print("\n  🧪 Тестируем analyze_customer:")
            try:
                result = profile.analyze_customer('123456789012')
                print(f"  ✅ Результат: {result}")
                return True
            except Exception as e:
                print(f"  ❌ Ошибка analyze_customer: {e}")
        
        # Альтернативный тест
        if hasattr(profile, 'analyze_customer_data'):
            print("\n  🧪 Тестируем analyze_customer_data:")
            try:
                result = profile.analyze_customer_data(test_transaction)
                print(f"  ✅ Результат: {result}")
                return True
            except Exception as e:
                print(f"  ❌ Ошибка analyze_customer_data: {e}")
                
        return False
            
    except Exception as e:
        print(f"❌ Критическая ошибка в CustomerProfile: {e}")
        return False

def test_network_profile():
    """Тест сетевого профиля"""
    print("\n🕸️ ТЕСТ 3: NetworkProfile")
    print("-" * 40)
    
    try:
        profile = NetworkProfile()
        
        # Проверяем методы
        methods_to_test = [
            'analyze_network_patterns',
            'detect_circular_schemes',
            'detect_star_schemes', 
            'detect_smurfing',
            'build_graph'
        ]
        
        for method_name in methods_to_test:
            if hasattr(profile, method_name):
                print(f"  ✅ Метод {method_name} существует")
            else:
                print(f"  ❌ Метод {method_name} отсутствует")
        
        # Тест анализа сети
        if hasattr(profile, 'analyze_network_patterns'):
            print("\n  🧪 Тестируем analyze_network_patterns:")
            try:
                result = profile.analyze_network_patterns(test_transaction)
                print(f"  ✅ Результат: {result}")
                return True
            except Exception as e:
                print(f"  ❌ Ошибка analyze_network_patterns: {e}")
                traceback.print_exc()
                
        return False
            
    except Exception as e:
        print(f"❌ Критическая ошибка в NetworkProfile: {e}")
        return False

def test_behavioral_profile():
    """Тест поведенческого профиля"""
    print("\n🎭 ТЕСТ 4: BehavioralProfile")
    print("-" * 40)
    
    try:
        # BehavioralProfile требует customer_id
        profile = BehavioralProfile('123456789012')
        
        # Проверяем методы
        methods_to_test = [
            'analyze_behavior',
            'detect_anomalies',
            'build_baseline_profile',
            'update_transaction_history'
        ]
        
        for method_name in methods_to_test:
            if hasattr(profile, method_name):
                print(f"  ✅ Метод {method_name} существует")
            else:
                print(f"  ❌ Метод {method_name} отсутствует")
        
        # Тест анализа поведения
        if hasattr(profile, 'analyze_behavior'):
            print("\n  🧪 Тестируем analyze_behavior:")
            try:
                result = profile.analyze_behavior('123456789012', test_transaction)
                print(f"  ✅ Результат: {result}")
                return True
            except Exception as e:
                print(f"  ❌ Ошибка analyze_behavior: {e}")
                traceback.print_exc()
                
        return False
            
    except Exception as e:
        print(f"❌ Критическая ошибка в BehavioralProfile: {e}")
        return False

def test_geographic_profile():
    """Тест географического профиля"""
    print("\n🌍 ТЕСТ 5: GeographicProfile")
    print("-" * 40)
    
    try:
        # GeographicProfile может требовать db_manager
        profile = GeographicProfile(None)  # Пробуем с None
        
        # Проверяем методы
        methods_to_test = [
            'analyze_geography',
            'analyze_transaction_geography',
            'get_country_risk',
            'get_country_profile'
        ]
        
        for method_name in methods_to_test:
            if hasattr(profile, method_name):
                print(f"  ✅ Метод {method_name} существует")
            else:
                print(f"  ❌ Метод {method_name} отсутствует")
        
        # Тест анализа географии
        if hasattr(profile, 'analyze_geography'):
            print("\n  🧪 Тестируем analyze_geography:")
            try:
                result = profile.analyze_geography(test_transaction)
                print(f"  ✅ Результат: {result}")
                return True
            except Exception as e:
                print(f"  ❌ Ошибка analyze_geography: {e}")
        
        # Альтернативный тест
        if hasattr(profile, 'analyze_transaction_geography'):
            print("\n  🧪 Тестируем analyze_transaction_geography:")
            try:
                result = profile.analyze_transaction_geography(test_transaction)
                print(f"  ✅ Результат: {result}")
                return True
            except Exception as e:
                print(f"  ❌ Ошибка analyze_transaction_geography: {e}")
                
        return False
            
    except Exception as e:
        print(f"❌ Критическая ошибка в GeographicProfile: {e}")
        traceback.print_exc()
        return False

def test_unified_pipeline_integration():
    """Тест интеграции с unified pipeline"""
    print("\n🔗 ТЕСТ 6: Интеграция с Unified Pipeline")
    print("-" * 40)
    
    try:
        from unified_aml_pipeline import UnifiedAMLPipeline
        
        # Проверяем инициализацию анализаторов
        pipeline = UnifiedAMLPipeline()
        
        print("  🧪 Проверяем инициализацию анализаторов:")
        for analyzer_name, analyzer in pipeline.analyzers.items():
            if analyzer:
                print(f"  ✅ {analyzer_name}: {type(analyzer).__name__}")
            else:
                print(f"  ❌ {analyzer_name}: None")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в Unified Pipeline: {e}")
        traceback.print_exc()
        return False

def main():
    """Запуск всех тестов"""
    results = []
    
    # Запускаем все тесты
    results.append(("TransactionProfile", test_transaction_profile()))
    results.append(("CustomerProfile", test_customer_profile()))
    results.append(("NetworkProfile", test_network_profile()))
    results.append(("BehavioralProfile", test_behavioral_profile()))
    results.append(("GeographicProfile", test_geographic_profile()))
    results.append(("Unified Pipeline", test_unified_pipeline_integration()))
    
    # Итоговый отчет
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        if result:
            print(f"✅ {test_name}: ПРОЙДЕН")
            passed += 1
        else:
            print(f"❌ {test_name}: ПРОВАЛЕН")
    
    print(f"\n🎯 Результат: {passed}/{total} тестов пройдено ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ - ТРЕБУЕТСЯ ДОРАБОТКА")

if __name__ == "__main__":
    main()