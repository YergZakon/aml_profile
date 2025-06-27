import json

with open('do_range.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

first = data[0]
print('Ключи в первой записи:')
keys = list(first.keys())
for i, key in enumerate(keys):
    if i < 30:  # Первые 30 ключей
        print(f'  {key}')

print(f'\nВсего ключей: {len(keys)}')

# Ищем поля получателя
beneficiary_keys = [k for k in keys if 'pol' in k.lower() or 'beneficiary' in k.lower()]
print(f'\nПоля получателя: {beneficiary_keys}')

# Проверяем конкретные поля
row_data = first.get('row_to_json', {})
if row_data:
    print('\nПоля в row_to_json:')
    for key in list(row_data.keys())[:20]:
        print(f'  {key}: {row_data[key]}') 