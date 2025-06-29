import time
import psutil
from simple_performance_test import analyze_single_client_simple, get_client_list
from analyze_suspicious_clients_parallel import analyze_batch_parallel

def test_sequential_performance(client_ids, db_path='aml_system.db'):
    """Тестирование последовательной версии"""
    print("🐌 Тестирование ПОСЛЕДОВАТЕЛЬНОЙ версии:")
    print("-" * 50)
    
    start_time = time.time()
    results = []
    
    for i, client_id in enumerate(client_ids, 1):
        if i % 50 == 0 or i <= 10:
            print(f"  📋 Обрабатываем клиента {i}/{len(client_ids)}...")
        
        result = analyze_single_client_simple(client_id, db_path)
        if result:
            results.append(result)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    return {
        'results': results,
        'total_time': total_time,
        'clients_per_second': len(results) / total_time,
        'success_rate': len(results) / len(client_ids) * 100
    }

def test_parallel_performance(client_ids, db_path='aml_system.db', max_workers=20):
    """Тестирование параллельной версии"""
    print("🚀 Тестирование ПАРАЛЛЕЛЬНОЙ версии:")
    print("-" * 50)
    
    results, stats = analyze_batch_parallel(
        client_ids=client_ids,
        max_workers=max_workers,
        db_path=db_path,
        show_progress=True
    )
    
    return {
        'results': results,
        'total_time': stats['total_time'],
        'clients_per_second': stats['clients_per_second'],
        'success_rate': stats['success_rate']
    }

def compare_performance():
    """Сравнение производительности двух версий"""
    print("⚡ СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ AML-АНАЛИЗА")
    print("=" * 60)
    
    # Информация о системе
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    print(f"💻 Система:")
    print(f"   CPU: Intel Core Ultra 9 275HX ({cpu_count} ядер)")
    print(f"   RAM: {memory_gb:.1f} GB")
    print()
    
    # Получаем список клиентов для тестирования
    db_path = 'aml_system.db'
    test_sizes = [100, 500, 1000]  # Разные размеры для тестирования
    
    all_client_ids = get_client_list(db_path)
    print(f"📊 Всего клиентов в базе: {len(all_client_ids):,}")
    print()
    
    comparison_results = []
    
    for test_size in test_sizes:
        if test_size > len(all_client_ids):
            continue
            
        print(f"🧪 ТЕСТИРОВАНИЕ {test_size} КЛИЕНТОВ:")
        print("=" * 40)
        
        # Берем подвыборку клиентов
        test_client_ids = all_client_ids[:test_size]
        
        # Тестируем последовательную версию
        sequential_result = test_sequential_performance(test_client_ids, db_path)
        
        print(f"✅ Последовательно: {sequential_result['total_time']:.2f} сек, "
              f"{sequential_result['clients_per_second']:.1f} кл/сек")
        print()
        
        # Тестируем параллельную версию
        parallel_result = test_parallel_performance(test_client_ids, db_path, max_workers=20)
        
        print(f"✅ Параллельно: {parallel_result['total_time']:.2f} сек, "
              f"{parallel_result['clients_per_second']:.1f} кл/сек")
        print()
        
        # Вычисляем ускорение
        speedup = sequential_result['total_time'] / parallel_result['total_time']
        efficiency = speedup / cpu_count * 100
        
        result_data = {
            'test_size': test_size,
            'sequential_time': sequential_result['total_time'],
            'parallel_time': parallel_result['total_time'],
            'sequential_speed': sequential_result['clients_per_second'],
            'parallel_speed': parallel_result['clients_per_second'],
            'speedup': speedup,
            'efficiency': efficiency,
            'sequential_success': sequential_result['success_rate'],
            'parallel_success': parallel_result['success_rate']
        }
        
        comparison_results.append(result_data)
        
        print(f"📊 РЕЗУЛЬТАТЫ для {test_size} клиентов:")
        print(f"   ⚡ Ускорение: {speedup:.1f}x")
        print(f"   📈 Эффективность: {efficiency:.1f}%")
        print(f"   🎯 Улучшение скорости: {(parallel_result['clients_per_second'] / sequential_result['clients_per_second']):.1f}x")
        print()
        print("-" * 60)
        print()
    
    # Итоговое сравнение
    print("📈 ИТОГОВОЕ СРАВНЕНИЕ:")
    print("=" * 30)
    
    if comparison_results:
        avg_speedup = sum(r['speedup'] for r in comparison_results) / len(comparison_results)
        avg_efficiency = sum(r['efficiency'] for r in comparison_results) / len(comparison_results)
        max_speedup = max(r['speedup'] for r in comparison_results)
        
        print(f"🚀 Среднее ускорение: {avg_speedup:.1f}x")
        print(f"📊 Средняя эффективность: {avg_efficiency:.1f}%")
        print(f"🎯 Максимальное ускорение: {max_speedup:.1f}x")
        print()
        
        # Рекомендации
        print("💡 РЕКОМЕНДАЦИИ:")
        print("-" * 20)
        
        if avg_speedup > 15:
            print("✅ Отличное ускорение! Параллелизация очень эффективна.")
        elif avg_speedup > 10:
            print("✅ Хорошее ускорение! Параллелизация эффективна.")
        elif avg_speedup > 5:
            print("⚠️ Умеренное ускорение. Можно оптимизировать.")
        else:
            print("❌ Низкое ускорение. Нужна серьезная оптимизация.")
        
        print()
        
        if avg_efficiency > 70:
            print("✅ Высокая эффективность использования ядер.")
        elif avg_efficiency > 50:
            print("⚠️ Средняя эффективность. Есть потенциал для улучшения.")
        else:
            print("❌ Низкая эффективность. Много накладных расходов.")
        
        print()
        
        # Прогнозы для полной базы
        best_result = max(comparison_results, key=lambda x: x['speedup'])
        total_clients = len(all_client_ids)
        
        sequential_time_full = (best_result['sequential_time'] / best_result['test_size']) * total_clients
        parallel_time_full = (best_result['parallel_time'] / best_result['test_size']) * total_clients
        
        print(f"🔮 ПРОГНОЗ для всех {total_clients:,} клиентов:")
        print(f"   🐌 Последовательно: {sequential_time_full:.1f} сек ({sequential_time_full/60:.1f} мин)")
        print(f"   🚀 Параллельно: {parallel_time_full:.1f} сек ({parallel_time_full/60:.1f} мин)")
        print(f"   💾 Экономия времени: {sequential_time_full - parallel_time_full:.1f} сек ({(sequential_time_full - parallel_time_full)/60:.1f} мин)")
        print()
        
        print("🎯 ЗАКЛЮЧЕНИЕ:")
        print(f"Параллельная версия обрабатывает {total_clients:,} клиентов в {best_result['speedup']:.1f} раз быстрее!")
        print(f"Это экономит {(sequential_time_full - parallel_time_full)/60:.1f} минут времени.")
    
    return comparison_results

if __name__ == "__main__":
    comparison_results = compare_performance() 