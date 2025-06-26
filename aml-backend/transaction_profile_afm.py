# Транзакционный профиль для системы мониторинга АФМ РК
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
import re
from enum import Enum
import math

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
        self.pattern_analysis = {}
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
            'purpose_text': '', 'is_cash': False, 'is_international': False,
            'operation_type': None
        }
        self.risk_indicators = {
            'is_high_risk_country': False, 'is_offshore': False,
            'is_pep_involved': False, 'is_round_amount': False,
            'is_unusual_time': False, 'is_structuring': False,
            'is_rapid_movement': False, 'round_amount_type': None,
            'time_risk_level': None
        }
        self.checks = {
            'threshold_check': False, 'pattern_match': [], 'rule_triggers': [],
            'final_risk_score': 0.0, 'risk_components': {}
        }
        self.analysis_result = {
            'is_suspicious': False, 'suspicion_reasons': [],
            'recommended_action': 'PASS', 'confidence_level': 0.0
        }
        self.pattern_analysis = {
            'time_patterns': {}, 'amount_patterns': {},
            'behavioral_flags': []
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

    def is_round_amount(self, amount: float) -> Tuple[bool, str]:
        """Детальная проверка круглых сумм с определением типа"""
        if amount <= 0:
            return False, None
            
        # Проверка на точные круглые суммы (кратные 1000, 10000, 100000)
        round_thresholds = [
            (1_000_000, "миллион"),
            (100_000, "сто тысяч"),
            (50_000, "пятьдесят тысяч"),
            (10_000, "десять тысяч"),
            (5_000, "пять тысяч"),
            (1_000, "тысяча")
        ]
        
        for threshold, label in round_thresholds:
            if amount % threshold == 0 and amount >= threshold:
                return True, f"Круглая сумма - кратна {label}"
        
        # Проверка на "почти круглые" суммы (999,000 или 1,001,000)
        amount_str = str(int(amount))
        if len(amount_str) >= 4:
            # Проверяем паттерны типа 999xxx, 1001xxx
            if amount_str.startswith('999') or amount_str.startswith('1001'):
                return True, "Почти круглая сумма (структурирование)"
            
            # Проверяем повторяющиеся цифры (111,111 или 555,555)
            if len(set(amount_str)) == 1:
                return True, "Повторяющиеся цифры"
        
        # Проверка на суммы чуть ниже порога (1,999,000 вместо 2,000,000)
        thresholds_check = [2_000_000, 7_000_000, 10_000_000]
        for threshold in thresholds_check:
            if threshold * 0.95 <= amount < threshold:
                return True, f"Сумма чуть ниже порога {threshold:,} KZT"
        
        return False, None

    def is_unusual_time(self, transaction_date: datetime) -> Tuple[bool, str]:
        """Детальный анализ времени операции"""
        if not transaction_date:
            return False, None
            
        hour = transaction_date.hour
        weekday = transaction_date.weekday()  # 0 = Monday, 6 = Sunday
        
        # Определяем уровень риска по времени
        risk_level = None
        reason = None
        
        # Ночные операции (00:00 - 06:00)
        if 0 <= hour < 6:
            risk_level = "HIGH"
            reason = f"Ночная операция ({hour:02d}:00-{hour+1:02d}:00)"
            
        # Ранние утренние (06:00 - 08:00)
        elif 6 <= hour < 8:
            risk_level = "MEDIUM"
            reason = f"Ранняя утренняя операция ({hour:02d}:00-{hour+1:02d}:00)"
            
        # Поздние вечерние (22:00 - 24:00)
        elif 22 <= hour <= 23:
            risk_level = "MEDIUM"
            reason = f"Поздняя вечерняя операция ({hour:02d}:00-{hour+1:02d}:00)"
            
        # Выходные дни
        if weekday in [5, 6]:  # Saturday, Sunday
            if risk_level:
                risk_level = "HIGH"
                reason += " в выходной день"
            else:
                risk_level = "LOW"
                reason = "Операция в выходной день"
        
        # Праздничные дни (можно расширить список)
        holidays = [
            (1, 1), (1, 2), (3, 8), (3, 21), (3, 22), (3, 23),
            (5, 1), (5, 7), (5, 9), (7, 6), (8, 30), (10, 25),
            (12, 16), (12, 17)
        ]
        
        if (transaction_date.month, transaction_date.day) in holidays:
            if risk_level:
                risk_level = "HIGH"
                reason += " в праздничный день"
            else:
                risk_level = "MEDIUM"
                reason = "Операция в праздничный день"
        
        self.risk_indicators['time_risk_level'] = risk_level
        return risk_level in ["MEDIUM", "HIGH"], reason

    def analyze_transaction_patterns(self, transaction: Dict, transaction_history: List[Dict] = None):
        """Анализ паттернов транзакций"""
        patterns = []
        
        # Анализ структурирования (дробление)
        if transaction_history:
            recent_transactions = []
            for t in transaction_history:
                if 'transaction_date' in t and 'transaction_date' in transaction:
                    try:
                        # Преобразуем строки в datetime если нужно
                        tx_date = transaction['transaction_date']
                        t_date = t['transaction_date']
                        
                        if isinstance(tx_date, str):
                            tx_date = datetime.fromisoformat(tx_date)
                        if isinstance(t_date, str):
                            t_date = datetime.fromisoformat(t_date)
                            
                        if abs((tx_date - t_date).total_seconds()) < 3600:  # В течение часа
                            recent_transactions.append(t)
                    except (ValueError, TypeError):
                        continue
            
            if len(recent_transactions) >= 3:
                total_amount = sum(t.get('amount', 0) for t in recent_transactions)
                if total_amount >= 2_000_000:
                    patterns.append("Возможное структурирование - множественные транзакции")
                    self.risk_indicators['is_structuring'] = True
        
        # Быстрое движение средств
        if transaction.get('channel') == 'instant' or 'express' in str(transaction.get('purpose_text', '')).lower():
            patterns.append("Быстрое движение средств")
            self.risk_indicators['is_rapid_movement'] = True
        
        self.pattern_analysis['behavioral_flags'] = patterns
        return patterns

    def check_risk_indicators(self):
        """Расширенная проверка индикаторов риска"""
        amount = self.basic_info.get('amount', 0)
        
        # Проверка круглых сумм
        is_round, round_type = self.is_round_amount(amount)
        if is_round:
            self.risk_indicators['is_round_amount'] = True
            self.risk_indicators['round_amount_type'] = round_type
            self.checks['pattern_match'].append(round_type)
        
        # Проверка времени
        if self.basic_info.get('transaction_date'):
            is_unusual, time_reason = self.is_unusual_time(self.basic_info['transaction_date'])
            if is_unusual:
                self.risk_indicators['is_unusual_time'] = True
                self.checks['pattern_match'].append(time_reason)
        
        # Проверка высокорисковых стран
        high_risk = {'IR', 'KP', 'MM', 'AF', 'YE', 'SY'}
        offshore = {'KY', 'VG', 'BS', 'BZ', 'SC', 'VU', 'PA', 'LI', 'MC'}
        
        sender_country = self.parties.get('sender_country', '')
        beneficiary_country = self.parties.get('beneficiary_country', '')
        
        if sender_country in high_risk or beneficiary_country in high_risk:
            self.risk_indicators['is_high_risk_country'] = True
            
        if sender_country in offshore or beneficiary_country in offshore:
            self.risk_indicators['is_offshore'] = True

    def analyze_purpose_text(self):
        """Улучшенный анализ назначения платежа"""
        purpose = self.operation_details.get('purpose_text', '').lower()
        if not purpose: 
            self.checks['pattern_match'].append("Отсутствует назначение платежа")
            return

        # Расширенный список подозрительных ключевых слов
        suspicious_keywords = {
            'высокий': ['благотворительность', 'пожертвование', 'помощь', 'спонсорская'],
            'средний': ['услуги', 'консультация', 'возврат долга', 'займ'],
            'низкий': ['товар', 'продукция', 'оборудование']
        }
        
        for risk_level, keywords in suspicious_keywords.items():
            if any(kw in purpose for kw in keywords):
                self.checks['pattern_match'].append(f"Ключевое слово '{risk_level}' риска в назначении")
                break

        # Проверка на неинформативность
        if len(purpose) < 10 or purpose in ['перевод', 'оплата', 'платеж']:
            self.checks['pattern_match'].append("Неинформативное назначение платежа")
            
        # Проверка на избыточную информацию (может скрывать истинную цель)
        if len(purpose) > 200:
            self.checks['pattern_match'].append("Избыточно длинное назначение платежа")

    def apply_afm_rules(self):
        """Применение правил АФМ РК"""
        rules = []
        
        # Правило 1: Высокорисковая юрисдикция
        if self.risk_indicators.get('is_high_risk_country'):
            rules.append("R001: Операция с высокорисковой юрисдикцией")
            
        # Правило 2: Офшорная зона
        if self.risk_indicators.get('is_offshore'):
            rules.append("R002: Операция с офшорной зоной")
        
        # Правило 3: Комбинация факторов
        if self.risk_indicators.get('is_round_amount') and self.risk_indicators.get('is_unusual_time'):
            rules.append("R003: Круглая сумма + необычное время")
            
        # Правило 4: Структурирование
        if self.risk_indicators.get('is_structuring'):
            rules.append("R004: Признаки структурирования")
            
        # Правило 5: Пороговая операция в нерабочее время
        if self.checks.get('threshold_check') and self.risk_indicators.get('time_risk_level') == "HIGH":
            rules.append("R005: Крупная операция в нерабочее время")
            
        self.checks['rule_triggers'] = rules

    def calculate_final_score(self) -> float:
        """Улучшенный расчет риск-скора с детализацией компонентов"""
        components = {}
        
        # 1. Базовый риск от порога (0-3 балла)
        if self.checks.get('threshold_check'):
            amount = self.basic_info.get('amount_kzt', 0)
            if amount >= 10_000_000:
                components['threshold'] = 3.0
            elif amount >= 7_000_000:
                components['threshold'] = 2.5
            elif amount >= 2_000_000:
                components['threshold'] = 2.0
            else:
                components['threshold'] = 1.5
        else:
            components['threshold'] = 0.0
        
        # 2. Географический риск (0-3 балла)
        geo_risk = 0.0
        if self.risk_indicators.get('is_high_risk_country'):
            geo_risk += 2.5
        if self.risk_indicators.get('is_offshore'):
            geo_risk += 1.5
        components['geographic'] = min(geo_risk, 3.0)
        
        # 3. Временной риск (0-2 балла)
        time_risk_map = {'HIGH': 2.0, 'MEDIUM': 1.0, 'LOW': 0.5}
        components['time'] = time_risk_map.get(self.risk_indicators.get('time_risk_level'), 0.0)
        
        # 4. Риск от паттернов (0-2 балла)
        pattern_risk = 0.0
        if self.risk_indicators.get('is_round_amount'):
            if 'структурирование' in str(self.risk_indicators.get('round_amount_type', '')).lower():
                pattern_risk += 1.5
            else:
                pattern_risk += 0.5
        if self.risk_indicators.get('is_structuring'):
            pattern_risk += 1.0
        if self.risk_indicators.get('is_rapid_movement'):
            pattern_risk += 0.5
        components['patterns'] = min(pattern_risk, 2.0)
        
        # 5. Риск от правил (0-2 балла)
        components['rules'] = min(len(self.checks.get('rule_triggers', [])) * 0.5, 2.0)
        
        # Суммируем компоненты
        total_score = sum(components.values())
        
        # Применяем нелинейную функцию для более точного распределения
        # Используем сигмоидную функцию для сглаживания
        final_score = 10 * (1 / (1 + math.exp(-0.5 * (total_score - 5))))
        final_score = round(min(max(final_score, 0.0), 10.0), 2)
        
        # Сохраняем компоненты для анализа
        self.checks['risk_components'] = components
        self.checks['final_risk_score'] = final_score
        
        # Определяем уровень уверенности
        confidence = 0.0
        if len(self.checks.get('rule_triggers', [])) >= 2:
            confidence += 0.3
        if len(self.checks.get('pattern_match', [])) >= 3:
            confidence += 0.3
        if components.get('geographic', 0) > 0 and components.get('patterns', 0) > 0:
            confidence += 0.4
        self.analysis_result['confidence_level'] = min(confidence, 1.0)
        
        # Определяем рекомендуемое действие
        if final_score >= 7.0:
            self.analysis_result.update({
                'is_suspicious': True,
                'recommended_action': 'STR'  # Suspicious Transaction Report
            })
        elif final_score >= 5.0:
            self.analysis_result.update({
                'is_suspicious': True,
                'recommended_action': 'EDD'  # Enhanced Due Diligence
            })
        elif final_score >= 3.0:
            self.analysis_result.update({
                'is_suspicious': False,
                'recommended_action': 'MONITOR'  # Продолжить мониторинг
            })
        else:
            self.analysis_result.update({
                'is_suspicious': False,
                'recommended_action': 'PASS'  # Пропустить
            })
        
        return final_score

    def analyze_transaction(self, transaction: Dict, transaction_history: List[Dict] = None) -> Dict:
        """Основной метод анализа транзакции"""
        self.reset_profile()
        self.transaction_id = transaction.get('transaction_id', 'N/A')

        # Устанавливаем базовую информацию
        self.set_basic_info(
            amount=transaction.get('amount', 0.0),
            currency=transaction.get('currency', 'KZT'),
            transaction_date=transaction.get('date', datetime.now()),
            channel=(transaction.get('channel') or 'unknown')
        )
        
        # Информация об участниках
        self.parties.update({
            'sender_id': transaction.get('sender_id'),
            'sender_country': transaction.get('sender_country', 'KZ'),
            'beneficiary_id': transaction.get('beneficiary_id'),
            'beneficiary_country': transaction.get('beneficiary_country', 'KZ'),
        })
        
        # Детали операции
        self.operation_details.update({
            'purpose_text': (transaction.get('purpose') or transaction.get('purpose_text') or ''),
            'is_cash': 'cash' in (transaction.get('channel') or '').lower(),
            'is_international': (transaction.get('sender_country') or 'KZ') != (transaction.get('beneficiary_country') or 'KZ'),
            'operation_type': transaction.get('operation_type')
        })

        # Проверка порогов
        threshold_passed, reason = self.check_threshold_afm()
        if threshold_passed:
            self.checks['threshold_check'] = True
            self.checks['rule_triggers'].append(reason)

        # Комплексные проверки
        self.check_risk_indicators()
        self.analyze_purpose_text()
        self.analyze_transaction_patterns(transaction, transaction_history)
        self.apply_afm_rules()
        final_score = self.calculate_final_score()

        # Формируем результат
        return {
            'transaction_id': self.transaction_id,
            'is_suspicious': self.analysis_result['is_suspicious'],
            'risk_score': final_score,
            'risk_components': self.checks['risk_components'],
            'reasons': self.checks['rule_triggers'] + self.checks['pattern_match'],
            'recommendation': self.analysis_result['recommended_action'],
            'confidence_level': self.analysis_result['confidence_level'],
            'risk_indicators': {
                k: v for k, v in self.risk_indicators.items() 
                if v and k not in ['round_amount_type', 'time_risk_level']
            },
            'detailed_analysis': {
                'round_amount_type': self.risk_indicators.get('round_amount_type'),
                'time_risk_level': self.risk_indicators.get('time_risk_level'),
                'behavioral_flags': self.pattern_analysis.get('behavioral_flags', [])
            }
        } 