# update_country_settings.py
# Скрипт для обновления списков стран в системных настройках

import sqlite3
import json
from aml_codes_config import HIGH_RISK_COUNTRIES, OFFSHORE_COUNTRIES

def update_country_settings(db_path: str = "aml_system.db"):
    """Обновляет списки высокорисковых и офшорных стран в БД"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем альфа-2 коды высокорисковых стран
    high_risk_codes = list(HIGH_RISK_COUNTRIES.values())
    
    # Получаем альфа-2 коды офшорных юрисдикций
    offshore_codes = list(OFFSHORE_COUNTRIES.values())
    
    print("📊 Обновление настроек стран в базе данных...")
    print(f"├── Высокорисковых стран: {len(high_risk_codes)}")
    print(f"└── Офшорных юрисдикций: {len(offshore_codes)}")
    
    # Обновляем high_risk_countries
    cursor.execute('''
    UPDATE system_settings 
    SET setting_value = ?, 
        updated_at = CURRENT_TIMESTAMP 
    WHERE setting_key = 'high_risk_countries'
    ''', (json.dumps(high_risk_codes, ensure_ascii=False),))
    
    if cursor.rowcount == 0:
        # Если записи нет, создаем
        cursor.execute('''
        INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
        VALUES ('high_risk_countries', ?, 'JSON', 'Список высокорисковых стран (FATF)')
        ''', (json.dumps(high_risk_codes, ensure_ascii=False),))
    
    # Обновляем offshore_countries
    cursor.execute('''
    UPDATE system_settings 
    SET setting_value = ?, 
        updated_at = CURRENT_TIMESTAMP 
    WHERE setting_key = 'offshore_countries'
    ''', (json.dumps(offshore_codes, ensure_ascii=False),))
    
    if cursor.rowcount == 0:
        cursor.execute('''
        INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
        VALUES ('offshore_countries', ?, 'JSON', 'Список офшорных юрисдикций')
        ''', (json.dumps(offshore_codes, ensure_ascii=False),))
    
    # Добавляем новую настройку с полным списком всех стран для валидации
    all_country_codes = list(set([
        *HIGH_RISK_COUNTRIES.values(),
        *OFFSHORE_COUNTRIES.values(),
        'KZ', 'RU', 'CN', 'US', 'GB', 'DE', 'TR', 'AE'  # Основные партнеры
    ]))
    
    cursor.execute('''
    INSERT OR REPLACE INTO system_settings (setting_key, setting_value, setting_type, description)
    VALUES ('known_country_codes', ?, 'JSON', 'Список всех известных кодов стран для валидации')
    ''', (json.dumps(sorted(all_country_codes), ensure_ascii=False),))
    
    conn.commit()
    
    # Проверяем результат
    cursor.execute('''
    SELECT setting_key, setting_value 
    FROM system_settings 
    WHERE setting_key IN ('high_risk_countries', 'offshore_countries', 'known_country_codes')
    ''')
    
    print("\n✅ Настройки обновлены:")
    for key, value in cursor.fetchall():
        codes = json.loads(value)
        print(f"\n{key}:")
        print(f"Количество: {len(codes)}")
        if len(codes) <= 10:
            print(f"Коды: {', '.join(codes)}")
        else:
            print(f"Коды: {', '.join(codes[:5])}... и еще {len(codes)-5}")
    
    conn.close()
    print("\n✅ Обновление завершено!")

if __name__ == "__main__":
    update_country_settings()
