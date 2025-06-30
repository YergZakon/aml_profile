import json
from collections import Counter

def analyze_operation_types():
    with open('do_range.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    operation_types = []
    operation_views = []
    
    for item in data:
        row_data = item.get('row_to_json', {})
        
        op_type = row_data.get('goper_idtype')
        op_view = row_data.get('goper_idview')
        
        operation_types.append(op_type)
        operation_views.append(op_view)
    
    print('Типы операций (goper_idtype):')
    type_counts = Counter(operation_types)
    for op_type, count in type_counts.most_common(10):
        print(f'  {op_type}: {count} операций')
    
    print('\nВиды операций (goper_idview):')
    view_counts = Counter(operation_views)
    for op_view, count in view_counts.most_common(10):
        print(f'  {op_view}: {count} операций')
    
    # Проверим образцы данных
    print('\nОбразцы данных:')
    for i, item in enumerate(data[:3]):
        row_data = item.get('row_to_json', {})
        print(f'\nТранзакция {i+1}:')
        print(f'  ID: {row_data.get("gmess_id")}')
        print(f'  Тип: {row_data.get("goper_idtype")}')
        print(f'  Вид: {row_data.get("goper_idview")}')
        print(f'  Сумма: {row_data.get("goper_tenge_amount")}')
        print(f'  Отправитель: {row_data.get("gmember_maincode_pl1")}')
        print(f'  Получатель: {row_data.get("gmember_maincode_pol1")}')
        print(f'  Доп.инфо: {row_data.get("goper_dopinfo")}')

if __name__ == "__main__":
    analyze_operation_types() 