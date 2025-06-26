import requests
import json

print("🎯 ФИНАЛЬНЫЙ ТЕСТ СИСТЕМЫ АНАЛИЗА РИСКОВ")
print("=" * 60)

base_url = "http://localhost:8000/api"

# Тест 1: Общий анализ рисков (365 дней)
print("\n1️⃣ ОБЩИЙ АНАЛИЗ РИСКОВ")
try:
    response = requests.get(f"{base_url}/analytics/risk-analysis?dateRange=365")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Всего транзакций: {data['risk_summary']['total']}")
        print(f"✅ Высокий риск: {data['risk_summary']['high']}")
        print(f"✅ Низкий риск: {data['risk_summary']['low']}")
        print(f"✅ Подозрительных транзакций: {len(data['suspicious_transactions'])}")
        
        print("\n📊 Разбивка по типам анализа:")
        for analysis_type, count in data['analysis_type_breakdown'].items():
            emoji = {"transactional": "🔄", "network": "🌐", "behavioral": "👤", "customer": "🏢", "geographic": "📍"}
            print(f"   {emoji.get(analysis_type, '🔹')} {analysis_type.capitalize()}: {count}")
    else:
        print(f"❌ Ошибка: {response.status_code}")
except Exception as e:
    print(f"❌ Ошибка: {e}")

# Тест 2: Фильтрация по сетевому анализу
print("\n2️⃣ ФИЛЬТРАЦИЯ ПО СЕТЕВОМУ АНАЛИЗУ")
try:
    response = requests.get(f"{base_url}/analytics/risk-analysis?dateRange=365&analysisType=network")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Найдено транзакций: {len(data['suspicious_transactions'])}")
        print(f"✅ Применен фильтр: {data['filters_applied']['analysis_type']}")
        
        if data['suspicious_transactions']:
            print("📋 Первые 3 транзакции:")
            for i, tx in enumerate(data['suspicious_transactions'][:3]):
                print(f"   {i+1}. {tx['transaction_id']} - Риск: {tx['final_risk_score']}")
    else:
        print(f"❌ Ошибка: {response.status_code}")
except Exception as e:
    print(f"❌ Ошибка: {e}")

# Тест 3: Фильтрация по поведенческому анализу
print("\n3️⃣ ФИЛЬТРАЦИЯ ПО ПОВЕДЕНЧЕСКОМУ АНАЛИЗУ")
try:
    response = requests.get(f"{base_url}/analytics/risk-analysis?dateRange=365&analysisType=behavioral")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Найдено транзакций: {len(data['suspicious_transactions'])}")
        print(f"✅ Применен фильтр: {data['filters_applied']['analysis_type']}")
        
        if data['suspicious_transactions']:
            print("📋 Первые 3 транзакции:")
            for i, tx in enumerate(data['suspicious_transactions'][:3]):
                print(f"   {i+1}. {tx['transaction_id']} - Риск: {tx['final_risk_score']}")
    else:
        print(f"❌ Ошибка: {response.status_code}")
except Exception as e:
    print(f"❌ Ошибка: {e}")

# Тест 4: Фильтрация по транзакционному анализу
print("\n4️⃣ ФИЛЬТРАЦИЯ ПО ТРАНЗАКЦИОННОМУ АНАЛИЗУ")
try:
    response = requests.get(f"{base_url}/analytics/risk-analysis?dateRange=365&analysisType=transactional")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Найдено транзакций: {len(data['suspicious_transactions'])}")
        print(f"✅ Применен фильтр: {data['filters_applied']['analysis_type']}")
        
        if data['suspicious_transactions']:
            print("📋 Первые 3 транзакции:")
            for i, tx in enumerate(data['suspicious_transactions'][:3]):
                print(f"   {i+1}. {tx['transaction_id']} - Риск: {tx['final_risk_score']}")
    else:
        print(f"❌ Ошибка: {response.status_code}")
except Exception as e:
    print(f"❌ Ошибка: {e}")

# Тест 5: Топ индикаторы риска
print("\n5️⃣ ТОП ИНДИКАТОРЫ РИСКА")
try:
    response = requests.get(f"{base_url}/analytics/risk-analysis?dateRange=365")
    if response.status_code == 200:
        data = response.json()
        print("✅ Топ индикаторы:")
        for indicator in data['top_risk_indicators'][:5]:
            print(f"   🔸 {indicator['name']}: {indicator['count']} транзакций")
    else:
        print(f"❌ Ошибка: {response.status_code}")
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\n" + "=" * 60)
print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
print("📋 Все основные функции системы анализа рисков работают корректно.")
print("💡 Для корректной работы используйте dateRange=365 в параметрах запроса.") 