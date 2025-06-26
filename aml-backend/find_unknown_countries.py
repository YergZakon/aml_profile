# Поиск неизвестных кодов стран в данных
# find_unknown_countries.py

import sqlite3
import json
from aml_codes_config import COUNTRY_CODES, HIGH_RISK_COUNTRIES, OFFSHORE_COUNTRIES

def find_unknown_country_codes(db_path: str = "aml_system.db"):
    """Находит все коды стран из базы, которых нет в справочнике"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Объединяем все известные коды
    all_known_codes = {
        **COUNTRY_CODES,
        **HIGH_RISK_COUNTRIES,
        **OFFSHORE_COUNTRIES
    }
    
    print("🔍 ПОИСК НЕИЗВЕСТНЫХ КОДОВ СТРАН")
    print("="*60)
    
    # 1. Ищем в исходных JSON данных (сохраненных в risk_indicators)
    cursor.execute('''
    SELECT DISTINCT 
        sender_country,
        beneficiary_country,
        risk_indicators
    FROM transactions
    ''')
    
    unknown_codes = {}
    country_stats = {}
    
    for row in cursor.fetchall():
        # Проверяем страны отправителя и получателя
        for country in [row[0], row[1]]:
            if country and country != 'KZ':
                country_stats[country] = country_stats.get(country, 0) + 1
                
                # Если код XX - значит не нашли в справочнике
                if country == 'XX':
                    # Пытаемся найти оригинальный код в risk_indicators
                    try:
                        indicators = json.loads(row[2])
                        # Здесь может быть оригинальный код
                    except:
                        pass
    
    # 2. Ищем оригинальные коды в customer_profiles
    cursor.execute('''
    SELECT DISTINCT residence_country
    FROM customer_profiles
    WHERE residence_country IS NOT NULL
    ''')
    
    for row in cursor.fetchall():
        country = row[0]
        if country and country not in ['KZ', 'XX']:
            if country not in all_known_codes.values():
                # Это буквенный код, которого нет в справочнике
                print(f"⚠️ Неизвестный буквенный код: {country}")
    
    # 3. Проверяем raw данные если есть
    cursor.execute('''
    SELECT name, sql FROM sqlite_master 
    WHERE type='table' AND name LIKE '%raw%'
    ''')
    
    raw_tables = cursor.fetchall()
    if raw_tables:
        print(f"\nНайдены таблицы с сырыми данными: {[t[0] for t in raw_tables]}")
    
    # 4. Анализируем транзакции с XX
    cursor.execute('''
    SELECT 
        transaction_id,
        sender_id,
        sender_name,
        sender_country,
        beneficiary_id,
        beneficiary_name,
        beneficiary_country,
        amount_kzt
    FROM transactions
    WHERE sender_country = 'XX' OR beneficiary_country = 'XX'
    ORDER BY amount_kzt DESC
    ''')
    
    xx_transactions = cursor.fetchall()
    if xx_transactions:
        print(f"\n🌍 ТРАНЗАКЦИИ С НЕИЗВЕСТНЫМИ СТРАНАМИ (XX):")
        print(f"Найдено: {len(xx_transactions)} транзакций")
        
        for tx in xx_transactions[:10]:  # Первые 10
            print(f"\n├── ID: {tx[0]}")
            print(f"│   Сумма: {tx[7]:,.0f} тенге")
            print(f"│   Отправитель: {tx[2]} ({tx[1]})")
            print(f"│   Страна отправителя: {tx[3]}")
            print(f"│   Получатель: {tx[5]} ({tx[4]})")
            print(f"│   Страна получателя: {tx[6]}")
            
            # Пытаемся найти клиентов в базе
            for client_id in [tx[1], tx[4]]:
                if client_id:
                    cursor.execute('''
                    SELECT residence_country FROM customer_profiles 
                    WHERE customer_id = ?
                    ''', (client_id,))
                    client = cursor.fetchone()
                    if client:
                        print(f"│   └── Резидентство в профиле: {client[0]}")
    
    # 5. Статистика по всем странам
    print(f"\n📊 СТАТИСТИКА ПО СТРАНАМ В БАЗЕ:")
    for country, count in sorted(country_stats.items(), key=lambda x: x[1], reverse=True)[:20]:
        status = "✓" if country in all_known_codes.values() else "❌"
        print(f"{status} {country}: {count} транзакций")
    
    conn.close()
    
    return unknown_codes

def check_original_json(json_file: str = "do_range.json"):
    """Проверяет оригинальный JSON файл на предмет кодов стран"""
    try:
        import json
        
        print(f"\n📄 ПРОВЕРКА ОРИГИНАЛЬНОГО ФАЙЛА: {json_file}")
        print("="*60)
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Собираем все уникальные коды резидентства
        residence_codes = set()
        
        for item in data[:10]:  # Первые 10 записей для примера
            record = item.get('row_to_json', item)
            
            # Все поля с кодами стран
            country_fields = [
                'gmember_residence_pl1',
                'gmember_residence_pl2', 
                'gmember_residence_pol1',
                'gmember_residence_pol2'
            ]
            
            for field in country_fields:
                code = record.get(field)
                if code and code != 398:  # 398 = KZ
                    residence_codes.add(code)
                    
                    # Проверяем, есть ли в справочнике
                    all_codes = {**COUNTRY_CODES, **HIGH_RISK_COUNTRIES, **OFFSHORE_COUNTRIES}
                    if code not in all_codes:
                        participant = record.get(field.replace('residence', 'name'))
                        print(f"\n❌ Неизвестный код страны: {code}")
                        print(f"   Участник: {participant}")
                        print(f"   Поле: {field}")
                        
                        # Показываем контекст
                        if field.endswith('pl1') or field.endswith('pl2'):
                            print(f"   Тип участника: Плательщик")
                        else:
                            print(f"   Тип участника: Получатель")
        
        print(f"\n📊 Найдено уникальных кодов стран: {len(residence_codes)}")
        print(f"Коды: {sorted(residence_codes)}")
        
    except FileNotFoundError:
        print(f"❌ Файл {json_file} не найден")
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")

def update_unknown_countries(db_path: str = "aml_system.db"):
    """Обновляет транзакции с правильными кодами стран"""
    
    # Дополнительные коды стран, которые могут быть в данных
    ADDITIONAL_COUNTRY_CODES = {
        # Добавьте сюда коды, которые найдете в данных
        # Например:
        # 999: 'ZZ',  # Неопределенная страна
        # 000: 'XX',  # Неизвестная страна
    }
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Обновляем транзакции
    updates = 0
    
    # Здесь можно добавить логику обновления
    
    conn.commit()
    conn.close()
    
    if updates > 0:
        print(f"✅ Обновлено {updates} транзакций")

if __name__ == "__main__":
    # 1. Ищем неизвестные коды в базе
    unknown = find_unknown_country_codes()
    
    # 2. Проверяем оригинальный JSON
    check_original_json("do_range.json")
    
    print("\n💡 РЕКОМЕНДАЦИИ:")
    print("1. Проверьте оригинальный JSON файл на наличие кодов стран")
    print("2. Добавьте недостающие коды в COUNTRY_CODES")
    print("3. Перезагрузите данные с обновленным справочником")
