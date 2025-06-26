# Скрипт для добавления недостающих кодов подозрительности
# add_missing_codes.py

from aml_codes_config import ALL_SUSPICION_CODES

# Недостающие коды из ваших данных
ADDITIONAL_SUSPICION_CODES = {
    # Коды 1000-1099 (основная серия)
    1011: 'Операция не соответствует обычной деятельности клиента',
    1049: 'Подозрительная операция с наличными',
    1076: 'Получение и выдача беспроцентных займов',
    1081: 'Расчеты через третьи страны',
    1088: 'Использование электронных кошельков',
    1094: 'Подозрительная операция - специальный код',
    
    # Коды 3000-3999 (операции специальных субъектов)
    3002: 'Операция страховой компании',
    
    # Коды 7000-7999 (новые типы операций)
    7001: 'Подозрение в хакерской атаке',
    7006: 'Операция с признаками киберпреступления',
    7013: 'Подозрительная операция в цифровой среде',
    
    # Коды 9000-9999 (дополнительные категории)
    9014: 'Операция требует дополнительной проверки',
}

# Обновляем основной словарь
ALL_SUSPICION_CODES.update(ADDITIONAL_SUSPICION_CODES)

# Функция для анализа неизвестных кодов
def analyze_unknown_codes(db_path: str = "aml_system.db"):
    """Анализ кодов подозрительности в базе данных"""
    import sqlite3
    import json
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем все коды из базы
    cursor.execute('''
    SELECT risk_indicators
    FROM transactions
    WHERE is_suspicious = 1
    ''')
    
    all_codes = {}
    unknown_codes = {}
    
    for row in cursor.fetchall():
        indicators = json.loads(row[0])
        for code in indicators.get('suspicion_codes', []):
            all_codes[code] = all_codes.get(code, 0) + 1
            
            # Проверяем, известен ли код
            if code not in ALL_SUSPICION_CODES:
                unknown_codes[code] = unknown_codes.get(code, 0) + 1
    
    print("📊 АНАЛИЗ КОДОВ ПОДОЗРИТЕЛЬНОСТИ:")
    print(f"Всего уникальных кодов: {len(all_codes)}")
    print(f"Известных кодов: {len(all_codes) - len(unknown_codes)}")
    print(f"Неизвестных кодов: {len(unknown_codes)}")
    
    if unknown_codes:
        print("\n❓ НЕИЗВЕСТНЫЕ КОДЫ:")
        for code, count in sorted(unknown_codes.items(), key=lambda x: x[1], reverse=True):
            print(f"  • Код {code}: {count} операций")
            
        print("\n💡 Рекомендация: Запросите у АФМ РК расшифровку этих кодов")
    
    # Статистика по категориям
    categories = {}
    for code, count in all_codes.items():
        if code in ALL_SUSPICION_CODES:
            category = get_suspicion_category(code)
            categories[category] = categories.get(category, 0) + count
    
    print("\n📈 СТАТИСТИКА ПО КАТЕГОРИЯМ:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {category}: {count} операций")
    
    conn.close()
    return all_codes, unknown_codes

# Функция для обновления описаний кодов в базе
def update_code_descriptions(db_path: str = "aml_system.db"):
    """Обновление описаний кодов в базе данных"""
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создаем таблицу для справочника кодов, если её нет
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suspicion_codes_reference (
        code INTEGER PRIMARY KEY,
        description TEXT,
        category TEXT,
        risk_level TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Добавляем/обновляем коды
    for code, description in ALL_SUSPICION_CODES.items():
        category = get_suspicion_category(code)
        risk_level = 'HIGH' if code in [1054, 1057, 1062, 8002] else 'MEDIUM'
        
        cursor.execute('''
        INSERT OR REPLACE INTO suspicion_codes_reference 
        (code, description, category, risk_level)
        VALUES (?, ?, ?, ?)
        ''', (code, description, category, risk_level))
    
    conn.commit()
    print(f"✅ Обновлено {len(ALL_SUSPICION_CODES)} кодов в справочнике")
    conn.close()

def get_suspicion_category(code: int) -> str:
    """Определить категорию кода подозрительности (расширенная версия)"""
    if 1000 <= code < 1100:
        return 'Основные признаки'
    elif 1050 <= code < 1080:
        return 'Схемы отмывания'
    elif 1080 <= code < 1095:
        return 'Платежи и переводы'
    elif 1070 <= code < 1075:
        return 'Наличные операции'
    elif 2000 <= code < 3000:
        return 'Пороговые операции'
    elif 3000 <= code < 4000:
        return 'Операции спецсубъектов'
    elif 5000 <= code < 6000:
        return 'Финансирование терроризма'
    elif 6000 <= code < 7000:
        return 'Санкционные операции'
    elif 7000 <= code < 8000:
        return 'Киберпреступления'
    elif 8000 <= code < 9000:
        return 'Криптовалюты'
    elif 9000 <= code < 10000:
        return 'Прочие операции'
    else:
        return 'Неклассифицированные'

if __name__ == "__main__":
    print("🔄 Обновление кодов подозрительности...")
    
    # Анализируем коды в базе
    all_codes, unknown = analyze_unknown_codes("aml_system.db")
    
    # Обновляем справочник в базе
    update_code_descriptions("aml_system.db")
    
    print("\n✅ Готово! Теперь система знает все коды из ваших данных.")
