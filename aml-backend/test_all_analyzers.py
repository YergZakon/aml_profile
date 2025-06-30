#!/usr/bin/env python3
"""
Тест активации всех анализаторов: клиентский, сетевой, поведенческий, географический
"""

import sys
import json
from datetime import datetime
from unified_aml_pipeline import UnifiedAMLPipeline
from aml_database_setup import AMLDatabaseManager

def test_all_analyzers():
    """Тестирует все типы анализа на небольшой выборке транзакций"""
    
    print("🚀 Тестирование всех анализаторов...")
    
    # Инициализация pipeline
    pipeline = UnifiedAMLPipeline()
    pipeline._initialize_database('aml_system_e840b2937714940f.db')
    
    # Получаем транзакции для анализа
    with AMLDatabaseManager('aml_system_e840b2937714940f.db') as db:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT transaction_id, amount, amount_kzt, sender_id, beneficiary_id, 
                   transaction_date, sender_country, beneficiary_country,
                   sender_name, beneficiary_name, purpose_text, 
                   final_risk_score, is_suspicious
            FROM transactions 
            ORDER BY transaction_date DESC
            LIMIT 100
        """)
        transactions = [dict(zip([desc[0] for desc in cursor.description], row)) 
                       for row in cursor.fetchall()]
    
    print(f"📊 Анализируем {len(transactions)} транзакций...")
    
    # Анализируем транзакции
    results = []
    analysis_counts = {
        'transaction': 0,
        'customer': 0, 
        'network': 0,
        'behavioral': 0,
        'geographic': 0,
        'total_high_risk': 0,
        'total_medium_risk': 0,
        'total_low_risk': 0
    }
    
    for i, tx in enumerate(transactions):
        result = pipeline._analyze_single_transaction(tx)
        results.append(result)
        
        # Подсчитываем активные анализы (риск > 0)
        if result.transaction_risk > 0:
            analysis_counts['transaction'] += 1
        if result.customer_risk > 0:
            analysis_counts['customer'] += 1
        if result.network_risk > 0:
            analysis_counts['network'] += 1
        if result.behavioral_risk > 0:
            analysis_counts['behavioral'] += 1
        if result.geographic_risk > 0:
            analysis_counts['geographic'] += 1
            
        # Подсчитываем категории риска
        if result.overall_risk >= 4.0:
            analysis_counts['total_high_risk'] += 1
        elif result.overall_risk >= 2.0:
            analysis_counts['total_medium_risk'] += 1
        else:
            analysis_counts['total_low_risk'] += 1
        
        if (i + 1) % 20 == 0:
            print(f"📈 Прогресс: {i + 1}/{len(transactions)}")
    
    # Генерируем отчет
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_analyzed': len(transactions),
        'analysis_activation': analysis_counts,
        'sample_results': [
            {
                'transaction_id': r.client_id,
                'transaction_risk': r.transaction_risk,
                'customer_risk': r.customer_risk,
                'network_risk': r.network_risk,
                'behavioral_risk': r.behavioral_risk,
                'geographic_risk': r.geographic_risk,
                'overall_risk': r.overall_risk,
                'risk_category': r.risk_category,
                'flags_count': len(r.suspicious_flags),
                'explanations_count': len(r.explanations)
            } for r in results[:10]  # Первые 10 для примера
        ]
    }
    
    # Сохраняем результат
    report_file = f"analyzer_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ АНАЛИЗАТОРОВ:")
    print("=" * 50)
    print(f"📈 Всего проанализировано: {report['total_analyzed']}")
    print("\n🔍 Активация анализаторов:")
    for analyzer, count in analysis_counts.items():
        if analyzer.startswith('total_'):
            continue
        percentage = (count / len(transactions)) * 100
        print(f"  {analyzer.capitalize()}: {count}/{len(transactions)} ({percentage:.1f}%)")
    
    print(f"\n🎯 Распределение рисков:")
    print(f"  Высокий (≥4.0): {analysis_counts['total_high_risk']}")
    print(f"  Средний (2.0-4.0): {analysis_counts['total_medium_risk']}")
    print(f"  Низкий (<2.0): {analysis_counts['total_low_risk']}")
    
    print(f"\n💾 Отчет сохранен: {report_file}")
    
    return report

if __name__ == "__main__":
    test_all_analyzers()