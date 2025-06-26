# Загрузчик данных из JSON файла для системы AML АФМ РК
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import os

try:
    from aml_codes_config import get_suspicion_category
except ImportError:
    def get_suspicion_category(code): return "Прочие"

class AMLJSONDataLoader:
    """Загрузчик данных из JSON файла в базу данных AML"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.connection = db_manager.connection
        self.stats = {
            'total_processed': 0,
            'customers_created': 0,
            'transactions_saved': 0,
            'suspicious_found': 0,
            'errors': 0
        }
    
    def load_and_process_json(self, json_file_path: str):
        """Загрузка и обработка данных из JSON файла"""
        print(f"📂 Загрузка данных из файла: {json_file_path}")
        if not os.path.exists(json_file_path):
            print(f"❌ Файл не найден: {json_file_path}")
            return False
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            print(f"📊 Найдено записей: {len(data)}")
            
            for item in data:
                transaction_data = item.get('row_to_json')
                if transaction_data:
                    self._process_transaction(transaction_data)
                else:
                    self.stats['errors'] += 1
            
            self.connection.commit()
            self._print_statistics()
            return True
            
        except Exception as e:
            print(f"❌ Критическая ошибка при загрузке JSON: {e}")
            return False
    
    def _process_transaction(self, tx_data: Dict):
        """Обработка одной транзакции"""
        self.stats['total_processed'] += 1
        try:
            participants = self._extract_participants(tx_data)
            for p in participants:
                self.db_manager.save_customer_profile(p)
            
            transaction_to_save = self._prepare_transaction(tx_data, participants)
            self.db_manager.save_transaction(transaction_to_save)
            self.stats['transactions_saved'] += 1

            if transaction_to_save.get('is_suspicious'):
                self.stats['suspicious_found'] += 1
            
        except Exception as e:
            print(f"⚠️ Ошибка обработки транзакции {tx_data.get('gmess_id')}: {e}")
            self.stats['errors'] += 1

    def _extract_participants(self, tx_data: Dict) -> List[Dict]:
        """Извлечение участников транзакции"""
        # Эта функция должна быть адаптирована под точную структуру ваших данных
        # Здесь приведен упрощенный пример
        participants = []
        if tx_data.get('gmember_maincode_pl1'):
            participants.append({
                'customer_id': tx_data['gmember_maincode_pl1'],
                'full_name': tx_data.get('gmember_name_pl1', '').strip()
            })
        if tx_data.get('gmember_maincode_pol1'):
             participants.append({
                'customer_id': tx_data['gmember_maincode_pol1'],
                'full_name': tx_data.get('gmember_name_pol1', '').strip()
            })
        return participants

    def _prepare_transaction(self, tx_data: Dict, participants: List[Dict]) -> Dict:
        """Подготовка данных транзакции для сохранения"""
        sender = participants[0] if participants else {}
        beneficiary = participants[1] if len(participants) > 1 else {}
        
        is_suspicious = bool(tx_data.get('goper_susp_first'))

        return {
            'transaction_id': f"TX_{tx_data.get('gmess_id')}",
            'amount': float(tx_data.get('goper_tenge_amount', 0)),
            'currency': 'KZT',
            'amount_kzt': float(tx_data.get('goper_tenge_amount', 0)),
            'transaction_date': self._parse_date(tx_data.get('goper_trans_date')),
            'sender_id': sender.get('customer_id'),
            'sender_name': sender.get('full_name'),
            'beneficiary_id': beneficiary.get('customer_id'),
            'beneficiary_name': beneficiary.get('full_name'),
            'purpose_text': tx_data.get('goper_dopinfo', ''),
            'is_suspicious': is_suspicious,
            'final_risk_score': 5.0 if is_suspicious else 1.0,
            'risk_indicators': json.dumps({'susp_code': tx_data.get('goper_susp_first')})
        }

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        if not date_str: return None
        try:
            return datetime.fromisoformat(date_str.split('.')[0]).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return None

    def _print_statistics(self):
        """Вывод статистики загрузки"""
        print("\n📊 СТАТИСТИКА ЗАГРУЗКИ:")
        print(f"├── Обработано записей: {self.stats['total_processed']}")
        print(f"├── Сохранено транзакций: {self.stats['transactions_saved']}")
        print(f"├── Подозрительных операций: {self.stats['suspicious_found']}")
        print(f"└── Ошибок: {self.stats['errors']}")
        if self.stats['total_processed'] > 0 and self.stats['suspicious_found'] > 0:
            rate = (self.stats['suspicious_found'] / self.stats['total_processed']) * 100
            print(f"\n⚠️ Уровень подозрительности: {rate:.1f}%") 