# Транзакционный профиль для системы мониторинга АФМ РК
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
from enum import Enum

class TransactionType(Enum):
    """Типы операций согласно классификации АФМ РК"""
    CASH_DEPOSIT = "1100"
    CASH_WITHDRAWAL = "1200"
    TRANSFER_INTERNAL = "2100"
    TRANSFER_EXTERNAL = "2200"
    TRANSFER_INTERNATIONAL = "2300"
    CURRENCY_EXCHANGE = "3100"
    CARD_PAYMENT = "4100"
    LOAN_DISBURSEMENT = "5100"
    LOAN_REPAYMENT = "5200"
    SUSPICIOUS_PATTERN = "9999"

class TransactionProfile:
    """Профиль транзакции для анализа ПОД/ФТ"""
    
    def __init__(self):
        self.created_at = datetime.now()
        self.transaction_id = "N/A"
        self.basic_info = {}
        self.parties = {}
        self.operation_details = {}
        self.risk_indicators = {}
        self.checks = {}
        self.analysis_result = {}
        self.reset_profile()

    def reset_profile(self):
        """Сброс состояния профиля для нового анализа"""
        self.transaction_id = "N/A"
        self.basic_info = {
            'amount': 0.0, 'currency': 'KZT', 'amount_kzt': 0.0,
            'transaction_date': None, 'channel': 'unknown'
        }
        self.parties = {
            'sender_id': '', 'sender_country': 'KZ',
            'beneficiary_id': '', 'beneficiary_country': 'KZ'
        }
        self.operation_details = {
            'purpose_text': '', 'is_cash': False, 'is_international': False
        }
        self.risk_indicators = {
            'is_high_risk_country': False, 'is_offshore': False,
            'is_pep_involved': False, 'is_round_amount': False,
            'is_unusual_time': False
        }
        self.checks = {
            'threshold_check': False, 'pattern_match': [], 'rule_triggers': [],
            'final_risk_score': 0.0
        }
        self.analysis_result = {
            'is_suspicious': False, 'suspicion_reasons': [],
            'recommended_action': 'PASS'
        }

    def set_basic_info(self, amount: float, currency: str, transaction_date: datetime, channel: str):
        self.basic_info['amount'] = amount
        self.basic_info['currency'] = currency
        self.basic_info['transaction_date'] = transaction_date
        self.basic_info['channel'] = channel
        
        rates = {'USD': 450, 'EUR': 490, 'RUB': 5}
        self.basic_info['amount_kzt'] = amount * rates.get(currency, 1)

    def check_threshold_afm(self) -> Tuple[bool, str]:
        amount_kzt = self.basic_info.get('amount_kzt', 0)
        thresholds = {'cash': 2_000_000, 'international': 1_000_000, 'transfer': 7_000_000}
        
        if self.operation_details.get('is_cash') and amount_kzt >= thresholds['cash']:
            return True, f"Наличная операция >= {thresholds['cash']:,} KZT"
        if self.operation_details.get('is_international') and amount_kzt >= thresholds['international']:
            return True, f"Международная операция >= {thresholds['international']:,} KZT"
        if amount_kzt >= thresholds['transfer']:
            return True, f"Перевод >= {thresholds['transfer']:,} KZT"
        return False, "Ниже пороговых значений"

    def check_risk_indicators(self):
        amount = self.basic_info.get('amount', 0)
        if amount % 1000 == 0 and amount >= 100000:
            self.risk_indicators['is_round_amount'] = True
        
        if self.basic_info.get('transaction_date'):
            hour = self.basic_info['transaction_date'].hour
            if hour < 6 or hour > 23:
                self.risk_indicators['is_unusual_time'] = True
        
        high_risk = {'IR', 'KP', 'MM', 'AF', 'YE', 'SY'}
        if self.parties.get('sender_country') in high_risk or self.parties.get('beneficiary_country') in high_risk:
            self.risk_indicators['is_high_risk_country'] = True

    def analyze_purpose_text(self):
        purpose = self.operation_details.get('purpose_text', '').lower()
        if not purpose: return

        suspicious_keywords = ['благотворительность', 'пожертвование', 'услуги', 'возврат долга']
        if any(kw in purpose for kw in suspicious_keywords):
            self.checks['pattern_match'].append("Подозрительное ключевое слово в назначении")

        if len(purpose) < 10 or purpose in ['перевод', 'оплата']:
            self.checks['pattern_match'].append("Неинформативное назначение платежа")

    def apply_afm_rules(self):
        rules = []
        if self.risk_indicators.get('is_high_risk_country'):
            rules.append("R003: Операция с высокорисковой юрисдикцией")
        if self.risk_indicators.get('is_round_amount') and self.checks.get('pattern_match'):
            rules.append("R004: Круглая сумма и подозрительное назначение")
        self.checks['rule_triggers'] = rules

    def calculate_final_score(self) -> float:
        score = 0.0
        if self.checks.get('threshold_check'): score += 3.0
        
        risk_weights = {'is_high_risk_country': 2.5, 'is_round_amount': 0.5, 'is_unusual_time': 0.5}
        for indicator, weight in risk_weights.items():
            if self.risk_indicators.get(indicator):
                score += weight
        
        score += len(self.checks.get('rule_triggers', [])) * 1.5
        score += len(self.checks.get('pattern_match', [])) * 0.5
        
        final_score = min(score, 10.0)
        self.checks['final_risk_score'] = final_score
        
        if final_score >= 7.0:
            self.analysis_result.update({'is_suspicious': True, 'recommended_action': 'STR'})
        elif final_score >= 5.0:
            self.analysis_result.update({'is_suspicious': True, 'recommended_action': 'EDD'})
        
        return final_score

    def analyze_transaction(self, transaction: Dict) -> Dict:
        self.reset_profile()
        self.transaction_id = transaction.get('transaction_id', 'N/A')

        self.set_basic_info(
            amount=transaction.get('amount', 0.0),
            currency=transaction.get('currency', 'KZT'),
            transaction_date=transaction.get('date', datetime.now()),
            channel=(transaction.get('channel') or 'unknown')
        )
        
        self.parties.update({
            'sender_id': transaction.get('sender_id'),
            'sender_country': transaction.get('sender_country', 'KZ'),
            'beneficiary_id': transaction.get('beneficiary_id'),
            'beneficiary_country': transaction.get('beneficiary_country', 'KZ'),
        })
        
        self.operation_details.update({
            'purpose_text': (transaction.get('purpose') or ''),
            'is_cash': 'cash' in (transaction.get('channel') or '').lower(),
            'is_international': (transaction.get('sender_country') or '') != (transaction.get('beneficiary_country') or ''),
        })

        threshold_passed, reason = self.check_threshold_afm()
        if threshold_passed:
            self.checks['threshold_check'] = True
            self.checks['rule_triggers'].append(reason)

        self.check_risk_indicators()
        self.analyze_purpose_text()
        self.apply_afm_rules()
        self.calculate_final_score()

        return {
            'transaction_id': self.transaction_id,
            'is_suspicious': self.analysis_result['is_suspicious'],
            'risk_score': self.checks['final_risk_score'],
            'reasons': self.checks['rule_triggers'] + self.checks['pattern_match'],
            'recommendation': self.analysis_result['recommended_action'],
        } 