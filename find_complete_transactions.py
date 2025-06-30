import json

def find_complete_transactions():
    with open('do_range.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    complete_count = 0
    incomplete_count = 0
    examples = []
    
    for item in data:
        row_data = item.get('row_to_json', {})
        
        sender_id = row_data.get('gmember_maincode_pl1')
        beneficiary_id = row_data.get('gmember_maincode_pol1')
        
        if sender_id and beneficiary_id:
            complete_count += 1
            if len(examples) < 5:
                examples.append({
                    'id': row_data.get('gmess_id'),
                    'sender': sender_id,
                    'beneficiary': beneficiary_id,
                    'amount': row_data.get('goper_tenge_amount', 0)
                })
        else:
            incomplete_count += 1
    
    print(f'Всего транзакций: {len(data)}')
    print(f'С полными данными: {complete_count}')
    print(f'С неполными данными: {incomplete_count}')
    
    if examples:
        print('\nПримеры полных транзакций:')
        for ex in examples:
            print(f'  ID: {ex["id"]}, От: {ex["sender"]}, Кому: {ex["beneficiary"]}, Сумма: {ex["amount"]}')
    
    return complete_count > 0

if __name__ == "__main__":
    find_complete_transactions() 