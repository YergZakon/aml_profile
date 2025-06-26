import json

# Читаем результаты анализа
with open('analysis_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== РЕЗУЛЬТАТЫ АНАЛИЗА С УЛУЧШЕННЫМ ПРОФИЛЕМ ===")
print(f"Всего транзакций: {data['summary']['total_transactions']}")
print(f"Подозрительных: {data['summary']['suspicious_transactions']}")
print(f"Процент подозрительных: {data['summary']['suspicious_percentage']:.1f}%")

# Проверяем наличие новых полей
if data['suspicious_transactions']:
    print("\n=== ПРИМЕРЫ ПОДОЗРИТЕЛЬНЫХ ТРАНЗАКЦИЙ ===")
    
    # Счетчики для новых индикаторов
    round_amount_count = 0
    unusual_time_count = 0
    structuring_count = 0
    
    for i, trans in enumerate(data['suspicious_transactions'][:5]):
        print(f"\n{i+1}. ID: {trans['transaction_id']}")
        print(f"   Сумма: {trans['amount']:,.0f} {trans['currency']}")
        print(f"   Риск-скор: {trans['final_risk_score']:.2f}/10")
        
        # Проверяем наличие новых причин
        reasons = trans.get('suspicious_reasons', [])
        if reasons:
            print("   Причины:")
            for reason in reasons[:5]:
                print(f"     - {reason}")
                
                # Считаем новые индикаторы
                if 'Круглая сумма' in reason:
                    round_amount_count += 1
                if 'Ночная операция' in reason or 'вечерняя операция' in reason:
                    unusual_time_count += 1
                if 'структурирование' in reason:
                    structuring_count += 1
    
    # Общая статистика по всем подозрительным
    total_new_indicators = 0
    for trans in data['suspicious_transactions']:
        reasons_str = ' '.join(trans.get('suspicious_reasons', []))
        if any(x in reasons_str for x in ['Круглая сумма', 'Ночная операция', 'структурирование']):
            total_new_indicators += 1
    
    print(f"\n=== СТАТИСТИКА НОВЫХ ИНДИКАТОРОВ ===")
    print(f"Транзакций с новыми индикаторами риска: {total_new_indicators}")
    print(f"- С круглыми суммами: минимум {round_amount_count}")
    print(f"- С необычным временем: минимум {unusual_time_count}")
    print(f"- Со структурированием: минимум {structuring_count}")
else:
    print("\nНет подозрительных транзакций") 