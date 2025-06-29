#!/usr/bin/env python3
"""
🚀 Быстрый запуск AML-анализа
Простой скрипт для автоматического анализа всех клиентов
"""

from aml_pipeline import AMLPipeline
import sys

def quick_analysis():
    """Быстрый анализ всех клиентов"""
    print("🚀 БЫСТРЫЙ AML-АНАЛИЗ")
    print("=" * 30)
    
    try:
        # Создаем пайплайн
        pipeline = AMLPipeline('aml_system.db')
        
        # Запускаем полный анализ
        result = pipeline.run_full_analysis()
        
        if result.get('success'):
            print()
            print("🎉 АНАЛИЗ ЗАВЕРШЕН УСПЕШНО!")
            stats = result['stats']
            print(f"⚡ {stats['total_clients']:,} клиентов за {stats['analysis_time']:.3f} сек")
            print(f"🔴 Найдено подозрительных: {stats['suspicious_clients']:,}")
            
            return True
        else:
            print(f"❌ Ошибка: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    success = quick_analysis()
    sys.exit(0 if success else 1) 