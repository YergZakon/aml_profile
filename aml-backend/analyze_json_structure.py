#!/usr/bin/env python3
"""
Анализ структуры входящих JSON файлов
"""

import json
import sys
from pathlib import Path

def analyze_json_structure(file_path):
    """Анализирует структуру JSON файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📁 Файл: {file_path}")
        print(f"📊 Тип данных: {type(data)}")
        
        if isinstance(data, list):
            print(f"📦 Количество элементов: {len(data):,}")
            if len(data) > 0:
                print(f"🔍 Тип первого элемента: {type(data[0])}")
                if isinstance(data[0], dict):
                    print(f"🗝️  Ключи первого элемента:")
                    for i, key in enumerate(data[0].keys()):
                        if i < 10:  # Показываем только первые 10 ключей
                            value = data[0][key]
                            value_type = type(value).__name__
                            if isinstance(value, str) and len(value) > 50:
                                value_preview = value[:50] + "..."
                            else:
                                value_preview = str(value)
                            print(f"   • {key}: {value_preview} ({value_type})")
                        elif i == 10:
                            print(f"   ... и еще {len(data[0].keys()) - 10} ключей")
                            break
                            
                # Анализируем структуру для AML
                print(f"\n🔍 АНАЛИЗ ДЛЯ AML:")
                first_item = data[0]
                
                # Ищем поля транзакций
                transaction_fields = []
                for key in first_item.keys():
                    if any(keyword in key.lower() for keyword in ['transaction', 'trans', 'amount', 'sum', 'money', 'tenge']):
                        transaction_fields.append(key)
                
                if transaction_fields:
                    print(f"💰 Поля транзакций: {transaction_fields}")
                
                # Ищем поля клиентов
                client_fields = []
                for key in first_item.keys():
                    if any(keyword in key.lower() for keyword in ['member', 'client', 'customer', 'name', 'id']):
                        client_fields.append(key)
                
                if client_fields:
                    print(f"👤 Поля клиентов: {client_fields}")
                
                # Ищем поля подозрительности
                suspicious_fields = []
                for key in first_item.keys():
                    if any(keyword in key.lower() for keyword in ['susp', 'suspicious', 'risk', 'alert']):
                        suspicious_fields.append(key)
                
                if suspicious_fields:
                    print(f"🚨 Поля подозрительности: {suspicious_fields}")
                    
        elif isinstance(data, dict):
            print(f"🗝️  Ключи верхнего уровня: {list(data.keys())}")
            
        return data
        
    except FileNotFoundError:
        print(f"❌ Файл не найден: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Анализируем все JSON файлы в uploads
        uploads_dir = Path("uploads")
        if uploads_dir.exists():
            json_files = list(uploads_dir.glob("*.json"))
            if json_files:
                print(f"🔍 Найдено JSON файлов: {len(json_files)}")
                for json_file in json_files[:3]:  # Анализируем первые 3 файла
                    print("\n" + "="*60)
                    analyze_json_structure(json_file)
            else:
                print("❌ JSON файлы не найдены в папке uploads")
        else:
            print("❌ Папка uploads не найдена")
            
        # Также анализируем тестовый файл
        test_file = Path("test_transactions.json")
        if test_file.exists():
            print("\n" + "="*60)
            print("📋 ТЕСТОВЫЙ ФАЙЛ:")
            analyze_json_structure(test_file) 