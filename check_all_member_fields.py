import json

def check_member_fields():
    with open('do_range.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Найдем все поля с gmember
    first_row = data[0].get('row_to_json', {})
    member_fields = [k for k in first_row.keys() if 'gmember' in k]
    
    print('Все поля участников (gmember):')
    for field in member_fields:
        print(f'  {field}')
    
    # Проверим значения в первых нескольких записях
    print('\nЗначения полей в первых 5 записях:')
    for i, item in enumerate(data[:5]):
        row_data = item.get('row_to_json', {})
        print(f'\nЗапись {i+1} (ID: {row_data.get("gmess_id")}):')
        for field in member_fields:
            value = row_data.get(field)
            print(f'  {field}: {value}')

if __name__ == "__main__":
    check_member_fields() 